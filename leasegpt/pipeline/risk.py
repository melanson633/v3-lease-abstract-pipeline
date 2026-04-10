"""Implementation of the lease-risk skill."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from leasegpt.constants import RISK_MATERIALITY_ANNUAL_RENT
from leasegpt.utils.dates import parse_date, parse_datetime_to_date, today_utc
from leasegpt.utils.json_paths import ancestor_paths


@dataclass(slots=True)
class RiskResult:
    register_markdown: str
    manifest: dict[str, Any]


def _trace_map(bundle: dict[str, Any]) -> dict[str, Any]:
    traceability = bundle.get("traceability") or {}
    metadata = traceability.get("extractedFieldsMetadata") or {}
    return metadata if isinstance(metadata, dict) else {}


def _trace_for(path: str, trace_map: dict[str, Any]) -> dict[str, Any]:
    for candidate in ancestor_paths(path):
        info = trace_map.get(candidate)
        if isinstance(info, dict):
            return info
    return {}


def _current_annual_rent(lease_state: dict[str, Any], ref_date: date) -> float | None:
    schedule = (((lease_state.get("Financials") or {}).get("BaseRent") or {}).get("Schedule")) or []
    if not isinstance(schedule, list):
        return None
    nearest_future = None
    for row in schedule:
        if not isinstance(row, dict):
            continue
        start = parse_date(row.get("startDate"))
        end = parse_date(row.get("endDate"))
        annual = row.get("annualAmount")
        if annual is None:
            continue
        if start and end and start <= ref_date <= end:
            return float(annual)
        if start and start > ref_date and nearest_future is None:
            nearest_future = float(annual)
    if nearest_future is not None:
        return nearest_future
    for row in reversed(schedule):
        if isinstance(row, dict) and row.get("annualAmount") is not None:
            return float(row["annualAmount"])
    return None


def _remaining_years(lease_state: dict[str, Any], ref_date: date) -> float | None:
    expiration = parse_date(((lease_state.get("Dates") or {}).get("ExpirationDate")))
    if not expiration:
        return None
    return max((expiration - ref_date).days / 365.25, 0.0)


def _append_finding(
    findings: list[dict[str, Any]],
    *,
    risk_code: str,
    severity: str,
    finding: str,
    evidence_paths: list[str],
    citations: list[str],
    exposure_formula: str | None,
    estimated_exposure: float | None,
    exposure_status: str = "computed",
    recommended_follow_up: str,
) -> None:
    findings.append(
        {
            "risk_code": risk_code,
            "severity": severity,
            "finding": finding,
            "evidence_paths": evidence_paths,
            "citations": citations or ["citation_unavailable"],
            "exposure_formula": exposure_formula,
            "estimated_exposure": estimated_exposure,
            "exposure_status": exposure_status,
            "recommended_follow_up": recommended_follow_up,
        }
    )


def build_risk_register(
    bundle: dict[str, Any],
    calendar_manifest: dict[str, Any] | None = None,
) -> RiskResult:
    lease_state = bundle.get("lease_state") or {}
    trace_map = _trace_map(bundle)
    tenant = (((lease_state.get("Parties") or {}).get("Tenant") or {}).get("Name")) or "Unknown Tenant"
    reference_date = parse_datetime_to_date(
        (((lease_state.get("Metadata") or {}).get("Extraction") or {}).get("GenerationTimestamp"))
    ) or today_utc()

    annual_rent = _current_annual_rent(lease_state, reference_date)
    remaining_years = _remaining_years(lease_state, reference_date)
    findings: list[dict[str, Any]] = []
    warnings: list[str] = []

    options = lease_state.get("Options") or {}
    financials = lease_state.get("Financials") or {}
    clauses = lease_state.get("Clauses") or {}

    # 1) Co-tenancy trigger
    co_tenancy = options.get("CoTenancy")
    if isinstance(co_tenancy, dict) and any(co_tenancy.get(k) for k in ("Requirement", "Remedies")):
        _append_finding(
            findings,
            risk_code="RISK_CO_TENANCY_TRIGGER",
            severity="High",
            finding="Co-tenancy provision present; tenant remedies may reduce or suspend rent.",
            evidence_paths=["Options.CoTenancy"],
            citations=[_trace_for("Options.CoTenancy", trace_map).get("citation") or "citation_unavailable"],
            exposure_formula="annual_rent * trigger_discount_pct",
            estimated_exposure=None,
            exposure_status="input_missing",
            recommended_follow_up="Confirm trigger thresholds and model downside rent scenarios.",
        )

    # 2) Go-dark right
    go_dark = options.get("GoDarkRights")
    if isinstance(go_dark, str) and go_dark.strip():
        exposure = annual_rent * remaining_years if annual_rent and remaining_years is not None else None
        _append_finding(
            findings,
            risk_code="RISK_GO_DARK",
            severity="High",
            finding="Go-dark rights detected; occupancy and traffic may deteriorate without lease termination.",
            evidence_paths=["Options.GoDarkRights"],
            citations=[_trace_for("Options.GoDarkRights", trace_map).get("citation") or "citation_unavailable"],
            exposure_formula="remaining_rent_years * annual_rent",
            estimated_exposure=round(exposure, 2) if exposure is not None else None,
            exposure_status="computed" if exposure is not None else "input_missing",
            recommended_follow_up="Review continuous-operation obligations and landlord remedies.",
        )

    # 3) Kick-out / termination right
    term_opt = options.get("TerminationOptions")
    if isinstance(term_opt, dict) and term_opt.get("EarlyTerminationRight"):
        _append_finding(
            findings,
            risk_code="RISK_KICK_OUT",
            severity="High",
            finding="Early termination right detected; cashflow continuity risk exists.",
            evidence_paths=["Options.TerminationOptions"],
            citations=[_trace_for("Options.TerminationOptions", trace_map).get("citation") or "citation_unavailable"],
            exposure_formula="unamortized_TI + leasing_downtime_cost",
            estimated_exposure=None,
            exposure_status="input_missing",
            recommended_follow_up="Quantify unamortized TI and downtime assumptions for downside case.",
        )

    # 4) Exclusive use conflicts
    exclusive_use = options.get("ExclusiveUseRights")
    if isinstance(exclusive_use, str) and "conflict" in exclusive_use.lower():
        _append_finding(
            findings,
            risk_code="RISK_EXCLUSIVE_USE_CONFLICT",
            severity="Medium",
            finding="Exclusive-use language references potential conflicts.",
            evidence_paths=["Options.ExclusiveUseRights"],
            citations=[_trace_for("Options.ExclusiveUseRights", trace_map).get("citation") or "citation_unavailable"],
            exposure_formula=None,
            estimated_exposure=None,
            exposure_status="notional_only",
            recommended_follow_up="Validate competing-use restrictions against tenant mix and leasing plans.",
        )

    # 5) Uncapped CAM under net structure
    recovery_type = ((financials.get("AdditionalRent") or {}).get("RecoveryType")) or ""
    cam_cap = ((financials.get("AdditionalRent") or {}).get("CAMCap")) or None
    if isinstance(recovery_type, str) and any(k in recovery_type.lower() for k in ("net", "nnn", "pass")) and not cam_cap:
        _append_finding(
            findings,
            risk_code="RISK_UNCAPPED_CAM",
            severity="Medium",
            finding="Net expense recovery structure appears uncapped.",
            evidence_paths=["Financials.AdditionalRent.RecoveryType", "Financials.AdditionalRent.CAMCap"],
            citations=[
                _trace_for("Financials.AdditionalRent.RecoveryType", trace_map).get("citation")
                or "citation_unavailable"
            ],
            exposure_formula=None,
            estimated_exposure=None,
            exposure_status="open_ended",
            recommended_follow_up="Confirm cap exclusions and estimate operating expense escalation sensitivity.",
        )

    # 6) Structural obligations on tenant
    tenant_maint = ((clauses.get("Maintenance") or {}).get("TenantResponsibilities")) or ""
    if isinstance(tenant_maint, str) and any(
        token in tenant_maint.lower() for token in ("roof", "foundation", "load-bearing", "structural")
    ):
        _append_finding(
            findings,
            risk_code="RISK_STRUCTURAL_TENANT_MAINT",
            severity="High",
            finding="Tenant maintenance language includes potential structural obligations.",
            evidence_paths=["Clauses.Maintenance.TenantResponsibilities"],
            citations=[_trace_for("Clauses.Maintenance.TenantResponsibilities", trace_map).get("citation") or "citation_unavailable"],
            exposure_formula=None,
            estimated_exposure=None,
            exposure_status="input_missing",
            recommended_follow_up="Confirm carve-outs, cap mechanics, and landlord step-in rights.",
        )

    # 7) Guaranty burn-off timing
    guaranty = clauses.get("Guaranty")
    if isinstance(guaranty, dict) and guaranty.get("Guarantor"):
        burnoff = parse_date(guaranty.get("BurnOff"))
        expiration = parse_date(((lease_state.get("Dates") or {}).get("ExpirationDate")))
        if burnoff is None or (expiration and burnoff > expiration):
            monthly = annual_rent / 12 if annual_rent else None
            months = ((burnoff.year - reference_date.year) * 12 + (burnoff.month - reference_date.month)) if burnoff else None
            exposure = (months * monthly) if months and monthly else None
            _append_finding(
                findings,
                risk_code="RISK_GUARANTY_BURNOFF",
                severity="Medium",
                finding="Guaranty burn-off timing is unclear or extends beyond expected term.",
                evidence_paths=["Clauses.Guaranty.BurnOff"],
                citations=[_trace_for("Clauses.Guaranty.BurnOff", trace_map).get("citation") or "citation_unavailable"],
                exposure_formula="remaining_guaranty_months * monthly_base_rent",
                estimated_exposure=round(exposure, 2) if exposure is not None else None,
                exposure_status="computed" if exposure is not None else "input_missing",
                recommended_follow_up="Clarify burn-off trigger and surviving obligations.",
            )

    # 8) Missing guaranty on high-dollar lease
    guarantor = ((lease_state.get("Parties") or {}).get("Guarantor"))
    if annual_rent and annual_rent > RISK_MATERIALITY_ANNUAL_RENT and not guarantor:
        _append_finding(
            findings,
            risk_code="RISK_NO_GUARANTY_HIGH_DOLLAR",
            severity="Medium",
            finding=f"Annual base rent exceeds ${RISK_MATERIALITY_ANNUAL_RENT:,.0f} with no guarantor captured.",
            evidence_paths=["Parties.Guarantor", "Financials.BaseRent.Schedule"],
            citations=[
                _trace_for("Parties.Guarantor", trace_map).get("citation") or "citation_unavailable",
                _trace_for("Financials.BaseRent.Schedule", trace_map).get("citation") or "citation_unavailable",
            ],
            exposure_formula="annual_rent",
            estimated_exposure=round(float(annual_rent), 2),
            recommended_follow_up="Confirm credit support package (guaranty, LOC, or additional deposit).",
        )

    # 9) Past-due notice deadlines from calendar
    if calendar_manifest and isinstance(calendar_manifest, dict):
        for event in calendar_manifest.get("events") or []:
            if not isinstance(event, dict):
                continue
            if "notice" in str(event.get("event_type", "")).lower() and event.get("status") == "past":
                _append_finding(
                    findings,
                    risk_code="RISK_PAST_DUE_NOTICE",
                    severity="Critical",
                    finding=f"Past-due notice deadline detected: {event.get('summary')}.",
                    evidence_paths=[event.get("source_field_path") or "unknown"],
                    citations=[event.get("citation") or "citation_unavailable"],
                    exposure_formula=None,
                    estimated_exposure=None,
                    exposure_status="input_missing",
                    recommended_follow_up="Confirm whether notice was timely delivered and document cure/waiver path.",
                )
    elif calendar_manifest is None:
        warnings.append("skipped_no_calendar_cross_reference")

    # 10) Low-confidence critical fields
    critical_paths = [
        "Dates.CommencementDate",
        "Dates.ExpirationDate",
        "Premises.RSF",
        "Financials.BaseRent.Schedule",
    ]
    for path in critical_paths:
        info = _trace_for(path, trace_map)
        conf = info.get("confidence")
        if isinstance(conf, (int, float)) and conf < 0.7:
            _append_finding(
                findings,
                risk_code="RISK_LOW_CONFIDENCE_CRITICAL",
                severity="High" if "Dates" in path or "BaseRent" in path else "Medium",
                finding=f"Low confidence critical field: {path} ({conf}).",
                evidence_paths=[path],
                citations=[info.get("citation") or "citation_unavailable"],
                exposure_formula=None,
                estimated_exposure=None,
                exposure_status="input_missing",
                recommended_follow_up="Re-verify source language and update traceability confidence.",
            )

    # 11) Financial validation warnings
    for path, info in trace_map.items():
        if not isinstance(info, dict):
            continue
        if not path.startswith("Financials."):
            continue
        status = info.get("validation_status")
        if status in {"flagged", "uncertain"}:
            _append_finding(
                findings,
                risk_code="RISK_FINANCIAL_VALIDATION_WARNING",
                severity="High" if "BaseRent" in path else "Medium",
                finding=f"Financial field has validation status '{status}': {path}.",
                evidence_paths=[path],
                citations=[info.get("citation") or "citation_unavailable"],
                exposure_formula=None,
                estimated_exposure=None,
                exposure_status="input_missing",
                recommended_follow_up="Resolve validation warning before underwriting use.",
            )

    if findings:
        markdown_lines = [
            "| Risk Code | Severity | Finding | Evidence | Exposure (Rule-Based) | Follow-up |",
            "|---|---|---|---|---|---|",
        ]
        for finding in findings:
            exposure = (
                f"{finding['exposure_formula']} = ${finding['estimated_exposure']:,.2f}"
                if isinstance(finding.get("estimated_exposure"), (int, float))
                else finding.get("exposure_formula") or "n/a"
            )
            markdown_lines.append(
                f"| {finding['risk_code']} | {finding['severity']} | {finding['finding']} | "
                f"{'; '.join(finding['evidence_paths'])} | {exposure} | {finding['recommended_follow_up']} |"
            )
        markdown = "\n".join(markdown_lines) + "\n"
    else:
        markdown = "No rule-triggered risks detected for the provided lease_state.\n"

    manifest = {
        "tenant": tenant,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "finding_count": len(findings),
        "findings": findings,
        "warnings": warnings,
        "legal_disclaimer": "Operational risk summary only; not legal advice.",
    }
    return RiskResult(register_markdown=markdown, manifest=manifest)
