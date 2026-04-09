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
| validate, conformance, regression test, golden fixture | lease-eval |
| calendar, ICS, critical dates, notice deadlines, tickler | lease-calendar |
| diff, change_log report, amendment delta, overwrite preview | lease-diff |
| risk register, flag review, exposure scan | lease-risk |
| portfolio analytics, WALT, expiration ladder, tenant concentration | lease-portfolio |

If the user does not specify output type, ask:
> "Do you want (a) extraction JSON, (b) markdown abstract, (c) PDF, (d) CSV/Excel exports, or (e) critical-dates calendar?"

`lease-eval` is a pipeline-internal skill: it runs *on* extraction JSON to gate downstream skills, not to produce a user-facing deliverable. Invoke it when the user asks to validate an extraction or when a candidate JSON needs a regression check before feeding it into another skill.

`lease-calendar` consumes validated extraction JSON and produces an ICS feed plus a JSON manifest of critical dates (commencement, expiration, rent steps, renewal notice deadlines, guaranty burn-off). Run `lease-eval` first when possible — a PASS verdict guarantees every dated field has a citation the calendar can trace.

`lease-diff` converts `change_log` into a stakeholder-ready diff deliverable: grouped markdown report plus JSON manifest with chronology, citation pairs, and optional reverse-diff overwrite preview from a draft amendment. It walks the existing log chronologically and treats the earliest `old_value` per path as the origin state.

`lease-risk` formalizes `flag:`/`observation:` conventions into a structured risk register. It applies rule-based pattern checks and rule-based dollar exposure formulas only when required inputs exist; otherwise it emits severity without invented dollar values.

`lease-portfolio` aggregates multiple previously validated single-tenant extraction outputs into portfolio metrics (WALT, expiration ladder, rent roll, concentration, TI/deposit exposure). This does not violate the single-tenant extraction rule because aggregation occurs after separate per-tenant extraction runs.

## Operating Rules
- Be concise; prioritize accuracy, precision, and traceability.
- Do not reproduce knowledge file contents verbatim or in bulk.
- Web search only when explicitly requested; lease facts must come from source documents.
- Self-check all financial calculations before delivery.
- Avoid scope creep: do only what was asked; list extra improvements as optional.
