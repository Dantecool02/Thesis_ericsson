from __future__ import annotations

import argparse
import pickle
from pathlib import Path

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency guard
    raise SystemExit(
        "Missing baseline dependencies. Install scikit-learn first, "
        "for example with `pip install -r requirements.txt`."
    ) from exc

from router_utils import (
    compute_binary_metrics,
    load_jsonl,
    save_prediction_rows,
    write_json,
)


DEFAULT_DATASET_DIR = Path("data/processed/2wiki/router_binary")
DEFAULT_OUTPUT_DIR = Path("data/models/router_baseline_tfidf")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a TF-IDF + logistic regression baseline router."
    )
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-features", type=int, default=20000)
    parser.add_argument("--min-df", type=int, default=2)
    parser.add_argument("--max-iter", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_split(dataset_dir: Path, split_name: str) -> list[dict]:
    path = dataset_dir / f"{split_name}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Dataset split not found: {path}")
    return load_jsonl(path)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    train_rows = load_split(args.dataset_dir, "train")
    validation_rows = load_split(args.dataset_dir, "validation")
    test_rows = load_split(args.dataset_dir, "test")

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=args.min_df,
        max_features=args.max_features,
    )

    x_train = vectorizer.fit_transform(row["question"] for row in train_rows)
    y_train = [int(row["label"]) for row in train_rows]

    classifier = LogisticRegression(
        max_iter=args.max_iter,
        class_weight="balanced",
        random_state=args.seed,
    )
    classifier.fit(x_train, y_train)

    metrics_summary: dict[str, dict] = {}
    for split_name, rows in {
        "validation": validation_rows,
        "test": test_rows,
    }.items():
        x_split = vectorizer.transform(row["question"] for row in rows)
        y_true = [int(row["label"]) for row in rows]
        y_scores = classifier.predict_proba(x_split)[:, 1].tolist()

        save_prediction_rows(args.output_dir / f"{split_name}_predictions.jsonl", rows, y_scores)
        metrics_summary[split_name] = compute_binary_metrics(
            y_true,
            y_scores,
            threshold=0.5,
        )

    with (args.output_dir / "model.pkl").open("wb") as handle:
        pickle.dump(
            {
                "vectorizer": vectorizer,
                "classifier": classifier,
                "config": {
                    "max_features": args.max_features,
                    "min_df": args.min_df,
                    "max_iter": args.max_iter,
                    "seed": args.seed,
                },
            },
            handle,
        )

    write_json(args.output_dir / "metrics_at_0_5.json", metrics_summary)

    print(f"Saved baseline model to {args.output_dir / 'model.pkl'}")
    print(f"Saved validation/test predictions to {args.output_dir}")


if __name__ == "__main__":
    main()
