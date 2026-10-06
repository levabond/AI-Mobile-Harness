from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from .doctor import run_doctor
from .documents import load_document
from .errors import ConfigurationError, GateError, HarnessError
from .eval import run_profile_details_eval
from .orchestrator import Orchestrator, STAGE_ORDER, create_default_config


EXIT_OK = 0
EXIT_FAILED_GATE = 3
EXIT_CONFIGURATION = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mobile-harness", description="Evidence-driven mobile engineering workflow")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="mobile project root (default: current directory)")
    parser.add_argument("--json", action="store_true", dest="json_output", help="emit machine-readable JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="attach the harness to a project")
    init_parser.add_argument("--name")
    init_parser.add_argument("--platform", choices=("auto", "ios"), default="auto")
    init_parser.add_argument("--profile", choices=("prototype", "standard", "strict"), default="standard")

    discover_parser = subparsers.add_parser("discover", help="discover project context")
    discover_parser.add_argument("target", choices=("project",))

    start_parser = subparsers.add_parser("start", help="create a work item")
    start_parser.add_argument("type", choices=("feature", "bugfix", "hotfix"))
    start_parser.add_argument("title")
    start_parser.add_argument("--id")
    start_parser.add_argument("--profile", choices=("prototype", "standard", "strict", "hotfix"))
    start_parser.add_argument("--risk-level", choices=("low", "medium", "high", "critical"), default="medium")
    start_parser.add_argument("--risk-factor", action="append", default=[])
    start_parser.add_argument("--spec", type=Path, help="JSON-compatible YAML request document")

    run_parser = subparsers.add_parser("run", help="run a stage or the active workflow")
    run_parser.add_argument("target", choices=tuple(STAGE_ORDER) + ("feature", "bugfix", "hotfix"))
    run_parser.add_argument("--work-item")
    run_parser.add_argument("--profile", choices=("prototype", "standard", "strict", "hotfix"))

    status_parser = subparsers.add_parser("status", help="show active work item status")
    status_parser.add_argument("--work-item")

    report_parser = subparsers.add_parser("report", help="evaluate the final gate and write the report")
    report_parser.add_argument("--work-item")

    subparsers.add_parser("doctor", help="validate configuration and contracts")

    eval_parser = subparsers.add_parser("eval", help="run a deterministic harness evaluation")
    eval_parser.add_argument("name", choices=("profile-details",))
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project_root = args.project.resolve()
    distribution_root = Path(__file__).resolve().parent.parent
    try:
        if args.command == "init":
            result: Dict[str, Any] = {"status": "passed", "configuration": str(create_default_config(project_root, args.name, args.platform, args.profile))}
        elif args.command == "doctor":
            result = run_doctor(project_root, distribution_root)
        elif args.command == "eval":
            result = run_profile_details_eval(distribution_root)
        else:
            orchestrator = Orchestrator(project_root)
            if args.command == "discover":
                result = orchestrator.discover()
            elif args.command == "start":
                request = load_document(args.spec.resolve()) if args.spec else None
                result = orchestrator.start(
                    args.type,
                    args.title,
                    profile=args.profile,
                    risk_level=args.risk_level,
                    risk_factors=args.risk_factor,
                    requested_id=args.id,
                    request=request,
                )
            elif args.command == "run":
                if args.target in {"feature", "bugfix", "hotfix"}:
                    manifest = orchestrator.store.load_manifest(args.work_item)
                    if manifest["type"] != args.target:
                        raise ConfigurationError(f"Active work item type is {manifest['type']!r}, not {args.target!r}")
                    result = orchestrator.run_workflow(args.work_item, args.profile)
                else:
                    result = orchestrator.run_stage(args.target, args.work_item)
            elif args.command == "status":
                result = orchestrator.status(args.work_item)
            elif args.command == "report":
                result = orchestrator.run_stage("final", args.work_item)
            else:
                parser.error("unsupported command")
                return EXIT_CONFIGURATION
    except (ConfigurationError, GateError, HarnessError) as exc:
        result = {"status": "error", "error": str(exc)}
        _print_result(result, args.json_output)
        return EXIT_CONFIGURATION if isinstance(exc, ConfigurationError) else EXIT_FAILED_GATE
    except KeyboardInterrupt:
        result = {"status": "cancelled", "error": "Interrupted by user."}
        _print_result(result, args.json_output)
        return 130

    _print_result(result, args.json_output)
    return EXIT_OK if result.get("status") in {"passed", "ready", "ready_with_accepted_risk"} or "id" in result else EXIT_FAILED_GATE


def _print_result(result: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return
    status = result.get("status") or result.get("decision") or result.get("state") or "ok"
    print(f"mobile-harness: {status}")
    if "id" in result:
        print(f"work item: {result['id']}")
    if result.get("work_item_id"):
        print(f"work item: {result['work_item_id']}")
    if result.get("decision"):
        print(f"decision: {result['decision']}")
    if result.get("report"):
        print(f"report: {result['report']}")
    if result.get("error"):
        print(result["error"], file=sys.stderr)
    if result.get("message"):
        print(result["message"])
    if "checks" in result and isinstance(result["checks"], list):
        for check in result["checks"]:
            print(f"- {check['name']}: {check['status']} — {check['details']}")


if __name__ == "__main__":
    raise SystemExit(main())

