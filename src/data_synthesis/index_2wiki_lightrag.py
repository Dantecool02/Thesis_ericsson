"""
Index the processed 2Wiki samples into LightRAG in original sample order.

The input is a sample-preserving JSONL export:
  data/processed/2wiki/samples/train_samples.jsonl

Each row contains one original 2Wiki sample with its question, answer,
supporting facts, evidences, and full inline context docs. The indexer walks
those rows sequentially, de-duplicates docs internally, and tracks both:
  - which docs have been indexed
  - which samples are now fully queryable
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from dotenv import load_dotenv
from lightrag import LightRAG
from lightrag.llm.gemini import gemini_embed, gemini_model_complete
from lightrag.utils import wrap_embedding_func_with_attrs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_JSONL = Path("data/processed/2wiki/samples/train_samples.jsonl")
DEFAULT_WORKING_DIR = Path("data/index/2wiki")
DEFAULT_DOC_TRACKING_FILE = Path("data/processed/2wiki/progress/indexed_docs.jsonl")
DEFAULT_SAMPLE_TRACKING_FILE = Path(
    "data/processed/2wiki/progress/queryable_samples.jsonl"
)
DEFAULT_LLM_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-3-flash-preview")
DEFAULT_EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "models/gemini-embedding-001",
)
DEFAULT_TIKTOKEN_MODEL = os.getenv("TIKTOKEN_MODEL_NAME", "gpt-4o-mini")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Index 2Wiki samples in order while tracking which samples are queryable."
    )
    parser.add_argument("--input-jsonl", type=Path, default=DEFAULT_INPUT_JSONL)
    parser.add_argument("--working-dir", type=Path, default=DEFAULT_WORKING_DIR)
    parser.add_argument(
        "--doc-tracking-file",
        type=Path,
        default=DEFAULT_DOC_TRACKING_FILE,
        help="Append-only JSONL file for indexed docs.",
    )
    parser.add_argument(
        "--sample-tracking-file",
        type=Path,
        default=DEFAULT_SAMPLE_TRACKING_FILE,
        help="Append-only JSONL file for samples that are now safe to query.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Number of samples to process per batch, in original sample order.",
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=None,
        help="Optional cap on batches for this run.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Optional cap on how many not-yet-queryable samples to process.",
    )
    parser.add_argument(
        "--llm-model",
        default=DEFAULT_LLM_MODEL,
        help="Gemini LLM model to use for LightRAG graph extraction.",
    )
    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help="Gemini embedding model to use for vector indexing.",
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
        help="Preview the first prepared sample batch without calling the Gemini API.",
    )
    return parser.parse_args()


def ensure_credentials_if_needed(dry_run: bool) -> None:
    if dry_run:
        return

    use_vertexai = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true"
    if use_vertexai:
        if not os.getenv("GOOGLE_CLOUD_PROJECT"):
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT must be set when using Vertex AI mode."
            )
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


def load_ids(tracking_file: Path, key: str) -> set[str]:
    if not tracking_file.exists():
        return set()

    loaded_ids: set[str] = set()
    with tracking_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            value = row.get(key)
            if value:
                loaded_ids.add(value)
    return loaded_ids


def iter_pending_samples(
    input_jsonl: Path,
    indexed_sample_ids: set[str],
    max_samples: int | None,
) -> Iterator[dict[str, Any]]:
    yielded = 0
    with input_jsonl.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            sample_id = row["sample_id"]
            if sample_id in indexed_sample_ids:
                continue
            yield row
            yielded += 1
            if max_samples is not None and yielded >= max_samples:
                return


def batch_iterator(
    samples: Iterator[dict[str, Any]],
    batch_size: int,
    max_batches: int | None,
) -> Iterator[list[dict[str, Any]]]:
    batch: list[dict[str, Any]] = []
    batches_yielded = 0

    for sample in samples:
        batch.append(sample)
        if len(batch) < batch_size:
            continue

        yield batch
        batches_yielded += 1
        if max_batches is not None and batches_yielded >= max_batches:
            return
        batch = []

    if batch and (max_batches is None or batches_yielded < max_batches):
        yield batch


def prepare_batch(
    batch_samples: list[dict[str, Any]],
    indexed_doc_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    new_docs: list[dict[str, Any]] = []
    seen_doc_ids = set(indexed_doc_ids)
    prepared_samples: list[dict[str, Any]] = []

    for sample in batch_samples:
        sample_new_doc_ids: list[str] = []
        for doc in sample.get("context_docs", []):
            doc_id = doc["doc_id"]
            if doc_id in seen_doc_ids:
                continue
            seen_doc_ids.add(doc_id)
            sample_new_doc_ids.append(doc_id)
            new_docs.append(doc)

        prepared_samples.append(
            {
                "sample_id": sample["sample_id"],
                "split": sample["split"],
                "question_type": sample["question_type"],
                "question": sample["question"],
                "answer": sample.get("answer"),
                "answer_available": sample.get("answer_available", False),
                "context_count": sample["context_count"],
                "context_doc_ids": sample["context_doc_ids"],
                "supporting_fact_count": sample["supporting_fact_count"],
                "supporting_doc_ids": sample["supporting_doc_ids"],
                "new_doc_ids": sample_new_doc_ids,
                "new_doc_count": len(sample_new_doc_ids),
            }
        )

    return new_docs, prepared_samples


def print_batch_preview(
    batch_samples: list[dict[str, Any]],
    new_docs: list[dict[str, Any]],
) -> None:
    print(
        f"\nPrepared first 2Wiki sample batch of {len(batch_samples)} sample(s) "
        f"with {len(new_docs)} new doc(s)."
    )
    for sample in batch_samples[:5]:
        print(
            f"  sample={sample['sample_id']} | type={sample['question_type']} | "
            f"context_docs={sample['context_count']} | question={sample['question']}"
        )
    if len(batch_samples) > 5:
        print(f"  ... plus {len(batch_samples) - 5} more sample(s)")

    if new_docs:
        char_counts = [doc["char_count"] for doc in new_docs]
        print(
            "New doc char stats:"
            f" min={min(char_counts):,}"
            f" avg={sum(char_counts) / len(char_counts):.1f}"
            f" max={max(char_counts):,}"
        )


async def insert_docs(
    rag: LightRAG,
    docs: list[dict[str, Any]],
    batch_number: int,
    max_retries: int = 3,
) -> None:
    if not docs:
        print(f"Batch {batch_number}: all docs already existed, nothing to insert.")
        return

    texts = [doc["text"] for doc in docs]
    ids = [doc["doc_id"] for doc in docs]
    file_paths = [doc["file_path"] for doc in docs]

    for attempt in range(1, max_retries + 1):
        try:
            print(
                f"Indexing sample batch {batch_number} with {len(docs)} new doc(s) "
                f"(attempt {attempt}/{max_retries})..."
            )
            await rag.ainsert(texts, ids=ids, file_paths=file_paths)
            return
        except Exception as exc:
            print(f"  Batch insert failed: {exc}")
            if attempt == max_retries:
                raise
            await asyncio.sleep(10)


def append_doc_tracking(
    tracking_file: Path,
    docs: list[dict[str, Any]],
    batch_number: int,
) -> None:
    if not docs:
        return

    indexed_at = datetime.now(timezone.utc).isoformat()
    with tracking_file.open("a", encoding="utf-8") as handle:
        for doc in docs:
            handle.write(
                json.dumps(
                    {
                        "doc_id": doc["doc_id"],
                        "title": doc["title"],
                        "split": doc["split"],
                        "char_count": doc["char_count"],
                        "sentence_count": doc["sentence_count"],
                        "file_path": doc["file_path"],
                        "batch_number": batch_number,
                        "indexed_at": indexed_at,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def append_sample_tracking(
    tracking_file: Path,
    samples: list[dict[str, Any]],
    batch_number: int,
) -> None:
    indexed_at = datetime.now(timezone.utc).isoformat()
    with tracking_file.open("a", encoding="utf-8") as handle:
        for sample in samples:
            handle.write(
                json.dumps(
                    {
                        **sample,
                        "batch_number": batch_number,
                        "indexed_at": indexed_at,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


async def main() -> None:
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
    args = parse_args()
    ensure_credentials_if_needed(args.dry_run)

    if not args.input_jsonl.exists():
        raise FileNotFoundError(f"Input sample file not found: {args.input_jsonl}")

    args.working_dir.mkdir(parents=True, exist_ok=True)
    args.doc_tracking_file.parent.mkdir(parents=True, exist_ok=True)
    args.sample_tracking_file.parent.mkdir(parents=True, exist_ok=True)

    indexed_doc_ids = load_ids(args.doc_tracking_file, "doc_id")
    indexed_sample_ids = load_ids(args.sample_tracking_file, "sample_id")

    print(f"Already indexed docs: {len(indexed_doc_ids):,}")
    print(f"Already queryable samples: {len(indexed_sample_ids):,}")
    print(f"Reading samples from: {args.input_jsonl}")
    print(f"LightRAG working dir: {args.working_dir}")
    print(f"Doc tracking file: {args.doc_tracking_file}")
    print(f"Sample tracking file: {args.sample_tracking_file}")
    print(f"LLM model: {args.llm_model}")
    print(f"Embedding model: {args.embedding_model}")

    sample_batches = batch_iterator(
        iter_pending_samples(args.input_jsonl, indexed_sample_ids, args.max_samples),
        batch_size=args.batch_size,
        max_batches=args.max_batches,
    )

    try:
        first_batch_samples = next(sample_batches)
    except StopIteration:
        print("No remaining samples to process.")
        return

    first_new_docs, first_prepared_samples = prepare_batch(
        first_batch_samples, indexed_doc_ids
    )
    print_batch_preview(first_batch_samples, first_new_docs)
    if args.dry_run:
        print("\nDry run only. No LightRAG indexing was executed.")
        return

    rag = build_rag(args)
    print("\nInitializing LightRAG storages...")
    await rag.initialize_storages()

    batch_number = 1
    await insert_docs(rag, first_new_docs, batch_number=batch_number)
    append_doc_tracking(args.doc_tracking_file, first_new_docs, batch_number=batch_number)
    append_sample_tracking(
        args.sample_tracking_file,
        first_prepared_samples,
        batch_number=batch_number,
    )
    indexed_doc_ids.update(doc["doc_id"] for doc in first_new_docs)
    indexed_sample_ids.update(sample["sample_id"] for sample in first_prepared_samples)
    print(f"Tracking updated after batch {batch_number}.")

    for batch_number, batch_samples in enumerate(sample_batches, start=2):
        batch_new_docs, prepared_samples = prepare_batch(batch_samples, indexed_doc_ids)
        await insert_docs(rag, batch_new_docs, batch_number=batch_number)
        append_doc_tracking(
            args.doc_tracking_file,
            batch_new_docs,
            batch_number=batch_number,
        )
        append_sample_tracking(
            args.sample_tracking_file,
            prepared_samples,
            batch_number=batch_number,
        )
        indexed_doc_ids.update(doc["doc_id"] for doc in batch_new_docs)
        indexed_sample_ids.update(sample["sample_id"] for sample in prepared_samples)
        print(f"Tracking updated after batch {batch_number}.")

    print("\n2Wiki sample-driven indexing run complete.")


if __name__ == "__main__":
    asyncio.run(main())
