# Risk Patterns Reference

## Severity Tiers
- **Critical**: immediate monetary/default exposure likely.
- **High**: material downside possible; near-term monitoring required.
- **Medium**: meaningful but bounded operational/financial risk.
- **Low**: informational or contingent risk.

## Exposure Formula Policy
- Use explicit formulas only.
- If a required input is null/missing, return severity without dollar amount.
- Never provide legal advice or legal conclusions.

## Detection Rules

### 1) Co-tenancy trigger
- Trigger when `Options.CoTenancy` is populated with threshold/failure language.
- Severity: High.
- Exposure formula: `annual_rent * trigger_discount_pct` when both are known.

### 2) Go-dark right
- Trigger when `Options.GoDarkRights` is populated/allowed.
- Severity: High.
- Exposure formula: `remaining_rent_years * annual_rent`.

### 3) Kick-out right
- Trigger when `Options.TerminationOptions` includes sales-threshold termination rights.
- Severity: High.
- Exposure formula: `unamortized_TI + leasing_downtime_cost` (only if both inputs exist).

### 4) Exclusive use conflicts
- Trigger when `Options.ExclusiveUseRights` exists and known conflicting users are identified in notes.
- Severity: Medium.
- Exposure formula: notional only unless penalty language extracted.

### 5) Uncapped CAM / missing CAM cap
- Trigger when recovery type is NNN or expense pass-through and `Financials.AdditionalRent.CAMCap` is null.
- Severity: Medium.
- Exposure formula: none (open-ended unless cap/estimate exists).

### 6) Structural obligations on tenant
- Trigger when `Clauses.Maintenance.TenantResponsibilities` includes structural elements (roof/foundation/load-bearing).
- Severity: High.
- Exposure formula: none unless capped reimbursement is extracted.

### 7) Guaranty burn-off timing
- Trigger when guaranty exists and burn-off condition is late/unclear.
- Severity: Medium.
- Exposure formula: `remaining_guaranty_months * monthly_base_rent` (if available).

### 8) Missing personal guaranty on high-dollar lease
- Trigger when annual base rent exceeds materiality threshold and `Parties.Guarantor` is null.
- Severity: Medium.
- Exposure formula: `annual_rent` (single-year proxy).
- Default materiality threshold: `$250,000 annual base rent` unless user overrides.

### 9) Past-due notice deadlines (calendar cross-check)
- Trigger when any computed notice deadline is before reference date.
- Severity: Critical for missed hard options; High otherwise.
- Exposure formula: option-specific; often none if unknown.
- Cross-reference source: `lease-calendar` manifest if supplied.

### 10) Low-confidence critical fields
- Trigger when confidence `< 0.7` on:
  - `Dates.CommencementDate`
  - `Dates.ExpirationDate`
  - `Premises.RSF`
  - `Financials.BaseRent.Schedule[*].annualAmount` or `monthlyAmount`
- Severity: High (dates/rent), Medium (RSF).
- Exposure formula: none; data-quality risk.

### 11) Financial field validation warnings
- Trigger when any financial metadata has `validation_status` in `{flagged, uncertain}`.
- Severity: High for base rent fields; Medium for ancillary charges.
- Exposure formula: none unless mismatch delta is computable.

## Citation Templates
- Single source: `A1 p2 §3`
- Multi-source derived: `OL p8 §5.2; A1 p1 §2`
- Missing citation fallback: `citation_unavailable`

## Canonical Skip Reasons
- `skipped_ambiguous_or_null_input`
- `skipped_missing_formula_inputs`
- `skipped_no_calendar_cross_reference`
