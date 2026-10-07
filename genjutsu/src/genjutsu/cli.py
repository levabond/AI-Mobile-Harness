"""Command-line interface for Genjutsu."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .scenario import ScenarioError, load_scenario
from .server import serve
from .state import (
    cast_scenario,
    load_active_state,
    release_active_state,
    resolve_state_file,
)


DEFAULT_REQUEST_LOG = Path(".genjutsu/requests.jsonl")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="genjutsu",
        description="Create controlled realities for mobile development and testing.",
    )
    parser.add_argument(
        "--state-file",
        help="Active-state path (default: .genjutsu/active.json or GENJUTSU_STATE_FILE)",
    )
    parser.add_argument("--version", action="version", version="genjutsu 0.1.0")

    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate", help="Validate a scenario contract"
    )
    validate_parser.add_argument("scenario")

    cast_parser = subparsers.add_parser(
        "cast", help="Activate a controlled reality"
    )
    cast_parser.add_argument("scenario")

    inspect_parser = subparsers.add_parser(
        "inspect", help="Inspect the active reality"
    )
    inspect_parser.add_argument(
        "--json", action="store_true", help="Print the complete active state as JSON"
    )

    subparsers.add_parser("release", help="Return to the real environment")

    serve_parser = subparsers.add_parser(
        "serve", help="Serve the active HTTP simulation"
    )
    _add_server_arguments(serve_parser)

    run_parser = subparsers.add_parser(
        "run", help="Cast a scenario and serve it immediately"
    )
    run_parser.add_argument("scenario")
    _add_server_arguments(run_parser)

    return parser


def _add_server_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument(
        "--request-log",
        default=str(DEFAULT_REQUEST_LOG),
        help="JSONL request-evidence path",
    )


def _inspect_text(state: dict) -> str:
    scenario = state["scenario"]
    routes = scenario.get("network", {}).get("routes", [])
    lines = [
        f"Active reality: {scenario['name']}",
        f"Description: {scenario.get('description', '-') or '-'}",
        f"Cast ID: {state.get('cast_id', '-')}",
        f"Cast at: {state.get('cast_at', '-')}",
        f"Source: {state.get('source', '-')}",
        f"HTTP routes: {len(routes)}",
    ]
    for route in routes:
        status = route.get("response", {}).get("status", 200)
        lines.append(f"  {route['method'].upper():7} {route['path']} -> {status}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    state_file = resolve_state_file(args.state_file)

    try:
        if args.command == "validate":
            scenario = load_scenario(args.scenario)
            route_count = len(scenario.get("network", {}).get("routes", []))
            print(f"Valid scenario: {scenario['name']} ({route_count} HTTP routes)")
            return 0

        if args.command == "cast":
            scenario = load_scenario(args.scenario)
            state = cast_scenario(scenario, args.scenario, state_file)
            print(
                f"Casting '{scenario['name']}'\n"
                f"State: {state_file}\n"
                f"Cast ID: {state['cast_id']}"
            )
            return 0

        if args.command == "inspect":
            state = load_active_state(state_file)
            if args.json:
                print(json.dumps(state, indent=2, ensure_ascii=False))
            else:
                print(_inspect_text(state))
            return 0

        if args.command == "release":
            if release_active_state(state_file):
                print(f"Released active reality at '{state_file}'.")
            else:
                print(f"No active reality at '{state_file}'.")
            return 0

        if args.command == "serve":
            state = load_active_state(state_file)
            serve(state, args.host, args.port, args.request_log)
            return 0

        if args.command == "run":
            scenario = load_scenario(args.scenario)
            state = cast_scenario(scenario, args.scenario, state_file)
            serve(state, args.host, args.port, args.request_log)
            return 0

        parser.error(f"unknown command: {args.command}")
    except ScenarioError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    return 0
