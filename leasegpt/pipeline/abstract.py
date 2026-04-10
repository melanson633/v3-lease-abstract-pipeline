"""Implementation of the lease-abstract skill."""

from __future__ import annotations

from datetime import date
from typing import Any

from leasegpt.utils.dates import fmt_mmddyyyy, parse_datetime_to_date, today_utc
from leasegpt.utils.json_paths import ancestor_paths


def _trace_map(bundle: dict[str, Any]) -> dict[str, Any]:
    traceability = bundle.get("traceability") or {}
    metadata = traceability.get("extractedFieldsMetadata") or {}
    return metadata if isinstance(metadata, dict) else {}


def _citation_for_path(path: str, traceability_map: dict[str, Any]) -> str:
    for candidate in ancestor_paths(path):
        payload = traceability_map.get(candidate)
        if isinstance(payload, dict):
            citation = payload.get("citation")
            if isinstance(citation, str) and citation.strip():
                return citation
    return "citation_unavailable"


def _value_with_citation(
    value: str | int | float | None, citation: str, formatter: str | None = None
) -> tuple[str, str]:
    if value is None:
        return "Not specified", citation
    if formatter == "date":
        return fmt_mmddyyyy(str(value)), citation
    if formatter == "currency":
        return f"${float(value):,.2f}", citation
    if formatter == "percent":
        return f"{float(value) * 100:.2f}%", citation
    if isinstance(value, float):
        return f"{value:,.2f}", citation
    return str(value), citation


def _current_rent_step(lease_state: dict[str, Any], ref_date: date) -> dict[str, Any] | None:
    schedule = (((lease_state.get("Financials") or {}).get("BaseRent") or {}).get("Schedule")) or []
    if not isinstance(schedule, list) or not schedule:
        return None

    # First choose period spanning the reference date, then nearest future, else last.
    candidate = None
    nearest_future = None
    for row in schedule:
        if not isinstance(row, dict):
            continue
        start = row.get("startDate")
        end = row.get("endDate")
        if isinstance(start, str) and isinstance(end, str):
            try:
                start_d = date.fromisoformat(start)
                end_d = date.fromisoformat(end)
                if start_d <= ref_date <= end_d:
                    return row
                if start_d > ref_date and nearest_future is None:
                    nearest_future = row
            except ValueError:
                pass
        candidate = row
    return nearest_future or candidate


def _major_change_lines(change_log: list[dict[str, Any]]) -> list[str]:
    major = []
    for entry in change_log:
        path = str(entry.get("field_path", ""))
        if any(
            token in path
            for token in ("BaseRent", "ExpirationDate", "TermMonths", "SecurityDeposit", "Options")
        ):
            old_v = entry.get("old_value")
            new_v = entry.get("new_value")
            eff = entry.get("effective_date")
            major.append(
                f"- `{path}`: `{old_v}` -> `{new_v}` (effective {fmt_mmddyyyy(eff) if eff else 'unspecified'})"
            )
    return major[:8]


def generate_abstract_markdown(
    bundle: dict[str, Any],
    property_type: str,
    audience: str,
    need_pm_block: bool = True,
    exec_only: bool = False,
) -> str:
    lease_state = bundle.get("lease_state") or {}
    change_log = bundle.get("change_log") or []
    trace_map = _trace_map(bundle)

    tenant = (((lease_state.get("Parties") or {}).get("Tenant") or {}).get("Name")) or "Unknown Tenant"
    landlord = (((lease_state.get("Parties") or {}).get("Landlord") or {}).get("Name")) or "Unknown Landlord"
    premises = ((lease_state.get("Premises") or {}).get("Address")) or "Unknown Premises"
    rsf = ((lease_state.get("Premises") or {}).get("RSF"))
    dates = lease_state.get("Dates") or {}
    metadata = lease_state.get("Metadata") or {}
    reference_date = parse_datetime_to_date(((metadata.get("Extraction") or {}).get("GenerationTimestamp"))) or today_utc()
    current_rent = _current_rent_step(lease_state, reference_date)

    metrics_rows = []
    metric_specs = [
        ("Tenant", tenant, "Parties.Tenant.Name", None),
        ("Landlord", landlord, "Parties.Landlord.Name", None),
        ("Premises", premises, "Premises.Address", None),
        ("RSF", rsf, "Premises.RSF", None),
        ("Lease Execution", dates.get("LeaseExecutionDate"), "Dates.LeaseExecutionDate", "date"),
        ("Commencement", dates.get("CommencementDate"), "Dates.CommencementDate", "date"),
        ("Expiration", dates.get("ExpirationDate"), "Dates.ExpirationDate", "date"),
    ]
    if current_rent:
        metric_specs.extend(
            [
                (
                    "Current Annual Base Rent",
                    current_rent.get("annualAmount"),
                    "Financials.BaseRent.Schedule",
                    "currency",
                ),
                (
                    "Current Monthly Base Rent",
                    current_rent.get("monthlyAmount"),
                    "Financials.BaseRent.Schedule",
                    "currency",
                ),
            ]
        )

    for label, raw_value, path, fmt in metric_specs:
        value, citation = _value_with_citation(
            raw_value, _citation_for_path(path, trace_map), formatter=fmt
        )
        metrics_rows.append((label, value, citation))

    renewal = (((lease_state.get("Options") or {}).get("RenewalOptions")) or {})
    renewal_summary = "None"
    if renewal:
        num = renewal.get("NumberOfOptions")
        term = renewal.get("TermMonthsPerOption")
        notice = renewal.get("NoticePeriodDays")
        renewal_summary = (
            f"{num or 0} option(s), term months {term or []}, notice {notice or 'Not specified'} days"
        )

    executive_lines = [
        f"# Lease Abstract — {tenant}",
        "",
        "## Executive Fact Sheet",
        "",
        f"{tenant} leases {premises} from {landlord}. This abstract summarizes current effective terms after supersession "
        f"review across provided documents. Property type focus: {property_type}. Audience focus: {audience}.",
        "",
    ]
    highlights = _major_change_lines(change_log if isinstance(change_log, list) else [])
    if highlights:
        executive_lines.extend(
            [
                "### Amendment Highlights",
                "",
                *highlights,
                "",
            ]
        )

    executive_lines.extend(
        [
            "| Metric | Value | Citation |",
            "|---|---|---|",
            *[f"| {label} | {value} | {citation} |" for (label, value, citation) in metrics_rows],
            "",
            "\\f",
        ]
    )

    if exec_only:
        return "\n".join(executive_lines).strip() + "\n"

    # Canonical sections
    rent_schedule = (((lease_state.get("Financials") or {}).get("BaseRent") or {}).get("Schedule")) or []
    additional_rent = ((lease_state.get("Financials") or {}).get("AdditionalRent")) or {}
    maintenance = (((lease_state.get("Clauses") or {}).get("Maintenance")) or {})

    sections: list[str] = []
    sections.extend(
        [
            "## Lease Fundamentals",
            "",
            f"- Tenant: {tenant} ({_citation_for_path('Parties.Tenant.Name', trace_map)})",
            f"- Landlord: {landlord} ({_citation_for_path('Parties.Landlord.Name', trace_map)})",
            f"- Premises: {premises} ({_citation_for_path('Premises.Address', trace_map)})",
            f"- Term: {fmt_mmddyyyy(dates.get('CommencementDate'))} to {fmt_mmddyyyy(dates.get('ExpirationDate'))} "
            f"({_citation_for_path('Dates.CommencementDate', trace_map)}; {_citation_for_path('Dates.ExpirationDate', trace_map)})",
            "",
            "\\f",
            "## Rent & Security",
            "",
            "| Period | Start | End | Annual | Monthly | $/RSF | Citation |",
            "|---|---|---|---:|---:|---:|---|",
        ]
    )

    if isinstance(rent_schedule, list) and rent_schedule:
        for row in rent_schedule:
            if not isinstance(row, dict):
                continue
            sections.append(
                "| {period} | {start} | {end} | ${annual:,.2f} | ${monthly:,.2f} | {psf:,.2f} | {citation} |".format(
                    period=row.get("period") or "N/A",
                    start=fmt_mmddyyyy(row.get("startDate")),
                    end=fmt_mmddyyyy(row.get("endDate")),
                    annual=float(row.get("annualAmount") or 0.0),
                    monthly=float(row.get("monthlyAmount") or 0.0),
                    psf=float(row.get("baseRentPSF") or 0.0),
                    citation=_citation_for_path("Financials.BaseRent.Schedule", trace_map),
                )
            )
    else:
        sections.append("| Not specified | - | - | - | - | - | citation_unavailable |")
    security_amount = float(
        (((lease_state.get("Financials") or {}).get("SecurityDeposit") or {}).get("Amount") or 0.0)
    )
    sections.extend(
        [
            "",
            f"Security Deposit: ${security_amount:,.2f} "
            f"({_citation_for_path('Financials.SecurityDeposit.Amount', trace_map)})",
            "",
            "\\f",
            "## Additional Rent / Expenses",
            "",
            f"- Recovery Type: {additional_rent.get('RecoveryType') or 'Not specified'} "
            f"({_citation_for_path('Financials.AdditionalRent.RecoveryType', trace_map)})",
            f"- Pro-rata Share: {((additional_rent.get('ProRataShare') * 100) if additional_rent.get('ProRataShare') is not None else 'Not specified')} "
            f"({_citation_for_path('Financials.AdditionalRent.ProRataShare', trace_map)})",
            f"- CAM Cap: {((additional_rent.get('CAMCap') or {}).get('Percent') if isinstance(additional_rent.get('CAMCap'), dict) else 'Not specified')} "
            f"({_citation_for_path('Financials.AdditionalRent.CAMCap', trace_map)})",
            "",
            "\\f",
            "## Options",
            "",
            f"- Renewal: {renewal_summary} ({_citation_for_path('Options.RenewalOptions', trace_map)})",
            f"- Termination: {(((lease_state.get('Options') or {}).get('TerminationOptions')) or {}).get('TerminationDate') or 'Not specified'} "
            f"({_citation_for_path('Options.TerminationOptions.TerminationDate', trace_map)})",
            "",
            "\\f",
            "## Use / Operating Covenants",
            "",
            f"- Permitted Use: {((lease_state.get('Clauses') or {}).get('Use')) or 'Not specified'} "
            f"({_citation_for_path('Clauses.Use', trace_map)})",
            f"- Assignment/Subletting: {((((lease_state.get('Clauses') or {}).get('AssignmentAndSubletting')) or {}).get('Restrictions')) or 'Not specified'} "
            f"({_citation_for_path('Clauses.AssignmentAndSubletting.Restrictions', trace_map)})",
            "",
            "\\f",
            "## Maintenance & Repairs",
            "",
        ]
    )

    if need_pm_block:
        sections.extend(
            [
                "| Area | Landlord | Tenant | Citation |",
                "|---|---|---|---|",
                f"| Building/Structural | {maintenance.get('LandlordResponsibilities') or 'Not specified'} | {maintenance.get('TenantResponsibilities') or 'Not specified'} | {_citation_for_path('Clauses.Maintenance', trace_map)} |",
                "",
            ]
        )
    else:
        sections.append(
            f"- Maintenance Summary: {maintenance or 'Not specified'} ({_citation_for_path('Clauses.Maintenance', trace_map)})"
        )

    sections.extend(
        [
            "\\f",
            "## Other Key Provisions / Open Items",
            "",
            f"- Governing Law: {((lease_state.get('Clauses') or {}).get('GoverningLaw')) or 'Not specified'} "
            f"({_citation_for_path('Clauses.GoverningLaw', trace_map)})",
            f"- Environmental: {((lease_state.get('Clauses') or {}).get('EnvironmentalCompliance')) or 'Not specified'} "
            f"({_citation_for_path('Clauses.EnvironmentalCompliance', trace_map)})",
            "",
            "### Change Log",
            "",
            "| Field Path | Old Value | New Value | Effective Date | Source | Citation |",
            "|---|---|---|---|---|---|",
        ]
    )

    if isinstance(change_log, list) and change_log:
        for row in change_log:
            if not isinstance(row, dict):
                continue
            sections.append(
                f"| {row.get('field_path')} | {row.get('old_value')} | {row.get('new_value')} | "
                f"{fmt_mmddyyyy(row.get('effective_date')) if row.get('effective_date') else 'Not specified'} | "
                f"{row.get('source_document') or 'Not specified'} | {row.get('citation') or 'citation_unavailable'} |"
            )
    else:
        sections.append("| No amendments logged | - | - | - | - | - |")

    sections.extend(
        [
            "",
            "_Self-check: Abstract generated from lease_state with deterministic mappings, table citations, and documented date/currency formatting._",
        ]
    )

    return "\n".join(executive_lines + sections).strip() + "\n"
