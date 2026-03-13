---
name: lease-extract
description: >
  Extract structured lease data from uploaded documents into validated JSON
  following the v4 unified schema. Produces lease_state, change_log,
  pending_fields, and traceability objects.
  TRIGGER when: user asks to "extract", produce "JSON", "schema output",
  "validated data", or uploads lease documents without specifying output type.
  DO NOT TRIGGER when: user asks for abstract, summary, PDF, render, CSV,
  Excel, or export.
---

# Extraction Procedure

## Role
Guide **shortcut.ai_cre** when extracting lease data from uploaded documents. Ensure accurate, comprehensive, and traceable extraction while maintaining a sequential lease state and change log.

Hard constraints (single-tenant rule, sequential supersession, per-field traceability): per CLAUDE.md.
Confidence scale, validation status enum, citation format, date conventions: per `config/shared_constants.md`.

## Inputs
- `LEASE_DOCS_RAW`: Files (PDFs, scanned images, OCR text) representing the original lease, commencement memo(s), and amendments for a single tenant.
- `EXTRACTION_SCHEMA`: The canonical JSON schema (`v4_unified_schema.json`) defining required data points, field paths, data types, and citation requirements.

## Output Objects
- `lease_state`: JSON object representing the current state of the lease after processing all documents. Follows the unified schema; includes metadata (extractor version, generation timestamp, schema version 4.0.0, confidence score, validation status).
- `change_log`: Array of change records, each with:
  - `field_path`, `old_value`, `new_value`, `effective_date` (YYYY-MM-DD), `source_document`, `citation` (DOC pPAGE REF), `impact_notes`
- `pending_fields`: Array for fields that could not be fully extracted:
  - `path`, `reason`, `where_to_find`, `hint`
- `traceability`: Field-level metadata mapping schema paths to citation, confidence, validation_status, and notes.

## Workflow

### 1. Document Review & Meta-Plan
1. **Validate Inputs**: Ensure all uploaded files pertain to the same tenant (per CLAUDE.md single-tenant rule).
2. **Assign Document Codes**: Label each document by type and sequence (e.g., `OL`, `CM`, `A1`, `A2`). Order chronologically by effective date.
3. **Inventory & Quality Assessment**: For each document, note page count, quality (OCR confidence), missing pages or corruption. Flag issues for user attention.
4. **Extraction Strategy**: Outline a three-pass approach. For pass field lists, read `references/schema_priority_map.md`.
   - **Pass 1** (Critical Business Terms): Parties, Premises, Dates/Term, Base Rent schedule, Security/TI, Options, Use
   - **Pass 2** (Financial + Operating): CAM/Taxes/Insurance/Utilities, Maintenance, Assignment/Subletting
   - **Pass 3** (Legal/Edge Clauses): Default/Remedies, Guaranty, Environmental, SNDA, Force Majeure, etc.
5. **Risk Assessment**: Identify potential challenges (conflicting clauses, poor OCR, missing exhibits). Prepare mitigation strategies.
6. **Success Criteria**: >=99% field completion for Pass 1, >=95% citation coverage, zero calculation errors, complete amendment reconciliation.
7. Produce a **Meta-Plan** in a fenced `markdown` block summarizing steps 1-6.

### 2. Initialize Lease State
1. Create empty `lease_state` following the unified schema. Populate metadata: extractor version, schema version (4.0.0), generation timestamp (UTC), default validation status (`pending`).
2. Initialize empty `change_log`, `pending_fields`, and `traceability.extractedFieldsMetadata`.
3. Set initial confidence scores to `null` or `0`.

### 3. Sequential Document Processing
For each document in chronological order:
1. **Parse Document**: Read and, if necessary, OCR each page. Extract relevant text snippets for citation.
2. **Identify Impacted Fields**: Determine which schema fields may be affected.
3. **Extract Field Values**: For each impacted field, extract the value with correct normalization, capture citation, assign confidence score and validation_status.
4. **Update Lease State**: If field is new, set it. If field already exists and new value represents an amendment, append to `change_log` then overwrite in `lease_state`.
5. **Handle Conflicts & Ambiguities**: Apply latest amendment; document resolution in `change_log`. If ambiguity remains, flag for manual review with multiple interpretations and confidence scores.
6. **Date Definition-First Rule**: If a date is defined by formula rather than explicit date, leave field `null`, record definition in `Dates.DateNotes`, add to `pending_fields`, set validation_status to `pending`.
7. Repeat until all documents processed.

### Amendment Merge Algorithm (Worked Example)
Given: OL defines base rent $20.00/RSF; A1 (effective 2025-06-01) changes to $22.00/RSF.
1. Process OL: Set `Financials.BaseRent.Schedule[0].baseRentPSF = 20.00`, citation `OL p12 §3.1`, confidence `1.0`, status `confirmed`.
2. Process A1: Detect change to `Financials.BaseRent.Schedule[0].baseRentPSF`.
3. Append to `change_log`: `{field_path: "Financials.BaseRent.Schedule[0].baseRentPSF", old_value: 20.00, new_value: 22.00, effective_date: "2025-06-01", source_document: "A1", citation: "A1 p2 §1.a", impact_notes: "Rent increase of $2.00/RSF effective Year 2"}`
4. Update `lease_state`: overwrite with 22.00 and update traceability metadata.

### 4. Validation & Consistency Checks
1. **Calculation Verification**: Ensure base rent calculations (annual/12 = monthly), PSF rates (annual/RSF), pro-rata shares (tenant RSF / building RSF), and escalation computations are correct.
2. **Schema Compliance**: Verify all required fields are present. For schema field definitions, read `references/v4_unified_schema.json`. Missing fields: search documents again; if still missing, mark `null`, set validation_status `missing`, add to `pending_fields`.
3. **Citation Coverage**: Confirm every field has at least one citation. Flag uncited values.
4. **Cross-Reference Matrix**: Check logical consistency between related fields (term dates vs. rent schedule periods; security deposit vs. monthly rent). Document discrepancies.
5. Update `lease_state.Metadata.LeaseStatus`. Populate `traceability` for all extracted fields.

### 5. Output Generation
1. **JSON Output**: Produce a fenced `json` block containing `lease_state`, `change_log`, `pending_fields`, and `traceability`. Include summary metrics: documents processed, fields extracted, citations count, validation status, confidence score.
2. **Error Reporting**: If validation fails or confidence below threshold, produce error report with critical errors, validation failures, missing fields, recommended actions.
3. Conclude with a self-check statement on completeness and accuracy.

### Progressive Extraction Rules
- Return **Pass 1** promptly. If time-constrained, return partial with `pending_fields` + `change_log`.
- Run Passes 2/3 only if time remains or user asks.
- **No runtime schema introspection.** Use `references/schema_priority_map.md` for pass ordering.
- **Low-text pages/exhibits:** no OCR loops by default; set null + pending. OCR max 2 pages only if explicitly requested.

## Error Handling
- **Multiple Tenants**: Stop and ask user to specify (per CLAUDE.md).
- **Poor OCR Quality**: Flag pages with confidence < 0.7; request better scans. Proceed with caution; mark affected fields low confidence.
- **Corrupted/Missing Files**: Identify issues, ask user to re-upload.
- **Ambiguous Terms**: Provide multiple interpretations, cite exact language, assign confidence scores, flag for manual review.

## Prerequisites
- If user asks for extraction but no documents are uploaded, ask them to upload documents first.
- Extraction produces JSON only. For CSV/Excel exports, the user should request the lease-export skill.
