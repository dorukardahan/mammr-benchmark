# Pinned Failure Overlap Review

Updated: 2026-05-06

This review compares high-label failures across the four pinned public local-GGUF reruns. It is public-safe: it reports pair IDs, categories, and scores, but not source text.

## Model Summaries

| Model | Weighted | MRR | Recall@5 | Total Fail | High Fail | Dataset SHA |
|-------|----------|-----|----------|------------|-----------|-------------|
| Snowflake-Arctic-L-v2 Q8_0 | 0.6995 | 0.8917 | 0.9578 | 96 | 45 | `844361d0f7bb` |
| BGE-M3 Q8_0 | 0.7143 | 0.9134 | 0.9639 | 91 | 13 | `844361d0f7bb` |
| Jina-v3 Q8_0 | 0.6956 | 0.9257 | 0.9880 | 95 | 10 | `844361d0f7bb` |
| Qwen3-0.6B Q8_0 | 0.3731 | 0.4549 | 0.6446 | 187 | 139 | `844361d0f7bb` |

## Overlap Summary

| Measure | Count |
|---------|-------|
| unique_high_failures_any_model | 142 |
| failed_all_models | 9 |
| failed_all_strong_baselines | 9 |
| qwen_only_high_failures | 97 |

Failure count distribution means how many models failed the same high pair.

| Failed Model Count | High Pair Count |
|--------------------|-----------------|
| 1 | 100 |
| 2 | 28 |
| 3 | 5 |
| 4 | 9 |

## Interpretation

The current public dataset is not globally broken: Snowflake, BGE-M3, and Jina-v3 stay strong on the same sanitized pairs. Most Qwen3 high failures are Qwen-only, so the dataset should not be mass-rewritten to improve one model.

The strongest cleanup candidates are the pairs failed by all three strong baselines. Those are more likely to expose ambiguous wording, sanitization damage, or genuinely difficult retrieval cases.

## Strong-Baseline Failure Queue

| Pair ID | Category | Failed Models | Similarities |
|---------|----------|---------------|--------------|
| `mammr-v0.1-0181` | temporal | BGE-M3 Q8_0, Jina-v3 Q8_0, Qwen3-0.6B Q8_0, Snowflake-Arctic-L-v2 Q8_0 | Snowflake-Arctic-L-v2 Q8_0: 0.2132, BGE-M3 Q8_0: 0.3047, Jina-v3 Q8_0: 0.3312, Qwen3-0.6B Q8_0: 0.1896 |
| `mammr-v0.1-0275` | partial_match | BGE-M3 Q8_0, Jina-v3 Q8_0, Qwen3-0.6B Q8_0, Snowflake-Arctic-L-v2 Q8_0 | Snowflake-Arctic-L-v2 Q8_0: 0.1557, BGE-M3 Q8_0: 0.3083, Jina-v3 Q8_0: 0.4564, Qwen3-0.6B Q8_0: 0.2530 |
| `mammr-v0.1-0108` | conversational_recall | BGE-M3 Q8_0, Jina-v3 Q8_0, Qwen3-0.6B Q8_0, Snowflake-Arctic-L-v2 Q8_0 | Snowflake-Arctic-L-v2 Q8_0: 0.2185, BGE-M3 Q8_0: 0.4297, Jina-v3 Q8_0: 0.3949, Qwen3-0.6B Q8_0: 0.2892 |
| `mammr-v0.1-0264` | context_implicit | BGE-M3 Q8_0, Jina-v3 Q8_0, Qwen3-0.6B Q8_0, Snowflake-Arctic-L-v2 Q8_0 | Snowflake-Arctic-L-v2 Q8_0: 0.2538, BGE-M3 Q8_0: 0.4445, Jina-v3 Q8_0: 0.4158, Qwen3-0.6B Q8_0: 0.2559 |
| `mammr-v0.1-0178` | temporal | BGE-M3 Q8_0, Jina-v3 Q8_0, Qwen3-0.6B Q8_0, Snowflake-Arctic-L-v2 Q8_0 | Snowflake-Arctic-L-v2 Q8_0: 0.3217, BGE-M3 Q8_0: 0.4544, Jina-v3 Q8_0: 0.4665, Qwen3-0.6B Q8_0: 0.2098 |
| `mammr-v0.1-0146` | turkish_chars | BGE-M3 Q8_0, Jina-v3 Q8_0, Qwen3-0.6B Q8_0, Snowflake-Arctic-L-v2 Q8_0 | Snowflake-Arctic-L-v2 Q8_0: 0.2986, BGE-M3 Q8_0: 0.4027, Jina-v3 Q8_0: 0.4277, Qwen3-0.6B Q8_0: 0.3388 |
| `mammr-v0.1-0147` | turkish_chars | BGE-M3 Q8_0, Jina-v3 Q8_0, Qwen3-0.6B Q8_0, Snowflake-Arctic-L-v2 Q8_0 | Snowflake-Arctic-L-v2 Q8_0: 0.2850, BGE-M3 Q8_0: 0.3638, Jina-v3 Q8_0: 0.4122, Qwen3-0.6B Q8_0: 0.4340 |
| `mammr-v0.1-0141` | turkish_chars | BGE-M3 Q8_0, Jina-v3 Q8_0, Qwen3-0.6B Q8_0, Snowflake-Arctic-L-v2 Q8_0 | Snowflake-Arctic-L-v2 Q8_0: 0.3202, BGE-M3 Q8_0: 0.4129, Jina-v3 Q8_0: 0.3423, Qwen3-0.6B Q8_0: 0.4227 |
| `mammr-v0.1-0196` | noise_typo | BGE-M3 Q8_0, Jina-v3 Q8_0, Qwen3-0.6B Q8_0, Snowflake-Arctic-L-v2 Q8_0 | Snowflake-Arctic-L-v2 Q8_0: 0.3677, BGE-M3 Q8_0: 0.4661, Jina-v3 Q8_0: 0.4516, Qwen3-0.6B Q8_0: 0.3814 |

## Qwen-Only Failure Sample

These are diagnostic examples showing why Qwen3 should be treated as backend-specific evidence, not as a cleanup oracle.

| Pair ID | Category | Similarities |
|---------|----------|--------------|
| `mammr-v0.1-0174` | temporal | Snowflake-Arctic-L-v2 Q8_0: 0.5216, BGE-M3 Q8_0: 0.5621, Jina-v3 Q8_0: 0.6202, Qwen3-0.6B Q8_0: 0.1504 |
| `mammr-v0.1-0259` | context_implicit | Snowflake-Arctic-L-v2 Q8_0: 0.7139, BGE-M3 Q8_0: 0.7649, Jina-v3 Q8_0: 0.8155, Qwen3-0.6B Q8_0: 0.1806 |
| `mammr-v0.1-0272` | partial_match | Snowflake-Arctic-L-v2 Q8_0: 0.5058, BGE-M3 Q8_0: 0.5259, Jina-v3 Q8_0: 0.6494, Qwen3-0.6B Q8_0: 0.1980 |
| `mammr-v0.1-0009` | short_query_long_memory | Snowflake-Arctic-L-v2 Q8_0: 0.6991, BGE-M3 Q8_0: 0.7252, Jina-v3 Q8_0: 0.8152, Qwen3-0.6B Q8_0: 0.1992 |
| `mammr-v0.1-0234` | synonym_alias | Snowflake-Arctic-L-v2 Q8_0: 0.5316, BGE-M3 Q8_0: 0.5936, Jina-v3 Q8_0: 0.7570, Qwen3-0.6B Q8_0: 0.2007 |
| `mammr-v0.1-0175` | temporal | Snowflake-Arctic-L-v2 Q8_0: 0.6580, BGE-M3 Q8_0: 0.7031, Jina-v3 Q8_0: 0.8131, Qwen3-0.6B Q8_0: 0.2020 |
| `mammr-v0.1-0271` | partial_match | Snowflake-Arctic-L-v2 Q8_0: 0.5714, BGE-M3 Q8_0: 0.6430, Jina-v3 Q8_0: 0.6812, Qwen3-0.6B Q8_0: 0.2048 |
| `mammr-v0.1-0274` | partial_match | Snowflake-Arctic-L-v2 Q8_0: 0.5721, BGE-M3 Q8_0: 0.6876, Jina-v3 Q8_0: 0.7499, Qwen3-0.6B Q8_0: 0.2054 |
| `mammr-v0.1-0131` | crosslingual | Snowflake-Arctic-L-v2 Q8_0: 0.7626, BGE-M3 Q8_0: 0.8666, Jina-v3 Q8_0: 0.9030, Qwen3-0.6B Q8_0: 0.2119 |
| `mammr-v0.1-0204` | noise_typo | Snowflake-Arctic-L-v2 Q8_0: 0.7621, BGE-M3 Q8_0: 0.7170, Jina-v3 Q8_0: 0.8131, Qwen3-0.6B Q8_0: 0.2120 |
| `mammr-v0.1-0001` | short_query_long_memory | Snowflake-Arctic-L-v2 Q8_0: 0.5377, BGE-M3 Q8_0: 0.5448, Jina-v3 Q8_0: 0.6861, Qwen3-0.6B Q8_0: 0.2250 |
| `mammr-v0.1-0117` | conversational_recall | Snowflake-Arctic-L-v2 Q8_0: 0.6445, BGE-M3 Q8_0: 0.6600, Jina-v3 Q8_0: 0.7702, Qwen3-0.6B Q8_0: 0.2302 |
| `mammr-v0.1-0276` | partial_match | Snowflake-Arctic-L-v2 Q8_0: 0.6404, BGE-M3 Q8_0: 0.6216, Jina-v3 Q8_0: 0.7675, Qwen3-0.6B Q8_0: 0.2311 |
| `mammr-v0.1-0126` | crosslingual | Snowflake-Arctic-L-v2 Q8_0: 0.7646, BGE-M3 Q8_0: 0.8094, Jina-v3 Q8_0: 0.8482, Qwen3-0.6B Q8_0: 0.2313 |
| `mammr-v0.1-0134` | crosslingual | Snowflake-Arctic-L-v2 Q8_0: 0.6844, BGE-M3 Q8_0: 0.7470, Jina-v3 Q8_0: 0.7637, Qwen3-0.6B Q8_0: 0.2315 |
| `mammr-v0.1-0038` | code_switching | Snowflake-Arctic-L-v2 Q8_0: 0.6792, BGE-M3 Q8_0: 0.6152, Jina-v3 Q8_0: 0.7663, Qwen3-0.6B Q8_0: 0.2316 |
| `mammr-v0.1-0005` | short_query_long_memory | Snowflake-Arctic-L-v2 Q8_0: 0.6000, BGE-M3 Q8_0: 0.6211, Jina-v3 Q8_0: 0.7325, Qwen3-0.6B Q8_0: 0.2383 |
| `mammr-v0.1-0292` | code_to_description | Snowflake-Arctic-L-v2 Q8_0: 0.5379, BGE-M3 Q8_0: 0.6526, Jina-v3 Q8_0: 0.6846, Qwen3-0.6B Q8_0: 0.2403 |
| `mammr-v0.1-0089` | turkish_morphology | Snowflake-Arctic-L-v2 Q8_0: 0.7295, BGE-M3 Q8_0: 0.8883, Jina-v3 Q8_0: 0.8816, Qwen3-0.6B Q8_0: 0.2503 |
| `mammr-v0.1-0170` | paraphrase | Snowflake-Arctic-L-v2 Q8_0: 0.6930, BGE-M3 Q8_0: 0.6630, Jina-v3 Q8_0: 0.6944, Qwen3-0.6B Q8_0: 0.2522 |

## Decision

- Do not rewrite P1/P2 pairs solely because Qwen3 fails them.
- Manually review the strong-baseline failure queue first.
- Keep Qwen3 production discussion scoped to VPS deployment tradeoffs, not public leaderboard dominance.
- Keep unreleased operational checks separate from public pinned reruns.
