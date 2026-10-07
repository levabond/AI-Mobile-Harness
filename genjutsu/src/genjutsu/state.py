"""Lifecycle of the active Genjutsu reality."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .scenario import ScenarioError, scenario_digest, validate_scenario


DEFAULT_STATE_FILE = Path(".genjutsu/active.json")


def resolve_state_file(explicit: str | Path | None = None) -> Path:
    """Resolve CLI, environment, and default state-file configuration."""

    if explicit is not None:
        return Path(explicit)
    configured = os.environ.get("GENJUTSU_STATE_FILE")
    return Path(configured) if configured else DEFAULT_STATE_FILE


def cast_scenario(
    scenario: dict[str, Any], source: str | Path, state_file: str | Path
) -> dict[str, Any]:
    """Atomically activate a validated scenario."""

    errors = validate_scenario(scenario)
    if errors:
        formatted = "\n".join(f"- {error}" for error in errors)
        raise ScenarioError(f"cannot cast invalid scenario:\n{formatted}")

    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    state: dict[str, Any] = {
        "state_version": 1,
        "cast_id": str(uuid.uuid4()),
        "cast_at": datetime.now(timezone.utc).isoformat(),
        "source": str(Path(source).resolve()),
        "scenario_sha256": scenario_digest(scenario),
        "scenario": scenario,
    }

    temporary = state_path.with_name(f".{state_path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(
            json.dumps(state, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(state_path)
    finally:
        temporary.unlink(missing_ok=True)

    return state


def load_active_state(state_file: str | Path) -> dict[str, Any]:
    """Load the active reality or raise a user-facing error."""

    state_path = Path(state_file)
    if not state_path.exists():
        raise ScenarioError(
            f"no active reality at '{state_path}'; cast a scenario first"
        )

    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScenarioError(f"cannot read active reality '{state_path}': {exc}") from exc

    if not isinstance(data, dict) or not isinstance(data.get("scenario"), dict):
        raise ScenarioError(f"active reality '{state_path}' is malformed")

    errors = validate_scenario(data["scenario"])
    if errors:
        formatted = "\n".join(f"- {error}" for error in errors)
        raise ScenarioError(f"active reality contains an invalid scenario:\n{formatted}")

    actual_digest = scenario_digest(data["scenario"])
    if data.get("scenario_sha256") != actual_digest:
        raise ScenarioError(
            f"active reality '{state_path}' failed its integrity check"
        )

    return data


def release_active_state(state_file: str | Path) -> bool:
    """Release the active reality. Return whether a state existed."""

    state_path = Path(state_file)
    if not state_path.exists():
        return False
    state_path.unlink()
    return True
