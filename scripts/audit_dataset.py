#!/usr/bin/env python3
"""Audit MAMMR public dataset structure and benchmark hygiene."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data" / "mammr_pairs_public.json"

EXPECTED_LABELS = {"high", "medium_high", "medium", "low"}
REQUIRED_FIELDS = {"id", "category", "expected", "query", "document"}

PRIVATE_PATTERNS = {
    "private_home_path": re.compile(r"/Users/[^/\s]+|/home/[^/\s]+|/root/"),
    "email_address": re.compile(r"\b[A-Z0-9._%+-]+@(?!example\.com\b)[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "ssh_public_key_material": re.compile(r"\bssh-(?:rsa|ed25519)\s+[A-Za-z0-9+/=]{16,}|\bauthorized_keys\b"),
    "private_chat_tone_marker": re.compile(r"\b(my birthday|my cat|my house|my apartment)\b", re.IGNORECASE),
    "secret_like_token": re.compile(r"(sk-or-v1|xox[baprs]-|xapp-|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})", re.IGNORECASE),
}


def is_allowed_ip(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return True
    if ip in ipaddress.ip_network("203.0.113.0/24"):
        return True
    if ip in ipaddress.ip_network("192.0.2.0/24"):
        return True
    if ip in ipaddress.ip_network("198.51.100.0/24"):
        return True
    return value in {"0.0.0.0", "127.0.0.1", "::1"}


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = json.loads(path.read_text())
    if not isinstance(rows, list):
        raise ValueError("dataset root must be a list")
    return rows


def audit(path: Path) -> dict[str, Any]:
    rows = load_rows(path)
    findings: list[str] = []

    ids = [str(row.get("id", "")) for row in rows]
    id_counts = Counter(ids)
    duplicate_ids = sorted(row_id for row_id, count in id_counts.items() if count > 1)
    if duplicate_ids:
        findings.append(f"duplicate_ids={duplicate_ids}")

    missing_fields = []
    invalid_labels = []
    empty_text = []
    private_hits = []
    category_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    high_by_category: Counter[str] = Counter()
    query_lengths = []
    document_lengths = []
    unique_texts = set()
    pools: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        row_id = str(row.get("id", "<missing-id>"))
        missing = REQUIRED_FIELDS - set(row)
        if missing:
            missing_fields.append({"id": row_id, "missing": sorted(missing)})
            continue

        expected = str(row["expected"])
        category = str(row["category"])
        query = str(row["query"])
        document = str(row["document"])

        category_counts[category] += 1
        label_counts[expected] += 1
        if expected == "high":
            high_by_category[category] += 1
        if expected not in EXPECTED_LABELS:
            invalid_labels.append({"id": row_id, "expected": expected})

        if not query.strip() or not document.strip():
            empty_text.append(row_id)

        query_lengths.append(len(query))
        document_lengths.append(len(document))
        unique_texts.add(query)
        unique_texts.add(document)
        pools[category].add(document)

        text = f"{query}\n{document}"
        for label, pattern in PRIVATE_PATTERNS.items():
            if pattern.search(text):
                private_hits.append({"id": row_id, "pattern": label})
        for match in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text):
            if not is_allowed_ip(match):
                private_hits.append({"id": row_id, "pattern": "private_ipv4"})

    categories_with_small_pools = sorted(
        (
            {"category": category, "unique_documents": len(documents)}
            for category, documents in pools.items()
            if len(documents) < 6
        ),
        key=lambda row: (row["unique_documents"], row["category"]),
    )

    severe_short_high_queries = sorted(
        row["id"]
        for row in rows
        if row.get("expected") == "high" and len(str(row.get("query", "")).strip()) <= 3
    )

    if missing_fields:
        findings.append(f"missing_fields={len(missing_fields)}")
    if invalid_labels:
        findings.append(f"invalid_labels={len(invalid_labels)}")
    if empty_text:
        findings.append(f"empty_text={len(empty_text)}")
    if private_hits:
        findings.append(f"private_hits={len(private_hits)}")

    return {
        "dataset": str(path),
        "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "pair_count": len(rows),
        "unique_texts": len(unique_texts),
        "category_count": len(category_counts),
        "label_counts": dict(sorted(label_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "high_by_category": dict(sorted(high_by_category.items())),
        "query_length": {
            "min": min(query_lengths) if query_lengths else 0,
            "max": max(query_lengths) if query_lengths else 0,
            "avg": round(sum(query_lengths) / len(query_lengths), 2) if query_lengths else 0,
        },
        "document_length": {
            "min": min(document_lengths) if document_lengths else 0,
            "max": max(document_lengths) if document_lengths else 0,
            "avg": round(sum(document_lengths) / len(document_lengths), 2) if document_lengths else 0,
        },
        "duplicate_ids": duplicate_ids,
        "missing_fields": missing_fields,
        "invalid_labels": invalid_labels,
        "empty_text": empty_text,
        "private_hits": private_hits,
        "categories_with_small_pools": categories_with_small_pools,
        "severe_short_high_queries": severe_short_high_queries,
        "findings": findings,
        "status": "pass" if not findings else "fail",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Dataset Quality Report",
        "",
        "Generated by `scripts/audit_dataset.py`.",
        "",
        "## Summary",
        "",
        f"- status: `{report['status']}`",
        f"- pairs: `{report['pair_count']}`",
        f"- unique_texts: `{report['unique_texts']}`",
        f"- categories: `{report['category_count']}`",
        f"- dataset_sha256: `{report['dataset_sha256']}`",
        "",
        "## Labels",
        "",
        "| Label | Count |",
        "|-------|-------|",
    ]
    for label, count in report["label_counts"].items():
        lines.append(f"| {label} | {count} |")

    lines.extend([
        "",
        "## Text Lengths",
        "",
        "| Field | Min | Avg | Max |",
        "|-------|-----|-----|-----|",
        f"| query | {report['query_length']['min']} | {report['query_length']['avg']} | {report['query_length']['max']} |",
        f"| document | {report['document_length']['min']} | {report['document_length']['avg']} | {report['document_length']['max']} |",
        "",
        "## Structural Checks",
        "",
        f"- duplicate IDs: `{len(report['duplicate_ids'])}`",
        f"- missing required fields: `{len(report['missing_fields'])}`",
        f"- invalid labels: `{len(report['invalid_labels'])}`",
        f"- empty query/document text: `{len(report['empty_text'])}`",
        f"- private pattern hits: `{len(report['private_hits'])}`",
        f"- very short high-query IDs: `{len(report['severe_short_high_queries'])}`",
        "",
        "## Retrieval Pool Notes",
        "",
        "MRR skips categories with fewer than six unique documents. This is intentional to avoid trivial Recall@5 behavior.",
        "",
        "| Category | Unique Documents |",
        "|----------|------------------|",
    ])
    if report["categories_with_small_pools"]:
        for row in report["categories_with_small_pools"]:
            lines.append(f"| {row['category']} | {row['unique_documents']} |")
    else:
        lines.append("| none | - |")

    if report["severe_short_high_queries"]:
        lines.extend([
            "",
            "## Very Short High Queries",
            "",
            "These pair IDs intentionally test vague or shorthand memory recall. The audit lists IDs only and does not print pair text.",
            "",
            "| Pair ID |",
            "|---------|",
        ])
        for row_id in report["severe_short_high_queries"]:
            lines.append(f"| `{row_id}` |")

    lines.extend([
        "",
        "## Reviewer Notes",
        "",
        "- This audit checks structure, safety, and benchmark hygiene.",
        "- It does not prove semantic correctness by itself.",
        "- Semantic cleanup review and pinned P0 local-GGUF reruns are complete for public v0.1 candidate scope.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = audit(args.dataset)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(report))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
