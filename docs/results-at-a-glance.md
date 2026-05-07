# Results At A Glance

This page summarizes the public v0.1 candidate status. Read it together with `docs/backend-divergence.md`.

The current public candidate package passed a 0G Sandbox clean-room preflight for safety, dataset audits, JSON parsing, hash-chain checks, and stale-reference checks. This validates the public release package, not the full model rerun. It does not reproduce operational traces.

## Core Finding

Agent memory retrieval is a different workload from general semantic search. The hard cases are short vague queries, long conversational memories, Turkish-English code-switching, operational state changes, and near-miss false positives.

## Production Motivation

MAMMR was motivated by a real OpenClaw + NoldoMem memory stack on a CPU-only VPS. That production setting shaped the task design: short vague recall queries, long operational memories, Turkish-English code-switching, stale state, and near-miss negatives.

The public repo does not include raw operational traces, vector caches, chat logs, account details, or unreleased benchmark artifacts. The public results below are reproducible with the pinned dataset, model files, pooling modes, llama-server build, and backend metadata, not from the sandbox preflight alone.

## Public v0.1 Pinned Local-GGUF Status

The public dataset is sanitized. The refreshed pinned four-model local-GGUF rerun set is available. This table is ranked by weighted threshold score.

| Rank | Model | Weighted | MRR | Recall@5 |
|------|-------|----------|-----|----------|
| 1 | BGE-M3 Q8_0 | 0.7143 | 0.9134 | 0.9639 |
| 2 | Snowflake-Arctic-L-v2 Q8_0 | 0.6995 | 0.8917 | 0.9578 |
| 3 | Jina-v3 Q8_0 | 0.6956 | 0.9257 | 0.9880 |
| 4 | Qwen3-0.6B Q8_0 | 0.3731 | 0.4549 | 0.6446 |

The public rerun result is useful because it separates two claims that were previously tangled:

- Snowflake, BGE-M3, and Jina-v3 remain strong on the sanitized public set.
- Qwen3-0.6B was a production tradeoff choice on one VPS, not the public sanitized leaderboard winner.

## Full-Corpus And Held-Out Evidence

The same four local-GGUF models were also rerun against mixed public retrieval pools with synthetic public-safe distractors.

Full public corpus plus 96 distractors:
| Model | MRR | Recall@5 | Median Rank |
|-------|-----|----------|-------------|
| BGE-M3 Q8_0 | 0.6053 | 0.8012 | 2 |
| Jina-v3 Q8_0 | 0.6043 | 0.7952 | 2 |
| Snowflake-Arctic-L-v2 Q8_0 | 0.5764 | 0.7530 | 2 |
| Qwen3-Embedding-0.6B Q8_0 | 0.1520 | 0.1747 | 95 |

Held-out mini-set plus 96 distractors:

| Model | MRR | Recall@5 | Median Rank |
|-------|-----|----------|-------------|
| Jina-v3 Q8_0 | 0.7083 | 0.8286 | 1 |
| BGE-M3 Q8_0 | 0.6712 | 0.8286 | 1 |
| Snowflake-Arctic-L-v2 Q8_0 | 0.6208 | 0.8286 | 2 |
| Qwen3-Embedding-0.6B Q8_0 | 0.1338 | 0.2000 | 49 |

See `docs/full-corpus-distractor-results.md` and `docs/heldout-mini-results.md`.

## Sanitized Public Reranker Matrix

The sanitized public reranker matrix reranks top-10 same-category candidates.

| Reranker | Avg MRR Gain | Avg MRR Gain Excluding Qwen3 | Note |
|----------|--------------|------------------------------|------|
| Cohere Rerank 4 Pro | +0.1414 | +0.0445 | strongest average MRR gain among the two hosted rerankers tested |
| Cohere Rerank v3.5 | +0.1179 | +0.0186 | MRR-positive for all four embeddings, but with smaller gains |

See `docs/sanitized-reranker-matrix.md`.

## Practical Takeaways

For CPU-only OpenClaw/NoldoMem VPS users:

- start with small multilingual embedding models
- treat reranking as a major quality lever
- measure latency under real system load
- do not use local CPU rerankers blindly

For stronger local hardware users:

- rerun the benchmark on your own backend
- test larger local models if latency is acceptable
- test local rerankers before paying for hosted reranking

## Domain Coverage

The public v0.1 candidate is strongest for multilingual agent memory, technical operations, and near-miss control cases.
It is not a broad-domain benchmark.

Current aggregate coverage is documented in `docs/domain-coverage.md`.
The domain report is text-safe: it summarizes category groups and cue counts without printing query or document text.

## Runtime Extensions

NoldoMem started as the memory backend for the motivating OpenClaw deployment. A useful downstream direction is a generic external-runtime adapter pattern so other agent runtimes can call a memory service through a small HTTP boundary. That work is useful for agent-memory users, but it is not counted as primary benchmark evidence for the public v0.1 release.
