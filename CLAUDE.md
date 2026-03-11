# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

This is **LeaseGPT (shortcut.ai_cre)** — a modular commercial lease extraction and abstraction system. It is **not a traditional software project**. There is no source code, no build system, no package manager, and no tests. The repository contains structured documentation, JSON schemas, procedural knowledge files, and style definitions that are uploaded as knowledge files to an LLM platform (ChatGPT/Claude).

## Repository Structure

- `config/` — System prompt (v3.0.0) and shared constants (confidence scale, validation status, citation format, date conventions)
- `schemas/` — Canonical JSON schema (v4.0.0) defining all lease fields, plus the progressive extraction priority map (Pass 1/2/3)
- `procedures/` — Four self-contained execution modules: extraction, abstraction, PDF rendering, CSV/Excel export
- `style/` — Markdown authoring rules, PDF presentation standards, and YAML design tokens (typography, colors, spacing)
- `docs/` — Requirements spec, workflow decision routing, and directory navigation guide

## Architecture

The system has four request-driven operating modes, each backed by its own procedure file:

1. **Extract** → `extraction_procedure_refined.md` → Produces `lease_state` JSON + `change_log` + `pending_fields` + `traceability`
2. **Abstract** → `abstraction_procedure_refined.md` → Produces markdown lease abstract from validated `lease_state`
3. **Render** → `render_procedure_pdf.md` → Converts markdown abstract to styled PDF
4. **Export** → `export_procedure_refined.md` → Produces CSV/XLSX workbooks from `lease_state`

### Critical Design Constraints

- **Single-tenant rule**: Each run processes exactly one leaseholder. Multiple documents are allowed only if they relate to the same tenant. If multiple tenants are detected, the system must stop and ask for clarification.
- **Sequential supersession**: Documents processed in order OL → CM → A1 → A2 → ... Later documents override earlier terms. The final output reflects current effective lease state.
- **Per-field traceability**: Every extracted field carries `citation` (format: `DOC pPAGE REF`), `confidence` (0.0–1.0), and `validation_status` (confirmed/pending/uncertain/flagged/missing).
- **Progressive multi-pass extraction**: Pass 1 (critical business terms, ~99% target) is returned promptly; Pass 2 (financial/operating) and Pass 3 (legal/edge clauses) enrich if time remains.

### Schema

`schemas/v4_unified_schema.json` (JSON Schema draft-07) is the canonical data contract. Top-level sections: Metadata, Parties, Premises, Dates, Financials, Options, Clauses, Utilities. All procedures and exports must conform to this schema.

### Style Standards

- Dates in JSON/exports: `YYYY-MM-DD`; in abstracts/PDFs: `MM-DD-YYYY`
- Currency: `$1,234.56` with commas and decimals
- Citations inline in narrative: `(OL p5 §4.1)`; in tables: dedicated Citation column
- Markdown tables: max 7 columns, GitHub-flavored pipes
- PDF design tokens in `style/lease_abstract_pdf_style_tokens.yaml`: Poppins font, ink blue `#00304d` primary, US Letter paper

## Deployment

To deploy, copy `config/system_prompt.md` into the LLM platform's system instructions, then upload knowledge files in the order listed in `docs/README.md`.
