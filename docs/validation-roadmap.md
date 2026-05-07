# Validation Roadmap

This roadmap addresses the main evidence gaps before MAMMR can move from public candidate to stronger benchmark release.

## Phase 1: Public Dataset Cleanup

Goal: make the sanitized dataset read like a designed benchmark, not a mechanically sanitized operational note.

Rules:

1. Keep pair IDs stable.
2. Keep categories and expected labels stable unless a written review says the pair is invalid.
3. Rewrite text only when sanitization damaged the retrieval skill being tested.
4. Do not make high pairs trivially identical.
5. Preserve Turkish, English, code-switching, temporal, log, and config cases.

Output:

- cleaned `data/mammr_pairs_public.json`
- changelog of changed pair IDs
- before/after dry-run metadata

Current status:

- P0 semantic review completed.
- Cross-model P1/P2 cleanup review completed.
- No mass rewrite was made because most Qwen3 high failures are Qwen-only.
- A second-model label review is complete; next cleanup step should be human adjudication of disagreements, not model-specific text tuning.

## Phase 2: Pinned Backend Reruns

Goal: remove backend drift from public leaderboard claims.

Minimum rerun set:

- Qwen3-Embedding-0.6B Q8_0
- Snowflake Arctic L v2 Q8_0
- BGE-M3 Q8_0
- Jina Embeddings v3 Q8_0

Each result must include:

- dataset SHA-256
- model SHA-256 or provider model ID
- vector dimensions
- pooling mode
- context size
- backend type
- hardware class
- script commit

Current status:

- Qwen3, Snowflake, BGE-M3, and Jina-v3 pinned public reruns completed for local-GGUF v0.1 candidate evidence.
- Results are documented in `docs/pinned-public-reruns.md`.
- Failure overlap is documented in `docs/pinned-failure-overlap-review.md`.
- Full-corpus plus synthetic-distractor retrieval is documented in `docs/full-corpus-distractor-results.md`.
- Sanitized public reranker results are documented in `docs/sanitized-reranker-matrix.md`.

## Phase 3: Held-Out Mini-Set

Goal: reduce threshold calibration bias.

Detailed protocol: `docs/heldout-and-independent-review-protocol.md`.

Build 50 to 100 new pairs after the public thresholds are frozen.

Suggested split:

| Category group | New pairs |
|----------------|-----------|
| vague recall | 15 |
| temporal/stale state | 15 |
| Turkish morphology and code-switching | 20 |
| technical logs/config | 15 |
| negative and near-miss false positives | 20 |

Do not recalibrate thresholds on this set.

Current status:

- 60 public-safe held-out pairs were generated after the public v0.1 thresholds were frozen.
- Four local-GGUF models were evaluated against the held-out set plus synthetic distractors.
- Results are documented in `docs/heldout-mini-results.md`.

## Phase 4: Second-Pass Label Review

Goal: reduce single-annotator risk.

Detailed protocol: `docs/heldout-and-independent-review-protocol.md`.

Ask a second reviewer, human or independent LLM with a fixed rubric, to label a subset without seeing the original labels.

Minimum:

- 100 randomly sampled pairs
- all 21 categories represented where possible
- report agreement and disagreements
- keep disagreement examples for the paper appendix

Current status:

- 100-pair second-model blind review completed.
- Agreement: 80 / 100.
- Disagreements are summarized in `docs/independent-label-review-codex-20260506.md`.
- Human adjudication is still needed before a v0.2 label freeze.

## Phase 5: Large-Distractor Retrieval

Goal: make retrieval closer to production.

Current MRR is intra-category. The next step is to rank each query against a larger mixed pool.

Options:

1. Full public dataset pool.
2. Public dataset plus synthetic distractors.
3. Private production memory corpus, reported only as aggregate if privacy allows.

Report:

- MRR
- Recall@5
- target missing from top-n count
- false-positive examples

Current status:

- Full public corpus plus 96 synthetic public-safe distractors is complete for Qwen3, Snowflake, BGE-M3, and Jina-v3.
- This is stronger than same-category retrieval, but still smaller than a production memory database.
- Future work should add a larger independent corpus and more non-DevOps domains.

## Phase 5.5: Domain Coverage Transparency

Goal: make the benchmark scope visible without exposing source text.

Current status:

- Aggregate domain coverage is documented in `docs/domain-coverage.md`.
- The report groups categories into memory recall, multilingual, semantic matching, technical surface, and negative controls.
- The report intentionally does not print query or document text.

Release rule:

- Public v0.1 can claim strong coverage for multilingual agent memory and technical operations.
- Public v0.1 should not claim broad-domain coverage.
- Broader domains should be added as a separate v0.2 extension set instead of diluting the current benchmark.

## Phase 6: OpenClaw/NoldoMem Canary

Goal: connect benchmark metrics to real agent behavior.

Run a small canary with real OpenClaw recall tasks:

- 20 to 30 recall prompts
- semantic score recorded
- rerank score recorded
- response latency recorded
- manual pass/fail judgment

This should be labeled as deployment validation, not benchmark scoring.
