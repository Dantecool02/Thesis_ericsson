from __future__ import annotations

import argparse
from pathlib import Path

from router_utils import load_jsonl, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Average router prediction files into a simple probability ensemble."
    )
    parser.add_argument(
        "--inputs",
        type=Path,
        nargs="+",
        required=True,
        help="Prediction JSONL files with score_mix_required fields in matching row order.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output JSONL file for the averaged predictions.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    row_sets = [load_jsonl(path) for path in args.inputs]
    if not row_sets:
        raise ValueError("No input prediction files were provided.")

    expected_length = len(row_sets[0])
    for path, rows in zip(args.inputs, row_sets, strict=True):
        if len(rows) != expected_length:
            raise ValueError(
                f"Prediction length mismatch for {path}: expected {expected_length}, got {len(rows)}."
            )

    ensembled_rows = []
    for row_group in zip(*row_sets, strict=True):
        base_row = dict(row_group[0])
        sample_id = base_row.get("sample_id")
        if any(row.get("sample_id") != sample_id for row in row_group[1:]):
            raise ValueError("Input prediction files are not aligned by sample_id.")

        average_score = sum(float(row["score_mix_required"]) for row in row_group) / len(row_group)
        base_row["score_mix_required"] = average_score
        ensembled_rows.append(base_row)

    write_jsonl(args.output, ensembled_rows)
    print(f"Wrote ensembled predictions to {args.output}")


if __name__ == "__main__":
    main()
