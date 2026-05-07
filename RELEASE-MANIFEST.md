# MAMMR Public v0.1 Candidate Release Manifest

Date: 2026-05-07

This manifest freezes the evidence boundary for the public v0.1 candidate. It is a release manifest for the repository, not a claim that MAMMR is a final universal leaderboard.

## Scope

Included:

- 305 sanitized public query-document pairs for multilingual agent memory retrieval
- 60-pair held-out mini-set
- 96 public-safe synthetic distractors
- four pinned local-GGUF embedding reruns
- full public corpus plus synthetic-distractor retrieval results
- sanitized top-10 same-category reranker matrix
- 100-pair second-model label review sample
- public privacy and scope review docs
- 0G Sandbox clean-room validation record

Not included:

- raw operational traces
- raw chat logs
- private memory database exports
- vector caches
- account details
- unreleased internal benchmark result folders
- a claim that this is a final universal embedding leaderboard

## Frozen Dataset Hashes

| Artifact | SHA-256 |
|----------|---------|
| `data/mammr_pairs_public.json` | `844361d0f7bb013f05c5fc3a172d71e8ed15cc9d801e60ac16749508a1c89545` |
| `data/heldout_mini_public.json` | `48d97350d1ffaaa87834c31ffd3877ca94000665657cad5afb9d8979f9622c75` |
| `data/synthetic_distractors_public.json` | `4024f98fae0ed6d6ae4df2f99e0fd03087078813be83850df0c12afd9dd2b13d` |

## Pinned Local-GGUF Result Set

All rows below use `data/mammr_pairs_public.json` and a pinned CPU-only OpenBLAS llama-server backend.

| Rank | Model | Weighted | Unweighted | MRR | Recall@5 | Result file |
|------|-------|----------|------------|-----|----------|-------------|
| 1 | BGE-M3 Q8_0 | 0.7143 | 0.7016 | 0.9134 | 0.9639 | `results/bge-m3-q8_0-pinned-20260506.json` |
| 2 | Snowflake-Arctic-L-v2 Q8_0 | 0.6995 | 0.6852 | 0.8917 | 0.9578 | `results/snowflake-arctic-l-v2-q8_0-pinned-20260506.json` |
| 3 | Jina-v3 Q8_0 | 0.6956 | 0.6885 | 0.9257 | 0.9880 | `results/jina-v3-q8_0-pinned-20260506.json` |
| 4 | Qwen3-0.6B Q8_0 | 0.3731 | 0.3869 | 0.4549 | 0.6446 | `results/qwen3-0.6b-q8_0-pinned-20260506.json` |

Interpretation:

- BGE-M3 has the highest weighted point estimate among the four pinned local-GGUF models.
- Jina-v3 has the highest same-category MRR and Recall@5.
- Qwen3-0.6B was a practical production choice for one CPU-only VPS, not the public sanitized leaderboard winner.

## Full-Corpus And Held-Out Evidence

Full public corpus plus synthetic distractors:

| Model | MRR | Recall@5 | Median rank |
|-------|-----|----------|-------------|
| BGE-M3 Q8_0 | 0.6053 | 0.8012 | 2 |
| Jina-v3 Q8_0 | 0.6043 | 0.7952 | 2 |
| Snowflake-Arctic-L-v2 Q8_0 | 0.5764 | 0.7530 | 2 |
| Qwen3-Embedding-0.6B Q8_0 | 0.1520 | 0.1747 | 95 |

Held-out mini-set plus synthetic distractors:

| Model | MRR | Recall@5 | Median rank |
|-------|-----|----------|-------------|
| Jina-v3 Q8_0 | 0.7083 | 0.8286 | 1 |
| BGE-M3 Q8_0 | 0.6712 | 0.8286 | 1 |
| Snowflake-Arctic-L-v2 Q8_0 | 0.6208 | 0.8286 | 2 |
| Qwen3-Embedding-0.6B Q8_0 | 0.1338 | 0.2000 | 49 |

These retrieval pools are stronger than same-category ranking, but still not a large production-memory corpus.

## Sanitized Reranker Matrix

The public reranker matrix reranks top-10 same-category candidates.

| Reranker | Average MRR gain | Average MRR gain excluding Qwen3 |
|----------|------------------|----------------------------------|
| Cohere Rerank 4 Pro | +0.1414 | +0.0445 |
| Cohere Rerank v3.5 | +0.1179 | +0.0186 |

This is controlled public reranker evidence, not a full production retrieval benchmark.

## Validation Record

| Check | Status |
|-------|--------|
| public safety scan | passed |
| dataset structural audit | passed |
| held-out structural audit | passed |
| domain coverage audit | passed |
| JSON parse check | passed |
| result hash-chain check | passed |
| summary metric consistency check | passed |
| stale public reference check | passed |
| git whitespace check | passed |
| 0G Sandbox clean-room preflight | passed |

Current 0G Sandbox run record:

- file: `metadata/0g-sandbox-run-20260506.json`
- date_utc: `2026-05-07T10:39:32.541253+00:00`
- artifact_archive_sha256: `38e9a7364ce2b6073e5d98956a90c59181f94ec062bdb5c8ae75a16b9eb53c35`
- result: `pass`

The canonical sandbox archive is built by `scripts/run_0g_sandbox_preflight.py`. This top-level manifest is a repository release manifest and is not part of the canonical sandbox archive, so the archive hash can be recorded here without a self-reference.

## Exact Release Gate

Before public announcement, rerun:

```bash
python3 scripts/check_public_safety.py --json > data/privacy_report.json
python3 scripts/public_release_preflight.py --clean
python3 scripts/public_release_preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/run_0g_sandbox_preflight.py
git diff --check
```

The package should not be announced if `scripts/public_release_preflight.py` does not end with:

```text
PUBLIC PREFLIGHT PASSED
```
