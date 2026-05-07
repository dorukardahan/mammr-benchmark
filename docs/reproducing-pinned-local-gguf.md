# Reproducing The Pinned Local-GGUF Runs

This page is for exact reproduction of the public v0.1 pinned local-GGUF comparison.
For normal users who only want to test their own model, use `docs/running-your-model.md`.

The public result files record the backend metadata that matters for comparison. If any model file hash, pooling mode, llama.cpp build, context size, or batch setting differs, label the run as a new backend rather than mixing it into the pinned table.

## Dataset

```bash
python3 - <<'PY'
import hashlib
from pathlib import Path
for path in [
    Path("data/mammr_pairs_public.json"),
    Path("data/heldout_mini_public.json"),
    Path("data/synthetic_distractors_public.json"),
]:
    print(path, hashlib.sha256(path.read_bytes()).hexdigest())
PY
```

Expected hashes:

| File | SHA-256 |
|------|---------|
| `data/mammr_pairs_public.json` | `844361d0f7bb013f05c5fc3a172d71e8ed15cc9d801e60ac16749508a1c89545` |
| `data/heldout_mini_public.json` | `48d97350d1ffaaa87834c31ffd3877ca94000665657cad5afb9d8979f9622c75` |
| `data/synthetic_distractors_public.json` | `4024f98fae0ed6d6ae4df2f99e0fd03087078813be83850df0c12afd9dd2b13d` |

## Model Files

The source URLs below are public Hugging Face model-file pages checked during release preparation. Always verify the downloaded file hash locally; the hash is the invariant, not the mirror.

| Model | Source file page | Local filename used in metadata | SHA-256 | Pooling |
|-------|------------------|----------------------------------|---------|---------|
| Qwen3-Embedding-0.6B Q8_0 | `https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF/blob/main/Qwen3-Embedding-0.6B-Q8_0.gguf` | `Qwen3-Embedding-0.6B-Q8_0.gguf` | `06507c7b42688469c4e7298b0a1e16deff06caf291cf0a5b278c308249c3e439` | `last` |
| Snowflake Arctic Embed L v2.0 Q8_0 | `https://huggingface.co/Casual-Autopsy/snowflake-arctic-embed-l-v2.0-gguf/blob/main/snowflake-arctic-embed-l-v2.0-q8_0.gguf` | `snowflake-arctic-embed-l-v2.0-Q8_0.gguf` | `0be8320ecb0fb6e205f0a1419ce3d468834bc44d02cbfda5fd171b3681b12597` | `cls` |
| BGE-M3 Q8_0 | `https://huggingface.co/gpustack/bge-m3-GGUF/blob/main/bge-m3-Q8_0.gguf` | `bge-m3-Q8_0.gguf` | `950f4a8e5e19477a6d3c26d2f162233c20002c601f75e4b002e3239997821167` | `cls` |
| Jina Embeddings v3 Q8_0 | `https://huggingface.co/second-state/jina-embeddings-v3-GGUF/blob/main/jina-embeddings-v3-Q8_0.gguf` | `jina-embeddings-v3-Q8_0.gguf` | `da95bb315ec9766aabfdfa920124a6997a5d9617bd7c9708c4195557136864e1` | `mean` |

Hash check:

```bash
shasum -a 256 /path/to/model.gguf
```

## Backend

Pinned metadata:

| Field | Value |
|-------|-------|
| Backend | `llama-server OpenBLAS` |
| llama.cpp version | `version: 1 (408225b)` |
| backend binary SHA-256 | `5f2609599bc72850fe0a5349502cdaa137c2477aa620e64eb53ae5c010b0fae7` |
| hardware class | `cpu_only_vps` |
| context size | `8192` |
| llama batch size | `2048` |
| llama ubatch size | `2048` |
| threads | `1` |
| threads batch | `1` |
| parallel | `1` |
| GPU layers | `0` |

The pinned results used an isolated loopback benchmark endpoint. Do not run the benchmark through a long-running memory service and call it the same backend.

## Embedding Run

Start one model at a time:

```bash
llama-server \
  --model /path/to/model.gguf \
  --embedding \
  --pooling POOLING_MODE \
  --host 127.0.0.1 \
  --port 8090 \
  --ctx-size 8192 \
  --batch-size 2048 \
  --ubatch-size 2048 \
  --threads 1 \
  --threads-batch 1 \
  --parallel 1 \
  --n-gpu-layers 0 \
  --no-warmup \
  --cache-ram 0 \
  --slot-prompt-similarity 0 \
  --no-cont-batching
```

Then run:

```bash
python3 scripts/run_embedding_eval.py \
  --endpoint http://127.0.0.1:8090/v1/embeddings \
  --endpoint-label llama-server-openblas-cpu-vps \
  --model MODEL_LABEL \
  --batch-size 1 \
  --timeout 120 \
  --output results/MODEL_RESULT.json
```

Use the model labels and output filenames from `metadata/*-pinned-20260506.json`.

## Full-Corpus Run

```bash
python3 scripts/run_retrieval_eval.py \
  --dataset data/mammr_pairs_public.json \
  --distractors data/synthetic_distractors_public.json \
  --endpoint http://127.0.0.1:8090/v1/embeddings \
  --endpoint-label llama-server-openblas-cpu-vps \
  --model MODEL_LABEL \
  --batch-size 1 \
  --timeout 120 \
  --output results/retrieval/MODEL-full-corpus.json
```

## Held-Out Run

```bash
python3 scripts/run_retrieval_eval.py \
  --dataset data/heldout_mini_public.json \
  --distractors data/synthetic_distractors_public.json \
  --endpoint http://127.0.0.1:8090/v1/embeddings \
  --endpoint-label llama-server-openblas-cpu-vps \
  --model MODEL_LABEL \
  --batch-size 1 \
  --timeout 120 \
  --output results/heldout/MODEL-heldout-full-corpus.json
```

## Reranker Run

Public v0.1 reranker files use a hosted reranker through an environment variable, never a committed key.

```bash
python3 scripts/run_reranker_eval.py \
  --dataset data/mammr_pairs_public.json \
  --endpoint http://127.0.0.1:8090/v1/embeddings \
  --endpoint-label llama-server-openblas-cpu-vps \
  --model MODEL_LABEL \
  --pool same_category \
  --top-n 10 \
  --reranker-model cohere/rerank-4-pro \
  --reranker-label cohere-4-pro \
  --reranker-endpoint-label openrouter-rerank \
  --rerank-api-key-env OPENROUTER_API_KEY \
  --fail-on-rerank-error \
  --output results/reranker/MODEL-cohere-4-pro-top10-same-category.json
```

Run the same command with `--reranker-model cohere/rerank-v3.5` and `--reranker-label cohere-v3.5` for the second hosted reranker.

## Release Checks

Generated local artifacts should not exist in the public workspace:

```bash
python3 scripts/public_release_preflight.py
```

If the command reports only local generated artifacts such as `.DS_Store`, `.tmp-*`, `__pycache__`, or `.pyc` files, clean them explicitly:

```bash
python3 scripts/public_release_preflight.py --clean
python3 scripts/public_release_preflight.py
```

Do not publish if the second command does not end with:

```text
PUBLIC PREFLIGHT PASSED
```
