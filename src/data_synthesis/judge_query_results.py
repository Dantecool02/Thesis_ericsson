"""
Incrementally judge LightRAG query results into three routing classes.

This script reads query outputs produced by query_lightrag.py, sends the
question together with the Naive and Mix answers to Gemini, and writes one
judgment row per sample to a separate JSONL file. It is resumable: already
judged sample_ids are skipped on later runs.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from dotenv import load_dotenv
from lightrag.llm.gemini import gemini_model_complete

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_JSONL = Path("data/processed/2wiki/progress/query_results.jsonl")
DEFAULT_OUTPUT_JSONL = Path("data/processed/2wiki/progress/router_judgments.jsonl")
DEFAULT_LLM_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-3-flash-preview")

CLASS_NAIVE_ENOUGH = "naive_enough"
CLASS_MIX_REQUIRED = "mix_required"
CLASS_NONE_ENOUGH = "none_enough"
VALID_CLASSES = {
    CLASS_NAIVE_ENOUGH,
    CLASS_MIX_REQUIRED,
    CLASS_NONE_ENOUGH,
}

JUDGE_SYSTEM_PROMPT = f"""You are a strict evaluator for a retrieval-routing dataset.

You must output exactly one class label and nothing else.

Allowed labels:
- {CLASS_NAIVE_ENOUGH}
- {CLASS_MIX_REQUIRED}
- {CLASS_NONE_ENOUGH}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Judge LightRAG query results into three routing classes."
    )
    parser.add_argument("--input-jsonl", type=Path, default=DEFAULT_INPUT_JSONL)
    parser.add_argument("--output-jsonl", type=Path, default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument(
        "--max-items",
        type=int,
        default=10,
        help="Maximum number of new query results to judge this run.",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Skip this many unjudged items before starting.",
    )
    parser.add_argument(
        "--llm-model",
        default=DEFAULT_LLM_MODEL,
        help="Gemini model to use for judging.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=1.0,
        help="Pause between judgments to reduce rate-limit pressure.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retries when the judge response is malformed or the API fails.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview which rows would be judged without calling Gemini.",
    )
    return parser.parse_args()


def ensure_credentials() -> None:
    use_vertexai = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true"
    if use_vertexai:
        if not os.getenv("GOOGLE_CLOUD_PROJECT"):
            raise ValueError("GOOGLE_CLOUD_PROJECT must be set when using Vertex AI mode.")
        return

    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY not found in environment variables.")


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            yield json.loads(line)


def load_processed_sample_ids(output_jsonl: Path) -> set[str]:
    if not output_jsonl.exists():
        return set()

    processed: set[str] = set()
    for row in iter_jsonl(output_jsonl):
        sample_id = row.get("sample_id")
        if sample_id:
            processed.add(sample_id)
    return processed


def select_rows(
    input_jsonl: Path,
    processed_sample_ids: set[str],
    max_items: int,
    offset: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    skipped = 0

    for row in iter_jsonl(input_jsonl):
        sample_id = row["sample_id"]
        if sample_id in processed_sample_ids:
            continue

        if skipped < offset:
            skipped += 1
            continue

        selected.append(row)
        if len(selected) >= max_items:
            break

    return selected


def build_judge_prompt(query_result: dict[str, Any]) -> str:
    payload = {
        "question": query_result.get("question"),
        "ground_truth_answer": query_result.get("ground_truth"),
        "naive_answer": query_result.get("naive_answer"),
        "mix_answer": query_result.get("mix_answer"),
    }

    return f"""Classify this example into exactly one of these labels:

- {CLASS_NAIVE_ENOUGH}: the Naive answer was already enough to answer the question correctly.
- {CLASS_MIX_REQUIRED}: the Naive answer was not enough, but the Mix answer provided more context that led to a correct answer.
- {CLASS_NONE_ENOUGH}: neither answer was enough.

Rules:
1. Output exactly one label and nothing else.
2. Do not output JSON.
3. Do not explain your choice.
4. Use the ground-truth answer to judge correctness when it is provided.
5. A longer answer is not better just because it is longer.
6. If both Naive and Mix are correct, choose {CLASS_NAIVE_ENOUGH}.
7. If Naive is wrong or insufficient and Mix is correct, choose {CLASS_MIX_REQUIRED}.
8. If both are wrong, insufficient, or clearly fail to answer, choose {CLASS_NONE_ENOUGH}.
9. Treat explicit admissions of missing information and obvious error messages as not enough.

Example:
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""


def normalize_label(raw_text: str) -> str:
    cleaned = raw_text.strip().lower()
    cleaned = re.sub(r"^```(?:text|json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    cleaned = cleaned.replace('"', "").replace("'", "").strip()

    if cleaned in VALID_CLASSES:
        return cleaned

    match = re.search(
        rf"\b({CLASS_NAIVE_ENOUGH}|{CLASS_MIX_REQUIRED}|{CLASS_NONE_ENOUGH})\b",
        cleaned,
    )
    if match:
        return match.group(1)

    raise ValueError(f"Judge returned invalid class label: {raw_text!r}")


async def judge_with_retry(
    prompt: str,
    model_name: str,
    max_retries: int,
) -> tuple[str, str]:
    last_error = None

    for attempt in range(max_retries):
        try:
            raw = await gemini_model_complete(
                prompt,
                system_prompt=JUDGE_SYSTEM_PROMPT,
                history_messages=[],
                model_name=model_name,
                temperature=0.0,
            )
            return normalize_label(raw), raw
        except Exception as exc:
            last_error = exc
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
                continue
            raise RuntimeError(f"Judge failed after {max_retries} attempts: {exc}") from exc

    raise RuntimeError(f"Judge failed unexpectedly: {last_error}")


def append_result(output_jsonl: Path, record: dict[str, Any]) -> None:
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with output_jsonl.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


async def main() -> None:
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
    args = parse_args()

    if not args.input_jsonl.exists():
        raise FileNotFoundError(f"Input query-results file not found: {args.input_jsonl}")

    processed_sample_ids = load_processed_sample_ids(args.output_jsonl)
    rows = select_rows(
        args.input_jsonl,
        processed_sample_ids=processed_sample_ids,
        max_items=args.max_items,
        offset=args.offset,
    )

    print(f"Already judged rows: {len(processed_sample_ids):,}")
    print(f"Selected rows for this run: {len(rows):,}")
    print(f"Input file: {args.input_jsonl}")
    print(f"Output file: {args.output_jsonl}")
    print(f"Judge model: {args.llm_model}")

    if not rows:
        print("No new rows selected. Exiting.")
        return

    for idx, row in enumerate(rows[:5], start=1):
        print(f"  Preview {idx}: {row['sample_id']} | {row['question']}")

    if args.dry_run:
        print("\nDry run only. No judge calls were executed.")
        return

    ensure_credentials()

    total = len(rows)
    for index, row in enumerate(rows, start=1):
        sample_id = row["sample_id"]
        print(f"\n[{index}/{total}] sample={sample_id}")
        print(f"  Question: {row['question']}")

        prompt = build_judge_prompt(row)
        class_label, raw_response = await judge_with_retry(
            prompt=prompt,
            model_name=args.llm_model,
            max_retries=args.max_retries,
        )

        result = {
            "sample_id": sample_id,
            "split": row.get("split"),
            "question_type": row.get("question_type"),
            "question": row.get("question"),
            "ground_truth": row.get("ground_truth"),
            "naive_answer": row.get("naive_answer"),
            "mix_answer": row.get("mix_answer"),
            "judge_model": args.llm_model,
            "judge_class": class_label,
            "judged_at": datetime.now(timezone.utc).isoformat(),
            "raw_judge_response": raw_response,
        }
        append_result(args.output_jsonl, result)

        print(f"  Class: {class_label}")

        if args.sleep_seconds > 0:
            await asyncio.sleep(args.sleep_seconds)

    print(f"\nFinished. Judgments appended to {args.output_jsonl}")


if __name__ == "__main__":
    asyncio.run(main())
