from __future__ import annotations

import fnmatch
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .adapters import discover_project, write_project_context
from .command import CommandRunner
from .documents import load_document, timestamp_id, utc_now, write_document, write_text
from .errors import ConfigurationError, GateError
from .schema import validate_or_raise
from .store import ArtifactStore


STAGE_ORDER = ("discovery", "rnd", "plan", "dev", "verify", "review", "qa", "final")
CHECK_TO_OPERATION = {
    "build": "build_app",
    "clean_build": "build_app",
    "lint": "run_lint",
    "static_analysis": "run_lint",
    "unit_tests": "run_unit_tests",
    "integration_tests": "run_integration_tests",
    "ui_tests": "run_ui_tests",
}


class Orchestrator:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.distribution_root = Path(__file__).resolve().parent.parent
        self.store = ArtifactStore(self.project_root)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        path = self.project_root / "harness.yaml"
        if not path.exists():
            raise ConfigurationError(f"No harness.yaml in {self.project_root}. Run `mobile-harness init` first.")
        config = load_document(path)
        if config.get("version") != 1:
            raise ConfigurationError("Unsupported harness.yaml version; expected 1")
        return config

    def _definition(self, category: str, name: str) -> Dict[str, Any]:
        configured = self.config.get(f"{category}s", {}).get(name)
        candidates = []
        if configured:
            candidates.append(self.project_root / configured)
        candidates.append(self.distribution_root / f"{category}s" / f"{name}.yaml")
        for candidate in candidates:
            if candidate.is_file():
                return load_document(candidate)
        raise ConfigurationError(f"No {category} definition for {name!r}")

    def discover(self) -> Dict[str, Any]:
        profile, details = discover_project(self.project_root, self.config)
        validate_or_raise(profile, self.distribution_root / "contracts/project-profile.schema.json", "project profile")
        artifacts = write_project_context(self.project_root, self.store.context_root, profile, details)
        return {"status": "passed", "profile": profile, "artifacts": artifacts}

    def start(
        self,
        item_type: str,
        title: str,
        profile: Optional[str] = None,
        risk_level: str = "medium",
        risk_factors: Iterable[str] = (),
        requested_id: Optional[str] = None,
        request: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        selected_profile = profile or self.config.get("project", {}).get("default_profile", "standard")
        self._definition("profile", selected_profile)
        self._definition("workflow", item_type)
        manifest = self.store.create_run(
            item_type=item_type,
            title=title,
            profile=selected_profile,
            risk_level=risk_level,
            risk_factors=risk_factors,
            requested_id=requested_id,
            request=request,
        )
        validate_or_raise(manifest, self.distribution_root / "contracts/work-item.schema.json", "work item")
        return manifest

    def run_workflow(self, work_item_id: Optional[str] = None, profile: Optional[str] = None) -> Dict[str, Any]:
        run_root = self.store.resolve_run(work_item_id)
        manifest = load_document(run_root / "manifest.yaml")
        if profile:
            self._definition("profile", profile)
            manifest["profile"] = profile
            self.store.save_manifest(run_root, manifest)
        workflow = self._definition("workflow", manifest["type"])
        final_result: Dict[str, Any] = {}
        for stage_spec in workflow.get("stages", []):
            stage = stage_spec["id"]
            final_result = self.run_stage(stage, manifest["id"])
            if final_result.get("status") not in {"passed", "ready", "ready_with_accepted_risk"}:
                return final_result
        return final_result

    def run_stage(self, stage: str, work_item_id: Optional[str] = None) -> Dict[str, Any]:
        if stage not in STAGE_ORDER:
            raise ConfigurationError(f"Unknown stage {stage!r}; choose one of {', '.join(STAGE_ORDER)}")
        run_root = self.store.resolve_run(work_item_id)
        manifest = load_document(run_root / "manifest.yaml")
        workflow = self._definition("workflow", manifest["type"])
        stage_spec = next((item for item in workflow.get("stages", []) if item.get("id") == stage), None)
        if not stage_spec:
            raise ConfigurationError(f"Stage {stage!r} is absent from workflow {manifest['type']!r}")
        for dependency in stage_spec.get("depends_on", []):
            dependency_status = manifest.get("stages", {}).get(dependency, {}).get("status")
            if dependency_status != "passed":
                raise GateError(f"Stage {stage} requires {dependency}=passed; observed {dependency_status or 'not_run'}")

        self.store.update_stage(run_root, stage, "running", [])
        try:
            handler = getattr(self, f"_run_{stage}")
            result, artifacts = handler(run_root, manifest)
            status = result.get("status", "failed")
            manifest_status = "passed" if status in {"passed", "ready", "ready_with_accepted_risk"} else status
            self.store.update_stage(run_root, stage, manifest_status, artifacts, result.get("message", ""))
            return result
        except (ConfigurationError, GateError) as exc:
            self.store.update_stage(run_root, stage, "failed", [], str(exc))
            raise

    def _run_discovery(self, run_root: Path, manifest: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        result = self.discover()
        blocking = [item for item in result["profile"]["unknowns"] if item.get("status") == "blocking"]
        if blocking:
            return {"status": "failed", "blocking": blocking, "message": "Project discovery has blocking unknowns."}, result["artifacts"]
        return {"status": "passed", "project": result["profile"]["project"]}, result["artifacts"]

    def _run_rnd(self, run_root: Path, manifest: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        request = manifest.get("request", {})
        title = manifest["title"]
        supplied_brief = request.get("feature_brief", {})
        supplied_method = request.get("methodology", {}).get("rnd", {})
        approval = supplied_method.get("approval", {"status": "required", "evidence": ""})
        rnd_method = {
            "framework": "superpowers",
            "process": "superpowers:brainstorming",
            "classification": supplied_method.get("classification", "bounded"),
            "approval": approval,
        }
        brief = {
            "schema_version": 1,
            "work_item_id": manifest["id"],
            "methodology": rnd_method,
            "problem": supplied_brief.get("problem", f"The requested mobile capability, {title}, is not available."),
            "user": supplied_brief.get("user", "Mobile application user"),
            "value": supplied_brief.get("value", f"The user can complete {title}."),
            "scope": supplied_brief.get("scope", {"in": [title], "out": ["Unrelated application behavior"]}),
            "states": supplied_brief.get("states", ["loading", "content", "error", "retry"]),
            "integrations": supplied_brief.get("integrations", []),
            "uncertainties": supplied_brief.get(
                "uncertainties",
                [{"question": "Final product copy and analytics taxonomy", "status": "deferred", "resolution": "Use project-native defaults; confirm before release."}],
            ),
        }
        criteria_items = request.get("acceptance_criteria") or [
            {
                "id": "AC-001",
                "given": "the feature is opened",
                "when": "data is loading, available, or fails",
                "then": "the corresponding loading, content, or recoverable error state is presented",
                "priority": "must",
                "evidence": ["check:unit_tests"],
            },
            {
                "id": "AC-002",
                "given": "the user selects retry after an error",
                "when": "retry is invoked",
                "then": "loading restarts and a successful response can produce content",
                "priority": "must",
                "evidence": ["check:unit_tests"],
            },
        ]
        criteria = {"schema_version": 1, "work_item_id": manifest["id"], "criteria": criteria_items}
        validate_or_raise(brief, self.distribution_root / "contracts/feature-brief.schema.json", "feature brief")
        validate_or_raise(criteria, self.distribution_root / "contracts/acceptance-criteria.schema.json", "acceptance criteria")
        brief_path = run_root / "rnd/feature-brief.yaml"
        criteria_path = run_root / "rnd/acceptance-criteria.yaml"
        methodology_path = run_root / "rnd/methodology.yaml"
        write_document(brief_path, brief)
        write_document(criteria_path, criteria)
        write_document(
            methodology_path,
            {
                "schema_version": 1,
                "framework": "superpowers",
                "process": "superpowers:brainstorming",
                "classification": rnd_method["classification"],
                "approval": approval,
                "gate": "passed" if approval.get("status") == "approved" else "approval_required",
            },
        )
        write_text(
            run_root / "rnd/feature-brief.md",
            f"# Feature brief: {title}\n\n## Problem\n\n{brief['problem']}\n\n## User value\n\n{brief['value']}\n\n## States\n\n"
            + "\n".join(f"- {state}" for state in brief["states"])
            + f"\n\n## Methodology\n\n- Process: `{rnd_method['process']}`\n- Classification: `{rnd_method['classification']}`\n- Approval: `{approval.get('status', 'required')}`\n",
        )
        blocking = [item for item in brief["uncertainties"] if item.get("status") == "blocking"]
        if blocking:
            status = "failed"
            message = "Blocking product questions remain."
        elif approval.get("status") != "approved" or not approval.get("evidence"):
            status = "approval_required"
            message = "Superpowers brainstorming requires explicit design approval before development."
        else:
            status = "passed"
            message = ""
        artifacts = ["rnd/feature-brief.yaml", "rnd/feature-brief.md", "rnd/acceptance-criteria.yaml", "rnd/methodology.yaml"]
        return {"status": status, "blocking": blocking, "methodology": rnd_method, "message": message}, artifacts

    def _run_plan(self, run_root: Path, manifest: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        request = manifest.get("request", {})
        supplied = request.get("plan", {})
        criteria = load_document(run_root / "rnd/acceptance-criteria.yaml")["criteria"]
        profile = self._definition("profile", manifest["profile"])
        modules = supplied.get("modules") or load_document(self.store.context_root / "module-map.yaml").get("modules") or ["Application"]
        steps = supplied.get("steps") or [
            {
                "id": "STEP-001",
                "description": f"Implement {manifest['title']} using project-native modules and patterns.",
                "acceptance_criteria": [item["id"] for item in criteria],
            }
        ]
        scope = supplied.get(
            "scope",
            {
                "allowed_modules": modules,
                "protected_paths": [".git", "Generated", "Vendor", "Secrets"],
                "expected_file_changes": len(supplied.get("expected_files", [])) or 5,
                "max_file_changes_without_replan": 12,
            },
        )
        plan = {
            "schema_version": 1,
            "work_item_id": manifest["id"],
            "design": supplied.get("design", "Extend the existing project-native feature boundary and keep state transitions explicit."),
            "modules": modules,
            "expected_files": supplied.get("expected_files", []),
            "steps": steps,
            "scope": scope,
            "verification": supplied.get("verification", profile["verification"]["required"]),
            "rollback": supplied.get("rollback", "Revert the scoped feature files and route registration as one change set."),
            "risks": supplied.get("risks", []),
        }
        validate_or_raise(plan, self.distribution_root / "contracts/implementation-plan.schema.json", "implementation plan")
        covered = {criterion for step in steps for criterion in step.get("acceptance_criteria", [])}
        required = {item["id"] for item in criteria if item.get("priority") == "must"}
        missing = sorted(required - covered)
        path = run_root / "plan/implementation-plan.yaml"
        write_document(path, plan)
        if missing:
            return {"status": "failed", "missing_criteria": missing, "message": "Plan does not cover all must criteria."}, ["plan/implementation-plan.yaml"]
        return {"status": "passed", "scope": scope}, ["plan/implementation-plan.yaml"]

    def _run_dev(self, run_root: Path, manifest: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        plan = load_document(run_root / "plan/implementation-plan.yaml")
        expected_files = plan.get("expected_files", [])
        missing = [path for path in expected_files if not (self.project_root / path).is_file()]
        changed = self._changed_files()
        protected = plan["scope"].get("protected_paths", [])
        protected_changes = [path for path in changed if self._matches_any(path, protected)]
        over_budget = len(changed) > plan["scope"]["max_file_changes_without_replan"]
        status = "failed" if missing or protected_changes or over_budget else "passed"
        deviations = {
            "schema_version": 1,
            "missing_expected_files": missing,
            "protected_path_changes": protected_changes,
            "scope_budget_exceeded": over_budget,
            "changed_files": changed,
        }
        write_document(run_root / "dev/deviations.yaml", deviations)
        write_text(
            run_root / "dev/development-summary.md",
            f"# Development summary: {manifest['title']}\n\n"
            f"- Expected files present: {'yes' if not missing else 'no'}\n"
            f"- Observed changed files: {len(changed)}\n"
            f"- Protected changes: {len(protected_changes)}\n"
            f"- Scope budget: {len(changed)}/{plan['scope']['max_file_changes_without_replan']}\n",
        )
        message = ""
        if missing:
            message = f"Missing expected implementation files: {', '.join(missing)}"
        elif protected_changes:
            message = f"Protected paths changed: {', '.join(protected_changes)}"
        elif over_budget:
            message = "Scope budget exceeded; replan is required."
        return {"status": status, "missing": missing, "changed_files": changed, "message": message}, ["dev/development-summary.md", "dev/deviations.yaml"]

    def _run_verify(self, run_root: Path, manifest: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        context = load_document(self.store.context_root / "project-profile.yaml")
        profile = self._definition("profile", manifest["profile"])
        required_checks = profile["verification"]["required"]
        allowed_unsupported = set(profile["verification"].get("allow_unsupported", []))
        runner = CommandRunner(self.project_root, run_root)
        checks: Dict[str, Dict[str, Any]] = {}
        for check in required_checks:
            if check == "acceptance_criteria":
                checks[check] = self._verify_acceptance_criteria(run_root, checks)
                continue
            operation = CHECK_TO_OPERATION.get(check)
            command = context.get("commands", {}).get(operation or "")
            if not command:
                checks[check] = {"status": "unsupported", "details": f"Adapter does not provide {operation or check}."}
                continue
            result = runner.run(operation or check, command)
            checks[check] = result.as_check()
            checks[check]["details"]["provider"] = context.get("command_providers", {}).get(operation or "", "unresolved")
        blocking_findings = []
        for check in required_checks:
            status = checks[check]["status"]
            if status == "unsupported" and check in allowed_unsupported:
                continue
            if status != "passed":
                blocking_findings.append(
                    {"id": f"VER-{len(blocking_findings) + 1:03d}", "category": check, "message": f"Required check {check} is {status}."}
                )
        status = "passed" if not blocking_findings else "failed"
        result_document = {
            "schema_version": 1,
            "work_item_id": manifest["id"],
            "status": status,
            "profile": manifest["profile"],
            "methodology": {
                "framework": "superpowers",
                "process": "superpowers:verification-before-completion",
                "failure_process": "superpowers:systematic-debugging",
                "fresh_evidence": True,
            },
            "checks": checks,
            "blocking_findings": blocking_findings,
        }
        validate_or_raise(result_document, self.distribution_root / "contracts/verification-result.schema.json", "verification result")
        write_document(run_root / "verification/result.yaml", result_document)
        return {
            "status": status,
            "checks": checks,
            "blocking_findings": blocking_findings,
            "next_method": "superpowers:systematic-debugging" if blocking_findings else None,
            "message": "Required verification failed; investigate with superpowers:systematic-debugging." if blocking_findings else "",
        }, ["verification/result.yaml"]

    def _verify_acceptance_criteria(self, run_root: Path, checks: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        criteria = load_document(run_root / "rnd/acceptance-criteria.yaml")["criteria"]
        outcomes = []
        all_passed = True
        for criterion in criteria:
            references = criterion.get("evidence", [])
            resolved = []
            for reference in references:
                if reference.startswith("check:"):
                    check_name = reference.split(":", 1)[1]
                    passed = checks.get(check_name, {}).get("status") == "passed"
                else:
                    passed = (self.project_root / reference).exists() or (run_root / reference).exists()
                resolved.append({"reference": reference, "passed": passed})
            criterion_passed = bool(references) and all(item["passed"] for item in resolved)
            all_passed = all_passed and criterion_passed
            outcomes.append({"id": criterion["id"], "passed": criterion_passed, "evidence": resolved})
        evidence_path = run_root / f"evidence/acceptance-criteria-{timestamp_id()}.json"
        write_document(evidence_path, {"schema_version": 1, "criteria": outcomes, "status": "passed" if all_passed else "failed"})
        return {
            "status": "passed" if all_passed else "failed",
            "evidence": str(evidence_path.relative_to(self.project_root)),
            "details": {"covered": sum(1 for item in outcomes if item["passed"]), "total": len(outcomes)},
        }

    def _run_review(self, run_root: Path, manifest: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        plan = load_document(run_root / "plan/implementation-plan.yaml")
        changed = self._changed_files()
        reviewed_scope = changed or plan.get("expected_files", [])
        findings: List[Dict[str, Any]] = []
        protected = plan["scope"].get("protected_paths", [])
        for path in changed:
            if self._matches_any(path, protected):
                findings.append(self._finding(len(findings) + 1, "high", "scope", path, "Protected path changed.", "The change crosses the approved scope boundary.", "Revert the change or obtain approval.", True))
        risky_patterns = ((r"\bfatalError\s*\(", "high", "correctness", "A fatalError call is present."), (r"\btry!\b", "high", "error-handling", "Forced error handling is present."), (r"\bTODO\b", "medium", "maintainability", "A TODO remains in reviewed source."))
        for relative in reviewed_scope:
            path = self.project_root / relative
            if not path.is_file() or path.suffix not in {".swift", ".m", ".mm", ".kt", ".java", ".dart", ".tsx", ".ts"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern, severity, category, observation in risky_patterns:
                match = re.search(pattern, text)
                if match:
                    line = text.count("\n", 0, match.start()) + 1
                    finding = self._finding(len(findings) + 1, severity, category, relative, observation, "The construct can hide a production failure or unfinished work.", "Replace it with explicit, tested behavior or document an accepted risk.", severity in {"critical", "high"})
                    finding["line"] = line
                    findings.append(finding)
        blocking = [item for item in findings if item["blocking"] or item["severity"] in {"critical", "high"}]
        status = "changes_requested" if blocking else "passed"
        result = {
            "schema_version": 1,
            "work_item_id": manifest["id"],
            "status": status,
            "reviewed_scope": reviewed_scope,
            "mode": "deterministic-policy-scan",
            "findings": findings,
        }
        validate_or_raise(result, self.distribution_root / "contracts/review-result.schema.json", "review result")
        write_document(run_root / "review/result.yaml", result)
        return {"status": status, "findings": findings, "message": "Review has blocking findings." if blocking else ""}, ["review/result.yaml"]

    def _run_qa(self, run_root: Path, manifest: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        verification = load_document(run_root / "verification/result.yaml")
        request = manifest.get("request", {})
        supplied = request.get("qa_scenarios") or [
            {"id": "QA-001", "name": "Loading, content, and error state contract", "evidence": "check:unit_tests"},
            {"id": "QA-002", "name": "Retry recovery contract", "evidence": "check:unit_tests"},
        ]
        scenarios = []
        for scenario in supplied:
            evidence = scenario.get("evidence", "")
            if evidence.startswith("check:"):
                check = evidence.split(":", 1)[1]
                check_result = verification["checks"].get(check, {})
                passed = check_result.get("status") == "passed"
                resolved_evidence = check_result.get("evidence", "")
            else:
                passed = bool(evidence) and ((self.project_root / evidence).exists() or (run_root / evidence).exists())
                resolved_evidence = evidence
            scenarios.append(
                {
                    "id": scenario["id"],
                    "name": scenario["name"],
                    "status": "passed" if passed else "failed",
                    "evidence": resolved_evidence,
                    "reason": "" if passed else "Required evidence did not pass or is missing.",
                }
            )
        defects = []
        for scenario in scenarios:
            if scenario["status"] == "failed":
                defects.append({"id": f"QA-DEF-{len(defects) + 1:03d}", "severity": "high", "scenario": scenario["id"], "blocking": True})
        residual_risk = request.get("residual_risk", [])
        status = "passed" if not defects else "failed"
        result = {
            "schema_version": 1,
            "work_item_id": manifest["id"],
            "status": status,
            "scenarios": scenarios,
            "defects": defects,
            "residual_risk": residual_risk,
        }
        validate_or_raise(result, self.distribution_root / "contracts/qa-result.schema.json", "QA result")
        write_document(run_root / "qa/result.yaml", result)
        return {"status": status, "scenarios": scenarios, "defects": defects, "message": "QA has blocking defects." if defects else ""}, ["qa/result.yaml"]

    def _run_final(self, run_root: Path, manifest: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        verification = load_document(run_root / "verification/result.yaml")
        review = load_document(run_root / "review/result.yaml")
        qa = load_document(run_root / "qa/result.yaml")
        project_context = load_document(self.store.context_root / "project-profile.yaml")
        findings = verification["blocking_findings"] + review["findings"] + qa["defects"]
        if verification["status"] != "passed" or review["status"] != "passed" or qa["status"] != "passed":
            decision = "changes_requested"
        elif qa["residual_risk"]:
            decision = "ready_with_accepted_risk"
        else:
            decision = "ready"
        evidence = []
        for check in verification["checks"].values():
            if check.get("evidence"):
                evidence.append(check["evidence"])
        result = {
            "schema_version": 1,
            "work_item_id": manifest["id"],
            "decision": decision,
            "methodology": {
                "rnd": "superpowers:brainstorming",
                "verification": verification["methodology"]["process"],
                "build_provider": project_context.get("command_providers", {}).get("build_app", "unresolved"),
            },
            "stage_status": {"verification": verification["status"], "review": review["status"], "qa": qa["status"]},
            "evidence": evidence,
            "findings": findings,
            "unresolved_risks": qa["residual_risk"],
        }
        validate_or_raise(result, self.distribution_root / "contracts/final-report.schema.json", "final report")
        write_document(run_root / "final-report.yaml", result)
        evidence_md = "\n".join(f"- `{item}`" for item in evidence) or "- No executable evidence recorded"
        risks_md = "\n".join(f"- {item}" for item in qa["residual_risk"]) or "- None"
        write_text(
            run_root / "final-report.md",
            f"# Feature report: {manifest['title']}\n\n## Decision\n\n{decision.replace('_', ' ').title()}\n\n"
            f"## Methodology\n\n- R&D: `superpowers:brainstorming`\n- Verification: `{verification['methodology']['process']}`\n- Build provider: `{result['methodology']['build_provider']}`\n\n"
            f"## Stage status\n\n- Verification: {verification['status']}\n- Review: {review['status']}\n- QA: {qa['status']}\n\n"
            f"## Evidence\n\n{evidence_md}\n\n## Unresolved risk\n\n{risks_md}\n",
        )
        return {"status": decision, "decision": decision, "report": str((run_root / "final-report.md").relative_to(self.project_root))}, ["final-report.yaml", "final-report.md"]

    def status(self, work_item_id: Optional[str] = None) -> Dict[str, Any]:
        manifest = self.store.load_manifest(work_item_id)
        return {
            "work_item_id": manifest["id"],
            "title": manifest["title"],
            "state": manifest["state"],
            "profile": manifest["profile"],
            "stages": {key: value.get("status", "not_run") for key, value in manifest.get("stages", {}).items()},
        }

    def _changed_files(self) -> List[str]:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=str(self.project_root),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return []
        if result.returncode != 0:
            return []
        paths = []
        for line in result.stdout.splitlines():
            if len(line) < 4:
                continue
            value = line[3:]
            if " -> " in value:
                value = value.split(" -> ", 1)[1]
            if value.startswith(".mobile-harness/"):
                continue
            paths.append(value)
        return sorted(set(paths))

    @staticmethod
    def _matches_any(path: str, patterns: Iterable[str]) -> bool:
        return any(path == pattern or path.startswith(pattern.rstrip("/") + "/") or fnmatch.fnmatch(path, pattern) for pattern in patterns)

    @staticmethod
    def _finding(index: int, severity: str, category: str, file: str, observation: str, risk: str, recommendation: str, blocking: bool) -> Dict[str, Any]:
        return {
            "id": f"REV-{index:03d}",
            "severity": severity,
            "category": category,
            "file": file,
            "observation": observation,
            "risk": risk,
            "recommendation": recommendation,
            "confidence": "high",
            "blocking": blocking,
        }


def create_default_config(project_root: Path, name: Optional[str], platform: str, profile: str) -> Path:
    path = project_root / "harness.yaml"
    if path.exists():
        raise ConfigurationError(f"Refusing to overwrite existing {path}")
    config = {
        "version": 1,
        "project": {"name": name or project_root.name, "platform": platform, "adapter": "auto" if platform == "auto" else "ios-xcode", "default_profile": profile},
        "context": {"source": ".mobile-harness/context/project-profile.yaml"},
        "integrations": {
            "methodology": {
                "provider": "superpowers",
                "contract": "integrations/superpowers.yaml",
                "required_for": ["rnd", "verification"],
            },
            "mobile_build": {
                "provider": "mobilebuildmcp",
                "contract": "integrations/mobilebuildmcp.yaml",
                "enabled": True,
                "command": ["npx", "-y", "mobilebuildmcp@2.7.1"],
            },
        },
        "workflows": {"feature": "workflows/feature.yaml", "bugfix": "workflows/bugfix.yaml", "hotfix": "workflows/hotfix.yaml"},
        "profiles": {"prototype": "profiles/prototype.yaml", "standard": "profiles/standard.yaml", "strict": "profiles/strict.yaml", "hotfix": "profiles/hotfix.yaml"},
        "policies": ["policies/default.yaml", "policies/dependency-policy.yaml", "policies/protected-paths.yaml"],
        "gates": {"require_clean_build": True, "require_tests": True, "require_review": True},
        "human_approval": {"required_for": ["add_external_dependency", "public_api_change", "data_migration", "privacy_behavior_change", "release"]},
    }
    write_document(path, config)
    ArtifactStore(project_root).initialize()
    return path
