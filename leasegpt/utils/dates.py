"""Date helpers."""

from __future__ import annotations

from datetime import UTC, date, datetime


def parse_date(value: str | None) -> date | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def parse_datetime_to_date(value: str | None) -> date | None:
    if not value or not isinstance(value, str):
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value).date()
    except ValueError:
        parsed_date = parse_date(value)
        return parsed_date


def today_utc() -> date:
    return datetime.now(UTC).date()


def fmt_mmddyyyy(value: str | None) -> str:
    parsed = parse_date(value)
    if not parsed:
        return value or ""
    return parsed.strftime("%m-%d-%Y")
