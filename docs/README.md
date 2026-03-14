# LeaseGPT — Repository Guide

This repository contains the knowledge files for **shortcut.ai_cre** (LeaseGPT), a modular commercial lease extraction and abstraction system organized as Agent Skills.

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
│       └── lease-export/
│           └── SKILL.md               # CSV/Excel export procedure
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

## The Four Skills

| Skill | Trigger | Produces |
|-------|---------|----------|
| **lease-extract** | "extract", "JSON", "schema", "validated data" | `lease_state` JSON + `change_log` + `pending_fields` + `traceability` |
| **lease-abstract** | "abstract", "summary", "investment-grade" | Markdown lease abstract (audience-tailored) |
| **lease-render** | "PDF", "render", "downloadable report" | Professional styled PDF |
| **lease-export** | "CSV", "Excel", "export", "rollup" | CSV/XLSX workbooks with provenance |

## Key Concepts

- **Single-tenant rule**: Each run processes exactly one tenant/leaseholder.
- **Sequential supersession**: Documents processed OL → CM → A1..An; later overrides earlier.
- **Per-field traceability**: Every field carries citation, confidence (0.0-1.0), and validation_status.
- **Progressive extraction**: Pass 1 (critical terms) returned promptly; Pass 2/3 on request.
- **Canonical section ordering**: 7 thematic sections defined in the lease-abstract skill.

## Schema

The canonical data contract is `v4_unified_schema.json` (v4.0.0, JSON Schema draft-07), located in `.claude/skills/lease-extract/references/`. All extraction and export outputs conform to this schema.
