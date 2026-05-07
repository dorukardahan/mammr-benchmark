# Backend and Reproducibility Metadata

Date: 2026-05-06

This file records the benchmark backend metadata that should be reflected in the paper appendix or artifact release.

## Benchmark Backend Snapshot

Source: benchmark backend snapshot. Absolute paths, hostnames, account identifiers, and public network details are not included.

```text
Binary: <llama-openblas-dir>/llama-server
Model: <model-dir>/Qwen3-Embedding-0.6B-Q8_0.gguf
Mode: --embedding --pooling last
Bind: loopback interface for the benchmark run
ctx-size: 8192
batch-size: 2048
ubatch-size: 2048
threads: 1
threads-batch: 1
parallel: 2
n-gpu-layers: 0
flags: --no-warmup --cache-ram 0 --slot-prompt-similarity 0 --no-cont-batching
```

Benchmark binary:

```text
<llama-openblas-dir>/llama-server
version: 1 (408225b)
built with GNU 13.3.0 for Linux x86_64
sha256: 5f2609599bc72850fe0a5349502cdaa137c2477aa620e64eb53ae5c010b0fae7
```

## Local GGUF Files Available During Benchmark

| File | Size bytes |
|------|------------|
| Qwen3-Embedding-0.6B-Q8_0.gguf | 639150592 |
| Qwen3-Embedding-4B-Q4_K_M.gguf | 2496703776 |
| Qwen3-Embedding-4B-Q8_0.gguf | 4279660224 |
| bge-m3-Q8_0.gguf | 634553760 |
| granite-278m-multilingual-Q8_0.gguf | 303137952 |
| hf_ggml-org_embeddinggemma-300M-Q8_0.gguf | 328576992 |
| jina-embeddings-v3-Q8_0.gguf | 600995424 |
| kalm-multilingual-mini-v1.5-Q8_0.gguf | 531065504 |
| multilingual-e5-large-instruct-Q8_0.gguf | 603097568 |
| nomic-embed-text-v2-moe-Q8_0.gguf | 512225120 |
| snowflake-arctic-embed-l-v2.0-Q8_0.gguf | 634554752 |

Reranker GGUF files:

| File | Size bytes |
|------|------------|
| bge-reranker-v2-m3-q8_0.gguf | 635674304 |
| jina-reranker-v2-base-multilingual-q8_0.gguf | 305339680 |
| qwen3-reranker-0.6b-q8_0.gguf | 639153184 |

Note: `gte-multilingual-base-Q8_0.gguf` exists as a zero-byte file and should not be listed as a valid evaluated artifact.

## Required Artifact Metadata For Final Release

For each benchmark result JSON, include or document:

- model display name
- provider or local file name
- quantization
- pooling mode
- embedding dimensionality
- backend or API endpoint family
- llama.cpp build/version for local models
- CPU/GPU backend
- context size
- batch size
- benchmark timestamp

The pinned public local-GGUF result JSONs now carry backend metadata. This appendix remains useful because it explains the metadata contract and records the benchmark backend context behind the public reruns.

## 2026-04-17 Public Rerun Diagnostic

The first sanitized public Qwen3 rerun used the then-current benchmark endpoint and batch size 1.

Result:

- weighted_score: 0.3499
- MRR: 0.3654
- Recall@5: 0.5904
- dataset_sha256: `886d4ba4ec43600c9f1ee14b7d4cf4707f40edd2e9cb050891c9fbff2c359281`
- endpoint_label: `diagnostic-qwen3-openblas-408225b`
- dimensions: 1024
- batch_size: 1
- result_sha256: `6714c827d555a2ff047da27b251e23be2ab0f2a4294d41a195050ec4d4d5f23a`

This run should not be treated as a public leaderboard result.

## 2026-05-05 Public Rerun Diagnostic

The second sanitized public Qwen3 rerun used the audited public dataset after a small stale-reference cleanup and P0 semantic review.

Result:

- weighted_score: 0.3545
- MRR: 0.3791
- Recall@5: 0.5964
- dataset_sha256: `68743ae59481807ce00ed1f218831f98d3d4ade62d064dd1dde4be2c676c2ff8`
- endpoint_label: `diagnostic-qwen3-openblas-408225b-rerun-20260505`
- dimensions: 1024
- batch_size: 1
- result_sha256: `08cad69f7d9ca6915d0cb237e26f097806ace8580418b881248af035f83c3e9c`

This run also should not be treated as a public leaderboard result. It is evidence that the P0 failures are not explained by obvious broken pair text alone.

Reason:

- Some older internal similarity checks did not reproduce on the public rerun endpoint.
- Same-text cosine remains 1.0, so the endpoint is functional.
- The issue is likely backend/config drift, threshold calibration, sanitized anchor loss, or a combination of these. It is not a blank or random embedding response.

Publication implication:

- Production deployment decisions and public sanitized reruns must be clearly separated.
- Public leaderboard claims require rerunning all compared models on a pinned backend with recorded metadata.

## 2026-05-06 Controlled Public Reranker Matrix

The sanitized public reranker matrix was rerun with public-safe vectors and top-10 same-category candidates.

Scope:

- embeddings: Qwen3-0.6B Q8_0, Snowflake Arctic L v2 Q8_0, BGE-M3 Q8_0, Jina-v3 Q8_0
- rerankers: Cohere Rerank 4 Pro and Cohere Rerank v3.5 via OpenRouter
- candidate pool: same category
- top-n: 10
- result files: `results/reranker/*20260506.json`

Result summary:

- all eight result files have `rerank_errors=0`
- Cohere Rerank 4 Pro average MRR gain: +0.1414 across all four embeddings, +0.0445 excluding Qwen3
- Cohere Rerank v3.5 average MRR gain: +0.1179 across all four embeddings, +0.0186 excluding Qwen3

Cohere Rerank 4 Pro improved MRR for all four embedding baselines. Cohere Rerank v3.5 was also MRR-positive for all four embeddings in this rerun, but with smaller gains and some recall-at-k tradeoffs on already strong baselines.

This is controlled public reranker evidence. It is still not a full production retrieval benchmark because the candidate pool is same-category top-10.
