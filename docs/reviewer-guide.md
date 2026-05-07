# Reviewer Guide

This guide is for people reviewing MAMMR public v0.1 for correctness, privacy, or methodology.

## One-Sentence Claim

MAMMR is a production-informed benchmark for multilingual agent memory retrieval, focused on short vague queries, long conversational memories, Turkish-English code-switching, operational state, and near-miss false positives.

## What This Release Claims

Allowed claims:

- MAMMR is a scoped benchmark for agent memory retrieval, not generic semantic search.
- The public v0.1 candidate contains a sanitized 305-pair dataset and a runnable embedding evaluator.
- Four local-GGUF embedding models were rerun on the sanitized public dataset with pinned backend metadata.
- BGE-M3, Snowflake Arctic L v2, and Jina-v3 formed the strongest group on the sanitized public rerun.
- Qwen3-Embedding-0.6B Q8_0 was a practical initial production choice for one CPU-only VPS, but it is not the public sanitized leaderboard winner.
- The motivating deployment later migrated to BGE-M3 Q8_0 after the pinned public reruns and private production canaries.
- Cohere Rerank 4 Pro and Cohere Rerank v3.5 improved top-10 same-category MRR in the public reranker matrix.
- The public candidate package passed local preflight and 0G Sandbox clean-room validation.

## What This Release Does Not Claim

Do not read this release as claiming:

- MAMMR is a final universal embedding leaderboard.
- The sanitized public dataset exactly reproduces unreleased internal rankings.
- One model stack is best for every OpenClaw or agent-memory user.
- 0G Sandbox validation reproduces private production traces.
- The current reranker matrix is a full production retrieval benchmark.
- The label review is human inter-annotator agreement.

## Fast Review Path

Read these files first:

1. `README.md` - scope, quick start, release principle
2. `RELEASE-MANIFEST.md` - frozen hashes, headline metrics, validation record
3. `docs/results-at-a-glance.md` - short evidence summary
4. `docs/publication-scorecard.md` - allowed and disallowed claims
5. `docs/public-scope-and-privacy-review.md` - public/private boundary
6. `paper/manuscript.md` - technical report draft

## Reproduction Checks

Run the release preflight:

```bash
python3 scripts/public_release_preflight.py
```

Expected final line:

```text
PUBLIC PREFLIGHT PASSED
```

Verify the dataset hash:

```bash
python3 - <<'PY'
from pathlib import Path
import hashlib
print(hashlib.sha256(Path("data/mammr_pairs_public.json").read_bytes()).hexdigest())
PY
```

Expected:

```text
844361d0f7bb013f05c5fc3a172d71e8ed15cc9d801e60ac16749508a1c89545
```

Dry-run the evaluator:

```bash
python3 scripts/run_embedding_eval.py --dry-run
```

This should report 305 pairs, 564 unique texts, and 21 categories.

## Privacy Review Checklist

The public artifact should not contain:

- raw chat logs
- private memory database exports
- vector caches
- account identifiers
- API keys
- private local paths
- raw operational trace dumps
- unreleased internal benchmark result folders

The automated report is `data/privacy_report.json`. It should say:

```json
{
  "status": "passed",
  "findings": []
}
```

`OpenClaw` and `NoldoMem` are intentionally public project names in this release, not accidental private identifiers.

## Methodology Review Checklist

When reviewing claims, check that the text keeps these boundaries:

- Pairwise weighted score and retrieval MRR are different metrics.
- Same-category MRR is controlled and interpretable, but easier than full-corpus retrieval.
- Full-corpus plus synthetic distractors is stronger evidence, but the distractors are still synthetic and templated.
- Held-out mini-set evidence is useful but small.
- Second-model label review is not human inter-annotator agreement.
- Weighted confidence intervals overlap for the top three local-GGUF models, so use point-estimate language rather than significance language.
- Qwen3 production selection is an operations tradeoff, not a public leaderboard claim.

## Common Review Mistakes

Avoid these mistakes:

- Treating the public v0.1 candidate as a universal leaderboard.
- Comparing Qwen3 production deployment choice directly to the public sanitized leaderboard without the CPU-only VPS context.
- Treating 0G Sandbox preflight as a model rerun.
- Treating synthetic distractor results as equivalent to a large production memory corpus.
- Treating the second-model label review as independent human annotation.

## Best Next Critiques

The most useful critiques are:

- label disagreements that should be reviewed by a human
- categories that are underrepresented
- better public-safe distractor corpus designs
- backend metadata gaps for additional model runs
- reproducibility problems in the runner scripts
- unclear or overbroad wording in the technical report
