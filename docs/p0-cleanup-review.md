# P0 Cleanup Review

Updated: 2026-05-06

This review covers the severe high-pair failures from the public Qwen3 diagnostic and pinned reruns. P0 means the public diagnostic similarity is below 0.20 even though the expected label is `high`.

Important: this is a semantic review, not a model-tuning pass. A pair should only be rewritten if the sanitized text no longer preserves the retrieval skill being tested.

## Current Summary

Current P0 high failures after the 2026-05-06 pinned Qwen3 rerun: 7.

Decision:

- keep as valid hard cases for v0.1 candidate scope: 6
- keep for human adjudication before v0.2: 1
- rewrite now: 0
- drop now: 0

The current P0 queue is Qwen3-specific and does not justify rewriting the dataset to fit one backend. These pairs remain useful release-gate evidence: they show that Qwen3 needs backend-specific interpretation and threshold calibration on the sanitized public task.

## Current P0 Pairs

| Pair ID | Category | Decision | Rationale |
|---------|----------|----------|-----------|
| `mammr-v0.1-0008` | short_query_long_memory | keep | Query asks why Provider A was removed; document gives the removal reason and replacement rationale. |
| `mammr-v0.1-0009` | short_query_long_memory | keep | Query asks for workspace handover files; document explains AGENTS.md and handover summary behavior. |
| `mammr-v0.1-0116` | conversational_recall | keep | Query asks for the latest weekly maintenance summary; document is a compact weekly maintenance summary. |
| `mammr-v0.1-0167` | paraphrase | human-adjudicate | Query asks for the count of running containers; document is a very compressed paraphrase. This should be reviewed before v0.2 label freeze, but it is not a privacy or release blocker. |
| `mammr-v0.1-0174` | temporal | keep | Query asks whether the server has an issue today; document reports a dated health check with all services running. |
| `mammr-v0.1-0259` | context_implicit | keep | Query uses shorthand about a memory port; document explains the MemoryService and embedder/gateway port separation. |
| `mammr-v0.1-0272` | partial_match | keep | Query is a short alias; document describes the chat relay/integration state. |

## Historical First-Run Review

The first public Qwen3 diagnostic run had 12 P0 failures. All 12 were manually reviewed and kept as semantically valid for that diagnostic run. After stale-reference cleanup, fake-token cleanup, public-polish cleanup, and the final 2026-05-06 pinned rerun, the current P0 queue is the 7-pair table above.

Previously reviewed and kept:

| Pair ID | Category | Rationale |
|---------|----------|-----------|
| `mammr-v0.1-0156` | specificity | Query and document both referenced the same primary/fallback model configuration. |
| `mammr-v0.1-0279` | partial_match | Query asked for the embedder; document described the embedder service, port, model, and vector dimensions. |
| `mammr-v0.1-0009` | short_query_long_memory | Query asked for workspace handover files; document described handover file behavior. |
| `mammr-v0.1-0204` | noise_typo | Typos are intentional for the `noise_typo` category. |
| `mammr-v0.1-0113` | conversational_recall | Query asked about server security settings; document listed login-rate-limit, firewall, UMask, and permission guard settings. |
| `mammr-v0.1-0133` | crosslingual | English query and Turkish document expressed the same expired-token authentication failure. |
| `mammr-v0.1-0117` | conversational_recall | Query asked about the OAuth error; document explained the provider account-routing collision and fix. |
| `mammr-v0.1-0121` | conversational_recall | Query asked about the provider issue; document described provider and fallback ordering. |
| `mammr-v0.1-0253` | entity_confusion | Query asked for the memory service; document described the memory API service and semantic recall. |
| `mammr-v0.1-0176` | temporal | Query asked for the latest update; document gave a specific update date and version transition. |
| `mammr-v0.1-0152` | specificity | Query asked for the embedder endpoint; document named the service endpoint, service unit, model, and dimensions. |
| `mammr-v0.1-0243` | synonym_alias | Turkish query and document contained direct synonym/alias evidence. |

## Implication

Do not rewrite these pairs just to raise Qwen3 public diagnostic score. The next useful evidence is a broader review of P1/P2 candidates where sanitization may have removed private anchors, compared against Snowflake, BGE-M3, and Jina-v3 rather than Qwen3 alone.
