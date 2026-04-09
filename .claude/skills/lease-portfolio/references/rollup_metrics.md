# Portfolio Rollup Metrics Reference

## 1) Join Keys / Lease Identity
- Preferred key: `Parties.Tenant.Name + Premises.Address + Dates.OriginalLeaseDate`.
- If duplicate keys appear, append deterministic ordinal and warn.

## 2) WALT Formula
- Remaining term in years per lease: `(ExpirationDate - ReferenceDate) / 365.25`.
- Primary weighting: RSF.
- Formula: `WALT = sum(remaining_term_years * weight) / sum(weight)`.
- Fallback weight: annual base rent when RSF missing.

## 3) Expiration Ladder Buckets
Use years-to-expiration buckets:
- `<1 year`
- `1-2 years`
- `3-5 years`
- `6-10 years`
- `>10 years`

## 4) Rent Roll by Year
- For each lease schedule period, map `annualAmount` to overlapping calendar year(s).
- If schedule granularity is yearly and aligned to lease years, assign to the schedule start year for MVP.
- Aggregate totals by year across leases.

## 5) Tenant Concentration
- Share by tenant: `tenant_annual_rent / total_portfolio_annual_rent`.
- Report top tenant and top-3 cumulative share.
- If annual rent unavailable for a lease, exclude from concentration denominator and warn.

## 6) TI + Security Deposit Exposure
- `total_ti_allowance = sum(Financials.TIAllowance.Amount where populated)`
- `total_security_deposit = sum(Financials.SecurityDeposit.Amount where populated)`
- Also report lease-level contributions.

## 7) Missing-Field Handling
- Never impute missing numeric values.
- Exclude missing fields metric-by-metric and log one canonical reason:
  - `missing_expiration_date`
  - `missing_rsf_and_rent_weight`
  - `missing_rent_schedule`
  - `skipped_ambiguous_or_null_input`
