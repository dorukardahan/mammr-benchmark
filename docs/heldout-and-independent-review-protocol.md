# Held-Out And Independent Review Protocol

Updated: 2026-05-06

This protocol defines the validation evidence added after the first public v0.1 candidate. The held-out set remains separated from threshold calibration and public dataset cleanup.

## Goal

Reduce three risks:

1. threshold calibration bias,
2. single-author label bias,
3. overfitting cleanup to one embedding backend.

## Held-Out Mini-Set

Create 50 to 100 new pairs after the v0.1 thresholds and public dataset are frozen.

Suggested composition:

| Group | Count |
|-------|-------|
| vague conversational recall | 15 |
| temporal and stale-state recall | 15 |
| Turkish morphology, Turkish chars, and code-switching | 20 |
| technical logs, commands, and config memories | 15 |
| negative, low, and near-miss false positives | 20 |

Rules:

- Do not copy exact v0.1 examples.
- Do not use the held-out set to recalibrate thresholds.
- Keep hardware/backend metadata identical to the main public rerun when comparing models.
- Report held-out metrics separately from v0.1. For pairwise calibration runs,
  report weighted score and label-level pass rates. For retrieval runs, report
  MRR, Recall@5, and rank statistics.
- If held-out performance contradicts v0.1, report the contradiction instead of hiding it.

Current status:

- completed: `data/heldout_mini_public.json`
- pairs: 60
- SHA-256: `48d97350d1ffaaa87834c31ffd3877ca94000665657cad5afb9d8979f9622c75`
- result summary: `docs/heldout-mini-results.md`
- quality report: `docs/heldout-mini-quality-report.md`

## Independent Label Review

Sample 100 existing public pairs with deterministic seed.

Minimum requirements:

- hide the existing `expected` label from the reviewer,
- show only pair ID, category, query, and document,
- ask for one of `high`, `medium_high`, `medium`, `low`,
- include a short optional rationale field,
- report agreement rate and disagreement counts by category.

Reviewer rubric:

| Label | Meaning |
|-------|---------|
| high | The document directly answers or strongly satisfies the recall query. |
| medium_high | The document is useful but incomplete or less direct. |
| medium | The document is related but would not be enough alone. |
| low | The document is irrelevant, misleading, stale, or a false positive. |

Disagreement policy:

- Do not automatically change labels.
- Review disagreements manually.
- Change a label only when the original label is clearly wrong under the rubric.
- Keep a disagreement appendix with pair IDs, categories, old label, reviewer label, and final decision.

Current status:

- sample: `data/independent_review_sample_20260506.json`
- review file: `data/independent_label_review_codex_20260506.json`
- summary: `docs/independent-label-review-codex-20260506.md`
- agreement: 80 / 100 = 0.8000
- caveat: this is a second-model review, not a human inter-annotator agreement study.

## Release Use

Public v0.1 can ship without this protocol being complete if it is labeled as a candidate release.

A stronger v0.2 or paper-submission claim should not ship until:

- human review is added for the disagreement sample or a fresh blinded subset,
- disagreements are adjudicated,
- larger distractor or production-like retrieval evidence is added,
- non-DevOps domains are expanded.
