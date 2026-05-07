# Public Scope And Privacy Review

Date: 2026-05-07

This file records the public-release privacy and scope decisions for the MAMMR v0.1 candidate.

## Decision

MAMMR may refer to `OpenClaw` and `NoldoMem` by name.

Those names are intentionally public project names in this release. They are not leaked account identifiers, private hostnames, private channel names, or credentials.

## What Is Public

- The benchmark motivation: a real long-running agent memory system had retrieval quality and operations problems.
- The public project names: `OpenClaw` and `NoldoMem`.
- Public-safe operational themes: CPU-only VPS constraints, embedding backend reproducibility, cron/load effects, reranker latency, stale state, and near-miss recall.
- Aggregate benchmark results, dataset hashes, and public-safe backend metadata.

## What Is Not Public

- raw chat logs
- raw operational memories
- vector caches
- database exports
- account identifiers
- API keys or credential values
- private IP addresses, hostnames, or SSH details
- private channel names or workspace identifiers
- unsanitized result folders

## Review Status

| Check | Status |
|-------|--------|
| Automated public safety scan | `passed` |
| Dataset structural audit | `passed` |
| Local denylist scan | `passed` |
| Stale public reference scan | `passed` |
| Model-assisted public-scope review | `passed with no publication blocker` |
| Owner publication approval | `required before public announcement` |

The owner approval gate is intentionally separate from benchmark evidence. It controls when the artifact is announced, not whether the current public candidate passes automated safety checks.

## Release Wording

Safe:

> MAMMR was motivated by an OpenClaw + NoldoMem memory stack, but the public artifact contains sanitized benchmark text rather than raw operational traces.

Safe:

> OpenClaw and NoldoMem are named because they are public project names for the system that motivated this benchmark.

Avoid:

> The public dataset contains the original production memories.

Avoid:

> The public benchmark exposes the exact production configuration.
