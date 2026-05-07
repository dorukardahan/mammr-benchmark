#!/usr/bin/env python3
"""Run full-corpus and distractor retrieval evaluation for MAMMR datasets."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data" / "mammr_pairs_public.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = json.loads(path.read_text())
    if not isinstance(rows, list):
        raise ValueError("dataset root must be a list")
    return rows


def load_distractors(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return []
    rows = json.loads(path.read_text())
    result = []
    for index, row in enumerate(rows):
        if isinstance(row, str):
            result.append({"id": f"distractor-{index:04d}", "text": row})
        else:
            result.append({"id": str(row["id"]), "text": str(row["text"])})
    return result


def unique_preserve_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def post_embeddings(endpoint: str, model: str, texts: list[str], api_key: str, timeout: float) -> list[list[float]]:
    payload = json.dumps({"model": model, "input": texts}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    embeddings = [None] * len(texts)
    for item in data.get("data", []):
        embeddings[item["index"]] = item["embedding"]
    if any(vec is None for vec in embeddings):
        raise RuntimeError("embedding endpoint returned incomplete data")
    return embeddings  # type: ignore[return-value]


def embed_all(
    texts: list[str],
    endpoint: str,
    model: str,
    api_key: str,
    batch_size: int,
    timeout: float,
) -> tuple[dict[str, list[float]], list[float]]:
    vectors: dict[str, list[float]] = {}
    times = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        t0 = time.perf_counter()
        vecs = post_embeddings(endpoint, model, batch, api_key, timeout)
        times.append(time.perf_counter() - t0)
        for text, vec in zip(batch, vecs):
            vectors[text] = vec
        print(f"embedded {min(start + batch_size, len(texts))}/{len(texts)}")
    return vectors, times


def load_vector_cache(path: Path, texts: list[str]) -> dict[str, list[float]] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text())
    vectors = payload.get("vectors", {})
    if not isinstance(vectors, dict):
        return None
    missing = [text for text in texts if text not in vectors]
    if missing:
        return None
    print(f"loaded vector cache {path}")
    return {text: vectors[text] for text in texts}


def save_vector_cache(path: Path, model: str, texts: list[str], vectors: dict[str, list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": model,
        "text_count": len(texts),
        "vectors": {text: vectors[text] for text in texts},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False))
    print(f"saved vector cache {path}")


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError(f"embedding dimension mismatch: {len(a)} != {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def validate_vectors(vectors: dict[str, list[float]]) -> int:
    if not vectors:
        raise RuntimeError("no embeddings returned")
    dimensions = {len(vec) for vec in vectors.values()}
    if len(dimensions) != 1:
        raise RuntimeError(f"mixed embedding dimensions returned: {sorted(dimensions)}")
    dimension = next(iter(dimensions))
    if dimension <= 0:
        raise RuntimeError("empty embedding vectors returned")
    for text, vec in vectors.items():
        if not all(isinstance(value, (int, float)) and math.isfinite(float(value)) for value in vec):
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
            raise RuntimeError(f"non-finite embedding value for text hash {digest}")
    return dimension


def rank_target(query: str, target: str, candidates: list[str], vectors: dict[str, list[float]]) -> tuple[int | None, float]:
    scored = [(doc, cosine(vectors[query], vectors[doc])) for doc in candidates]
    scored.sort(key=lambda item: (-item[1], item[0]))
    for index, (doc, score) in enumerate(scored, start=1):
        if doc == target:
            return index, score
    return None, 0.0


def summarize_ranks(rows: list[dict[str, Any]], candidates_by_row: dict[str, list[str]], vectors: dict[str, list[float]]) -> dict[str, Any]:
    ranks: list[int] = []
    reciprocal_ranks = []
    hits = {1: 0, 3: 0, 5: 0, 10: 0, 20: 0, 50: 0}
    per_category: dict[str, dict[str, Any]] = defaultdict(lambda: {"ranks": [], "count": 0})
    examples = []

    for row in rows:
        if row["expected"] != "high":
            continue
        rank, target_score = rank_target(row["query"], row["document"], candidates_by_row[row["id"]], vectors)
        cat = row["category"]
        per_category[cat]["count"] += 1
        if rank is None:
            reciprocal_ranks.append(0.0)
            per_category[cat]["ranks"].append(None)
        else:
            ranks.append(rank)
            reciprocal_ranks.append(1.0 / rank)
            per_category[cat]["ranks"].append(rank)
            for k in hits:
                if rank <= k:
                    hits[k] += 1
            examples.append(
                {
                    "id": row["id"],
                    "category": cat,
                    "rank": rank,
                    "target_score": round(target_score, 4),
                }
            )

    total = len(reciprocal_ranks)
    category_rows = {}
    for category, data in per_category.items():
        cat_ranks = [rank for rank in data["ranks"] if rank is not None]
        cat_total = data["count"]
        category_rows[category] = {
            "queries": cat_total,
            "mrr": round(sum(1.0 / rank for rank in cat_ranks) / cat_total, 4) if cat_total else 0.0,
            "recall_at_5": round(sum(1 for rank in cat_ranks if rank <= 5) / cat_total, 4) if cat_total else 0.0,
            "median_rank": sorted(cat_ranks)[len(cat_ranks) // 2] if cat_ranks else None,
        }

    worst_examples = sorted(examples, key=lambda row: (-row["rank"], row["id"]))[:20]
    return {
        "queries": total,
        "mrr": round(sum(reciprocal_ranks) / total, 4) if total else 0.0,
        "recall_at_1": round(hits[1] / total, 4) if total else 0.0,
        "recall_at_3": round(hits[3] / total, 4) if total else 0.0,
        "recall_at_5": round(hits[5] / total, 4) if total else 0.0,
        "recall_at_10": round(hits[10] / total, 4) if total else 0.0,
        "recall_at_20": round(hits[20] / total, 4) if total else 0.0,
        "recall_at_50": round(hits[50] / total, 4) if total else 0.0,
        "median_rank": sorted(ranks)[len(ranks) // 2] if ranks else None,
        "max_rank": max(ranks) if ranks else None,
        "per_category": dict(sorted(category_rows.items())),
        "worst_ranked_high_pairs": worst_examples,
    }


def evaluate(rows: list[dict[str, Any]], distractors: list[dict[str, str]], vectors: dict[str, list[float]]) -> dict[str, Any]:
    docs_by_category: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        docs_by_category[row["category"]].append(row["document"])
    docs_by_category = {category: unique_preserve_order(docs) for category, docs in docs_by_category.items()}
    public_docs = unique_preserve_order([row["document"] for row in rows])
    distractor_texts = unique_preserve_order([row["text"] for row in distractors])
    full_docs = unique_preserve_order(public_docs + distractor_texts)

    same_category = {row["id"]: docs_by_category[row["category"]] for row in rows}
    full_corpus = {row["id"]: public_docs for row in rows}
    with_distractors = {row["id"]: full_docs for row in rows}

    return {
        "same_category": summarize_ranks(rows, same_category, vectors),
        "full_public_corpus": summarize_ranks(rows, full_corpus, vectors),
        "full_public_corpus_plus_distractors": summarize_ranks(rows, with_distractors, vectors),
        "candidate_counts": {
            "public_documents": len(public_docs),
            "synthetic_distractors": len(distractor_texts),
            "total_with_distractors": len(full_docs),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--distractors", type=Path)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--endpoint-label", default="openai-compatible")
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--metadata-json", type=Path)
    parser.add_argument("--vector-cache", type=Path, help="Optional public-text vector cache for local rerun reuse")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = load_rows(args.dataset)
    distractors = load_distractors(args.distractors)
    texts = unique_preserve_order(
        [text for row in rows for text in (row["query"], row["document"])]
        + [row["text"] for row in distractors]
    )
    vectors = load_vector_cache(args.vector_cache, texts) if args.vector_cache else None
    embed_times: list[float] = []
    if vectors is None:
        api_key = os.environ.get(args.api_key_env, "")
        vectors, embed_times = embed_all(texts, args.endpoint, args.model, api_key, args.batch_size, args.timeout)
        if args.vector_cache:
            save_vector_cache(args.vector_cache, args.model, texts, vectors)
    metrics = evaluate(rows, distractors, vectors)
    dimensions = validate_vectors(vectors)
    backend_metadata = json.loads(args.metadata_json.read_text()) if args.metadata_json else None
    dataset_sha = sha256(args.dataset)
    if isinstance(backend_metadata, dict):
        metadata_dataset_sha = backend_metadata.get("dataset_sha256")
        if metadata_dataset_sha and metadata_dataset_sha != dataset_sha:
            backend_metadata = dict(backend_metadata)
            backend_metadata["metadata_source_dataset_sha256"] = metadata_dataset_sha
        backend_metadata["dataset_sha256"] = dataset_sha
    result = {
        "model": args.model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": args.dataset.name,
        "dataset_sha256": dataset_sha,
        "distractors": args.distractors.name if args.distractors else None,
        "distractors_sha256": sha256(args.distractors) if args.distractors else None,
        "endpoint_label": args.endpoint_label,
        "batch_size": args.batch_size,
        "timeout_s": args.timeout,
        "unique_texts": len(texts),
        "dimensions": dimensions,
        "embed_times_s": [round(value, 4) for value in embed_times],
        "metrics": metrics,
        "backend_metadata": backend_metadata,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {args.output}")
    print(json.dumps(metrics["full_public_corpus_plus_distractors"], indent=2, ensure_ascii=False)[:1200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
