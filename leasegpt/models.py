"""Shared data models used by LeaseGPT modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class LeaseDocument:
    """A normalized input lease document."""

    path: Path
    doc_code: str
    order_index: int
    text: str
    page_count: int | None = None
    truncated: bool = False
    truncation_note: str | None = None


@dataclass(slots=True)
class ExtractionBundle:
    """Canonical extraction output bundle."""

    lease_state: dict[str, Any]
    change_log: list[dict[str, Any]]
    pending_fields: list[dict[str, Any]]
    traceability: dict[str, Any]
    tenant_candidates: list[str] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EvalResult:
    """Evaluation output payload."""

    conformance_report: dict[str, Any]
    summary_markdown: str
    diff_report: dict[str, Any] | None = None
