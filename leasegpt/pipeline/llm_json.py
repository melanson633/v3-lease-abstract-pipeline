"""Utilities for extracting JSON payloads from model text output."""

from __future__ import annotations

import json
import re
from typing import Any

from leasegpt.errors import InputValidationError

JSON_FENCE_RE = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def extract_json_text(raw: str) -> str:
    match = JSON_FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    raise InputValidationError("Model output did not contain a JSON object.")


def parse_json_from_text(raw: str) -> dict[str, Any]:
    json_text = extract_json_text(raw)
    try:
        value = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise InputValidationError(f"Failed to parse model JSON output: {exc}") from exc
    if not isinstance(value, dict):
        raise InputValidationError("Model output JSON must be an object at top-level.")
    return value
