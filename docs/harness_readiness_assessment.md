# Harness Engineering Readiness Assessment

Date: 2026-04-11

This assessment benchmarks the repository against the OpenAI Harness Engineering model (agent-first engineering focused on repository legibility, explicit system-of-record docs, eval loops, enforced standards, and continuous entropy management).

## Executive assessment

**Current confidence level: _partially ready_ (foundation exists, harness controls incomplete).**

The repo already has strong building blocks for harness engineering:
- Clear CLI entrypoints and modular pipeline stages (`extract`, `eval`, `abstract`, `render`, `export`, `calendar`, `diff`, `risk`, `portfolio`).
- Golden fixtures and automated tests that validate core deterministic workflows.
- A schema-first data contract and skill-oriented documentation layout.

However, several harness-critical capabilities are missing or only implicit:
- No explicit `AGENTS.md` operating contract for autonomous agents.
- No architecture map and policy docs that function as machine-readable “system of record.”
- No CI policy that gates merges on eval quality signals beyond local pytest.
- No continuous “entropy cleanup” loop (lint/refactor drift scanners + auto-PR routines).
- No autonomous runbook for reproducible bug capture, artifact evidence, and escalation.

## Evidence snapshot (what exists today)

1. Runtime and workflow orchestration are implemented via a single Typer CLI with both full pipeline (`run`, `run-from-json`) and stage-level commands.  
2. Schema and skill references exist under `.claude/skills/*`, with extraction and eval fixtures present for regression checks.  
3. Tests cover eval, calendar, diff, portfolio, and offline CLI end-to-end behavior.  
4. Project metadata exists in `pyproject.toml`, but there is no documented CI matrix, architecture contract, or agent governance file in repo root.

## Prioritized task list to become harness-ready

> Priority legend: **P0** = must-have to claim harness readiness, **P1** = high leverage next, **P2** = scale optimizations.

### P0 — Must complete before declaring harness-ready

1. **Create root `AGENTS.md` with enforceable agent workflow contract** (task intake, required checks, escalation conditions, commit/PR conventions, no-manual-code policy scope).
2. **Create root `ARCHITECTURE.md`** mapping pipeline boundaries, module ownership, dependency layering, and invariants for each stage.
3. **Create `docs/system-of-record/index.md`** that explicitly points agents to canonical sources (schema, constants, skill docs, architecture, runbooks).
4. **Create `docs/exec-plans/` structure** (`active/`, `completed/`, `tech-debt-tracker.md`) and make plan files mandatory for non-trivial work.
5. **Define repository quality gates in CI** (format/lint/type/tests + eval fixture checks) and block merges on failure.
6. **Add deterministic harness smoke command** (single command that runs eval + offline end-to-end + artifact checks).
7. **Add coverage reporting + minimum thresholds** for pipeline and CLI surfaces.
8. **Add machine-readable policy checks** for required docs (`AGENTS.md`, architecture, runbooks) so they cannot drift/missing.
9. **Introduce structured PR template** requiring intent, acceptance criteria, evidence artifacts, and rollback plan.
10. **Add failure triage runbook** documenting when agents auto-retry, when to open incident issues, and when to escalate to humans.
11. **Implement artifactized validation outputs** (store conformance report, summary, and diff artifacts in CI for every PR).
12. **Create explicit dependency + secrets policy** for providers (key handling, env constraints, redaction rules).

### P1 — High-leverage improvements immediately after P0

13. **Add static analysis stack** (`ruff`/equivalent lint, formatting, and strict type checks) with pinned config in repo.
14. **Add mutation or property-based tests** for schema evolution and change-log coherence edge cases.
15. **Create architecture decision records (ADRs)** for key pipeline contracts and data model assumptions.
16. **Add domain quality scorecard doc** grading each pipeline stage and updating over time.
17. **Create reproducible bug reproduction harness** (input fixture + expected/actual artifact capture command).
18. **Add benchmark suite** for throughput/latency/cost of extraction and downstream stages.
19. **Pin and version golden fixtures policy** (fixture update protocol, reviewer requirements, drift detection).
20. **Add compatibility matrix** (Python versions, OS assumptions, provider SDK versions).
21. **Add API/model abstraction conformance tests** to ensure provider adapters remain behaviorally equivalent.
22. **Implement docs verification job** (link checking, stale reference detection, required section validator).
23. **Add schema migration playbook** with backward compatibility policy and deprecation windows.
24. **Create observability guide** for runtime logs, failure classes, and metrics naming conventions.

### P2 — Scale/autonomy optimizations

25. **Automate recurring entropy cleanup jobs** (duplicate helpers, dead code, style drift) via scheduled agent PRs.
26. **Introduce auto-labeling + auto-routing for PRs/issues** based on touched pipeline area and risk profile.
27. **Add artifact diff visualizations** (conformance delta, output delta) to speed agent/human review.
28. **Implement confidence trend dashboards** from conformance results across commits.
29. **Add “golden principles” codification doc** with mechanical style rules and anti-pattern bans.
30. **Create merge philosophy guide for high-throughput agent PRs** (batching strategy, auto-merge rules, rollback cadence).
31. **Add autonomous remediation loops** for common CI failures (flake, formatting, missing docs) with bounded retries.
32. **Define periodic repository garbage-collection SLOs** (time-to-cleanup and allowable drift budgets).

## Suggested implementation sequence (90-day)

- **Days 1–14:** complete P0 items 1–6 (agent contract, architecture, system-of-record, exec plan scaffolding, CI gates, harness smoke command).
- **Days 15–30:** complete P0 items 7–12 (coverage gates, policy checks, PR template, triage runbook, artifacts, secrets/dependency policy).
- **Days 31–60:** execute P1 items 13–20 (analysis rigor, ADRs, scorecard, benchmarks, fixture governance, compatibility matrix).
- **Days 61–90:** execute P1 items 21–24 and initial P2 automation (adapter conformance tests, docs verifier, migration playbook, entropy jobs).

## Readiness exit criteria

You can confidently declare this repo **harness-ready** once all are true:

1. Agents have a complete, enforceable operating contract and architecture map in-repo.
2. CI blocks merges on deterministic harness checks and quality standards.
3. Repository docs are the authoritative system-of-record and are automatically validated.
4. Evaluation artifacts are captured per PR and compared over time.
5. Continuous entropy cleanup runs on cadence with measurable debt burn-down.
6. Human escalation boundaries are explicit, tested, and auditable.
