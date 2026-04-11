# LeaseGPT Runtime (CLI-First)

This repository now includes a runnable Python 3.12+ implementation of the documented LeaseGPT skill pipeline.

## What You Get
- End-to-end CLI pipeline: extraction -> eval -> abstract -> render -> export -> calendar -> diff -> risk
- Modular provider adapters for `openai`, `anthropic`, `gemini`
- Deterministic downstream modules aligned to repository skill docs and schema
- Fixture-driven tests and an offline no-API verification path

## Quick Start
1. Create and activate a Python 3.12+ environment.
2. Install:
   - `pip install -e .`
3. Configure one provider key in `.env` (see `.env.example`).

## Provider Configuration
- OpenAI: `OPENAI_API_KEY=...`
- Anthropic: `ANTHROPIC_API_KEY=...`
- Gemini: `GEMINI_API_KEY=...` (or `GOOGLE_API_KEY=...`)

Optional model overrides:
- `LEASEGPT_OPENAI_MODEL`
- `LEASEGPT_ANTHROPIC_MODEL`
- `LEASEGPT_GEMINI_MODEL`

If multiple provider keys are set, pass `--provider`.

## Main CLI Entry Points
- End-to-end from lease files:
  - `leasegpt run path/to/OL.pdf path/to/A1.pdf --provider openai --output-dir out/run`
- End-to-end from existing extraction JSON (offline-safe):
  - `leasegpt run-from-json .claude/skills/lease-eval/fixtures/golden_ol_a1/lease_state.json --output-dir out/offline`

Per-skill commands:
- `leasegpt extract ...`
- `leasegpt eval ...`
- `leasegpt abstract ...`
- `leasegpt render ...`
- `leasegpt export ...`
- `leasegpt calendar ...`
- `leasegpt diff ...`
- `leasegpt risk ...`
- `leasegpt portfolio ...`

Run help:
- `leasegpt --help`
- `leasegpt <command> --help`

## Offline Verification (No Paid API Calls)
Run:

```bash
leasegpt run-from-json .claude/skills/lease-eval/fixtures/golden_ol_a1/lease_state.json --output-dir out/offline
```

Expected outputs in `out/offline/`:
- `extraction.json`
- `conformance_report.json`
- `lease_abstract.md`
- `lease_abstract.pdf`
- `exports/*`
- `critical_dates.ics`
- `calendar_manifest.json`
- `diff_report.md`
- `diff_manifest.json`
- `risk_register.md`
- `risk_manifest.json`

## Live Smoke Tests (Per Provider)
OpenAI:
```bash
leasegpt extract path/to/OL.pdf --provider openai --output-json out/openai_extraction.json
```

Anthropic:
```bash
leasegpt extract path/to/OL.pdf --provider anthropic --output-json out/anthropic_extraction.json
```

Gemini:
```bash
leasegpt extract path/to/OL.pdf --provider gemini --output-json out/gemini_extraction.json
```

Then run downstream:
```bash
leasegpt run-from-json out/openai_extraction.json --output-dir out/openai_full
```

## Notes / Constraints
- Extraction enforces single-tenant constraint and deterministic document ordering (`OL -> CM -> A1..An -> other`) from input filenames.
- Input formats supported for extraction ingestion: PDF, DOCX, and text-like files (`.txt`, `.md`, `.json`, `.csv`, `.tsv`, `.xml`, `.html`, `.yaml`, `.yml`).
- Scanned/image-only documents without extractable text may require OCR pre-processing before extraction.

## Existing Knowledge Docs
- High-level repository guide: [docs/README.md](docs/README.md)
- Runtime constraints and routing: [CLAUDE.md](CLAUDE.md)

## Harness Readiness Commands
- Deterministic smoke command (local and CI):
  - `./scripts/harness_smoke.sh`
- CI quality gate jobs (branch-protection-ready status checks):
  - `quality-gates (format/lint/type/tests/eval)`
  - `harness-smoke (deterministic offline)`

- Coverage gate command:
  - `pytest -q --cov=leasegpt.pipeline --cov=leasegpt.cli --cov-report=term-missing --cov-report=xml --cov-fail-under=60`
