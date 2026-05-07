#!/usr/bin/env python3
"""Summarize independent MAMMR label review without printing pair text."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data" / "mammr_pairs_public.json"
DEFAULT_REVIEW = ROOT / "data" / "independent_label_review_codex_20260506.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--out-md", type=Path, default=ROOT / "docs" / "independent-label-review-codex-20260506.md")
    parser.add_argument("--out-json", type=Path, default=ROOT / "data" / "independent_label_review_summary_20260506.json")
    args = parser.parse_args()

    rows = {row["id"]: row for row in json.loads(args.dataset.read_text())}
    review = json.loads(args.review.read_text())
    reviewed = review["labels"]
    disagreements = []
    by_category: dict[str, Counter[str]] = defaultdict(Counter)
    by_label_pair: Counter[str] = Counter()
    original_counts: Counter[str] = Counter()
    reviewer_counts: Counter[str] = Counter()

    for item in reviewed:
        row = rows[item["id"]]
        original = row["expected"]
        reviewer = item["reviewer_label"]
        category = row["category"]
        original_counts[original] += 1
        reviewer_counts[reviewer] += 1
        by_category[category]["total"] += 1
        by_label_pair[f"{original}->{reviewer}"] += 1
        if original == reviewer:
            by_category[category]["agree"] += 1
        else:
            by_category[category]["disagree"] += 1
            disagreements.append(
                {
                    "id": item["id"],
                    "category": category,
                    "original_label": original,
                    "reviewer_label": reviewer,
                }
            )

    total = len(reviewed)
    agree = total - len(disagreements)
    summary: dict[str, Any] = {
        "reviewer": review["reviewer"],
        "review_date": review["review_date"],
        "sample_seed": review["sample_seed"],
        "sample_size": total,
        "agreement": {
            "count": agree,
            "rate": round(agree / total, 4) if total else 0.0,
            "disagreement_count": len(disagreements),
        },
        "original_label_counts": dict(sorted(original_counts.items())),
        "reviewer_label_counts": dict(sorted(reviewer_counts.items())),
        "label_transition_counts": dict(sorted(by_label_pair.items())),
        "category_agreement": {
            category: {
                "total": counts["total"],
                "agree": counts["agree"],
                "disagree": counts["disagree"],
                "agreement_rate": round(counts["agree"] / counts["total"], 4) if counts["total"] else 0.0,
            }
            for category, counts in sorted(by_category.items())
        },
        "disagreements": disagreements,
    }

    args.out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# Independent Label Review - Codex",
        "",
        "Date: 2026-05-06",
        "",
        "This is a second-model review of 100 deterministic sample pairs. The reviewer saw pair text and category, but not the original expected label. This report is public-safe and lists only IDs, labels, and aggregate counts.",
        "",
        "## Summary",
        "",
        f"- sample seed: `{review['sample_seed']}`",
        f"- sample size: `{total}`",
        f"- agreements: `{agree}`",
        f"- disagreements: `{len(disagreements)}`",
        f"- agreement rate: `{summary['agreement']['rate']:.4f}`",
        "",
        "## Label Counts",
        "",
        "| Label | Original | Reviewer |",
        "|-------|----------|----------|",
    ]
    for label in ["high", "medium_high", "medium", "low"]:
        lines.append(f"| {label} | {original_counts.get(label, 0)} | {reviewer_counts.get(label, 0)} |")

    lines.extend([
        "",
        "## Disagreements",
        "",
        "| Pair ID | Category | Original | Reviewer |",
        "|---------|----------|----------|----------|",
    ])
    for item in disagreements:
        lines.append(
            f"| `{item['id']}` | {item['category']} | {item['original_label']} | {item['reviewer_label']} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "Disagreements include boundary cases between adjacent labels, intentionally tricky negation/temporal examples, and possible label-validity issues. They require human adjudication before a final v0.2 label freeze, but they do not block the public v0.1 candidate because no automatic relabeling is being made.",
        "",
    ])
    args.out_md.write_text("\n".join(lines))
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    print(f"agreement_rate={summary['agreement']['rate']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
