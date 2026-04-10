"""Path and repository helpers."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def skills_root() -> Path:
    root = repo_root()
    agents_root = root / ".agents" / "skills"
    if agents_root.exists():
        return agents_root
    claude_root = root / ".claude" / "skills"
    return claude_root


def schema_path() -> Path:
    return skills_root() / "lease-extract" / "references" / "v4_unified_schema.json"


def shared_constants_path() -> Path:
    return repo_root() / "config" / "shared_constants.md"


def fixture_path(name: str) -> Path:
    return skills_root() / "lease-eval" / "fixtures" / name / "lease_state.json"
