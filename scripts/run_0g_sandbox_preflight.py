#!/usr/bin/env python3
"""Run the public MAMMR preflight inside a temporary 0G Sandbox.

The script is deliberately conservative:

- dry-run by default
- loads secrets only from env or a local env file
- never prints USER_KEY
- packages only public repository files
- deletes sandboxes it creates unless --keep is passed
"""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = "~/.config/benchmark-gap/0g-sandbox.env"
DEFAULT_SANDBOX_REPO = "~/.cache/benchmark-gap/0g-sandbox"
# Keep this as a shell expression, not an absolute user path, so the public
# scanner does not bless or publish a specific sandbox account layout.
REMOTE_ROOT = "${HOME}/project"
REMOTE_ARCHIVE = f"{REMOTE_ROOT}/mammr-public-candidate.tgz"
REMOTE_B64 = REMOTE_ARCHIVE + ".b64"
REMOTE_DIR = f"{REMOTE_ROOT}/mammr-public-candidate"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
PYTHON_VERSION_RE = re.compile(r"Python\s+\d+(?:\.\d+)+")

PUBLIC_TOP_LEVEL_FILES = {
    ".gitignore",
    "CITATION.cff",
    "LICENSE",
    "LICENSE-DATA-DOCS.md",
    "NEXT-STEPS.md",
    "README.md",
    "RELEASE-CHECK.txt",
}
PUBLIC_TOP_LEVEL_DIRS = {"data", "docs", "metadata", "paper", "results", "scripts"}
DEFAULT_RUN_RECORD = ROOT / "metadata" / "0g-sandbox-run-20260506.json"
SKIP_NAMES = {
    ".DS_Store",
    ".git",
    ".mammr-private-denylist.txt",
    "__pycache__",
}
SKIP_SUFFIXES = {".pyc", ".pyo", ".swp", ".swo"}
SKIP_RELATIVE_PATTERNS = (
    re.compile(r"^data/cleanup_candidates.*\.json$"),
    re.compile(r"^results/.*\.tmp\.json$"),
    re.compile(r"^results/private(?:/|$)"),
    re.compile(r"^vector-cache(?:/|$)"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run MAMMR public preflight in a temporary 0G Sandbox."
    )
    parser.add_argument(
        "--env-file",
        default=DEFAULT_ENV_FILE,
        help="Local env file with USER_KEY, OG_SANDBOX_API, OG_SANDBOX_REPO, and OG_SANDBOX_SNAPSHOT.",
    )
    parser.add_argument(
        "--sandbox-repo",
        default=os.environ.get("OG_SANDBOX_REPO", DEFAULT_SANDBOX_REPO),
        help="Path to a local clone of 0gfoundation/0g-sandbox.",
    )
    parser.add_argument("--api", default=os.environ.get("OG_SANDBOX_API", ""))
    parser.add_argument("--snapshot", default=os.environ.get("OG_SANDBOX_SNAPSHOT", ""))
    parser.add_argument("--name", default="mammr-public-preflight")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--startup-timeout", type=int, default=240)
    parser.add_argument("--chunk-size", type=int, default=30_000)
    parser.add_argument("--keep", action="store_true", help="Keep the created sandbox.")
    parser.add_argument("--execute", action="store_true", help="Create a sandbox and run the preflight.")
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional public-safe run record to write after execution.",
    )
    return parser.parse_args()


def load_env_file(path_text: str) -> None:
    path = Path(path_text).expanduser()
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def ensure_ready(args: argparse.Namespace) -> Path:
    load_env_file(args.env_file)
    if not args.api:
        args.api = os.environ.get("OG_SANDBOX_API", "")
    if not args.snapshot:
        args.snapshot = os.environ.get("OG_SANDBOX_SNAPSHOT", "")

    repo = Path(args.sandbox_repo).expanduser().resolve()
    if args.execute and not (repo / "cmd" / "user" / "main.go").exists():
        raise SystemExit(
            "0G Sandbox repo not found. Pass --sandbox-repo or set OG_SANDBOX_REPO."
        )
    if args.execute and shutil.which("go") is None:
        raise SystemExit("go is not installed or not in PATH.")
    if args.execute:
        if not args.api:
            raise SystemExit("--api or OG_SANDBOX_API is required with --execute.")
        if not os.environ.get("USER_KEY"):
            raise SystemExit("USER_KEY is required with --execute.")
    if args.chunk_size < 1000:
        raise SystemExit("--chunk-size must be at least 1000.")
    return repo


def is_public_path(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    rel_text = rel.as_posix()
    parts = rel.parts
    if any(part in SKIP_NAMES for part in parts):
        return False
    if path.suffix in SKIP_SUFFIXES:
        return False
    if any(pattern.search(rel_text) for pattern in SKIP_RELATIVE_PATTERNS):
        return False
    if len(parts) == 1:
        return parts[0] in PUBLIC_TOP_LEVEL_FILES
    return parts[0] in PUBLIC_TOP_LEVEL_DIRS


def relative_to_root(path: Path) -> Path | None:
    try:
        return path.expanduser().resolve(strict=False).relative_to(ROOT)
    except ValueError:
        return None


def build_archive(*, exclude_path: Path | None = None) -> tuple[bytes, str, str]:
    exclude_rel = relative_to_root(exclude_path) if exclude_path else None
    included: list[Path] = []
    for path in sorted(ROOT.rglob("*")):
        if exclude_rel is not None and path.relative_to(ROOT) == exclude_rel:
            continue
        if path.is_file() and is_public_path(path):
            included.append(path)

    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for path in included:
                info = tar.gettarinfo(str(path), arcname=str(path.relative_to(ROOT)))
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                info.mode = 0o644
                info.mtime = 0
                info.pax_headers = {}
                with path.open("rb") as fh:
                    tar.addfile(info, fh)

    payload = buffer.getvalue()
    archive_sha = hashlib.sha256(payload).hexdigest()
    dataset_sha = hashlib.sha256((ROOT / "data" / "mammr_pairs_public.json").read_bytes()).hexdigest()
    return payload, archive_sha, dataset_sha


def canonical_exclude_path(json_output: Path | None) -> Path | None:
    if json_output is not None:
        return json_output
    if DEFAULT_RUN_RECORD.exists():
        return DEFAULT_RUN_RECORD
    return None


def parse_json_objects(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    objects: list[dict[str, Any]] = []
    index = 0
    while index < len(text):
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            break
        if text.startswith("No sandboxes.", index):
            break
        obj, end = decoder.raw_decode(text, index)
        if isinstance(obj, dict):
            objects.append(obj)
        index = end
    return objects


def run_user(
    repo: Path,
    args: argparse.Namespace,
    user_args: list[str],
    *,
    check: bool = True,
    announce: str | None = None,
    echo_output: bool = True,
) -> subprocess.CompletedProcess[str] | None:
    if announce:
        print(announce)
    if not args.execute:
        return None
    completed = subprocess.run(
        ["go", "run", "./cmd/user/"] + user_args,
        cwd=repo,
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=args.timeout,
        check=False,
    )
    if echo_output and completed.stdout:
        print(completed.stdout, end="")
    if echo_output and completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if check and completed.returncode != 0:
        label = announce or "$ 0g-sandbox user command"
        raise RuntimeError(f"{label} failed with exit code {completed.returncode}")
    return completed


def create_sandbox(repo: Path, args: argparse.Namespace) -> str | None:
    user_args = ["create", "--api", args.api, "--name", args.name]
    if args.snapshot:
        user_args.extend(["--snapshot", args.snapshot])
    completed = run_user(
        repo,
        args,
        user_args,
        announce="$ 0g-sandbox user create --api <set> --name mammr-public-preflight",
        echo_output=False,
    )
    if completed is None:
        return None
    start = completed.stdout.find("{")
    if start < 0:
        raise RuntimeError("create output did not include JSON")
    data = json.loads(completed.stdout[start:])
    sandbox_id = data.get("id")
    if not isinstance(sandbox_id, str) or not sandbox_id:
        raise RuntimeError("create output did not include sandbox id")
    print("sandbox created")
    return sandbox_id


def list_sandboxes(repo: Path, args: argparse.Namespace) -> list[dict[str, Any]]:
    completed = run_user(
        repo,
        args,
        ["list", "--api", args.api],
        announce=None,
        echo_output=False,
    )
    if completed is None:
        return []
    return parse_json_objects(completed.stdout)


def wait_for_started(repo: Path, args: argparse.Namespace, sandbox_id: str) -> None:
    if not args.execute:
        return
    deadline = time.time() + args.startup_timeout
    while time.time() < deadline:
        for sandbox in list_sandboxes(repo, args):
            if sandbox.get("id") == sandbox_id:
                state = sandbox.get("state")
                print(f"sandbox state={state}")
                if state == "started":
                    return
                if state == "error":
                    raise RuntimeError("sandbox entered error state")
        time.sleep(5)
    raise TimeoutError("sandbox did not reach started state")


def exec_in_sandbox(
    repo: Path,
    args: argparse.Namespace,
    sandbox_id: str,
    command: str,
    *,
    announce: str,
    echo_output: bool = True,
) -> subprocess.CompletedProcess[str] | None:
    return run_user(
        repo,
        args,
        [
            "exec",
            "--api",
            args.api,
            "--id",
            sandbox_id,
            "--timeout",
            str(args.timeout),
            "--cmd",
            command,
        ],
        announce=announce,
        echo_output=echo_output,
    )


def upload_archive(repo: Path, args: argparse.Namespace, sandbox_id: str, payload: bytes, archive_sha: str) -> None:
    encoded = base64.b64encode(payload).decode("ascii")
    chunks = [encoded[i : i + args.chunk_size] for i in range(0, len(encoded), args.chunk_size)]
    print(f"archive bytes={len(payload)} sha256={archive_sha} chunks={len(chunks)}")
    if not args.execute:
        return

    exec_in_sandbox(
        repo,
        args,
        sandbox_id,
        f"sh -lc 'mkdir -p {REMOTE_ROOT} && rm -rf {REMOTE_DIR} {REMOTE_ARCHIVE} {REMOTE_B64}'",
        announce="$ sandbox exec prepare-upload",
        echo_output=False,
    )
    for index, chunk in enumerate(chunks, start=1):
        if index == 1 or index == len(chunks) or index % 20 == 0:
            print(f"upload_chunk={index}/{len(chunks)}")
        exec_in_sandbox(
            repo,
            args,
            sandbox_id,
            f"sh -lc 'printf \"%s\" \"{chunk}\" >> {REMOTE_B64}'",
            announce="",
            echo_output=False,
        )

    verify = exec_in_sandbox(
        repo,
        args,
        sandbox_id,
        (
            f"sh -lc 'base64 -d {REMOTE_B64} > {REMOTE_ARCHIVE} && "
            "python3 - <<\"PY\"\n"
            "from pathlib import Path\n"
            "import hashlib\n"
            "archive = Path.home() / \"project\" / \"mammr-public-candidate.tgz\"\n"
            "print(hashlib.sha256(archive.read_bytes()).hexdigest())\n"
            "PY'"
        ),
        announce="$ sandbox exec verify-archive-sha",
        echo_output=False,
    )
    remote_sha = ""
    if verify:
        for token in verify.stdout.split():
            if len(token) == 64 and all(ch in "0123456789abcdef" for ch in token):
                remote_sha = token
                break
    print(f"remote_sha256={remote_sha}")
    if remote_sha != archive_sha:
        raise RuntimeError("uploaded archive SHA mismatch")

    exec_in_sandbox(
        repo,
        args,
        sandbox_id,
        f"sh -lc 'mkdir -p {REMOTE_DIR} && tar -xzf {REMOTE_ARCHIVE} -C {REMOTE_DIR}'",
        announce="$ sandbox exec extract-archive",
        echo_output=False,
    )


def run_remote_preflight(repo: Path, args: argparse.Namespace, sandbox_id: str) -> tuple[str, str]:
    version = exec_in_sandbox(
        repo,
        args,
        sandbox_id,
        "python3 --version",
        announce="$ sandbox exec python-version",
    )
    preflight = exec_in_sandbox(
        repo,
        args,
        sandbox_id,
        f"sh -lc 'cd {REMOTE_DIR} && python3 scripts/public_release_preflight.py'",
        announce="$ sandbox exec public-release-preflight",
    )
    python_output = ANSI_RE.sub("", (version.stdout or "") if version else "")
    match = PYTHON_VERSION_RE.search(python_output)
    python_version = match.group(0) if match else "unknown"
    preflight_output = (preflight.stdout or "") if preflight else ""
    return python_version, preflight_output


def delete_sandbox(repo: Path, args: argparse.Namespace, sandbox_id: str) -> None:
    run_user(
        repo,
        args,
        ["delete", "--api", args.api, "--id", sandbox_id],
        check=False,
        announce="$ 0g-sandbox user delete --api <set> --id <created>",
        echo_output=False,
    )
    print("sandbox deleted")


def write_run_record(
    path: Path,
    *,
    dataset_sha: str,
    archive_sha: str,
    python_version: str,
    preflight_output: str,
) -> None:
    record = {
        "run_type": "0g-sandbox-clean-room",
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "repository": "mammr-benchmark",
        "dataset_sha256": dataset_sha,
        "artifact_archive_sha256": archive_sha,
        "environment": {
            "runner": "0G Sandbox",
            "os": "linux",
            "python": python_version,
        },
        "commands": [
            "python3 scripts/public_release_preflight.py",
        ],
        "result": {
            "public_release_preflight": "pass"
            if "PUBLIC PREFLIGHT PASSED" in preflight_output
            else "unknown",
        },
        "notes": (
            "Public-safe clean-room validation record. Does not include secrets, "
            "provider URLs, sandbox IDs, account identifiers, local paths, or raw private text."
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    args = parse_args()
    repo = ensure_ready(args)
    payload, archive_sha, dataset_sha = build_archive(exclude_path=canonical_exclude_path(args.json_output))

    print("MAMMR 0G Sandbox preflight")
    print(f"mode={'execute' if args.execute else 'dry-run'}")
    print(f"sandbox_repo={'available' if repo.exists() else 'missing'}")
    print(f"api={'set' if args.api else 'missing'}")
    print(f"snapshot={'set' if args.snapshot else 'missing'}")
    print(f"user_key={'set' if os.environ.get('USER_KEY') else 'missing'}")
    print(f"dataset_sha256={dataset_sha}")

    created = False
    sandbox_id: str | None = None
    python_version = "unknown"
    preflight_output = ""

    try:
        sandbox_id = create_sandbox(repo, args) or "<created-sandbox-id>"
        created = True
        wait_for_started(repo, args, sandbox_id)
        upload_archive(repo, args, sandbox_id, payload, archive_sha)
        python_version, preflight_output = run_remote_preflight(repo, args, sandbox_id)
        if args.execute and "PUBLIC PREFLIGHT PASSED" not in preflight_output:
            raise RuntimeError("remote public preflight did not pass")
    finally:
        if created and sandbox_id and args.execute and not args.keep:
            delete_sandbox(repo, args, sandbox_id)

    if args.json_output and args.execute:
        write_run_record(
            args.json_output,
            dataset_sha=dataset_sha,
            archive_sha=archive_sha,
            python_version=python_version,
            preflight_output=preflight_output,
        )
        print(f"wrote {args.json_output}")

    print("sandbox-preflight-plan-ok" if not args.execute else "sandbox-preflight-ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
