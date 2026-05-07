# MAMMR Public Release Next Steps

Date: 2026-05-07

## Current State

This repository is safe to review as a public v0.1 candidate.

It contains:

- sanitized 305-pair dataset candidate
- OpenAI-compatible embedding runner
- Qwen3 diagnostic results on the current production backend
- cleanup queue and cross-model failure overlap review for weak high-relevance pairs
- structural dataset audit and P0 semantic review
- aggregate-only inventory of old private embedding and reranker benchmark outputs
- pinned P0 local-GGUF reruns for Qwen3, Snowflake, BGE-M3, and Jina-v3
- full-corpus plus synthetic-distractor retrieval results
- held-out mini-set retrieval results
- sanitized public reranker matrix
- second-model label review summary
- aggregate-only domain coverage report
- one-command public release preflight
- OpenClaw/NoldoMem usage guide
- publication scorecard
- validation roadmap
- documentation explaining why this is not a universal leaderboard

The motivating deployment is a CPU-only OpenClaw + NoldoMem VPS. Public users with stronger local hardware should treat the included results as context, not as a hardware-independent prescription.

The bundle passes the local release scan.

Run the full preflight before any public share:

```bash
python3 scripts/public_release_preflight.py
```

## Do Not Publish Yet As

- a final universal benchmark leaderboard
- a paper artifact claiming full reproducibility
- evidence that the sanitized public dataset reproduces an earlier unpublished benchmark
- evidence that production Cohere-4-pro reranking quality has been proven in full production retrieval

## Recommended Release Path

### Phase 1 - Public Candidate

Goal: let developers inspect the benchmark shape and runner without trusting a leaderboard yet.

Publishable content:

- dataset candidate
- runner
- docs
- diagnostic Qwen3 results
- explicit caveat that the four-model public comparison is scoped and not universal

This is useful because developers can run their own endpoints and see where MAMMR is hard.

The pinned local-GGUF v0.1 result table is now usable as a candidate public comparison for the four tested local models. It should not be generalized beyond that scope.

This is especially important for Mac Studio, Mac mini, workstation GPU, and dedicated inference deployments. Those systems may support different model sizes and reranker choices than the original VPS deployment.

### Phase 2 - Dataset Cleanup

Goal: make the dataset read like a designed public benchmark, not a mechanically sanitized operational note dump.

Current status: P0 and P1/P2 review is complete for public v0.1 candidate. The cross-model overlap review found that most Qwen3 high-pair failures are Qwen-only, so the dataset should not be rewritten to favor Qwen3.

Use `docs/cleanup-candidate-triage.md`, `docs/p0-cleanup-review.md`, `docs/p1-p2-cleanup-review.md`, and `docs/pinned-failure-overlap-review.md` as the decision trail.

Rules:

1. Keep all 305 pair IDs stable unless a pair is removed with a written reason.
2. Keep category and expected label distribution stable.
3. Rewrite only text, not labels, during the first cleanup pass.
4. For every rewritten high pair, preserve the same retrieval skill being tested.
5. Do not make high pairs trivially identical just to raise scores.
6. Keep negative and low pairs adversarial enough to catch false positives.
7. Keep Turkish, English, code-switching, typo, temporal, and agent-memory cases.

Future v0.2 quality gate:

- human independent label review should confirm that hard pairs are still semantically valid.
- remaining operator-specific placeholder names and overly conversational source phrasing should be reviewed before any dataset SHA change.
- held-out pairs should not be used for threshold calibration.
- improvements should come from natural examples, not easier thresholds.
- manual spot review should focus first on pairs failed by multiple strong baselines.

See `docs/validation-roadmap.md` for the full validation sequence.

### Phase 3 - Backend Pinning

Goal: make public results reproducible.

Required:

- decide the exact local backend build for public GGUF runs
- record llama.cpp commit/build hash
- record pooling mode
- record dimensions
- record ctx size
- record batch size
- record dataset SHA-256 in every result JSON

See `docs/backend-pinning-plan.md` for the minimum metadata contract.

Current status:

- older internal vector checks and the public rerun endpoint do not match on several spot checks.
- the P0 local-GGUF public reruns now use pinned backend metadata.
- broader public leaderboard runs must keep using pinned backend metadata, not a vague "production endpoint".

### Phase 4 - P0 Rerun Matrix

Minimum public leaderboard:

1. Qwen3-Embedding-0.6B-Q8_0 - complete
2. Snowflake Arctic Embed L v2.0 Q8_0 - complete
3. BGE-M3 Q8_0 - complete
4. Jina Embeddings v3 Q8_0 - complete

Optional:

- API embeddings
- one small model baseline
- reranker top-n sweep on sanitized public vectors beyond the current Cohere top-10 matrix

### Phase 4.5 - Strong Evidence Added

Completed after the first public v0.1 candidate:

- `docs/full-corpus-distractor-results.md`
- `docs/heldout-mini-results.md`
- `docs/sanitized-reranker-matrix.md`
- `docs/independent-label-review-codex-20260506.md`

These results make the public v0.1 package much stronger, but they still do not turn it into a universal leaderboard.

### Phase 5 - Paper Claim Sync

The paper should use four separate labels:

1. private production-derived benchmark
2. public sanitized candidate
3. public reproducible leaderboard
4. target-hardware recommendation

Do not merge the fourth label into the first three. A model that is practical on the VPS may not be the best choice on stronger local hardware, and a model that is impractical on the VPS may be reasonable elsewhere.

Do not mix scores across these labels.

## Release Decisions

1. Author line.
   - Recommended: use the owner-approved public author line before announcement.
2. Release mode.
   - Recommended: public v0.1 candidate release first, then stronger leaderboard release after human review, larger distractor evidence, broader domains, and maintainer approval.
