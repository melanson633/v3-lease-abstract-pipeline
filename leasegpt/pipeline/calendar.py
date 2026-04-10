"""Implementation of the lease-calendar skill."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from leasegpt.utils.dates import parse_date, parse_datetime_to_date, today_utc
from leasegpt.utils.json_paths import ancestor_paths


@dataclass(slots=True)
class CalendarResult:
    calendar_ics: str
    manifest: dict[str, Any]
    summary_markdown: str


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


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return re.sub(r"-{2,}", "-", cleaned) or "unknown"


def _escape_ics(value: str) -> str:
    return value.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def _event_uid(tenant: str, event_type: str, source_path: str, event_date: date) -> str:
    source_slug = re.sub(r"\[\d+\]", lambda m: f"-{m.group(0).strip('[]')}-", source_path)
    source_slug = source_slug.replace(".", "-")
    return f"lease-{_slug(tenant)}-{event_type}-{source_slug}-{event_date.strftime('%Y%m%d')}@leasegpt"


def _status_for_event(event_date: date, reference: date) -> str:
    if event_date < reference:
        return "past"
    if event_date == reference:
        return "today"
    return "future"


def _add_fixed_event(
    events: list[dict[str, Any]],
    tenant: str,
    category: str,
    event_type: str,
    summary: str,
    source_path: str,
    value: str | None,
    trace_map: dict[str, Any],
    reference_date: date,
    warnings: list[str],
) -> None:
    parsed = parse_date(value)
    if not parsed:
        return
    trace = _trace_for(source_path, trace_map)
    citation = trace.get("citation")
    note_parts = []
    status = trace.get("validation_status")
    confidence = trace.get("confidence")
    if status in {"flagged", "uncertain"}:
        note_parts.append(f"source field has validation_status={status}")
    if isinstance(confidence, (int, float)) and confidence < 0.7:
        note_parts.append(f"low confidence: {confidence}")
    if not citation:
        warnings.append(f"Missing citation for event source path {source_path}")
        citation = "citation_unavailable"

    events.append(
        {
            "date": parsed.isoformat(),
            "event_type": event_type,
            "summary": summary,
            "category": category,
            "source_field_path": source_path,
            "citation": citation,
            "derivation": None,
            "status": _status_for_event(parsed, reference_date),
            "notes": "; ".join(note_parts) if note_parts else None,
            "uid": _event_uid(tenant, event_type, source_path, parsed),
        }
    )


def _render_ics(tenant: str, events: list[dict[str, Any]], timezone_name: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//LeaseGPT//lease-calendar v4.0.0//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape_ics(tenant)} — Critical Dates",
        f"X-WR-TIMEZONE:{_escape_ics(timezone_name)}",
    ]
    for event in events:
        event_date = date.fromisoformat(event["date"])
        description = f"{event['citation']} | {event['source_field_path']}"
        if event.get("notes"):
            description += f"\\n{event['notes']}"
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{event['uid']}",
                f"DTSTAMP:{now}",
                f"DTSTART;VALUE=DATE:{event_date.strftime('%Y%m%d')}",
                f"SUMMARY:{_escape_ics(event['summary'])}",
                f"DESCRIPTION:{_escape_ics(description)}",
                f"CATEGORIES:{event['category']}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\n".join(lines) + "\n"


def _dedupe_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    deduped = []
    for event in sorted(events, key=lambda e: (e["date"], e["summary"])):
        key = (event["date"], event["summary"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    return deduped


def build_calendar(
    bundle: dict[str, Any],
    timezone_name: str = "UTC",
    lead_days: int = 0,
    include_rent_steps: bool = True,
) -> CalendarResult:
    lease_state = bundle.get("lease_state") or {}
    trace_map = _trace_map(bundle)
    tenant = (((lease_state.get("Parties") or {}).get("Tenant") or {}).get("Name")) or "Unknown Tenant"
    premises = ((lease_state.get("Premises") or {}).get("Address")) or None
    metadata = lease_state.get("Metadata") or {}
    reference_date = parse_datetime_to_date(((metadata.get("Extraction") or {}).get("GenerationTimestamp"))) or today_utc()

    warnings: list[str] = []
    skipped: list[dict[str, str]] = []
    events: list[dict[str, Any]] = []

    dates = lease_state.get("Dates") or {}
    _add_fixed_event(
        events,
        tenant=tenant,
        category="TERM",
        event_type="lease_executed",
        summary=f"Lease Executed — {tenant}",
        source_path="Dates.LeaseExecutionDate",
        value=dates.get("LeaseExecutionDate"),
        trace_map=trace_map,
        reference_date=reference_date,
        warnings=warnings,
    )
    _add_fixed_event(
        events,
        tenant=tenant,
        category="TERM",
        event_type="lease_commencement",
        summary=f"Lease Commencement — {tenant}",
        source_path="Dates.CommencementDate",
        value=dates.get("CommencementDate"),
        trace_map=trace_map,
        reference_date=reference_date,
        warnings=warnings,
    )
    _add_fixed_event(
        events,
        tenant=tenant,
        category="TERM",
        event_type="rent_commencement",
        summary=f"Rent Commencement — {tenant}",
        source_path="Dates.RentCommencementDate",
        value=dates.get("RentCommencementDate"),
        trace_map=trace_map,
        reference_date=reference_date,
        warnings=warnings,
    )
    _add_fixed_event(
        events,
        tenant=tenant,
        category="TERM",
        event_type="lease_expiration",
        summary=f"Lease Expiration — {tenant}",
        source_path="Dates.ExpirationDate",
        value=dates.get("ExpirationDate"),
        trace_map=trace_map,
        reference_date=reference_date,
        warnings=warnings,
    )

    base_rent = (((lease_state.get("Financials") or {}).get("BaseRent")) or {})
    schedule = base_rent.get("Schedule") or []
    if include_rent_steps and isinstance(schedule, list):
        for idx, row in enumerate(schedule):
            if not isinstance(row, dict):
                continue
            start_date = parse_date(row.get("startDate"))
            if not start_date:
                continue
            if idx == 0 and parse_date(dates.get("CommencementDate")) == start_date:
                continue
            period = row.get("period") or f"Period {idx + 1}"
            psf = row.get("baseRentPSF")
            summary = f"Rent Step — {period}"
            if psf is not None:
                summary += f" — ${float(psf):,.2f}/RSF"
            events.append(
                {
                    "date": start_date.isoformat(),
                    "event_type": "rent_step",
                    "summary": summary,
                    "category": "RENT",
                    "source_field_path": f"Financials.BaseRent.Schedule[{idx}].startDate",
                    "citation": _trace_for("Financials.BaseRent.Schedule", trace_map).get("citation")
                    or "citation_unavailable",
                    "derivation": None,
                    "status": _status_for_event(start_date, reference_date),
                    "notes": None,
                    "uid": _event_uid(
                        tenant,
                        "rent_step",
                        f"Financials.BaseRent.Schedule[{idx}].startDate",
                        start_date,
                    ),
                }
            )

    guaranty_burn = (((lease_state.get("Clauses") or {}).get("Guaranty")) or {}).get("BurnOff")
    _add_fixed_event(
        events,
        tenant=tenant,
        category="GUARANTY",
        event_type="guaranty_burn_off",
        summary=f"Guaranty Burn-Off — {tenant}",
        source_path="Clauses.Guaranty.BurnOff",
        value=guaranty_burn,
        trace_map=trace_map,
        reference_date=reference_date,
        warnings=warnings,
    )

    # Derived renewal deadline
    expiration = parse_date(dates.get("ExpirationDate"))
    renewal = (((lease_state.get("Options") or {}).get("RenewalOptions")) or {})
    notice_days = renewal.get("NoticePeriodDays")
    options_count = renewal.get("NumberOfOptions")
    if expiration and isinstance(notice_days, int) and (options_count or 0) > 0:
        deadline = expiration - timedelta(days=notice_days + lead_days)
        citation_parts = []
        for source_path in ("Dates.ExpirationDate", "Options.RenewalOptions.NoticePeriodDays"):
            citation = _trace_for(source_path, trace_map).get("citation")
            if citation:
                citation_parts.append(citation)
        events.append(
            {
                "date": deadline.isoformat(),
                "event_type": "renewal_notice_deadline",
                "summary": f"Renewal Option Notice Deadline — {tenant}",
                "category": "OPTION",
                "source_field_path": "Options.RenewalOptions.NoticePeriodDays",
                "citation": "; ".join(dict.fromkeys(citation_parts)) or "citation_unavailable",
                "derivation": f"{expiration.isoformat()} - {notice_days} days - lead {lead_days} days",
                "status": _status_for_event(deadline, reference_date),
                "notes": None,
                "uid": _event_uid(
                    tenant,
                    "renewal_notice_deadline",
                    "Options.RenewalOptions.NoticePeriodDays",
                    deadline,
                ),
            }
        )
        window_open = expiration - timedelta(days=notice_days + 90)
        events.append(
            {
                "date": window_open.isoformat(),
                "event_type": "renewal_notice_window_opens",
                "summary": f"Renewal Notice Window Opens — {tenant}",
                "category": "OPTION",
                "source_field_path": "Options.RenewalOptions.NoticePeriodDays",
                "citation": "; ".join(dict.fromkeys(citation_parts)) or "citation_unavailable",
                "derivation": "heuristic_window_90d",
                "status": _status_for_event(window_open, reference_date),
                "notes": "Heuristic 90-day window before contractual deadline.",
                "uid": _event_uid(
                    tenant,
                    "renewal_notice_window_opens",
                    "Options.RenewalOptions.NoticePeriodDays",
                    window_open,
                ),
            }
        )
    else:
        reason = "missing_expiration_date" if not expiration else "missing_notice_period"
        skipped.append({"event_type": "renewal_notice_deadline", "reason": reason})

    # Termination deadline
    termination = (((lease_state.get("Options") or {}).get("TerminationOptions")) or {})
    term_date_raw = termination.get("TerminationDate")
    term_date = parse_date(term_date_raw) if isinstance(term_date_raw, str) else None
    term_notice = termination.get("NoticePeriodDays")
    if term_date and isinstance(term_notice, int) and termination.get("EarlyTerminationRight"):
        term_deadline = term_date - timedelta(days=term_notice + lead_days)
        citations = []
        for source_path in ("Options.TerminationOptions.TerminationDate", "Options.TerminationOptions.NoticePeriodDays"):
            citation = _trace_for(source_path, trace_map).get("citation")
            if citation:
                citations.append(citation)
        events.append(
            {
                "date": term_deadline.isoformat(),
                "event_type": "termination_notice_deadline",
                "summary": f"Termination Notice Deadline — {tenant}",
                "category": "OPTION",
                "source_field_path": "Options.TerminationOptions.NoticePeriodDays",
                "citation": "; ".join(dict.fromkeys(citations)) or "citation_unavailable",
                "derivation": f"{term_date.isoformat()} - {term_notice} days - lead {lead_days} days",
                "status": _status_for_event(term_deadline, reference_date),
                "notes": None,
                "uid": _event_uid(
                    tenant,
                    "termination_notice_deadline",
                    "Options.TerminationOptions.NoticePeriodDays",
                    term_deadline,
                ),
            }
        )
    elif termination:
        skipped.append(
            {
                "event_type": "termination_notice_deadline",
                "reason": "termination_right_disabled"
                if not termination.get("EarlyTerminationRight")
                else "missing_source_field",
            }
        )

    # ROFO/ROFR skipped by default
    if ((lease_state.get("Options") or {}).get("RightOfFirstOffer")):
        skipped.append({"event_type": "rofo_notice_deadline", "reason": "trigger-based, no fixed date"})
    if ((lease_state.get("Options") or {}).get("RightOfFirstRefusal")):
        skipped.append({"event_type": "rofr_notice_deadline", "reason": "trigger-based, no fixed date"})

    # CAM reconciliation due (simple parser for "<N> days ... year-end")
    reconciliation = (((lease_state.get("Financials") or {}).get("AdditionalRent")) or {}).get("ReconciliationTerms")
    if isinstance(reconciliation, str):
        match = re.search(r"(\d{1,3})\s+days?.*year-end", reconciliation, flags=re.IGNORECASE)
        if match:
            days = int(match.group(1))
            anchor = date(reference_date.year, 12, 31)
            cam_due = anchor + timedelta(days=days)
            events.append(
                {
                    "date": cam_due.isoformat(),
                    "event_type": "cam_reconciliation_due",
                    "summary": f"CAM Reconciliation Due — {tenant}",
                    "category": "OTHER",
                    "source_field_path": "Financials.AdditionalRent.ReconciliationTerms",
                    "citation": _trace_for("Financials.AdditionalRent.ReconciliationTerms", trace_map).get("citation")
                    or "citation_unavailable",
                    "derivation": f"{anchor.isoformat()} + {days} days",
                    "status": _status_for_event(cam_due, reference_date),
                    "notes": None,
                    "uid": _event_uid(
                        tenant,
                        "cam_reconciliation_due",
                        "Financials.AdditionalRent.ReconciliationTerms",
                        cam_due,
                    ),
                }
            )
        else:
            skipped.append(
                {
                    "event_type": "cam_reconciliation_due",
                    "reason": "reconciliation_anchor_undefined",
                }
            )

    deduped_events = _dedupe_events(events)
    ics_text = _render_ics(tenant=tenant, events=deduped_events, timezone_name=timezone_name)

    category_counts: dict[str, int] = {}
    future_12m = 0
    for event in deduped_events:
        category_counts[event["category"]] = category_counts.get(event["category"], 0) + 1
        event_date = date.fromisoformat(event["date"])
        if reference_date <= event_date <= (reference_date + timedelta(days=365)):
            future_12m += 1

    summary_lines = [
        f"Events by category: {', '.join(f'{k}={v}' for k, v in sorted(category_counts.items())) or 'none'}",
        f"Past events: {sum(1 for e in deduped_events if e['status'] == 'past')}",
        f"Future events within 12 months: {future_12m}",
    ]
    if skipped:
        summary_lines.append(
            "Skipped: " + "; ".join(f"{item['event_type']} ({item['reason']})" for item in skipped[:5])
        )
    summary_lines.append("Import the ICS file into your calendar app as a new calendar.")

    manifest = {
        "tenant": tenant,
        "premises": premises,
        "reference_date": reference_date.isoformat(),
        "timezone": timezone_name,
        "lead_days_applied": lead_days,
        "event_count": len(deduped_events),
        "events": deduped_events,
        "skipped": skipped,
        "warnings": warnings,
    }

    return CalendarResult(
        calendar_ics=ics_text,
        manifest=manifest,
        summary_markdown="\n".join(summary_lines),
    )
