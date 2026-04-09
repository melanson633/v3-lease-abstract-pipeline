---
name: lease-diff
description: >
  Produce amendment-aware field diffs from change_log plus an optional reverse diff
  preview from a draft amendment. Emits a markdown diff report and a JSON manifest
  with OL -> A1 -> A2 progression, citation pairs, and overwrite impact.
  TRIGGER when: user asks for "diff", "redline from JSON", "amendment delta",
  "what changed", "change log report", or asks what a draft amendment would overwrite.
  DO NOT TRIGGER when: user asks for extraction, abstract, PDF render, CSV/Excel
  export, schema conformance, calendar generation, risk scan, or portfolio rollup.
---

# Diff Procedure (Markdown Report + JSON Manifest)

## Role
Guide **shortcut.ai_cre** when converting `change_log` history into a first-class, amendment-attributed diff deliverable. The skill must preserve chronological supersession and evidence for every change while avoiding synthetic historical reconstructions.

Hard constraints (single-tenant rule, sequential supersession, per-field traceability): per CLAUDE.md.
Confidence scale, validation status enum, citation format, date conventions: per `config/shared_constants.md`.
Detailed normalization and grouping policy: `references/diff_rules.md`.

## Inputs
- `CANDIDATE_JSON` (required): extraction object containing `lease_state`, `change_log`, and `traceability`.
- `DRAFT_AMENDMENT` (optional): structured object of proposed field updates for reverse diff preview.

## Outputs
- `diff_report_markdown`: sectioned markdown report grouped by field prefix (for stakeholder review).
- `diff_manifest_json`: machine-readable JSON with per-path timeline, citations, normalized values, and reverse-diff overwrite preview.

## Workflow

### 1. Load and normalize inputs
1. Parse `CANDIDATE_JSON` and locate `lease_state`, `change_log`, and `traceability`.
2. If `change_log` is missing, null, or empty, emit an empty diff report with reason `no_change_log_entries`.
3. Apply normalization rules from `references/diff_rules.md` before comparing values (trimmed strings, numeric epsilon, lexical date comparison).

### 2. Build chronological path timelines
1. Walk `change_log` in listed order only. Do not create a synthetic “state at date T” view.
2. For each `field_path`, initialize the timeline origin as the earliest observed `old_value`.
3. Append each change event as a transition containing:
   - `from_value`, `to_value`
   - `effective_date`
   - `source_document`
   - `citation`
   - `impact_notes`
4. Derive progression labels like `OL -> A1 -> A2` using unique source documents encountered on that path.

### 3. Group for report readability
1. Group timelines by `field_path` prefix according to `references/diff_rules.md`.
2. Maintain stable output ordering:
   - Dates
   - Financial schedule inserts/changes
   - Financial scalar updates (for example TI allowance)
   - Remaining groups alphabetically
3. Within each group, sort paths by first appearance index in `change_log`.

### 4. Render markdown diff report
For each grouped section, emit a table with canonical columns from `diff_rules.md`:
- `Field Path`
- `Progression`
- `Original`
- `Current`
- `Amendment Events`
- `Citation Pair(s)`
- `Notes`

Display rules:
- Show null-to-value transitions explicitly (`null -> 50000`).
- Show type changes explicitly (`string("60") -> number(60)`).
- For object/array values, summarize compactly in markdown but keep full normalized values in manifest.

### 5. Reverse diff preview (optional)
If `DRAFT_AMENDMENT` is provided:
1. Flatten draft updates into dot/bracket paths.
2. For each draft path, compare against current `lease_state` value.
3. Emit `overwrite_preview` entries with:
   - `field_path`
   - `current_value`
   - `draft_value`
   - `would_overwrite` (true/false)
   - `comparison_reason` (`equal_after_normalization`, `value_change`, `type_change`, `current_missing`)
4. Do not mutate or merge into `lease_state`; preview only.

### 6. Emit JSON manifest
Emit one fenced `json` block with:
- `schema_version`
- `change_entry_count`
- `groups`
- `field_timelines`
- `overwrite_preview` (optional)
- `warnings`

## Validation
Before emission, verify:
- Every `change_log.field_path` resolves in `lease_state` or is a valid append path for arrays.
- Earliest timeline value equals earliest `old_value` per path.
- Latest timeline value equals current `lease_state` value for that path.
- Every event with `source_document` also has `citation` (and vice versa).
- Grouping and column order match `references/diff_rules.md`.

## Error Handling
- **Malformed JSON**: stop and return parser error.
- **Missing `change_log`**: return empty deliverable with warning `missing_change_log`.
- **Unresolvable path**: keep entry, mark `path_resolution_warning`, do not guess replacements.
- **Null or ambiguous values**: skip-don’t-guess; include canonical reason string `skipped_ambiguous_or_null_input`.

## Prerequisites
- Upstream extraction should be conformance-checked with `lease-eval` when available.
- This skill depends on explicit `change_log` chronology and does not infer amendment deltas from prose.

## Worked Example (fixture `golden_ol_a1`)
Expected grouped sections from 6 entries:
1. `Dates` (ExpirationDate, TermMonths)
2. `Financials.BaseRent.Schedule[5]`
3. `Financials.BaseRent.Schedule[6]`
4. `Financials.TIAllowance` (Amount + RatePerSF grouped together)

The TI allowance fields are presented as one section because they share the `Financials.TIAllowance` prefix and same amendment attribution.

## Follow-on Work
- Optional HTML diff renderer for downstream portal embedding.
- Optional path alias map for friendlier labels without changing canonical manifest paths.
