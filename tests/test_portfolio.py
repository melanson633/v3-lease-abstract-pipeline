from __future__ import annotations

from leasegpt.pipeline.portfolio import build_portfolio
from leasegpt.utils.io import coerce_bundle_shape, load_json
from leasegpt.utils.paths import skills_root


def _eval_fixture(name: str) -> dict:
    payload = load_json(skills_root() / "lease-eval" / "fixtures" / name / "lease_state.json")
    return coerce_bundle_shape(payload)


def _portfolio_fixture(name: str) -> dict:
    payload = load_json(skills_root() / "lease-portfolio" / "fixtures" / name / "lease_state.json")
    return coerce_bundle_shape(payload)


def test_portfolio_walt_matches_fixture_expectation() -> None:
    bundle_a = _eval_fixture("golden_ol_a1")
    bundle_b = _portfolio_fixture("golden_office_harbortech")
    result = build_portfolio([bundle_a, bundle_b], reference_date=None)
    walt = result.manifest["walt"]["value_years"]
    assert walt is not None
    # Fixture docs indicate approx 7.186 years from these two leases.
    assert abs(walt - 7.186) < 0.02
