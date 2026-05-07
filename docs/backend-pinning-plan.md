# Backend Pinning Plan

Date: 2026-04-27

## Why This Exists

MAMMR public results must be reproducible. The public Qwen3 diagnostic runs found a mismatch between older internal similarity checks and the current benchmark endpoint. That means public comparison runs need a pinned backend, not an informal "whatever service happens to be running" endpoint.

This document defines the minimum metadata every public result file should include before leaderboard claims are made.

Backend pinning is also hardware pinning. The original production deployment was a CPU-only OpenClaw + NoldoMem VPS. Results from Mac Studio, Mac mini, GPU workstation, or dedicated inference hosts should be labeled separately instead of mixed into the VPS recommendation.

## Current Production Snapshot

This snapshot is useful for diagnosis, but it is not yet the final public leaderboard backend.

| Field | Value |
|-------|-------|
| snapshot_time_utc | `2026-04-26T23:54:12Z` |
| host_kernel | `Linux 6.8.0-101-generic x86_64 GNU/Linux` |
| embedding_model | `Qwen3-Embedding-0.6B-Q8_0.gguf` |
| model_sha256 | `06507c7b42688469c4e7298b0a1e16deff06caf291cf0a5b278c308249c3e439` |
| model_size_bytes | `639150592` |
| llama_binary | `llama-server OpenBLAS build` |
| llama_binary_sha256 | `5f2609599bc72850fe0a5349502cdaa137c2477aa620e64eb53ae5c010b0fae7` |
| llama_binary_size_bytes | `13461056` |
| llama_version | `version: 1 (408225b)` |
| pooling | `last` |
| dimensions | `1024` |
| ctx_size | `8192` |
| batch_size | `2048` |
| ubatch_size | `2048` |
| threads | `1` |
| threads_batch | `1` |
| parallel | `2` |
| gpu_layers | `0` |
| cpu_affinity | `8-15` |
| warmup | `disabled` |
| continuous_batching | `disabled` |
| embedding_probe | `hello -> 1024 dimensions` |

## Public Result Metadata Requirement

Every public result should include or document:

1. dataset name and dataset SHA-256
2. script version or commit SHA, when the run is made from a committed public release state
3. model filename and model SHA-256
4. embedding dimensions
5. pooling mode
6. context size
7. batch size and sub-batch size
8. CPU/GPU backend
9. llama.cpp version or commit/build hash
10. local patch set name or hash, if any
11. endpoint label
12. hardware class, such as CPU-only VPS, Apple Silicon local, GPU workstation, or dedicated inference host
13. result file SHA-256 after generation

For API models, replace local backend fields with:

1. provider name
2. provider model id
3. API date or version if exposed
4. request batch size
5. endpoint label
6. dataset SHA-256
7. result file SHA-256

Do not include API keys, account ids, local usernames, hostnames, private IPs, or raw private memory text.

## Required Decision Before Leaderboard Release

Pick one of these paths:

1. **Local pinned backend:** publish GGUF runs from one fixed llama.cpp build and model hash.
2. **API pinned backend:** publish API model results only where provider model ids are stable enough.
3. **Hybrid:** publish local GGUF and API tables separately, with backend metadata in every result.

Recommended path for public v0.1 leaderboard:

- use a local pinned backend for the four P0 local embedding models - complete for the v0.1 candidate
- keep API embeddings in a separate optional table
- rerun Qwen3 after dataset cleanup, using the pinned backend - complete for the v0.1 candidate

## Acceptance Gate

Public leaderboard claims are blocked until:

- the pinned backend is chosen - complete for the v0.1 local-GGUF candidate
- Qwen3, Snowflake Arctic L v2, BGE-M3, and Jina-v3 are rerun on the same sanitized dataset - complete
- each result file contains the run-critical backend metadata above, with script commit deferred until the final public release commit exists - complete for the P0 local-GGUF candidate
- each result file hash is recorded in the summary - complete for the P0 local-GGUF candidate
- the manuscript labels private and public results separately - complete for the current draft
