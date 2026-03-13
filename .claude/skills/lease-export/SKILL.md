---
name: lease-export
description: >
  Export validated extraction JSON as CSV or Excel workbooks with full
  provenance columns (citation, confidence, validation_status).
  TRIGGER when: user asks for "CSV", "Excel", "export", "rollup",
  "spreadsheet", or tabular output from extraction data.
  DO NOT TRIGGER when: user asks for extract/JSON, abstract/summary, PDF/render.
---

# Export Procedure (CSV/Excel)

> Convert validated extraction outputs (`lease_state`, `change_log`) into tabular exports (CSV and/or XLSX) suitable for underwriting, asset management, and property management workflows.

Key principles: schema-aligned columns, consistent units, citations preserved, explicit handling of missing/low-confidence fields.

Hard constraints: per CLAUDE.md.
Confidence scale, validation status, citation format, date conventions: per `config/shared_constants.md`.

## 1) Inputs
- `lease_state` (JSON; preferably `ValidationStatus == PASSED`)
- `change_log` (JSON array)
- `output_type` (optional): `csv`, `xlsx`, or both
- Optional: list of prior tenant JSONs for rollups (`lease_state[]` + `change_log[]`)

## Prerequisites
- Extraction JSON is required. If missing, inform the user to run extraction first (lease-extract skill).
- If `ValidationStatus != PASSED`, proceed only if user agrees; mark outputs with `VALIDATION_WARNING`.

## 2) Outputs
### 2.1 Single-Tenant
- **XLSX** (preferred): multi-sheet workbook
- Optional **CSVs**: one per sheet OR a single "flat" export

### 2.2 Multi-Tenant Rollup (only when multiple JSONs provided)
- One workbook with:
  - `Portfolio_Summary` (one row per lease)
  - Optional schedule tabs (Rent Schedule, Options) normalized across leases
- Never "extract multiple tenants" in one run (per CLAUDE.md single-tenant rule). Rollups aggregate **prior** extraction outputs only.

## 3) Export Conventions (Must Follow)

### 3.1 Column Naming
- Use schema paths when possible (e.g., `Financials.BaseRent.CurrentRate.Value`)
- For schedule tables, use human columns plus an optional `field_path` column.

### 3.2 Mandatory Provenance Columns (where applicable)
For each exported fact row (or key fields in summary):
- `value`, `citation`, `confidence`, `source_document` (Doc ID: OL/CM/A1...), `effective_date` (if relevant), `notes` (optional)

### 3.3 Standard Formats
- Dates: `YYYY-MM-DD` (per `config/shared_constants.md`)
- Currency: numeric columns store numbers; display formatting may show `$` in XLSX
- Percentages: decimals (0.125) or percent (12.5) — choose one and be consistent; document choice in header note
- RSF: numeric

## 4) Single-Tenant Workbook Layout (Recommended)

### Sheet: `Summary`
One-row "key facts" for quick ingestion:
- Tenant legal name, Landlord legal name, Premises address, RSF
- Commencement date / Expiration date
- Current base rent (annual + monthly + $/RSF)
- Additional rent structure (NNN / MG / Gross)
- Security deposit, Renewal options summary, Guarantor summary
- Provenance columns for critical fields (dates, RSF, base rent, additional rent)

### Sheet: `Key_Dates`
Rows for: execution, commencement, expiration, option windows, rent step dates.
Columns: `date_type`, `date_value`, `citation`, `confidence`, `notes`

### Sheet: `Rent_Schedule`
Normalized rent steps.
Columns: `period_label`, `start_date`, `end_date`, `annual_rent`, `monthly_rent`, `psf_annual`, `escalation_type` / `escalation_rate` / `frequency` (if applicable), `citation`, `confidence`, `effective_date`

### Sheet: `Additional_Rent`
CAM/Opex/Taxes/Insurance/utilities terms.
Columns: `category` (CAM, Taxes, Insurance, Utilities, Other), `structure` (NNN/MG/Gross/Other), `definition`, `base_year`, `cap`, `exclusions`, `citation`, `confidence`

### Sheet: `Options`
Renewal / expansion / ROFO/ROFR / termination options.
Columns: `option_type`, `term`, `notice_period`, `notice_start_date`, `notice_end_date`, `rent_adjustment_method`, `conditions`, `citation`, `confidence`

### Sheet: `Maintenance_Matrix`
Landlord vs tenant responsibilities.
Columns: `responsibility_area`, `landlord_responsibility`, `tenant_responsibility`, `citation`, `confidence`

### Sheet: `Compliance_Flags`
Columns: `flag`, `description`, `citation`, `confidence`

### Sheet: `Change_Log`
Direct export of `change_log`.
Columns: `field_path`, `old_value`, `new_value`, `effective_date`, `source_document`, `citation`, `impact_notes`

## 5) Multi-Tenant Rollup Rules
### 5.1 Inputs
User must provide multiple `lease_state` objects (attachments or prior outputs).

### 5.2 Normalization
- `Portfolio_Summary`: one row per lease, consistent columns.
- Schedule tabs: include `lease_id` or `tenant_legal_name` + `premises_address` as join keys. Keep columns identical across leases; missing fields become null/blank.
- Do **not** infer missing fields to "complete" the rollup.

## 6) Validation & Error Handling
### 6.1 Checks
- Rent schedule: monthly = annual/12 (where values present)
- Pro-rata: tenant_rsf / building_rsf if both present
- Missing citations: flag in a `Warnings` sheet or column

### 6.2 Failure Mode
If export cannot be generated:
- Return structured error report: missing prerequisites, schema mismatch issues, recommended next action (run extraction first, upload missing docs, etc.)

## 7) Output (When Responding)
- Attach file(s) and provide:
  - List of sheets generated
  - Row counts per sheet
  - Warnings summary (<=5 bullets)
- Keep narrative short; exports are the primary deliverable.
