#!/usr/bin/env python3
"""Build a human-review queue from second-model label disagreements."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data" / "mammr_pairs_public.json"
DEFAULT_SUMMARY = ROOT / "data" / "independent_label_review_summary_20260506.json"
DEFAULT_OUT_JSON = ROOT / "data" / "label_disagreement_review_queue_20260506.json"
DEFAULT_OUT_MD = ROOT / "docs" / "label-disagreement-review-queue.md"

LABEL_SCORE = {
    "low": 0,
    "medium": 1,
    "medium_high": 2,
    "high": 3,
}


def review_priority(original: str, reviewer: str) -> str:
    delta = LABEL_SCORE[original] - LABEL_SCORE[reviewer]
    if abs(delta) >= 2:
        return "high"
    if original == "high" or reviewer == "high":
        return "medium"
    return "low"


def suggested_action(original: str, reviewer: str) -> str:
    delta = LABEL_SCORE[original] - LABEL_SCORE[reviewer]
    if delta >= 2:
        return "Check if original label is too generous."
    if delta == 1:
        return "Check boundary between adjacent relevance labels."
    if delta <= -2:
        return "Check if original label is too strict."
    if delta == -1:
        return "Check whether partial relevance deserves a higher label."
    return "No action."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    args = parser.parse_args()

    summary = json.loads(args.summary.read_text())
    queue: list[dict[str, Any]] = []
    for item in summary["disagreements"]:
        original = item["original_label"]
        reviewer = item["reviewer_label"]
        queue.append(
            {
                "id": item["id"],
                "category": item["category"],
                "original_label": original,
                "reviewer_label": reviewer,
                "priority": review_priority(original, reviewer),
                "suggested_action": suggested_action(original, reviewer),
            }
        )

    priority_order = {"high": 0, "medium": 1, "low": 2}
    queue.sort(key=lambda item: (priority_order[item["priority"]], item["category"], item["id"]))

    args.out_json.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n")

    counts = {
        priority: sum(1 for item in queue if item["priority"] == priority)
        for priority in ["high", "medium", "low"]
    }
    lines = [
        "# Label Disagreement Review Queue",
        "",
        "This is the compact human-review queue derived from the 2026-05-06 second-model label review.",
        "It does not change the dataset. It only identifies labels a human reviewer should inspect before a future v0.2 label freeze.",
        "",
        "## Summary",
        "",
        f"- total disagreements: {len(queue)}",
        f"- high priority: {counts['high']}",
        f"- medium priority: {counts['medium']}",
        f"- low priority: {counts['low']}",
        "- source: `docs/independent-label-review-codex-20260506.md`",
        "- queue JSON: `data/label_disagreement_review_queue_20260506.json`",
        "- pair text source: `data/mammr_pairs_public.json`",
        "",
        "## Review Queue",
        "",
        "| Priority | Pair ID | Category | Original | Reviewer | Suggested Action |",
        "|----------|---------|----------|----------|----------|------------------|",
    ]
    for item in queue:
        lines.append(
            f"| {item['priority']} | `{item['id']}` | {item['category']} | "
            f"{item['original_label']} | {item['reviewer_label']} | "
            f"{item['suggested_action']} |"
        )

    lines.extend(
        [
            "",
            "## Release Decision",
            "",
            "These disagreements do not block public v0.1 because the release is labeled as a candidate and no automatic relabeling is being made.",
            "They should block a stronger v0.2 label-freeze claim until a human reviewer adjudicates them.",
            "",
        ]
    )
    args.out_md.write_text("\n".join(lines))
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    print(f"disagreements={len(queue)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
