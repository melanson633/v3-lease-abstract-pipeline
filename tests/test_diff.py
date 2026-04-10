from __future__ import annotations

from leasegpt.pipeline.diff import build_diff
from leasegpt.utils.io import coerce_bundle_shape, load_json
from leasegpt.utils.paths import skills_root


def _fixture(name: str) -> dict:
    payload = load_json(skills_root() / "lease-eval" / "fixtures" / name / "lease_state.json")
    return coerce_bundle_shape(payload)


def test_diff_reports_expected_change_count_and_groups() -> None:
    result = build_diff(_fixture("golden_ol_a1"))
    assert result.manifest["change_entry_count"] == 6
    groups = result.manifest["groups"]
    assert "Dates" in groups
    assert "TI Allowance" in groups
