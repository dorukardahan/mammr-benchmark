# Public v0.1 Preliminary Results

Date: 2026-05-07

## Status

This is now a pinned public v0.1 four-model local-GGUF comparison candidate. It is not a final or universal benchmark leaderboard.

Two early diagnostic reruns are recorded for the Qwen3 embedding model, followed by a pinned four-model public rerun set.

The first run exposed a large mismatch between an unpublished benchmark table and the public sanitized candidate. The refreshed pinned rerun used the audited public dataset after stale-reference, fake-token, public-polish, and final privacy cleanup.

The pinned reruns are the results to use for public sanitized local-GGUF comparisons. The older Qwen3-only diagnostic files remain in the repo as release-gate evidence.

Additional 2026-05-07 evidence adds full-corpus+distractor retrieval, held-out mini-set retrieval, and a sanitized public reranker matrix.

## Pinned Public Local-GGUF Results

Dataset:

- file: `data/mammr_pairs_public.json`
- pairs: 305
- unique texts: 564
- dataset_sha256: `844361d0f7bb013f05c5fc3a172d71e8ed15cc9d801e60ac16749508a1c89545`

Backend:

- `llama-server OpenBLAS`
- version: `version: 1 (408225b)`
- transient benchmark service
- the long-running memory service was not modified

| Rank | Model | Weighted | Unweighted | MRR | Recall@5 | Result |
|------|-------|----------|------------|-----|----------|--------|
| 1 | BGE-M3 Q8_0 | 0.7143 | 0.7016 | 0.9134 | 0.9639 | `bge-m3-q8_0-pinned-20260506.json` |
| 2 | Snowflake-Arctic-L-v2 Q8_0 | 0.6995 | 0.6852 | 0.8917 | 0.9578 | `snowflake-arctic-l-v2-q8_0-pinned-20260506.json` |
| 3 | Jina-v3 Q8_0 | 0.6956 | 0.6885 | 0.9257 | 0.9880 | `jina-v3-q8_0-pinned-20260506.json` |
| 4 | Qwen3-0.6B Q8_0 | 0.3731 | 0.3869 | 0.4549 | 0.6446 | `qwen3-0.6b-q8_0-pinned-20260506.json` |

See `docs/pinned-public-reruns.md` for backend metadata and interpretation.

## Full-Corpus + Synthetic Distractors

Each high-relevance query was ranked against the full public document pool plus 96 synthetic public-safe distractors.


| Model | MRR | Recall@5 | Median Rank |
|-------|-----|----------|-------------|
| BGE-M3 Q8_0 | 0.6053 | 0.8012 | 2 |
| Jina-v3 Q8_0 | 0.6043 | 0.7952 | 2 |
| Snowflake-Arctic-L-v2 Q8_0 | 0.5764 | 0.7530 | 2 |
| Qwen3-Embedding-0.6B Q8_0 | 0.1520 | 0.1747 | 95 |

See `docs/full-corpus-distractor-results.md`.

## Held-Out Mini-Set

The held-out mini-set contains 60 public-safe pairs generated after public thresholds were frozen.

| Model | MRR | Recall@5 | Median Rank |
|-------|-----|----------|-------------|
| Jina-v3 Q8_0 | 0.7083 | 0.8286 | 1 |
| BGE-M3 Q8_0 | 0.6712 | 0.8286 | 1 |
| Snowflake-Arctic-L-v2 Q8_0 | 0.6208 | 0.8286 | 2 |
| Qwen3-Embedding-0.6B Q8_0 | 0.1338 | 0.2000 | 49 |

See `docs/heldout-mini-results.md`.

## Sanitized Public Reranker Matrix

Top-10 same-category reranking was rerun on sanitized public vectors.

| Reranker | Avg MRR Gain | Avg MRR Gain Excluding Qwen3 |
|----------|--------------|------------------------------|
| Cohere Rerank 4 Pro | +0.1414 | +0.0445 |
| Cohere Rerank v3.5 | +0.1179 | +0.0186 |

See `docs/sanitized-reranker-matrix.md`.

## Qwen3-Embedding-0.6B Q8_0

Diagnostic run details:

- dataset: `data/mammr_pairs_public.json`
- pairs: 305
- unique texts: 564
- endpoint: diagnostic Qwen3 benchmark backend
- batch size: 1
- diagnostic result file: `results/qwen3-0.6b-q8_0-rerun-20260505.json`
- pinned result file: `results/qwen3-0.6b-q8_0-pinned-20260506.json`
- dataset audit: `docs/dataset-quality-report.md`
- P0 semantic review: `docs/p0-cleanup-review.md`

Qwen3 result comparison:

| Metric | First diagnostic | 2026-05-05 diagnostic | refreshed pinned |
|--------|------------------|------------------------|-------------------|
| weighted_score | 0.3499 | 0.3545 | 0.3731 |
| unweighted_score | 0.3705 | 0.3738 | 0.3869 |
| MRR | 0.3654 | 0.3791 | 0.4549 |
| Recall@5 | 0.5904 | 0.5964 | 0.6446 |

Latest pinned metadata:

- dataset_sha256: `844361d0f7bb013f05c5fc3a172d71e8ed15cc9d801e60ac16749508a1c89545`
- endpoint_label: `llama-server-openblas-cpu-vps`
- dimensions: 1024
- batch_size: 1
- embedding wall time: recorded in per-text timing fields

Latest label pass rates:

| Label | Pass rate |
|-------|-----------|
| high | 27 / 166 = 0.163 |
| medium_high | 14 / 25 = 0.560 |
| medium | 7 / 11 = 0.636 |
| low | 70 / 103 = 0.680 |

## Interpretation

The sanitized public set can now support a cautious four-model local-GGUF public v0.1 comparison, but it still cannot reuse earlier unpublished benchmark claims blindly.

Qwen3 remains weak on the pinned public rerun, while Snowflake, BGE-M3, and Jina-v3 are strong. That means the public dataset itself is not globally broken. The issue is model/backend-specific and claim-specific.

This could come from one or more causes:

1. Sanitization changed important lexical anchors and reduced similarity.
2. The current public rerun backend differs from the earlier unpublished benchmark backend.
3. The fixed threshold ranges are not portable across sanitized and private variants.
