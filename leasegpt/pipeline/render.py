"""Implementation of the lease-render skill using ReportLab."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


@dataclass(slots=True)
class RenderSummary:
    output_path: Path
    warnings: list[str]


def _build_styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "LeaseH1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "LeaseH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=colors.white,
            backColor=colors.HexColor("#00304d"),
            leading=18,
            leftIndent=4,
            rightIndent=4,
            spaceBefore=12,
            spaceAfter=8,
        ),
        "h3": ParagraphStyle(
            "LeaseH3",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=colors.HexColor("#00304d"),
            leading=15,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "LeaseBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=13,
            spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "LeaseBullet",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=13,
            leftIndent=14,
            bulletIndent=6,
            spaceAfter=3,
        ),
    }


def _parse_table(lines: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        parts = [cell.strip() for cell in stripped.strip("|").split("|")]
        if parts and all(part.replace("-", "").strip() == "" for part in parts):
            continue
        rows.append(parts)
    return rows


def _numeric_columns(header: list[str]) -> set[int]:
    numeric_tokens = ("annual", "monthly", "$", "amount", "percent", "psf", "rate", "rsf")
    out = set()
    for idx, name in enumerate(header):
        lower = name.lower()
        if any(token in lower for token in numeric_tokens):
            out.add(idx)
    return out


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _footer(canvas: Any, doc: SimpleDocTemplate) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawString(doc.leftMargin, 0.45 * inch, "LeaseGPT Abstract")
    canvas.drawRightString(
        doc.pagesize[0] - doc.rightMargin,
        0.45 * inch,
        f"Page {canvas.getPageNumber()}",
    )
    canvas.restoreState()


def render_markdown_to_pdf(markdown_text: str, output_path: Path) -> RenderSummary:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = _build_styles()
    warnings: list[str] = []
    elements: list[Any] = []

    lines = markdown_text.splitlines()
    idx = 0
    while idx < len(lines):
        line = lines[idx].rstrip()
        stripped = line.strip()
        if not stripped:
            idx += 1
            continue
        if stripped == "\\f" or stripped == "\f":
            elements.append(PageBreak())
            idx += 1
            continue
        if stripped.startswith("# "):
            elements.append(Paragraph(_escape_html(stripped[2:].strip()), styles["h1"]))
            idx += 1
            continue
        if stripped.startswith("## "):
            elements.append(Paragraph(_escape_html(stripped[3:].strip()), styles["h2"]))
            idx += 1
            continue
        if stripped.startswith("### "):
            elements.append(Paragraph(_escape_html(stripped[4:].strip()), styles["h3"]))
            idx += 1
            continue
        if stripped.startswith("|"):
            table_lines = []
            while idx < len(lines) and lines[idx].strip().startswith("|"):
                table_lines.append(lines[idx])
                idx += 1
            table_data = _parse_table(table_lines)
            if not table_data:
                continue
            col_count = max(len(row) for row in table_data)
            if col_count > 7:
                warnings.append("A table exceeded 7 columns and was still rendered as-is.")
            normalized = []
            for row in table_data:
                padded = row + [""] * (col_count - len(row))
                normalized.append([Paragraph(_escape_html(cell), styles["body"]) for cell in padded])

            available_width = letter[0] - (0.75 + 0.75) * inch
            col_width = available_width / col_count
            col_widths = [col_width] * col_count
            table = Table(normalized, colWidths=col_widths, repeatRows=1)
            num_cols = _numeric_columns(table_data[0] if table_data else [])
            table_style = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00304d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d1d5db")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
            for col in num_cols:
                table_style.append(("ALIGN", (col, 1), (col, -1), "RIGHT"))
            table.setStyle(TableStyle(table_style))
            elements.append(table)
            elements.append(Spacer(1, 8))
            continue
        if stripped.startswith("- "):
            elements.append(
                Paragraph(
                    _escape_html(stripped[2:].strip()),
                    styles["bullet"],
                    bulletText="•",
                )
            )
            idx += 1
            continue

        # Paragraph block
        para_lines = [stripped]
        idx += 1
        while idx < len(lines):
            next_line = lines[idx].strip()
            if not next_line or next_line.startswith(("#", "|", "- ")) or next_line in {"\\f", "\f"}:
                break
            para_lines.append(next_line)
            idx += 1
        elements.append(Paragraph(_escape_html(" ".join(para_lines)), styles["body"]))

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )
    doc.build(elements, onFirstPage=_footer, onLaterPages=_footer)
    return RenderSummary(output_path=output_path, warnings=warnings)
