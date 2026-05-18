"""
Index Ericsson technical documentation PDFs into LightRAG.

This version is configurable and batch-aware:
  - Gemini model defaults can be overridden from the CLI or environment
  - documents are inserted in batches via LightRAG's list-based `ainsert(...)`
  - a dry-run mode lets us inspect the first batch before any API call

Input:  data/raw/ericsson/*.pdf
Output: data/index/ (LightRAG graph + vector stores)
Tracking: data/processed/index_tracking.json
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from dotenv import load_dotenv
from lightrag import LightRAG
from lightrag.llm.gemini import gemini_embed, gemini_model_complete
from lightrag.utils import wrap_embedding_func_with_attrs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKING_DIR = Path("data/index")
DEFAULT_PDF_DIR = Path("data/raw/ericsson")
DEFAULT_TRACKING_FILE = Path("data/processed/index_tracking.json")
DEFAULT_LLM_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-3-flash-preview")
DEFAULT_EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "models/gemini-embedding-001",
)
DEFAULT_TIKTOKEN_MODEL = os.getenv("TIKTOKEN_MODEL_NAME", "gpt-4o-mini")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Index Ericsson PDFs into LightRAG in configurable batches."
    )
    parser.add_argument("--pdf-dir", type=Path, default=DEFAULT_PDF_DIR)
    parser.add_argument("--working-dir", type=Path, default=DEFAULT_WORKING_DIR)
    parser.add_argument(
        "--tracking-file",
        type=Path,
        default=DEFAULT_TRACKING_FILE,
        help="JSON file used to resume indexing across runs.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of PDFs to send in each LightRAG insert batch.",
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=None,
        help="Optional cap on how many batches to process in this run.",
    )
    parser.add_argument(
        "--max-docs",
        type=int,
        default=None,
        help="Optional cap on how many unindexed PDFs to prepare.",
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
        help="Print the first prepared batch without calling the Gemini API.",
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


def extract_text_from_pdf(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    text_parts: list[str] = []
    for page_num, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
    doc.close()
    return "\n\n".join(text_parts)


def discover_pdfs(pdf_dir: Path) -> list[Path]:
    if not pdf_dir.exists():
        return []
    return sorted(pdf_dir.glob("**/*.pdf"))


def load_tracking(tracking_file: Path) -> list[dict[str, Any]]:
    if not tracking_file.exists():
        return []

    try:
        with tracking_file.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            if isinstance(data, list):
                return data
    except json.JSONDecodeError:
        print(
            f"Warning: {tracking_file} is not valid JSON. Starting with an empty tracking set."
        )

    return []


def chunked(items: list[dict[str, Any]], batch_size: int):
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def make_pdf_doc_id(pdf_path: Path) -> str:
    digest = hashlib.md5(str(pdf_path.resolve()).encode("utf-8")).hexdigest()[:16]
    return f"pdf-{digest}"


def prepare_documents(
    pdf_paths: list[Path],
    indexed_paths: set[str],
    max_docs: int | None,
) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []

    for pdf_path in pdf_paths:
        path_str = str(pdf_path)
        if path_str in indexed_paths:
            continue

        print(f"Extracting text from {pdf_path.name}...")
        text = extract_text_from_pdf(pdf_path)
        if not text.strip():
            print(f"  Skipping {pdf_path.name}: no extractable text found.")
            continue

        prepared.append(
            {
                "doc_id": make_pdf_doc_id(pdf_path),
                "filename": pdf_path.name,
                "path": path_str,
                "text": text,
                "char_count": len(text),
                "word_count": len(text.split()),
            }
        )

        if max_docs is not None and len(prepared) >= max_docs:
            break

    return prepared


def print_batch_preview(batch: list[dict[str, Any]], batch_size: int) -> None:
    print(f"\nPrepared first batch of {len(batch)} document(s) with batch size {batch_size}.")
    for item in batch[:5]:
        print(
            f"  {item['filename']} | words={item['word_count']:,} | chars={item['char_count']:,}"
        )
    if len(batch) > 5:
        print(f"  ... plus {len(batch) - 5} more document(s)")


async def insert_batch(
    rag: LightRAG,
    batch: list[dict[str, Any]],
    batch_number: int,
    total_batches: int,
    max_retries: int = 3,
) -> None:
    texts = [item["text"] for item in batch]
    ids = [item["doc_id"] for item in batch]
    file_paths = [item["path"] for item in batch]

    for attempt in range(1, max_retries + 1):
        try:
            print(
                f"Indexing batch {batch_number}/{total_batches} with {len(batch)} PDF(s) "
                f"(attempt {attempt}/{max_retries})..."
            )
            await rag.ainsert(texts, ids=ids, file_paths=file_paths)
            return
        except Exception as exc:
            print(f"  Batch insert failed: {exc}")
            if attempt == max_retries:
                raise
            await asyncio.sleep(10)


async def main() -> None:
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
    args = parse_args()
    ensure_credentials_if_needed(args.dry_run)

    args.working_dir.mkdir(parents=True, exist_ok=True)
    args.tracking_file.parent.mkdir(parents=True, exist_ok=True)

    pdf_paths = discover_pdfs(args.pdf_dir)
    if not pdf_paths:
        print(f"No PDFs found in {args.pdf_dir}.")
        return

    tracking_entries = load_tracking(args.tracking_file)
    indexed_paths = {entry["path"] for entry in tracking_entries if "path" in entry}
    prepared_documents = prepare_documents(pdf_paths, indexed_paths, args.max_docs)

    print(f"\nFound {len(pdf_paths)} PDF(s) total.")
    print(f"Already indexed: {len(indexed_paths)}")
    print(f"Prepared for this run: {len(prepared_documents)}")

    if not prepared_documents:
        print("Nothing new to index.")
        return

    batches = list(chunked(prepared_documents, args.batch_size))
    if args.max_batches is not None:
        batches = batches[: args.max_batches]

    print_batch_preview(batches[0], args.batch_size)
    if args.dry_run:
        print("\nDry run only. No LightRAG indexing was executed.")
        return

    rag = build_rag(args)
    print("\nInitializing LightRAG storages...")
    await rag.initialize_storages()

    total_batches = len(batches)
    for batch_number, batch in enumerate(batches, start=1):
        await insert_batch(rag, batch, batch_number, total_batches)

        for item in batch:
            tracking_entries.append(
                {
                    "doc_id": item["doc_id"],
                    "filename": item["filename"],
                    "path": item["path"],
                    "word_count": item["word_count"],
                    "char_count": item["char_count"],
                }
            )

        with args.tracking_file.open("w", encoding="utf-8") as handle:
            json.dump(tracking_entries, handle, indent=2, ensure_ascii=False)

        print(f"Updated tracking file: {args.tracking_file}")

    print("\nIndexing complete.")


if __name__ == "__main__":
    asyncio.run(main())
