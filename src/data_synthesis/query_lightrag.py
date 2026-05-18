"""
Query the 2Wiki LightRAG index with both naive and mix modes.

This script is aligned with the sample-first 2Wiki pipeline:
  - input questions come from queryable_samples.jsonl
  - the LightRAG working dir defaults to data/index/2wiki
  - results are written incrementally to JSONL so resume is straightforward

Typical use:
  ./venv/bin/python src/data_synthesis/query_lightrag.py --max-queries 10
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Iterator

from dotenv import load_dotenv
from lightrag import LightRAG, QueryParam
from lightrag.llm.gemini import gemini_embed, gemini_model_complete
from lightrag.utils import wrap_embedding_func_with_attrs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_JSONL = Path("data/processed/2wiki/progress/queryable_samples.jsonl")
DEFAULT_OUTPUT_JSONL = Path("data/processed/2wiki/progress/query_results.jsonl")
DEFAULT_WORKING_DIR = Path("data/index/2wiki")
DEFAULT_LLM_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-3-flash-preview")
DEFAULT_EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "models/gemini-embedding-001",
)
DEFAULT_TIKTOKEN_MODEL = os.getenv("TIKTOKEN_MODEL_NAME", "gpt-4o-mini")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query the 2Wiki LightRAG index with naive and mix retrieval."
    )
    parser.add_argument("--input-jsonl", type=Path, default=DEFAULT_INPUT_JSONL)
    parser.add_argument("--output-jsonl", type=Path, default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--working-dir", type=Path, default=DEFAULT_WORKING_DIR)
    parser.add_argument(
        "--max-queries",
        type=int,
        default=10,
        help="Maximum number of new queryable samples to process this run.",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Skip this many unprocessed queryable samples before starting.",
    )
    parser.add_argument(
        "--naive-top-k",
        type=int,
        default=3,
        help="top_k to use for naive/vector-only retrieval.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=1.0,
        help="Pause between queries to reduce rate-limit pressure.",
    )
    parser.add_argument(
        "--llm-model",
        default=DEFAULT_LLM_MODEL,
        help="Gemini LLM model to use for query-time generation.",
    )
    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help="Gemini embedding model to use for query-time retrieval.",
    )
    parser.add_argument("--llm-max-async", type=int, default=4)
    parser.add_argument("--embedding-batch-num", type=int, default=32)
    parser.add_argument("--embedding-max-async", type=int, default=16)
    parser.add_argument(
        "--tiktoken-model",
        default=DEFAULT_TIKTOKEN_MODEL,
        help="Tokenizer model name passed to LightRAG chunking.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview which queries would run without calling Gemini.",
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


def make_embedding_func(model_name: str):
    @wrap_embedding_func_with_attrs(
        embedding_dim=768,
        send_dimensions=True,
        max_token_size=2048,
        model_name=model_name,
    )
    async def embedding_func(texts: list[str], **kwargs) -> list[float]:
        return await gemini_embed.func(
            texts=texts,
            model=model_name,
            **kwargs,
        )

    return embedding_func


def make_llm_model_func(model_name: str):
    async def llm_model_func(
        prompt: str,
        system_prompt: str | None = None,
        history_messages: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> str:
        return await gemini_model_complete(
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages or [],
            model_name=model_name,
            **kwargs,
        )

    return llm_model_func


def build_rag(args: argparse.Namespace) -> LightRAG:
    return LightRAG(
        working_dir=str(args.working_dir),
        llm_model_func=make_llm_model_func(args.llm_model),
        llm_model_name=args.llm_model,
        llm_model_max_async=args.llm_max_async,
        llm_model_kwargs={"temperature": 0.0},
        embedding_func=make_embedding_func(args.embedding_model),
        embedding_batch_num=args.embedding_batch_num,
        embedding_func_max_async=args.embedding_max_async,
        tiktoken_model_name=args.tiktoken_model,
    )


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


def select_queries(
    input_jsonl: Path,
    processed_sample_ids: set[str],
    max_queries: int,
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
        if len(selected) >= max_queries:
            break

    return selected


async def query_with_retry(
    rag: LightRAG,
    query: str,
    param: QueryParam,
    max_retries: int = 3,
) -> str:
    for attempt in range(max_retries):
        try:
            return await rag.aquery(query, param=param)
        except Exception as exc:
            print(f"    Error during {param.mode} query: {exc}")
            if attempt < max_retries - 1:
                print("    Retrying in 5 seconds...")
                await asyncio.sleep(5)
            else:
                print(f"    Failed after {max_retries} attempts.")
                return f"ERROR: Failed after {max_retries} attempts. Details: {exc}"


def append_result(output_jsonl: Path, record: dict[str, Any]) -> None:
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with output_jsonl.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


async def main() -> None:
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
    args = parse_args()

    if not args.input_jsonl.exists():
        raise FileNotFoundError(f"Input query file not found: {args.input_jsonl}")
    if not args.working_dir.exists():
        raise FileNotFoundError(
            f"Working directory {args.working_dir} not found. Run the 2Wiki indexer first."
        )

    processed_sample_ids = load_processed_sample_ids(args.output_jsonl)
    queries = select_queries(
        args.input_jsonl,
        processed_sample_ids=processed_sample_ids,
        max_queries=args.max_queries,
        offset=args.offset,
    )

    print(f"Already processed queries: {len(processed_sample_ids):,}")
    print(f"Selected queries for this run: {len(queries):,}")
    print(f"Input file: {args.input_jsonl}")
    print(f"Output file: {args.output_jsonl}")
    print(f"LightRAG working dir: {args.working_dir}")
    print(f"LLM model: {args.llm_model}")
    print(f"Embedding model: {args.embedding_model}")

    if not queries:
        print("No new queries selected. Exiting.")
        return

    for idx, row in enumerate(queries[:5], start=1):
        print(f"  Preview {idx}: {row['sample_id']} | {row['question']}")

    if args.dry_run:
        print("\nDry run only. No LightRAG queries were executed.")
        return

    ensure_credentials()
    rag = build_rag(args)
    print("\nInitializing LightRAG storages...")
    await rag.initialize_storages()

    total = len(queries)
    for index, item in enumerate(queries, start=1):
        query = item["question"]
        print(f"\n[{index}/{total}] sample={item['sample_id']}")
        print(f"  Query: {query}")

        print(f"  Running Naive RAG (top_k={args.naive_top_k})...")
        start_time = time.time()
        naive_answer = await query_with_retry(
            rag,
            query,
            param=QueryParam(
                mode="naive",
                top_k=args.naive_top_k,
                chunk_top_k=args.naive_top_k,
            ),
        )
        naive_time = time.time() - start_time
        print(f"  Naive Time: {naive_time:.2f}s")

        print("  Running Mix RAG...")
        start_time = time.time()
        mix_answer = await query_with_retry(
            rag,
            query,
            param=QueryParam(mode="mix", chunk_top_k=args.naive_top_k),
        )
        mix_time = time.time() - start_time
        print(f"  Mix Time: {mix_time:.2f}s")

        result = {
            "sample_id": item["sample_id"],
            "split": item.get("split"),
            "question_type": item.get("question_type"),
            "question": query,
            "ground_truth": item.get("answer"),
            "answer_available": item.get("answer_available"),
            "context_count": item.get("context_count"),
            "supporting_fact_count": item.get("supporting_fact_count"),
            "supporting_doc_ids": item.get("supporting_doc_ids"),
            "naive_top_k": args.naive_top_k,
            "naive_answer": naive_answer,
            "mix_answer": mix_answer,
            "naive_time_seconds": naive_time,
            "mix_time_seconds": mix_time,
        }
        append_result(args.output_jsonl, result)

        if args.sleep_seconds > 0:
            await asyncio.sleep(args.sleep_seconds)

    print(f"\nFinished. Results appended to {args.output_jsonl}")


if __name__ == "__main__":
    asyncio.run(main())
