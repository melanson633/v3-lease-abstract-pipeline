# Dependency and Secrets Policy

## Purpose
Define required controls for dependency handling, provider key management, and secret redaction in this repository.

## Provider Key Handling
- Provider/API credentials must be supplied through environment variables only.
- Allowed local source for developer secrets: untracked `.env` file loaded manually by developer tooling.
- `.env.example` may contain placeholders only, never live keys.
- Hardcoding provider keys in code, fixtures, docs, or tests is prohibited.

## Environment Constraints
- Default CI/test paths must run without network-required provider calls.
- New tests must use local fixtures/mocks and cannot require live external credentials.
- CLI commands used in CI must remain deterministic with fixture-backed inputs.

## Allowed Secret Paths
- Local-only, ignored paths: `.env`, `.env.local`, and developer-specific shell profiles.
- Disallowed paths for any secret material: tracked files under `leasegpt/`, `tests/`, `.github/`, `docs/`, and fixture directories.

## Redaction Rules
- Never print full secret values in logs, PR text, or incident reports.
- When evidence is required, show only last 4 characters (example: `****ABCD`).
- Redact bearer tokens, API keys, and connection URIs before storing CI artifacts.

## Dependency Policy
- Runtime and dev dependencies must be declared in `pyproject.toml`.
- Dependency changes require:
  1. rationale in PR description,
  2. passing CI quality gates,
  3. successful `pip check` in CI.
- Avoid adding dependencies that force network access in default test/CI workflows.

## CI / Security Check Alignment
Current enforcement points:
- `.github/workflows/ci-quality-gates.yml` runs deterministic checks + docs policy.
- `scripts/check_required_docs.py` verifies required policy/runbook docs are present with key section markers.
- `python -m pip check` validates install-time dependency integrity in CI jobs.

Future hardening (tracked separately): dedicated secret scanning workflow and dependency vulnerability scanning gate.
