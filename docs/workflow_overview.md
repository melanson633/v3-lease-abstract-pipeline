# LeaseGPT Workflow Overview (Knowledge Module)

> **Purpose:** Define the end-to-end workflow and decision routing across modules (Extract → Abstract → Render → Export), including prerequisites, data contracts, and user interaction rules.
>
> **Scope:** Single-tenant processing per run. Multi-tenant rollups are allowed **only** when multiple prior validated extraction JSONs are provided by the user.

---

## 1) Canonical Data Contracts

### 1.1 Source Inputs
- **LEASE_DOCS_RAW**: PDFs / scans / OCR text for *one tenant*, potentially multiple documents.
- **EXTRACTION_SCHEMA**: `v4_unified_schema.json` (authoritative field names/types/structure).

### 1.2 Core Outputs (Extraction Product)
- **lease_state**: Structured JSON representing the **current lease state** after sequential processing.
- **change_log**: Array of change records capturing overrides/supersession across documents.

**Per-field traceability requirements:** See `Configuration/shared_constants.md` for confidence scale, validation status enum, and citation format.

### 1.3 Downstream Inputs
- **Abstract Module** consumes: `lease_state` + `change_log` with `lease_state.ValidationStatus == PASSED`.
- **Render Module** consumes: the generated **markdown abstract**.
- **Export Module** consumes: `lease_state` + `change_log` (PASSED strongly preferred; otherwise export must clearly mark low-confidence/missing fields).

---

## 2) Decision Routing (User Intent → Module)

### 2.1 If user asks for "extract", "JSON", "schema", "validated data"
Run:
1) **Extraction Procedure** (`extraction_procedure_refined.md`)
2) Produce `lease_state` + `change_log` + `pending_fields` + `traceability` (extraction produces JSON only; CSV/Excel is handled exclusively by the Export Module)

### 2.2 If user asks for “abstract”, “summary”, “lease abstract”, “investment-grade”
Prerequisite: validated `lease_state`.
If missing:
- Ask for extraction output type **or** run extraction first (if docs are provided).
Then run:
1) **Abstraction Procedure** (`abstraction_procedure_refined.md`)
2) Output markdown abstract (fenced markdown)

### 2.3 If user asks for “PDF”, “render”, “downloadable report”
Prerequisite: markdown abstract exists (generate it if not).
Then run:
1) **Render Procedure** (`render_procedure_pdf.md`)
2) Produce PDF as an attachment

### 2.4 If user asks for “CSV”, “Excel”, “export”, “rollup”
Prerequisite: extraction JSON exists.
Then run:
1) **Export Procedure** (`export_procedure_refined.md`)
2) Produce CSV/XLSX attachment(s)

**Multi-tenant rollup rule**
- Only allowed when the user provides **multiple prior extraction JSONs** (attachments or previously produced outputs).
- Never “extract multiple tenants” in one run.

---

## 3) Standard Interaction Rules

### 3.1 Clarifying Questions (ask only when needed)
Ask a short clarifier when:
- Output type is unspecified
- Multiple tenants detected
- Document ordering ambiguity affects meaning
- `property_type` / `audience` is required for abstraction
- Critical inputs are missing (e.g., RSF but no building RSF for pro-rata verification)

### 3.2 Confidence & Failure Behavior
- If critical fields cannot reach acceptable confidence or citations are missing, produce a **structured error report**:
  - Missing fields + suggested document search locations
  - Low-confidence fields + why
  - Conflicts detected + resolution rule applied or options
  - Next actions requested from user (e.g., upload missing exhibit)

---

## 4) Formatting & Style Dependencies
- Markdown abstract formatting must follow: `style_guide_markdown.md`
- PDF rendering must follow: `style_guide_pdf.md`
- Exports must follow: `export_procedure_refined.md` (column conventions, schedule tabs)

**Cross-module constants** (confidence, validation status, citation format, date conventions): See `Configuration/shared_constants.md`.

---

## 5) Quick “Happy Path” Example
1) User uploads OL + A1 + A2 and asks: “Extract to JSON”
2) Run extraction → produce PASSED `lease_state` + `change_log`
3) User asks: “Generate executive abstract”
4) Run abstraction → produce markdown
5) User asks: “Render to PDF”
6) Run render → produce PDF
7) User asks: “Export rent schedule to Excel”
8) Run export → produce XLSX

