# LeaseGPT — Repository Guide

This repository contains the knowledge files for **shortcut.ai_cre** (LeaseGPT), plus a runnable Python CLI runtime that operationalizes those skill contracts.

---

## Repository Structure

```
v3-lease-abstract-pipeline/
├── CLAUDE.md                          # Universal hard constraints + skill routing
├── config/
│   └── shared_constants.md            # Confidence scale, validation status, citation format, dates
├── .claude/
│   └── skills/
│       ├── lease-extract/
│       │   ├── SKILL.md               # Extraction procedure (JSON from lease docs)
│       │   └── references/
│       │       ├── v4_unified_schema.json   # Canonical JSON schema (v4.0.0)
│       │       └── schema_priority_map.md   # Pass 1/2/3 field ordering
│       ├── lease-abstract/
│       │   ├── SKILL.md               # Abstraction procedure (markdown from JSON)
│       │   └── references/
│       │       └── style_guide_markdown.md  # Table/formatting authoring rules
│       ├── lease-render/
│       │   ├── SKILL.md               # PDF render procedure (PDF from markdown)
│       │   └── references/
│       │       ├── style_guide_pdf.md       # PDF layout standards
│       │       └── lease_abstract_pdf_style_tokens.yaml  # Design tokens
│       ├── lease-export/
│       │   └── SKILL.md               # CSV/Excel export procedure
│       ├── lease-eval/
│       │   ├── SKILL.md               # Schema conformance + golden fixture diff
│       │   ├── fixtures/
│       │   │   ├── golden_ol_only/    # Anonymized OL-only lease_state (baseline)
│       │   │   └── golden_ol_a1/      # Anonymized OL + A1 lease_state (exercises change_log)
│       │   └── references/
│       │       └── conformance_checklist.md  # All checks + failure/fix table
│       ├── lease-calendar/
│       │   ├── SKILL.md               # Critical-dates ICS + JSON manifest procedure
│       │   └── references/
│       │       └── event_catalog.md   # Event types, derivation rules, skip reasons
│       ├── lease-diff/
│       │   ├── SKILL.md               # Amendment-aware change_log diff procedure
│       │   └── references/
│       │       └── diff_rules.md      # Normalization/grouping/column ordering rules
│       ├── lease-risk/
│       │   ├── SKILL.md               # Risk register detection procedure
│       │   └── references/
│       │       └── risk_patterns.md   # Risk rules, severity tiers, exposure formulas
│       └── lease-portfolio/
│           ├── SKILL.md               # Portfolio analytics rollup procedure
│           ├── fixtures/
│           │   └── golden_office_harbortech/
│           │       ├── README.md
│           │       └── lease_state.json
│           └── references/
│               └── rollup_metrics.md  # WALT, ladder, concentration, exposure formulas
├── leasegpt/                          # Runtime package (CLI + core pipeline + providers)
├── tests/                             # Fixture-driven runtime tests
├── pyproject.toml                     # Python project config
├── .env.example                       # Provider configuration template
├── README.md                          # Runtime quick start
└── docs/
    └── README.md                      # This file
```

## Architecture: Three-Layer Progressive Disclosure

The system uses Agent Skills with three layers to minimize context loading:

| Layer | What loads | When |
|-------|-----------|------|
| **Layer 1** (frontmatter) | Skill name + trigger description (~6 lines each) | Always — for intent routing |
| **Layer 2** (SKILL.md body) | Full procedure for the activated skill | On skill activation |
| **Layer 3** (references/) | Supporting files (schema, style guides, tokens) | On demand, when the procedure directs |

`CLAUDE.md` and `config/shared_constants.md` are always available as universal context.

## The Nine Skills

| Skill | Trigger | Produces |
|-------|---------|----------|
| **lease-extract** | "extract", "JSON", "schema", "validated data" | `lease_state` JSON + `change_log` + `pending_fields` + `traceability` |
| **lease-abstract** | "abstract", "summary", "investment-grade" | Markdown lease abstract (audience-tailored) |
| **lease-render** | "PDF", "render", "downloadable report" | Professional styled PDF |
| **lease-export** | "CSV", "Excel", "export", "rollup" | CSV/XLSX workbooks with provenance |
| **lease-eval** | "validate", "conformance", "regression test", "golden fixture" | Conformance report (PASS/WARN/FAIL) + optional golden fixture diff |
| **lease-calendar** | "calendar", "ICS", "critical dates", "notice deadlines", "tickler" | RFC 5545 ICS feed + JSON manifest of dated obligations |
| **lease-diff** | "diff", "change log", "amendment delta", "overwrite preview" | Markdown diff report + JSON manifest with per-path chronology and citation pairs |
| **lease-risk** | "risk register", "flag review", "exposure scan" | Structured risk register (markdown + JSON manifest), including zero-risk outputs |
| **lease-portfolio** | "portfolio rollup", "WALT", "expiration ladder", "tenant concentration" | Portfolio markdown summary + JSON metrics manifest over multiple leases |

`lease-eval` is a pipeline-internal gate. It runs on extraction JSON to catch schema, provenance, and change-log regressions before downstream skills consume the data. It does not produce a user-facing deliverable on its own.

`lease-calendar` reads dated fields from a validated `lease_state` and emits a schedulable calendar: commencement, expiration, rent steps, renewal notice deadlines, guaranty burn-off. Derived dates (notice deadlines) record their formulas in the manifest for auditability. Skips trigger-based windows (ROFO/ROFR) rather than synthesizing fake dates.

`lease-diff` elevates `change_log` into a first-class deliverable: grouped amendment chronology, OL -> A1 -> A2 path progression, citation pairs, and optional reverse diff preview from draft amendments.

`lease-risk` formalizes operational `flag:`/`observation:` findings into rule-based risk rows with explicit severity and formula-governed exposure handling. If formula inputs are missing, severity is still emitted but dollar values are intentionally omitted.

`lease-portfolio` computes portfolio analytics from prior single-tenant extraction outputs (WALT, expiration ladder, rent roll, concentration, TI/deposit exposure). This aggregation stage is intentionally downstream and does not violate the extraction-time single-tenant rule.

## Key Concepts

- **Single-tenant rule**: Each run processes exactly one tenant/leaseholder.
- **Sequential supersession**: Documents processed OL → CM → A1..An; later overrides earlier.
- **Per-field traceability**: Every field carries citation, confidence (0.0-1.0), and validation_status.
- **Progressive extraction**: Pass 1 (critical terms) returned promptly; Pass 2/3 on request.
- **Canonical section ordering**: 7 thematic sections defined in the lease-abstract skill.

## Schema

The canonical data contract is `v4_unified_schema.json` (v4.0.0, JSON Schema draft-07), located in `.claude/skills/lease-extract/references/`. All extraction and export outputs conform to this schema.

## Runtime Commands

The Python runtime exposes:
- `leasegpt run` for full document-to-deliverables flow using a configured LLM provider.
- `leasegpt run-from-json` for offline downstream verification from existing extraction JSON.
- Per-skill commands: `extract`, `eval`, `abstract`, `render`, `export`, `calendar`, `diff`, `risk`, `portfolio`.

See root `README.md` for setup and command examples.
