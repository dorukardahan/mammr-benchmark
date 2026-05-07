#!/usr/bin/env python3
"""Build public-safe synthetic distractors for full-corpus retrieval eval."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "synthetic_distractors_public.json"


TOPICS = [
    ("frontend", "The settings panel now keeps the save button disabled until all required fields are valid."),
    ("frontend", "The dashboard chart uses weekly aggregation and hides empty series by default."),
    ("frontend", "The onboarding modal should not reopen after the user completes the first checklist."),
    ("frontend", "The theme switcher stores its state in local browser storage and does not call the API."),
    ("backend", "The billing worker retries failed invoices three times before moving them to manual review."),
    ("backend", "The notification queue uses exponential backoff when the email provider returns a temporary error."),
    ("backend", "The webhook receiver validates the event signature before writing the payload to the queue."),
    ("backend", "The export job writes CSV files to object storage and sends a download link when complete."),
    ("database", "The customer table migration adds a nullable timezone column with no default value."),
    ("database", "The report cache should be invalidated when a saved filter changes."),
    ("database", "The analytics database keeps raw event rows for thirty days before compaction."),
    ("database", "The search index rebuild is safe to run while read traffic continues."),
    ("ops", "The staging deploy uses a separate domain and must not share cookies with production."),
    ("ops", "The health check endpoint returns build version, uptime, and dependency status."),
    ("ops", "The release script tags the container image before updating the deployment manifest."),
    ("ops", "The incident channel should include timeline updates, owner, impact, and next action."),
    ("ai", "The summarizer model should preserve user decisions and remove repeated small talk."),
    ("ai", "The classifier falls back to the default route when confidence is below the threshold."),
    ("ai", "The prompt evaluator checks instruction leakage, missing context, and malformed JSON."),
    ("ai", "The image captioning job stores alt text separately from the original image metadata."),
    ("mobile", "The iOS build failed because the provisioning profile did not include the new bundle id."),
    ("mobile", "The Android notification permission prompt appears only after the user enables alerts."),
    ("mobile", "The offline sync screen shows pending edits and lets the user retry failed uploads."),
    ("mobile", "The tablet layout keeps the sidebar visible while collapsing secondary filters."),
]


def main() -> int:
    rows = []
    variants = [
        "Context note",
        "Follow-up reminder",
        "Archived decision",
        "Operational aside",
    ]
    index = 0
    for topic, text in TOPICS:
        for variant in variants:
            rows.append(
                {
                    "id": f"mammr-distractor-{index:04d}",
                    "topic": topic,
                    "text": f"{variant}: {text}",
                }
            )
            index += 1

    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {OUT}")
    print(f"distractors={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
