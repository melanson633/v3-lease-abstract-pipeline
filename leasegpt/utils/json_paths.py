"""Helpers for dot/bracket JSON path traversal and flattening."""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

PATH_TOKEN_RE = re.compile(r"([^[.\]]+)|\[(\d+)\]")


def split_path(path: str) -> list[str | int]:
    parts: list[str | int] = []
    for match in PATH_TOKEN_RE.finditer(path):
        key = match.group(1)
        idx = match.group(2)
        if key is not None:
            parts.append(key)
        elif idx is not None:
            parts.append(int(idx))
    return parts


def normalize_array_path(path: str) -> str:
    return re.sub(r"\[\d+\]", "[]", path)


def _iter_object(
    value: Any, prefix: str = "", include_objects: bool = False
) -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict):
        if include_objects and prefix:
            yield prefix, value
        for key, sub in value.items():
            sub_prefix = f"{prefix}.{key}" if prefix else key
            yield from _iter_object(sub, sub_prefix, include_objects=include_objects)
        return

    if isinstance(value, list):
        if include_objects and prefix:
            yield prefix, value
        for idx, sub in enumerate(value):
            sub_prefix = f"{prefix}[{idx}]"
            yield from _iter_object(sub, sub_prefix, include_objects=include_objects)
        return

    yield prefix, value


def flatten_leaves(value: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for path, leaf in _iter_object(value):
        if path:
            result[path] = leaf
    return result


def flatten_paths(value: Any) -> set[str]:
    paths: set[str] = set()
    for path, _ in _iter_object(value, include_objects=True):
        if path:
            paths.add(path)
    return paths


def get_by_path(value: Any, path: str) -> Any:
    current = value
    for token in split_path(path):
        if isinstance(token, int):
            if not isinstance(current, list) or token >= len(current):
                raise KeyError(path)
            current = current[token]
            continue
        if not isinstance(current, dict) or token not in current:
            raise KeyError(path)
        current = current[token]
    return current


def try_get_by_path(value: Any, path: str) -> tuple[bool, Any]:
    try:
        return True, get_by_path(value, path)
    except KeyError:
        return False, None


def ancestor_paths(path: str) -> list[str]:
    parts = split_path(path)
    output: list[str] = []
    current = ""
    for part in parts:
        if isinstance(part, int):
            current = f"{current}[{part}]"
        else:
            current = f"{current}.{part}" if current else part
        output.append(current)
    output.reverse()
    return output


def is_populated_leaf(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def values_equal(left: Any, right: Any, numeric_epsilon: float = 1e-9) -> bool:
    if isinstance(left, str) and isinstance(right, str):
        return left.strip() == right.strip()
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right)) <= numeric_epsilon
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        if len(left) != len(right):
            return False
        return all(values_equal(lv, rv, numeric_epsilon) for lv, rv in zip(left, right))
    if isinstance(left, dict):
        if set(left.keys()) != set(right.keys()):
            return False
        return all(values_equal(left[k], right[k], numeric_epsilon) for k in left)
    return left == right
