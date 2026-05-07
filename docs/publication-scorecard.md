# Publication Scorecard

This scorecard exists so readers can see what is strong, what is still candidate-grade, and what needs more evidence before stronger claims.

## Current Readiness

Public-readiness status: candidate-ready for a scoped v0.1 release, not submission-grade or universal-leaderboard-ready.

This is ready as a public v0.1 candidate, technical report, and four-model local-GGUF comparison candidate. It is not ready as a final universal benchmark leaderboard.

## What Is Strong

| Area | Status | Why it matters |
|------|--------|----------------|
| Problem framing | Strong | Agent memory retrieval is scoped separately from generic semantic search. |
| Production grounding | Strong | The benchmark came from a real OpenClaw + NoldoMem memory failure mode. |
| Public runner | Strong | Developers can test their own OpenAI-compatible embedding endpoint. |
| Clean-room validation flow | Strong | The current local public preflight passes, and the current public candidate package passed clean 0G Sandbox validation. |
| Claim discipline | Strong | The repo separates production motivation, public candidate data, and future leaderboard work. |
| Safety posture | Strong | Private caches, raw memory DB exports, and unsanitized pair text are excluded. |
| Public naming posture | Strong | `OpenClaw` and `NoldoMem` are intentionally public project names in this release, not accidental private identifiers. |
| Public preflight | Strong | `scripts/public_release_preflight.py` checks safety, audits, JSON validity, hash-chain consistency, stale references, domain coverage, and whitespace. |
| Evidence hygiene | Strong | Structural dataset audit, P0 semantic review, and a second Qwen3 diagnostic rerun are included. |
| Pinned public reruns | Strong | Qwen3, Snowflake, BGE-M3, and Jina-v3 were rerun on the sanitized public dataset with backend metadata. |
| Cleanup discipline | Strong | Cross-model failure overlap review prevents rewriting the public set to favor one backend. |
| Full-corpus evidence | Scoped evidence | Four local-GGUF models were evaluated against the full public document pool plus synthetic distractors. Tail failures remain. |
| Held-out mini-set | Scoped evidence | A separate mini-set was evaluated after public thresholds were frozen. It is useful support, not a large held-out benchmark. |
| Public reranker matrix | Scoped evidence | Cohere 4 Pro and v3.5 were rerun on sanitized public top-10 same-category candidates with zero API errors. |
| Second-model label review | Candidate-strengthening | A 100-pair blind sample was reviewed and agreement/disagreement counts were published. It is not human inter-annotator agreement. |
| Domain coverage transparency | Strong | Aggregate domain coverage is reported without exposing pair text, so users can see the scope before trusting the benchmark. |

## What Is Still Candidate-Grade

| Area | Status | Current mitigation |
|------|--------|--------------------|
| Public dataset cleanup | Candidate-ready | P0 reviewed, fake-token/stale-reference cleanup done, and P1/P2 cross-model review completed without model-specific rewrites. |
| Backend reproducibility | Partial | P0 local-GGUF reruns include metadata; future API/reranker reruns need the same discipline. |
| Public leaderboard | Partial | The four-model local-GGUF v0.1 comparison is supported; universal leaderboard claims are not. |
| Human annotation independence | Needs work | The current second review is a model-assisted pass; a human reviewer would strengthen submission-grade claims. |
| Larger retrieval pool | Partial | Synthetic distractors are included; larger independent corpora would strengthen production generalization. |
| Domain breadth | Partial | The benchmark remains strongest for multilingual agent memory, technical operations, and near-miss controls; broader domains should be a separate v0.2 extension. |
| Final publication approval | Workflow gate | Automated and model-assisted public-scope checks pass, but the owner still controls when the artifact is actually published. |

## Claim Levels

### Allowed Now

> MAMMR is a production-informed benchmark for multilingual agent memory retrieval.

> Qwen3-Embedding-0.6B Q8_0 was a practical production choice for the tested CPU-only VPS.

> On the pinned public v0.1 local-GGUF rerun, BGE-M3 had the highest weighted score among the four P0 models tested, Jina-v3 had the highest MRR and Recall@5, and Snowflake stayed close on weighted score.

> On full-corpus plus synthetic-distractor retrieval, Snowflake, BGE-M3, and Jina-v3 remained strong while Qwen3 remained weak on the sanitized public task.

> On sanitized public top-10 same-category reranking, Cohere Rerank 4 Pro had the strongest average MRR gain among the two hosted rerankers tested.

> The public candidate package passed a clean 0G Sandbox validation run that does not require operational traces.

### Not Allowed Yet

> MAMMR is the definitive embedding leaderboard for agent memory.

> The public sanitized dataset exactly reproduces unreleased internal rankings.

> One model stack is best for every OpenClaw user.

> 0G Sandbox validation reproduces unreleased production traces.

> External runtime adapter work is primary benchmark evidence for this release.

## What Would Move This Toward A Stronger Release

1. Add human independent review on the disagreement sample.
2. Add larger independent or production-like distractor corpora.
3. Add more non-DevOps domains for generalization testing.
4. Add API embedding reruns with pinned provider metadata if the public leaderboard expands beyond local GGUF.
5. Run a controlled CPU-vs-Metal reproducibility matrix.
6. Add generic external-runtime adapter guidance as downstream adoption work.
