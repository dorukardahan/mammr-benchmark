#!/usr/bin/env python3
"""Summarize the public strong-evidence reruns into docs and JSON."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

MODEL_ORDER = [
    "snowflake",
    "bge",
    "jina",
    "qwen3",
]

MODEL_LABELS = {
    "snowflake": "Snowflake-Arctic-L-v2 Q8_0",
    "bge": "BGE-M3 Q8_0",
    "jina": "Jina-v3 Q8_0",
    "qwen3": "Qwen3-Embedding-0.6B Q8_0",
}

RERANKER_ORDER = ["cohere-4-pro", "cohere-v3.5"]
RERANKER_LABELS = {
    "cohere-4-pro": "Cohere Rerank 4 Pro",
    "cohere-v3.5": "Cohere Rerank v3.5",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def fmt(value: float | int | None) -> str:
    if value is None:
        return "-"
    if isinstance(value, int):
        return str(value)
    return f"{value:.4f}"


def model_key(path: Path) -> str:
    name = path.name
    if name.startswith("snowflake-"):
        return "snowflake"
    if name.startswith("bge-"):
        return "bge"
    if name.startswith("jina-"):
        return "jina"
    if name.startswith("qwen3-"):
        return "qwen3"
    raise ValueError(f"unknown model file: {path}")


def reranker_key(path: Path) -> str:
    name = path.name
    if "cohere-4-pro" in name:
        return "cohere-4-pro"
    if "cohere-v3.5" in name:
        return "cohere-v3.5"
    raise ValueError(f"unknown reranker file: {path}")


def evidence_tables() -> dict[str, Any]:
    retrieval = {}
    for path in sorted((ROOT / "results" / "retrieval").glob("*20260506.json")):
        data = load(path)
        metric = data["metrics"]["full_public_corpus_plus_distractors"]
        retrieval[model_key(path)] = {
            "file": str(path.relative_to(ROOT)),
            "model": MODEL_LABELS[model_key(path)],
            "dataset_sha256": data["dataset_sha256"],
            "distractors_sha256": data["distractors_sha256"],
            "queries": metric["queries"],
            "mrr": metric["mrr"],
            "recall_at_1": metric["recall_at_1"],
            "recall_at_5": metric["recall_at_5"],
            "recall_at_20": metric["recall_at_20"],
            "median_rank": metric["median_rank"],
            "max_rank": metric["max_rank"],
            "candidate_counts": data["metrics"]["candidate_counts"],
        }

    heldout = {}
    for path in sorted((ROOT / "results" / "heldout").glob("*20260506.json")):
        data = load(path)
        metric = data["metrics"]["full_public_corpus_plus_distractors"]
        heldout[model_key(path)] = {
            "file": str(path.relative_to(ROOT)),
            "model": MODEL_LABELS[model_key(path)],
            "dataset_sha256": data["dataset_sha256"],
            "distractors_sha256": data["distractors_sha256"],
            "queries": metric["queries"],
            "mrr": metric["mrr"],
            "recall_at_1": metric["recall_at_1"],
            "recall_at_5": metric["recall_at_5"],
            "recall_at_20": metric["recall_at_20"],
            "median_rank": metric["median_rank"],
            "max_rank": metric["max_rank"],
            "candidate_counts": data["metrics"]["candidate_counts"],
        }

    reranker = defaultdict(dict)
    for path in sorted((ROOT / "results" / "reranker").glob("*20260506.json")):
        data = load(path)
        metric = data["metrics"]
        rkey = reranker_key(path)
        reranker[model_key(path)][rkey] = {
            "file": str(path.relative_to(ROOT)),
            "embedding_model": MODEL_LABELS[model_key(path)],
            "reranker": RERANKER_LABELS[rkey],
            "baseline_mrr": metric["baseline"]["mrr"],
            "reranked_mrr": metric["reranked"]["mrr"],
            "delta_mrr": metric["delta"]["mrr"],
            "reranked_recall_at_1": metric["reranked"]["recall_at_1"],
            "reranked_recall_at_5": metric["reranked"]["recall_at_5"],
            "avg_rerank_ms": metric["reranked"]["avg_rerank_ms"],
            "improved": metric["reranked"]["queries_improved"],
            "degraded": metric["reranked"]["queries_degraded"],
            "unchanged": metric["reranked"]["queries_unchanged"],
            "errors": metric["reranked"]["rerank_errors"],
        }

    return {
        "retrieval": retrieval,
        "heldout": heldout,
        "reranker": {key: dict(value) for key, value in reranker.items()},
    }


def write_full_corpus_doc(tables: dict[str, Any]) -> None:
    rows = tables["retrieval"]
    first = next(iter(rows.values()))
    counts = first["candidate_counts"]
    strong_keys = [key for key in MODEL_ORDER if key != "qwen3"]
    best_mrr_key = max(strong_keys, key=lambda key: rows[key]["mrr"])
    best_recall5_key = max(strong_keys, key=lambda key: rows[key]["recall_at_5"])
    lines = [
        "# Full-Corpus And Distractor Retrieval Results",
        "",
        "This evaluation ranks each high-relevance query against the full sanitized public document pool plus synthetic public-safe distractors.",
        "",
        "Scope:",
        "",
        f"- dataset: `data/mammr_pairs_public.json`",
        f"- dataset SHA-256: `{first['dataset_sha256']}`",
        f"- distractors: `data/synthetic_distractors_public.json`",
        f"- distractors SHA-256: `{first['distractors_sha256']}`",
        f"- high-relevance queries: {first['queries']}",
        f"- public candidate documents: {counts['public_documents']}",
        f"- synthetic distractors: {counts['synthetic_distractors']} rows from 24 base public-safe distractor topics",
        f"- total candidate documents: {counts['total_with_distractors']}",
        "",
        "## Results",
        "",
        "| Model | MRR | Recall@1 | Recall@5 | Recall@20 | Median Rank | Max Rank |",
        "|-------|-----|----------|----------|-----------|-------------|----------|",
    ]
    for key in MODEL_ORDER:
        row = rows[key]
        lines.append(
            f"| {row['model']} | {fmt(row['mrr'])} | {fmt(row['recall_at_1'])} | "
            f"{fmt(row['recall_at_5'])} | {fmt(row['recall_at_20'])} | "
            f"{fmt(row['median_rank'])} | {fmt(row['max_rank'])} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Snowflake, BGE-M3, and Jina-v3 all have median rank 2 in the mixed public pool, but the Recall@5 values and max ranks show nontrivial tail failures.",
            f"{rows[best_mrr_key]['model']} has the highest full-corpus MRR point estimate in this run by a very small margin over Jina-v3 Q8_0, and {rows[best_recall5_key]['model']} has the strongest Recall@5 among the three strong baselines.",
            "",
            "The distractors are synthetic and public-safe. They are useful for a harder smoke test than same-category ranking, but the 96 rows come from 24 base distractor topics with templated prefixes. Absolute MRR and Recall@k should therefore be expected to change on a larger, more diverse independent corpus.",
            "",
            "Qwen3-Embedding-0.6B remains weak on the sanitized public full-corpus task.",
            "This reinforces the release framing: Qwen3 was a practical production choice on one CPU-only VPS, not the sanitized public leaderboard winner.",
            "",
        ]
    )
    (ROOT / "docs" / "full-corpus-distractor-results.md").write_text("\n".join(lines))


def write_heldout_doc(tables: dict[str, Any]) -> None:
    rows = tables["heldout"]
    first = next(iter(rows.values()))
    counts = first["candidate_counts"]
    lines = [
        "# Held-Out Mini-Set Results",
        "",
        "The held-out mini-set was generated after the public v0.1 thresholds were frozen.",
        "It is used as a small sanity check against threshold and cleanup overfitting.",
        "",
        "Scope:",
        "",
        f"- dataset: `data/heldout_mini_public.json`",
        f"- dataset SHA-256: `{first['dataset_sha256']}`",
        f"- high-relevance queries: {first['queries']}",
        f"- public candidate documents: {counts['public_documents']}",
        f"- synthetic distractors: {counts['synthetic_distractors']}",
        f"- total candidate documents: {counts['total_with_distractors']}",
        "",
        "## Results",
        "",
        "| Model | MRR | Recall@1 | Recall@5 | Recall@20 | Median Rank | Max Rank |",
        "|-------|-----|----------|----------|-----------|-------------|----------|",
    ]
    for key in MODEL_ORDER:
        row = rows[key]
        lines.append(
            f"| {row['model']} | {fmt(row['mrr'])} | {fmt(row['recall_at_1'])} | "
            f"{fmt(row['recall_at_5'])} | {fmt(row['recall_at_20'])} | "
            f"{fmt(row['median_rank'])} | {fmt(row['max_rank'])} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "BGE-M3, Jina-v3, and Snowflake remain strong on the held-out mini-set.",
            "Qwen3-Embedding-0.6B again performs poorly on the sanitized public-style task.",
            "",
            "This is useful evidence that the public v0.1 result is not only an artifact of the original 305-pair set.",
            "It is still a small mini-set, so it should be reported as additional evidence, not as a replacement for a larger independent test set.",
            "",
        ]
    )
    (ROOT / "docs" / "heldout-mini-results.md").write_text("\n".join(lines))


def write_reranker_doc(tables: dict[str, Any]) -> None:
    rows = tables["reranker"]
    lines = [
        "# Sanitized Public Reranker Matrix",
        "",
        "This reranker matrix uses the sanitized public vectors and reranks the top-10 same-category candidates.",
        "It is not a full-corpus reranker benchmark, but it directly checks whether the earlier reranker finding survives on public-safe data.",
        "",
        "Scope:",
        "",
        "- dataset: `data/mammr_pairs_public.json`",
        "- candidate pool: same category",
        "- top-n: 10",
        "- rerankers: Cohere Rerank 4 Pro and Cohere Rerank v3.5 via OpenRouter",
        "- raw API keys are not stored in result files",
        "",
        "## Results",
        "",
        "| Embedding | Reranker | Baseline MRR | Reranked MRR | Delta | R@1 | R@5 | Avg ms | Improved | Degraded | Errors |",
        "|-----------|----------|--------------|--------------|-------|-----|-----|--------|----------|----------|--------|",
    ]
    deltas_by_reranker = defaultdict(list)
    deltas_ex_qwen = defaultdict(list)
    for model in MODEL_ORDER:
        for reranker in RERANKER_ORDER:
            row = rows[model][reranker]
            deltas_by_reranker[reranker].append(row["delta_mrr"])
            if model != "qwen3":
                deltas_ex_qwen[reranker].append(row["delta_mrr"])
            lines.append(
                f"| {row['embedding_model']} | {row['reranker']} | {fmt(row['baseline_mrr'])} | "
                f"{fmt(row['reranked_mrr'])} | {fmt(row['delta_mrr'])} | "
                f"{fmt(row['reranked_recall_at_1'])} | {fmt(row['reranked_recall_at_5'])} | "
                f"{row['avg_rerank_ms']:.1f} | {row['improved']} | {row['degraded']} | {row['errors']} |"
            )
    lines.extend(["", "## Average MRR Gain", ""])
    lines.append("| Reranker | All four embeddings | Excluding Qwen3 |")
    lines.append("|----------|---------------------|-----------------|")
    for key in RERANKER_ORDER:
        avg_all = sum(deltas_by_reranker[key]) / len(deltas_by_reranker[key])
        avg_ex = sum(deltas_ex_qwen[key]) / len(deltas_ex_qwen[key])
        lines.append(f"| {RERANKER_LABELS[key]} | {fmt(avg_all)} | {fmt(avg_ex)} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Cohere Rerank 4 Pro is the strongest reranker in this sanitized matrix.",
            "Cohere Rerank v3.5 is average-positive and MRR-positive for all four embeddings in this rerun, but the gains are smaller and some recall-at-k values can still trade off on already strong baselines.",
            "",
            "The Qwen3 gain is large because the baseline public sanitized same-category ranking is weak.",
            "For the already strong Snowflake, BGE-M3, and Jina-v3 baselines, reranker gains are smaller and must be read per model rather than assumed uniform.",
            "",
            "This supports the paper claim that reranker choice is a major quality lever, but it should not be overstated as a full production retrieval result because the candidate pool is same-category top-10.",
            "",
        ]
    )
    (ROOT / "docs" / "sanitized-reranker-matrix.md").write_text("\n".join(lines))


def main() -> int:
    tables = evidence_tables()
    (ROOT / "results" / "strong-evidence-summary.json").write_text(json.dumps(tables, indent=2) + "\n")
    write_full_corpus_doc(tables)
    write_heldout_doc(tables)
    write_reranker_doc(tables)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
