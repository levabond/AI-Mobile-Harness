from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

from .adapters import discover_project
from .documents import load_document
from .schema import validate


def run_doctor(project_root: Path, distribution_root: Path) -> Dict[str, Any]:
    checks: List[Dict[str, str]] = []
    config: Dict[str, Any] = {}

    try:
        config = load_document(project_root / "harness.yaml")
        status = "passed" if config.get("version") == 1 else "failed"
        checks.append({"name": "configuration", "status": status, "details": "harness.yaml version 1" if status == "passed" else "Unsupported version"})
    except Exception as exc:  # Presented as a doctor result, not a traceback.
        checks.append({"name": "configuration", "status": "failed", "details": str(exc)})

    integration_failures = []
    for name in ("superpowers", "mobilebuildmcp"):
        path = distribution_root / f"integrations/{name}.yaml"
        try:
            integration = load_document(path)
            if integration.get("license") != "MIT" or not integration.get("source"):
                integration_failures.append(f"{name}: source/license metadata missing")
        except Exception as exc:
            integration_failures.append(f"{name}: {exc}")
    checks.append(
        {
            "name": "methodology_integrations",
            "status": "passed" if not integration_failures else "failed",
            "details": "; ".join(integration_failures) or "Superpowers and MobileBuildMCP contracts are declared",
        }
    )

    mobile_build = config.get("integrations", {}).get("mobile_build", {})
    command = mobile_build.get("command", [])
    executable = command[0] if isinstance(command, list) and command else "mobilebuildmcp"
    mobile_status = "passed" if not mobile_build.get("enabled", False) or shutil.which(executable) else "failed"
    checks.append(
        {
            "name": "mobile_build_backend",
            "status": mobile_status,
            "details": (
                f"configured via {executable}" if mobile_build.get("enabled", False) and mobile_status == "passed" else "disabled for hermetic fixture"
                if not mobile_build.get("enabled", False)
                else f"configured executable not found: {executable}"
            ),
        }
    )

    contract_failures = []
    for path in sorted((distribution_root / "contracts").glob("*.schema.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                contract_failures.append(f"{path.name}: missing draft 2020-12 marker")
        except (OSError, json.JSONDecodeError) as exc:
            contract_failures.append(f"{path.name}: {exc}")
    checks.append({"name": "contracts", "status": "passed" if not contract_failures else "failed", "details": "; ".join(contract_failures) or "all contract files parse"})

    try:
        adapter = load_document(distribution_root / "adapters/ios-xcode/adapter.yaml")
        schema = json.loads((distribution_root / "adapters/contract/adapter.schema.json").read_text(encoding="utf-8"))
        failures = validate(adapter, schema)
    except Exception as exc:
        failures = [str(exc)]
    checks.append({"name": "adapter_contract", "status": "passed" if not failures else "failed", "details": "; ".join(failures) or "ios-xcode descriptor is valid"})

    skill_failures = []
    for skill_path in sorted((distribution_root / "skills").glob("*/SKILL.md")):
        text = skill_path.read_text(encoding="utf-8")
        if "TODO" in text or not text.startswith("---\n"):
            skill_failures.append(skill_path.parent.name)
    checks.append({"name": "skills", "status": "passed" if not skill_failures else "failed", "details": ", ".join(skill_failures) or "all P0 skills are populated"})

    try:
        profile, _ = discover_project(project_root, config)
        project_details = f"detected {profile['project']['kind']} with {profile['adapter']}"
        project_status = "passed"
    except Exception as exc:
        project_details = f"not a mobile target: {exc}"
        project_status = "warning"
    checks.append({"name": "project_detection", "status": project_status, "details": project_details})
    status = "passed" if all(item["status"] != "failed" for item in checks) else "failed"
    return {"status": status, "checks": checks}
