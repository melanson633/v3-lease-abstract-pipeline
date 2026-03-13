# schema_priority_map.md (v0.3)
# Purpose: latency-safe priority mapping for LeaseGPT (shortcut.ai_cre)
# How it's used:
# - This file is a Knowledge File that guides "progressive extraction" without runtime schema traversal.
# - The canonical schema remains v4_unified_schema.json (v4.0.0); this is a *priority* and *routing* layer only.

## Conventions
- Paths use dot notation matching schema keys. Arrays are marked with [] (e.g., Financials.BaseRent.Schedule[].monthlyAmount).
- “Extract” means: populate field value + include traceable citation(s) + confidence.
- If a value cannot be confirmed (e.g., commencement is definition-based and depends on a later memo), leave the date null and capture the *definition* in Notes / relevant descriptive field, plus mark as Pending in your output’s pending_fields list (per procedure).

---

Citation format, confidence scale, and validation status: per `config/shared_constants.md`.

## Confidence Targets by Pass
- **Pass 1 fields:** >=0.9 for core terms (rent, dates, parties). Definition-only dates get confidence 0.0, status `pending`.
- **Pass 2 fields:** >=0.7. Summary-first approach acceptable.
- **Pass 3 fields:** Extract-if-present; confidence reflects clarity of source language.

## Pass 1 Blocking vs Non-Blocking
- **Blocking fields** (must attempt before outputting Pass 1): Parties.Tenant.Name, Parties.Landlord.Name, Premises.Address, Premises.RSF, Dates.CommencementDate (or DateNotes if definition-only), Financials.BaseRent.Schedule, Clauses.Use
- **Non-blocking fields** (best-effort in Pass 1): Parties.Guarantor.Name, Premises.Parking, Dates.TermMonths, Options.RenewalOptions

---

## PASS 1 — Critical Business Terms (timeboxed "must attempt")
Goal: deliver a usable first output quickly (parties + premises + dates/term + full rent schedule + core deposits/options).
If any Pass 1 items are blocked by graphics/OCR limits, output null + Pending reason + what doc/exhibit to request.

### A) Parties (identify who is who)
- Parties.Landlord.Name
- Parties.Tenant.Name
- Parties.Guarantor.Name (if present)
Optional (only if clearly stated / quick):
- Parties.Landlord.EntityType, Jurisdiction
- Parties.Tenant.EntityType, Jurisdiction

### B) Premises (what/where/how big)
- Premises.Address
- Premises.Suite
- Premises.RSF
Nice-to-have if explicit:
- Premises.BuildingName
- Premises.SpaceUseType
- Premises.Parking.Spaces / Type / Cost (only if clearly specified)

### C) Dates / Term (with “definition-first” rule)
- Dates.LeaseExecutionDate (if explicitly dated)
- Dates.OriginalLeaseDate (if explicitly dated)
- Dates.CommencementDate (ONLY if explicitly stated as a date; otherwise leave null and flag Pending)
- Dates.RentCommencementDate (same rule)
- Dates.ExpirationDate (ONLY if explicitly stated as a date; otherwise leave null and flag Pending)
- Dates.TermMonths (if explicitly stated)
- Dates.LeaseYearDefinition (if defined)

**Definition-first rule (worked example):**
If the lease says 'Commencement Date shall be the date that is 6 months after Lease Execution': leave `Dates.CommencementDate = null`, record `Dates.DateNotes = '6 months from lease execution per OL §2.1'`, add to `pending_fields`, set validation_status to `pending`.

### D) Base Rent — FULL RENT SCHEDULE (required in Pass 1)
- Financials.BaseRent.EscalationMethod (if stated: fixed/CPI/etc.)
- Financials.BaseRent.CommencementDate (if explicitly stated as date; otherwise null)
- Financials.BaseRent.Schedule[]  (capture the entire table/steps):
  - Financials.BaseRent.Schedule[].period
  - Financials.BaseRent.Schedule[].startDate
  - Financials.BaseRent.Schedule[].endDate
  - Financials.BaseRent.Schedule[].monthlyAmount
  - Financials.BaseRent.Schedule[].annualAmount
  - Financials.BaseRent.Schedule[].baseRentPSF
Notes for tables:
- Preserve “Year 1/Year 2…” semantics exactly (period column).
- If table has partial columns, fill what’s present; don’t invent.

### E) Allowance "pegs" that appear on the rent table (CAM/Tax allowances)
Important constraint from user: include allowance/peg amounts when present on the rent table, but do not deep-dive recovery mechanics in Pass 1.

**CAM allowance routing clarification:**
- If the table shows a single 'Expense Stop' or 'Base Year Stop': route to `Financials.AdditionalRent.ExpenseStopAmount`.
- If the table shows separate CAM/Tax/Insurance allowances: route each to `Financials.AdditionalRent.OtherCharges[]` with the exact label as `Name`.
- Do NOT route these to `Financials.AdditionalRent.ExpenseStructure` in Pass 1; expense detail extraction happens in Pass 2.

Routing:
1) If the table clearly labels an “Expense Stop” amount:
   - Financials.AdditionalRent.ExpenseStopAmount
2) Otherwise, record peg line items as:
   - Financials.AdditionalRent.OtherCharges[] with:
     - Name = exact label (“CAM Allowance”, “Tax Allowance”, “Expense Allowance”, etc.)
     - Amount = numeric amount shown
     - Description = short clarification only if needed (e.g., “from rent schedule table”)

### F) Abatement / Free Rent (if present and clear)
- Financials.BaseRent.Abatement.Schedule[] (if described as discrete free-rent periods):
  - period
  - monthsFree
  - amount
  - reason

### G) Security / TI / Prepaid (core cash terms)
- Financials.SecurityDeposit.Amount
- Financials.SecurityDeposit.Form
- Financials.TIAllowance.Amount
- Financials.TIAllowance.RatePerSF (if given)
- Financials.PrepaidRent.Amount (if given)

### H) Payment / Late / Holdover (only if explicit)
- Financials.PaymentTerms.Frequency
- Financials.PaymentTerms.DueDate
- Financials.LateFees.RatePercent / FlatAmount / RateDescription
- Financials.LateFees.GracePeriodDays
- Financials.Holdover.Multiplier

### I) Options (renewal first; capture structure)
- Options.RenewalOptions.NumberOfOptions
- Options.RenewalOptions.TermMonthsPerOption[]
- Options.RenewalOptions.NoticePeriodDays
- Options.RenewalOptions.RentAdjustmentMethod
If any option requires “exercise notice” timing, also capture:
- Dates.NoticePeriods.RenewalNoticeDays (when explicitly defined as a general notice period)

### J) Use clause (high-signal)
- Clauses.Use

---

## PASS 2 — Financial + Operating Expansions (subtree-driven, not leaf-exhaustive)
Goal: broaden coverage *without forcing every field*.
Rule: Prefer extracting the “headline” fields first; only drill down if the clause is clearly present.

### A) Additional Rent (recoveries) — capture the frame, not every detail
Start with:
- Financials.AdditionalRent.RecoveryType
- Financials.AdditionalRent.ProRataShare
- Financials.AdditionalRent.BaseYears.(OperatingExpenses, Taxes) (if stated)
Then expand only as present:
- Financials.AdditionalRent.ExpenseStructure (OperatingExpenses / Taxes / Insurance / Utilities / AdminManagementFee)
- Financials.AdditionalRent.CAMCap (Percent / Scope)
- Financials.AdditionalRent.BillingCycle
- Financials.AdditionalRent.ReconciliationTerms
- Financials.AdditionalRent.AuditRights

### B) Insurance (summary-first)
Start with:
- Clauses.Insurance.Summary
Then expand only if spelled out:
- Clauses.Insurance.TenantRequirements
- Clauses.Insurance.LandlordRequirements

### C) Maintenance / Repairs (responsibility allocation)
- Clauses.Maintenance.TenantResponsibilities
- Clauses.Maintenance.LandlordResponsibilities
- Clauses.Maintenance.SharedResponsibilities (includes structural, building systems, interior, common area, thresholds, step-in rights)

### D) Utilities (only as present; keep concise)
- Utilities.Summary
- Utilities.ResponsibilityAllocation

### E) Assignment/Subletting (deal-critical risk flag)
- Clauses.AssignmentAndSubletting.Allowed
- Clauses.AssignmentAndSubletting.Restrictions
Optional if clearly present:
- ProfitSharing, PermittedTransfers, RecaptureRight, OriginalTenantLiability, ConditionsForConsent

---

## PASS 3 — Legal / Edge Clauses + Compliance Flags (extract-if-present; don’t bloat)
Goal: capture “watch-outs” and legal mechanics in a compact, citeable way.

Extract if present (usually as short summaries, with citations):
- Clauses.GoverningLaw
- Clauses.DefaultRemedies.(EventsOfDefault, CurePeriodDays, Remedies)
- Clauses.Guaranty.(Guarantor, Terms, Scope, BurnOff)
- Clauses.HazardousMaterials
- Clauses.Condemnation
- Clauses.DamageDestruction
- Clauses.EnvironmentalCompliance (includes ADA/disability access)
- Clauses.SNDA
- Clauses.Estoppel
- Clauses.Notices
- Clauses.Signage
- Clauses.ForceMajeure
- Clauses.DisputeResolution
- Clauses.OtherClauses

Options (non-renewal) — only if the lease actually includes them:
- Options.(ExpansionRights, TerminationOptions, RightOfFirstOffer, RightOfFirstRefusal, ExclusiveUseRights, CoTenancy, GoDarkRights, ContractionOption, PurchaseOption)

---

## Stop Conditions / Defer Rules (latency + correctness guardrail)
- If Pass 1 is complete (or clearly blocked with Pending flags), STOP and output.
- Do not "hunt" for Pass 2/3 items unless time remains in the budget or the user requests deeper extraction.
- Graphic-heavy exhibits/site plans:
  - Do not OCR-loop.
  - If a key Pass 1 value depends on a graphic exhibit, leave null + Pending and request the specific exhibit in text form (or a typed confirmation).

---

## pending_fields Structure
When a field cannot be extracted, add it to the `pending_fields` array:
```json
{
  "path": "Dates.CommencementDate",
  "reason": "Definition-based; no CM provided to confirm actual date",
  "where_to_find": "Commencement Memo or landlord confirmation letter",
  "hint": "Lease defines commencement as 6 months after execution (OL §2.1)"
}
```

## change_log Population Guidance
- **Pass 1:** Record all changes found when processing CM and amendments against OL values for Pass 1 fields.
- **Pass 2:** Record changes to financial/operating terms. Include impact_notes for rent changes, cap changes, recovery type changes.
- **Pass 3:** Record changes to legal clauses. Impact_notes should flag material risk changes.
- Even if no amendments are provided, output `change_log: []` (empty array, not omitted).

---

Single-tenant rule and document precedence: per CLAUDE.md hard constraints.