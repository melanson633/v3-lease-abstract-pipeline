# Render Procedure (Markdown → PDF) — Knowledge Module

> **Purpose:** Convert an approved markdown lease abstract into a client-ready PDF with professional pagination, consistent typography, and *table fidelity* (no overflow, no clipping, repeatable across leases).

---

## 1) Inputs
- `LEASE_ABSTRACT_MD` (markdown string produced by Abstraction Module)
- Optional render parameters:
  - `paper_size` (default: Letter)
  - `orientation` (default: portrait)
  - `include_toc` (default: false unless requested)
  - `client_mode` (default: false; hides internal debug notes)
- Style tokens: `lease_abstract_pdf_style_tokens.yaml`

---

## 2) Output
- `LEASE_ABSTRACT.pdf` (attachment)

---

## 3) Preflight Checks (Must Run)
1) **Structural**
   - Confirm required top-level sections exist (Executive Fact Sheet + main thematic sections).
   - Confirm any existing `\f` page breaks are intentional (never insert mid-table).
2) **Table Integrity**
   - Identify wide tables; plan a column-width strategy (or split the table).
   - Ensure each table has a header row.
   - Confirm no single column is used as a "paragraph dump" when it should be a subsection.
   - Max 7 columns per table; if exceeded, flag for splitting.
3) **Citation Legibility**
   - Citations must remain readable (avoid shrinking fonts excessively to "make it fit").
4) **Formatting Consistency**
   - Dates/currency formatting matches `style_guide_markdown.md`.
   - Dates display as `MM-DD-YYYY` in the abstract.

If any preflight check fails, return a short error report describing what must be fixed in the markdown before rendering.

---

## 4) Pre-Render Transform (Required)
> Goal: make pagination + tables deterministic *before* the PDF engine sees the content.

### 4.1 Page-Break Policy (H2 Rules)
Apply the project's page-break policy (defined in `style_guide_markdown.md`):
- Insert a hard page break marker `\f` **before each H2 (`## `) section** *after* the Executive Fact Sheet section.
- Never insert `\f`:
  - inside a markdown table block,
  - inside fenced code blocks,
  - between a heading and its immediate following content.

### 4.2 Orphan-Heading Prevention (Minimum Guarantee)
If the renderer supports "keep-with-next":
- Mark every H2 heading as **keep-with-next** with *at least the next block* (first paragraph, list, or table).
If not supported:
- The `\f` insertion rule above is mandatory (it guarantees no orphaned H2 headings).

### 4.3 Table Wrapping Normalization
Normalize tables so the PDF renderer can wrap reliably:
- Ensure all tables are GitHub-flavored pipe tables (no multi-line cells).
- Normalize cell whitespace (collapse runs of spaces; remove stray hard line breaks).
- Insert *soft break opportunities* for long unbroken tokens:
  - e.g., add zero-width spaces (`\u200b`) after `/`, `-`, and `_` in long identifiers/paths, and after `,` in very long comma-separated phrases.
- If a table is still too wide after column-width tuning, split it into two tables (see `style_guide_markdown.md` "Tables" rules).

---

## 5) Rendering Approach (Implementation)
**Primary (required): ReportLab/Platypus composition.**

Why: deterministic pagination and true table wrapping (including row-height growth + header repetition) without relying on external services or brittle HTML-to-PDF quirks.

Minimum implementation requirements:
- Markdown parsing must preserve:
  - headings (`#`, `##`, `###`)
  - paragraphs/lists
  - tables (pipe tables)
  - hard page breaks (`\f`)
- Tables must be rendered as ReportLab `Table`/`LongTable` with:
  - each cell as a **Paragraph** (not a raw string) so text wraps,
  - explicit `colWidths` that sum to available page width,
  - `repeatRows=1` for header repetition,
  - table splitting enabled across pages (do not shrink fonts to fit).

---

## 6) PDF Style Requirements (Must Follow)
Pull rules from: `style_guide_pdf.md` and `lease_abstract_pdf_style_tokens.yaml`. Minimum requirements:
- Page numbers in footer
- Consistent margins
- Clean heading hierarchy
- Tables readable and not clipped
- Avoid orphaned headings at page bottom
- Preserve page breaks (`\f`) as hard breaks

---

## 7) Quality Assurance Checklist (Before Returning PDF)
- [ ] Executive Fact Sheet is on page 1 (or begins the document)
- [ ] Metrics table is not split awkwardly
- [ ] **No table cell text overflows into adjacent cells or off-page**
- [ ] Rent schedule tables are readable; split across pages if needed
- [ ] Header row repeats when a table spans pages (if supported by the renderer)
- [ ] No missing glyphs / broken encodings
- [ ] Citations present throughout and readable
- [ ] PDF opens cleanly and page count is reasonable
- [ ] Date format is `MM-DD-YYYY` throughout
- [ ] No table exceeds 7 columns

If issues remain, fix markdown (or adjust rendering settings) and rerender.

---

## 8) Failure Mode
If PDF quality is degraded (tables unreadable, clipping, broken formatting):
- Report the specific issue and **where it appears** (section name + table name).
- Choose the minimal fix:
  - **renderer fix** (preferred): adjust column widths / wrapping rules
  - **markdown fix**: split table; shorten cell text; move citations to last column
- Rerender and re-check.

---

## 9) Output Message (When Delivering)
Provide a short confirmation:
- "Rendered PDF from markdown abstract"
- Any warnings (≤3 bullets), e.g., "wide rent schedule table wrapped; review for readability"

Attach the PDF.
