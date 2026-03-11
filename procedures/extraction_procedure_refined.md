# Extraction Procedure (Refined)

## Role
This procedure guides **shortcut.ai_cre** when extracting lease data from a set of uploaded documents. It ensures accurate, comprehensive and traceable information while maintaining a sequential lease state and change log.

## Inputs
- `LEASE_DOCS_RAW`: A set of files (PDFs, scanned images, OCR text) representing the original lease, commencement memo(s) and amendments for a single tenant.
- `EXTRACTION_SCHEMA`: The canonical JSON schema (`v4_unified_schema.json`) defining required data points, field paths, data types and citation requirements.

## Output Objects
- `lease_state`: A JSON object representing the current state of the lease after processing all documents. It follows the unified schema and includes metadata such as extractor version, generation timestamp, schema version (4.0.0), confidence score, and validation status.
- `change_log`: An array of change records. Each record has:
  - `field_path`: The schema path (e.g., `Financials.BaseRent.Schedule`)
  - `old_value`: The value before the change
  - `new_value`: The updated value
  - `effective_date`: The date the change takes effect (format: `YYYY-MM-DD`)
  - `source_document`: The shorthand label of the document where the change was found (e.g., `A1`)
  - `citation`: A precise citation in format `DOC pPAGE REF` (e.g., `A1 p3 §2.1`)
  - `impact_notes`: Optional context or impact analysis
- `pending_fields`: An array of objects for fields that could not be fully extracted:
  - `path`: Schema dot-notation path
  - `reason`: Why the field could not be extracted
  - `where_to_find`: Guidance on which document likely contains the value
  - `hint`: Partial information or definition text
- `traceability`: Field-level metadata mapping schema paths to citation, confidence, validation_status, and notes.

**Note:** CSV/Excel exports are NOT produced by this procedure. Use `export_procedure_refined.md` for all tabular exports.

**Confidence scale, validation status enum, and citation format:** See `Configuration/shared_constants.md`.

## Workflow

### 1. Document Review & Meta-Plan
1. **Validate Inputs**: Ensure all uploaded files pertain to the same tenant. If multiple tenants are detected, stop and request clarification.
   - **Single-tenant detection:** If the lease names only one tenant entity (including DBAs), proceed. Subtenants and guarantors are not separate tenants.
2. **Assign Document Codes**: Label each document by type and sequence (e.g., `OL`, `CM`, `A1`, `A2`). Order them chronologically by effective date.
3. **Inventory & Quality Assessment**: For each document, note the page count, quality (OCR confidence) and any missing pages or corruption. Flag issues for user attention.
4. **Extraction Strategy**: Outline a three-pass approach per `schema_priority_map.md`:
   - **Pass 1** (Critical Business Terms): Parties, Premises, Dates/Term, Base Rent schedule, Security/TI, Options, Use
   - **Pass 2** (Financial + Operating): CAM/Taxes/Insurance/Utilities, Maintenance, Assignment/Subletting
   - **Pass 3** (Legal/Edge Clauses): Default/Remedies, Guaranty, Environmental, SNDA, Force Majeure, etc.
5. **Risk Assessment**: Identify potential challenges such as conflicting clauses, poor OCR, or missing exhibits. Prepare mitigation strategies.
6. **Success Criteria**: ≥99% field completion for Pass 1, ≥95% citation coverage, zero calculation errors, complete amendment reconciliation.
7. Produce a **Meta-Plan** in a fenced `markdown` block summarizing steps 1-6.

### 2. Initialize Lease State
1. Create an empty `lease_state` structure following the unified schema. Populate metadata: extractor version, schema version (`4.0.0`), generation timestamp (UTC), and default validation status (`pending`).
2. Initialize an empty `change_log` array.
3. Initialize an empty `pending_fields` array.
4. Initialize empty `traceability.extractedFieldsMetadata` object.
5. Set initial confidence scores to `null` or `0`.

### 3. Sequential Document Processing
For each document in chronological order:
1. **Parse Document**: Read and, if necessary, OCR each page. Extract relevant text snippets to allow citation.
2. **Identify Impacted Fields**: Determine which schema fields may be affected (e.g., commencement memos update `Dates.CommencementDate` and rent schedule; amendments may add options, change term dates, alter maintenance responsibilities).
3. **Extract Field Values**:
   - For each impacted field, extract the value, ensuring correct normalization (dates in `YYYY-MM-DD` format, currency normalized, percentages as decimals).
   - Capture the citation in `DOC pPAGE REF` format.
   - Assign a confidence score (0.0--1.0).
   - Assign a validation_status from the enum.
4. **Update Lease State**:
   - If the field does not yet exist in `lease_state`, set it along with its citation and confidence.
   - If the field already exists, compare the new value to the current value. If the new value represents an amendment or update, append a record to `change_log` documenting the change, then overwrite the field in `lease_state`.
5. **Handle Conflicts & Ambiguities**:
   - If conflicting terms are found across documents (e.g., overlapping rent schedules), apply the latest amendment and document the resolution rule in the `change_log` record.
   - If ambiguity remains after applying rules, flag the field for manual review and include multiple possible interpretations with confidence scores.
6. **Date Definition-First Rule**: If a date field (e.g., CommencementDate, RentCommencementDate) is defined by a formula rather than an explicit date (e.g., "6 months from lease execution"), leave the date field `null`, record the definition in `Dates.DateNotes`, add the field to `pending_fields`, and set validation_status to `pending`.
7. Repeat until all documents have been processed.

### Amendment Merge Algorithm (Worked Example)
Given: OL defines base rent as $20.00/RSF; A1 (effective 2025-06-01) changes to $22.00/RSF.

1. Process OL: Set `Financials.BaseRent.Schedule[0].baseRentPSF = 20.00`, citation `OL p12 §3.1`, confidence `1.0`, status `confirmed`.
2. Process A1: Detect change to `Financials.BaseRent.Schedule[0].baseRentPSF`.
3. Append to `change_log`: `{field_path: "Financials.BaseRent.Schedule[0].baseRentPSF", old_value: 20.00, new_value: 22.00, effective_date: "2025-06-01", source_document: "A1", citation: "A1 p2 §1.a", impact_notes: "Rent increase of $2.00/RSF effective Year 2"}`
4. Update `lease_state`: overwrite with 22.00 and update traceability metadata.

### 4. Validation & Consistency Checks
1. **Calculation Verification**: Ensure base rent calculations (annual / 12 = monthly), PSF rates (annual / RSF), pro-rata shares (tenant RSF / building RSF) and escalation computations are correct.
2. **Schema Compliance**: Verify all required fields are present. For missing fields, search the documents again; if still missing, mark as `null`, set validation_status to `missing`, and add to `pending_fields`.
3. **Citation Coverage**: Confirm that every field has at least one citation. Flag any uncited values for user review.
4. **Cross-Reference Matrix**: Check for logical consistency between related fields (e.g., term dates vs. rent schedule periods; security deposit vs. monthly rent). Document any discrepancies.
5. Update `lease_state.Metadata.LeaseStatus` appropriately. Populate `traceability` for all extracted fields.

### 5. Output Generation
1. **JSON Output**: Produce a fenced `json` block containing `lease_state`, `change_log`, `pending_fields`, and `traceability`. Include summary metrics: number of documents processed, number of fields extracted, citations count, validation status and confidence score.
2. **Error Reporting**: If validation fails or confidence is below threshold, produce an error report detailing critical errors, validation failures, missing fields and recommended actions.
3. Conclude each deliverable with a self-check statement indicating whether completeness and accuracy goals were met.

## Error Handling
- **Multiple Tenants**: Stop processing and ask the user to specify which tenant to proceed with.
- **Poor OCR Quality**: Flag pages with confidence < 0.7 and request better scans. Proceed with caution and mark affected fields as low confidence.
- **Corrupted or Missing Files**: Identify the missing pages or corrupt files and ask the user to re-upload.
- **Ambiguous Terms**: Provide multiple interpretations, cite the exact language, assign confidence scores and flag the item for manual review.
