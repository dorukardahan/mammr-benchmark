# 0G Sandbox Clean-Room Validation

This document describes how to validate the public MAMMR artifact in a fresh
0G Sandbox environment.

The goal is artifact reproducibility, not operational-corpus reproduction.

## What This Proves

- The public dataset parses.
- The public safety scan passes.
- The public audit passes.
- The embedding evaluator dry-run works in a clean environment.
- Optional endpoint smoke tests can run without private data.

## What This Does Not Prove

- It does not reproduce operational traces.
- It does not prove unreleased internal scores.
- It does not require raw OpenClaw, chat, server, or operational memory text.

## Packaging Note

On macOS, system `tar` can add extended headers that show harmless warnings
when extracted inside Linux sandboxes. For a clean public artifact tarball,
prefer Python `tarfile` or another packager that does not add macOS xattrs.

## Minimal Validation Commands

Run these from the repository root:

```bash
python3 scripts/public_release_preflight.py
```

Expected result:

- final line prints `PUBLIC PREFLIGHT PASSED`

## Optional Endpoint Smoke Test

If the sandbox has an OpenAI-compatible embedding endpoint, run a small public
endpoint smoke test:

```bash
python3 scripts/run_embedding_eval.py \
  --endpoint http://127.0.0.1:8090/v1/embeddings \
  --endpoint-label sandbox-local \
  --model local-test-model \
  --output results/sandbox-local-smoke.json
```

Do not use operational memory text or raw vector caches for this step.

## Run Metadata

Use `metadata/0g-sandbox-run-template.json` as the starting point for a run
record.

The run record may include:

- repository commit
- dataset SHA-256
- canonical artifact SHA-256 with the run record file excluded
- Python version
- operating system
- command list
- pass/fail status

The run record must not include:

- secrets
- local user paths
- private IPs
- hostnames
- account identifiers
- raw operational memory text

## 2026-05-06 Live Validation Status

A clean 0G Sandbox run validated the current public candidate tarball. The run record is stored in
`metadata/0g-sandbox-run-20260506.json`.

```bash
python3 scripts/public_release_preflight.py
```

Current public dataset metadata:

- pairs: `305`
- unique texts: `564`
- dataset SHA-256: `844361d0f7bb013f05c5fc3a172d71e8ed15cc9d801e60ac16749508a1c89545`
- private pattern hits: `0`
- 0G Sandbox preflight: `PUBLIC PREFLIGHT PASSED`

## Paper Wording

Safe wording:

> The public candidate package was validated in a clean 0G Sandbox environment.

Safe wording:

> The original motivation came from an OpenClaw + NoldoMem production memory
> stack, but raw operational traces are not released.

Avoid wording that implies 0G Sandbox reproduces unreleased operational scores.
