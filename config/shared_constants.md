# Shared Constants (v4.0.0)

> **Single source of truth** for values referenced across all LeaseGPT modules.
> All procedures and the system prompt reference this file rather than redefining these constants.

---

## Schema Version

- **Current:** `4.0.0`
- **Schema file:** `Configuration/v4_unified_schema.json`

---

## Confidence Scale (5-Tier, 0.0--1.0)

| Score | Meaning |
|-------|---------|
| **1.0** | Value explicitly stated in clear lease language |
| **0.9** | Value clearly implied or calculable from explicit terms |
| **0.7--0.8** | Value inferred from context with reasonable certainty |
| **0.5--0.6** | Value partially supported; ambiguity present |
| **< 0.5** | Insufficient support; flag for manual review |

- When confidence < 0.7, quote the exact lease language and explain the ambiguity.
- Never round up confidence to avoid flagging a field.

---

## Validation Status Enum

| Status | Meaning |
|--------|---------|
| `confirmed` | Value verified against source with high confidence |
| `pending` | Value not yet verified or awaiting additional documents |
| `uncertain` | Value extracted but ambiguous; requires review |
| `flagged` | Value may have errors or conflicts |
| `missing` | Value not found in any provided document |

---

## Citation Format

All citations must follow: **`DOC pPAGE REF`**

| Example | Meaning |
|---------|---------|
| `OL p5 §4.1` | Original Lease, page 5, section 4.1 |
| `A1 p3 §2.1` | Amendment 1, page 3, section 2.1 |
| `CM p1` | Commencement Memo, page 1 |
| `EX-A p2` | Exhibit A, page 2 |

---

## Date Conventions

| Context | Format | Example |
|---------|--------|---------|
| JSON / schema / exports | `YYYY-MM-DD` | `2025-06-01` |
| Abstracts / PDFs | `MM-DD-YYYY` | `06-01-2025` |

---

## Document Processing Order

Process documents in this order (best-effort; confirm if ambiguous):

1. **OL** -- Original Lease
2. **CM** -- Commencement Memo(s) / Delivery / Rent Commencement confirmation
3. **A1..An** -- Amendments in chronological order
4. Other modifying instruments (side letters, option memos) chronologically
