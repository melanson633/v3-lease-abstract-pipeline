"""CLI entrypoint for the LeaseGPT runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from leasegpt.config import load_environment, resolve_provider_config
from leasegpt.errors import ConfigError, InputValidationError, LeaseGPTError, ProviderInvocationError
from leasegpt.pipeline.abstract import generate_abstract_markdown
from leasegpt.pipeline.calendar import build_calendar
from leasegpt.pipeline.diff import build_diff
from leasegpt.pipeline.evaluate import evaluate_bundle
from leasegpt.pipeline.export import generate_exports
from leasegpt.pipeline.extract import build_extraction_output, load_schema_text, run_extraction
from leasegpt.pipeline.portfolio import build_portfolio
from leasegpt.pipeline.render import render_markdown_to_pdf
from leasegpt.pipeline.risk import build_risk_register
from leasegpt.providers.factory import create_adapter
from leasegpt.utils.dates import parse_date
from leasegpt.utils.io import (
    coerce_bundle_shape,
    load_json,
    normalize_documents,
    write_json,
    write_text,
)
from leasegpt.utils.paths import schema_path

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="LeaseGPT CLI runtime for extraction, validation, and downstream lease artifacts.",
)


def _load_bundle(path: Path) -> dict[str, Any]:
    return coerce_bundle_shape(load_json(path))


def _handle_error(exc: Exception) -> None:
    typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1)


@app.command()
def extract(
    documents: list[Path] = typer.Argument(..., help="Input lease files for a single tenant."),
    output_json: Path = typer.Option(
        Path("out/extraction.json"),
        "--output-json",
        help="Path to write extraction JSON.",
    ),
    provider: str | None = typer.Option(None, "--provider", help="openai | anthropic | gemini"),
    model: str | None = typer.Option(None, "--model", help="Model override."),
    max_chars_per_doc: int = typer.Option(
        120_000, "--max-chars-per-doc", help="Prompt safety truncation ceiling per document."
    ),
    max_output_tokens: int = typer.Option(6_000, "--max-output-tokens", help="LLM max output tokens."),
) -> None:
    """Run lease-extract and emit extraction JSON."""
    try:
        load_environment()
        provider_cfg = resolve_provider_config(provider=provider, model=model, max_output_tokens=max_output_tokens)
        adapter = create_adapter(provider_cfg)
        docs = normalize_documents(documents, max_chars_per_doc=max_chars_per_doc)
        schema_text = load_schema_text(schema_path())
        bundle = run_extraction(adapter=adapter, schema_text=schema_text, documents=docs)
        write_json(output_json, build_extraction_output(bundle))
        typer.secho(
            f"Extraction complete ({provider_cfg.provider}:{provider_cfg.model}). Output: {output_json}",
            fg=typer.colors.GREEN,
        )
        if bundle.tenant_candidates:
            typer.echo(f"Tenant: {bundle.tenant_candidates[0]}")
    except (LeaseGPTError, ConfigError, InputValidationError, ProviderInvocationError) as exc:
        _handle_error(exc)


@app.command(name="eval")
def eval_cmd(
    candidate_json: Path = typer.Argument(..., help="Extraction JSON file to evaluate."),
    output_report: Path = typer.Option(Path("out/conformance_report.json"), "--output-report"),
    output_summary: Path = typer.Option(Path("out/conformance_summary.md"), "--output-summary"),
    scope: str = typer.Option("full", "--scope", help="schema_only | provenance_only | full"),
    golden_fixture: str | None = typer.Option(None, "--golden-fixture", help="Fixture name under lease-eval/fixtures."),
) -> None:
    """Run lease-eval checks."""
    try:
        bundle = _load_bundle(candidate_json)
        result = evaluate_bundle(bundle, scope=scope, golden_fixture_name=golden_fixture)
        write_json(output_report, result.conformance_report)
        write_text(output_summary, result.summary_markdown + "\n")
        verdict = result.conformance_report.get("verdict", "UNKNOWN")
        color = typer.colors.GREEN if verdict == "PASS" else typer.colors.YELLOW if verdict == "WARN" else typer.colors.RED
        typer.secho(f"Evaluation complete. Verdict={verdict}. Report: {output_report}", fg=color)
    except Exception as exc:
        _handle_error(exc)


@app.command()
def abstract(
    candidate_json: Path = typer.Argument(..., help="Extraction JSON file."),
    output_markdown: Path = typer.Option(Path("out/lease_abstract.md"), "--output-markdown"),
    property_type: str = typer.Option(..., "--property-type", help="Office | Retail | Industrial | Other"),
    audience: str = typer.Option(..., "--audience", help="Executive | AssetManagement | PropertyManagement | ..."),
    need_pm_block: bool = typer.Option(True, "--need-pm-block/--no-need-pm-block"),
    exec_only: bool = typer.Option(False, "--exec-only"),
) -> None:
    """Generate markdown lease abstract."""
    try:
        bundle = _load_bundle(candidate_json)
        markdown = generate_abstract_markdown(
            bundle=bundle,
            property_type=property_type,
            audience=audience,
            need_pm_block=need_pm_block,
            exec_only=exec_only,
        )
        write_text(output_markdown, markdown)
        typer.secho(f"Abstract written: {output_markdown}", fg=typer.colors.GREEN)
    except Exception as exc:
        _handle_error(exc)


@app.command()
def render(
    markdown_file: Path = typer.Argument(..., help="Markdown abstract file."),
    output_pdf: Path = typer.Option(Path("out/lease_abstract.pdf"), "--output-pdf"),
) -> None:
    """Render markdown abstract to PDF."""
    try:
        markdown = markdown_file.read_text(encoding="utf-8")
        summary = render_markdown_to_pdf(markdown, output_pdf)
        typer.secho(f"PDF rendered: {summary.output_path}", fg=typer.colors.GREEN)
        for warning in summary.warnings:
            typer.secho(f"Warning: {warning}", fg=typer.colors.YELLOW)
    except Exception as exc:
        _handle_error(exc)


@app.command()
def export(
    candidate_json: Path = typer.Argument(..., help="Extraction JSON file."),
    output_dir: Path = typer.Option(Path("out/exports"), "--output-dir"),
    output_type: str = typer.Option("xlsx", "--output-type", help="xlsx | csv | both"),
) -> None:
    """Export lease data to XLSX/CSV."""
    try:
        bundle = _load_bundle(candidate_json)
        summary = generate_exports(bundle=bundle, output_dir=output_dir, output_type=output_type)
        if summary.workbook_path:
            typer.secho(f"Workbook: {summary.workbook_path}", fg=typer.colors.GREEN)
        if summary.csv_paths:
            typer.echo(f"CSV files: {len(summary.csv_paths)}")
        typer.echo(
            "Rows per sheet: " + ", ".join(f"{sheet}={count}" for sheet, count in summary.sheet_row_counts.items())
        )
        for warning in summary.warnings:
            typer.secho(f"Warning: {warning}", fg=typer.colors.YELLOW)
    except Exception as exc:
        _handle_error(exc)


@app.command()
def calendar(
    candidate_json: Path = typer.Argument(..., help="Extraction JSON file."),
    output_ics: Path = typer.Option(Path("out/critical_dates.ics"), "--output-ics"),
    output_manifest: Path = typer.Option(Path("out/calendar_manifest.json"), "--output-manifest"),
    timezone_name: str = typer.Option("UTC", "--timezone"),
    lead_days: int = typer.Option(0, "--lead-days"),
    include_rent_steps: bool = typer.Option(True, "--include-rent-steps/--no-include-rent-steps"),
) -> None:
    """Generate critical-dates ICS and JSON manifest."""
    try:
        bundle = _load_bundle(candidate_json)
        result = build_calendar(
            bundle=bundle,
            timezone_name=timezone_name,
            lead_days=lead_days,
            include_rent_steps=include_rent_steps,
        )
        write_text(output_ics, result.calendar_ics)
        write_json(output_manifest, result.manifest)
        typer.secho(f"Calendar outputs: {output_ics}, {output_manifest}", fg=typer.colors.GREEN)
        typer.echo(result.summary_markdown)
    except Exception as exc:
        _handle_error(exc)


@app.command()
def diff(
    candidate_json: Path = typer.Argument(..., help="Extraction JSON file."),
    output_report: Path = typer.Option(Path("out/diff_report.md"), "--output-report"),
    output_manifest: Path = typer.Option(Path("out/diff_manifest.json"), "--output-manifest"),
    draft_amendment_json: Path | None = typer.Option(None, "--draft-amendment-json"),
) -> None:
    """Generate amendment-aware diff report."""
    try:
        bundle = _load_bundle(candidate_json)
        draft = load_json(draft_amendment_json) if draft_amendment_json else None
        result = build_diff(bundle=bundle, draft_amendment=draft)
        write_text(output_report, result.report_markdown)
        write_json(output_manifest, result.manifest)
        typer.secho(f"Diff outputs: {output_report}, {output_manifest}", fg=typer.colors.GREEN)
    except Exception as exc:
        _handle_error(exc)


@app.command()
def risk(
    candidate_json: Path = typer.Argument(..., help="Extraction JSON file."),
    output_report: Path = typer.Option(Path("out/risk_register.md"), "--output-report"),
    output_manifest: Path = typer.Option(Path("out/risk_manifest.json"), "--output-manifest"),
    calendar_manifest_json: Path | None = typer.Option(None, "--calendar-manifest-json"),
) -> None:
    """Generate rule-based risk register."""
    try:
        bundle = _load_bundle(candidate_json)
        calendar_manifest = load_json(calendar_manifest_json) if calendar_manifest_json else None
        result = build_risk_register(bundle=bundle, calendar_manifest=calendar_manifest)
        write_text(output_report, result.register_markdown)
        write_json(output_manifest, result.manifest)
        typer.secho(f"Risk outputs: {output_report}, {output_manifest}", fg=typer.colors.GREEN)
    except Exception as exc:
        _handle_error(exc)


@app.command()
def portfolio(
    candidate_json_files: list[Path] = typer.Argument(..., help="Two or more extraction JSON files."),
    output_summary: Path = typer.Option(Path("out/portfolio_summary.md"), "--output-summary"),
    output_manifest: Path = typer.Option(Path("out/portfolio_manifest.json"), "--output-manifest"),
    reference_date: str | None = typer.Option(None, "--reference-date", help="YYYY-MM-DD"),
) -> None:
    """Generate portfolio analytics from prior single-tenant outputs."""
    try:
        bundles = [_load_bundle(path) for path in candidate_json_files]
        ref = parse_date(reference_date) if reference_date else None
        result = build_portfolio(bundles=bundles, reference_date=ref)
        write_text(output_summary, result.summary_markdown)
        write_json(output_manifest, result.manifest)
        typer.secho(f"Portfolio outputs: {output_summary}, {output_manifest}", fg=typer.colors.GREEN)
    except Exception as exc:
        _handle_error(exc)


@app.command("run")
def run_pipeline(
    documents: list[Path] = typer.Argument(..., help="Input lease files for end-to-end run."),
    output_dir: Path = typer.Option(Path("out/run"), "--output-dir"),
    provider: str | None = typer.Option(None, "--provider", help="openai | anthropic | gemini"),
    model: str | None = typer.Option(None, "--model"),
    property_type: str = typer.Option("Other", "--property-type"),
    audience: str = typer.Option("AssetManagement", "--audience"),
    timezone_name: str = typer.Option("UTC", "--timezone"),
    lead_days: int = typer.Option(0, "--lead-days"),
    include_rent_steps: bool = typer.Option(True, "--include-rent-steps/--no-include-rent-steps"),
    export_type: str = typer.Option("xlsx", "--export-type", help="xlsx | csv | both"),
    max_chars_per_doc: int = typer.Option(120_000, "--max-chars-per-doc"),
    max_output_tokens: int = typer.Option(6_000, "--max-output-tokens"),
) -> None:
    """Run extraction -> eval -> abstract -> render -> export -> calendar -> diff -> risk."""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        load_environment()
        provider_cfg = resolve_provider_config(provider=provider, model=model, max_output_tokens=max_output_tokens)
        adapter = create_adapter(provider_cfg)

        docs = normalize_documents(documents, max_chars_per_doc=max_chars_per_doc)
        schema_text = load_schema_text(schema_path())
        bundle_obj = run_extraction(adapter=adapter, schema_text=schema_text, documents=docs)
        bundle = build_extraction_output(bundle_obj)

        extraction_path = output_dir / "extraction.json"
        write_json(extraction_path, bundle)

        eval_result = evaluate_bundle(bundle)
        write_json(output_dir / "conformance_report.json", eval_result.conformance_report)
        write_text(output_dir / "conformance_summary.md", eval_result.summary_markdown + "\n")

        abstract_md = generate_abstract_markdown(
            bundle=bundle,
            property_type=property_type,
            audience=audience,
            need_pm_block=True,
            exec_only=False,
        )
        abstract_path = output_dir / "lease_abstract.md"
        write_text(abstract_path, abstract_md)
        render_summary = render_markdown_to_pdf(abstract_md, output_dir / "lease_abstract.pdf")

        export_summary = generate_exports(bundle=bundle, output_dir=output_dir / "exports", output_type=export_type)

        calendar_result = build_calendar(
            bundle=bundle,
            timezone_name=timezone_name,
            lead_days=lead_days,
            include_rent_steps=include_rent_steps,
        )
        write_text(output_dir / "critical_dates.ics", calendar_result.calendar_ics)
        write_json(output_dir / "calendar_manifest.json", calendar_result.manifest)

        diff_result = build_diff(bundle=bundle)
        write_text(output_dir / "diff_report.md", diff_result.report_markdown)
        write_json(output_dir / "diff_manifest.json", diff_result.manifest)

        risk_result = build_risk_register(bundle=bundle, calendar_manifest=calendar_result.manifest)
        write_text(output_dir / "risk_register.md", risk_result.register_markdown)
        write_json(output_dir / "risk_manifest.json", risk_result.manifest)

        verdict = eval_result.conformance_report.get("verdict", "UNKNOWN")
        typer.secho(
            f"End-to-end run complete ({provider_cfg.provider}:{provider_cfg.model}) -> {output_dir}",
            fg=typer.colors.GREEN,
        )
        typer.echo(f"Conformance verdict: {verdict}")
        typer.echo(f"Render warnings: {len(render_summary.warnings)}")
        typer.echo(
            "Export sheets: " + ", ".join(f"{k}={v}" for k, v in export_summary.sheet_row_counts.items())
        )
    except Exception as exc:
        _handle_error(exc)


@app.command("run-from-json")
def run_from_json(
    candidate_json: Path = typer.Argument(..., help="Existing extraction JSON."),
    output_dir: Path = typer.Option(Path("out/run_from_json"), "--output-dir"),
    property_type: str = typer.Option("Other", "--property-type"),
    audience: str = typer.Option("AssetManagement", "--audience"),
    timezone_name: str = typer.Option("UTC", "--timezone"),
    lead_days: int = typer.Option(0, "--lead-days"),
    include_rent_steps: bool = typer.Option(True, "--include-rent-steps/--no-include-rent-steps"),
    export_type: str = typer.Option("xlsx", "--export-type"),
) -> None:
    """Offline verification path: run downstream pipeline from an existing extraction JSON."""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        bundle = _load_bundle(candidate_json)
        write_json(output_dir / "extraction.json", bundle)

        eval_result = evaluate_bundle(bundle)
        write_json(output_dir / "conformance_report.json", eval_result.conformance_report)
        write_text(output_dir / "conformance_summary.md", eval_result.summary_markdown + "\n")

        abstract_md = generate_abstract_markdown(
            bundle=bundle,
            property_type=property_type,
            audience=audience,
            need_pm_block=True,
            exec_only=False,
        )
        write_text(output_dir / "lease_abstract.md", abstract_md)
        render_markdown_to_pdf(abstract_md, output_dir / "lease_abstract.pdf")

        generate_exports(bundle=bundle, output_dir=output_dir / "exports", output_type=export_type)
        calendar_result = build_calendar(
            bundle=bundle,
            timezone_name=timezone_name,
            lead_days=lead_days,
            include_rent_steps=include_rent_steps,
        )
        write_text(output_dir / "critical_dates.ics", calendar_result.calendar_ics)
        write_json(output_dir / "calendar_manifest.json", calendar_result.manifest)

        diff_result = build_diff(bundle=bundle)
        write_text(output_dir / "diff_report.md", diff_result.report_markdown)
        write_json(output_dir / "diff_manifest.json", diff_result.manifest)

        risk_result = build_risk_register(bundle=bundle, calendar_manifest=calendar_result.manifest)
        write_text(output_dir / "risk_register.md", risk_result.register_markdown)
        write_json(output_dir / "risk_manifest.json", risk_result.manifest)

        typer.secho(f"Offline run complete -> {output_dir}", fg=typer.colors.GREEN)
    except Exception as exc:
        _handle_error(exc)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
