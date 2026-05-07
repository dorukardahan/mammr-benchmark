# Using MAMMR With OpenClaw and NoldoMem

MAMMR was motivated by a real OpenClaw + NoldoMem deployment. This guide explains how an OpenClaw user should use the benchmark without copying the original VPS setup blindly.

## What MAMMR Helps You Decide

MAMMR is useful when you are choosing:

- which embedding model to use for long-term agent memory
- whether a small local model is enough
- whether reranking is worth the latency and cost
- whether your hardware can support larger local models
- whether your memory search is calibrated or only ranking well

It does not choose a model for you automatically. It gives you a repeatable way to test your own backend.

## Recommended OpenClaw Workflow

1. Start with your current memory stack.
2. Run the dry-run to confirm the dataset shape.
3. Evaluate the embedding endpoint you actually plan to use.
4. Compare `weighted_score`, `mrr`, and `recall_at_5` together.
5. Record backend metadata before trusting the result.
6. Only then change your OpenClaw or NoldoMem production config.

```bash
python3 scripts/run_embedding_eval.py --dry-run
```

```bash
python3 scripts/run_embedding_eval.py \
  --endpoint http://localhost:8090/v1/embeddings \
  --endpoint-label my-openclaw-memory-backend \
  --model my-embedding-model \
  --batch-size 8 \
  --output results/my-openclaw-memory-backend.json
```

## VPS Class Setup

If you run OpenClaw on a small CPU-only VPS, the original production lesson is relevant:

- prefer small multilingual embedding models first
- test latency under normal system load, not only on an idle machine
- avoid large CPU-only rerankers for interactive recall unless you can tolerate seconds of delay
- consider hosted reranking if the privacy, cost, and dependency tradeoff is acceptable
- keep batch sizes conservative when the embedding server also serves live recall

The original production choice was Qwen3-Embedding-0.6B Q8_0 plus hosted reranking. That was a practical choice for one constrained VPS, not a universal winner.

## Local Mac or Workstation Setup

If you run OpenClaw on a Mac Studio, Mac mini, GPU workstation, or dedicated inference machine, do not inherit the VPS recommendation directly.

You should rerun at least:

- Qwen3-Embedding-0.6B Q8_0
- Snowflake Arctic L v2 Q8_0
- BGE-M3 Q8_0
- Jina Embeddings v3 Q8_0
- any larger model your hardware can serve with acceptable latency

For stronger local hardware, local rerankers may become more practical than they were on the VPS.

## What To Watch In Production

An embedding benchmark can look good while production recall still feels bad. For OpenClaw/NoldoMem, also watch:

- single-query embedding latency
- tail latency during cron or backfill jobs
- vector dimension consistency
- pooling mode
- context size for long memory text
- backend reproducibility after upgrades
- whether semantic search silently falls back to keyword search
- reranker timeout and fallback behavior

## Minimum Production Smoke Test

After changing your memory backend, run a real recall query and verify:

- semantic search is active
- returned memories have non-zero semantic scores
- reranker scores exist if reranking is enabled
- latency is acceptable while the system is under normal load
- vectorless memory count is zero or explained by a known backfill queue

Record the smoke result without private query text:

| Field | Record |
|-------|--------|
| embedding dimensions | model vector length, for example `1024` |
| semantic search active | yes/no |
| semantic score present | yes/no |
| rerank score present | yes/no/not enabled |
| vectorless memories | count, or known backfill queue reason |
| p95 recall latency | milliseconds over a small private canary |
| fallback mode | semantic, reranked, lexical fallback, or keyword-only |

Do not publish raw memories, chat text, account identifiers, private paths, or API keys with this canary.

## Safe Claim

Safe:

> MAMMR helped me choose a memory retrieval stack for my OpenClaw deployment.

Unsafe:

> MAMMR proves one embedding model is best for every OpenClaw user.
