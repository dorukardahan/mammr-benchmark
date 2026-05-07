#!/usr/bin/env python3
"""Build deterministic blind-review sample for MAMMR label review."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data" / "mammr_pairs_public.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260506)
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "independent_review_sample_20260506.json")
    args = parser.parse_args()

    rows = json.loads(args.dataset.read_text())
    rng = random.Random(args.seed)
    sample = sorted(rng.sample(rows, min(args.sample_size, len(rows))), key=lambda row: row["id"])
    public_sample = [
        {
            "id": row["id"],
            "category": row["category"],
            "query": row["query"],
            "document": row["document"],
        }
        for row in sample
    ]
    args.out.write_text(json.dumps(public_sample, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {args.out}")
    print(f"sample_size={len(public_sample)} seed={args.seed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
