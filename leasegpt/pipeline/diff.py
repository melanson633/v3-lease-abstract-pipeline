"""Implementation of the lease-diff skill."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from leasegpt.utils.json_paths import get_by_path, try_get_by_path, values_equal


@dataclass(slots=True)
class DiffResult:
    report_markdown: str
    manifest: dict[str, Any]


def _normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return {k: _normalize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_value(v) for v in value]
    return value


def _value_label(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=True)


def _group_for_path(path: str) -> str:
    if path.startswith("Dates."):
        return "Dates"
    match = re.match(r"Financials\.BaseRent\.Schedule\[(\d+)\]", path)
    if match:
        return f"Schedule[{match.group(1)}]"
    if path.startswith("Financials.TIAllowance."):
        return "TI Allowance"
    parts = path.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return parts[0]


def _group_sort_key(group: str) -> tuple[int, str]:
    if group == "Dates":
        return (0, group)
    if group.startswith("Schedule["):
        idx = int(re.search(r"\[(\d+)\]", group).group(1))  # type: ignore[union-attr]
        return (1, f"{idx:05d}")
    if group == "TI Allowance":
        return (2, group)
    return (3, group.lower())


def _flatten_draft(value: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, sub in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else key
            out.update(_flatten_draft(sub, next_prefix))
        return out
    if isinstance(value, list):
        for idx, sub in enumerate(value):
            next_prefix = f"{prefix}[{idx}]"
            out.update(_flatten_draft(sub, next_prefix))
        return out
    out[prefix] = value
    return out


def build_diff(
    bundle: dict[str, Any],
    draft_amendment: dict[str, Any] | None = None,
) -> DiffResult:
    lease_state = bundle.get("lease_state") or {}
    change_log = bundle.get("change_log") or []
    if not isinstance(change_log, list) or not change_log:
        manifest = {
            "schema_version": "4.0.0",
            "change_entry_count": 0,
            "groups": {},
            "field_timelines": {},
            "overwrite_preview": [],
            "warnings": ["no_change_log_entries"],
        }
        return DiffResult(
            report_markdown="No change log entries available (`no_change_log_entries`).\n",
            manifest=manifest,
        )

    timelines: dict[str, dict[str, Any]] = {}
    first_seen_index: dict[str, int] = {}
    for idx, entry in enumerate(change_log):
        if not isinstance(entry, dict):
            continue
        field_path = entry.get("field_path")
        if not isinstance(field_path, str):
            continue
        norm_old = _normalize_value(entry.get("old_value"))
        norm_new = _normalize_value(entry.get("new_value"))
        timeline = timelines.get(field_path)
        if not timeline:
            timeline = {
                "field_path": field_path,
                "origin": norm_old,
                "events": [],
                "progression_docs": [],
            }
            timelines[field_path] = timeline
            first_seen_index[field_path] = idx
        src_doc = entry.get("source_document")
        if isinstance(src_doc, str) and src_doc and src_doc not in timeline["progression_docs"]:
            timeline["progression_docs"].append(src_doc)
        timeline["events"].append(
            {
                "from_value": norm_old,
                "to_value": norm_new,
                "effective_date": entry.get("effective_date"),
                "source_document": src_doc,
                "citation": entry.get("citation"),
                "impact_notes": entry.get("impact_notes"),
            }
        )

    groups: dict[str, list[str]] = {}
    for path in timelines:
        group = _group_for_path(path)
        groups.setdefault(group, []).append(path)
    for paths in groups.values():
        paths.sort(key=lambda p: first_seen_index.get(p, 0))

    ordered_groups = sorted(groups.keys(), key=_group_sort_key)

    markdown_lines = [
        "# Lease Diff Report",
        "",
    ]
    for group in ordered_groups:
        markdown_lines.extend(
            [
                f"## {group}",
                "",
                "| Field Path | Progression | Original | Current | Amendment Events | Citation Pair(s) | Notes |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for path in groups[group]:
            timeline = timelines[path]
            progression = " -> ".join(timeline["progression_docs"]) or "unspecified"
            ok, current_value = try_get_by_path(lease_state, path)
            current_label = _value_label(_normalize_value(current_value)) if ok else "<path-missing>"
            events_label = "; ".join(
                f"{e.get('source_document') or '?'}@{e.get('effective_date') or '?'}: {_value_label(e.get('from_value'))} -> {_value_label(e.get('to_value'))}"
                for e in timeline["events"]
            )
            citation_pairs = "; ".join(
                f"{e.get('source_document') or '?'}: {e.get('citation') or 'citation_unavailable'}"
                for e in timeline["events"]
            )
            notes = "; ".join(
                str(e.get("impact_notes")) for e in timeline["events"] if e.get("impact_notes")
            )
            markdown_lines.append(
                f"| {path} | {progression} | {_value_label(timeline['origin'])} | {current_label} | {events_label} | {citation_pairs} | {notes or '-'} |"
            )
        markdown_lines.append("")

    overwrite_preview = []
    if draft_amendment is not None:
        flat_draft = _flatten_draft(draft_amendment)
        for path, draft_value in flat_draft.items():
            ok, current_value = try_get_by_path(lease_state, path)
            if not ok:
                comparison_reason = "current_missing"
                would_overwrite = True
            elif type(current_value) is not type(draft_value):
                comparison_reason = "type_change"
                would_overwrite = True
            elif values_equal(_normalize_value(current_value), _normalize_value(draft_value)):
                comparison_reason = "equal_after_normalization"
                would_overwrite = False
            else:
                comparison_reason = "value_change"
                would_overwrite = True
            overwrite_preview.append(
                {
                    "field_path": path,
                    "current_value": current_value if ok else None,
                    "draft_value": draft_value,
                    "would_overwrite": would_overwrite,
                    "comparison_reason": comparison_reason,
                }
            )

    warnings = []
    for path, timeline in timelines.items():
        ok, current_value = try_get_by_path(lease_state, path)
        if not ok:
            warnings.append({"issue": "path_resolution_warning", "field_path": path})
            continue
        latest = timeline["events"][-1]["to_value"] if timeline["events"] else None
        if not values_equal(_normalize_value(latest), _normalize_value(current_value)):
            warnings.append(
                {
                    "issue": "current_state_mismatch",
                    "field_path": path,
                    "latest_timeline_value": latest,
                    "lease_state_value": current_value,
                }
            )

    manifest = {
        "schema_version": "4.0.0",
        "change_entry_count": len(change_log),
        "groups": {group: groups[group] for group in ordered_groups},
        "field_timelines": timelines,
        "overwrite_preview": overwrite_preview,
        "warnings": warnings,
    }
    return DiffResult(report_markdown="\n".join(markdown_lines).strip() + "\n", manifest=manifest)
