# Production Migration Follow-Up

This note records a public-safe deployment follow-up after the MAMMR v0.1 candidate was published.

It is not new benchmark evidence and it does not change the frozen public result files. It shows how the benchmark was used to make a real memory-stack decision.

## What Changed

The motivating OpenClaw + NoldoMem deployment was migrated from Qwen3-Embedding-0.6B Q8_0 to BGE-M3 Q8_0 after the pinned public reruns and private production canaries both favored BGE-M3 for this memory workload.

| Layer | Before | After |
|-------|--------|-------|
| Embedding model | Qwen3-Embedding-0.6B Q8_0 | BGE-M3 Q8_0 |
| Dimensions | 1024 | 1024 |
| Pooling | `last` | `cls` |
| Reranker | Cohere Rerank 4 Pro | Cohere Rerank 4 Pro |

The dimensions did not change, but the vectors are still not interchangeable. A 1024-dimensional Qwen vector and a 1024-dimensional BGE-M3 vector live in different embedding spaces.

## Migration Pattern

The safe migration pattern was:

1. snapshot the production memory databases and config
2. verify that the target model returns the expected 1024-dimensional vectors
3. reindex every active memory with one embedding model
4. verify row counts, vector coverage, and database integrity
5. swap the reindexed databases during a short maintenance window
6. keep rollback snapshots until the new stack is stable
7. run real recall canaries without publishing private memory text

For this deployment, the heavy reindex work was done off the VPS on a local CPU backend, then swapped back after hash and coverage checks. This reduced production downtime and avoided CPU contention with the live agent system.

## Verification Summary

The private production canary verified the following aggregate conditions:

- embedding endpoint returned 1024-dimensional BGE-M3 vectors
- active vectorless memory count was zero
- active memory rows and vector rows matched after reindex
- recall returned results with semantic search active
- returned results had positive semantic scores
- hosted reranker scores were present and positive
- fresh recall latency stayed in the low-single-digit second range
- repeated recall benefited from cache without disabling semantic search

No raw memories, queries, account identifiers, paths, tokens, or operational traces are published with this note.

## What This Means For Users

For CPU-only OpenClaw/NoldoMem-style deployments, BGE-M3 Q8_0 is now the stronger default candidate from this evidence package, with hosted reranking kept as the quality lever.

Do not treat this as a universal rule:

- rerun the benchmark on your own backend
- record pooling mode and backend metadata
- do not mix vectors from different models or backends
- verify production recall, not only benchmark scores
- keep a rollback path before swapping a live memory database

## Claim Boundary

Safe claim:

> MAMMR informed a real production migration from Qwen3-Embedding-0.6B Q8_0 to BGE-M3 Q8_0 for one CPU-only OpenClaw/NoldoMem memory stack.

Unsafe claim:

> BGE-M3 is the best embedding model for every agent memory system.
