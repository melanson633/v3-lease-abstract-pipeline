from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from leasegpt.cli import app
from leasegpt.utils.paths import skills_root


def test_run_from_json_generates_end_to_end_outputs(tmp_path: Path) -> None:
    fixture = skills_root() / "lease-eval" / "fixtures" / "golden_ol_a1" / "lease_state.json"
    out_dir = tmp_path / "offline_run"
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "run-from-json",
            str(fixture),
            "--output-dir",
            str(out_dir),
            "--property-type",
            "Retail",
            "--audience",
            "AssetManagement",
        ],
    )
    assert result.exit_code == 0, result.output
    expected_files = [
        out_dir / "extraction.json",
        out_dir / "conformance_report.json",
        out_dir / "lease_abstract.md",
        out_dir / "lease_abstract.pdf",
        out_dir / "critical_dates.ics",
        out_dir / "calendar_manifest.json",
        out_dir / "diff_report.md",
        out_dir / "diff_manifest.json",
        out_dir / "risk_register.md",
        out_dir / "risk_manifest.json",
    ]
    for path in expected_files:
        assert path.exists(), f"missing expected output: {path}"
