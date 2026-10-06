from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .documents import load_document, slugify, utc_now, write_document
from .errors import ConfigurationError


STAGE_DIRECTORIES = ("rnd", "plan", "dev", "verification", "review", "qa", "evidence")


class ArtifactStore:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.root = self.project_root / ".mobile-harness"
        self.context_root = self.root / "context"
        self.runs_root = self.root / "runs"

    def initialize(self) -> None:
        self.context_root.mkdir(parents=True, exist_ok=True)
        self.runs_root.mkdir(parents=True, exist_ok=True)

    def create_run(
        self,
        item_type: str,
        title: str,
        profile: str,
        risk_level: str,
        risk_factors: Iterable[str],
        requested_id: Optional[str] = None,
        request: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self.initialize()
        base = slugify(requested_id or f"{item_type}-{title}")
        item_id = base
        suffix = 2
        while (self.runs_root / item_id).exists():
            item_id = f"{base}-{suffix}"
            suffix += 1
        run_root = self.runs_root / item_id
        run_root.mkdir(parents=True)
        for directory in STAGE_DIRECTORIES:
            (run_root / directory).mkdir()
        manifest = {
            "schema_version": 1,
            "id": item_id,
            "type": item_type,
            "title": title,
            "state": "draft",
            "profile": profile,
            "risk": {"level": risk_level, "factors": list(risk_factors)},
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "stages": {},
            "approvals": [],
        }
        if request:
            manifest["request"] = request
        write_document(run_root / "manifest.yaml", manifest)
        write_document(self.root / "active-run.yaml", {"work_item_id": item_id})
        return manifest

    def resolve_run(self, work_item_id: Optional[str] = None) -> Path:
        item_id = work_item_id
        if item_id is None:
            active = load_document(self.root / "active-run.yaml")
            item_id = active.get("work_item_id")
        if not isinstance(item_id, str) or not item_id:
            raise ConfigurationError("No active work item. Run `mobile-harness start ...` first.")
        run_root = (self.runs_root / item_id).resolve()
        if run_root.parent != self.runs_root.resolve() or not run_root.is_dir():
            raise ConfigurationError(f"Unknown work item: {item_id}")
        return run_root

    def load_manifest(self, work_item_id: Optional[str] = None) -> Dict[str, Any]:
        return load_document(self.resolve_run(work_item_id) / "manifest.yaml")

    def save_manifest(self, run_root: Path, manifest: Dict[str, Any]) -> None:
        manifest["updated_at"] = utc_now()
        write_document(run_root / "manifest.yaml", manifest)

    def update_stage(
        self,
        run_root: Path,
        stage: str,
        status: str,
        artifacts: Iterable[str],
        message: str = "",
    ) -> Dict[str, Any]:
        manifest = load_document(run_root / "manifest.yaml")
        previous = manifest.setdefault("stages", {}).get(stage, {})
        started_at = previous.get("started_at", utc_now())
        manifest["stages"][stage] = {
            "status": status,
            "started_at": started_at,
            "finished_at": utc_now() if status in {"passed", "failed", "approval_required"} else None,
            "artifacts": list(artifacts),
            "message": message,
        }
        state_by_stage = {
            "discovery": "discovery",
            "rnd": "discovery",
            "plan": "ready_for_development",
            "dev": "ready_for_validation",
            "verify": "validation_in_progress",
            "review": "validation_in_progress",
            "qa": "validation_in_progress",
            "final": "ready_for_delivery",
        }
        if status == "failed":
            manifest["state"] = "changes_requested"
        elif status == "approval_required":
            manifest["state"] = "approval_required"
        else:
            manifest["state"] = state_by_stage.get(stage, manifest["state"])
        self.save_manifest(run_root, manifest)
        return manifest

