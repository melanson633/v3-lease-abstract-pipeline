"""Schema loading and path-resolution helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from leasegpt.errors import InputValidationError
from leasegpt.utils.json_paths import normalize_array_path
from leasegpt.utils.paths import schema_path


def load_schema(schema_file: Path | None = None) -> dict[str, Any]:
    path = schema_file or schema_path()
    if not path.exists():
        raise InputValidationError(f"Schema file not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InputValidationError(f"Invalid JSON schema at {path}: {exc}") from exc


def validate_lease_state(
    lease_state: dict[str, Any], schema: dict[str, Any]
) -> list[dict[str, Any]]:
    validator = jsonschema.Draft7Validator(schema)
    violations: list[dict[str, Any]] = []
    for error in sorted(validator.iter_errors(lease_state), key=lambda e: e.path):
        if error.validator == "required":
            code = "missing_required"
            expected = list(error.validator_value)
            actual = None
        elif error.validator == "type":
            code = "type_mismatch"
            expected = error.validator_value
            actual = type(error.instance).__name__
        elif error.validator == "enum":
            code = "enum_violation"
            expected = error.validator_value
            actual = error.instance
        elif error.validator == "format":
            code = "format_violation"
            expected = error.validator_value
            actual = error.instance
        elif error.validator == "additionalProperties":
            code = "additional_property"
            expected = "no additional properties"
            actual = error.message
        else:
            code = error.validator or "schema_error"
            expected = error.validator_value
            actual = error.instance

        path = ".".join(str(part) for part in error.path)
        violations.append(
            {
                "path": path or "(root)",
                "error": code,
                "expected": expected,
                "actual": actual,
                "message": error.message,
            }
        )
    return violations


def schema_paths(schema: dict[str, Any]) -> set[str]:
    paths: set[str] = set()

    def walk(node: dict[str, Any], prefix: str) -> None:
        node_type = node.get("type")
        node_types: set[str] = set()
        if isinstance(node_type, str):
            node_types.add(node_type)
        elif isinstance(node_type, list):
            node_types.update(t for t in node_type if isinstance(t, str))

        if "object" in node_types or "properties" in node:
            for key, sub in node.get("properties", {}).items():
                next_prefix = f"{prefix}.{key}" if prefix else key
                paths.add(next_prefix)
                if isinstance(sub, dict):
                    walk(sub, next_prefix)
            return

        if "array" in node_types or "items" in node:
            item_schema = node.get("items")
            array_prefix = f"{prefix}[]"
            paths.add(array_prefix)
            if isinstance(item_schema, dict):
                walk(item_schema, array_prefix)

    root_props = schema.get("properties", {})
    for key, sub in root_props.items():
        paths.add(key)
        if isinstance(sub, dict):
            walk(sub, key)
    return paths


def path_resolves_in_schema(path: str, allowed_paths: set[str]) -> bool:
    normalized = normalize_array_path(path)
    return normalized in allowed_paths
