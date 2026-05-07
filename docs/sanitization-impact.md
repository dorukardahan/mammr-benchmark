# Sanitization Impact

The first public-dataset rerun showed that mechanical sanitization is not enough.

## What Happened

Earlier internal Qwen3 checks looked strong. After mechanically replacing operational project names, domains, IPs, and paths, the public candidate dataset produced a much lower Qwen3 score.

Latest pinned Qwen3 rerun:

- weighted_score: 0.3731
- MRR: 0.4549
- Recall@5: 0.6446
- dataset_sha256: `844361d0f7bb013f05c5fc3a172d71e8ed15cc9d801e60ac16749508a1c89545`

Most Qwen3 failures were high-relevance pairs falling below the `high >= 0.50` similarity threshold. The pinned Qwen3 cleanup queue contains 139 high-pair failures, which is too many to treat as a simple copyediting pass.

The current P0 semantic review covers 7 severe Qwen3 failures. Six are kept as valid hard cases for v0.1 candidate scope, and one compact paraphrase/count case is reserved for human adjudication before a v0.2 label freeze. That makes the evidence stronger: Qwen3 needs backend-specific interpretation and calibration, not just more aggressive text rewriting.

The four-model pinned rerun also showed that Snowflake, BGE-M3, and Jina-v3 score strongly on the same sanitized dataset. Sanitization is a real concern, but it is not enough to explain Qwen3's public rerun drop by itself.

## Why This Matters

This is exactly the kind of issue a serious public benchmark must catch before release.

If we published unreleased internal scores beside a sanitized dataset, developers would rerun the benchmark and get inconsistent results. That would damage trust.

## Likely Causes

1. Some examples relied on real project names as semantic anchors.
2. Mechanical replacement made certain memories less natural.
3. Fixed cosine thresholds are model/backend/dataset sensitive.
4. The current public rerun backend may not match the backend used for older internal checks.

## Backend Drift Is Now A Separate Blocker

Follow-up checks found that some older internal similarity values do not reproduce on the public rerun endpoint even when the texts are tested directly.

This means the public score drop should not be attributed only to sanitization. The release needs both:

1. semantic cleanup of the public dataset, and
2. a pinned, reproducible embedding backend for all public reruns.

See `docs/backend-divergence.md`.

The order matters. Backend pinning should happen before large-scale dataset edits; otherwise we risk rewriting examples to fit a drifting endpoint rather than improving the benchmark.

## Fix Direction

The public dataset should be edited as a real public benchmark, not just sanitized mechanically.

Recommended process:

1. Keep the 21-category structure.
2. Rewrite operationally dependent examples into natural public examples.
3. Preserve the intended semantic relation for each pair.
4. Review P1/P2 Qwen3 failures without tuning the dataset to one model.
5. Keep Qwen3 production-choice claims separate from public leaderboard claims.

## Paper Implication

The public paper should say:

> The benchmark was motivated by production memory. A sanitized public benchmark is released separately because direct release of operational memory is unsafe.

Do not say:

> The sanitized public dataset exactly reproduces unreleased internal results.
