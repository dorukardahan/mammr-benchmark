#!/usr/bin/env python3
"""Create a public-safe cleanup queue from a MAMMR public result JSON."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "mammr_pairs_public.json")
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "cleanup_candidates.json")
    args = parser.parse_args()

    rows = {row["id"]: row for row in json.loads(args.dataset.read_text())}
    result = json.loads(args.result.read_text())
    candidates = []
    category_failures = Counter()
    label_failures = Counter()
    for pair_result in result["pairs"]:
        if pair_result["status"] == "pass":
            continue
        row = rows[pair_result["id"]]
        category_failures[row["category"]] += 1
        label_failures[row["expected"]] += 1
        if row["expected"] == "high":
            candidates.append(
                {
                    "id": row["id"],
                    "category": row["category"],
                    "expected": row["expected"],
                    "similarity": pair_result["similarity"],
                    "margin": pair_result["margin"],
                    "query": row["query"],
                    "document": row["document"],
                    "review_note": "High pair below threshold; review whether sanitization preserved semantic anchors.",
                }
            )

    candidates.sort(key=lambda row: row["similarity"])
    output = {
        "source_result": str(args.result),
        "total_candidates": len(candidates),
        "category_failures": dict(category_failures.most_common()),
        "label_failures": dict(label_failures.most_common()),
        "high_failure_candidates": candidates,
    }
    args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {args.out}")
    print(f"high_failure_candidates={len(candidates)}")
    for category, count in category_failures.most_common(10):
        print(f"{category}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

