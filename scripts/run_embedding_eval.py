#!/usr/bin/env python3
"""Run MAMMR public v0.1 against an OpenAI-compatible embeddings endpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCORE_RANGES = {
    "high": (0.50, 1.00),
    "medium_high": (0.40, 0.75),
    "medium": (0.25, 0.65),
    "low": (-1.00, 0.35),
}

CATEGORY_WEIGHTS = {
    "short_query_long_memory": 10,
    "code_switching": 9,
    "specificity": 9,
    "negative_control": 9,
    "irrelevant": 9,
    "conversational_recall": 8,
    "paraphrase": 8,
    "similar_but_different": 8,
    "adversarial": 8,
    "crosslingual": 7,
    "code_to_description": 7,
    "temporal": 6,
    "turkish_morphology": 6,
    "entity_confusion": 6,
    "synonym_alias": 5,
    "context_implicit": 5,
    "partial_match": 5,
    "code_mixed": 5,
    "same_topic_different_time": 5,
    "turkish_chars": 4,
    "noise_typo": 4,
}


def load_pairs(path: Path) -> list[dict[str, Any]]:
    rows = json.loads(path.read_text())
    required = {"id", "category", "expected", "query", "document"}
    for row in rows:
        missing = required - set(row)
        if missing:
            raise ValueError(f"{row.get('id', '<unknown>')} missing fields: {sorted(missing)}")
        if row["expected"] not in SCORE_RANGES:
            raise ValueError(f"{row['id']} invalid expected label: {row['expected']}")
    return rows


def unique_texts(rows: list[dict[str, Any]]) -> list[str]:
    seen = set()
    texts = []
    for row in rows:
        for key in ("query", "document"):
            text = row[key]
            if text not in seen:
                seen.add(text)
                texts.append(text)
    return texts


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


def embed_all(
    texts: list[str],
    endpoint: str,
    model: str,
    api_key: str,
    batch_size: int,
    timeout: float,
) -> tuple[dict[str, list[float]], list[float]]:
    vectors: dict[str, list[float]] = {}
    times: list[float] = []
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


def evaluate(
    rows: list[dict[str, Any]],
    vectors: dict[str, list[float]],
    model: str,
    embed_times: list[float],
    dataset_path: Path,
    endpoint_label: str,
    batch_size: int,
    timeout: float,
    backend_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dimensions = validate_vectors(vectors)
    results: dict[str, Any] = {
        "model": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": str(dataset_path.name),
        "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
        "endpoint_label": endpoint_label,
        "batch_size": batch_size,
        "timeout_s": timeout,
        "unique_texts": len(vectors),
        "dimensions": dimensions,
        "total_pairs": len(rows),
        "total_pass": 0,
        "total_fail": 0,
        "categories": {},
        "pairs": [],
        "embed_times_s": [round(x, 4) for x in embed_times],
    }

    for row in rows:
        cat = row["category"]
        results["categories"].setdefault(
            cat,
            {"total": 0, "pass": 0, "fail": 0, "weight": CATEGORY_WEIGHTS.get(cat, 4), "scores": []},
        )
        sim = cosine(vectors[row["query"]], vectors[row["document"]])
        lo, hi = SCORE_RANGES[row["expected"]]
        ok = lo <= sim <= hi
        status = "pass" if ok else "fail"
        results["total_pass" if ok else "total_fail"] += 1
        cat_data = results["categories"][cat]
        cat_data["total"] += 1
        cat_data["pass" if ok else "fail"] += 1
        cat_data["scores"].append(sim)
        margin = 0.0
        if sim < lo:
            margin = lo - sim
        elif sim > hi:
            margin = sim - hi
        results["pairs"].append(
            {
                "id": row["id"],
                "category": cat,
                "expected": row["expected"],
                "similarity": round(sim, 4),
                "status": status,
                "margin": round(margin, 4),
            }
        )

    weighted_sum = 0.0
    weight_total = 0.0
    for cat, data in results["categories"].items():
        evaluated = data["pass"] + data["fail"]
        data["accuracy"] = round(data["pass"] / evaluated, 4) if evaluated else 0.0
        scores = data.pop("scores")
        data["avg_sim"] = round(sum(scores) / len(scores), 4) if scores else 0.0
        data["min_sim"] = round(min(scores), 4) if scores else 0.0
        data["max_sim"] = round(max(scores), 4) if scores else 0.0
        weighted_sum += data["accuracy"] * data["weight"]
        weight_total += data["weight"]

    total_evaluated = results["total_pass"] + results["total_fail"]
    results["weighted_score"] = round(weighted_sum / weight_total, 4) if weight_total else 0.0
    results["unweighted_score"] = round(results["total_pass"] / total_evaluated, 4) if total_evaluated else 0.0

    rr_values = []
    recall5_hits = 0
    recall5_total = 0
    pools: dict[str, list[str]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        cat = row["category"]
        doc = row["document"]
        if doc not in seen[cat]:
            seen[cat].add(doc)
            pools[cat].append(doc)

    for row in rows:
        if row["expected"] != "high":
            continue
        pool = pools[row["category"]]
        if len(pool) < 6:
            continue
        scored = [(doc, cosine(vectors[row["query"]], vectors[doc])) for doc in pool]
        scored.sort(key=lambda item: (-item[1], item[0]))
        rank = None
        for i, (doc, _score) in enumerate(scored, start=1):
            if doc == row["document"]:
                rank = i
                break
        recall5_total += 1
        if rank is None:
            rr_values.append(0.0)
        else:
            rr_values.append(1.0 / rank)
            if rank <= 5:
                recall5_hits += 1

    results["mrr"] = round(sum(rr_values) / len(rr_values), 4) if rr_values else 0.0
    results["recall_at_5"] = round(recall5_hits / recall5_total, 4) if recall5_total else 0.0
    results["retrieval_queries"] = recall5_total
    results["label_counts"] = dict(sorted(Counter(row["expected"] for row in rows).items()))
    if backend_metadata is not None:
        results["backend_metadata"] = backend_metadata
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "mammr_pairs_public.json")
    parser.add_argument("--endpoint", required=False, help="Full embeddings endpoint URL, e.g. http://localhost:8090/v1/embeddings")
    parser.add_argument("--endpoint-label", default="openai-compatible", help="Public-safe backend label stored in the output JSON")
    parser.add_argument("--model", required=False, default="model")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--output", type=Path, default=Path("mammr-result.json"))
    parser.add_argument("--metadata-json", type=Path, help="Optional public-safe backend metadata JSON to embed in the result")
    parser.add_argument("--vector-cache", type=Path, help="Optional public-text vector cache for local rerun reuse")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = load_pairs(args.dataset)
    texts = unique_texts(rows)
    print(f"pairs={len(rows)} unique_texts={len(texts)} categories={len(set(row['category'] for row in rows))}")
    print(f"labels={dict(sorted(Counter(row['expected'] for row in rows).items()))}")
    if args.dry_run:
        return 0
    if not args.endpoint:
        raise SystemExit("--endpoint is required unless --dry-run is used")

    backend_metadata = None
    if args.metadata_json:
        backend_metadata = json.loads(args.metadata_json.read_text())

    vectors = load_vector_cache(args.vector_cache, texts) if args.vector_cache else None
    embed_times: list[float] = []
    if vectors is None:
        api_key = os.environ.get(args.api_key_env, "")
        vectors, embed_times = embed_all(texts, args.endpoint, args.model, api_key, args.batch_size, args.timeout)
        if args.vector_cache:
            save_vector_cache(args.vector_cache, args.model, texts, vectors)
    results = evaluate(
        rows,
        vectors,
        args.model,
        embed_times,
        args.dataset,
        args.endpoint_label,
        args.batch_size,
        args.timeout,
        backend_metadata,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(f"weighted_score={results['weighted_score']} mrr={results['mrr']} recall_at_5={results['recall_at_5']}")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
