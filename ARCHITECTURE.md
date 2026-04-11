# ARCHITECTURE

## Pipeline Boundary
This repository implements an internal lease-document processing pipeline from extraction to evaluation artifacts.
Primary package: `leasegpt/`.
Primary runtime entrypoint: `leasegpt/cli.py`.

## Module Ownership & Dependency Layering
- **CLI / orchestration layer**: `leasegpt/cli.py`
- **Pipeline stage layer**: `leasegpt/pipeline/*.py`
- **Provider adapter layer**: `leasegpt/providers/*.py`
- **Core models/config/constants**: `leasegpt/models.py`, `leasegpt/config.py`, `leasegpt/constants.py`
- **Utility layer**: `leasegpt/utils/*.py`
- **Tests**: `tests/*.py`

Dependency rule: CLI may depend on pipeline/providers/models/utils; pipeline may depend on models/utils/providers but not CLI; providers should expose adapter behavior through provider interfaces; utils remain side-effect-light helpers.

## Pipeline Stages, Entrypoints, and Invariants

1. **Extract** (`leasegpt/pipeline/extract.py`)
   - Input: source document text/structured payload.
   - Output: normalized lease state payload.
   - Invariants:
     - schema-required top-level keys always present (possibly null/defaulted),
     - deterministic field normalization for identical inputs.

2. **Abstract** (`leasegpt/pipeline/abstract.py`)
   - Input: normalized lease state.
   - Output: abstracted lease summary content.
   - Invariants:
     - summary sections map to canonical schema sections,
     - no mutation of immutable source identity fields.

3. **Calendar** (`leasegpt/pipeline/calendar.py`)
   - Input: lease state with relevant date/rent terms.
   - Output: normalized event schedule.
   - Invariants:
     - events sorted deterministically by effective date,
     - date math uses shared utilities for consistency.

4. **Risk** (`leasegpt/pipeline/risk.py`)
   - Input: lease state/derived artifacts.
   - Output: risk findings with severity metadata.
   - Invariants:
     - risk entries include stable identifiers/categories,
     - severity taxonomy is consistent across providers.

5. **Portfolio** (`leasegpt/pipeline/portfolio.py`)
   - Input: single-lease outputs or grouped fixtures.
   - Output: rollups/aggregations.
   - Invariants:
     - aggregation metrics are reproducible from source artifacts,
     - missing optional lease attributes do not crash rollups.

6. **Diff** (`leasegpt/pipeline/diff.py`)
   - Input: baseline and candidate lease artifacts.
   - Output: deterministic change set.
   - Invariants:
     - unchanged fields are not emitted as diffs,
     - ordering of diff output is stable for same inputs.

7. **Render / Export** (`leasegpt/pipeline/render.py`, `leasegpt/pipeline/export.py`)
   - Input: pipeline artifacts.
   - Output: presentation/export artifacts.
   - Invariants:
     - render/export does not alter semantic data,
     - output paths and filenames follow utility/path conventions.

8. **Evaluate** (`leasegpt/pipeline/evaluate.py`)
   - Input: generated artifacts + golden fixtures.
   - Output: conformance/evaluation report.
   - Invariants:
     - scoring is deterministic for identical fixture sets,
     - report includes machine-readable pass/fail indicators.

## External Provider Boundary
Provider adapters in `leasegpt/providers/` encapsulate SDK-specific behavior so pipeline logic remains provider-agnostic.
