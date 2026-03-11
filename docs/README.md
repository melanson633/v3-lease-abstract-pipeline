# LeaseGPT Directory Structure

This directory contains all procedures, configuration, system instructions, and reference materials for **shortcut.ai_cre**—a modular commercial lease extraction and abstraction system.

---

## 📋 Quick Navigation

| Folder | Purpose | When to Use |
|--------|---------|------------|
| **Procedures/** | Core workflow modules | Reference when executing extract → abstract → render → export pipeline |
| **Configuration/** | Schema, priorities, style tokens | Consult when defining data structure or visual styling |
| **System_Instructions/** | System prompts | Copy active prompt into your LLM platform configuration |
| **Reference/** | Requirements, guides, workflow overview | Read for high-level understanding and best practices |
| **Assets/** | Sample documents and visual assets | Reference examples when testing or onboarding |
| **Archives/** | Previous versions and update notes | Historical reference; preserved for version tracking |

---

## 📁 Directory Details

### `Procedures/`
The four core execution procedures that drive LeaseGPT's functionality.

- **`extraction_procedure_refined.md`**
  How to extract structured lease data from raw documents (PDFs, scans, OCR text) into validated JSON. Covers document review, field extraction, change logging, and validation.

- **`abstraction_procedure_refined.md`**
  How to generate polished, audience-tailored lease abstracts from validated extraction JSON. Includes template selection, content generation, and formatting rules.

- **`render_procedure_pdf.md`**
  How to convert markdown abstracts into professional PDFs. Covers preflight checks, styling, pagination, and table handling.

- **`export_procedure_refined.md`**
  How to export extraction outputs as CSV or Excel. Includes single-tenant exports and multi-tenant rollup conventions.

**When to use:** Follow these procedures sequentially or per user request (extraction → abstraction → rendering → export).

---

### `Configuration/`
Schema definitions, priority mappings, and style tokens that govern data structure and visual presentation.

#### Root files:
- **`v4_unified_schema.json`** (Canonical)
  The authoritative JSON schema defining all lease data fields, types, descriptions, and relationships. This is the source of truth for extraction outputs.

- **`schema_priority_map.md`**
  Progressive extraction roadmap. Defines which fields to extract first (Pass 1: Critical Terms) vs. later passes (detailed analysis). Used to optimize for speed without sacrificing key data.

- **`lease_abstract_pdf_style_tokens.yaml`**
  Design system tokens for PDF rendering: typography (font families, sizes, weights), colors, spacing, and margins. Reference when styling PDFs.

#### `style_guides/` subdirectory:
- **`style_guide_markdown.md`**
  Rules for structuring and formatting markdown abstracts: heading hierarchy, table conventions, citation formatting, and content ordering.

- **`style_guide_pdf.md`**
  Rules for final PDF presentation: page setup, typography, headers/footers, table layout, and section spacing.

**When to use:** Consult when defining extraction scope, formatting outputs, or ensuring consistency.

---

### `System_Instructions/`
System prompts. Only one is active; others are archived versions.

- **`system_prompt.md`** ⭐ **ACTIVE** (v3.0.0)
  The consolidated, production system instructions for shortcut.ai_cre. Copy the full contents into the system instructions field of your LLM platform.

Previous versions archived to `Archives/System_Instructions/`:
- `system_prompt_current.md` (previous active)
- `system_prompt_refined.md`
- `system_prompt_v.1_010926.md`

**When to use:**
- Copy `system_prompt.md` into your LLM platform configuration when setting up or updating.
- Refer to archived versions if you need to understand prior design decisions.

---

### `Reference/`
High-level documentation, guides, and best practices.

- **`requirements.md`**
  North-star system specification: operating modes, hard constraints (single-tenant rule, stateful processing), data contracts, and knowledge file usage.

- **`workflow_overview.md`**
  End-to-end workflow decision tree. Shows which procedure to run based on user intent (extract vs. abstract vs. render vs. export) and prerequisite data.

- **`gpt5_prompting_guides_notes_2026-01-09.txt`**
  Official OpenAI prompting patterns for GPT-5 models. Includes output shape clamping, scope guardrails, context gathering, and tool budgets—useful for optimizing system prompts.

- **`create_a_gpt_notes_2026-01-09.txt`**
  Guide to ChatGPT's "Create a GPT" builder. Covers UX, knowledge file limits, publishing options, and collaboration features.

**When to use:**
- Read `requirements.md` to understand the system's hard constraints and operating model.
- Consult `workflow_overview.md` to route user requests to the correct procedure.
- Reference prompting guides when refining system instructions.

---

### `Assets/`
Sample documents and visual references for testing and onboarding.

#### `images/`
- **`ChatGPT Image Jan 9, 2026, 03_32_34 PM.png`**
  Screenshot showing ChatGPT interface or workflow state.

- **`Visual_rendering_new.png`**
  Visual mockup of a rendered lease abstract or dashboard.

#### `sample_documents/`
- **`600 Griffin Brook Drive - Restaurant Technologies Lease 11042025.pdf`**
  Real sample lease document. Use for testing extraction, abstraction, and rendering workflows.

**When to use:** Reference images when onboarding or testing; process sample lease when validating end-to-end workflow.

---

### `Archives/`
Previous versions and update proposals; preserved for historical reference.

#### `Table_render_updates/`
- `render_procedure_pdf.updated.md`
- `style_guide_markdown.updated.md`
- `style_guide_pdf.updated.md`

Earlier iterations of rendering and style procedures.

#### `UPDATES/`
- `GPT_builder_proposals.011026.txt`
  Proposals and notes for GPT builder enhancements.

**When to use:** Historical reference only. Consult if you need to understand prior design decisions or revert to an older version.

---

## 🎯 Workflow: How Files Work Together

### User uploads lease documents → Request extract:
1. Follow **`Procedures/extraction_procedure_refined.md`**
2. Reference **`Configuration/v4_unified_schema.json`** for field definitions
3. Use **`Configuration/schema_priority_map.md`** to prioritize extraction passes
4. Output: `lease_state` (JSON) + `change_log`

### User requests abstract from extraction JSON:
1. Follow **`Procedures/abstraction_procedure_refined.md`**
2. Consult **`Configuration/style_guides/style_guide_markdown.md`** for formatting
3. Review **`Reference/requirements.md`** for output validation
4. Output: Markdown abstract

### User requests PDF from markdown:
1. Follow **`Procedures/render_procedure_pdf.md`**
2. Apply **`Configuration/lease_abstract_pdf_style_tokens.yaml`** for styling
3. Reference **`Configuration/style_guides/style_guide_pdf.md`** for layout rules
4. Output: PDF file

### User requests CSV/Excel exports:
1. Follow **`Procedures/export_procedure_refined.md`**
2. Use extraction JSON as input
3. Output: CSV or XLSX files

---

## ⚙️ Key Concepts

**Single Tenant Per Run**
Each extraction processes one leaseholder's documents (original lease + amendments + memos). Multiple tenants require separate runs.

**Current Lease State**
Documents are processed sequentially (Original → Commencement Memo → Amendments). Later documents override earlier terms; state evolves with each update.

**Full Traceability**
Every extracted field includes:
- Field path (schema reference)
- Value + units
- Citation (document ID + section/page)
- Confidence score
- Validation status

**Schema Alignment**
All outputs align to `v4_unified_schema.json`. This ensures consistency across extraction, abstraction, and export.

---

## 🚀 Getting Started

1. **Understand the system:**
   Read `Reference/requirements.md` (5 min) and `Reference/workflow_overview.md` (5 min)

2. **Set up your LLM:**
   Copy `System_Instructions/system_prompt.md` into your platform's system instructions field

3. **Test with sample lease:**
   Use `Assets/sample_documents/600 Griffin Brook Drive...pdf` to validate the full pipeline

4. **Reference as needed:**
   Use this README to navigate to the specific procedure or guide for each step

---

## 📞 Support & Questions

- **What should I extract?** → See `Configuration/schema_priority_map.md`
- **How do I format outputs?** → See `Configuration/style_guides/`
- **What's the workflow?** → See `Reference/workflow_overview.md`
- **How do I set it up?** → See `System_Instructions/system_prompt.md` and `Reference/create_a_gpt_notes_2026-01-09.txt`
- **What are the rules?** → See `Reference/requirements.md`

---

**Last Updated:** February 4, 2026
**Version:** 3.0.0 (system_prompt.md is active)
**Schema Version:** v4_unified_schema.json (v4.0.0)

### Knowledge File Attachment List
Upload these files to your LLM platform as knowledge files:

| # | File | Purpose |
|---|------|---------|
| 1 | `Configuration/v4_unified_schema.json` | Canonical schema (field names, types, structure) |
| 2 | `Configuration/shared_constants.md` | Shared constants (confidence, validation, citation, dates) |
| 3 | `Configuration/schema_priority_map.md` | Progressive extraction pass ordering |
| 4 | `Configuration/lease_abstract_pdf_style_tokens.yaml` | PDF styling tokens |
| 5 | `Configuration/style_guides/style_guide_markdown.md` | Markdown formatting rules |
| 6 | `Configuration/style_guides/style_guide_pdf.md` | PDF presentation rules |
| 7 | `Procedures/extraction_procedure_refined.md` | Extraction workflow |
| 8 | `Procedures/abstraction_procedure_refined.md` | Abstraction workflow |
| 9 | `Procedures/render_procedure_pdf.md` | PDF rendering workflow |
| 10 | `Procedures/export_procedure_refined.md` | CSV/Excel export workflow |
| 11 | `Reference/workflow_overview.md` | End-to-end decision routing |
