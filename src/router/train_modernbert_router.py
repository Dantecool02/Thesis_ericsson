from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path

try:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        get_linear_schedule_with_warmup,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency guard
    raise SystemExit(
        "Missing training dependencies. Install torch and transformers first, "
        "for example with `pip install -r requirements.txt`."
    ) from exc

from router_utils import compute_binary_metrics, load_jsonl, save_prediction_rows, write_json


DEFAULT_DATASET_DIR = Path("data/processed/2wiki/router_binary")
DEFAULT_OUTPUT_DIR = Path("data/models/router_modernbert")
DEFAULT_MODEL_NAME = "answerdotai/ModernBERT-base"


class QuestionDataset(Dataset):
    def __init__(self, rows: list[dict[str, object]]):
        self.rows = rows

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, object]:
        row = self.rows[index]
        return {
            "text": str(row["question"]),
            "label": int(row["label"]),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a ModernBERT router on the binary judged 2Wiki dataset."
    )
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME)
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Load model/tokenizer/config only from the local Hugging Face cache.",
    )
    parser.add_argument(
        "--use-fast-tokenizer",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether to prefer the fast tokenizer implementation when available.",
    )
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-ratio", type=float, default=0.1)
    parser.add_argument("--patience", type=int, default=2)
    parser.add_argument("--min-epochs", type=int, default=2)
    parser.add_argument("--label-smoothing", type=float, default=0.05)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument(
        "--sampling",
        default="shuffle",
        choices=["shuffle", "weighted"],
        help="How to sample training batches.",
    )
    parser.add_argument(
        "--class-weight-mode",
        default="balanced",
        choices=["balanced", "none"],
        help="Whether to use balanced class weights in the loss.",
    )
    parser.add_argument(
        "--selection-metric",
        default="average_precision",
        choices=["average_precision", "f1_mix_required", "balanced_accuracy", "f1_macro"],
        help="Validation metric used for best-checkpoint selection.",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_split(dataset_dir: Path, split_name: str) -> list[dict]:
    path = dataset_dir / f"{split_name}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Dataset split not found: {path}")
    return load_jsonl(path)


def build_collate_fn(tokenizer, max_length: int):
    def collate(batch: list[dict[str, object]]) -> dict[str, torch.Tensor]:
        texts = [str(item["text"]) for item in batch]
        labels = torch.tensor([int(item["label"]) for item in batch], dtype=torch.long)
        encoded = tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors="pt",
        )
        encoded["labels"] = labels
        return encoded

    return collate


def select_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def compute_class_weights(train_rows: list[dict]) -> torch.Tensor:
    counts = Counter(int(row["label"]) for row in train_rows)
    total = sum(counts.values())
    weights = []
    for label in [0, 1]:
        label_count = counts[label]
        weights.append(total / (2 * label_count))
    return torch.tensor(weights, dtype=torch.float)


def build_weighted_sampler(train_rows: list[dict]) -> WeightedRandomSampler:
    counts = Counter(int(row["label"]) for row in train_rows)
    sample_weights = [1.0 / counts[int(row["label"])] for row in train_rows]
    return WeightedRandomSampler(
        weights=torch.tensor(sample_weights, dtype=torch.double),
        num_samples=len(sample_weights),
        replacement=True,
    )


def move_batch_to_device(batch: dict[str, torch.Tensor], device: torch.device) -> dict[str, torch.Tensor]:
    return {key: value.to(device) for key, value in batch.items()}


def evaluate_loss(
    model,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    model.eval()
    losses = []
    with torch.no_grad():
        for batch in loader:
            batch = move_batch_to_device(batch, device)
            labels = batch["labels"]
            outputs = model(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
            )
            loss = criterion(outputs.logits.float(), labels)
            losses.append(float(loss.item()))
    return sum(losses) / max(len(losses), 1)


def predict_scores(
    model,
    rows: list[dict],
    tokenizer,
    max_length: int,
    batch_size: int,
    device: torch.device,
) -> list[float]:
    model.eval()
    dataset = QuestionDataset(rows)
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=build_collate_fn(tokenizer, max_length),
    )

    scores: list[float] = []
    with torch.no_grad():
        for batch in loader:
            batch = move_batch_to_device(batch, device)
            outputs = model(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
            )
            probabilities = torch.softmax(outputs.logits.float(), dim=-1)[:, 1]
            scores.extend(float(score) for score in probabilities.cpu().tolist())
    return scores


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    train_rows = load_split(args.dataset_dir, "train")
    validation_rows = load_split(args.dataset_dir, "validation")
    test_rows = load_split(args.dataset_dir, "test")

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_name,
        local_files_only=args.local_files_only,
        use_fast=args.use_fast_tokenizer,
    )
    model_kwargs = {}
    config = None
    try:
        from transformers import AutoConfig

        config = AutoConfig.from_pretrained(
            args.model_name,
            local_files_only=args.local_files_only,
        )
        config.num_labels = 2
        if hasattr(config, "classifier_dropout") and config.classifier_dropout is None:
            config.classifier_dropout = 0.1
        model_kwargs["config"] = config
    except Exception:
        model_kwargs["num_labels"] = 2
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        local_files_only=args.local_files_only,
        **model_kwargs,
    )

    device = select_device()
    model.to(device)

    collate_fn = build_collate_fn(tokenizer, args.max_length)
    train_dataset = QuestionDataset(train_rows)
    train_loader_kwargs = {
        "dataset": train_dataset,
        "batch_size": args.batch_size,
        "collate_fn": collate_fn,
    }
    if args.sampling == "weighted":
        train_loader_kwargs["sampler"] = build_weighted_sampler(train_rows)
    else:
        train_loader_kwargs["shuffle"] = True

    train_loader = DataLoader(**train_loader_kwargs)
    validation_loader = DataLoader(
        QuestionDataset(validation_rows),
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=collate_fn,
    )

    class_weights = None
    if args.class_weight_mode == "balanced":
        class_weights = compute_class_weights(train_rows).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=args.label_smoothing)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )
    total_steps = max(
        (len(train_loader) * args.epochs) // args.gradient_accumulation_steps,
        1,
    )
    warmup_steps = int(total_steps * args.warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(
        optimizer=optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    best_state = None
    best_metric = float("-inf")
    patience_counter = 0
    history: list[dict[str, float]] = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_losses = []
        optimizer.zero_grad()
        for step, batch in enumerate(train_loader, start=1):
            batch = move_batch_to_device(batch, device)
            labels = batch["labels"]

            outputs = model(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
            )
            loss = criterion(outputs.logits.float(), labels)
            loss = loss / args.gradient_accumulation_steps
            loss.backward()
            train_losses.append(float(loss.item() * args.gradient_accumulation_steps))

            should_step = (
                step % args.gradient_accumulation_steps == 0
                or step == len(train_loader)
            )
            if should_step:
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=args.max_grad_norm)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

        validation_loss = evaluate_loss(model, validation_loader, criterion, device)
        validation_scores = predict_scores(
            model,
            validation_rows,
            tokenizer,
            args.max_length,
            args.batch_size,
            device,
        )
        validation_metrics = compute_binary_metrics(
            [int(row["label"]) for row in validation_rows],
            validation_scores,
            threshold=0.5,
        )

        epoch_record = {
            "epoch": epoch,
            "train_loss": sum(train_losses) / max(len(train_losses), 1),
            "validation_loss": validation_loss,
            "validation_f1_mix_required": validation_metrics["f1_mix_required"],
            "validation_macro_f1": validation_metrics["f1_macro"],
        }
        history.append(epoch_record)
        print(
            f"Epoch {epoch}: "
            f"train_loss={epoch_record['train_loss']:.4f} "
            f"val_loss={validation_loss:.4f} "
            f"val_f1_mix={validation_metrics['f1_mix_required']:.4f} "
            f"val_ap={validation_metrics['average_precision']:.4f}"
        )

        metric_value = validation_metrics[args.selection_metric]
        if metric_value is None:
            metric_value = float("-inf")

        if metric_value > best_metric:
            best_metric = metric_value
            best_state = copy.deepcopy(model.state_dict())
            patience_counter = 0
        else:
            patience_counter += 1
            if epoch >= args.min_epochs and patience_counter >= args.patience:
                print("Early stopping triggered.")
                break

    if best_state is None:
        raise RuntimeError("Training finished without a valid best model state.")

    model.load_state_dict(best_state)
    best_model_dir = args.output_dir / "best_model"
    best_model_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(best_model_dir)
    tokenizer.save_pretrained(best_model_dir)

    metrics_summary: dict[str, dict] = {}
    for split_name, rows in {
        "validation": validation_rows,
        "test": test_rows,
    }.items():
        scores = predict_scores(
            model,
            rows,
            tokenizer,
            args.max_length,
            args.batch_size,
            device,
        )
        save_prediction_rows(args.output_dir / f"{split_name}_predictions.jsonl", rows, scores)
        metrics_summary[split_name] = compute_binary_metrics(
            [int(row["label"]) for row in rows],
            scores,
            threshold=0.5,
        )

    write_json(args.output_dir / "training_history.json", {"epochs": history})
    write_json(args.output_dir / "metrics_at_0_5.json", metrics_summary)
    write_json(
        args.output_dir / "training_config.json",
        {
            "model_name": args.model_name,
            "local_files_only": args.local_files_only,
            "use_fast_tokenizer": args.use_fast_tokenizer,
            "max_length": args.max_length,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "weight_decay": args.weight_decay,
            "warmup_ratio": args.warmup_ratio,
            "patience": args.patience,
            "min_epochs": args.min_epochs,
            "gradient_accumulation_steps": args.gradient_accumulation_steps,
            "label_smoothing": args.label_smoothing,
            "max_grad_norm": args.max_grad_norm,
            "sampling": args.sampling,
            "class_weight_mode": args.class_weight_mode,
            "selection_metric": args.selection_metric,
            "seed": args.seed,
            "device": str(device),
        },
    )

    print(f"Saved best ModernBERT model to {best_model_dir}")
    print(f"Saved validation/test predictions to {args.output_dir}")


if __name__ == "__main__":
    main()
