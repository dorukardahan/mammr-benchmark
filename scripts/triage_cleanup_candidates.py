#!/usr/bin/env python3
"""Triage high-relevance cleanup candidates without printing pair text.

The script reads data/cleanup_candidates.json and classifies each high-pair
failure by severity. It intentionally reports only IDs, categories, scores, and
flags so it can be used in public release review without leaking source text.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "cleanup_candidates.json"

ANCHOR_RE = re.compile(
    r"\[[A-Z0-9_ -]{2,}\]"
    r"|example\.(com|org|net)"
    r"|localhost"
    r"|127\.0\.0\.1"
    r"|\b(project|repo|service|app|agent|workspace|server|gateway|memory|provider|model|api|database|dashboard)\b",
    re.IGNORECASE,
)

CODE_OPS_RE = re.compile(
    r"[/{}:=_`$]"
    r"|\b(json|yaml|env|cron|systemd|docker|sqlite|http|https|ssh|error|stack|trace|config)\b",
    re.IGNORECASE,
)


def priority(similarity: float) -> str:
    if similarity < 0.20:
        return "P0_rewrite_or_drop"
    if similarity < 0.35:
        return "P1_semantic_rewrite"
    if similarity < 0.45:
        return "P2_review_and_rewrite_if_needed"
    return "P3_near_threshold_calibration"


def flags(candidate: dict[str, Any]) -> list[str]:
    text = f"{candidate.get('query', '')}\n{candidate.get('document', '')}"
    result: list[str] = []
    if ANCHOR_RE.search(text):
        result.append("anchor_or_sanitization_risk")
    if CODE_OPS_RE.search(text):
        result.append("code_or_ops_surface")
    if len(candidate.get("query", "")) <= 8:
        result.append("very_short_query")
    if float(candidate["similarity"]) < 0.20:
        result.append("severe_similarity_failure")
    if float(candidate["similarity"]) >= 0.45:
        result.append("near_threshold")
    return result


def load_candidates(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text())
    candidates = payload.get("high_failure_candidates")
    if not isinstance(candidates, list):
        raise ValueError("cleanup_candidates.json missing high_failure_candidates list")
    return candidates


def build_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        rows.append(
            {
                "id": candidate["id"],
                "category": candidate["category"],
                "expected": candidate["expected"],
                "similarity": round(float(candidate["similarity"]), 4),
                "margin": round(float(candidate["margin"]), 4),
                "priority": priority(float(candidate["similarity"])),
                "flags": flags(candidate),
            }
        )
    return rows


def print_markdown(rows: list[dict[str, Any]]) -> None:
    by_priority = Counter(row["priority"] for row in rows)
    by_flag = Counter(flag for row in rows for flag in row["flags"])
    by_category = Counter(row["category"] for row in rows)

    print("# Cleanup Candidate Triage")
    print()
    print(f"Total high-pair failures: {len(rows)}")
    print()
    print("## Priority Counts")
    print()
    print("| Priority | Count |")
    print("|----------|-------|")
    for name in [
        "P0_rewrite_or_drop",
        "P1_semantic_rewrite",
        "P2_review_and_rewrite_if_needed",
        "P3_near_threshold_calibration",
    ]:
        print(f"| {name} | {by_priority.get(name, 0)} |")

    print()
    print("## Flag Counts")
    print()
    print("| Flag | Count |")
    print("|------|-------|")
    for name, count in by_flag.most_common():
        print(f"| {name} | {count} |")

    print()
    print("## Category Counts")
    print()
    print("| Category | Count |")
    print("|----------|-------|")
    for name, count in by_category.most_common():
        print(f"| {name} | {count} |")

    p0_rows = [row for row in rows if row["priority"] == "P0_rewrite_or_drop"]
    if p0_rows:
        print()
        print("## P0 Queue")
        print()
        print("| Pair ID | Category | Similarity | Flags |")
        print("|---------|----------|------------|-------|")
        for row in p0_rows:
            print(
                f"| {row['id']} | {row['category']} | {row['similarity']:.4f} | "
                f"{', '.join(row['flags']) or 'none'} |"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--json", action="store_true", help="emit machine-readable rows")
    args = parser.parse_args()

    rows = build_rows(load_candidates(args.input))
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print_markdown(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
