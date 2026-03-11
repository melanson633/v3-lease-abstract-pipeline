# Lease Abstract Style Guide (PDF) — Knowledge Module

> **Purpose:** Define PDF output standards so generated abstracts look professional, read cleanly, and remain consistent across leases and audiences.

---

## 1) Page Setup
- Paper: Letter (unless requested otherwise)
- Margins: consistent on all sides (avoid "edge hugging" tables)
- Body font size: readable by default (avoid shrinking to "make it fit")

---

## 2) Typography & Hierarchy
- Clear hierarchy:
  - Title (largest)
  - H2 section headings (distinct)
  - H3 subsections (smaller)
- Avoid overly small font sizes; prioritize table readability.

---

## 3) Headers / Footers
- Footer should include:
  - Page number ("Page X of Y" if available)
  - Document name or tenant name (optional, subtle)
- Avoid heavy branding unless requested.

---

## 4) Tables (Most Important)

### 4.1 Table Acceptance Criteria
- **No clipping:** tables must never be cut off at the page edge.
- **No overflow:** cell text must never spill into adjacent columns or off the page.
- **Wrap + grow:** long cell text wraps and row height expands as needed.
- **Readable citations:** citations are legible at normal zoom (no micro-fonts).
- **Alignment:**
  - numbers right-aligned
  - text left-aligned

### 4.2 Multi-Page Table Rules
- If a table spans pages:
  - **Repeat header row** on new pages (required if supported by renderer)
  - Allow the table to split across pages; do not compress fonts as a workaround
  - Keep at least one body row with the header row — **no "header-only" page ends**
  - Never end a page with just a table header and no data rows

### 4.3 When Tables Are Too Wide
- Split into logical segments (e.g., rent schedule by years or by escalation blocks), or
- Move verbose narrative into paragraphs and keep table values concise.
- Maximum 7 columns per table; if more are needed, split the table.

---

## 5) Section Layout
- Executive Fact Sheet starts at the beginning.
- Use whitespace to separate sections.
- **Orphan heading prevention:** an H2 heading must not appear alone at the bottom of a page.
  - Preferred: start each H2 on a new page (after Page 1).
  - Minimum: keep the heading with the next block of content (paragraph/table).

---

## 6) Callouts / Highlights (Optional)
- If supported by the rendering method, use subtle callout boxes for:
  - major change_log items
  - deadlines (option notice windows)
  - compliance flags
- Keep callouts minimal and consistent.

---

## 7) QA Checklist (Before Delivery)
- [ ] Executive Fact Sheet is on Page 1
- [ ] Page breaks are sensible; no mid-table truncation
- [ ] Tables: no clipping, no overflow, wrapping works, citations readable
- [ ] Header row repeats on multi-page tables (if supported)
- [ ] No orphaned headings at page bottom
- [ ] No missing glyphs / broken encodings
- [ ] PDF opens cleanly and page count is reasonable
- [ ] Date format is MM-DD-YYYY throughout the abstract
- [ ] All financial figures have citations

---

## 8) Failure Mode
If PDF quality is degraded (tables unreadable, clipping, broken formatting):
- **Diagnose first:** determine whether it's a renderer issue (preferred fix) or a markdown authoring issue.
- Apply the **minimal fix**:
  - renderer: wrapping/col widths/repeat headers/page breaks
  - markdown: split table; shorten cells; move narrative to body text
- Rerender and re-check.
- Report the specific issue and **where it appears** (section name + table name).
