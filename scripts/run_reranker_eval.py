#!/usr/bin/env python3
"""Run public-safe reranker evaluation on MAMMR datasets."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
import urllib.request
from collections import defaultdict
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


def load_api_key(args: argparse.Namespace) -> str:
    if args.rerank_api_key_file:
        return args.rerank_api_key_file.read_text().strip()
    return os.environ.get(args.rerank_api_key_env, "")


def rerank_api(
    query: str,
    documents: list[str],
    model: str,
    api_key: str,
    timeout: float,
    endpoint: str,
    retries: int,
    retry_backoff: float,
) -> list[tuple[int, float]]:
    payload = json.dumps({"model": model, "query": query, "documents": documents}).encode("utf-8")
    attempts = max(1, retries + 1)
    last_error: Exception | None = None
    for attempt in range(attempts):
        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            break
        except Exception as exc:
            last_error = exc
            if attempt == attempts - 1:
                raise
            time.sleep(max(0.0, retry_backoff) * (2**attempt))
    else:
        raise RuntimeError(f"reranker request failed: {last_error}") from last_error
    if "error" in body:
        raise RuntimeError(str(body["error"])[:160])
    parsed = []
    for item in body.get("results", []):
        if "index" in item and "relevance_score" in item:
            parsed.append((int(item["index"]), float(item["relevance_score"])))
    return parsed


def candidate_pools(rows: list[dict[str, Any]], pool: str) -> dict[str, list[str]]:
    docs_by_category: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        docs_by_category[row["category"]].append(row["document"])
    docs_by_category = {cat: unique_preserve_order(docs) for cat, docs in docs_by_category.items()}
    all_docs = unique_preserve_order([row["document"] for row in rows])
    if pool == "same_category":
        return {row["id"]: docs_by_category[row["category"]] for row in rows}
    if pool == "full_public_corpus":
        return {row["id"]: all_docs for row in rows}
    raise ValueError(f"unsupported pool: {pool}")


def evaluate(
    rows: list[dict[str, Any]],
    vectors: dict[str, list[float]],
    pool_name: str,
    top_n: int,
    reranker_model: str,
    reranker_api_key: str,
    reranker_timeout: float,
    reranker_endpoint: str,
    reranker_retries: int,
    reranker_retry_backoff: float,
    fail_on_rerank_error: bool,
) -> dict[str, Any]:
    pools = candidate_pools(rows, pool_name)
    baseline_rrs = []
    reranked_rrs = []
    baseline_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    reranked_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    improved = degraded = unchanged = outside_topn = errors = 0
    latencies = []
    per_pair = []

    high_rows = [row for row in rows if row["expected"] == "high"]

    def add_reranked_hits(rank: int) -> None:
        for k in reranked_hits:
            if rank <= k:
                reranked_hits[k] += 1

    for row in high_rows:
        query = row["query"]
        target = row["document"]
        scored = [(doc, cosine(vectors[query], vectors[doc])) for doc in pools[row["id"]]]
        scored.sort(key=lambda item: (-item[1], item[0]))
        base_rank = None
        for index, (doc, _score) in enumerate(scored, start=1):
            if doc == target:
                base_rank = index
                break
        if base_rank is None:
            baseline_rrs.append(0.0)
            reranked_rrs.append(0.0)
            errors += 1
            continue
        baseline_rrs.append(1.0 / base_rank)
        for k in baseline_hits:
            if base_rank <= k:
                baseline_hits[k] += 1

        top_docs = [doc for doc, _score in scored[: min(top_n, len(scored))]]
        if target not in top_docs:
            reranked_rrs.append(1.0 / base_rank)
            add_reranked_hits(base_rank)
            outside_topn += 1
            unchanged += 1
            per_pair.append(
                {
                    "id": row["id"],
                    "category": row["category"],
                    "baseline_rank": base_rank,
                    "reranked_rank": base_rank,
                    "target_outside_top_n": True,
                    "rerank_error": False,
                }
            )
            continue

        t0 = time.perf_counter()
        try:
            reranked = rerank_api(
                query,
                top_docs,
                reranker_model,
                reranker_api_key,
                reranker_timeout,
                reranker_endpoint,
                reranker_retries,
                reranker_retry_backoff,
            )
        except Exception as exc:
            if fail_on_rerank_error:
                raise RuntimeError(f"reranker failed for {row['id']}: {exc}") from exc
            reranked_rrs.append(1.0 / base_rank)
            add_reranked_hits(base_rank)
            errors += 1
            unchanged += 1
            per_pair.append(
                {
                    "id": row["id"],
                    "category": row["category"],
                    "baseline_rank": base_rank,
                    "reranked_rank": base_rank,
                    "target_outside_top_n": False,
                    "rerank_error": True,
                }
            )
            continue
        latencies.append(time.perf_counter() - t0)
        reranked.sort(key=lambda item: (-item[1], top_docs[item[0]]))
        reranked_order = [top_docs[index] for index, _score in reranked if 0 <= index < len(top_docs)]
        new_rank = None
        for index, doc in enumerate(reranked_order, start=1):
            if doc == target:
                new_rank = index
                break
        if new_rank is None:
            new_rank = base_rank
        reranked_rrs.append(1.0 / new_rank)
        add_reranked_hits(new_rank)
        if new_rank < base_rank:
            improved += 1
        elif new_rank > base_rank:
            degraded += 1
        else:
            unchanged += 1
        per_pair.append(
            {
                "id": row["id"],
                "category": row["category"],
                "baseline_rank": base_rank,
                "reranked_rank": new_rank,
                "target_outside_top_n": False,
                "rerank_error": False,
            }
        )

    total = len(high_rows)
    baseline_mrr = sum(baseline_rrs) / total if total else 0.0
    reranked_mrr = sum(reranked_rrs) / total if total else 0.0
    return {
        "pool": pool_name,
        "top_n": top_n,
        "queries": total,
        "baseline": {
            "mrr": round(baseline_mrr, 4),
            **{f"recall_at_{k}": round(v / total, 4) if total else 0.0 for k, v in baseline_hits.items()},
        },
        "reranked": {
            "mrr": round(reranked_mrr, 4),
            **{f"recall_at_{k}": round(v / total, 4) if total else 0.0 for k, v in reranked_hits.items()},
            "avg_rerank_ms": round(1000 * sum(latencies) / len(latencies), 1) if latencies else 0.0,
            "total_rerank_s": round(sum(latencies), 2),
            "queries_improved": improved,
            "queries_degraded": degraded,
            "queries_unchanged": unchanged,
            "target_outside_top_n": outside_topn,
            "rerank_errors": errors,
        },
        "delta": {
            "mrr": round(reranked_mrr - baseline_mrr, 4),
            **{
                f"recall_at_{k}": round(
                    (reranked_hits[k] / total if total else 0.0) - (baseline_hits[k] / total if total else 0.0),
                    4,
                )
                for k in baseline_hits
            },
        },
        "per_pair_ranks": per_pair,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--endpoint-label", default="openai-compatible")
    parser.add_argument("--model", required=True)
    parser.add_argument("--embed-api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--embed-timeout", type=float, default=120.0)
    parser.add_argument("--pool", choices=["same_category", "full_public_corpus"], default="same_category")
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--reranker-model", required=True)
    parser.add_argument("--reranker-label", required=True)
    parser.add_argument("--reranker-endpoint", default="https://openrouter.ai/api/v1/rerank")
    parser.add_argument(
        "--reranker-endpoint-label",
        default="openrouter-rerank",
        help="Public-safe label stored in result JSON; the endpoint URL itself is not written.",
    )
    parser.add_argument("--rerank-api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument("--rerank-api-key-file", type=Path)
    parser.add_argument("--rerank-timeout", type=float, default=45.0)
    parser.add_argument("--rerank-retries", type=int, default=3)
    parser.add_argument("--rerank-retry-backoff", type=float, default=1.0)
    parser.add_argument("--fail-on-rerank-error", action="store_true")
    parser.add_argument("--metadata-json", type=Path)
    parser.add_argument("--vector-cache", type=Path, help="Optional public-text vector cache for local rerun reuse")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = load_rows(args.dataset)
    texts = unique_preserve_order([text for row in rows for text in (row["query"], row["document"])])
    reranker_api_key = load_api_key(args)
    if not reranker_api_key:
        raise SystemExit("reranker API key missing")
    vectors = load_vector_cache(args.vector_cache, texts) if args.vector_cache else None
    embed_times: list[float] = []
    if vectors is None:
        embed_api_key = os.environ.get(args.embed_api_key_env, "")
        vectors, embed_times = embed_all(texts, args.endpoint, args.model, embed_api_key, args.batch_size, args.embed_timeout)
        if args.vector_cache:
            save_vector_cache(args.vector_cache, args.model, texts, vectors)
    dimensions = validate_vectors(vectors)
    metrics = evaluate(
        rows,
        vectors,
        args.pool,
        args.top_n,
        args.reranker_model,
        reranker_api_key,
        args.rerank_timeout,
        args.reranker_endpoint,
        args.rerank_retries,
        args.rerank_retry_backoff,
        args.fail_on_rerank_error,
    )
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
        "endpoint_label": args.endpoint_label,
        "reranker_label": args.reranker_label,
        "reranker_model": args.reranker_model,
        "reranker_endpoint_label": args.reranker_endpoint_label,
        "unique_texts": len(texts),
        "dimensions": dimensions,
        "embed_times_s": [round(value, 4) for value in embed_times],
        "metrics": metrics,
        "backend_metadata": backend_metadata,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {args.output}")
    print(json.dumps({k: metrics[k] for k in ["pool", "top_n", "baseline", "reranked", "delta"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
