# Full-Corpus And Distractor Retrieval Results

This evaluation ranks each high-relevance query against the full sanitized public document pool plus synthetic public-safe distractors.

Scope:

- dataset: `data/mammr_pairs_public.json`
- dataset SHA-256: `844361d0f7bb013f05c5fc3a172d71e8ed15cc9d801e60ac16749508a1c89545`
- distractors: `data/synthetic_distractors_public.json`
- distractors SHA-256: `4024f98fae0ed6d6ae4df2f99e0fd03087078813be83850df0c12afd9dd2b13d`
- high-relevance queries: 166
- public candidate documents: 303
- synthetic distractors: 96 rows from 24 base public-safe distractor topics
- total candidate documents: 399

## Results

| Model | MRR | Recall@1 | Recall@5 | Recall@20 | Median Rank | Max Rank |
|-------|-----|----------|----------|-----------|-------------|----------|
| Snowflake-Arctic-L-v2 Q8_0 | 0.5764 | 0.4458 | 0.7530 | 0.9036 | 2 | 225 |
| BGE-M3 Q8_0 | 0.6053 | 0.4518 | 0.8012 | 0.9157 | 2 | 325 |
| Jina-v3 Q8_0 | 0.6043 | 0.4639 | 0.7952 | 0.9337 | 2 | 272 |
| Qwen3-Embedding-0.6B Q8_0 | 0.1520 | 0.1205 | 0.1747 | 0.2651 | 95 | 392 |

## Interpretation

Snowflake, BGE-M3, and Jina-v3 all have median rank 2 in the mixed public pool, but the Recall@5 values and max ranks show nontrivial tail failures.
BGE-M3 Q8_0 has the highest full-corpus MRR point estimate in this run by a very small margin over Jina-v3 Q8_0, and BGE-M3 Q8_0 has the strongest Recall@5 among the three strong baselines.

The distractors are synthetic and public-safe. They are useful for a harder smoke test than same-category ranking, but the 96 rows come from 24 base distractor topics with templated prefixes. Absolute MRR and Recall@k should therefore be expected to change on a larger, more diverse independent corpus.

Qwen3-Embedding-0.6B remains weak on the sanitized public full-corpus task.
This reinforces the release framing: Qwen3 was a practical production choice on one CPU-only VPS, not the sanitized public leaderboard winner.
