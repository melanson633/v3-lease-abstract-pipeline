#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS: dict[Path, list[str]] = {
    Path("AGENTS.md"): [
        "## Workflow (Required)",
        "## Required Checks Before Commit",
        "## Escalation & Boundaries",
        "## Commit Conventions",
        "## PR Conventions",
    ],
    Path("ARCHITECTURE.md"): [
        "## Pipeline Boundary",
        "## Module Ownership & Dependency Layering",
        "## Pipeline Stages, Entrypoints, and Invariants",
    ],
    Path("docs/system-of-record/index.md"): [
        "# System of Record Index",
        "Source of Truth",
    ],
    Path("docs/runbooks/failure-triage.md"): [
        "# Failure Triage Runbook",
        "## Decision Flow (Summary)",
    ],
}


def main() -> int:
    errors: list[str] = []
    for rel_path, required_markers in REQUIRED_DOCS.items():
        doc_path = ROOT / rel_path
        if not doc_path.exists():
            errors.append(f"missing required doc: {rel_path}")
            continue
        content = doc_path.read_text(encoding="utf-8")
        for marker in required_markers:
            if marker not in content:
                errors.append(f"missing section marker in {rel_path}: {marker}")

    if errors:
        print("Required docs policy check failed:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1

    print("Required docs policy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
