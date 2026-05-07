#!/usr/bin/env python3
"""Bootstrap weighted-score intervals for pinned public result files."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = [
    ROOT / "results" / "bge-m3-q8_0-pinned-20260506.json",
    ROOT / "results" / "snowflake-arctic-l-v2-q8_0-pinned-20260506.json",
    ROOT / "results" / "jina-v3-q8_0-pinned-20260506.json",
    ROOT / "results" / "qwen3-0.6b-q8_0-pinned-20260506.json",
]


def percentile(values: list[float], p: float) -> float:
    if not values:
        raise ValueError("empty values")
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    lo = int(index)
    hi = min(lo + 1, len(ordered) - 1)
    frac = index - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def weighted_score_from_sample(categories: dict[str, dict[str, Any]], pairs_by_category: dict[str, list[bool]], rng: random.Random) -> float:
    weighted_sum = 0.0
    weight_total = 0.0
    for category, outcomes in pairs_by_category.items():
        if not outcomes:
            continue
        sample = [rng.choice(outcomes) for _ in outcomes]
        accuracy = sum(1 for value in sample if value) / len(sample)
        weight = float(categories.get(category, {}).get("weight", 4))
        weighted_sum += accuracy * weight
        weight_total += weight
    return weighted_sum / weight_total if weight_total else 0.0


def summarize(path: Path, iterations: int, seed: int) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    pairs_by_category: dict[str, list[bool]] = defaultdict(list)
    for pair in payload["pairs"]:
        pairs_by_category[pair["category"]].append(pair["status"] == "pass")
    rng = random.Random(seed)
    values = [
        weighted_score_from_sample(payload["categories"], pairs_by_category, rng)
        for _ in range(iterations)
    ]
    return {
        "model": payload["model"],
        "weighted": payload["weighted_score"],
        "weighted_ci95_low": round(percentile(values, 0.025), 4),
        "weighted_ci95_high": round(percentile(values, 0.975), 4),
        "iterations": iterations,
        "seed": seed,
        "file": str(path.relative_to(ROOT)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260507)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("results", nargs="*", type=Path)
    args = parser.parse_args()

    paths = args.results or DEFAULT_RESULTS
    rows = [summarize(path, args.iterations, args.seed + index) for index, path in enumerate(paths)]
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0

    print("| Model | Weighted | Stratified bootstrap 95% CI |")
    print("|-------|----------|------------------------------|")
    for row in rows:
        print(
            f"| {row['model']} | {row['weighted']:.4f} | "
            f"{row['weighted_ci95_low']:.4f} - {row['weighted_ci95_high']:.4f} |"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
