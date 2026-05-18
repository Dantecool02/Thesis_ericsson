"""
Measure query-time token usage for LightRAG naive and mix modes.

This script reuses the already-built 2Wiki LightRAG index, runs a small number
of questions through both retrieval modes, and stores per-mode token accounting.

Token accounting:
  - LLM generation tokens come from Gemini API usage metadata.
  - Embedding tokens are recorded from Gemini metadata when available; otherwise
    a tiktoken estimate is stored separately.
  - LightRAG's LLM cache is disabled so reruns measure actual model calls.

Typical use:
  ./venv/bin/python src/data_synthesis/query_lightrag_token_usage.py --max-queries 5
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from dotenv import load_dotenv
from lightrag import LightRAG, QueryParam
from lightrag.llm.gemini import gemini_embed, gemini_model_complete
from lightrag.utils import TiktokenTokenizer, wrap_embedding_func_with_attrs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_JSONL = Path("data/processed/2wiki/progress/queryable_samples.jsonl")
DEFAULT_OUTPUT_JSONL = Path("data/processed/2wiki/progress/query_token_usage.jsonl")
DEFAULT_WORKING_DIR = Path("data/index/2wiki")
DEFAULT_LLM_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-3-flash-preview")
DEFAULT_EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "models/gemini-embedding-001",
)
DEFAULT_TIKTOKEN_MODEL = os.getenv("TIKTOKEN_MODEL_NAME", "gpt-4o-mini")


class SingleCallTokenTracker:
    """Small adapter for LightRAG Gemini token_tracker hooks."""

    def __init__(self) -> None:
        self.usage: dict[str, int] | None = None

    def add_usage(self, token_counts: dict[str, int]) -> None:
        self.usage = {
            "prompt_tokens": int(token_counts.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(token_counts.get("completion_tokens", 0) or 0),
            "total_tokens": int(token_counts.get("total_tokens", 0) or 0),
        }


@dataclass
class UsageRecorder:
    tokenizer: TiktokenTokenizer
    tiktoken_model: str
    current_sample_id: str | None = None
    current_mode: str | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)

    def set_scope(self, sample_id: str, mode: str) -> None:
        self.current_sample_id = sample_id
        self.current_mode = mode

    def clear_scope(self) -> None:
        self.current_sample_id = None
        self.current_mode = None

    def estimate_tokens(self, text: str | None) -> int:
        if not text:
            return 0
        return len(self.tokenizer.encode(text))

    def add_llm_call(
        self,
        *,
        model: str,
        purpose: str,
        prompt: str,
        system_prompt: str | None,
        history_messages: list[dict[str, Any]] | None,
        api_usage: dict[str, int] | None,
        latency_seconds: float,
    ) -> None:
        history_text = "\n".join(
            f"[{message.get('role', 'user')}] {message.get('content', '')}"
            for message in (history_messages or [])
        )
        estimated_input_tokens = (
            self.estimate_tokens(prompt)
            + self.estimate_tokens(system_prompt)
            + self.estimate_tokens(history_text)
        )
        self.calls.append(
            {
                "component": "llm",
                "sample_id": self.current_sample_id,
                "mode": self.current_mode,
                "purpose": purpose,
                "model": model,
                "api_reported": api_usage is not None,
                "api_prompt_tokens": (api_usage or {}).get("prompt_tokens"),
                "api_completion_tokens": (api_usage or {}).get("completion_tokens"),
                "api_total_tokens": (api_usage or {}).get("total_tokens"),
                "estimated_input_tokens": estimated_input_tokens,
                "tiktoken_model": self.tiktoken_model,
                "prompt_char_count": len(prompt or ""),
                "system_prompt_char_count": len(system_prompt or ""),
                "history_message_count": len(history_messages or []),
                "latency_seconds": latency_seconds,
            }
        )

    def add_embedding_call(
        self,
        *,
        model: str,
        texts: list[str],
        api_usage: dict[str, int] | None,
        latency_seconds: float,
    ) -> None:
        estimated_input_tokens = sum(self.estimate_tokens(text) for text in texts)
        self.calls.append(
            {
                "component": "embedding",
                "sample_id": self.current_sample_id,
                "mode": self.current_mode,
                "purpose": "retrieval_embedding",
                "model": model,
                "api_reported": api_usage is not None,
                "api_prompt_tokens": (api_usage or {}).get("prompt_tokens"),
                "api_completion_tokens": (api_usage or {}).get("completion_tokens"),
                "api_total_tokens": (api_usage or {}).get("total_tokens"),
                "estimated_input_tokens": estimated_input_tokens,
                "tiktoken_model": self.tiktoken_model,
                "batch_size": len(texts),
                "text_char_count": sum(len(text) for text in texts),
                "latency_seconds": latency_seconds,
            }
        )

    def calls_for(self, sample_id: str, mode: str) -> list[dict[str, Any]]:
        return [
            call
            for call in self.calls
            if call.get("sample_id") == sample_id and call.get("mode") == mode
        ]

    @staticmethod
    def summarize_calls(calls: list[dict[str, Any]]) -> dict[str, Any]:
        llm_calls = [call for call in calls if call["component"] == "llm"]
        embedding_calls = [call for call in calls if call["component"] == "embedding"]
        llm_api_calls = [call for call in llm_calls if call["api_reported"]]
        embedding_api_calls = [
            call for call in embedding_calls if call["api_reported"]
        ]

        return {
            "llm_call_count": len(llm_calls),
            "llm_api_reported_call_count": len(llm_api_calls),
            "llm_prompt_tokens": sum(
                call.get("api_prompt_tokens") or 0 for call in llm_api_calls
            ),
            "llm_completion_tokens": sum(
                call.get("api_completion_tokens") or 0 for call in llm_api_calls
            ),
            "llm_total_tokens": sum(
                call.get("api_total_tokens") or 0 for call in llm_api_calls
            ),
            "llm_estimated_input_tokens": sum(
                call.get("estimated_input_tokens") or 0 for call in llm_calls
            ),
            "embedding_call_count": len(embedding_calls),
            "embedding_api_reported_call_count": len(embedding_api_calls),
            "embedding_prompt_tokens": sum(
                call.get("api_prompt_tokens") or 0 for call in embedding_api_calls
            ),
            "embedding_total_tokens": sum(
                call.get("api_total_tokens") or 0 for call in embedding_api_calls
            ),
            "embedding_estimated_input_tokens": sum(
                call.get("estimated_input_tokens") or 0 for call in embedding_calls
            ),
            "total_api_reported_tokens": sum(
                call.get("api_total_tokens") or 0
                for call in calls
                if call["api_reported"]
            ),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a small LightRAG token-usage measurement for naive and mix."
    )
    parser.add_argument("--input-jsonl", type=Path, default=DEFAULT_INPUT_JSONL)
    parser.add_argument("--output-jsonl", type=Path, default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--working-dir", type=Path, default=DEFAULT_WORKING_DIR)
    parser.add_argument("--max-queries", type=int, default=5)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="top_k for naive and chunk_top_k for mix. Defaults to the existing run setting.",
    )
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--llm-model", default=DEFAULT_LLM_MODEL)
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--llm-max-async", type=int, default=4)
    parser.add_argument("--embedding-batch-num", type=int, default=32)
    parser.add_argument("--embedding-max-async", type=int, default=16)
    parser.add_argument("--tiktoken-model", default=DEFAULT_TIKTOKEN_MODEL)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview selected queries without calling Gemini.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Process selected sample_ids even if they already exist in the output JSONL.",
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


def select_queries(
    input_jsonl: Path,
    processed_sample_ids: set[str],
    max_queries: int,
    offset: int,
    force: bool,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    skipped = 0

    for row in iter_jsonl(input_jsonl):
        sample_id = row["sample_id"]
        if not force and sample_id in processed_sample_ids:
            continue

        if skipped < offset:
            skipped += 1
            continue

        selected.append(row)
        if len(selected) >= max_queries:
            break

    return selected


def make_embedding_func(model_name: str, usage: UsageRecorder):
    @wrap_embedding_func_with_attrs(
        embedding_dim=768,
        send_dimensions=True,
        max_token_size=2048,
        model_name=model_name,
    )
    async def embedding_func(texts: list[str], **kwargs) -> list[float]:
        call_tracker = SingleCallTokenTracker()
        start_time = time.time()
        result = await gemini_embed.func(
            texts=texts,
            model=model_name,
            token_tracker=call_tracker,
            **kwargs,
        )
        usage.add_embedding_call(
            model=model_name,
            texts=texts,
            api_usage=call_tracker.usage,
            latency_seconds=time.time() - start_time,
        )
        return result

    return embedding_func


def make_llm_model_func(model_name: str, usage: UsageRecorder):
    async def llm_model_func(
        prompt: str,
        system_prompt: str | None = None,
        history_messages: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> str:
        purpose = "keyword_extraction" if kwargs.get("keyword_extraction") else "answer_generation"
        call_tracker = SingleCallTokenTracker()
        start_time = time.time()
        result = await gemini_model_complete(
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages or [],
            model_name=model_name,
            token_tracker=call_tracker,
            **kwargs,
        )
        usage.add_llm_call(
            model=model_name,
            purpose=purpose,
            prompt=prompt,
            system_prompt=system_prompt,
            history_messages=history_messages or [],
            api_usage=call_tracker.usage,
            latency_seconds=time.time() - start_time,
        )
        return result

    return llm_model_func


def build_rag(args: argparse.Namespace, usage: UsageRecorder) -> LightRAG:
    return LightRAG(
        working_dir=str(args.working_dir),
        llm_model_func=make_llm_model_func(args.llm_model, usage),
        llm_model_name=args.llm_model,
        llm_model_max_async=args.llm_max_async,
        llm_model_kwargs={"temperature": 0.0},
        embedding_func=make_embedding_func(args.embedding_model, usage),
        embedding_batch_num=args.embedding_batch_num,
        embedding_func_max_async=args.embedding_max_async,
        tiktoken_model_name=args.tiktoken_model,
        enable_llm_cache=False,
    )


async def query_with_retry(
    rag: LightRAG,
    query: str,
    param: QueryParam,
    max_retries: int,
) -> str:
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return await rag.aquery(query, param=param)
        except Exception as exc:
            last_error = exc
            print(f"    Error during {param.mode} query: {exc}")
            if attempt < max_retries:
                print("    Retrying in 5 seconds...")
                await asyncio.sleep(5)

    return f"ERROR: Failed after {max_retries} attempts. Details: {last_error}"


def append_result(output_jsonl: Path, record: dict[str, Any]) -> None:
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with output_jsonl.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


async def run_mode(
    *,
    rag: LightRAG,
    usage: UsageRecorder,
    sample_id: str,
    mode: str,
    question: str,
    top_k: int,
    max_retries: int,
) -> dict[str, Any]:
    usage.set_scope(sample_id, mode)
    start_time = time.time()
    if mode == "naive":
        answer = await query_with_retry(
            rag,
            question,
            param=QueryParam(mode="naive", top_k=top_k, chunk_top_k=top_k),
            max_retries=max_retries,
        )
    elif mode == "mix":
        answer = await query_with_retry(
            rag,
            question,
            param=QueryParam(mode="mix", chunk_top_k=top_k),
            max_retries=max_retries,
        )
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    elapsed = time.time() - start_time
    calls = usage.calls_for(sample_id, mode)
    usage.clear_scope()
    return {
        "answer": answer,
        "time_seconds": elapsed,
        "usage_summary": UsageRecorder.summarize_calls(calls),
        "usage_calls": calls,
    }


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
        force=args.force,
    )

    print(f"Already measured samples: {len(processed_sample_ids):,}")
    print(f"Selected queries for this run: {len(queries):,}")
    print(f"Input file: {args.input_jsonl}")
    print(f"Output file: {args.output_jsonl}")
    print(f"LightRAG working dir: {args.working_dir}")
    print(f"LLM model: {args.llm_model}")
    print(f"Embedding model: {args.embedding_model}")
    print(f"top_k/chunk_top_k: {args.top_k}")
    print("LLM cache: disabled for measurement")

    if not queries:
        print("No queries selected. Exiting.")
        return

    for idx, row in enumerate(queries[:5], start=1):
        print(f"  Preview {idx}: {row['sample_id']} | {row['question']}")

    if args.dry_run:
        print("\nDry run only. No LightRAG queries were executed.")
        return

    ensure_credentials()
    usage = UsageRecorder(
        tokenizer=TiktokenTokenizer(args.tiktoken_model),
        tiktoken_model=args.tiktoken_model,
    )
    rag = build_rag(args, usage)

    print("\nInitializing LightRAG storages...")
    await rag.initialize_storages()

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    total = len(queries)
    for index, item in enumerate(queries, start=1):
        sample_id = item["sample_id"]
        question = item["question"]
        print(f"\n[{index}/{total}] sample={sample_id}")
        print(f"  Query: {question}")

        print(f"  Running Naive RAG (top_k={args.top_k})...")
        naive = await run_mode(
            rag=rag,
            usage=usage,
            sample_id=sample_id,
            mode="naive",
            question=question,
            top_k=args.top_k,
            max_retries=args.max_retries,
        )
        print(
            "  Naive tokens: "
            f"LLM total={naive['usage_summary']['llm_total_tokens']}, "
            f"embedding est={naive['usage_summary']['embedding_estimated_input_tokens']}"
        )

        print(f"  Running Mix RAG (chunk_top_k={args.top_k})...")
        mix = await run_mode(
            rag=rag,
            usage=usage,
            sample_id=sample_id,
            mode="mix",
            question=question,
            top_k=args.top_k,
            max_retries=args.max_retries,
        )
        print(
            "  Mix tokens: "
            f"LLM total={mix['usage_summary']['llm_total_tokens']}, "
            f"embedding est={mix['usage_summary']['embedding_estimated_input_tokens']}"
        )

        record = {
            "run_id": run_id,
            "sample_id": sample_id,
            "split": item.get("split"),
            "question_type": item.get("question_type"),
            "question": question,
            "ground_truth": item.get("answer"),
            "answer_available": item.get("answer_available"),
            "context_count": item.get("context_count"),
            "supporting_fact_count": item.get("supporting_fact_count"),
            "supporting_doc_ids": item.get("supporting_doc_ids"),
            "top_k": args.top_k,
            "llm_model": args.llm_model,
            "embedding_model": args.embedding_model,
            "tiktoken_model": args.tiktoken_model,
            "measurement_notes": {
                "llm_token_source": "Gemini API usage_metadata",
                "embedding_token_source": (
                    "Gemini usage_metadata when present; otherwise tiktoken estimate"
                ),
                "llm_cache_enabled": False,
            },
            "measured_at": datetime.now(timezone.utc).isoformat(),
            "naive": naive,
            "mix": mix,
        }
        append_result(args.output_jsonl, record)

        if args.sleep_seconds > 0:
            await asyncio.sleep(args.sleep_seconds)

    print(f"\nFinished. Token usage appended to {args.output_jsonl}")


if __name__ == "__main__":
    asyncio.run(main())
