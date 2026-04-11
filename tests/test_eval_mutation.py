from __future__ import annotations

from copy import deepcopy

import pytest

from leasegpt.pipeline.evaluate import evaluate_bundle
from leasegpt.utils.io import coerce_bundle_shape, load_json
from leasegpt.utils.paths import skills_root


def _fixture(name: str = "golden_ol_a1") -> dict:
    payload = load_json(skills_root() / "lease-eval" / "fixtures" / name / "lease_state.json")
    return coerce_bundle_shape(payload)


def _mutate_current_state_mismatch(bundle: dict) -> dict:
    mutated = deepcopy(bundle)
    first_entry = mutated["change_log"][0]
    field_path = first_entry["field_path"]
    first_entry["new_value"] = "__intentionally_wrong__"
    return mutated, field_path, "current_state_mismatch"


def _mutate_incomplete_citation_pair(bundle: dict) -> dict:
    mutated = deepcopy(bundle)
    first_entry = mutated["change_log"][0]
    first_entry["source_document"] = "OL"
    first_entry["citation"] = ""
    return mutated, first_entry["field_path"], "incomplete_citation_pair"


def _mutate_pending_populated(bundle: dict) -> dict:
    mutated = deepcopy(bundle)
    mutated["pending_fields"].append({"path": "Parties.Tenant.Name", "reason": "seeded-regression"})
    return mutated, "Parties.Tenant.Name", "pending_but_populated"


@pytest.mark.parametrize(
    "mutator,expected_verdict,expected_issue",
    [
        (_mutate_current_state_mismatch, "FAIL", "current_state_mismatch"),
        (_mutate_incomplete_citation_pair, "WARN", "incomplete_citation_pair"),
        (_mutate_pending_populated, "WARN", "pending_but_populated"),
    ],
)
def test_eval_mutation_suite_detects_seeded_regressions(mutator, expected_verdict: str, expected_issue: str) -> None:
    bundle = _fixture()
    mutated, expected_path, issue_code = mutator(bundle)

    result = evaluate_bundle(mutated)
    report = result.conformance_report

    assert report["verdict"] == expected_verdict
    issues = report["checks"]["change_log_coherence"]["issues"] + report["checks"]["pending_fields_sanity"]["issues"]
    matching = [item for item in issues if item.get("issue") == issue_code]
    assert matching, f"Expected issue code {expected_issue} for {expected_path}"
