# Harness Readiness Execution Checklist

Purpose: Execute the full harness-readiness scope from `docs/harness_readiness_assessment.md` with bounded effort, observable completion, and compaction-safe continuity.

How to use:
- Work top-down by priority (`P0` → `P1` → `P2`), selecting highest-priority unblocked item first.
- Mark each task checkbox only when its completion contract is satisfied.
- If blocked after max effort, record blocker + evidence + next action in the task note and move on.

## P0 — Required before “harness-ready” claim

- [ ] **P0.1 Add root `AGENTS.md` contract**
  - Do: define agent workflow, required checks, escalation boundaries, commit/PR conventions, and policy scope.
  - Max effort: 60 minutes or 2 iterations.
  - Done when: `AGENTS.md` exists at repo root, covers all required sections, and is referenced by system-of-record index.

- [ ] **P0.2 Add root `ARCHITECTURE.md`**
  - Do: document pipeline boundaries, module ownership, dependency layering, and stage invariants.
  - Max effort: 90 minutes.
  - Done when: `ARCHITECTURE.md` exists, maps all pipeline stages/entrypoints, and includes invariant bullets per stage.

- [ ] **P0.3 Create `docs/system-of-record/index.md`**
  - Do: list canonical docs (schema/constants/skills/architecture/runbooks) and where to edit each.
  - Max effort: 45 minutes.
  - Done when: index exists and links to all canonical sources with explicit “source of truth” labels.

- [ ] **P0.4 Establish `docs/exec-plans/` operating structure**
  - Do: ensure `active/`, `completed/`, and `tech-debt-tracker.md`; add lightweight rule making plans mandatory for non-trivial work.
  - Max effort: 45 minutes.
  - Done when: directories/files exist and plan policy is documented in a discoverable location.

- [ ] **P0.5 Define CI quality gates**
  - Do: add CI workflow(s) gating format/lint/type/tests/eval fixtures; fail PRs on gate failure.
  - Max effort: 3 hours.
  - Done when: CI config enforces required checks on PR and branch protection-ready status checks are clearly named.

- [ ] **P0.6 Add deterministic harness smoke command**
  - Do: create one command/script/target running eval + offline e2e + artifact sanity checks.
  - Max effort: 2 hours.
  - Done when: command is documented, runnable locally and in CI, with stable exit codes.

- [ ] **P0.7 Add coverage reporting + thresholds**
  - Do: configure coverage output and minimum thresholds for CLI/pipeline surfaces.
  - Max effort: 2 hours.
  - Done when: CI fails below threshold; thresholds and rationale are documented.

- [ ] **P0.8 Add policy checks for required docs**
  - Do: machine-check presence/required sections of `AGENTS.md`, `ARCHITECTURE.md`, runbooks, and system-of-record.
  - Max effort: 2 hours.
  - Done when: automated check fails if required docs/sections are missing.

- [ ] **P0.9 Add structured PR template**
  - Do: require intent, acceptance criteria, evidence artifacts, rollback plan.
  - Max effort: 45 minutes.
  - Done when: template is default for PR creation and sections are explicit/required by convention.

- [ ] **P0.10 Add failure triage runbook**
  - Do: define auto-retry limits, incident-issue triggers, and human escalation rules.
  - Max effort: 90 minutes.
  - Done when: runbook exists, references CI/harness checks, and gives deterministic decision branches.

- [ ] **P0.11 Implement artifactized CI validation outputs**
  - Do: publish conformance report, summary, and diffs as CI artifacts for every PR.
  - Max effort: 2 hours.
  - Done when: PR runs attach artifacts with predictable names/paths and retention settings.

- [ ] **P0.12 Add dependency + secrets policy**
  - Do: document provider key handling, env constraints, allowed secret paths, and redaction rules.
  - Max effort: 90 minutes.
  - Done when: policy doc exists, is linked from system-of-record, and aligns with CI/security checks.

## P1 — High-leverage next

- [ ] **P1.13 Add static analysis stack**
  - Do: configure pinned lint/format/type tooling (e.g., Ruff + mypy/pyright) and CI enforcement.
  - Max effort: 2 hours.
  - Done when: local command + CI both enforce pinned config with documented invocation.

- [ ] **P1.14 Add mutation/property-based tests**
  - Do: add schema-evolution and changelog-coherence edge-case tests.
  - Max effort: 4 hours.
  - Done when: at least one robust property/mutation suite runs in CI and catches seeded regressions.

- [ ] **P1.15 Create ADRs for core contracts**
  - Do: add ADRs for pipeline/data-model assumptions and key interfaces.
  - Max effort: 2 hours.
  - Done when: ADR index exists and includes accepted decisions for major contracts.

- [ ] **P1.16 Add domain quality scorecard doc**
  - Do: define stage-by-stage quality dimensions and scoring update cadence.
  - Max effort: 90 minutes.
  - Done when: scorecard has baseline values and owner/update guidance.

- [ ] **P1.17 Add reproducible bug harness**
  - Do: add command/workflow capturing input fixture + expected vs actual artifacts.
  - Max effort: 3 hours.
  - Done when: one command reproduces a known failure and stores reproducible evidence.

- [ ] **P1.18 Add benchmark suite**
  - Do: measure throughput/latency/cost for extraction + downstream stages.
  - Max effort: 4 hours.
  - Done when: baseline benchmark output exists and is repeatable/documented.

- [ ] **P1.19 Add fixture versioning policy**
  - Do: define fixture update protocol, reviewer requirements, drift checks.
  - Max effort: 90 minutes.
  - Done when: policy is documented and linked to fixture-related CI checks.

- [ ] **P1.20 Add compatibility matrix**
  - Do: document supported Python/OS/provider SDK versions.
  - Max effort: 60 minutes.
  - Done when: matrix exists and is referenced by CI/test docs.

- [ ] **P1.21 Add provider abstraction conformance tests**
  - Do: ensure adapter behavior equivalence across supported providers.
  - Max effort: 4 hours.
  - Done when: conformance suite passes in CI with clear expected behavior contract.

- [ ] **P1.22 Add docs verification job**
  - Do: add link check, stale-reference detection, and required-section validation.
  - Max effort: 2 hours.
  - Done when: docs verifier runs in CI and fails on broken/stale docs.

- [ ] **P1.23 Add schema migration playbook**
  - Do: define backward-compat policy, migration steps, and deprecation windows.
  - Max effort: 90 minutes.
  - Done when: playbook exists with concrete migration and rollback procedures.

- [ ] **P1.24 Add observability guide**
  - Do: document logs, failure classes, and metrics naming conventions.
  - Max effort: 90 minutes.
  - Done when: guide maps key runtime paths to expected telemetry.

## P2 — Scale/autonomy optimization

- [ ] **P2.25 Automate entropy cleanup jobs**
  - Do: schedule recurring cleanup checks and auto-PR workflow with bounded scope.
  - Max effort: 3 hours.
  - Done when: scheduled job exists and opens scoped remediation PRs.

- [ ] **P2.26 Add auto-labeling/routing for PRs/issues**
  - Do: map touched areas to labels/owners/risk levels.
  - Max effort: 2 hours.
  - Done when: rules auto-apply labels/routes on new PRs/issues.

- [ ] **P2.27 Add artifact diff visualizations**
  - Do: generate human-readable conformance/output deltas per PR.
  - Max effort: 3 hours.
  - Done when: PR artifacts include diff views enabling quick regression triage.

- [ ] **P2.28 Add confidence trend dashboards**
  - Do: aggregate conformance metrics across commits/time.
  - Max effort: 4 hours.
  - Done when: dashboard/report shows trend lines with reproducible data source.

- [ ] **P2.29 Add “golden principles” codification doc**
  - Do: define mechanical style rules and anti-pattern bans.
  - Max effort: 90 minutes.
  - Done when: principles doc exists and is enforced by tooling/review checklist.

- [ ] **P2.30 Add merge philosophy guide for agent PRs**
  - Do: define batching, auto-merge criteria, and rollback cadence.
  - Max effort: 90 minutes.
  - Done when: guide is published and referenced by PR/triage docs.

- [ ] **P2.31 Add autonomous CI remediation loops**
  - Do: automate fixes for common failures with bounded retries and audit trail.
  - Max effort: 4 hours.
  - Done when: remediation automation is active, retry-bounded, and logs decisions.

- [ ] **P2.32 Define repository garbage-collection SLOs**
  - Do: set drift budgets and time-to-cleanup targets.
  - Max effort: 60 minutes.
  - Done when: SLOs are documented with measurable indicators and review cadence.

## Continuity / compaction handoff protocol

- At natural pause or context pressure, update this file before ending turn:
  - Mark completed tasks and add 1-line evidence note under each completed item.
  - For in-progress/blocked items, add: current state, precise blocker, next action, and owner.
  - Reorder only if dependencies force it; otherwise preserve priority order.
- Anti-churn rule: do **not** reopen completed tasks unless new evidence shows acceptance criteria are unmet.
- Blocking rule: after max effort hit, record blocker and move to next highest-priority unblocked task.
