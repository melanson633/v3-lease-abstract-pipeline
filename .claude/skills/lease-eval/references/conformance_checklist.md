# Conformance Checklist (v4.0.0)

> Layer-3 reference for the `lease-eval` skill. Lists every check the skill runs, what a failure looks like, and what the user should do about it. The skill's main procedure is in `../SKILL.md`; this file is loaded on demand when a deeper diagnostic is needed.

## 1. Schema Conformance

| Check | What it verifies | Typical failure | Fix |
|---|---|---|---|
| Type match | Each field value matches the JSON Schema type (`string`, `number`, `integer`, `boolean`, `object`, `array`, `null`). | Numeric field delivered as string (e.g., `"2500"` instead of `2500`). | Cast in the extractor; rerun `lease-extract`. |
| Enum compliance | `validation_status` is one of `confirmed`, `pending`, `uncertain`, `flagged`, `missing`. | Status `"verified"` or `"ok"`. | Map to canonical enum in extractor. |
| Date format | `format: "date"` fields match `YYYY-MM-DD`; `format: "date-time"` fields are ISO 8601. | `"06-01-2025"` in `lease_state`. | Re-normalize. Remember: JSON uses `YYYY-MM-DD`, abstracts/PDFs use `MM-DD-YYYY` (per `config/shared_constants.md`). |
| Nullable handling | Fields typed `["T", "null"]` accept `null`; required fields must not be omitted. | Omitting `Metadata` entirely. | Emit the key with a `null` or empty-object placeholder. |
| No spurious keys | Extractor did not invent schema paths. | `Financials.BaseRent.MysteryField`. | Remove or map to a schema-valid path. |

## 2. Citation & Traceability

| Check | What it verifies | Typical failure | Fix |
|---|---|---|---|
| Per-field metadata | Every populated leaf has an entry in `traceability.extractedFieldsMetadata`. | New field added to lease_state but not to traceability. | Update extractor to emit metadata alongside every write. |
| Citation format | Matches `DOC pPAGE [REF]` where DOC ∈ {OL, CM, A1..A9, EX-[A-Z], SL[1-9]}. | `"page 5"` or `"section 4.1"`. | Re-emit with canonical format from `config/shared_constants.md`. |
| Confidence range | `confidence` ∈ [0.0, 1.0]. | `confidence: 1.5` or negative. | Clamp; investigate why extractor produced out-of-range. |
| Validation status | Enum value per §1. | See above. | Same. |
| Coverage ≥ 95% | Rule of thumb, not a hard gate. `covered_fields / populated_fields ≥ 0.95`. | Extractor wrote values without citations under time pressure. | Run Pass 1 fully; uncited fields → `pending_fields`. |

## 3. Change Log Coherence

| Check | What it verifies | Typical failure | Fix |
|---|---|---|---|
| Path resolves | Every `field_path` walks cleanly in the v4 schema, including array indices. | `Financials.BaseRent.Schedule[5]` on a 5-element array (index 5 doesn't exist). | Ensure the amendment's change actually landed in `lease_state` before logging the change. |
| Current-state match | For each path, the most recent change's `new_value` equals the current value in `lease_state`. | Log says rent extended to Year 7 but `Schedule` only has 5 entries. | Forgot to update `lease_state` after appending to change_log. Re-run merge. |
| Effective date format | `YYYY-MM-DD` when present. | `"Jan 15, 2027"`. | Normalize. |
| Citation pair | `source_document` and `citation` both present or both absent. | `source_document: "A1"` with missing citation. | Fill citation or remove source_document. |
| Chronological order | Entries ordered by `effective_date` ascending within each path. (Not fatal, but surfaces as a warning.) | A1 entry before OL baseline entry. | Re-sort change_log. |

## 4. Pending Fields Sanity

| Check | What it verifies | Typical failure | Fix |
|---|---|---|---|
| Path resolves | Same as change log. | Path typo. | Fix the path. |
| Not populated | Pending means unknown; the corresponding `lease_state` value should be `null` or absent. | Value present AND listed as pending. | Decide: is it known or not? Remove from one side. |
| Actionable hint | `where_to_find` or `hint` is populated so a human reviewer can resolve it. | Both empty. | Add a location hint (exhibit name, section number, document not yet uploaded). |

## 5. Golden Fixture Diff (optional)

Only runs when `GOLDEN_FIXTURE_NAME` is provided. Produces:
- `match` count (no detail listed)
- `value_mismatch[]` — path, candidate, golden
- `candidate_only[]` — paths present in candidate but not golden
- `golden_only[]` — paths present in golden but not candidate

Interpretation:
- **Many value_mismatches**: likely a real extraction regression OR the candidate was extracted from a different document. Investigate before treating as a bug.
- **Many candidate_only**: extractor found more fields than the golden. Could mean golden is stale (add to fixture) or extractor is hallucinating (don't).
- **Many golden_only**: extractor dropped fields that were previously captured. Regression — investigate.

Diffs are structural, not graded. Do not use the diff count as a quality score.

## 6. Verdict Rules

| Verdict | Conditions |
|---|---|
| **PASS** | Zero schema violations, zero change_log current-state mismatches, zero provenance errors, empty golden diff (if run). |
| **WARN** | Any provenance issues (missing traceability, malformed citation, pending-but-populated), OR any golden diff. Schema and change-log still clean. |
| **FAIL** | Any schema conformance violation OR any change_log current-state mismatch. These block downstream skills. |

## 7. What `lease-eval` Explicitly Does Not Check (MVP)

- **Content accuracy** — does "$32.00/RSF" match what's actually written in the lease? Out of scope. That's what the golden fixture diff is for, and even then it's structural.
- **Calculation consistency** — monthly × 12 = annual, pro-rata share × building RSF = tenant RSF. The extractor already does this per `lease-extract/SKILL.md §4.1`; `lease-eval` does not re-verify.
- **Legal interpretation** — whether a clause is favorable, enforceable, or unusual. Never in scope for any LeaseGPT skill (per CLAUDE.md "No Legal Advice").
- **Precision/recall scoring** — planned follow-on. Not in the MVP.
- **Confidence calibration** — planned follow-on.
