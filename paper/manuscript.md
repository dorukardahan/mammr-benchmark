# MAMMR: A Production-Informed Benchmark for Multilingual Agent Memory Retrieval

Working manuscript draft for the public v0.1 candidate.

## Abstract

Long-running language-model agents increasingly rely on external memory systems to retrieve prior conversations, user preferences, operational facts, and lessons learned. Existing embedding and retrieval benchmarks are valuable, but they do not directly isolate the retrieval pattern of agent memory: short and vague recall queries, long conversational memories, temporal state changes, code-switched Turkish-English text, and technical context that mixes prose, logs, commands, and configuration names.

We introduce MAMMR, a benchmark for multilingual agent memory retrieval motivated by a real OpenClaw and NoldoMem deployment on a CPU-only VPS. The public v0.1 candidate contains 305 sanitized query-document pairs across 21 task dimensions, a 60-pair held-out mini-set, full-corpus plus synthetic-distractor retrieval checks, a sanitized public reranker matrix, and a 100-pair second-model label review sample. The current public candidate package passed a clean-room preflight in 0G Sandbox. Raw operational traces, chat logs, vector caches, account details, and unreleased internal result folders are not part of the public artifact. In the pinned public local-GGUF reruns, Snowflake Arctic L v2 Q8_0, BGE-M3 Q8_0, and Jina-v3 Q8_0 formed the strongest group among the four tested models, while Qwen3-Embedding-0.6B_Q8_0 scored substantially lower than the other three models on the sanitized public dataset and pinned CPU-only VPS backend.

The sanitized public reranker matrix shows positive top-10 same-category MRR gains for Cohere Rerank 4 Pro and Cohere Rerank v3.5 across the four pinned local-GGUF embedding baselines. However, these reranker results should not be interpreted as full production retrieval or as a comparison against local CPU rerankers. We disclose current limitations, including single-author pair construction, model-assisted rather than human inter-annotator review, threshold calibration after observing some model outputs, domain-specific sampling, and the need for larger external-domain retrieval pools before universal leaderboard claims.

## 1. Introduction

Agent memory retrieval is a practical bottleneck for long-running AI systems. A user may ask an agent to remember "the VPS problem from yesterday" and expect it to recover a long operational memory involving systemd units, cron jobs, Docker containers, embedding model configuration, and a production incident. The relevant memory may be written in Turkish, English, or code-switched prose. It may include stale conclusions, commands, timestamps, service names, and configuration paths. It may also be semantically close to other memories that are no longer correct.

This setting is different from general document retrieval. In general IR, a query often names the topic directly and relevant documents are frequently written as standalone information objects. In agent memory retrieval, the query is often vague and contextual, while the target memory may be conversational, personal, operational, or time-dependent. The retrieval system must recover the right remembered state while avoiding near misses such as old configuration values, wrong agents, similar incidents, or negated statements.

MAMMR evaluates this narrower retrieval setting. It is not intended to replace broad benchmarks such as MTEB or BEIR. Instead, it asks a deployment-oriented question: which embedding and reranking models work well enough for multilingual agent memory recall under realistic operational constraints?

The benchmark was motivated by a production system: NoldoMem used as a custom memory layer for an OpenClaw agent running on a CPU-only VPS. The same machine also hosted other long-running services, so model quality alone was not sufficient. Model size, CPU latency, backend reproducibility, context length, tail latency under contention, and serving stability all affected whether a model could be deployed safely.

This scope is intentional. A developer running an agent on a Mac Studio, Mac mini, workstation GPU, or a dedicated inference box may prefer a larger local model or a different latency-quality tradeoff. MAMMR should therefore be read as a production-driven benchmark for resource-constrained always-on agent memory systems, not as a universal prescription for every hardware environment.

The release separates three evidence layers. First, production experience motivates the task design. Second, the public sanitized artifact provides inspectable data, scripts, and pinned reruns. Third, clean-room validation in 0G Sandbox checks that the public artifact runs outside the original production machine. These layers should not be merged into a claim that the public artifact reproduces an unreleased internal run.

## 2. Related Work

### 2.1 Embedding and Retrieval Benchmarks

MTEB established a broad benchmark for text embeddings across multiple task families and languages [@muennighoff2023mteb]. BEIR provides a heterogeneous benchmark for zero-shot information retrieval models [@thakur2021beir]. More recent multilingual and language-specific work, including MMTEB and TR-MTEB, expands this evaluation tradition to multilingual coverage and Turkish sentence representation [@enevoldsen2025mmteb; @baysan2025trmteb].

These benchmarks are necessary context for MAMMR. They evaluate broad embedding capabilities and provide shared comparison points. MAMMR differs by focusing on a narrower task: agent memory retrieval. Its dimensions include vague conversational recall, short-query-to-long-memory matching, Turkish morphology, code-switching, temporal state changes, entity confusion, and technical log or command references.

### 2.2 Agent Memory Systems

Agent memory systems demonstrate why this retrieval setting matters. Generative Agents uses a memory stream and retrieval/reflection mechanisms to support believable simulated behavior [@park2023generativeagents]. MemGPT frames memory as a virtual context-management problem for LLMs [@packer2024memgpt]. MemoryBank studies long-term memory mechanisms for LLM companions [@zhong2023memorybank]. A-MEM explores dynamic memory organization, indexing, linking, and memory evolution for LLM agents [@xu2025amem].

These systems motivate the need for memory retrieval, but they do not answer the model-selection question directly. MAMMR fills this gap by evaluating embedding and reranking choices for multilingual semantic recall in an operational agent memory corpus.

## 3. Benchmark Design

### 3.1 Task Definition

Each benchmark item is a query-document pair. The query represents a future user or agent recall request. The document represents a candidate memory. The model must assign a similarity score that falls into the expected relevance band, and for high-relevance pairs the retrieval evaluator ranks the target document among same-category candidates.

This pairwise design reflects how memory systems are commonly built: store memory text, embed it, embed the query, retrieve candidates by vector similarity, and optionally rerank the candidate set.

### 3.2 Data Composition

MAMMR currently contains 305 pairs across 21 categories.

| Label | Count |
|-------|-------|
| high | 166 |
| medium_high | 25 |
| medium | 11 |
| low | 103 |

The categories cover:

- short query to long memory
- conversational recall
- Turkish morphology
- Turkish character handling
- crosslingual matching
- code-switching and code-mixed text
- code/log to natural-language description
- paraphrase
- temporal state
- same-topic different-time examples
- similar-but-different memories
- entity confusion
- specificity
- partial match
- synonym and alias matching
- adversarial inputs
- negative controls and irrelevant matches

Four categories contain no high pairs: `irrelevant`, `negative_control`, `same_topic_different_time`, and `similar_but_different`. They therefore do not contribute to high-pair MRR, but they are important for false-positive behavior and threshold calibration.

### 3.3 Metrics

MAMMR uses three primary metrics.

**Weighted accuracy** measures whether each pair's similarity score falls into the expected relevance band. Category weights are fixed, so a category contributes according to its importance for agent memory rather than its raw number of pairs.

**MRR** ranks the correct high-relevance document among same-category candidates. Categories with too few candidates are skipped to avoid trivial Recall@5 behavior.

**Recall@5** measures whether the correct document appears in the top five same-category candidates.

The metric mix is deliberate. Weighted accuracy tests calibration and semantic separation. MRR and Recall@5 test retrieval ranking. These can disagree: a model can rank well but be poorly calibrated against relevance thresholds, or it can separate thresholds while ranking less precisely.

## 4. Experimental Setup

Earlier unpublished exploration covered a wider model set, including local GGUF models and API-hosted models. Those runs motivated the public v0.1 design, but they are not treated as release evidence here because the public artifact must be reproducible from sanitized data, pinned backend metadata, and published result files. The public v0.1 comparison is therefore limited to the pinned four-model local-GGUF rerun. Hardware-rich local setups should rerun the benchmark on their own backend before making final model choices.

The public v0.1 evidence includes a sanitized reranker matrix for Cohere Rerank 4 Pro and Cohere Rerank v3.5 over the four pinned local-GGUF embedding baselines, using top-10 same-category candidates.

Production deployment uses Qwen3-Embedding-0.6B_Q8_0 served by a llama.cpp-based embedding server on CPU. The production choice was based on a joint quality and operations criterion: benchmark performance, model size, memory footprint, latency, and serving stability on the OpenClaw/NoldoMem VPS.

## 5. Embedding Results

### 5.1 Scope Of Published Embedding Evidence

The public v0.1 release intentionally does not publish the wider exploratory inventory as a leaderboard. That inventory used a different evidence boundary and cannot be reproduced from the sanitized public package alone. It was useful for choosing which local GGUF models deserved a careful rerun, but the publishable comparison is the pinned four-model rerun in Section 5.4, where all compared models use the same sanitized dataset SHA and backend metadata contract.

This keeps the release honest: the public package reports what a reader can inspect and rerun, while the deployment story explains why small CPU-friendly models mattered in the first place.

### 5.2 Practical Model Selection

The deployment selected Qwen3-Embedding-0.6B_Q8_0 because model quality was only one constraint. Size, CPU latency, memory footprint, and serving stability also mattered. In the pinned public sanitized rerun, Qwen3 did not rank near the top. That difference is why deployment selection and public leaderboard claims are separated throughout this report.

This distinction is central to MAMMR. The benchmark is not only a leaderboard; it is a model-selection tool for agent memory systems that must run reliably in their actual deployment environment.

### 5.3 MRR and Weighted Score Divergence

Several models had high MRR but lower weighted score. This suggests that ranking quality and similarity calibration are distinct behaviors. In agent memory systems, both matter. Ranking controls which memories are shown first, while calibration affects filtering, thresholds, and decisions about whether semantic search is trustworthy for a query.

### 5.4 Public v0.1 Pinned Reruns

The public v0.1 artifact is a sanitized candidate derived from production-motivated task design. It is not expected to reproduce unreleased internal rankings because sanitization changes anchors and the old vector caches are not published.

To reduce this ambiguity, four local GGUF models were rerun on a pinned CPU backend against the sanitized public dataset: Snowflake Arctic L v2 Q8_0, BGE-M3 Q8_0, Jina-v3 Q8_0, and Qwen3-Embedding-0.6B_Q8_0. On this pinned public rerun, BGE-M3 had the highest weighted score, Jina-v3 had the highest same-category MRR and Recall@5, and BGE-M3 had the highest full-corpus+distractor MRR point estimate by a very small margin over Jina-v3. Snowflake stayed close on weighted score and full-corpus retrieval. Qwen3 performed substantially worse on this sanitized public backend.

This result changes the public-release framing. Qwen3 may still be a practical production choice under strict CPU, size, and latency constraints, but the pinned public rerun does not support presenting Qwen3 as the public v0.1 leaderboard winner. Instead, it shows why public artifacts must separate production deployment decisions from reproducible sanitized-data comparisons.

The public rerun also informed cleanup review. Most Qwen3 high-pair failures were not shared by Snowflake, BGE-M3, and Jina-v3. Therefore, the sanitized dataset was not mass-rewritten to improve Qwen3. The cleanup decision preserves hard agent-memory cases such as vague Turkish recall, typo handling, diacritic normalization, implicit context, relative time, and command/config memories.

## 6. Reranking Results

Earlier unpublished reranker checks motivated the question of whether hosted reranking could help agent-memory retrieval under CPU constraints. Those checks are not published as release evidence here.

The public v0.1 reranker evidence is the sanitized top-10 same-category matrix. On that matrix, Cohere Rerank 4 Pro improved MRR for Snowflake, BGE-M3, Jina-v3, and Qwen3, with average MRR gain +0.1414 across all four embeddings and +0.0445 when excluding Qwen3. Cohere Rerank v3.5 was also MRR-positive for all four embeddings, with MRR gain +0.1179 across all four and +0.0186 excluding Qwen3, but its gains were smaller and some recall-at-k values traded off on already strong baselines.

This should be interpreted as controlled public reranker evidence, not a full production retrieval result. The candidate pool is top-10 same-category, so the next reranker step is a full-corpus reranker sweep across the same four embedding baselines.

## 7. Production Deployment Observations

Production deployment surfaced issues that are not visible from benchmark scores alone.

First, backend reproducibility matters. In production testing, CPU and Metal execution produced different vectors for the same model. MAMMR should therefore report backend metadata for all local results and avoid mixing vectors from different backends without validation.

Second, serving configuration can dominate model choice. In the production llama.cpp embedding server, high thread counts caused deadlock-like behavior in the embedding path. Context size also had to be increased because character truncation did not reliably bound token count for JSON-heavy memories. A source-level non-causal attention fix was required for embedding correctness in the deployed setup.

Third, CPU contention matters. The embedding service shared a VPS with other CPU-heavy inference workloads. A model that appears acceptable in an isolated benchmark may still fail operationally if it monopolizes CPU slots, has poor tail latency, or interacts badly with cron-driven backfills.

These constraints are not universal. On a Mac Studio, a Mac mini, or a dedicated inference host, larger local embedding models and local rerankers may be more practical than they were on the tested VPS. The MAMMR recommendation should therefore be interpreted as a resource-constrained production recommendation, not as a hardware-independent model ranking.

These findings are engineering observations from deployment. They should not be presented as controlled experiments until reproduced under a controlled matrix. They do, however, motivate a reproducibility appendix that records model file, quantization, pooling mode, context size, backend, llama.cpp build, and hardware.

## 8. Limitations

MAMMR is currently domain-specific. Most examples come from DevOps, VPS management, AI-agent operations, and Turkish-English technical workflows. This makes the benchmark valuable for the target production system but limits generalization to domains such as legal, medical, education, or consumer chat.

MAMMR is also hardware-scope-specific. The production recommendations are grounded in a CPU-only VPS deployment of OpenClaw and NoldoMem. Stronger local machines can change the feasible model set, especially for larger embedding models and local rerankers. The benchmark design and scripts remain useful in those settings, but the production recommendation should be rerun rather than copied.

The pair set was created by one human with LLM assistance, so there is not yet a human inter-annotator agreement score. A 100-pair second-model blind review is included and reached 80 percent agreement, but that should not be overstated as human annotation independence. Some thresholds were calibrated after observing model outputs, which introduces mild data snooping. A 60-pair held-out mini-set now exists and was evaluated after public thresholds were frozen, but it is still small.

The original MRR uses intra-category candidate pools rather than full-corpus retrieval against thousands of memories. This makes the metric controlled and interpretable, but easier than production retrieval. The public v0.1 evidence adds full public corpus plus synthetic-distractor retrieval, which is stronger than same-category MRR but still smaller than a real production memory database.

Bootstrap confidence intervals are now available for weighted score. MRR and Recall@5 are reported as point estimates in this candidate because the public result files do not yet store per-query rank traces needed for a public MRR bootstrap. No equivalence test has been performed. Therefore, the paper should report overlapping weighted intervals and point estimates rather than statistical equivalence claims.

Finally, the benchmark was motivated by real operational memory. This improves realism but creates privacy constraints for artifact release. A sanitized public v0.1 pair set now exists as a candidate artifact. Its Qwen3 diagnostic reruns exposed both sanitization sensitivity and backend drift, and a P0 semantic review found that the worst failures were not obvious broken text. Therefore, public sanitized results should be treated as the publishable evidence for this release until the dataset is reviewed more broadly and rerun on additional pinned backends.

Since that first diagnostic run, the four-model pinned public rerun has been completed for local GGUF baselines. The public v0.1 evidence now also includes full-corpus plus synthetic-distractor retrieval, a held-out mini-set, a sanitized public reranker matrix, and a second-model label review. These additions support a much stronger public v0.1 candidate comparison, but still not a universal leaderboard.

0G Sandbox validation and external-runtime adapter work are supporting engineering work, not primary benchmark evidence. 0G Sandbox was used to validate the current public candidate package in a clean environment. Adapter work shows how an agent memory service can be reused across runtimes through a small HTTP boundary. Neither should be interpreted as reproducing unreleased operational traces.

## 9. Future Work

The next version should add:

1. Human inter-annotator agreement on a subset of pairs.
2. A larger held-out evaluation set with more non-DevOps domains.
3. A reranker top-n sweep across all embedding baselines, extending beyond the current public Cohere top-10 matrix.
4. Full-corpus retrieval against a larger independent corpus or a privacy-safe production-like memory sample.
5. Backend reproducibility metadata for every local and API result.
6. Additional non-DevOps domains to test generalization.
7. A controlled CPU-vs-Metal embedding comparison for reproducibility.
8. A cleaned v0.2 public benchmark set that preserves task structure without exposing operational memory.
9. Generic external-runtime adapter guidance so MAMMR-style retrieval can be exercised outside OpenClaw without coupling the benchmark to one downstream runtime.

## 10. Conclusion

MAMMR provides a targeted benchmark for multilingual agent memory retrieval. Its current results suggest that compact multilingual GGUF embedding models can be strong practical choices, and that reranking can materially improve rank precision when latency, cost, and dependency constraints permit.

The production conclusion is pragmatic: Qwen3-Embedding-0.6B_Q8_0 plus an API reranker was selected as a practical balance for the tested OpenClaw/NoldoMem VPS deployment. This is separate from the public sanitized leaderboard, where Qwen3 underperformed the other three pinned local-GGUF baselines. The research conclusion is narrower: agent memory retrieval has distinct evaluation needs that are not fully captured by broad embedding leaderboards.

MAMMR should therefore be read as an initial benchmark and engineering study, not as a definitive universal ranking. Human label review, larger retrieval pools, broader domains, top-n reranker sweeps, cleaned v0.2 public data, and controlled backend reproducibility tests are the main requirements for turning it into a stronger public benchmark for a retrieval task that is increasingly important for long-running AI agents.

## References

References are tracked in `references.bib`.
