"""Scenario loading, validation, and route matching."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SUPPORTED_VERSION = 1
SUPPORTED_METHODS = {
    "DELETE",
    "GET",
    "HEAD",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
}


class ScenarioError(ValueError):
    """Raised when a scenario cannot be loaded or does not satisfy the contract."""


def _response_errors(response: Any, location: str) -> list[str]:
    if not isinstance(response, dict):
        return [f"{location} must be an object"]

    errors: list[str] = []
    status = response.get("status", 200)
    if not isinstance(status, int) or isinstance(status, bool) or not 100 <= status <= 599:
        errors.append(f"{location}.status must be an integer between 100 and 599")

    delay = response.get("delay_ms", 0)
    if (
        not isinstance(delay, (int, float))
        or isinstance(delay, bool)
        or delay < 0
    ):
        errors.append(f"{location}.delay_ms must be a non-negative number")

    headers = response.get("headers", {})
    if not isinstance(headers, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in headers.items()
    ):
        errors.append(f"{location}.headers must map strings to strings")

    return errors


def validate_scenario(data: Any) -> list[str]:
    """Return human-readable contract violations for a scenario."""

    if not isinstance(data, dict):
        return ["scenario root must be an object"]

    errors: list[str] = []

    version = data.get("version")
    if version != SUPPORTED_VERSION:
        errors.append(f"version must be {SUPPORTED_VERSION}")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("name must be a non-empty string")

    description = data.get("description")
    if description is not None and not isinstance(description, str):
        errors.append("description must be a string")

    for section_name in ("device", "storage", "time", "identity", "events", "expected"):
        section = data.get(section_name)
        if section is not None and not isinstance(section, dict):
            errors.append(f"{section_name} must be an object")

    network = data.get("network", {})
    if not isinstance(network, dict):
        errors.append("network must be an object")
        return errors

    default_response = network.get("default")
    if default_response is not None:
        errors.extend(_response_errors(default_response, "network.default"))

    routes = network.get("routes", [])
    if not isinstance(routes, list):
        errors.append("network.routes must be an array")
        return errors

    identities: set[tuple[str, str]] = set()
    for index, route in enumerate(routes):
        location = f"network.routes[{index}]"
        if not isinstance(route, dict):
            errors.append(f"{location} must be an object")
            continue

        method = route.get("method")
        if not isinstance(method, str) or method.upper() not in SUPPORTED_METHODS:
            allowed = ", ".join(sorted(SUPPORTED_METHODS))
            errors.append(f"{location}.method must be one of: {allowed}")
            normalized_method = ""
        else:
            normalized_method = method.upper()

        path = route.get("path")
        if not isinstance(path, str) or not path.startswith("/"):
            errors.append(f"{location}.path must be a string starting with '/'")
            normalized_path = ""
        else:
            normalized_path = path

        if normalized_method and normalized_path:
            identity = (normalized_method, normalized_path)
            if identity in identities:
                errors.append(
                    f"{location} duplicates route {normalized_method} {normalized_path}"
                )
            identities.add(identity)

        if "response" not in route:
            errors.append(f"{location}.response is required")
        else:
            errors.extend(_response_errors(route["response"], f"{location}.response"))

    return errors


def load_scenario(path: str | Path) -> dict[str, Any]:
    """Load and validate a JSON scenario from disk."""

    scenario_path = Path(path)
    try:
        raw = scenario_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ScenarioError(f"cannot read scenario '{scenario_path}': {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ScenarioError(
            f"invalid JSON in '{scenario_path}' at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    errors = validate_scenario(data)
    if errors:
        formatted = "\n".join(f"- {error}" for error in errors)
        raise ScenarioError(f"scenario '{scenario_path}' is invalid:\n{formatted}")

    return data


def scenario_digest(scenario: dict[str, Any]) -> str:
    """Return a stable digest of normalized scenario content."""

    payload = json.dumps(
        scenario,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def find_route(
    scenario: dict[str, Any], method: str, path: str
) -> dict[str, Any] | None:
    """Find an exact method/path route in a validated scenario."""

    normalized_method = method.upper()
    routes = scenario.get("network", {}).get("routes", [])
    for route in routes:
        if (
            route.get("method", "").upper() == normalized_method
            and route.get("path") == path
        ):
            return route
    return None


def response_for(
    scenario: dict[str, Any], method: str, path: str
) -> tuple[dict[str, Any], bool]:
    """Return a response and whether it came from a configured route/default."""

    route = find_route(scenario, method, path)
    if route is not None:
        return route["response"], True

    default_response = scenario.get("network", {}).get("default")
    if default_response is not None:
        return default_response, True

    return (
        {
            "status": 404,
            "body": {
                "error": "genjutsu_route_not_found",
                "method": method.upper(),
                "path": path,
            },
        },
        False,
    )
