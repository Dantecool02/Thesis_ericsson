from __future__ import annotations

import argparse
import json
from pathlib import Path

from two_wiki_utils import infer_split_name, iter_json_array, make_sample_record, write_jsonl_record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export 2Wiki into one-row-per-sample JSONL while preserving dataset order."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to a 2Wiki split JSON file such as train.json or dev.json.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where the sample-preserving outputs will be written.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of samples to process for a quick preview.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    split = infer_split_name(args.input)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    sample_jsonl_path = output_dir / f"{split}_samples.jsonl"
    stats_path = output_dir / f"{split}_stats.json"

    sample_count = 0
    context_doc_count = 0
    supporting_fact_count = 0
    evidence_count = 0

    with sample_jsonl_path.open("w", encoding="utf-8") as sample_jsonl:
        for sample in iter_json_array(args.input):
            if args.limit is not None and sample_count >= args.limit:
                break

            sample_record = make_sample_record(sample, split)
            write_jsonl_record(sample_jsonl, sample_record)

            sample_count += 1
            context_doc_count += sample_record["context_count"]
            supporting_fact_count += sample_record["supporting_fact_count"]
            evidence_count += sample_record["evidence_count"]

    stats = {
        "split": split,
        "sample_count": sample_count,
        "context_doc_count": context_doc_count,
        "supporting_fact_count": supporting_fact_count,
        "evidence_count": evidence_count,
        "output_file": str(sample_jsonl_path),
    }

    with stats_path.open("w", encoding="utf-8") as stats_handle:
        json.dump(stats, stats_handle, indent=2, ensure_ascii=False)

    print(
        f"Processed {sample_count} {split} samples "
        f"with {context_doc_count} context docs, "
        f"{supporting_fact_count} supporting facts, "
        f"and {evidence_count} evidences."
    )
    print(f"Wrote outputs to {output_dir}")


if __name__ == "__main__":
    main()
