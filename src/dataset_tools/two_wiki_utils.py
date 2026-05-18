from __future__ import annotations

import hashlib
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, Iterator


def infer_split_name(input_path: Path) -> str:
    return input_path.stem


def iter_json_array(input_path: Path, chunk_size: int = 1 << 20) -> Iterator[Dict[str, Any]]:
    """Stream objects from a top-level JSON array without loading the whole file."""
    decoder = json.JSONDecoder()
    buffer = ""
    started = False

    with input_path.open("r", encoding="utf-8") as handle:
        while True:
            chunk = handle.read(chunk_size)
            eof = chunk == ""
            buffer += chunk

            while True:
                buffer = buffer.lstrip()

                if not started:
                    if not buffer:
                        break
                    if buffer[0] != "[":
                        raise ValueError(f"{input_path} is not a JSON array")
                    started = True
                    buffer = buffer[1:]
                    continue

                buffer = buffer.lstrip()
                if not buffer:
                    break
                if buffer[0] == ",":
                    buffer = buffer[1:]
                    continue
                if buffer[0] == "]":
                    return

                try:
                    obj, end_index = decoder.raw_decode(buffer)
                except JSONDecodeError:
                    if eof:
                        raise
                    break

                yield obj
                buffer = buffer[end_index:]

            if eof:
                break


def parse_id_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    if isinstance(value, str):
        return [part for part in value.split("_") if part]
    return [str(value)]


def stable_doc_id(title: str) -> str:
    return hashlib.sha1(title.encode("utf-8")).hexdigest()[:16]


def safe_title_for_path(title: str) -> str:
    cleaned = []
    for char in title.strip():
        if char.isalnum() or char in {" ", ".", "-", "_"}:
            cleaned.append(char)
        else:
            cleaned.append("_")
    compact = "".join(cleaned)
    compact = "_".join(compact.split())
    return compact or "untitled"


def context_map(sample: Dict[str, Any]) -> Dict[str, list[str]]:
    return {title: sentences for title, sentences in sample.get("context", [])}


def make_context_doc(
    title: str,
    sentences: list[str],
    split: str,
    context_index: int,
) -> Dict[str, Any]:
    doc_id = stable_doc_id(title)
    text = " ".join(sentences)
    return {
        "doc_id": doc_id,
        "title": title,
        "split": split,
        "context_index": context_index,
        "sentence_count": len(sentences),
        "text": text,
        "sentences": sentences,
        "char_count": len(text),
        "file_path": f"2wiki/{split}/{doc_id}_{safe_title_for_path(title)}.txt",
    }


def supporting_fact_records(sample: Dict[str, Any]) -> list[Dict[str, Any]]:
    contexts = context_map(sample)
    rows: list[Dict[str, Any]] = []

    for index, item in enumerate(sample.get("supporting_facts", [])):
        title, sentence_index = item
        sentences = contexts.get(title, [])
        sentence_text = None
        if isinstance(sentence_index, int) and 0 <= sentence_index < len(sentences):
            sentence_text = sentences[sentence_index]
        rows.append(
            {
                "support_index": index,
                "doc_id": stable_doc_id(title),
                "title": title,
                "sentence_index": sentence_index,
                "sentence_text": sentence_text,
            }
        )

    return rows


def evidence_records(sample: Dict[str, Any]) -> list[Dict[str, Any]]:
    rows: list[Dict[str, Any]] = []

    for index, item in enumerate(sample.get("evidences", [])):
        rows.append(
            {
                "evidence_index": index,
                "head": item[0] if len(item) > 0 else None,
                "relation": item[1] if len(item) > 1 else None,
                "tail": item[2] if len(item) > 2 else None,
            }
        )

    return rows


def make_sample_record(sample: Dict[str, Any], split: str) -> Dict[str, Any]:
    contexts = sample.get("context", [])
    context_docs = [
        make_context_doc(title, sentences, split, context_index)
        for context_index, (title, sentences) in enumerate(contexts)
    ]
    support_rows = supporting_fact_records(sample)
    evidence_list = evidence_records(sample)
    context_doc_ids = [doc["doc_id"] for doc in context_docs]
    supporting_doc_ids = list(dict.fromkeys(row["doc_id"] for row in support_rows))

    return {
        "sample_id": sample.get("_id"),
        "split": split,
        "question_type": sample.get("type"),
        "question": sample.get("question"),
        "answer": sample.get("answer"),
        "answer_available": sample.get("answer") not in (None, ""),
        "answer_id": sample.get("answer_id"),
        "entity_ids": sample.get("entity_ids"),
        "entity_id_list": parse_id_list(sample.get("entity_ids")),
        "evidences_id": sample.get("evidences_id"),
        "evidence_id_list": parse_id_list(sample.get("evidences_id")),
        "context_count": len(context_docs),
        "context_titles": [doc["title"] for doc in context_docs],
        "context_doc_ids": context_doc_ids,
        "context_docs": context_docs,
        "supporting_fact_count": len(support_rows),
        "supporting_doc_ids": supporting_doc_ids,
        "supporting_facts": support_rows,
        "evidence_count": len(evidence_list),
        "evidences": evidence_list,
    }


def write_jsonl_record(handle, record: Dict[str, Any]) -> None:
    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
