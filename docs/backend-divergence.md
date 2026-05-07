# Backend Divergence Note

Date: 2026-04-17
Updated: 2026-05-06

## Status

Public v0.1 is ready only for a scoped local-GGUF candidate comparison.

The sanitized public reruns against the current diagnostic Qwen3 benchmark backend produced much lower scores than earlier internal Qwen3 checks. This is not safe to explain as sanitization alone.

Update: the pinned four-model public rerun set shows that Snowflake, BGE-M3, and Jina-v3 remain strong on the sanitized public dataset. Qwen3 remains weak on the current pinned backend. Full-corpus+distractor retrieval, held-out retrieval, and sanitized top-10 Cohere reranking now reinforce the same scoped conclusion. The public dataset is therefore not globally broken; the divergence is model/backend/threshold specific.

## Evidence

Spot checks compared older internal similarity checks with fresh embeddings from the public rerun benchmark backend. Several affected pairs showed a large drop on the current backend. The exact older spot-check values are not part of the public artifact because they were not produced under the current pinned metadata contract.

Controls:

- Same-text cosine on the current benchmark backend is 1.0.
- Batch-size 1 and batch calls are both low for the affected pairs.
- The current benchmark backend returns 1024-dimensional vectors and responds normally.
- Older Qwen3 artifacts and spot checks lack enough backend metadata to prove they were produced by the exact current public rerun backend.
- A second public rerun on 2026-05-05 used the audited public dataset SHA `68743ae59481807ce00ed1f218831f98d3d4ade62d064dd1dde4be2c676c2ff8` and still scored low: weighted 0.3545, MRR 0.3791, Recall@5 0.5964.
- The 2026-05-05 P0 semantic review found no obvious broken text among the 12 worst high-pair failures.
- The refreshed pinned local-GGUF rerun used dataset SHA `844361d0f7bb013f05c5fc3a172d71e8ed15cc9d801e60ac16749508a1c89545`.
- Pinned weighted scores: BGE-M3 0.7143, Snowflake 0.6995, Jina-v3 0.6956, Qwen3-0.6B 0.3731.

## Interpretation

The current benchmark backend is functional, but it may not be equivalent to the backend that produced older internal Qwen3 checks.

Likely causes to investigate before public leaderboard release:

1. llama.cpp build drift.
2. embedding attention patch drift.
3. pooling or normalization behavior drift.
4. cache/result files produced before the final production service patch set.
5. sanitized examples losing operational anchors and backend drift happening at the same time.
6. fixed cosine thresholds not being calibrated for the sanitized public distribution.

## Release Rule

Do not publish a broad public leaderboard until all listed result files include pinned backend metadata and the compared models use the same public dataset SHA.

See `docs/backend-pinning-plan.md` for the full metadata contract. Minimum backend pin for public reruns:

- llama.cpp commit/build hash
- local patch set applied
- model file hash
- pooling mode
- context size
- thread and batch flags
- CPU/GPU backend
- dataset SHA-256
- result JSON SHA-256

The paper should clearly separate:

1. production motivation,
2. public sanitized dataset candidate,
3. current backend drift diagnostic,
4. pinned public local-GGUF reruns,
5. sanitized public reranker matrix.
