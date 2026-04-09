---
name: lease-calendar
description: >
  Emit a critical-dates calendar (ICS feed + JSON manifest) from a validated
  lease_state. Covers commencement, expiration, rent step dates, renewal and
  termination notice deadlines, guaranty burn-off, and other dated obligations.
  TRIGGER when: user asks for "calendar", "ICS", "critical dates", "key dates
  export", "notice deadlines", "option windows", "tickler", or wants
  schedulable reminders from extraction data.
  DO NOT TRIGGER when: user asks for extract, abstract, render PDF, CSV/Excel
  export, eval, diff, risk, or portfolio rollup.
---

# Calendar Procedure (ICS + JSON Manifest)

## Role
Guide **shortcut.ai_cre** when converting a validated `lease_state` into a critical-dates calendar that asset managers and lease administrators can load into Outlook, Google Calendar, or a portfolio tickler system. Every event must trace back to a source field in `lease_state` with the same citation the extractor produced.

Hard constraints (single-tenant rule, sequential supersession, per-field traceability): per CLAUDE.md.
Confidence scale, validation status enum, citation format, date conventions: per `config/shared_constants.md`.

## Inputs
- `CANDIDATE_JSON` (required): A validated extraction output containing `lease_state` and `traceability`. Should ideally be a `lease-eval` PASS verdict. If `ValidationStatus != PASSED` or `LeaseStatus != "Active"`, warn and proceed only on user confirmation.
- `TIMEZONE` (optional, default = `UTC`): IANA timezone for the ICS `DTSTART` fields. All calendar events are all-day (VALUE=DATE), so timezone primarily affects `DTSTAMP`.
- `LEAD_DAYS` (optional, default = `0`): Additional lead time added to notice deadlines so the event lands earlier than the contractual last-day-to-act. Set to 30 to get "30 days before deadline" reminders.
- `INCLUDE_RENT_STEPS` (optional, default = `true`): Emit a calendar event for every `Financials.BaseRent.Schedule[].startDate`. Set to `false` for leases with long schedules when the user only wants notice deadlines.

## Output Objects
- `calendar_ics`: A fenced code block containing a valid ICS (RFC 5545) feed. One `VEVENT` per critical date.
- `calendar_manifest`: A fenced `json` block listing every event with metadata — event_type, date, source_field_path, citation, derivation (if computed), lead_days_applied, notes.
- `summary`: Short markdown block with event count by category and any dates that fell into the past relative to today.

## Event Catalog
The canonical list of event types, their source fields, and derivation rules lives in `references/event_catalog.md`. Read it on demand — do not inline the full catalog in the procedure.

## Workflow

### 1. Load & Sanity Check
1. Parse `CANDIDATE_JSON`. Locate `lease_state` and `traceability`. If either is missing, stop and ask for a complete extraction output.
2. Check `lease_state.Metadata.LeaseStatus`. If not `"Active"` (e.g., `"Expired"`, `"Terminated"`), warn the user: *"This lease's status is not Active — the calendar may contain historical-only events."* Proceed on confirmation.
3. If `lease-eval` has not been run, note it in the summary. Do not block — this skill is useful even on drafts — but flag the gap.
4. Determine "today" as the extraction generation timestamp (`Metadata.Extraction.GenerationTimestamp`) truncated to date. Use this as the reference for past/future classification.

### 2. Enumerate Fixed Events
Walk `lease_state` and emit a `VEVENT` for every populated field that matches an entry in the event catalog's **Fixed** section. For each event, capture:
- `uid`: `lease-<tenant-slug>-<field-path>-<date>@leasegpt`
- `date`: `YYYY-MM-DD` from the source field
- `summary`: Human label (e.g., `"Lease Commencement — Coastline Stationery LLC"`)
- `description`: Citation + source_field_path + any notes from traceability
- `categories`: One of `TERM`, `RENT`, `OPTION`, `GUARANTY`, `INSURANCE`, `OTHER`
- `source_field_path`: Dot-notation path used
- `citation`: Copy from `traceability.extractedFieldsMetadata[source_field_path].citation`

Fixed events include (non-exhaustive; consult catalog):
- `Dates.LeaseExecutionDate` → `Lease Executed`
- `Dates.CommencementDate` → `Lease Commencement`
- `Dates.RentCommencementDate` → `Rent Commencement` (skip if same as CommencementDate to avoid duplicates)
- `Dates.ExpirationDate` → `Lease Expiration`
- `Financials.BaseRent.Schedule[i].startDate` → `Rent Step — Year N — $X.XX/RSF` (one per schedule entry; skip the first if it equals CommencementDate)
- `Clauses.Guaranty.BurnOff` → `Guaranty Burn-Off`
- `Options.TerminationOptions.TerminationDate` → `Termination Right Effective`

### 3. Derive Computed Events
For notice-window fields, compute the deadline and emit an event. Each derived event records its formula in the manifest so the user can audit the math.

| Event | Formula | Source fields |
|---|---|---|
| Renewal Notice Deadline | `ExpirationDate − NoticePeriodDays − LEAD_DAYS` | `Dates.ExpirationDate`, `Options.RenewalOptions.NoticePeriodDays` |
| Renewal Notice Window Opens | `ExpirationDate − NoticePeriodDays − 90` (heuristic: 90-day window prior to deadline; override only if lease defines `OtherTerms`) | same |
| Termination Notice Deadline | `TerminationDate − NoticePeriodDays − LEAD_DAYS` | `Options.TerminationOptions.TerminationDate`, `Options.TerminationOptions.NoticePeriodDays` |
| ROFO Notice Deadline | derivable only when the user-supplied `Options.RightOfFirstOffer.NoticePeriodDays` is a tenant-response window tied to a fixed date. If the notice is triggered by landlord action (most cases), **skip** — record in manifest as `derivation_skipped: "trigger-based, no fixed date"`. | `Options.RightOfFirstOffer.*` |
| ROFR Notice Deadline | Same rule as ROFO. | `Options.RightOfFirstRefusal.*` |
| CAM Reconciliation Due | If `AdditionalRent.ReconciliationTerms` mentions a fixed number of days after year-end, compute next occurrence. Otherwise skip. | `Financials.AdditionalRent.ReconciliationTerms` |

**Skip-don't-guess rule**: If any formula input is `null` or ambiguous, do NOT invent a date. Record the event in the manifest with `derivation_skipped: "<reason>"` and move on. A missing event is always preferable to a wrong date — asset managers act on these reminders.

### 4. Deduplicate & Sort
- Collapse events with identical `date` + `summary` (e.g., first rent step = commencement).
- Sort by `date` ascending.
- Classify each event as `past`, `today`, or `future` relative to the reference date from §1.4.

### 5. Emit ICS Feed
Produce a fenced ` ```ics ` code block containing a valid RFC 5545 calendar:

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//LeaseGPT//lease-calendar v4.0.0//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:<Tenant Name> — Critical Dates
X-WR-TIMEZONE:<TIMEZONE>
BEGIN:VEVENT
UID:<uid>
DTSTAMP:<now UTC as YYYYMMDDTHHMMSSZ>
DTSTART;VALUE=DATE:<YYYYMMDD>
SUMMARY:<summary>
DESCRIPTION:<citation> | <source_field_path>\\n<notes>
CATEGORIES:<category>
END:VEVENT
...
END:VCALENDAR
```

Rules:
- Use `DTSTART;VALUE=DATE:YYYYMMDD` (all-day). Do not emit `DTEND` for all-day events.
- Escape commas, semicolons, and backslashes in `SUMMARY`/`DESCRIPTION` per RFC 5545.
- Fold long lines at 75 octets if strictly needed; otherwise leave unfolded (most clients accept unfolded lines).
- UID must be stable across re-runs so re-importing updates rather than duplicates. Use the `lease-<tenant-slug>-<field-path>-<date>@leasegpt` scheme.

### 6. Emit JSON Manifest
Produce a fenced ` ```json ` block with this shape:

```json
{
  "tenant": "<Parties.Tenant.Name>",
  "premises": "<Premises.Address>",
  "reference_date": "<YYYY-MM-DD>",
  "timezone": "<TIMEZONE>",
  "lead_days_applied": 0,
  "event_count": 0,
  "events": [
    {
      "date": "YYYY-MM-DD",
      "event_type": "lease_commencement | rent_step | renewal_notice_deadline | ...",
      "summary": "…",
      "category": "TERM | RENT | OPTION | GUARANTY | INSURANCE | OTHER",
      "source_field_path": "Dates.CommencementDate",
      "citation": "OL p3 §2.1",
      "derivation": null,
      "status": "past | today | future",
      "notes": null
    }
  ],
  "skipped": [
    {
      "event_type": "rofo_notice_deadline",
      "reason": "trigger-based, no fixed date"
    }
  ]
}
```

The manifest is the source of truth; the ICS is a derived view. If the two ever disagree, the manifest wins.

### 7. Summary Block
Close with a short markdown summary:
- Event count by category (3 TERM, 7 RENT, 2 OPTION, …)
- Number of past events (historical reference only)
- Number of future events within the next 12 months (action items)
- Any skipped events with their reasons
- One line on what to do next (`"Import the ICS block into your calendar app as a new calendar."`)

Keep the summary under 15 lines.

## Validation & Consistency Checks
Before emitting, verify:
- Every event date parses as `YYYY-MM-DD`.
- Every `source_field_path` resolves to a non-null value in `lease_state` (for fixed events) or to the formula inputs (for derived events).
- Every event has a citation unless its source is a pure derivation from fields that each already have citations (in which case the derived event's citation is the **union** of input citations, joined with `; `).
- No event falls before `Dates.OriginalLeaseDate` (sanity check — flag as a calendar bug if it does).
- Renewal notice deadline falls before `Dates.ExpirationDate` (math check).

If any check fails, record the failure in the manifest under `warnings` and continue.

## Error Handling
- **Missing `lease_state`**: stop, ask user to supply a complete extraction output.
- **`Dates.ExpirationDate` missing**: cannot compute renewal notice deadline. Emit fixed events only; record skipped computed events with reason `missing ExpirationDate`.
- **Ambiguous notice period** (e.g., `NoticePeriodDays` is null but `OtherTerms` describes it in prose): do NOT parse the prose. Skip with reason `notice period defined in prose, not parseable`.
- **Past lease**: if ALL fixed dates are in the past, still emit the calendar but label the lease as historical in the summary.

## Prerequisites
- Validated `lease_state` with dated fields populated. For best results, run `lease-eval` first — a conformance-passing candidate will have every dated field citable.
- This skill is additive. Re-running it on the same lease should produce stable UIDs so clients update rather than duplicate.

## Worked Example (Fixture golden_ol_a1)
Given fixture `lease-eval/fixtures/golden_ol_a1/lease_state.json`, the skill should emit at minimum:

| Date | Event | Source |
|---|---|---|
| 2025-04-15 | Lease Executed | `Dates.LeaseExecutionDate` |
| 2025-06-01 | Lease Commencement (also Rent Commencement, Year 1 rent step — dedup to one) | `Dates.CommencementDate` |
| 2026-06-01 | Rent Step — Year 2 — $33.00/RSF | `Financials.BaseRent.Schedule[1].startDate` |
| 2027-06-01 | Rent Step — Year 3 — $34.00/RSF | `Financials.BaseRent.Schedule[2].startDate` |
| 2028-06-01 | Rent Step — Year 4 — $35.00/RSF | `Financials.BaseRent.Schedule[3].startDate` |
| 2029-06-01 | Rent Step — Year 5 — $36.00/RSF | `Financials.BaseRent.Schedule[4].startDate` |
| 2030-06-01 | Rent Step — Year 6 — $37.00/RSF | `Financials.BaseRent.Schedule[5].startDate` |
| 2031-06-01 | Rent Step — Year 7 — $38.00/RSF | `Financials.BaseRent.Schedule[6].startDate` |
| 2031-09-04 | Renewal Notice Deadline (derived: 2032-05-31 − 270d) | `Dates.ExpirationDate` + `Options.RenewalOptions.NoticePeriodDays` |
| 2032-05-31 | Lease Expiration | `Dates.ExpirationDate` |

Skipped: ROFO, ROFR, termination (no termination option in fixture), CAM reconciliation (no fixed year-end anchor extracted).

If the derived renewal deadline comes out to a date other than `2031-09-04`, the math is wrong — 2032-05-31 minus 270 days is 2031-09-04.

## Follow-on Work (Not in this MVP)
- Timezone-aware notice windows (business days vs calendar days; jurisdictions that toll deadlines on weekends/holidays).
- Multi-calendar export (separate ICS feeds per category: TERM, RENT, OPTION).
- Integration with `lease-portfolio` to emit a single combined ICS across a book of leases.
- Parsing of `ReconciliationTerms` and other prose fields to derive additional deadlines.
