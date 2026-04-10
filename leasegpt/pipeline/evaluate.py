"""Implementation of the lease-eval skill."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from leasegpt.constants import CITATION_REGEX, SCHEMA_VERSION, VALIDATION_STATUSES
from leasegpt.models import EvalResult
from leasegpt.pipeline.schema_tools import (
    load_schema,
    path_resolves_in_schema,
    schema_paths,
    validate_lease_state,
)
from leasegpt.utils.dates import parse_date
from leasegpt.utils.io import coerce_bundle_shape, load_json
from leasegpt.utils.json_paths import (
    ancestor_paths,
    flatten_leaves,
    get_by_path,
    is_populated_leaf,
    normalize_array_path,
    try_get_by_path,
    values_equal,
)
from leasegpt.utils.paths import skills_root

INDEX_SEGMENT_RE = re.compile(r"\[\d+\]")


def _is_iso_date(value: str) -> bool:
    return parse_date(value) is not None


def _strip_indices(path: str) -> str:
    return INDEX_SEGMENT_RE.sub("", path)


def _path_candidates_for_traceability(path: str) -> list[str]:
    candidates = []
    for ancestor in ancestor_paths(path):
        candidates.append(ancestor)
        candidates.append(normalize_array_path(ancestor))
        candidates.append(_strip_indices(ancestor))
    deduped = []
    seen = set()
    for item in candidates:
        if item and item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def _extract_issue_codes(issues: list[dict[str, Any]]) -> set[str]:
    return {issue.get("issue", issue.get("error", "")) for issue in issues}


def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value


def _flatten_for_diff(value: Any) -> dict[str, Any]:
    leaves = flatten_leaves(value)
    return {path: _normalize_scalar(v) for path, v in leaves.items()}


def _load_fixture_lease_state(fixture_name: str) -> dict[str, Any]:
    fixture = (
        skills_root()
        / "lease-eval"
        / "fixtures"
        / fixture_name
        / "lease_state.json"
    )
    if not fixture.exists():
        available = [
            p.name for p in (skills_root() / "lease-eval" / "fixtures").iterdir() if p.is_dir()
        ]
        raise FileNotFoundError(
            f"Fixture '{fixture_name}' not found at {fixture}. Available fixtures: {', '.join(sorted(available))}."
        )
    payload = coerce_bundle_shape(load_json(fixture))
    return payload["lease_state"]


def evaluate_bundle(
    candidate_payload: dict[str, Any],
    scope: str = "full",
    golden_fixture_name: str | None = None,
    schema_file: Path | None = None,
) -> EvalResult:
    if scope not in {"schema_only", "provenance_only", "full"}:
        raise ValueError("scope must be one of: schema_only, provenance_only, full")

    bundle = coerce_bundle_shape(candidate_payload)
    lease_state = bundle["lease_state"]
    change_log = bundle["change_log"]
    pending_fields = bundle["pending_fields"]
    traceability = bundle["traceability"] or {}
    trace_map = traceability.get("extractedFieldsMetadata") or {}
    if not isinstance(trace_map, dict):
        trace_map = {}

    schema = load_schema(schema_file)
    schema_path_set = schema_paths(schema)

    schema_violations = validate_lease_state(lease_state, schema)
    schema_pass = len(schema_violations) == 0

    traceability_issues: list[dict[str, Any]] = []
    change_log_issues: list[dict[str, Any]] = []
    pending_issues: list[dict[str, Any]] = []

    populated = 0
    covered = 0

    if scope != "schema_only":
        leaves = flatten_leaves(lease_state)
        for path, value in leaves.items():
            if not is_populated_leaf(value):
                continue
            populated += 1

            metadata = None
            matched_path = None
            for candidate_path in _path_candidates_for_traceability(path):
                if candidate_path in trace_map:
                    metadata = trace_map[candidate_path]
                    matched_path = candidate_path
                    break

            if not isinstance(metadata, dict):
                traceability_issues.append(
                    {"issue": "missing_traceability", "path": path}
                )
                continue
            covered += 1

            citation = metadata.get("citation")
            if not (path.startswith("Metadata.") and citation in (None, "")):
                if not isinstance(citation, str) or not CITATION_REGEX.match(citation):
                    traceability_issues.append(
                        {
                            "issue": "malformed_citation",
                            "path": path,
                            "traceability_path": matched_path,
                            "citation": citation,
                        }
                    )

            confidence = metadata.get("confidence")
            if not isinstance(confidence, (int, float)) or not (0.0 <= float(confidence) <= 1.0):
                traceability_issues.append(
                    {
                        "issue": "confidence_out_of_range",
                        "path": path,
                        "traceability_path": matched_path,
                        "confidence": confidence,
                    }
                )

            status = metadata.get("validation_status")
            if status not in VALIDATION_STATUSES:
                traceability_issues.append(
                    {
                        "issue": "status_invalid",
                        "path": path,
                        "traceability_path": matched_path,
                        "validation_status": status,
                    }
                )

        # change log coherence
        if isinstance(change_log, list):
            last_by_path: dict[str, dict[str, Any]] = {}
            for entry in change_log:
                if not isinstance(entry, dict):
                    change_log_issues.append({"issue": "malformed_change_entry", "entry": entry})
                    continue
                path = entry.get("field_path")
                if not isinstance(path, str) or not path:
                    change_log_issues.append({"issue": "missing_field_path", "entry": entry})
                    continue
                if not path_resolves_in_schema(path, schema_path_set):
                    change_log_issues.append(
                        {"issue": "path_not_in_schema", "field_path": path}
                    )
                eff = entry.get("effective_date")
                if eff is not None and (not isinstance(eff, str) or not _is_iso_date(eff)):
                    change_log_issues.append(
                        {"issue": "malformed_effective_date", "field_path": path, "effective_date": eff}
                    )
                src = entry.get("source_document")
                cit = entry.get("citation")
                if bool(src) != bool(cit):
                    change_log_issues.append(
                        {"issue": "incomplete_citation_pair", "field_path": path}
                    )
                last_by_path[path] = entry

            for path, last_entry in last_by_path.items():
                ok, current_value = try_get_by_path(lease_state, path)
                if not ok:
                    change_log_issues.append(
                        {
                            "issue": "current_state_mismatch",
                            "field_path": path,
                            "expected": last_entry.get("new_value"),
                            "actual": "<path-missing>",
                        }
                    )
                    continue
                if not values_equal(last_entry.get("new_value"), current_value):
                    change_log_issues.append(
                        {
                            "issue": "current_state_mismatch",
                            "field_path": path,
                            "expected": last_entry.get("new_value"),
                            "actual": current_value,
                        }
                    )

        # pending sanity
        if isinstance(pending_fields, list):
            for entry in pending_fields:
                if not isinstance(entry, dict):
                    pending_issues.append({"issue": "malformed_pending_entry", "entry": entry})
                    continue
                path = entry.get("path")
                if not isinstance(path, str) or not path:
                    pending_issues.append({"issue": "missing_pending_path", "entry": entry})
                    continue
                if not path_resolves_in_schema(path, schema_path_set):
                    pending_issues.append({"issue": "path_not_in_schema", "path": path})
                    continue
                ok, current_value = try_get_by_path(lease_state, path)
                if ok and is_populated_leaf(current_value):
                    pending_issues.append(
                        {
                            "issue": "pending_but_populated",
                            "path": path,
                            "actual": current_value,
                        }
                    )

    golden_diff = None
    if golden_fixture_name:
        golden_lease_state = _load_fixture_lease_state(golden_fixture_name)
        cand_flat = _flatten_for_diff(lease_state)
        golden_flat = _flatten_for_diff(golden_lease_state)
        mismatches = []
        candidate_only = []
        golden_only = []
        match_count = 0

        all_paths = sorted(set(cand_flat.keys()) | set(golden_flat.keys()))
        for path in all_paths:
            in_candidate = path in cand_flat
            in_golden = path in golden_flat
            if in_candidate and in_golden:
                if values_equal(cand_flat[path], golden_flat[path]):
                    match_count += 1
                else:
                    mismatches.append(
                        {
                            "path": path,
                            "candidate": cand_flat[path],
                            "golden": golden_flat[path],
                            "kind": "value_mismatch",
                        }
                    )
            elif in_candidate:
                candidate_only.append({"path": path, "candidate": cand_flat[path], "kind": "candidate_only"})
            else:
                golden_only.append({"path": path, "golden": golden_flat[path], "kind": "golden_only"})

        golden_diff = {
            "fixture": golden_fixture_name,
            "match_count": match_count,
            "value_mismatch": mismatches,
            "candidate_only": candidate_only,
            "golden_only": golden_only,
        }

    issue_count_non_schema = (
        len(traceability_issues) + len(change_log_issues) + len(pending_issues)
    )
    if (
        golden_diff
        and (golden_diff["value_mismatch"] or golden_diff["candidate_only"] or golden_diff["golden_only"])
    ):
        issue_count_non_schema += 1

    verdict = "PASS"
    if not schema_pass or "current_state_mismatch" in _extract_issue_codes(change_log_issues):
        verdict = "FAIL"
    elif issue_count_non_schema > 0:
        verdict = "WARN"

    coverage_pct = round((covered / populated) if populated else 1.0, 4)
    conformance_report = {
        "schema_version": SCHEMA_VERSION,
        "candidate_summary": {
            "tenant_name": (((lease_state.get("Parties") or {}).get("Tenant") or {}).get("Name")),
            "populated_fields": populated,
            "covered_fields": covered,
            "coverage_pct": coverage_pct,
        },
        "checks": {
            "schema_conformance": {"pass": schema_pass, "violations": schema_violations},
            "citation_and_traceability": {
                "pass": len(traceability_issues) == 0,
                "issues": traceability_issues,
            },
            "change_log_coherence": {
                "pass": len(change_log_issues) == 0,
                "issues": change_log_issues,
            },
            "pending_fields_sanity": {"pass": len(pending_issues) == 0, "issues": pending_issues},
        },
        "golden_diff": golden_diff,
        "verdict": verdict,
    }

    issue_lines: list[str] = []
    for violation in schema_violations[:5]:
        issue_lines.append(f"- schema: {violation['path']} ({violation['error']})")
    for issue in traceability_issues[:5 - len(issue_lines)]:
        issue_lines.append(f"- traceability: {issue.get('path')} ({issue.get('issue')})")
    for issue in change_log_issues[:5 - len(issue_lines)]:
        issue_lines.append(f"- change_log: {issue.get('field_path')} ({issue.get('issue')})")
    for issue in pending_issues[:5 - len(issue_lines)]:
        issue_lines.append(f"- pending: {issue.get('path')} ({issue.get('issue')})")
    if not issue_lines:
        issue_lines.append("- none")

    if verdict == "FAIL":
        fix_first = "Fix schema and/or change-log current-state mismatches first."
    elif verdict == "WARN":
        fix_first = "Fix traceability coverage and citation issues first."
    else:
        fix_first = "No fixes required. Candidate is conformant."

    summary = "\n".join(
        [
            f"Verdict: **{verdict}**",
            "",
            "Top issues:",
            *issue_lines,
            "",
            f"Fix first: {fix_first}",
        ]
    )

    return EvalResult(
        conformance_report=conformance_report,
        summary_markdown=summary,
        diff_report=golden_diff,
    )
