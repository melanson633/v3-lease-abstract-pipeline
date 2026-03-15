# Schema Optimization Analysis — Session Prompt

You are analyzing `v4_unified_schema.json` (v4.0.0), a JSON Schema draft-07 file that defines the canonical data contract for a commercial lease extraction system (LeaseGPT). The schema lives at `.claude/skills/lease-extract/references/v4_unified_schema.json`.

## Why This Matters
This 830-line / ~31KB schema is the single largest file in the repo. It loads as Layer 3 context during extraction and is the authoritative contract for all downstream skills (abstract, render, export). Every line saved here reduces token cost on every extraction run.

## Current Schema Profile
- **215 total fields** across 11 top-level sections
- **93% of leaf fields are nullable** (`["type", "null"]`) — almost nothing is required
- **Field distribution**: Financials (65), Clauses (38), Options (28), Parties (26), Metadata (13), Premises (12), Dates (8), change_log (7), pending_fields (4), Utilities (2), traceability (1)
- **Structural duplication found**: Landlord/Tenant share identical 5-property objects (Name, TradeName, EntityType, Jurisdiction, Address) and Address shares identical 5-property objects (Street, City, State, PostalCode, Country)
- **8 descriptions exceed 100 chars** (1,139 chars total in verbose descriptions)
- **Three special arrays** at root level: `change_log`, `pending_fields`, `traceability` — these are extraction metadata, not lease data

## Your Task
Read the full schema and produce a detailed optimization report with these sections:

### 1. Structural Deduplication via `$ref`
Identify objects that share identical or near-identical structures and could use JSON Schema `$ref` / `$defs`. The Landlord/Tenant/Guarantor party objects and their Address sub-objects are known candidates. Find any others. Estimate line savings for each.

### 2. Field Necessity Audit
Cross-reference every schema field against the extraction priority map at `.claude/skills/lease-extract/references/schema_priority_map.md`. Identify:
- **Fields in schema but NOT referenced in any pass** (Pass 1/2/3) — candidates for removal
- **Fields that are always null in practice** (metadata/operational fields that serve no extraction purpose)
- **Fields that duplicate information available elsewhere** (e.g., does `Financials.BaseRent.CommencementDate` duplicate `Dates.RentCommencementDate`?)

### 3. Description Trimming
Many descriptions restate what the field name already implies (e.g., `"Name": { "description": "Legal name of the landlord entity" }`). Identify descriptions that add no information beyond the field name + parent context and could be shortened or removed. Estimate character/line savings.

### 4. Nesting Depth Reduction
Identify deeply nested paths (4+ levels) where flattening would reduce schema complexity without losing semantic clarity. Example: `Financials.AdditionalRent.ExpenseStructure.OperatingExpenses` — is the `ExpenseStructure` wrapper necessary?

### 5. Metadata vs. Data Separation
The schema mixes lease data (Parties, Premises, Dates, Financials, Options, Clauses, Utilities) with extraction metadata (Metadata, change_log, pending_fields, traceability). Evaluate whether the metadata sections should be:
- Kept inline (current approach)
- Moved to a separate `$defs` block
- Removed from the schema entirely (they're already defined in the extraction SKILL.md body)

### 6. Type Consistency
Audit for inconsistent type patterns:
- Fields using `"type": ["string", "null"]` vs `"type": "string"` — is the nullable pattern applied consistently?
- Array fields: are `items` schemas consistent? Any arrays missing `items`?
- Numeric fields: `number` vs `integer` usage — is it intentional?

### 7. Consolidation Candidates
Look for groups of closely related fields that could be consolidated:
- Multiple boolean/string fields that could become an enum
- Parallel arrays that could be a single array of objects
- Fields that are semantically part of the same concept but scattered across sections

## Output Format
For each section, provide:
1. **Finding** — what you found, with exact schema paths
2. **Recommendation** — specific change (with before/after examples where helpful)
3. **Impact** — estimated line reduction and any downstream effects on the extraction SKILL.md, export SKILL.md, or other consumers

End with a **Summary Table**: optimization name, estimated line savings, risk level (safe/moderate/breaking), and whether it requires updating downstream skills.

## Context Files to Read
1. `.claude/skills/lease-extract/references/v4_unified_schema.json` — the schema (primary target)
2. `.claude/skills/lease-extract/references/schema_priority_map.md` — field usage by extraction pass
3. `.claude/skills/lease-extract/SKILL.md` — extraction procedure (schema consumer)
4. `.claude/skills/lease-export/SKILL.md` — export procedure (schema consumer)
5. `config/shared_constants.md` — shared constants referenced by schema

## Constraints
- Do NOT modify any files. This is a read-only analysis.
- Do NOT propose changes that would break the extraction or export procedures without flagging the breakage.
- Treat the field names as a public API — renaming fields is a breaking change and should be flagged as such.
- The schema must remain valid JSON Schema draft-07 after any proposed changes.
