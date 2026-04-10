"""Implementation of the lease-export skill (XLSX/CSV)."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openpyxl import Workbook

from leasegpt.utils.json_paths import ancestor_paths


@dataclass(slots=True)
class ExportSummary:
    workbook_path: Path | None
    csv_paths: list[Path]
    sheet_row_counts: dict[str, int]
    warnings: list[str]


def _trace_map(bundle: dict[str, Any]) -> dict[str, Any]:
    traceability = bundle.get("traceability") or {}
    metadata = traceability.get("extractedFieldsMetadata") or {}
    return metadata if isinstance(metadata, dict) else {}


def _trace_for(path: str, trace_map: dict[str, Any]) -> dict[str, Any]:
    for candidate in ancestor_paths(path):
        info = trace_map.get(candidate)
        if isinstance(info, dict):
            return info
    return {}


def _append_sheet(ws: Any, header: list[str], rows: list[list[Any]]) -> int:
    ws.append(header)
    for row in rows:
        ws.append([_excel_safe(cell) for cell in row])
    return len(rows)


def _write_csv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows([[_excel_safe(cell) for cell in row] for row in rows])


def _excel_safe(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True)
    return value


def generate_exports(
    bundle: dict[str, Any],
    output_dir: Path,
    output_type: str = "xlsx",
) -> ExportSummary:
    lease_state = bundle.get("lease_state") or {}
    change_log = bundle.get("change_log") or []
    trace_map = _trace_map(bundle)
    output_dir.mkdir(parents=True, exist_ok=True)

    do_xlsx = output_type in {"xlsx", "both"}
    do_csv = output_type in {"csv", "both"}
    warnings: list[str] = []
    csv_paths: list[Path] = []
    sheet_counts: dict[str, int] = {}

    workbook = Workbook() if do_xlsx else None
    if workbook:
        default_sheet = workbook.active
        workbook.remove(default_sheet)

    def add_sheet(name: str, header: list[str], rows: list[list[Any]]) -> None:
        sheet_counts[name] = len(rows)
        if workbook:
            ws = workbook.create_sheet(name)
            _append_sheet(ws, header, rows)
        if do_csv:
            csv_path = output_dir / f"{name}.csv"
            _write_csv(csv_path, header, rows)
            csv_paths.append(csv_path)

    parties = lease_state.get("Parties") or {}
    dates = lease_state.get("Dates") or {}
    premises = lease_state.get("Premises") or {}
    financials = lease_state.get("Financials") or {}
    base_rent = financials.get("BaseRent") or {}
    addl = financials.get("AdditionalRent") or {}
    security = financials.get("SecurityDeposit") or {}
    options = lease_state.get("Options") or {}
    maintenance = ((lease_state.get("Clauses") or {}).get("Maintenance")) or {}

    summary_header = [
        "tenant_name",
        "landlord_name",
        "premises_address",
        "rsf",
        "commencement_date",
        "expiration_date",
        "recovery_type",
        "security_deposit",
        "renewal_options",
        "citation",
        "confidence",
        "validation_status",
    ]
    summary_trace = _trace_for("Parties.Tenant.Name", trace_map)
    summary_rows = [
        [
            ((parties.get("Tenant") or {}).get("Name")),
            ((parties.get("Landlord") or {}).get("Name")),
            premises.get("Address"),
            premises.get("RSF"),
            dates.get("CommencementDate"),
            dates.get("ExpirationDate"),
            addl.get("RecoveryType"),
            security.get("Amount"),
            ((options.get("RenewalOptions") or {}).get("NumberOfOptions")),
            summary_trace.get("citation"),
            summary_trace.get("confidence"),
            summary_trace.get("validation_status"),
        ]
    ]
    add_sheet("Summary", summary_header, summary_rows)

    key_dates_header = ["date_type", "date_value", "citation", "confidence", "notes"]
    key_dates_rows = []
    for field in (
        "LeaseExecutionDate",
        "OriginalLeaseDate",
        "CommencementDate",
        "RentCommencementDate",
        "ExpirationDate",
    ):
        path = f"Dates.{field}"
        info = _trace_for(path, trace_map)
        key_dates_rows.append(
            [field, dates.get(field), info.get("citation"), info.get("confidence"), info.get("notes")]
        )
    add_sheet("Key_Dates", key_dates_header, key_dates_rows)

    rent_header = [
        "period_label",
        "start_date",
        "end_date",
        "annual_rent",
        "monthly_rent",
        "psf_annual",
        "citation",
        "confidence",
        "effective_date",
    ]
    rent_rows = []
    for row in base_rent.get("Schedule") or []:
        if not isinstance(row, dict):
            continue
        info = _trace_for("Financials.BaseRent.Schedule", trace_map)
        rent_rows.append(
            [
                row.get("period"),
                row.get("startDate"),
                row.get("endDate"),
                row.get("annualAmount"),
                row.get("monthlyAmount"),
                row.get("baseRentPSF"),
                info.get("citation"),
                info.get("confidence"),
                row.get("startDate"),
            ]
        )
    add_sheet("Rent_Schedule", rent_header, rent_rows)

    additional_header = [
        "category",
        "structure",
        "definition",
        "base_year",
        "cap",
        "citation",
        "confidence",
    ]
    additional_rows = []
    exp_struct = addl.get("ExpenseStructure") or {}
    for category in ("OperatingExpenses", "Taxes", "Insurance", "Utilities"):
        path = f"Financials.AdditionalRent.ExpenseStructure.{category}"
        info = _trace_for(path, trace_map)
        additional_rows.append(
            [
                category,
                addl.get("RecoveryType"),
                exp_struct.get(category) if isinstance(exp_struct, dict) else None,
                ((addl.get("BaseYears") or {}).get(category)),
                ((addl.get("CAMCap") or {}).get("Percent")),
                info.get("citation"),
                info.get("confidence"),
            ]
        )
    add_sheet("Additional_Rent", additional_header, additional_rows)

    options_header = [
        "option_type",
        "term",
        "notice_period_days",
        "notice_start_date",
        "notice_end_date",
        "rent_adjustment_method",
        "conditions",
        "citation",
        "confidence",
    ]
    renewal = options.get("RenewalOptions") or {}
    options_rows = [
        [
            "Renewal",
            renewal.get("TermMonthsPerOption"),
            renewal.get("NoticePeriodDays"),
            None,
            None,
            renewal.get("RentAdjustmentMethod"),
            renewal.get("OtherTerms"),
            _trace_for("Options.RenewalOptions", trace_map).get("citation"),
            _trace_for("Options.RenewalOptions", trace_map).get("confidence"),
        ]
    ]
    termination = options.get("TerminationOptions")
    if isinstance(termination, dict):
        options_rows.append(
            [
                "Termination",
                None,
                termination.get("NoticePeriodDays"),
                None,
                termination.get("TerminationDate"),
                None,
                termination.get("TerminationFee"),
                _trace_for("Options.TerminationOptions", trace_map).get("citation"),
                _trace_for("Options.TerminationOptions", trace_map).get("confidence"),
            ]
        )
    add_sheet("Options", options_header, options_rows)

    maint_header = ["responsibility_area", "landlord_responsibility", "tenant_responsibility", "citation", "confidence"]
    maint_rows = [
        [
            "Maintenance",
            maintenance.get("LandlordResponsibilities") if isinstance(maintenance, dict) else None,
            maintenance.get("TenantResponsibilities") if isinstance(maintenance, dict) else None,
            _trace_for("Clauses.Maintenance", trace_map).get("citation"),
            _trace_for("Clauses.Maintenance", trace_map).get("confidence"),
        ]
    ]
    add_sheet("Maintenance_Matrix", maint_header, maint_rows)

    flags_header = ["flag", "description", "citation", "confidence"]
    flags_rows = []
    for path, meta in trace_map.items():
        if not isinstance(meta, dict):
            continue
        status = meta.get("validation_status")
        conf = meta.get("confidence")
        if status in {"flagged", "uncertain"} or (isinstance(conf, (int, float)) and conf < 0.7):
            flags_rows.append(
                [
                    status or "low_confidence",
                    path,
                    meta.get("citation"),
                    conf,
                ]
            )
    add_sheet("Compliance_Flags", flags_header, flags_rows)

    change_header = [
        "field_path",
        "old_value",
        "new_value",
        "effective_date",
        "source_document",
        "citation",
        "impact_notes",
    ]
    change_rows = []
    if isinstance(change_log, list):
        for entry in change_log:
            if not isinstance(entry, dict):
                continue
            change_rows.append(
                [
                    entry.get("field_path"),
                    entry.get("old_value"),
                    entry.get("new_value"),
                    entry.get("effective_date"),
                    entry.get("source_document"),
                    entry.get("citation"),
                    entry.get("impact_notes"),
                ]
            )
    add_sheet("Change_Log", change_header, change_rows)

    workbook_path: Path | None = None
    if workbook:
        workbook_path = output_dir / "lease_export.xlsx"
        workbook.save(workbook_path)

    if not change_rows:
        warnings.append("No change_log entries were available for Change_Log export.")

    return ExportSummary(
        workbook_path=workbook_path,
        csv_paths=csv_paths,
        sheet_row_counts=sheet_counts,
        warnings=warnings,
    )
