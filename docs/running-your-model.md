# Running Your Model

MAMMR public v0.1 expects an OpenAI-compatible embeddings endpoint.

The original production motivation was a CPU-only OpenClaw + NoldoMem VPS. Your hardware may be very different. If you run on a Mac Studio, Mac mini, GPU workstation, or dedicated inference server, use this guide to measure your own backend rather than copying the VPS production choice.

## Prerequisites

- Python 3.10 or newer
- no Python package install for the core scripts; they use the standard library
- an OpenAI-compatible `/v1/embeddings` endpoint for real model runs
- optional hosted reranker access if you run `scripts/run_reranker_eval.py`

## 1. Start an embedding endpoint

Example local endpoint:

```bash
llama-server \
  --model /path/to/model.gguf \
  --embedding \
  --pooling last \
  --host 127.0.0.1 \
  --port 8090
```

The exact flags depend on the model. Use the pooling mode recommended by the model provider.

## 2. Dry-run the dataset

```bash
python3 scripts/run_embedding_eval.py --dry-run
```

Expected shape:

```text
pairs=305 unique_texts=564 categories=21
labels={'high': 166, 'low': 103, 'medium': 11, 'medium_high': 25}
```

Before publishing or comparing results from a checkout, run the full public preflight:

```bash
python3 scripts/public_release_preflight.py
```

Expected final line:

```text
PUBLIC PREFLIGHT PASSED
```

If the preflight reports generated local files such as `.DS_Store`, `__pycache__`, or `.pyc`, clean them explicitly and rerun:

```bash
python3 scripts/public_release_preflight.py --clean
python3 scripts/public_release_preflight.py
```

For exact reproduction of the pinned public local-GGUF files, use `docs/reproducing-pinned-local-gguf.md`.

## 3. Smoke-test the endpoint

Before a full run, send one public-safe embedding request:

```bash
curl -sS http://localhost:8090/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{"model":"my-model","input":["public smoke test"]}' \
  | python3 -c 'import json,sys; data=json.load(sys.stdin); print(len(data["data"][0]["embedding"]))'
```

Expected output is the embedding dimension, for example `1024`.

## 4. Run evaluation

```bash
python3 scripts/run_embedding_eval.py \
  --endpoint http://localhost:8090/v1/embeddings \
  --endpoint-label local-llama-server \
  --model my-model \
  --batch-size 16 \
  --output results/my-model.json
```

If your endpoint needs an API key:

```bash
export OPENAI_API_KEY="YOUR_API_KEY"

python3 scripts/run_embedding_eval.py \
  --endpoint https://api.example.com/v1/embeddings \
  --endpoint-label provider-api \
  --model provider/model-name \
  --api-key-env OPENAI_API_KEY \
  --output results/provider-model-name.json
```

Never paste real API keys into committed files or shell snippets.

## 5. Read the output

Important fields:

| Field | Meaning |
|-------|---------|
| `weighted_score` | Category-weighted threshold accuracy. |
| `unweighted_score` | Raw pair pass rate. |
| `mrr` | Mean reciprocal rank for high-relevance recall queries. |
| `recall_at_5` | Share of high-relevance queries whose target appears in top 5. |
| `dataset_sha256` | Hash of the dataset file used for the run. |
| `endpoint_label` | Public-safe label for the backend, not the private endpoint URL. |
| `dimensions` | Embedding vector length returned by the endpoint. |
| `categories` | Per-category accuracy and similarity diagnostics. |
| `pairs` | Pair-level status without raw text. |

The expected-label bands are overlapping tolerance zones, not disjoint classes:

| Label | Acceptable cosine range |
|-------|-------------------------|
| `high` | `0.50` to `1.00` |
| `medium_high` | `0.40` to `0.75` |
| `medium` | `0.25` to `0.65` |
| `low` | `-1.00` to `0.35` |

The overlap is deliberate. MAMMR tests whether a model lands inside the expected tolerance zone for a relationship, not whether every pair belongs to a hard ordinal bucket.

The weighted score uses category weights because some agent-memory failures are more damaging than others:

| Highest weight categories | Why they matter |
|---------------------------|-----------------|
| `short_query_long_memory`, `code_switching`, `specificity` | Common agent recall failures with vague queries and technical state. |
| `negative_control`, `irrelevant` | False positives waste context and can cause wrong actions. |
| `conversational_recall`, `paraphrase`, `similar_but_different`, `adversarial` | Core memory-recall and near-miss behavior. |

## 6. Run Full-Corpus Retrieval

The default embedding runner reports same-category ranking. To test a harder mixed retrieval pool, use:

```bash
python3 scripts/run_retrieval_eval.py \
  --dataset data/mammr_pairs_public.json \
  --distractors data/synthetic_distractors_public.json \
  --endpoint http://localhost:8090/v1/embeddings \
  --endpoint-label local-llama-server \
  --model my-model \
  --batch-size 16 \
  --output results/retrieval/my-model-full-corpus.json
```

## 7. Run Hosted Reranking

Reranker evaluation expects an embedding endpoint and an API key supplied by environment variable or file. Never commit the key.

```bash
python3 scripts/run_reranker_eval.py \
  --dataset data/mammr_pairs_public.json \
  --endpoint http://localhost:8090/v1/embeddings \
  --endpoint-label local-llama-server \
  --model my-model \
  --pool same_category \
  --top-n 10 \
  --reranker-model cohere/rerank-4-pro \
  --reranker-label cohere-4-pro \
  --reranker-endpoint-label openrouter-rerank \
  --rerank-api-key-env OPENROUTER_API_KEY \
  --fail-on-rerank-error \
  --output results/reranker/my-model-cohere-4-pro.json
```

By default the reranker runner uses OpenRouter's rerank endpoint. For another OpenAI-like rerank gateway, pass `--reranker-endpoint`. The result JSON stores `reranker_endpoint_label`, not the raw endpoint URL, so choose a public-safe label.

Use `--fail-on-rerank-error` when producing publishable result files. Without it, failed reranker calls are counted in `metrics.reranked.rerank_errors` and the run falls back to the baseline rank for that query.

## 8. Common pitfalls

- Do not compare models with different pooling modes unless that is intentional.
- Do not mix vectors generated by different backends without checking reproducibility.
- Do not assume the VPS production recommendation is optimal for stronger local hardware.
- Do not use a tiny context size for long memory text.
- Do not rely on weighted score alone; MRR and Recall@5 measure different behavior.
- Do not call the result statistically significant unless you run a proper significance analysis.
