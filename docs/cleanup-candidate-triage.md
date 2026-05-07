# Cleanup Candidate Triage

Total high-pair failures: 139

## Priority Counts

| Priority | Count |
|----------|-------|
| P0_rewrite_or_drop | 7 |
| P1_semantic_rewrite | 79 |
| P2_review_and_rewrite_if_needed | 44 |
| P3_near_threshold_calibration | 9 |

## Flag Counts

| Flag | Count |
|------|-------|
| anchor_or_sanitization_risk | 80 |
| code_or_ops_surface | 74 |
| near_threshold | 9 |
| severe_similarity_failure | 7 |
| very_short_query | 6 |

## Category Counts

| Category | Count |
|----------|-------|
| conversational_recall | 13 |
| short_query_long_memory | 12 |
| crosslingual | 11 |
| context_implicit | 10 |
| partial_match | 10 |
| synonym_alias | 10 |
| code_to_description | 10 |
| paraphrase | 9 |
| code_mixed | 8 |
| temporal | 7 |
| code_switching | 7 |
| turkish_chars | 7 |
| noise_typo | 6 |
| turkish_morphology | 6 |
| specificity | 6 |
| entity_confusion | 5 |
| adversarial | 2 |

## P0 Queue

| Pair ID | Category | Similarity | Flags |
|---------|----------|------------|-------|
| mammr-v0.1-0008 | short_query_long_memory | 0.1262 | anchor_or_sanitization_risk, severe_similarity_failure |
| mammr-v0.1-0174 | temporal | 0.1504 | code_or_ops_surface, severe_similarity_failure |
| mammr-v0.1-0259 | context_implicit | 0.1806 | anchor_or_sanitization_risk, severe_similarity_failure |
| mammr-v0.1-0167 | paraphrase | 0.1819 | code_or_ops_surface, severe_similarity_failure |
| mammr-v0.1-0272 | partial_match | 0.1980 | code_or_ops_surface, severe_similarity_failure |
| mammr-v0.1-0116 | conversational_recall | 0.1986 | anchor_or_sanitization_risk, code_or_ops_surface, severe_similarity_failure |
| mammr-v0.1-0009 | short_query_long_memory | 0.1992 | anchor_or_sanitization_risk, code_or_ops_surface, severe_similarity_failure |
