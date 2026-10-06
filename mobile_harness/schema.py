from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence, Union

from .errors import ConfigurationError


JsonPath = List[Union[str, int]]


def validate(instance: Any, schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    _validate_node(instance, schema, [], errors)
    return errors


def validate_or_raise(instance: Any, schema_path: Path, label: str = "artifact") -> None:
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"Cannot load schema {schema_path}: {exc}") from exc
    errors = validate(instance, schema)
    if errors:
        joined = "; ".join(errors[:10])
        raise ConfigurationError(f"Invalid {label} against {schema_path.name}: {joined}")


def _location(path: JsonPath) -> str:
    if not path:
        return "$"
    result = "$"
    for part in path:
        result += f"[{part}]" if isinstance(part, int) else f".{part}"
    return result


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def _validate_node(value: Any, schema: Dict[str, Any], path: JsonPath, errors: List[str]) -> None:
    expected = schema.get("type")
    if expected:
        choices: Sequence[str] = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(value, choice) for choice in choices):
            errors.append(f"{_location(path)} expected {expected}, got {type(value).__name__}")
            return

    if "const" in schema and value != schema["const"]:
        errors.append(f"{_location(path)} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{_location(path)} must be one of {schema['enum']!r}")

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{_location(path)} missing required property {key!r}")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, child in value.items():
            if key in properties:
                _validate_node(child, properties[key], path + [key], errors)
            elif additional is False:
                errors.append(f"{_location(path + [key])} is not allowed")
            elif isinstance(additional, dict):
                _validate_node(child, additional, path + [key], errors)

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{_location(path)} must contain at least {schema['minItems']} items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, child in enumerate(value):
                _validate_node(child, item_schema, path + [index], errors)

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{_location(path)} is shorter than {schema['minLength']} characters")
        pattern = schema.get("pattern")
        if pattern and not re.search(pattern, value):
            errors.append(f"{_location(path)} does not match {pattern!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{_location(path)} must be >= {schema['minimum']}")

