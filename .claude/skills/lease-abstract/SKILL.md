---
name: lease-abstract
description: >
  Generate an investment-grade lease abstract in markdown from validated
  extraction JSON (lease_state + change_log).
  TRIGGER when: user asks for "abstract", "summary", "lease abstract",
  "investment-grade summary", or requests a human-readable lease summary.
  DO NOT TRIGGER when: user asks for extract/JSON, PDF/render, CSV/Excel/export.
---

# Abstraction Procedure

## Role
Guide **shortcut.ai_cre** when generating a polished Lease Abstract from a validated `lease_state` and associated `change_log`. Emphasize clarity, readability, and decision-readiness for different audiences and property types.

Hard constraints (single-tenant, supersession, traceability): per CLAUDE.md.
Confidence scale, validation status, citation format, date conventions: per `config/shared_constants.md`.

## Inputs
- `lease_state`: Final structured JSON from extraction. Must have validation status `confirmed` or `pending` (with acknowledged gaps).
- `change_log`: Historical modifications captured during extraction.
- `property_type`: One of `Office`, `Retail`, `Industrial`, or other. Determines emphasis areas. **If not provided, ask — do not silently default.**
- `audience`: One of `Executive`, `AssetManagement`, `PropertyManagement`, `Legal`, `Investor/Finance`, `Compliance/Regulatory`, `Marketing/Leasing`, or `Custom`. **If not provided, ask.**
- `need_PM_block` (optional, default `true`): Include detailed Property Management responsibility matrix.
- `exec_only` (optional, default `false`): If `true`, generate only the one-page Executive Fact Sheet.

### Custom Audience Handling
If user specifies `Custom` audience: fall back to generic template, ask which emphasis areas matter most, adjust section depth accordingly.

## Output
- `Lease Abstract`: A markdown document presenting a concise summary tailored to property type and audience, with change highlights and citations.

## Prerequisites
- Validated `lease_state` is required. If missing, ask the user to provide extraction output or run extraction first (if documents are available).

## Workflow

### 1. Pre-Flight Validation
1. Confirm `property_type` and `audience` are provided; if not, **ask the user**.
2. Confirm `lease_state` has been validated.
3. Summarize change log — identify most significant changes to highlight:
   - **High significance** (always highlight): rent changes, term changes, option additions/removals, security deposit changes
   - **Medium significance** (highlight if material): maintenance responsibility shifts, insurance changes, assignment/subletting modifications
   - **Low significance** (change log table only): administrative updates, notice address changes, minor clarifications

### 2. Template Selection & Layout
1. **Select Base Template** by `property_type`:
   - *Office*: Emphasize parking ratios, after-hours HVAC, expansion rights, business hours.
   - *Retail*: Emphasize percentage rent, co-tenancy, exclusive uses, foot traffic drivers.
   - *Industrial*: Emphasize loading capacities, power supply, environmental conditions, ceiling height.
   - *Other*: Generic template; ask user for custom emphasis areas.
2. **Audience Customization**:
   - *Executive*: One-page summary — critical metrics, key dates, rent structure, options, major risks/opportunities.
   - *Asset Management*: Detailed financial analysis, rent schedule table, escalation assumptions, ROI context.
   - *Property Management*: Detailed responsibility matrix, maintenance schedules, vendor requirements, operational guidance.
   - *Legal*: Compliance flags, default/remedy provisions, liabilities, dispute resolution.
   - *Investor/Finance*: Cash flows, rent escalation trends, pro-rata shares, valuation impacts.
   - *Compliance/Regulatory*: Accounting standards (ASC 842, IFRS 16), environmental compliance, municipal obligations.
   - *Marketing/Leasing*: Tenant mix, co-tenancy clauses, exclusives, synergy potential.
   - *Custom*: Generic template + user-specified emphasis areas.
3. Apply `exec_only` and `need_PM_block` flags as appropriate.

### 3. Content Generation

#### Executive Fact Sheet (Page 1)
- Concise narrative (<=400 words): parties, property address, term, lease structure, rent overview, key options. Highlight significant amendments from `change_log`.
- **Metrics Table** (columns: `Metric`, `Value`, `Citation`): lease execution date, commencement, expiration, RSF, pro-rata share, current base rent, rent structure, security deposit, options, guarantor, compliance flags.
- Compliance snapshot or highlights section.
- Insert form feed (`\f`) after Page 1.

#### Thematic Sections (Pages 2+) — Canonical Ordering
Generate up to seven sections in this order. Insert `\f` before each `## ` heading after the Executive Fact Sheet.

1. **Lease Fundamentals**: Parties, premises description, key dates, amendment summary.
2. **Rent & Security**: Term length, detailed rent schedule with escalations, additional rent structure, security deposit, late fees, holdover provisions.
3. **Additional Rent / Expenses**: Recovery type, pro-rata share, CAM charges, expense recoveries, caps, billing cycle.
4. **Options**: Renewal terms, expansion/contraction rights, termination options, ROFO/ROFR.
5. **Use / Operating Covenants**: Permitted uses, restrictions, operating hours, parking, TI, alteration rights, assignment/subletting.
6. **Maintenance & Repairs**: Landlord vs. tenant responsibility matrix (if `need_PM_block`), HVAC terms, insurance requirements, utilities.
7. **Other Key Provisions / Open Items**: Environmental obligations, SNDA/estoppel, force majeure, governing law, defaults/remedies, amendments & change log table.

#### Highlight Changes
Where `change_log` reveals major updates (rent increases, extended term), include call-out bullets with previous value, updated value, and effective date.

#### Confidence Display
For fields with confidence < 0.7, append `[confidence: X.X]` so the reader knows which values need verification.

### 4. Formatting Rules
- **Headings**: `#` = document title, `##` = thematic sections, `###` = subsections.
- **Page breaks**: Insert `\f` before each `##` after Executive Fact Sheet. Never inside tables, fenced code blocks, or between heading and first content.
- **Tables**: Max 7 columns, GitHub-flavored pipe tables. For detailed table authoring rules, read `references/style_guide_markdown.md`.
  - Metrics Table: `Metric | Value | Citation`
  - Rent Schedule: `Period | Start | End | Annual | Monthly | $/RSF | Citation`
  - Responsibility Matrix: `Area | Landlord | Tenant | Citation`
- **Dates**: Display as `MM-DD-YYYY` in abstracts (per `config/shared_constants.md`).
- **Currency**: `$1,234.56` with commas and decimals.
- **Citations**: Inline in narrative: `(OL p5 §4.1)`. In tables: dedicated Citation column.
- Blank line after each table.

### 5. Validation & QA
1. Cross-check every figure against `lease_state` with backing citation.
2. Review narrative for clarity and cohesion. Avoid legal jargon unless audience is `Legal`.
3. Confirm citation completeness for all table entries and narrative facts.
4. Self-check statement at end: abstract accurately reflects lease_state, calculations validated, content appropriate for specified audience.

### 6. Output
1. Provide lease abstract in a fenced `markdown` block with self-check statement.
2. If `output_type` is `pdf`, inform the user to request the lease-render skill for PDF conversion.
3. If abstract cannot be generated due to missing data, produce a markdown error report with issues and recommended actions.
