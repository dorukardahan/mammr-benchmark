# Held-Out Mini-Set Results

The held-out mini-set was generated after the public v0.1 thresholds were frozen.
It is used as a small sanity check against threshold and cleanup overfitting.

Scope:

- dataset: `data/heldout_mini_public.json`
- dataset SHA-256: `48d97350d1ffaaa87834c31ffd3877ca94000665657cad5afb9d8979f9622c75`
- high-relevance queries: 35
- public candidate documents: 60
- synthetic distractors: 96
- total candidate documents: 156

## Results

| Model | MRR | Recall@1 | Recall@5 | Recall@20 | Median Rank | Max Rank |
|-------|-----|----------|----------|-----------|-------------|----------|
| Snowflake-Arctic-L-v2 Q8_0 | 0.6208 | 0.4857 | 0.8286 | 0.9429 | 2 | 51 |
| BGE-M3 Q8_0 | 0.6712 | 0.5429 | 0.8286 | 0.9429 | 1 | 39 |
| Jina-v3 Q8_0 | 0.7083 | 0.6000 | 0.8286 | 0.9143 | 1 | 102 |
| Qwen3-Embedding-0.6B Q8_0 | 0.1338 | 0.0571 | 0.2000 | 0.2571 | 49 | 153 |

## Interpretation

BGE-M3, Jina-v3, and Snowflake remain strong on the held-out mini-set.
Qwen3-Embedding-0.6B again performs poorly on the sanitized public-style task.

This is useful evidence that the public v0.1 result is not only an artifact of the original 305-pair set.
It is still a small mini-set, so it should be reported as additional evidence, not as a replacement for a larger independent test set.
