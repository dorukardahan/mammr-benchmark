# Label Disagreement Review Queue

This is the compact human-review queue derived from the 2026-05-06 second-model label review.
It does not change the dataset. It only identifies labels a human reviewer should inspect before a future v0.2 label freeze.

## Summary

- total disagreements: 20
- high priority: 11
- medium priority: 2
- low priority: 7
- source: `docs/independent-label-review-codex-20260506.md`
- queue JSON: `data/label_disagreement_review_queue_20260506.json`
- pair text source: `data/mammr_pairs_public.json`

## Review Queue

| Priority | Pair ID | Category | Original | Reviewer | Suggested Action |
|----------|---------|----------|----------|----------|------------------|
| high | `mammr-v0.1-0252` | entity_confusion | medium_high | low | Check if original label is too generous. |
| high | `mammr-v0.1-0032` | same_topic_different_time | medium_high | low | Check if original label is too generous. |
| high | `mammr-v0.1-0036` | same_topic_different_time | medium_high | low | Check if original label is too generous. |
| high | `mammr-v0.1-0017` | similar_but_different | medium_high | low | Check if original label is too generous. |
| high | `mammr-v0.1-0018` | similar_but_different | medium_high | low | Check if original label is too generous. |
| high | `mammr-v0.1-0024` | similar_but_different | medium_high | low | Check if original label is too generous. |
| high | `mammr-v0.1-0240` | synonym_alias | high | medium | Check if original label is too generous. |
| high | `mammr-v0.1-0085` | turkish_morphology | medium_high | low | Check if original label is too generous. |
| high | `mammr-v0.1-0095` | turkish_morphology | medium_high | low | Check if original label is too generous. |
| high | `mammr-v0.1-0096` | turkish_morphology | high | medium | Check if original label is too generous. |
| high | `mammr-v0.1-0098` | turkish_morphology | high | medium | Check if original label is too generous. |
| medium | `mammr-v0.1-0271` | partial_match | high | medium_high | Check boundary between adjacent relevance labels. |
| medium | `mammr-v0.1-0275` | partial_match | high | medium_high | Check boundary between adjacent relevance labels. |
| low | `mammr-v0.1-0295` | adversarial | medium | low | Check boundary between adjacent relevance labels. |
| low | `mammr-v0.1-0297` | adversarial | medium | low | Check boundary between adjacent relevance labels. |
| low | `mammr-v0.1-0301` | adversarial | medium | low | Check boundary between adjacent relevance labels. |
| low | `mammr-v0.1-0248` | entity_confusion | low | medium | Check whether partial relevance deserves a higher label. |
| low | `mammr-v0.1-0028` | same_topic_different_time | medium | low | Check boundary between adjacent relevance labels. |
| low | `mammr-v0.1-0031` | same_topic_different_time | medium | low | Check boundary between adjacent relevance labels. |
| low | `mammr-v0.1-0103` | turkish_morphology | medium_high | medium | Check boundary between adjacent relevance labels. |

## Release Decision

These disagreements do not block public v0.1 because the release is labeled as a candidate and no automatic relabeling is being made.
They should block a stronger v0.2 label-freeze claim until a human reviewer adjudicates them.
