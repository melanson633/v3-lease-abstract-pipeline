# AGENTS.md

## Purpose & Scope
This file defines the default operating contract for AI/code agents working in this repository.
Scope: entire repository unless a deeper `AGENTS.md` overrides a subtree.

## Workflow (Required)
1. **Plan first for non-trivial work**: create/update an execution checklist under `docs/exec-plans/active/` before significant implementation.
2. **Execute smallest complete slice**: implement the highest-priority unblocked item only.
3. **Verify with commands**: run relevant local checks before commit.
4. **Record evidence**: update the active execution plan with completion notes and blockers.
5. **Commit and PR**: use focused commits and include evidence in PR body.

## Required Checks Before Commit
At minimum, run checks that cover touched surfaces:
- `pytest` (or focused subset with rationale)
- `python -m leasegpt.cli --help` (CLI sanity)
- Any task-specific harness/eval command required by active execution plan

If any check is skipped or fails due to environment limits, document why in the plan and PR.

## Escalation & Boundaries
- Do not modify secrets, credentials, or production configs.
- Do not introduce network-dependent test requirements for default CI paths.
- Stop and record blocker when effort limit in the active plan is reached.
- Escalate by opening/annotating an issue when acceptance criteria cannot be met safely.

## Commit Conventions
- One logical change set per commit.
- Commit message style:
  - `docs: ...` for policy/process/docs changes
  - `ci: ...` for workflow/check changes
  - `feat|fix|refactor: ...` for code behavior changes
- Reference the execution checklist item(s) in the commit body when applicable.

## PR Conventions
PR description should include:
- intent/scope
- acceptance criteria mapped to checklist items
- verification commands + outcomes
- rollback plan

## Policy Hierarchy
Order of precedence:
1. direct system/developer/user instructions
2. nested `AGENTS.md` in deeper paths
3. this root `AGENTS.md`
