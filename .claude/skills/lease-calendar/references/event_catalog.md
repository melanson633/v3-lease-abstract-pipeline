# Event Catalog (v4.0.0)

> Layer-3 reference for the `lease-calendar` skill. Canonical list of every event type the skill can emit, keyed to v4 schema paths. Loaded on demand. The skill procedure lives in `../SKILL.md`.

## Categories
- **TERM** — lifecycle of the lease itself (execution, commencement, expiration)
- **RENT** — scheduled rent steps, abatement boundaries
- **OPTION** — renewal, termination, expansion, contraction, ROFO/ROFR deadlines
- **GUARANTY** — guaranty burn-off, LOC renewal/reduction
- **INSURANCE** — COI renewal, certificate delivery deadlines (only if extracted as dated)
- **OTHER** — CAM reconciliation, audit windows, estoppel response deadlines

## 1. Fixed Events (Direct Field Reads)

Events whose date is a non-null value of a single dated field in `lease_state`. Emit one VEVENT per populated field.

| Event Type | Source Field | Category | Summary Template |
|---|---|---|---|
| `lease_executed` | `Dates.LeaseExecutionDate` | TERM | `Lease Executed — <Tenant Name>` |
| `original_lease_date` | `Dates.OriginalLeaseDate` | TERM | `Original Lease Date — <Tenant Name>` (suppress if equal to `lease_executed`) |
| `lease_commencement` | `Dates.CommencementDate` | TERM | `Lease Commencement — <Tenant Name>` |
| `rent_commencement` | `Dates.RentCommencementDate` | TERM | `Rent Commencement — <Tenant Name>` (suppress if equal to `lease_commencement`) |
| `lease_expiration` | `Dates.ExpirationDate` | TERM | `Lease Expiration — <Tenant Name>` |
| `base_rent_commencement` | `Financials.BaseRent.CommencementDate` | RENT | `Base Rent Commencement — <Tenant Name>` (suppress if equal to `rent_commencement`) |
| `rent_step` | `Financials.BaseRent.Schedule[i].startDate` (for i ≥ 1; skip i=0 if equal to commencement) | RENT | `Rent Step — <period> — $<baseRentPSF>/RSF` |
| `guaranty_burn_off` | `Clauses.Guaranty.BurnOff` | GUARANTY | `Guaranty Burn-Off — <Guarantor>` |
| `termination_right_effective` | `Options.TerminationOptions.TerminationDate` (only if it parses as a date) | OPTION | `Termination Right Effective — <Tenant Name>` |

### Suppression rules
- **Exact-date dedup**: If two events land on the same date with the same category, keep the higher-priority one. Priority order within TERM: `lease_commencement` > `rent_commencement` > `base_rent_commencement` > `original_lease_date` > `lease_executed`.
- **Commencement vs. first rent step**: The first entry in `Financials.BaseRent.Schedule` typically starts on `CommencementDate`. Emit `lease_commencement` only; skip `rent_step` for i=0 when dates match.
- **Past-dated events**: Still emit them (asset managers use historical timelines), but classify `status: past` in the manifest.

## 2. Derived Events (Computed From Formula)

Events whose date is computed from one or more source fields. Record the formula in the manifest's `derivation` field so the user can audit.

### 2.1 Renewal Notice Deadline

- **Source fields**: `Dates.ExpirationDate`, `Options.RenewalOptions.NoticePeriodDays`
- **Formula**: `ExpirationDate − NoticePeriodDays − LEAD_DAYS`
- **Skip if**: `NumberOfOptions` is 0 or null, OR `NoticePeriodDays` is null, OR `ExpirationDate` is null.
- **Citation**: union of the two source fields' citations, joined with `; `.
- **Summary**: `Renewal Option Notice Deadline — <Tenant Name>` with the computed date.
- **Category**: OPTION

### 2.2 Renewal Notice Window Opens

- **Source fields**: same as 2.1
- **Formula**: `ExpirationDate − NoticePeriodDays − 90` (90-day heuristic; the contract rarely defines a window-open date, only a deadline)
- **Skip if**: same as 2.1, OR the user sets `INCLUDE_NOTICE_WINDOW_OPENS=false`.
- **Summary**: `Renewal Notice Window Opens — <Tenant Name>`
- **Category**: OPTION
- **Note**: The 90-day heuristic is a convenience, not a contractual milestone. Mark it explicitly in the manifest: `derivation: "heuristic_window_90d"`.

### 2.3 Termination Notice Deadline

- **Source fields**: `Options.TerminationOptions.TerminationDate`, `Options.TerminationOptions.NoticePeriodDays`
- **Formula**: `TerminationDate − NoticePeriodDays − LEAD_DAYS`
- **Skip if**: either field null, OR `EarlyTerminationRight` is false/null.
- **Category**: OPTION

### 2.4 ROFO / ROFR Notice Deadlines — **skip by default**

- **Why**: ROFO/ROFR notice periods are almost always a tenant response window triggered by landlord action (e.g., "tenant has 15 days after landlord's notice of intent to lease"). There is no fixed calendar date until the landlord acts.
- **Rule**: Do not synthesize a date. Record in the manifest's `skipped[]` array with `reason: "trigger-based, no fixed date"`.
- **Exception**: If the user explicitly provides an assumed landlord-notice date via `ROFO_ASSUMED_TRIGGER_DATE`, compute `trigger_date + NoticePeriodDays`.

### 2.5 CAM Reconciliation Due

- **Source fields**: `Financials.AdditionalRent.ReconciliationTerms`
- **Rule**: Only derivable if the text explicitly states a number of days after a fixed year-end. Example: `"Landlord delivers annual reconciliation within 120 days of calendar year-end."` → next occurrence is `next December 31 + 120 days`.
- **Skip if**: Text is absent, or uses phrases like "as soon as practicable", "promptly", or does not anchor to a fixed year-end.
- **Summary**: `CAM Reconciliation Due — <Tenant Name>`
- **Category**: OTHER
- **Note**: Do not attempt to parse fiscal-year anchors ("within 120 days of fiscal year-end") unless `LeaseYearDefinition` is also populated with a fiscal anchor date.

### 2.6 TI Allowance Drawdown Deadline — **skip unless explicit**

- **Source fields**: `Financials.TIAllowance.Notes`
- **Rule**: Only emit if the notes field contains an explicit date in ISO format. Do not parse prose like "within 18 months of commencement".
- **Skip reason**: `ti_drawdown_deadline_in_prose`

### 2.7 Estoppel / SNDA Response Deadlines — **never emit**

- **Why**: These are response windows triggered by landlord request, not calendar dates. Treat like ROFO/ROFR.

## 3. Data Quality Checks Per Event

For each event emitted, verify:
1. Date parses as `YYYY-MM-DD`.
2. Source field path resolves in the current `lease_state`.
3. Citation is non-empty (fixed events) or is the union of input citations (derived events).
4. Traceability entry's `validation_status` ∈ {`confirmed`, `pending`}. If `flagged` or `uncertain`, emit the event but set `notes: "source field has validation_status=<status>"` on the event.
5. Traceability entry's `confidence ≥ 0.7`. If lower, emit with `notes: "low confidence: <value>"`.

## 4. UID Stability Rules

Calendar clients deduplicate events by UID. Use this format:

```
lease-<tenant-slug>-<event-type>-<source-path-slug>-<YYYYMMDD>@leasegpt
```

- `tenant-slug` = `Parties.Tenant.Name` lowercased, non-alphanumerics → `-`, collapsed.
- `source-path-slug` = `source_field_path` with `.` → `-` and `[i]` → `-i-`.
- `YYYYMMDD` = event date, no separators.

Example: `lease-coastline-stationery-llc-lease_expiration-dates-expirationdate-20320531@leasegpt`

Stability guarantees:
- Re-running on the same `lease_state` produces identical UIDs.
- Re-running after an amendment that shifts a date produces a NEW UID (because the date changed) and the client shows it as a new event. This is desired — the old event should be manually removed if the deadline moved, because treating it as an update would silently overwrite a reminder the user may have already actioned.

## 5. Skipped Events Reasons (Canonical Strings)

Record these exact strings in the manifest `skipped[].reason` field so downstream tooling can parse them:

- `missing_source_field`
- `missing_notice_period`
- `missing_expiration_date`
- `trigger-based, no fixed date`
- `notice_period_in_prose`
- `ti_drawdown_deadline_in_prose`
- `reconciliation_anchor_undefined`
- `termination_right_disabled`
- `low_confidence_below_threshold`

## 6. Non-Events (Things This Skill Does NOT Emit)

- **Move-in / fit-out milestones**: not in the v4 schema.
- **Insurance certificate renewal**: requires a COI-effective-date field not currently modeled.
- **Rent roll projections**: use `lease-export` for that.
- **Option value analyses**: use `lease-abstract` or `lease-risk`.
- **Events sourced from `pending_fields`**: a pending field has no confirmed value. Do not guess.
