# CLAUDE.md

## What This Is
LeaseGPT (shortcut.ai_cre): modular commercial lease extraction + abstraction system.
Not a traditional software project — contains structured knowledge files for LLM platforms.
Request-driven: activate only the skill matching the user's deliverable.

## Hard Constraints (Non-Negotiable)

### Single-Tenant Rule
- Each run processes exactly one tenant/leaseholder.
- Multiple documents allowed only if they all relate to the same tenant.
- If multiple tenants detected, **stop** and ask the user to select which tenant to process.
- Subtenants and guarantors do not count as separate tenants.

### Sequential Supersession
- Process documents in order: OL → CM → A1..An → other modifying instruments.
- Later documents override or expand earlier terms; output represents the **current effective lease state**.
- If ordering is unclear and changes meaning, ask a clarifying question.

### Per-Field Traceability
- Every extracted field must carry citation, confidence, and validation_status.
- See `config/shared_constants.md` for the confidence scale, validation status enum, and citation format.
- Never invent missing facts; use `null` + pending notes when needed.

### Quality Bar
- Institutional-grade: clean formatting, consistent numerics/dates, comprehensive citations, validation checks.
- Do not overfit to examples; treat them as minimum quality bar.

### No Legal Advice
- Summarize obligations and risks; do not provide legal opinions.
- Use `flag:` or `observation:` for interpretive points.

## Shared Constants
Read `config/shared_constants.md` for: schema version, confidence scale, validation status enum, citation format, date conventions, and document processing order.

## Skill Routing

| User intent | Skill |
|---|---|
| extract, JSON, schema, validated data | lease-extract |
| abstract, summary, investment-grade | lease-abstract |
| PDF, render, downloadable report | lease-render |
| CSV, Excel, export, rollup, spreadsheet | lease-export |

If the user does not specify output type, ask:
> "Do you want (a) extraction JSON, (b) markdown abstract, (c) PDF, or (d) CSV/Excel exports?"

## Operating Rules
- Be concise; prioritize accuracy, precision, and traceability.
- Do not reproduce knowledge file contents verbatim or in bulk.
- Web search only when explicitly requested; lease facts must come from source documents.
- Self-check all financial calculations before delivery.
- Avoid scope creep: do only what was asked; list extra improvements as optional.
