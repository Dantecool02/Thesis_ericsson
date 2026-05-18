from __future__ import annotations

import argparse
from pathlib import Path

from router_utils import (
    merge_query_results_and_judgments,
    stratified_split,
    summarize_rows,
    write_json,
    write_jsonl,
)


DEFAULT_QUERY_RESULTS = Path("data/processed/2wiki/progress/query_results.jsonl")
DEFAULT_JUDGMENTS = Path("data/processed/2wiki/progress/router_judgments.jsonl")
DEFAULT_OUTPUT_DIR = Path("data/processed/2wiki/router_binary")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a clean binary router dataset from judged 2Wiki query results."
    )
    parser.add_argument("--query-results", type=Path, default=DEFAULT_QUERY_RESULTS)
    parser.add_argument("--judgments", type=Path, default=DEFAULT_JUDGMENTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--stratify-by",
        default="joint",
        choices=["label", "question_type", "joint"],
        help="Stratification key for the train/validation/test split.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.query_results.exists():
        raise FileNotFoundError(f"Query results file not found: {args.query_results}")
    if not args.judgments.exists():
        raise FileNotFoundError(f"Judgments file not found: {args.judgments}")

    rows = merge_query_results_and_judgments(
        query_results_path=args.query_results,
        judgments_path=args.judgments,
        keep_none_enough=False,
    )
    if not rows:
        raise ValueError("No usable binary rows found after filtering out none_enough.")

    splits = stratified_split(
        rows,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
        stratify_by=args.stratify_by,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "all_binary.jsonl", rows)
    write_jsonl(args.output_dir / "train.jsonl", splits["train"])
    write_jsonl(args.output_dir / "validation.jsonl", splits["validation"])
    write_jsonl(args.output_dir / "test.jsonl", splits["test"])

    summary = {
        "dataset_name": "2wiki_router_binary",
        "source_query_results": str(args.query_results),
        "source_judgments": str(args.judgments),
        "seed": args.seed,
        "stratify_by": args.stratify_by,
        "split_ratios": {
            "train": args.train_ratio,
            "validation": args.val_ratio,
            "test": args.test_ratio,
        },
        "overall": summarize_rows(rows),
        "train": summarize_rows(splits["train"]),
        "validation": summarize_rows(splits["validation"]),
        "test": summarize_rows(splits["test"]),
    }
    write_json(args.output_dir / "summary.json", summary)

    print(f"Wrote binary router dataset to {args.output_dir}")
    print(f"  Total usable rows: {len(rows):,}")
    print(f"  Train: {len(splits['train']):,}")
    print(f"  Validation: {len(splits['validation']):,}")
    print(f"  Test: {len(splits['test']):,}")


if __name__ == "__main__":
    main()
