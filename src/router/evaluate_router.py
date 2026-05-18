from __future__ import annotations

import argparse
from pathlib import Path

from router_utils import (
    build_threshold_grid,
    compute_policy_curve,
    compute_static_policy_metrics,
    find_metrics_at_threshold,
    load_prediction_rows,
    select_best_threshold,
    write_json,
    write_jsonl,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate router predictions with threshold selection and offline policy analysis."
    )
    parser.add_argument("--validation-predictions", type=Path, required=True)
    parser.add_argument("--test-predictions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--num-thresholds", type=int, default=101)
    parser.add_argument(
        "--select-metric",
        default="f1_mix_required",
        choices=["f1_mix_required", "balanced_accuracy", "f1_macro"],
        help="Validation metric used to choose the deployment threshold.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    validation_rows = load_prediction_rows(args.validation_predictions)
    test_rows = load_prediction_rows(args.test_predictions)
    thresholds = build_threshold_grid(args.num_thresholds)

    validation_scores = [float(row["score_mix_required"]) for row in validation_rows]
    test_scores = [float(row["score_mix_required"]) for row in test_rows]

    selected_threshold, validation_curve = select_best_threshold(
        rows=validation_rows,
        y_scores=validation_scores,
        thresholds=thresholds,
        metric_name=args.select_metric,
    )
    test_curve = compute_policy_curve(
        rows=test_rows,
        y_scores=test_scores,
        thresholds=thresholds,
    )
    selected_test_metrics = find_metrics_at_threshold(test_curve, selected_threshold)

    baselines = {
        "always_naive": compute_static_policy_metrics(test_rows, "always_naive"),
        "always_mix": compute_static_policy_metrics(test_rows, "always_mix"),
    }

    write_json(
        args.output_dir / "selected_threshold.json",
        {
            "selected_on": "validation",
            "selection_metric": args.select_metric,
            "threshold": selected_threshold,
        },
    )
    write_json(args.output_dir / "test_metrics_at_selected_threshold.json", selected_test_metrics)
    write_json(args.output_dir / "baseline_policies.json", baselines)
    write_jsonl(args.output_dir / "validation_threshold_curve.jsonl", validation_curve)
    write_jsonl(args.output_dir / "test_threshold_curve.jsonl", test_curve)

    print(f"Selected threshold ({args.select_metric}): {selected_threshold:.2f}")
    print(f"Saved evaluation outputs to {args.output_dir}")


if __name__ == "__main__":
    main()
