#!/usr/bin/env python3
"""Run the public-release preflight checks for the MAMMR candidate bundle."""

from __future__ import annotations

import json
import hashlib
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from run_0g_sandbox_preflight import build_archive


ROOT = Path(__file__).resolve().parents[1]
STALE_SHA_PATTERNS = [
    "3e02895787d138a67bc7a1bbc43249ccb026e22e86412f64690420dc0ddc9343",
    "40082c4af5c0d9fd4596cbf2635a0c6f47294cd047e1125206025e6d8a7f714a",
    "6babc08752a24b6ec90e63f24f66c6d43e2526e7055cf02770a32e32aabe9244",
    "4eb66b4677da275e257e0a8b619698a81ca3581fc88f920cd7b6f51a2f700c59",
    "02fd2d56a5f5e1ef005bcbed48ebefd17813e9ae27e7755ee13765e155ce7ded",
    "b457ff422cc59fe921ca4f8988b4ed913d19ea123de62e2fc694a01e7b203d69",
    "e643a43bd609f5e81879478f455567b2fb9501c44434770011648c67e3ee7d23",
    "8c7b7bb3b815440021d571ee39e424702615d646bca0e260c23fe92facb96610",
    "23068762bc42248379d9789c7f3bf4b48577535c31f88a007cc3cb5b9ed5f34e",
    "730ce1cd5f3681ed63025e7542e31294d79c0bbb43688025a5a3941519da469b",
    "f959df5d19266465afbc95e65dc2a1e419db4efaf1579113b719b5aefcd526c9",
]
HISTORICAL_DIAGNOSTIC_RESULTS = {
    "qwen3-0.6b-q8_0.json",
    "qwen3-0.6b-q8_0-rerun-20260505.json",
}
RELEASE_CRITICAL_PATHS = [
    "RELEASE-MANIFEST.md",
    "docs/domain-coverage.md",
    "docs/public-scope-and-privacy-review.md",
    "docs/reproducing-pinned-local-gguf.md",
    "docs/reviewer-guide.md",
    "metadata/0g-sandbox-run-20260506.json",
    "metadata/bge-m3-q8_0-pinned-20260506.json",
    "metadata/jina-v3-q8_0-pinned-20260506.json",
    "metadata/qwen3-0.6b-q8_0-pinned-20260506.json",
    "metadata/snowflake-arctic-l-v2-q8_0-pinned-20260506.json",
    "results/bge-m3-q8_0-pinned-20260506.json",
    "results/jina-v3-q8_0-pinned-20260506.json",
    "results/qwen3-0.6b-q8_0-pinned-20260506.json",
    "results/snowflake-arctic-l-v2-q8_0-pinned-20260506.json",
    "scripts/audit_domain_coverage.py",
    "scripts/bootstrap_pinned_scores.py",
    "scripts/public_release_preflight.py",
    "scripts/run_0g_sandbox_preflight.py",
]


def run(name: str, command: list[str]) -> bool:
    print(f"== {name}")
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode != 0:
        print(f"FAILED: {name}", file=sys.stderr)
        return False
    print(f"PASSED: {name}")
    return True


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text())


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_json_parse() -> bool:
    print("== json parse")
    count = 0
    for base in ["data", "metadata", "results"]:
        for path in (ROOT / base).rglob("*.json"):
            try:
                load_json(path)
            except Exception as exc:
                print(f"{path.relative_to(ROOT)} failed to parse: {exc}", file=sys.stderr)
                print("FAILED: json parse", file=sys.stderr)
                return False
            count += 1
    print(f"parsed_json_files={count}")
    print("PASSED: json parse")
    return True


def check_hash_chain() -> bool:
    print("== result hash chain")
    public_sha = file_sha256(ROOT / "data" / "mammr_pairs_public.json")
    heldout_sha = file_sha256(ROOT / "data" / "heldout_mini_public.json")
    failures: list[str] = []
    for path in (ROOT / "results").glob("*-pinned-20260506.json"):
        payload = load_json(path)
        if payload.get("dataset_sha256") != public_sha:
            failures.append(f"{path.relative_to(ROOT)} has dataset_sha256={payload.get('dataset_sha256')}")
    for path in (ROOT / "results").glob("*.json"):
        if path.name in {"public-v0.1-summary.md", "strong-evidence-summary.json"}:
            continue
        payload = load_json(path)
        dataset_sha = payload.get("dataset_sha256")
        if dataset_sha == public_sha:
            continue
        if path.name not in HISTORICAL_DIAGNOSTIC_RESULTS:
            failures.append(
                f"{path.relative_to(ROOT)} has non-current dataset_sha256={dataset_sha}"
            )
            continue
        if payload.get("result_scope") != "historical_diagnostic":
            failures.append(f"{path.relative_to(ROOT)} missing result_scope=historical_diagnostic")
        if payload.get("current_public_comparison") is not False:
            failures.append(f"{path.relative_to(ROOT)} must set current_public_comparison=false")
        if payload.get("superseded_by") != "results/qwen3-0.6b-q8_0-pinned-20260506.json":
            failures.append(f"{path.relative_to(ROOT)} must point superseded_by to the pinned Qwen3 result")
    for path in (ROOT / "metadata").glob("*-pinned-20260506.json"):
        payload = load_json(path)
        if payload.get("dataset_sha256") != public_sha:
            failures.append(f"{path.relative_to(ROOT)} has dataset_sha256={payload.get('dataset_sha256')}")
    for path in (ROOT / "results" / "retrieval").glob("*20260506.json"):
        payload = load_json(path)
        if payload.get("dataset_sha256") != public_sha:
            failures.append(f"{path.relative_to(ROOT)} has dataset_sha256={payload.get('dataset_sha256')}")
    for path in (ROOT / "results" / "reranker").glob("*20260506.json"):
        payload = load_json(path)
        if payload.get("dataset_sha256") != public_sha:
            failures.append(f"{path.relative_to(ROOT)} has dataset_sha256={payload.get('dataset_sha256')}")
        reranked = ((payload.get("metrics") or {}).get("reranked") or {})
        if reranked.get("rerank_errors") != 0:
            failures.append(
                f"{path.relative_to(ROOT)} has rerank_errors={reranked.get('rerank_errors')}"
            )
    for path in (ROOT / "results" / "heldout").glob("*20260506.json"):
        payload = load_json(path)
        if payload.get("dataset_sha256") != heldout_sha:
            failures.append(f"{path.relative_to(ROOT)} has dataset_sha256={payload.get('dataset_sha256')}")
        backend = payload.get("backend_metadata") or {}
        if backend.get("dataset_sha256") != heldout_sha:
            failures.append(
                f"{path.relative_to(ROOT)} backend_metadata.dataset_sha256={backend.get('dataset_sha256')}"
            )
    sandbox_record = ROOT / "metadata" / "0g-sandbox-run-20260506.json"
    if sandbox_record.exists():
        payload = load_json(sandbox_record)
        if payload.get("dataset_sha256") != public_sha:
            failures.append(
                f"{sandbox_record.relative_to(ROOT)} has dataset_sha256={payload.get('dataset_sha256')}"
            )
        _archive_payload, archive_sha, _dataset_sha = build_archive(exclude_path=sandbox_record)
        recorded_archive_sha = payload.get("artifact_archive_sha256")
        if recorded_archive_sha != archive_sha:
            failures.append(
                f"{sandbox_record.relative_to(ROOT)} archive is stale: "
                f"artifact_archive_sha256={recorded_archive_sha}, current={archive_sha}"
            )
        result = payload.get("result") or {}
        if result.get("public_release_preflight") != "pass":
            failures.append(
                f"{sandbox_record.relative_to(ROOT)} has public_release_preflight={result.get('public_release_preflight')}"
            )
    analysis_summary = ROOT / "paper" / "analysis-summary.json"
    if analysis_summary.exists():
        payload = load_json(analysis_summary)
        sandbox_summary = payload.get("sandbox_preflight") or {}
        if "artifact_archive_sha256" in sandbox_summary:
            failures.append(
                "paper/analysis-summary.json must not duplicate artifact_archive_sha256; "
                "the archive hash is self-referential outside the metadata run record"
            )
    if failures:
        print("\n".join(failures), file=sys.stderr)
        print("FAILED: result hash chain", file=sys.stderr)
        return False
    print("PASSED: result hash chain")
    return True


def check_summary_metric_consistency() -> bool:
    print("== summary metric consistency")
    failures: list[str] = []
    pinned_paths = [
        ("bge", "BGE-M3 Q8_0", "cls", ROOT / "results" / "bge-m3-q8_0-pinned-20260506.json"),
        (
            "snowflake",
            "Snowflake-Arctic-L-v2 Q8_0",
            "cls",
            ROOT / "results" / "snowflake-arctic-l-v2-q8_0-pinned-20260506.json",
        ),
        ("jina", "Jina-v3 Q8_0", "mean", ROOT / "results" / "jina-v3-q8_0-pinned-20260506.json"),
        (
            "qwen3",
            "Qwen3-0.6B Q8_0",
            "last",
            ROOT / "results" / "qwen3-0.6b-q8_0-pinned-20260506.json",
        ),
    ]
    pinned = {
        key: {
            "label": label,
            "pooling": pooling,
            "file": path.name,
            "payload": load_json(path),
        }
        for key, label, pooling, path in pinned_paths
    }
    ranked = sorted(pinned.items(), key=lambda item: item[1]["payload"]["weighted_score"], reverse=True)

    analysis = load_json(ROOT / "paper" / "analysis-summary.json")
    public_sha = file_sha256(ROOT / "data" / "mammr_pairs_public.json")
    if analysis.get("dataset", {}).get("sha256") != public_sha:
        failures.append("paper/analysis-summary.json dataset.sha256 does not match current dataset")
    analysis_by_file = {
        Path(row["file"]).name: row for row in analysis.get("pinned_local_gguf", [])
    }
    for key, row in pinned.items():
        payload = row["payload"]
        summary = analysis_by_file.get(row["file"])
        if not summary:
            failures.append(f"paper/analysis-summary.json missing {row['file']}")
            continue
        for metric in ["dataset_sha256", "weighted_score", "unweighted_score", "mrr", "recall_at_5"]:
            if summary.get(metric) != payload.get(metric):
                failures.append(f"paper/analysis-summary.json {row['file']} {metric} mismatch")

    pinned_doc = (ROOT / "docs" / "pinned-public-reruns.md").read_text()
    glance_doc = (ROOT / "docs" / "results-at-a-glance.md").read_text()
    public_summary = (ROOT / "results" / "public-v0.1-summary.md").read_text()
    for rank, (_key, row) in enumerate(ranked, start=1):
        payload = row["payload"]
        weighted = f"{payload['weighted_score']:.4f}"
        unweighted = f"{payload['unweighted_score']:.4f}"
        mrr = f"{payload['mrr']:.4f}"
        recall5 = f"{payload['recall_at_5']:.4f}"
        pinned_line = (
            f"| {rank} | {row['label']} | {row['pooling']} | {weighted} |"
        )
        glance_line = f"| {rank} | {row['label']} | {weighted} | {mrr} | {recall5} |"
        summary_line = (
            f"| {rank} | {row['label']} | {weighted} | {unweighted} | {mrr} | {recall5} |"
        )
        if pinned_line not in pinned_doc:
            failures.append(f"docs/pinned-public-reruns.md missing current row for {row['label']}")
        if glance_line not in glance_doc:
            failures.append(f"docs/results-at-a-glance.md missing current row for {row['label']}")
        if summary_line not in public_summary:
            failures.append(f"results/public-v0.1-summary.md missing current row for {row['label']}")

    strong = load_json(ROOT / "results" / "strong-evidence-summary.json")
    reranker_summary = analysis.get("sanitized_reranker_matrix", {})
    for model_key, rerankers in strong.get("reranker", {}).items():
        for reranker_key, metrics in rerankers.items():
            summary = reranker_summary.get(model_key, {}).get(reranker_key, {})
            for metric in ["baseline_mrr", "reranked_mrr", "delta_mrr"]:
                if summary.get(metric) != metrics.get(metric):
                    failures.append(
                        f"paper/analysis-summary.json reranker {model_key}/{reranker_key} {metric} mismatch"
                    )

    if failures:
        print("\n".join(failures), file=sys.stderr)
        print("FAILED: summary metric consistency", file=sys.stderr)
        return False
    print("PASSED: summary metric consistency")
    return True


def check_stale_references() -> bool:
    print("== stale public references")
    failures: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.relative_to(ROOT) == Path("scripts/public_release_preflight.py"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "pinned-20260505" in text:
            failures.append(f"{path.relative_to(ROOT)} contains pinned-20260505")
        if "cached-vector MRR" in text:
            failures.append(
                f"{path.relative_to(ROOT)} contains unsupported cached-vector MRR CI wording"
            )
        for stale_sha in STALE_SHA_PATTERNS:
            if stale_sha in text:
                failures.append(f"{path.relative_to(ROOT)} contains stale SHA {stale_sha[:12]}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        print("FAILED: stale public references", file=sys.stderr)
        return False
    print("PASSED: stale public references")
    return True


def check_local_artifacts_absent(*, clean: bool = False) -> bool:
    print("== local ignored artifacts")
    cleaned: list[str] = []
    generated: list[Path] = []
    for path in ROOT.rglob("__pycache__"):
        if ".git" not in path.parts:
            generated.append(path)
    for path in ROOT.rglob(".DS_Store"):
        if ".git" not in path.parts:
            generated.append(path)
    for path in ROOT.glob(".tmp-*"):
        if ".git" not in path.parts:
            generated.append(path)
    for path in ROOT.rglob("*.pyc"):
        if ".git" not in path.parts:
            generated.append(path)
    if clean:
        for path in sorted(generated, key=lambda item: len(item.parts), reverse=True):
            if not path.exists():
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            cleaned.append(str(path.relative_to(ROOT)))
    if cleaned:
        print("removed generated local artifacts: " + ", ".join(sorted(cleaned)))
    blocked = [
        "data/cleanup_candidates.json",
    ]
    failures = [item for item in blocked if (ROOT / item).exists()]
    failures.extend(
        str(path.relative_to(ROOT))
        for path in ROOT.glob(".tmp-*")
        if ".git" not in path.parts
    )
    generated_existing = [path for path in generated if path.exists()]
    if generated_existing:
        tracked = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "ls-files",
                "--",
                *[str(path.relative_to(ROOT)) for path in generated_existing],
            ],
            text=True,
            capture_output=True,
        )
        tracked_generated = tracked.stdout.splitlines()
        if tracked_generated:
            failures.extend(tracked_generated)
        else:
            print(
                "WARNING: ignored generated local artifacts present: "
                + ", ".join(sorted(str(path.relative_to(ROOT)) for path in generated_existing))
            )
            if not clean:
                print("Run with --clean to remove them from the local workspace.")
    if failures:
        for item in failures:
            print(f"{item} should not be present in a public release workspace", file=sys.stderr)
        if not clean:
            print("Run with --clean to remove generated local artifacts.", file=sys.stderr)
        print("FAILED: local ignored artifacts", file=sys.stderr)
        return False
    print("PASSED: local ignored artifacts")
    return True


def check_git_diff_whitespace() -> bool:
    try:
        git_probe = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"],
            text=True,
            capture_output=True,
        )
    except FileNotFoundError:
        print("== git diff whitespace")
        print("SKIPPED: git not installed")
        return True
    if git_probe.returncode != 0 or git_probe.stdout.strip() != "true":
        print("== git diff whitespace")
        print("SKIPPED: not a git checkout")
        return True
    return run("git diff whitespace", ["git", "diff", "HEAD", "--check"])


def check_release_critical_tracked() -> bool:
    print("== release-critical tracked files")
    try:
        git_probe = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"],
            text=True,
            capture_output=True,
        )
    except FileNotFoundError:
        print("SKIPPED: git not installed")
        return True
    if git_probe.returncode != 0 or git_probe.stdout.strip() != "true":
        print("SKIPPED: not a git checkout")
        return True
    status = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=all"],
        text=True,
        capture_output=True,
        check=True,
    )
    untracked = {
        line[3:]
        for line in status.stdout.splitlines()
        if line.startswith("?? ")
    }
    missing = [path for path in RELEASE_CRITICAL_PATHS if not (ROOT / path).exists()]
    untracked_release = [path for path in RELEASE_CRITICAL_PATHS if path in untracked]
    if missing or untracked_release:
        for path in missing:
            print(f"{path} is missing from the release workspace", file=sys.stderr)
        for path in untracked_release:
            print(f"{path} is release-critical but untracked", file=sys.stderr)
        print("FAILED: release-critical tracked files", file=sys.stderr)
        return False
    print("PASSED: release-critical tracked files")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run public-release checks for the MAMMR candidate bundle."
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="remove generated local artifacts such as .DS_Store, .tmp-*, __pycache__, and .pyc before checking",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks = [
        run("public safety", ["python3", "scripts/check_public_safety.py"]),
        run("main dataset audit", ["python3", "scripts/audit_dataset.py"]),
        run("heldout dataset audit", ["python3", "scripts/audit_dataset.py", "--dataset", "data/heldout_mini_public.json"]),
        run("domain coverage audit", ["python3", "scripts/audit_domain_coverage.py"]),
        run("embedding evaluator dry-run", ["python3", "scripts/run_embedding_eval.py", "--dry-run"]),
        check_json_parse(),
        check_hash_chain(),
        check_summary_metric_consistency(),
        check_stale_references(),
        check_local_artifacts_absent(clean=args.clean),
        check_git_diff_whitespace(),
        check_release_critical_tracked(),
    ]
    if all(checks):
        print("PUBLIC PREFLIGHT PASSED")
        return 0
    print("PUBLIC PREFLIGHT FAILED", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
