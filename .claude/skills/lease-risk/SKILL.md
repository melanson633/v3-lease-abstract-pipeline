---
name: lease-risk
description: >
  Scan validated lease_state data for known commercial lease risk patterns and
  emit a structured risk register in markdown + JSON manifest form.
  TRIGGER when: user asks for "risk register", "flag review", "risk scan",
  "lease risks", "exposure", or to formalize flag:/observation: findings.
  DO NOT TRIGGER when: user asks for extraction, abstract-only output, PDF
  render, CSV/Excel export, conformance eval, calendar feed, diff, or portfolio rollup.
---

# Risk Procedure (Markdown Register + JSON Manifest)

## Role
Guide **shortcut.ai_cre** to detect known lease risk patterns directly from `lease_state` and traceability metadata, then output a transparent, rule-based risk register. This skill summarizes risk signals; it does not provide legal advice.

Hard constraints (single-tenant rule, sequential supersession, per-field traceability): per CLAUDE.md.
Confidence scale, validation status enum, citation format, date conventions: per `config/shared_constants.md`.
Detection logic and formulas: `references/risk_patterns.md`.

## Inputs
- `CANDIDATE_JSON` (required): extraction object containing `lease_state` and `traceability`.

## Outputs
- `risk_register_markdown`: human-readable register, possibly empty.
- `risk_manifest_json`: machine-readable findings with evidence, severity, and rule-based exposure.

## Workflow

### 1. Parse and gate inputs
1. Parse `CANDIDATE_JSON`; locate `lease_state` and `traceability.extractedFieldsMetadata`.
2. If either is missing, stop and return `missing_required_input`.
3. Load detection rules from `references/risk_patterns.md`.

### 2. Run rule checks
Evaluate each required pattern set:
- co-tenancy triggers
- go-dark rights
- kick-out rights
- exclusive use conflicts
- uncapped CAM / missing CAM cap
- structural obligations on tenant
- guaranty burn-off timing
- absent personal guaranty on high-dollar lease
- past-due notice deadlines (calendar cross-reference)
- low-confidence critical fields (`confidence < 0.7` for rent/dates/RSF)
- `validation_status` of `flagged` or `uncertain` on financial fields

Each hit must include:
- `risk_code`
- `severity`
- `finding`
- `evidence_paths`
- `citations`
- `exposure_formula` and optional `estimated_exposure`
- `recommended_follow_up` (operational only, no legal advice)

### 3. Compute exposure safely
1. Apply only formulas documented in `risk_patterns.md`.
2. If required numeric inputs are missing, emit severity without dollar estimate and set `exposure_status = input_missing`.
3. Never invent assumptions or unstated multipliers.

### 4. Emit markdown register
Include columns in this order:
1. Risk Code
2. Severity
3. Finding
4. Evidence
5. Exposure (Rule-Based)
6. Follow-up

If zero findings, output: `No rule-triggered risks detected for the provided lease_state.`

### 5. Emit JSON manifest
Provide:
- `tenant`
- `generated_at`
- `finding_count`
- `findings` (array)
- `warnings`
- `legal_disclaimer` (`"Operational risk summary only; not legal advice."`)

## Validation
- All findings must map to rules in `references/risk_patterns.md`.
- Every populated evidence path must resolve in `lease_state`.
- Citation strings must follow shared constants format.
- Exposure values must include formula + inputs used.

## Error Handling
- **Malformed JSON**: stop with parser error.
- **Missing traceability metadata**: emit findings with `citation_unavailable` warning; do not fabricate citations.
- **Ambiguous prose trigger**: skip with `skipped_ambiguous_or_null_input`.
- **No findings**: valid zero-risk output, not an error.

## Prerequisites
- Best run after `lease-eval` PASS/WARN so confidence and validation metadata are available.
- For deadline-related risks, optionally cross-reference `lease-calendar` output if already generated.

## Worked Example (fixture `golden_ol_a1`)
Dry-run expectation: empty register. The fixture is intentionally clean and should return `finding_count = 0` with no severity rows.

## Follow-on Work
- Add portfolio-level risk stacking in `lease-portfolio` (separate skill).
- Add configurable materiality thresholds by asset class.
