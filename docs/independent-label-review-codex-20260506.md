# Independent Label Review - Codex

Date: 2026-05-06

This is a second-model review of 100 deterministic sample pairs. The reviewer saw pair text and category, but not the original expected label. This report is public-safe and lists only IDs, labels, and aggregate counts.

## Summary

- sample seed: `20260506`
- sample size: `100`
- agreements: `80`
- disagreements: `20`
- agreement rate: `0.8000`

## Label Counts

| Label | Original | Reviewer |
|-------|----------|----------|
| high | 57 | 52 |
| medium_high | 9 | 2 |
| medium | 5 | 5 |
| low | 29 | 41 |

## Disagreements

| Pair ID | Category | Original | Reviewer |
|---------|----------|----------|----------|
| `mammr-v0.1-0017` | similar_but_different | medium_high | low |
| `mammr-v0.1-0018` | similar_but_different | medium_high | low |
| `mammr-v0.1-0024` | similar_but_different | medium_high | low |
| `mammr-v0.1-0028` | same_topic_different_time | medium | low |
| `mammr-v0.1-0031` | same_topic_different_time | medium | low |
| `mammr-v0.1-0032` | same_topic_different_time | medium_high | low |
| `mammr-v0.1-0036` | same_topic_different_time | medium_high | low |
| `mammr-v0.1-0085` | turkish_morphology | medium_high | low |
| `mammr-v0.1-0095` | turkish_morphology | medium_high | low |
| `mammr-v0.1-0096` | turkish_morphology | high | medium |
| `mammr-v0.1-0098` | turkish_morphology | high | medium |
| `mammr-v0.1-0103` | turkish_morphology | medium_high | medium |
| `mammr-v0.1-0240` | synonym_alias | high | medium |
| `mammr-v0.1-0248` | entity_confusion | low | medium |
| `mammr-v0.1-0252` | entity_confusion | medium_high | low |
| `mammr-v0.1-0271` | partial_match | high | medium_high |
| `mammr-v0.1-0275` | partial_match | high | medium_high |
| `mammr-v0.1-0295` | adversarial | medium | low |
| `mammr-v0.1-0297` | adversarial | medium | low |
| `mammr-v0.1-0301` | adversarial | medium | low |

## Interpretation

Disagreements include boundary cases between adjacent labels, intentionally tricky negation/temporal examples, and possible label-validity issues. They require human adjudication before a final v0.2 label freeze, but they do not block the public v0.1 candidate because no automatic relabeling is being made.
