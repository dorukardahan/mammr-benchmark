#!/usr/bin/env python3
"""Scan the public candidate repo for common private-data mistakes."""

from __future__ import annotations

import ipaddress
import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv"}
SKIP_FILES = {
    ".gitignore",
    ".mammr-private-denylist.txt",
    "scripts/audit_dataset.py",
    "scripts/check_public_safety.py",
}

TEXT_PATTERNS = {
    "private_home_path": re.compile(r"/Users/[^/\s]+|/home/[^/\s]+|/root/"),
    "private_service_path": re.compile(r"/(?:srv|opt|var/lib)/[A-Za-z0-9._/-]+"),
    "email_address": re.compile(r"\b[A-Z0-9._%+-]+@(?!example\.com\b)[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "ssh_public_key_material": re.compile(r"\bssh-(?:rsa|ed25519)\s+[A-Za-z0-9+/=]{16,}|\bauthorized_keys\b"),
    "env_file_reference": re.compile(r"(^|[^A-Za-z0-9_])\.env([^A-Za-z0-9_]|$)"),
    "private_chat_tone_marker": re.compile(r"\b(my birthday|my cat|my house|my apartment)\b", re.IGNORECASE),
    "internal_review_artifact": re.compile(
        r"internal[- ]only"
        r"|private[- ]review"
        r"|draft[- ]approval"
        r"|unpublished[- ]notes",
        re.IGNORECASE,
    ),
    "secret_like_token": re.compile(
        r"(sk-or-v1|xox[baprs]-|xapp-|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})",
        re.IGNORECASE,
    ),
    "secret_assignment": re.compile(
        r"(API[_-]?KEY|TOKEN|SECRET|PASSWORD|OPENROUTER_API_KEY)\s*=\s*"
        r"[\"']?(?!YOUR_API_KEY|REPLACE_ME|example|placeholder)[A-Za-z0-9_\-]{16,}",
        re.IGNORECASE,
    ),
}

PUBLIC_TEXT_DATA_FILES = {
    Path("data/mammr_pairs_public.json"),
    Path("data/heldout_mini_public.json"),
    Path("data/independent_review_sample_20260506.json"),
    Path("scripts/build_heldout_dataset.py"),
}

DATASET_SURFACE_PATTERNS = {
    "unsanitized_runtime_name": re.compile(
        r"\b(AgentGateway|AgentMemory|ContentReviewService|SocialReportService|EdgeProxy)\b",
        re.IGNORECASE,
    ),
    "unsanitized_channel_name": re.compile(r"\b(Slack|WhatsApp|Tailscale)\b", re.IGNORECASE),
    "unsanitized_hosting_term": re.compile(r"\bVPS\b", re.IGNORECASE),
    "unsanitized_security_incident": re.compile(r"\bfail2ban\b", re.IGNORECASE),
    "unsanitized_provider_name": re.compile(r"\b(SecondaryLLM|FallbackLLM|fallback-llm|nvidia-nim)\b", re.IGNORECASE),
    "unsanitized_private_result_path": re.compile(r"results/vps/|vector-cache", re.IGNORECASE),
    "unsanitized_personal_device": re.compile(r"\b(Mac \+ iPhone|my phone|my laptop)\b", re.IGNORECASE),
    "unsanitized_private_ops_tone": re.compile(
        r"\b(dünkü sorun|geçen hafta ne yaptık|operator hangi font|internal account identifier|ignoreip|jails?|private overlay network|X-API-Key)\b",
        re.IGNORECASE,
    ),
    "raw_private_runtime_codename": re.compile(
        r"\b(AgentGateway|AgentMemory|ContentReviewService|SocialReportService|EdgeProxy)\b",
        re.IGNORECASE,
    ),
    "raw_admin_access_surface": re.compile(
        r"\b(CPU-only server|SSH lockout|parallel SSH|UMask=0077)\b",
        re.IGNORECASE,
    ),
}


def local_denylist_patterns() -> dict[str, re.Pattern[str]]:
    path = ROOT / ".mammr-private-denylist.txt"
    if not path.exists():
        return {}
    patterns: dict[str, re.Pattern[str]] = {}
    for index, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        value = raw_line.strip()
        if not value or value.startswith("#"):
            continue
        patterns[f"local_private_denylist_{index}"] = re.compile(re.escape(value), re.IGNORECASE)
    return patterns


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


def should_skip(path: Path) -> bool:
    return str(path) in SKIP_FILES or any(part in SKIP_DIRS for part in path.parts)


def scan_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    findings: list[str] = []
    for label, pattern in {**TEXT_PATTERNS, **local_denylist_patterns()}.items():
        if pattern.search(text):
            findings.append(label)

    relative = path.relative_to(ROOT)
    if relative in PUBLIC_TEXT_DATA_FILES:
        for label, pattern in DATASET_SURFACE_PATTERNS.items():
            if pattern.search(text):
                findings.append(label)

    for match in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text):
        if not is_allowed_ip(match):
            findings.append(f"private_ipv4:{match}")
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan the public candidate repo for private-data mistakes.")
    parser.add_argument("--json", action="store_true", help="write a machine-readable scan report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or should_skip(path.relative_to(ROOT)):
            continue
        for finding in scan_file(path):
            findings.append(f"{path.relative_to(ROOT)}: {finding}")

    if args.json:
        print(json.dumps({"status": "failed" if findings else "passed", "findings": findings}, indent=2))
        return 1 if findings else 0

    if findings:
        print("FAILED")
        for finding in findings:
            print(finding)
        return 1

    print("PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
