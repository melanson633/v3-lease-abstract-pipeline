from __future__ import annotations

from leasegpt.pipeline.calendar import build_calendar
from leasegpt.utils.io import coerce_bundle_shape, load_json
from leasegpt.utils.paths import skills_root


def _fixture(name: str) -> dict:
    payload = load_json(skills_root() / "lease-eval" / "fixtures" / name / "lease_state.json")
    return coerce_bundle_shape(payload)


def test_calendar_derives_expected_renewal_deadline() -> None:
    bundle = _fixture("golden_ol_a1")
    result = build_calendar(bundle=bundle, lead_days=0, include_rent_steps=True)
    renewal = [
        e for e in result.manifest["events"] if e["event_type"] == "renewal_notice_deadline"
    ]
    assert renewal, "expected renewal_notice_deadline event"
    assert renewal[0]["date"] == "2031-09-04"
