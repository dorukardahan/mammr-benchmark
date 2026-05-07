# Pinned Public Reruns

Date: 2026-05-06
Refreshed: 2026-05-07

These are the pinned public reruns on `data/mammr_pairs_public.json` after stale-reference, fake-token, public-polish, and final privacy cleanup passes.

They were run on a CPU-only VPS through a transient llama-server service. The always-on embedding service was not modified.

## Dataset

- pairs: `305`
- unique texts: `564`
- dataset_sha256: `844361d0f7bb013f05c5fc3a172d71e8ed15cc9d801e60ac16749508a1c89545`

## Backend

- backend: `llama-server OpenBLAS`
- version: `version: 1 (408225b)`
- binary_sha256: `5f2609599bc72850fe0a5349502cdaa137c2477aa620e64eb53ae5c010b0fae7`
- hardware_class: `cpu_only_vps`
- ctx_size: `8192`
- threads: `1`
- threads_batch: `1`
- batch_size: `1`
- gpu_layers: `0`

Each result JSON embeds a `backend_metadata` object and has a matching metadata snapshot under `metadata/`.

## Results

| Rank | Model | Pooling | Weighted | Weighted 95% CI | Unweighted | MRR | Recall@5 | Dimensions | Result |
|------|-------|---------|----------|-----------------|------------|-----|----------|------------|--------|
| 1 | BGE-M3 Q8_0 | cls | 0.7143 | 0.6657 - 0.7613 | 0.7016 | 0.9134 | 0.9639 | 1024 | `results/bge-m3-q8_0-pinned-20260506.json` |
| 2 | Snowflake-Arctic-L-v2 Q8_0 | cls | 0.6995 | 0.6481 - 0.7498 | 0.6852 | 0.8917 | 0.9578 | 1024 | `results/snowflake-arctic-l-v2-q8_0-pinned-20260506.json` |
| 3 | Jina-v3 Q8_0 | mean | 0.6956 | 0.6474 - 0.7429 | 0.6885 | 0.9257 | 0.9880 | 1024 | `results/jina-v3-q8_0-pinned-20260506.json` |
| 4 | Qwen3-0.6B Q8_0 | last | 0.3731 | 0.3256 - 0.4218 | 0.3869 | 0.4549 | 0.6446 | 1024 | `results/qwen3-0.6b-q8_0-pinned-20260506.json` |

The weighted intervals are stratified bootstrap intervals from `scripts/bootstrap_pinned_scores.py` with 10,000 iterations. The top three intervals overlap, so this table supports "highest point estimate" language, not a statistically significant separation claim.

## Result File Hashes

| File | SHA-256 |
|------|---------|
| `data/mammr_pairs_public.json` | `844361d0f7bb013f05c5fc3a172d71e8ed15cc9d801e60ac16749508a1c89545` |
| `results/bge-m3-q8_0-pinned-20260506.json` | `2750c0e55d3aefe23189e1cfe86bc31ca3e87d66d791d8d9d0c8e3fd6be63573` |
| `results/snowflake-arctic-l-v2-q8_0-pinned-20260506.json` | `69d65aa56cd750439e1f4ab04041a82a6df57b025ebc7c85401d3f3769d041a9` |
| `results/jina-v3-q8_0-pinned-20260506.json` | `1e028f9d71d069a0d1517b60b21f1a06392f51e77b707375f01f7ac1042f8a76` |
| `results/qwen3-0.6b-q8_0-pinned-20260506.json` | `5ff0ab54db9d5fb1fa758165935703783c689faebf49885b04df9ca7907bd291` |

## Interpretation

The pinned public reruns change the story:

- The sanitized public dataset is not globally broken. Snowflake, BGE-M3, and Jina-v3 all score strongly on the public candidate.
- Qwen3-0.6B is the outlier on the current pinned public backend. It remains a practical production choice for the tested VPS because of size and operational stability, but it is not the public sanitized leaderboard winner.
- The paper should separate production deployment choice from benchmark leaderboard ranking.

## Public Claim Rule

Allowed:

> On the sanitized public v0.1 dataset and pinned CPU-only VPS backend, BGE-M3 had the highest weighted pairwise score among the four P0 local GGUF embedding models tested. Jina-v3 had the highest MRR and Recall@5, while Snowflake stayed close on weighted score.

Allowed:

> Qwen3-0.6B was selected for production because the deployment optimized quality, size, latency, and stability on one constrained VPS.

Not allowed:

> Qwen3-0.6B is the best model in the public sanitized leaderboard.

Not allowed:

> These four reruns prove the best embedding model for every agent memory system.
