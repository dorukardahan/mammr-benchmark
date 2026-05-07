#!/usr/bin/env python3
"""Compare high-label failures across pinned public embedding reruns.

The report is intentionally public-safe: it prints pair IDs, categories,
similarity scores, and aggregate counts, but not query or document text.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data" / "mammr_pairs_public.json"
DEFAULT_RESULTS = [
    ROOT / "results" / "snowflake-arctic-l-v2-q8_0-pinned-20260506.json",
    ROOT / "results" / "bge-m3-q8_0-pinned-20260506.json",
    ROOT / "results" / "jina-v3-q8_0-pinned-20260506.json",
    ROOT / "results" / "qwen3-0.6b-q8_0-pinned-20260506.json",
]


def short_label(path: Path, payload: dict[str, Any]) -> str:
    model = str(payload.get("model") or path.stem)
    aliases = [
        ("snowflake", "Snowflake-Arctic-L-v2 Q8_0"),
        ("bge-m3", "BGE-M3 Q8_0"),
        ("jina", "Jina-v3 Q8_0"),
        ("qwen3", "Qwen3-0.6B Q8_0"),
    ]
    lower = f"{model} {path.name}".lower()
    for needle, label in aliases:
        if needle in lower:
            return label
    return model


def load_dataset(path: Path) -> dict[str, dict[str, Any]]:
    rows = json.loads(path.read_text())
    return {row["id"]: row for row in rows}


def load_result(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    label = short_label(path, payload)
    pair_map = {row["id"]: row for row in payload["pairs"]}
    high_failures = {
        row["id"]
        for row in payload["pairs"]
        if row["expected"] == "high" and row["status"] == "fail"
    }
    return {
        "label": label,
        "path": str(path.relative_to(ROOT)),
        "dataset_sha256": payload.get("dataset_sha256"),
        "weighted_score": payload.get("weighted_score"),
        "unweighted_score": payload.get("unweighted_score"),
        "mrr": payload.get("mrr"),
        "recall_at_5": payload.get("recall_at_5"),
        "total_fail": payload.get("total_fail"),
        "high_failure_count": len(high_failures),
        "pair_map": pair_map,
        "high_failures": high_failures,
    }


def round_score(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def build_report(dataset: dict[str, dict[str, Any]], results: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [result["label"] for result in results]
    qwen_labels = {label for label in labels if "qwen3" in label.lower()}
    strong_labels = [label for label in labels if label not in qwen_labels]
    failure_by_id: dict[str, set[str]] = defaultdict(set)

    for result in results:
        for pair_id in result["high_failures"]:
            failure_by_id[pair_id].add(result["label"])

    all_high_ids = {pair_id for pair_id, row in dataset.items() if row.get("expected") == "high"}
    failed_all_models = {
        pair_id for pair_id, failed_labels in failure_by_id.items() if set(labels).issubset(failed_labels)
    }
    failed_all_strong = {
        pair_id
        for pair_id, failed_labels in failure_by_id.items()
        if strong_labels and set(strong_labels).issubset(failed_labels)
    }
    qwen_only = {
        pair_id
        for pair_id, failed_labels in failure_by_id.items()
        if failed_labels == qwen_labels and qwen_labels
    }

    failure_count_distribution = Counter(len(value) for value in failure_by_id.values())
    category_counts = Counter(dataset[pair_id]["category"] for pair_id in failure_by_id)
    all_strong_category_counts = Counter(dataset[pair_id]["category"] for pair_id in failed_all_strong)
    qwen_only_category_counts = Counter(dataset[pair_id]["category"] for pair_id in qwen_only)

    def pair_row(pair_id: str) -> dict[str, Any]:
        similarities = {}
        statuses = {}
        for result in results:
            pair = result["pair_map"][pair_id]
            similarities[result["label"]] = round_score(pair.get("similarity"))
            statuses[result["label"]] = pair.get("status")
        return {
            "id": pair_id,
            "category": dataset[pair_id]["category"],
            "failed_models": sorted(failure_by_id.get(pair_id, [])),
            "similarities": similarities,
            "statuses": statuses,
        }

    all_strong_rows = sorted(
        (pair_row(pair_id) for pair_id in failed_all_strong),
        key=lambda row: (
            sum(value for value in row["similarities"].values() if value is not None),
            row["id"],
        ),
    )
    qwen_only_rows = sorted(
        (pair_row(pair_id) for pair_id in qwen_only),
        key=lambda row: (row["similarities"].get(next(iter(qwen_labels)), 1.0), row["id"]),
    )

    def sorted_counter(counter: Counter[str]) -> dict[str, int]:
        return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))

    return {
        "dataset_high_pairs": len(all_high_ids),
        "labels": labels,
        "strong_baseline_labels": strong_labels,
        "model_summaries": [
            {
                key: value
                for key, value in result.items()
                if key
                in {
                    "label",
                    "path",
                    "dataset_sha256",
                    "weighted_score",
                    "unweighted_score",
                    "mrr",
                    "recall_at_5",
                    "total_fail",
                    "high_failure_count",
                }
            }
            for result in results
        ],
        "overlap_counts": {
            "unique_high_failures_any_model": len(failure_by_id),
            "failed_all_models": len(failed_all_models),
            "failed_all_strong_baselines": len(failed_all_strong),
            "qwen_only_high_failures": len(qwen_only),
        },
        "failure_count_distribution": dict(sorted(failure_count_distribution.items())),
        "category_counts_any_model": sorted_counter(category_counts),
        "category_counts_all_strong": sorted_counter(all_strong_category_counts),
        "category_counts_qwen_only": sorted_counter(qwen_only_category_counts),
        "all_strong_rows": all_strong_rows,
        "qwen_only_rows": qwen_only_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Pinned Failure Overlap Review")
    lines.append("")
    lines.append("Updated: 2026-05-06")
    lines.append("")
    lines.append(
        "This review compares high-label failures across the four pinned public local-GGUF reruns. "
        "It is public-safe: it reports pair IDs, categories, and scores, but not source text."
    )
    lines.append("")
    lines.append("## Model Summaries")
    lines.append("")
    lines.append("| Model | Weighted | MRR | Recall@5 | Total Fail | High Fail | Dataset SHA |")
    lines.append("|-------|----------|-----|----------|------------|-----------|-------------|")
    for row in report["model_summaries"]:
        lines.append(
            f"| {row['label']} | {round_score(row['weighted_score']):.4f} | "
            f"{round_score(row['mrr']):.4f} | {round_score(row['recall_at_5']):.4f} | "
            f"{row['total_fail']} | {row['high_failure_count']} | "
            f"`{str(row['dataset_sha256'])[:12]}` |"
        )
    lines.append("")
    lines.append("## Overlap Summary")
    lines.append("")
    lines.append("| Measure | Count |")
    lines.append("|---------|-------|")
    for key, value in report["overlap_counts"].items():
        lines.append(f"| {key} | {value} |")
    lines.append("")
    lines.append("Failure count distribution means how many models failed the same high pair.")
    lines.append("")
    lines.append("| Failed Model Count | High Pair Count |")
    lines.append("|--------------------|-----------------|")
    for key, value in report["failure_count_distribution"].items():
        lines.append(f"| {key} | {value} |")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The current public dataset is not globally broken: Snowflake, BGE-M3, and Jina-v3 stay strong on the same sanitized pairs. "
        "Most Qwen3 high failures are Qwen-only, so the dataset should not be mass-rewritten to improve one model."
    )
    lines.append("")
    lines.append(
        "The strongest cleanup candidates are the pairs failed by all three strong baselines. "
        "Those are more likely to expose ambiguous wording, sanitization damage, or genuinely difficult retrieval cases."
    )
    lines.append("")
    lines.append("## Strong-Baseline Failure Queue")
    lines.append("")
    lines.append("| Pair ID | Category | Failed Models | Similarities |")
    lines.append("|---------|----------|---------------|--------------|")
    for row in report["all_strong_rows"]:
        scores = ", ".join(f"{model}: {score:.4f}" for model, score in row["similarities"].items())
        failed = ", ".join(row["failed_models"])
        lines.append(f"| `{row['id']}` | {row['category']} | {failed} | {scores} |")
    lines.append("")
    lines.append("## Qwen-Only Failure Sample")
    lines.append("")
    lines.append(
        "These are diagnostic examples showing why Qwen3 should be treated as backend-specific evidence, "
        "not as a cleanup oracle."
    )
    lines.append("")
    lines.append("| Pair ID | Category | Similarities |")
    lines.append("|---------|----------|--------------|")
    for row in report["qwen_only_rows"][:20]:
        scores = ", ".join(f"{model}: {score:.4f}" for model, score in row["similarities"].items())
        lines.append(f"| `{row['id']}` | {row['category']} | {scores} |")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append("- Do not rewrite P1/P2 pairs solely because Qwen3 fails them.")
    lines.append("- Manually review the strong-baseline failure queue first.")
    lines.append("- Keep Qwen3 production discussion scoped to VPS deployment tradeoffs, not public leaderboard dominance.")
    lines.append("- Keep unreleased operational checks separate from public pinned reruns.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--results", type=Path, nargs="+", default=DEFAULT_RESULTS)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    results = [load_result(path) for path in args.results]
    dataset_hashes = {result["dataset_sha256"] for result in results}
    if len(dataset_hashes) != 1:
        raise ValueError(f"Result files use different dataset hashes: {sorted(dataset_hashes)}")

    report = build_report(dataset, results)
    if args.out_json:
        args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    markdown = render_markdown(report)
    if args.out_md:
        args.out_md.write_text(markdown)
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
