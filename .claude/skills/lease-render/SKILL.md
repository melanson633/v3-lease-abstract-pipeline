---
name: lease-render
description: >
  Convert an approved markdown lease abstract into a professional styled PDF
  using ReportLab/Platypus composition.
  TRIGGER when: user asks for "PDF", "render", "downloadable report", or
  asks to convert a markdown abstract to PDF.
  DO NOT TRIGGER when: user asks for extract/JSON, abstract/summary (text),
  CSV/Excel/export.
---

# Render Procedure (Markdown → PDF)

> Convert an approved markdown lease abstract into a client-ready PDF with professional pagination, consistent typography, and table fidelity (no overflow, no clipping, repeatable across leases).

Hard constraints: per CLAUDE.md.
Date/currency conventions: per `config/shared_constants.md`.

## 1) Inputs
- `LEASE_ABSTRACT_MD` (markdown string produced by the lease-abstract skill)
- Optional render parameters:
  - `paper_size` (default: Letter)
  - `orientation` (default: portrait)
  - `include_toc` (default: false unless requested)
  - `client_mode` (default: false; hides internal debug notes)
- Design tokens: read `references/lease_abstract_pdf_style_tokens.yaml`

## 2) Output
- `LEASE_ABSTRACT.pdf` (attachment)

## 3) Preflight Checks (Must Run)
1. **Structural**: Confirm required top-level sections exist (Executive Fact Sheet + thematic sections). Confirm any existing `\f` page breaks are intentional (never insert mid-table).
2. **Table Integrity**: Identify wide tables; plan column-width strategy (or split). Ensure each table has a header row. No single column used as "paragraph dump." Max 7 columns; flag if exceeded.
3. **Citation Legibility**: Citations must remain readable (avoid shrinking fonts excessively).
4. **Formatting Consistency**: Dates display as `MM-DD-YYYY`. Currency as `$1,234.56`.

If any preflight check fails, return a short error report describing what must be fixed in the markdown before rendering.

## Prerequisites
- A markdown abstract is required. If not available, inform the user to generate one first using the lease-abstract skill.

## 4) Pre-Render Transform (Required)
> Goal: make pagination + tables deterministic before the PDF engine sees the content.

### 4.1 Page-Break Policy (H2 Rules)
- Insert `\f` before each `## ` section after the Executive Fact Sheet.
- Never insert `\f`: inside a table block, inside fenced code blocks, or between a heading and its immediate content.

### 4.2 Orphan-Heading Prevention
If renderer supports "keep-with-next": mark every H2 as keep-with-next with at least the next block. If not supported: the `\f` insertion rule is mandatory (guarantees no orphaned H2).

### 4.3 Table Wrapping Normalization
- Ensure all tables are GitHub-flavored pipe tables.
- Normalize cell whitespace (collapse spaces; remove stray hard line breaks).
- Insert soft break opportunities for long tokens: zero-width spaces after `/`, `-`, `_`, and after `,` in long comma-separated phrases.
- If a table is still too wide after column-width tuning, split into two tables.

## 5) Rendering Approach (Implementation)
**Primary (required): ReportLab/Platypus composition.**

Why: deterministic pagination and true table wrapping (row-height growth + header repetition) without relying on external services or brittle HTML-to-PDF quirks.

Minimum implementation requirements:
- Markdown parsing must preserve: headings (`#`, `##`, `###`), paragraphs/lists, tables (pipe tables), hard page breaks (`\f`).
- Tables rendered as ReportLab `Table`/`LongTable` with:
  - each cell as a **Paragraph** (not raw string) so text wraps
  - explicit `colWidths` that sum to available page width
  - `repeatRows=1` for header repetition
  - table splitting enabled across pages (do not shrink fonts to fit)

## 6) PDF Style Requirements
For layout rules, read `references/style_guide_pdf.md`.
For design token values (typography, colors, spacing), read `references/lease_abstract_pdf_style_tokens.yaml`.

> **Section ordering note:** The style_tokens YAML `pdf_subsection_hints` provides a 15-section layout for PDF pages. Map the abstract's 7 canonical sections (defined in the lease-abstract skill) to these 15 subsections for finer-grained PDF pagination.

Minimum requirements:
- Page numbers in footer
- Consistent margins
- Clean heading hierarchy (title largest, H2 distinct, H3 smaller)
- Tables readable and not clipped
- No orphaned headings at page bottom
- Preserve `\f` as hard page breaks
- Footer with page number + optional tenant/document name

## 7) Quality Assurance Checklist (Before Returning PDF)
- [ ] Executive Fact Sheet on page 1
- [ ] Metrics table not split awkwardly
- [ ] No table cell text overflows into adjacent cells or off-page
- [ ] Rent schedule tables readable; split across pages if needed
- [ ] Header row repeats when table spans pages
- [ ] No missing glyphs or broken encodings
- [ ] Citations present throughout and readable
- [ ] PDF opens cleanly; page count is reasonable
- [ ] Date format is `MM-DD-YYYY` throughout
- [ ] No table exceeds 7 columns
- [ ] Sensible page breaks (no orphaned headings)
- [ ] Numbers right-aligned, text left-aligned in tables

If issues remain, fix markdown or adjust rendering settings and rerender.

## 8) Failure Mode
If PDF quality is degraded (tables unreadable, clipping, broken formatting):
- Report the specific issue and where it appears (section name + table name).
- Choose the minimal fix:
  - **Renderer fix** (preferred): adjust column widths / wrapping rules
  - **Markdown fix**: split table, shorten cell text, move citations to last column
- Rerender and re-check.

## 9) Output Message
Provide a short confirmation:
- "Rendered PDF from markdown abstract"
- Any warnings (<=3 bullets), e.g., "wide rent schedule table wrapped; review for readability"

Attach the PDF.
