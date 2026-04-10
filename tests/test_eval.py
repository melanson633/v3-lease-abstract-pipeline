from __future__ import annotations

from leasegpt.pipeline.evaluate import evaluate_bundle
from leasegpt.utils.io import coerce_bundle_shape, load_json
from leasegpt.utils.paths import skills_root


def _fixture(name: str) -> dict:
    payload = load_json(skills_root() / "lease-eval" / "fixtures" / name / "lease_state.json")
    return coerce_bundle_shape(payload)


def test_eval_golden_ol_only_passes() -> None:
    result = evaluate_bundle(_fixture("golden_ol_only"))
    assert result.conformance_report["verdict"] == "PASS"
    assert result.conformance_report["checks"]["schema_conformance"]["pass"] is True


def test_eval_golden_ol_a1_passes() -> None:
    result = evaluate_bundle(_fixture("golden_ol_a1"))
    assert result.conformance_report["verdict"] == "PASS"
    assert result.conformance_report["checks"]["change_log_coherence"]["pass"] is True
