---
name: lease-eval
description: >
  Validate extraction outputs against the v4 unified schema and compare against
  golden fixtures to catch regressions. Produces a conformance report covering
  schema compliance, citation coverage, traceability completeness, and
  change_log coherence.
  TRIGGER when: user asks to "validate", "check", "conformance", "regression
  test", "golden fixture", "eval", or wants to verify an extraction JSON is
  well-formed before downstream use.
  DO NOT TRIGGER when: user asks to extract, abstract, render PDF, or export
  CSV/Excel — those are separate skills and eval runs *on* their outputs.
---

# Evaluation Procedure (Schema Conformance + Golden Fixture Diff)

## Role
Guide **shortcut.ai_cre** when validating a candidate `lease_state` JSON against the v4 unified schema and, optionally, against a named golden fixture. This is the regression-safety harness for the extraction pipeline: every schema bump, prompt change, or new downstream skill (portfolio/diff/calendar/risk) should run its inputs through `lease-eval` first.

Hard constraints (single-tenant rule, sequential supersession, per-field traceability): per CLAUDE.md.
Confidence scale, validation status enum, citation format, date conventions: per `config/shared_constants.md`.

## Inputs
- `CANDIDATE_JSON` (required): A candidate extraction output — a JSON object containing `lease_state` plus optionally `change_log`, `pending_fields`, and `traceability`. Can be a fresh `lease-extract` result, a user-supplied file, or a downstream skill's upstream input.
- `GOLDEN_FIXTURE_NAME` (optional): Name of a fixture under `fixtures/` (e.g., `golden_ol_only`, `golden_ol_a1`). When provided, eval runs a structural diff against the fixture's `lease_state.json`.
- `SCOPE` (optional, default = `full`): `schema_only` | `provenance_only` | `full`. Lets the user run a fast subset when iterating.

## Output Objects
- `conformance_report`: Structured JSON with per-check results (see §6).
- `diff_report` (only when `GOLDEN_FIXTURE_NAME` provided): Field-level diff between candidate and golden, classified as `match`, `value_mismatch`, `candidate_only`, `golden_only`.
- `summary`: Short markdown block with pass/fail verdict and the top 5 issues (if any).

No scoring rubric yet — this is the minimal MVP. A precision/recall scorer is a planned follow-on; do not invent one now.

## Workflow

### 1. Load Inputs
1. Parse `CANDIDATE_JSON`. If parsing fails, emit a single error result with the JSON parser message and stop.
2. Locate `lease_state`, `change_log`, `pending_fields`, and `traceability` — they may be nested under a top-level object or provided side-by-side. Normalize to the extraction output shape documented in `lease-extract/SKILL.md` §Output Objects.
3. If `GOLDEN_FIXTURE_NAME` is provided, load `fixtures/<name>/lease_state.json` and `fixtures/<name>/README.md` (source-notes). If the fixture is missing, emit a single error and stop.

### 2. Schema Conformance Check (always runs)
Load `../lease-extract/references/v4_unified_schema.json` and validate the candidate `lease_state` against it. For each violation, record:
- `path`: dot-notation schema path
- `error`: one of `type_mismatch`, `missing_required`, `enum_violation`, `format_violation`, `additional_property`
- `expected`, `actual`: minimal reproducer

Notes:
- The v4 schema uses nullable types (`["string", "null"]` etc.) so `null` is always acceptable where the schema allows it.
- Do not treat an absent optional field as a violation — only required fields and type/enum/format mismatches count.
- Date fields with `format: "date"` must match `YYYY-MM-DD`; date-time must be ISO 8601.

### 3. Citation & Traceability Coverage (skip if SCOPE = `schema_only`)
For every **populated** leaf field in `lease_state` (non-null scalars, non-empty arrays), require a corresponding entry in `traceability.extractedFieldsMetadata` keyed by the same dot-notation path. For each covered field, verify:
- `citation` is present and matches the format `DOC pPAGE REF` (per `config/shared_constants.md`). Accept documents `OL`, `CM`, `A1..A9`, `EX-[A-Z]`, or `SL[1-9]` for side letters. Page segment is `p\d+` and reference segment is optional.
- `confidence` is a number in `[0.0, 1.0]`.
- `validation_status` is one of the five enum values from `shared_constants.md`.

Report per-field gaps as:
- `missing_traceability` — populated field with no metadata entry.
- `malformed_citation` — metadata exists but citation doesn't parse.
- `confidence_out_of_range`, `status_invalid` — self-explanatory.

Also emit aggregate coverage stats: `populated_fields`, `covered_fields`, `coverage_pct` (covered/populated). Do not define a pass threshold here; the summary just surfaces the number.

### 4. Change Log Coherence (skip if SCOPE = `schema_only`)
For every entry in `change_log`:
- `field_path` must resolve to a valid path in the v4 schema (walk the schema, arrays indexed numerically or by `[]` wildcard).
- `effective_date` must be `YYYY-MM-DD` if present.
- `source_document` and `citation` must be present together or both absent.
- `new_value` must equal the current value at `field_path` in `lease_state` **for the most recent change on that path** (supersession rule). Earlier changes in the log for the same path are historical and are not checked against current state.

Report coherence failures as:
- `path_not_in_schema`
- `current_state_mismatch` — last-write on path doesn't match `lease_state`
- `malformed_effective_date`
- `incomplete_citation_pair`

### 5. Pending Fields Sanity (skip if SCOPE = `schema_only`)
For every entry in `pending_fields`:
- `path` must resolve in the schema.
- The corresponding value in `lease_state` should be `null` (or absent); a pending field with a populated value is a contradiction. Report as `pending_but_populated`.

### 6. Golden Fixture Diff (only if `GOLDEN_FIXTURE_NAME` provided)
Walk both candidate and golden `lease_state` in parallel:
- Same path, same value → `match` (do not list individually; count only).
- Same path, different values → `value_mismatch` with `candidate`, `golden`.
- Path only in candidate → `candidate_only`.
- Path only in golden → `golden_only`.

Normalize before comparison:
- Trim whitespace in strings.
- Compare numbers with tolerance `1e-9` (exact for integers, tiny epsilon for floats).
- Dates compared lexically after normalizing to `YYYY-MM-DD`.
- Arrays of objects: match by index (order-sensitive). Rent schedules and change_logs are ordered by design.

Diff is structural only — this is NOT a scoring rubric. Surface-level mismatches are expected when the candidate is a new extraction; the purpose of the diff is to make regressions visible, not to grade.

### 7. Conformance Report Assembly
Emit a single fenced `json` block with this shape:

```json
{
  "schema_version": "4.0.0",
  "candidate_summary": {
    "tenant_name": "…",
    "populated_fields": 0,
    "covered_fields": 0,
    "coverage_pct": 0.0
  },
  "checks": {
    "schema_conformance": { "pass": true, "violations": [] },
    "citation_and_traceability": { "pass": true, "issues": [] },
    "change_log_coherence": { "pass": true, "issues": [] },
    "pending_fields_sanity": { "pass": true, "issues": [] }
  },
  "golden_diff": null,
  "verdict": "PASS | WARN | FAIL"
}
```

Verdict rules:
- `FAIL` — any schema conformance violation, or any `current_state_mismatch` in change log.
- `WARN` — any non-schema issue (missing traceability, malformed citation, pending-but-populated, golden diff non-empty).
- `PASS` — all checks clean.

Follow the JSON block with a short markdown summary: verdict, top 5 issues (if any), and a single-line instruction on what to fix first. Keep it under 20 lines.

## Fixtures Layout
Fixtures live under `fixtures/<name>/` and follow this structure:

```
fixtures/
  golden_ol_only/
    README.md          # anonymized source description + intent of the fixture
    lease_state.json   # hand-labeled lease_state matching v4 schema
  golden_ol_a1/
    README.md
    lease_state.json
    change_log.json    # present when fixture exercises amendments
```

**Adding a fixture**: hand-label it, run `lease-eval` on it with `SCOPE=full` and no `GOLDEN_FIXTURE_NAME` — the fixture must self-conform (PASS verdict) before being committed. A fixture that fails its own schema check is a bug in the fixture, not the skill.

**Do not commit real lease data.** All fixtures must be anonymized: fictional tenant/landlord names, fictional addresses, fictional dollar amounts. The `README.md` must declare `ANONYMIZED: true`.

## Error Handling
- **Malformed CANDIDATE_JSON**: report the parser error and stop. Do not attempt to guess.
- **Missing schema file**: report the path searched and stop. This indicates repo corruption.
- **Fixture not found**: list available fixture names from `fixtures/` and stop.
- **Ambiguous candidate shape**: if `lease_state` cannot be located in the input, ask the user to confirm the top-level structure rather than guessing.

## Prerequisites
- The v4 schema at `../lease-extract/references/v4_unified_schema.json` must exist. This skill does not ship its own copy; it always reads the canonical schema from `lease-extract` to guarantee they stay in sync.
- `lease-eval` does not produce any user-facing deliverable on its own. Its output is meant to gate the other skills. If the user wants a report to share with stakeholders, run `lease-abstract` or `lease-export` on the same candidate after `lease-eval` returns PASS.

## Follow-on Work (Not in this MVP)
These are planned but explicitly out of scope for the initial skill:
- Per-field precision/recall scoring against golden fixtures.
- Confidence calibration check (do high-confidence fields actually match golden more often than low-confidence ones?).
- Golden-corpus growth tooling (fixture generator, fixture linter).
- CI wiring — for now the skill runs interactively on request.
