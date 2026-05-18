from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

try:
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl")
    os.environ.setdefault("MPLBACKEND", "Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, roc_curve
except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency guard
    raise SystemExit(
        "Missing plotting dependencies. Install matplotlib and scikit-learn first, "
        "for example with `pip install -r requirements.txt`."
    ) from exc


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot threshold and cost-performance comparisons for router models."
    )
    parser.add_argument("--baseline-eval-dir", type=Path, required=True)
    parser.add_argument("--modernbert-eval-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def extract_static_point(static_metrics: dict, x_key: str, y_key: str) -> tuple[float, float]:
    return float(static_metrics[x_key]), float(static_metrics[y_key])


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    baseline_curve = load_jsonl(args.baseline_eval_dir / "test_threshold_curve.jsonl")
    modernbert_curve = load_jsonl(args.modernbert_eval_dir / "test_threshold_curve.jsonl")
    baseline_static = load_json(args.baseline_eval_dir / "baseline_policies.json")
    modernbert_static = load_json(args.modernbert_eval_dir / "baseline_policies.json")
    baseline_selected = load_json(args.baseline_eval_dir / "selected_threshold.json")
    modernbert_selected = load_json(args.modernbert_eval_dir / "selected_threshold.json")

    baseline_prediction_rows = load_jsonl(
        args.baseline_eval_dir.parent / "test_predictions.jsonl"
    )
    modernbert_prediction_rows = load_jsonl(
        args.modernbert_eval_dir.parent / "test_predictions.jsonl"
    )

    # 1. Threshold vs F1 for mix_required
    plt.figure(figsize=(8, 5))
    plt.plot(
        [row["threshold"] for row in baseline_curve],
        [row["f1_mix_required"] for row in baseline_curve],
        label="TF-IDF + Logistic Regression",
        linewidth=2,
    )
    plt.plot(
        [row["threshold"] for row in modernbert_curve],
        [row["f1_mix_required"] for row in modernbert_curve],
        label="ModernBERT-base",
        linewidth=2,
    )
    plt.axvline(float(baseline_selected["threshold"]), color="C0", linestyle="--", alpha=0.6)
    plt.axvline(float(modernbert_selected["threshold"]), color="C1", linestyle="--", alpha=0.6)
    plt.xlabel("Decision threshold for mix_required")
    plt.ylabel("F1 (mix_required)")
    plt.title("Threshold sweep: positive-class F1")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(args.output_dir / "threshold_vs_f1_mix_required.png", dpi=200)
    plt.close()

    # 2. Threshold vs average routed time
    plt.figure(figsize=(8, 5))
    plt.plot(
        [row["threshold"] for row in baseline_curve],
        [row["average_routed_time_seconds"] for row in baseline_curve],
        label="TF-IDF + Logistic Regression",
        linewidth=2,
    )
    plt.plot(
        [row["threshold"] for row in modernbert_curve],
        [row["average_routed_time_seconds"] for row in modernbert_curve],
        label="ModernBERT-base",
        linewidth=2,
    )
    plt.axvline(float(baseline_selected["threshold"]), color="C0", linestyle="--", alpha=0.6)
    plt.axvline(float(modernbert_selected["threshold"]), color="C1", linestyle="--", alpha=0.6)
    plt.xlabel("Decision threshold for mix_required")
    plt.ylabel("Average routed time (seconds)")
    plt.title("Threshold sweep: average routed time")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(args.output_dir / "threshold_vs_average_time.png", dpi=200)
    plt.close()

    # 3. Cost-performance frontier
    plt.figure(figsize=(8, 5))
    plt.plot(
        [row["average_routed_time_seconds"] for row in baseline_curve],
        [row["f1_mix_required"] for row in baseline_curve],
        label="TF-IDF + Logistic Regression",
        linewidth=2,
    )
    plt.plot(
        [row["average_routed_time_seconds"] for row in modernbert_curve],
        [row["f1_mix_required"] for row in modernbert_curve],
        label="ModernBERT-base",
        linewidth=2,
    )

    naive_time, naive_f1 = extract_static_point(
        baseline_static["always_naive"],
        "average_routed_time_seconds",
        "f1_mix_required",
    )
    mix_time, mix_f1 = extract_static_point(
        baseline_static["always_mix"],
        "average_routed_time_seconds",
        "f1_mix_required",
    )
    plt.scatter([naive_time], [naive_f1], marker="o", s=70, label="Always Naive")
    plt.scatter([mix_time], [mix_f1], marker="D", s=70, label="Always Mix")

    plt.xlabel("Average routed time (seconds)")
    plt.ylabel("F1 (mix_required)")
    plt.title("Offline policy frontier")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(args.output_dir / "cost_performance_frontier.png", dpi=200)
    plt.close()

    # 4. Standard ROC curve
    baseline_y_true = [int(row["label"]) for row in baseline_prediction_rows]
    baseline_scores = [float(row["score_mix_required"]) for row in baseline_prediction_rows]
    modernbert_y_true = [int(row["label"]) for row in modernbert_prediction_rows]
    modernbert_scores = [float(row["score_mix_required"]) for row in modernbert_prediction_rows]

    baseline_fpr, baseline_tpr, _ = roc_curve(baseline_y_true, baseline_scores)
    modernbert_fpr, modernbert_tpr, _ = roc_curve(modernbert_y_true, modernbert_scores)
    baseline_roc_auc = roc_auc_score(baseline_y_true, baseline_scores)
    modernbert_roc_auc = roc_auc_score(modernbert_y_true, modernbert_scores)

    plt.figure(figsize=(8, 5))
    plt.plot(
        baseline_fpr,
        baseline_tpr,
        linewidth=2,
        label=f"TF-IDF + Logistic Regression (ROC-AUC={baseline_roc_auc:.3f})",
    )
    plt.plot(
        modernbert_fpr,
        modernbert_tpr,
        linewidth=2,
        label=f"ModernBERT-base (ROC-AUC={modernbert_roc_auc:.3f})",
    )
    plt.plot([0, 1], [0, 1], linestyle="--", linewidth=1.5, color="gray", label="Random")
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Test ROC curve")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(args.output_dir / "roc_curve_test.png", dpi=200)
    plt.close()

    # 5. Precision-recall curve
    baseline_precision, baseline_recall, _ = precision_recall_curve(
        baseline_y_true, baseline_scores
    )
    modernbert_precision, modernbert_recall, _ = precision_recall_curve(
        modernbert_y_true, modernbert_scores
    )
    baseline_ap = average_precision_score(baseline_y_true, baseline_scores)
    modernbert_ap = average_precision_score(modernbert_y_true, modernbert_scores)

    plt.figure(figsize=(8, 5))
    plt.plot(
        baseline_recall,
        baseline_precision,
        linewidth=2,
        label=f"TF-IDF + Logistic Regression (AP={baseline_ap:.3f})",
    )
    plt.plot(
        modernbert_recall,
        modernbert_precision,
        linewidth=2,
        label=f"ModernBERT-base (AP={modernbert_ap:.3f})",
    )
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Test precision-recall curve")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(args.output_dir / "precision_recall_curve_test.png", dpi=200)
    plt.close()

    print(f"Saved plots to {args.output_dir}")


if __name__ == "__main__":
    main()
