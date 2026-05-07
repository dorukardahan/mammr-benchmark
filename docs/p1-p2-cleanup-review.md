# P1/P2 Cleanup Review

Updated: 2026-05-06

This review covers the broader high-pair cleanup question after the pinned four-model public reruns.

The goal is to avoid two bad outcomes:

1. shipping mechanically damaged public text, or
2. overfitting the public dataset to one embedding backend.

## Evidence Used

- Public dataset SHA-256: `844361d0f7bb013f05c5fc3a172d71e8ed15cc9d801e60ac16749508a1c89545`
- Qwen3 pinned cleanup queue: local generated queue, summarized in `docs/cleanup-candidate-triage.md`
- Cross-model overlap review: `docs/pinned-failure-overlap-review.md`
- P0 semantic review: `docs/p0-cleanup-review.md`

## Key Finding

Qwen3 produces many more high-pair threshold failures than the other pinned local GGUF baselines on the same sanitized public dataset.

| Model | High-Pair Failures |
|-------|--------------------|
| Snowflake-Arctic-L-v2 Q8_0 | 45 |
| BGE-M3 Q8_0 | 13 |
| Jina-v3 Q8_0 | 10 |
| Qwen3-0.6B Q8_0 | 139 |

Only 9 high pairs fail under all three stronger public baselines, and those same 9 also fail under Qwen3. By contrast, 97 high-pair failures are Qwen-only.

## Strong-Baseline Manual Review

The high pairs failed by Snowflake, BGE-M3, and Jina-v3 were manually reviewed. After the final public-safety rewrite and rerun, this queue contains 9 pairs.

| Category | Count | Decision |
|----------|-------|----------|
| temporal | 2 | Keep. These test vague time recall and month anchoring. |
| conversational_recall | 1 | Keep. This is an intentionally short conversational reference. |
| turkish_chars | 3 | Keep. These test accented Turkish query against unaccented text. |
| context_implicit | 1 | Keep. This tests context-dependent shorthand. |
| noise_typo | 1 | Keep. This intentionally tests typo robustness. |
| partial_match | 1 | Keep. This tests useful but incomplete recall under hard phrasing. |

Decision: no pair was rewritten in this pass.

## Why No Mass Rewrite

The Qwen3 queue contains many legitimate agent-memory cases that Snowflake, BGE-M3, and Jina-v3 pass comfortably. Rewriting those pairs would make the dataset easier for Qwen3 rather than cleaner for the benchmark.

The public candidate should preserve hard cases:

- short vague Turkish recall
- typo and diacritic normalization
- relative time references
- implicit context
- command/config/log style memories

These are central to agent memory retrieval. Making every high pair explicit and easy would weaken the benchmark.

## Actual Cleanup Already Done

The cleanup work that did change the dataset was limited to public-release issues:

- stale model references were normalized
- Turkish character consistency was checked
- fake-looking token fragments were removed
- operator-specific names and overly conversational source phrasing were replaced with generic public examples

Those edits improved safety and readability without changing the benchmark skills.

## Release Decision

For public v0.1 candidate:

- keep the current dataset SHA as the candidate artifact
- do not tune text to Qwen3
- label Qwen3 public rerun as backend-specific diagnostic evidence
- use Snowflake/BGE/Jina agreement to decide future cleanup targets
- reserve larger rewrites for v0.2 after human review and larger-domain validation

## Remaining Risk

The dataset is still single-author and domain-heavy. A second-model review and held-out mini-set now exist, so the right next quality step is human adjudication of disagreements and broader-domain validation, not another ad hoc rewrite pass.
