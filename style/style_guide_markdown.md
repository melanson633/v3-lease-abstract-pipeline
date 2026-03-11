# Lease Abstract Style Guide (Markdown) — Knowledge Module

> **Purpose:** Define the required structure, formatting, citation conventions, and authoring constraints for markdown abstracts so they render cleanly to PDF and meet the institutional quality bar.

---

## 1) Global Rules
- Use clear headings and short paragraphs.
- Prefer tables for schedules and matrices.
- Keep formatting consistent (dates, currency, percent).
- Do not include internal reasoning; deliver only the abstract content.

---

## 2) Required Document Structure
### Page 1 — Executive Fact Sheet
- Title line includes tenant + premises (or property name)
- Short narrative summary (target ≤400 words; adjust for audience)
- A **Metrics Table** with columns: `Metric | Value | Citation`
- End Page 1 with a hard page break: `\f`

### Pages 2+ — Thematic Sections (up to seven)
Use this order (aligned with abstraction procedure) unless the user requests otherwise:
1. Lease Fundamentals
2. Rent & Security
3. Additional Rent / Expenses
4. Options
5. Use / Operating Covenants
6. Maintenance & Repairs
7. Other Key Provisions (or Open Items / Underwriting Notes)

---

## 3) Headings
- `#` Document title
- `##` Main sections (Executive Fact Sheet; Lease Fundamentals; etc.)
- `###` Subsections
Avoid skipping levels (don't jump from `##` to `####`).

### 3.1 Page Break Policy (Major Sections)
To ensure professional pagination in PDF:
- Insert a hard page break `\f` **before each H2 (`## `) section** *after* the Executive Fact Sheet (Page 1).
- The renderer will enforce these breaks; authors may include `\f` explicitly if needed.
- Do **not** place `\f`:
  - inside a markdown table block,
  - inside fenced code blocks,
  - between a heading and its first paragraph/table.

---

## 4) Tables
### 4.1 Metrics Table (Required)
```markdown
| Metric | Value | Citation |
|--------|-------|----------|
| ...    | ...   | ...      |
```

### 4.2 Rent Schedule Table (Common)
```markdown
| Period | Start Date | End Date | Annual Rent | Monthly Rent | $/RSF Annual | Citation |
|--------|------------|----------|-------------|--------------|--------------|----------|
```

### 4.3 Responsibility Matrix (When Applicable)
```markdown
| Responsibility | Landlord | Tenant | Citation |
|----------------|----------|--------|----------|
```

**Table rules (authoring)**
- **Column count limit:** max 7 columns per table. If more columns are needed, split into two tables.
- Prefer a **Citation** column at the end.
- If a table is too wide:
  - split into two tables (e.g., "Key Dates" + "Notice Requirements"), or
  - move verbose explanations into a subsection paragraph and keep the table values short.
- **Cell content limit:** avoid cells exceeding ~140 characters. If a cell needs more, move the content to body text with a shorter table value.
- Avoid unbroken strings that won't wrap (very long IDs/URLs). If unavoidable, insert break-friendly punctuation (e.g., `/` or `-`) or rewrite.
- Add a blank line after each table for readability.

---

## 5) Citation Convention
- Every factual assertion must be supported by a citation.
- **Citation format:** `DOC pPAGE REF` — examples:
  - `OL p5 §4.1` (Original Lease, page 5, section 4.1)
  - `A1 p3 §2.1` (Amendment 1, page 3, section 2.1)
  - `CM p1` (Commencement Memo, page 1)
  - `EX-A p2` (Exhibit A, page 2)
- Document abbreviations: OL = Original Lease, CM = Commencement Memo, A1/A2/An = Amendments, EX = Exhibit
- If a value comes from multiple sources, cite the controlling document first.
- In tables, use the Citation column. In narrative text, place citations inline in parentheses.

---

## 6) Numeric & Date Formatting
- Dates in the **abstract / PDF**: `MM-DD-YYYY`
- Dates in **JSON / exports**: `YYYY-MM-DD`
- **Transformation rule:** When generating abstracts from extraction JSON, convert `YYYY-MM-DD` → `MM-DD-YYYY` for display. When exporting back to JSON/CSV, use `YYYY-MM-DD`.
- Currency:
  - Use commas and two decimals where appropriate: `$1,234.56`
  - For RSF-based values, include units: `$16.00/RSF annually` (and optionally the monthly equivalent)
- Percent: `8%` (no extra decimals unless required by precision needs)

---

## 7) Content Constraints (Quality Bar)
- Be specific and plainspoken.
- **Separate facts from open items:** confirmed lease terms go in thematic sections; unresolved items, TBDs, and missing data go in the "Open Items" section at the end.
- Keep "Open Items / Underwriting Notes" as the last section of the document.
- Do not mix confirmed values with speculation or assumptions.

---

## 8) Audience Tailoring (High-Level)
- Executive: concise, decision-ready, highlight key dates, dollars, options, major risks
- Asset Management: include schedules, escalations, valuation impacts, assumptions
- Property Management: expand the responsibility matrix and operational constraints
- Legal: emphasize defaults, remedies, liability allocations, compliance flags

---

## 9) Highlighting Changes (When `change_log` exists)
- Add a short "Highlights" bullet list under Executive Fact Sheet if there are major changes.
- In the Amendments/Change Log section, provide:
  - a table of amendments and key changes
  - mention effective dates and what was superseded

---

## 10) Prohibited Content
- No legal advice or recommendations.
- No internal chain-of-thought.
- Do not paste large chunks of the lease; quote only small excerpts when required for ambiguity.

---

## 11) Failure Mode
If PDF quality is degraded (tables unreadable, clipping, broken formatting):
- Prefer **renderer fixes** (wrapping/column widths/page breaks) over rewriting content.
- If markdown must change, apply the **minimal adjustment**:
  - split the table,
  - shorten cell text,
  - move narrative into body text,
  - keep citations last.
- Diagnose whether the issue is a renderer problem or a markdown authoring problem before making changes.
