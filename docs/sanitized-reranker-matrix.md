# Sanitized Public Reranker Matrix

This reranker matrix uses the sanitized public vectors and reranks the top-10 same-category candidates.
It is not a full-corpus reranker benchmark, but it directly checks whether the earlier reranker finding survives on public-safe data.

Scope:

- dataset: `data/mammr_pairs_public.json`
- candidate pool: same category
- top-n: 10
- rerankers: Cohere Rerank 4 Pro and Cohere Rerank v3.5 via OpenRouter
- raw API keys are not stored in result files

## Results

| Embedding | Reranker | Baseline MRR | Reranked MRR | Delta | R@1 | R@5 | Avg ms | Improved | Degraded | Errors |
|-----------|----------|--------------|--------------|-------|-----|-----|--------|----------|----------|--------|
| Snowflake-Arctic-L-v2 Q8_0 | Cohere Rerank 4 Pro | 0.8917 | 0.9553 | 0.0636 | 0.9217 | 1.0000 | 395.1 | 21 | 2 | 0 |
| Snowflake-Arctic-L-v2 Q8_0 | Cohere Rerank v3.5 | 0.8917 | 0.9290 | 0.0374 | 0.8916 | 0.9819 | 406.5 | 17 | 11 | 0 |
| BGE-M3 Q8_0 | Cohere Rerank 4 Pro | 0.9134 | 0.9553 | 0.0420 | 0.9217 | 1.0000 | 367.8 | 15 | 2 | 0 |
| BGE-M3 Q8_0 | Cohere Rerank v3.5 | 0.9134 | 0.9292 | 0.0158 | 0.8916 | 0.9819 | 340.6 | 13 | 10 | 0 |
| Jina-v3 Q8_0 | Cohere Rerank 4 Pro | 0.9257 | 0.9537 | 0.0280 | 0.9217 | 0.9940 | 287.0 | 17 | 6 | 0 |
| Jina-v3 Q8_0 | Cohere Rerank v3.5 | 0.9257 | 0.9283 | 0.0027 | 0.8916 | 0.9819 | 315.3 | 12 | 11 | 0 |
| Qwen3-Embedding-0.6B Q8_0 | Cohere Rerank 4 Pro | 0.4549 | 0.8871 | 0.4322 | 0.8494 | 0.9217 | 413.0 | 100 | 2 | 0 |
| Qwen3-Embedding-0.6B Q8_0 | Cohere Rerank v3.5 | 0.4549 | 0.8705 | 0.4156 | 0.8313 | 0.9096 | 353.4 | 100 | 3 | 0 |

## Average MRR Gain

| Reranker | All four embeddings | Excluding Qwen3 |
|----------|---------------------|-----------------|
| Cohere Rerank 4 Pro | 0.1414 | 0.0445 |
| Cohere Rerank v3.5 | 0.1179 | 0.0186 |

## Interpretation

Cohere Rerank 4 Pro is the strongest reranker in this sanitized matrix.
Cohere Rerank v3.5 is average-positive and MRR-positive for all four embeddings in this rerun, but the gains are smaller and some recall-at-k values can still trade off on already strong baselines.

The Qwen3 gain is large because the baseline public sanitized same-category ranking is weak.
For the already strong Snowflake, BGE-M3, and Jina-v3 baselines, reranker gains are smaller and must be read per model rather than assumed uniform.

This supports the paper claim that reranker choice is a major quality lever, but it should not be overstated as a full production retrieval result because the candidate pool is same-category top-10.
