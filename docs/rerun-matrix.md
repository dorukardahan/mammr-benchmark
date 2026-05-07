# Public v0.1 Rerun Matrix

The public dataset is sanitized. Because sanitization can change embedding similarities, public leaderboard claims must use reruns on `data/mammr_pairs_public.json`.

The production choice came from a CPU-only OpenClaw + NoldoMem VPS. Public reruns should record the target hardware. Stronger local machines may support larger local embeddings or rerankers than the original VPS.

## Current Rerun Status

The P0 local-GGUF embedding rerun set is complete on the sanitized public dataset with pinned backend metadata. Full-corpus+distractor retrieval, held-out mini-set retrieval, and a Cohere public reranker matrix are also complete for the same four local-GGUF baselines.

See `docs/pinned-public-reruns.md` and `results/public-v0.1-summary.md`.

## Minimum Rerun Set

Run these before publishing a public leaderboard table:

| Priority | Model | Why |
|----------|-------|-----|
| P0 | Qwen3-Embedding-0.6B Q8_0 | Complete. Production tradeoff model, but weak on current pinned public rerun. |
| P0 | Snowflake Arctic L v2 Q8_0 | Complete. Strong public weighted score and close full-corpus result. |
| P0 | BGE-M3 Q8_0 | Complete. Highest pinned public weighted score and strongest full-corpus MRR. |
| P0 | Jina-v3 Q8_0 | Complete. Highest same-category MRR and Recall@5 among P0 local GGUF reruns. |
| P1 | Codestral Embed | Strong API MRR baseline. |
| P1 | OpenAI text-embedding-3-large | Widely known API model. |
| P1 | Nomic Embed v2 MOE Q8_0 | Useful small/local comparison model. |
| P1 | EmbeddingGemma 300M Q8_0 | Small model comparison. |

## Minimum Reranker Rerun Set

The sanitized public Cohere reranker matrix is complete for top-10 same-category candidates across Qwen3, Snowflake, BGE-M3, and Jina-v3. Future reranker work should extend the matrix rather than replace it.

| Priority | Reranker | Top-N |
|----------|----------|-------|
| P0 | Cohere Rerank 4 Pro | 5, 10, 20 |
| P0 | Cohere Rerank v3.5 | 5, 10, 20 |
| P1 | Qwen3 local reranker | 10, 20 |
| P1 | BGE local reranker | 10, 20 |

## Acceptance Rules

Public v0.1 four-model local-GGUF comparison is allowed because:

1. every listed P0 embedding result was generated on the sanitized public dataset
2. result JSONs do not contain raw operational text
3. scripts can be run by another developer using documented commands
4. paper tables identify whether results are public sanitized reruns or future work
5. claim language matches the evidence
6. hardware and backend metadata are recorded before making production recommendations

Broader leaderboard claims still require human review, larger independent distractor evidence, and more non-DevOps domains.

## Claim Rules

> On the sanitized public v0.1 dataset, model X scored Y.

Not allowed until proven:

> Sanitization has no effect.

Not allowed:

> This is the definitive embedding leaderboard for all agent memory systems.

Not allowed:

> The VPS production choice is the best deployment choice for every hardware setup.
