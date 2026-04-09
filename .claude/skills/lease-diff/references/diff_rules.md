# Diff Rules Reference

## 1) Normalization Rules
- **Strings**: trim leading/trailing whitespace before compare.
- **Numbers**: compare with epsilon `1e-9` for floating values.
- **Dates**: compare lexically only after normalization to `YYYY-MM-DD`.
- **Booleans/null**: exact compare.
- If normalization fails for a value, preserve original and mark `normalization_warning`.

## 2) Array Matching Policy
- Default is **index-based** matching for ordered arrays (e.g., `Schedule[5]`, `Schedule[6]`).
- Identity matching may be used only when a stable key is present (e.g., object has explicit immutable ID).
- If no stable identity key exists, do not attempt identity remap; keep index semantics.

## 3) Null-to-Value Display
- Render explicitly as `null -> <value>`.
- For reverse diff, render `<value> -> null` when draft removes populated values.

## 4) Type-Change Display
- If normalized types differ, display as:
  - `string("60") -> number(60)`
  - `number(50000) -> object({...})`
- Type changes always set `comparison_reason = type_change` in manifest.

## 5) Grouping Rules by `field_path` Prefix
Group by longest meaningful shared prefix:
1. `Dates.*` -> **Dates**
2. `Financials.BaseRent.Schedule[i]` -> **Schedule[i]** per index
3. `Financials.TIAllowance.*` -> **TI Allowance**
4. All others -> first two path segments (for example `Clauses.Guaranty`)

## 6) Output Column Order (Markdown Table)
1. Field Path
2. Progression
3. Original
4. Current
5. Amendment Events
6. Citation Pair(s)
7. Notes

## 7) Canonical Skip Reasons
- `skipped_ambiguous_or_null_input`
- `skipped_missing_draft_amendment`
- `skipped_unresolvable_path`
