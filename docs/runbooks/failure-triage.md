# Failure Triage Runbook

## Purpose
Deterministic triage flow for CI and harness-readiness failures.

## Scope
Applies to failures in:
- `quality-gates (format/lint/type/tests/eval)` from `.github/workflows/ci-quality-gates.yml`
- `harness-smoke (deterministic offline)` from `.github/workflows/ci-quality-gates.yml`
- local harness verification command `./scripts/harness_smoke.sh`

## Inputs Required for Every Triage
1. Failing job name + failing step name.
2. Commit SHA and PR number.
3. Relevant artifact bundle from CI (`quality-gates-validation-artifacts` and/or `harness-smoke-validation-artifacts`).
4. Local reproduction command and result.

## Auto-Retry Policy (Deterministic Limits)

### Retry-eligible classes
A failure is retry-eligible only when it is clearly external/transient and not code-dependent, for example:
- GitHub Actions runner outage / infrastructure interruption.
- Package index timeout during dependency install.
- Artifact upload transport failure.

### Retry limits
- Per failing job: **maximum 1 automatic re-run**.
- Per PR across all jobs: **maximum 2 total re-runs**.
- If a retry reproduces the same step failure twice, mark **deterministic failure** and move to root-cause branch (no additional retries).

## Decision Flow (Summary)
1. Classify failure (deterministic code/config vs transient infra).
2. Execute bounded retries only for retry-eligible classes.
3. If still failing or not retry-eligible, reproduce locally with mapped command.
4. Open/append incident issue when trigger conditions are met.
5. Escalate to human owner by severity/branch below.

## Deterministic Decision Branches

### Branch A — Quality gate failure (`quality-gates`)
- Map failed CI step to local command:
  - `Format check (ruff format)`: `ruff format --check .`
  - `Lint check (ruff)`: `ruff check .`
  - `Type check (mypy)`: `mypy leasegpt`
  - `Unit tests + coverage gate`: `pytest -q --cov=leasegpt.pipeline --cov=leasegpt.cli --cov-report=term-missing --cov-report=xml --cov-fail-under=60`
  - `Eval fixtures check`: `pytest -q tests/test_eval.py`
  - `Required docs policy check`: `python scripts/check_required_docs.py`
- If local reproduction fails, create fix PR/commit immediately.
- If local reproduction passes but CI fails twice on same step, treat as environment issue and trigger incident issue.

### Branch B — Harness smoke failure (`harness-smoke`)
- Run: `./scripts/harness_smoke.sh`.
- Verify required outputs exist under `.tmp/harness-smoke/offline/`:
  `conformance_report.json`, `conformance_summary.md`, `diff_report.md`, `diff_manifest.json`.
- If any required artifact missing locally, treat as deterministic regression and fix before merge.
- If local smoke passes and CI failed twice on upload/download-only errors, create incident issue and request infra review.

### Branch C — Artifactized validation output mismatch
- Compare files from CI artifact bundle vs local run outputs.
- If conformance verdict changed unexpectedly or diff manifest is malformed, block merge and escalate to pipeline owner.
- If only markdown formatting differs with identical JSON semantics, classify as low severity and patch in next PR.

## Incident-Issue Trigger Rules
Open or append to an incident issue when any of the following are true:
1. Same failing step occurs on 2+ consecutive commits in the same PR.
2. Retry limit reached (job or PR limit).
3. Failure affects `main` branch protection checks.
4. Artifact bundle missing expected files after a successful step execution.

Required incident fields:
- failing workflow/job/step
- first-seen timestamp (UTC)
- commit SHA(s)
- retry count used
- local reproduction result
- links to CI run + downloaded artifacts

## Human Escalation Rules
- **Immediate escalation (within 30 minutes):** failures on `main` branch or release-critical PRs.
- **Standard escalation (same business day):** persistent PR-only failures after retry budget consumed.

Escalation targets:
1. PR author (owner of change set)
2. pipeline maintainer (from CODEOWNERS/maintainer rotation)
3. repository admin (only for CI infrastructure/security control failures)

## Exit Criteria for Triage
Triage is complete only when one is true:
- Fix merged and all required checks pass.
- Incident issue opened with evidence + owner + next action.
- Failure confirmed as external outage and PR is explicitly blocked pending infra recovery.

## References
- CI workflow: `.github/workflows/ci-quality-gates.yml`
- Smoke command: `scripts/harness_smoke.sh`
- Execution checklist: `docs/exec-plans/active/harness-readiness-execution-checklist.md`
