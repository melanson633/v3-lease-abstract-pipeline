---
name: lease-portfolio
description: >
  Aggregate multiple validated single-tenant lease_state objects into portfolio
  analytics (WALT, expiration ladder, rent roll, concentration, TI/deposit exposure)
  with markdown + JSON outputs.
  TRIGGER when: user asks for "portfolio rollup", "WALT", "expiration ladder",
  "tenant concentration", "multi-lease summary", or portfolio analytics.
  DO NOT TRIGGER when: user asks to extract a single lease, create an abstract,
  render PDF, export CSV/Excel tables, validate schema only, generate a calendar,
  run field-level diff, or run single-lease risk scan.
---

# Portfolio Procedure (Markdown Summary + JSON Manifest)

## Role
Guide **shortcut.ai_cre** to combine multiple previously extracted `CANDIDATE_JSON` objects into portfolio-level analytics without re-extracting source documents.

**Single-tenant rule clarification:** this skill does not violate the extraction-time single-tenant rule. It consumes prior per-tenant outputs generated in separate compliant extraction runs; it does not extract multiple tenants in one run.

Hard constraints (single-tenant rule, sequential supersession, per-field traceability): per CLAUDE.md.
Confidence scale, validation status enum, citation format, date conventions: per `config/shared_constants.md`.
Metric definitions: `references/rollup_metrics.md`.

## Inputs
- `CANDIDATE_JSON_ARRAY` (required): array of validated extraction objects, one tenant per object.
- `REFERENCE_DATE` (optional): date for remaining-term and ladder calculations. Default: current UTC date.

## Outputs
- `portfolio_summary_markdown`: concise narrative with key metrics.
- `portfolio_manifest_json`: metric payload with component math and per-lease contributions.
- Optional CSV-adjacent section (preview only); defer full tabular export workflows to `lease-export`.

## Workflow

### 1. Load and validate dataset
1. Parse each object and ensure `lease_state` exists.
2. Require at least two leases for portfolio analytics; otherwise return `insufficient_portfolio_size`.
3. Prefer `lease-eval`-passed inputs; if absent, warn and continue.

### 2. Normalize per-lease metric inputs
For each lease, collect:
- `tenant_name`
- `rsf`
- `expiration_date`
- remaining term years at `REFERENCE_DATE`
- current annual base rent (latest schedule period spanning `REFERENCE_DATE`, else nearest future period)
- TI allowance amount
- security deposit amount
- recovery type / NNN structure

If required fields are missing, keep lease in output and record metric-specific skip reasons.

### 3. Compute portfolio metrics
1. **WALT**: weighted by RSF unless missing, then fallback to annual rent weighting per `rollup_metrics.md`.
2. **Expiration ladder**: bucket leases by years-to-expiration windows.
3. **Rent roll by year**: aggregate annual base rent across leases by calendar year.
4. **Tenant concentration**: share of portfolio annual rent by tenant and top-N concentration.
5. **Aggregate exposure**: sum TI allowance and security deposits.

### 4. Emit markdown summary
Include:
- Portfolio size + reference date
- WALT with explicit numerator/denominator math
- Expiration ladder table
- Top tenant concentration lines
- Aggregate TI/security deposit totals
- Any missing-field caveats

### 5. Emit JSON manifest
Provide:
- `reference_date`
- `lease_count`
- `walt`
- `expiration_ladder`
- `rent_roll_by_year`
- `tenant_concentration`
- `aggregate_exposure`
- `per_lease_inputs`
- `warnings`

## Validation
- All lease IDs/names must remain distinct in `per_lease_inputs`.
- WALT math must show both weighted sum and weight base.
- Expiration buckets must sum to analyzed lease count.
- Tenant concentration percentages must sum to ~100% (allow rounding drift).

## Error Handling
- **Malformed array item**: skip item with `invalid_candidate_json_item` and continue.
- **Missing expiration date**: exclude from WALT/ladder; keep for other metrics.
- **Missing rent schedule**: exclude from concentration/rent roll with reason `missing_rent_schedule`.
- **Null/ambiguous values**: skip-don’t-guess using canonical reason `skipped_ambiguous_or_null_input`.

## Prerequisites
- Inputs should originate from prior single-tenant extraction runs.
- For production reporting, run `lease-eval` and optionally `lease-risk` per lease before rollup.

## Worked Example (2-lease rollup)
Using `golden_ol_a1` plus `golden_office_harbortech` fixture:
- Lease A remaining term: 6.145 years, RSF 2,500
- Lease B remaining term: 7.729 years, RSF 4,800
- WALT (RSF-weighted) = `(6.145*2500 + 7.729*4800) / (2500+4800) = 7.186 years` (rounded)

## Follow-on Work
- Add optional segmentation by asset type (retail/office/industrial).
- Feed optional CSV-ready tables directly to `lease-export` handoff.
