from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

try:
    from sklearn.metrics import (
        accuracy_score,
        average_precision_score,
        balanced_accuracy_score,
        confusion_matrix,
        precision_recall_fscore_support,
        roc_auc_score,
    )
    from sklearn.model_selection import train_test_split
except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency guard
    raise SystemExit(
        "Missing router dependencies. Install scikit-learn first, "
        "for example with `pip install -r requirements.txt`."
    ) from exc


CLASS_TO_LABEL = {
    "naive_enough": 0,
    "mix_required": 1,
}
LABEL_TO_CLASS = {value: key for key, value in CLASS_TO_LABEL.items()}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def merge_query_results_and_judgments(
    query_results_path: Path,
    judgments_path: Path,
    keep_none_enough: bool = False,
) -> list[dict[str, Any]]:
    query_rows = load_jsonl(query_results_path)
    judgment_rows = load_jsonl(judgments_path)

    query_by_id = {row["sample_id"]: row for row in query_rows}
    merged_rows: list[dict[str, Any]] = []

    for judgment in judgment_rows:
        sample_id = judgment["sample_id"]
        query_row = query_by_id.get(sample_id)
        if query_row is None:
            continue

        judge_class = judgment.get("judge_class")
        if judge_class == "none_enough" and not keep_none_enough:
            continue
        if judge_class not in {"naive_enough", "mix_required", "none_enough"}:
            continue

        merged = {
            "sample_id": sample_id,
            "split": judgment.get("split", query_row.get("split")),
            "question_type": judgment.get("question_type", query_row.get("question_type")),
            "question": judgment.get("question", query_row.get("question")),
            "ground_truth": judgment.get("ground_truth", query_row.get("ground_truth")),
            "judge_class": judge_class,
            "label": CLASS_TO_LABEL.get(judge_class),
            "naive_answer": judgment.get("naive_answer", query_row.get("naive_answer")),
            "mix_answer": judgment.get("mix_answer", query_row.get("mix_answer")),
            "naive_time_seconds": query_row.get("naive_time_seconds"),
            "mix_time_seconds": query_row.get("mix_time_seconds"),
            "naive_top_k": query_row.get("naive_top_k"),
            "context_count": query_row.get("context_count"),
            "supporting_fact_count": query_row.get("supporting_fact_count"),
            "supporting_doc_ids": query_row.get("supporting_doc_ids"),
            "judge_model": judgment.get("judge_model"),
            "judged_at": judgment.get("judged_at"),
            "raw_judge_response": judgment.get("raw_judge_response"),
        }
        merged_rows.append(merged)

    return merged_rows


def stratified_split(
    rows: list[dict[str, Any]],
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
    stratify_by: str = "joint",
) -> dict[str, list[dict[str, Any]]]:
    """Split rows into train/validation/test with stratification.

    Args:
        rows: dataset rows; each must have a numeric ``label`` and a
            ``question_type`` string.
        train_ratio, val_ratio, test_ratio: must sum to 1.
        seed: numpy/scikit-learn random state.
        stratify_by: one of ``"label"`` (stratify on the binary class only),
            ``"question_type"`` (stratify on the four-way question type),
            or ``"joint"`` (stratify on the cross product
            ``(question_type, label)``, the default).
    """
    if not math.isclose(train_ratio + val_ratio + test_ratio, 1.0, rel_tol=1e-6):
        raise ValueError("train_ratio + val_ratio + test_ratio must sum to 1.0")
    if not rows:
        raise ValueError("Cannot split an empty dataset.")

    def stratum_key(row: dict[str, Any]) -> str:
        if stratify_by == "label":
            return str(row["label"])
        if stratify_by == "question_type":
            return str(row.get("question_type", "unknown"))
        if stratify_by == "joint":
            return f"{row.get('question_type', 'unknown')}::{row['label']}"
        raise ValueError(
            f"Unknown stratify_by={stratify_by!r}; expected 'label', 'question_type', or 'joint'."
        )

    keys = [stratum_key(row) for row in rows]
    train_rows, temp_rows = train_test_split(
        rows,
        test_size=(1.0 - train_ratio),
        random_state=seed,
        stratify=keys,
    )

    temp_keys = [stratum_key(row) for row in temp_rows]
    val_fraction_of_temp = val_ratio / (val_ratio + test_ratio)
    val_rows, test_rows = train_test_split(
        temp_rows,
        train_size=val_fraction_of_temp,
        random_state=seed,
        stratify=temp_keys,
    )

    for split_name, split_rows in {
        "train": train_rows,
        "validation": val_rows,
        "test": test_rows,
    }.items():
        for row in split_rows:
            row["dataset_split"] = split_name

    return {
        "train": train_rows,
        "validation": val_rows,
        "test": test_rows,
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    class_counts = Counter(row["judge_class"] for row in rows)
    question_type_by_class: dict[str, Counter[str]] = defaultdict(Counter)
    split_counts = Counter(row.get("split") for row in rows)

    for row in rows:
        question_type_by_class[row["judge_class"]][row.get("question_type", "unknown")] += 1

    return {
        "total_rows": len(rows),
        "class_counts": dict(class_counts),
        "split_counts": dict(split_counts),
        "question_type_by_class": {
            class_name: dict(counter)
            for class_name, counter in question_type_by_class.items()
        },
    }


def compute_binary_metrics(
    y_true: list[int],
    y_scores: list[float],
    threshold: float,
) -> dict[str, Any]:
    y_pred = [1 if score >= threshold else 0 for score in y_scores]
    precision_pos, recall_pos, f1_pos, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="binary",
        pos_label=1,
        zero_division=0,
    )
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="macro",
        zero_division=0,
    )

    metrics = {
        "threshold": threshold,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision_mix_required": float(precision_pos),
        "recall_mix_required": float(recall_pos),
        "f1_mix_required": float(f1_pos),
        "precision_macro": float(precision_macro),
        "recall_macro": float(recall_macro),
        "f1_macro": float(f1_macro),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
    }

    if len(set(y_true)) > 1:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_scores))
        metrics["average_precision"] = float(average_precision_score(y_true, y_scores))
    else:
        metrics["roc_auc"] = None
        metrics["average_precision"] = None

    return metrics


def compute_policy_metrics(
    rows: list[dict[str, Any]],
    y_scores: list[float],
    threshold: float,
) -> dict[str, Any]:
    y_true = [int(row["label"]) for row in rows]
    y_pred = [1 if score >= threshold else 0 for score in y_scores]

    routed_costs = []
    mix_routes = 0
    for row, prediction in zip(rows, y_pred, strict=True):
        if prediction == 1:
            routed_costs.append(float(row["mix_time_seconds"]))
            mix_routes += 1
        else:
            routed_costs.append(float(row["naive_time_seconds"]))

    metrics = compute_binary_metrics(y_true, y_scores, threshold)
    metrics.update(
        {
            "total_routed_time_seconds": float(sum(routed_costs)),
            "average_routed_time_seconds": float(sum(routed_costs) / len(routed_costs)),
            "mix_route_rate": float(mix_routes / len(rows)),
        }
    )
    return metrics


def compute_static_policy_metrics(
    rows: list[dict[str, Any]],
    policy_name: str,
) -> dict[str, Any]:
    y_true = [int(row["label"]) for row in rows]

    if policy_name == "always_naive":
        y_scores = [0.0 for _ in rows]
        total_time = sum(float(row["naive_time_seconds"]) for row in rows)
        mix_route_rate = 0.0
    elif policy_name == "always_mix":
        y_scores = [1.0 for _ in rows]
        total_time = sum(float(row["mix_time_seconds"]) for row in rows)
        mix_route_rate = 1.0
    else:
        raise ValueError(f"Unknown static policy: {policy_name}")

    metrics = compute_binary_metrics(y_true, y_scores, threshold=0.5)
    metrics.update(
        {
            "policy_name": policy_name,
            "total_routed_time_seconds": float(total_time),
            "average_routed_time_seconds": float(total_time / len(rows)),
            "mix_route_rate": mix_route_rate,
        }
    )
    return metrics


def build_threshold_grid(num_thresholds: int = 101) -> list[float]:
    if num_thresholds < 2:
        raise ValueError("num_thresholds must be at least 2")
    return [index / (num_thresholds - 1) for index in range(num_thresholds)]


def compute_policy_curve(
    rows: list[dict[str, Any]],
    y_scores: list[float],
    thresholds: list[float],
) -> list[dict[str, Any]]:
    return [compute_policy_metrics(rows, y_scores, threshold) for threshold in thresholds]


def select_best_threshold(
    rows: list[dict[str, Any]],
    y_scores: list[float],
    thresholds: list[float],
    metric_name: str = "f1_mix_required",
) -> tuple[float, list[dict[str, Any]]]:
    curve = compute_policy_curve(rows, y_scores, thresholds)
    best = max(curve, key=lambda item: (item[metric_name], -item["mix_route_rate"]))
    return float(best["threshold"]), curve


def find_metrics_at_threshold(
    curve: list[dict[str, Any]],
    threshold: float,
) -> dict[str, Any]:
    for item in curve:
        if abs(float(item["threshold"]) - float(threshold)) < 1e-12:
            return item
    raise ValueError(f"Threshold {threshold} not found in curve.")


def save_prediction_rows(
    path: Path,
    rows: list[dict[str, Any]],
    scores: list[float],
) -> None:
    payload = []
    for row, score in zip(rows, scores, strict=True):
        payload.append(
            {
                "sample_id": row["sample_id"],
                "dataset_split": row["dataset_split"],
                "question": row["question"],
                "question_type": row.get("question_type"),
                "label": int(row["label"]),
                "judge_class": row["judge_class"],
                "score_mix_required": float(score),
                "naive_time_seconds": float(row["naive_time_seconds"]),
                "mix_time_seconds": float(row["mix_time_seconds"]),
            }
        )
    write_jsonl(path, payload)


def load_prediction_rows(path: Path) -> list[dict[str, Any]]:
    return load_jsonl(path)
