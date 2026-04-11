# Failure Triage Runbook

## Purpose
Deterministic triage flow for CI and harness-readiness failures.

## Scope
Applies to failures in:
- `quality-gates (format/lint/type/tests/eval)`
- `harness-smoke (deterministic offline)`

## Decision Flow (Summary)
1. Reproduce locally using the failing command.
2. If failure is deterministic and code-related, open/attach issue and fix in-scope.
3. If flaky/external, cap retries and escalate per incident policy.

## References
- CI workflow: `.github/workflows/ci-quality-gates.yml`
- Smoke command: `scripts/harness_smoke.sh`
