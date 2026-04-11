# Harness Quality Gates

## Coverage Thresholds
Coverage is enforced for high-risk runtime surfaces:
- `leasegpt/cli.py`
- `leasegpt/pipeline/*`

Threshold:
- minimum total coverage: **60%** (`--cov-fail-under=60`)

Rationale:
- Current repository baseline has strong pipeline-focused tests but still includes untyped/provider-heavy paths.
- 60% matches the current measured baseline (~64%) while still blocking regressions.
- Threshold should be raised after P1 test expansion items land.

## Local Command
```bash
pytest -q --cov=leasegpt.pipeline --cov=leasegpt.cli --cov-report=term-missing --cov-report=xml --cov-fail-under=60
```


## Static Analysis Stack
Pinned tooling is declared in `pyproject.toml` dev dependencies:
- `ruff==0.13.0`
- `mypy==1.18.2`

Local command:
```bash
./scripts/static_analysis.sh
```

CI enforcement:
- `.github/workflows/ci-quality-gates.yml` runs `./scripts/static_analysis.sh` in `quality-gates`.
