from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict

from .documents import load_document
from .orchestrator import Orchestrator


def run_profile_details_eval(distribution_root: Path) -> Dict[str, Any]:
    fixture = distribution_root / "evals/fixtures/ios-small-clean"
    request_path = distribution_root / "examples/profile-details-request.yaml"
    if not fixture.is_dir() or not request_path.is_file():
        return {"status": "failed", "message": "Profile Details fixture or request is missing."}
    with tempfile.TemporaryDirectory(prefix="mobile-harness-eval-") as temporary:
        project_root = Path(temporary) / "ios-small-clean"
        shutil.copytree(fixture, project_root)
        orchestrator = Orchestrator(project_root)
        request = load_document(request_path)
        manifest = orchestrator.start(
            "feature",
            "Profile Details",
            profile="standard",
            risk_level="medium",
            risk_factors=["user_visible_change", "navigation_change"],
            requested_id="profile-details",
            request=request,
        )
        result = orchestrator.run_workflow(manifest["id"])
        report = load_document(project_root / ".mobile-harness/runs/profile-details/final-report.yaml") if result.get("status") in {"ready", "ready_with_accepted_risk"} else None
        return {
            "status": "passed" if result.get("status") in {"ready", "ready_with_accepted_risk"} else "failed",
            "decision": result.get("decision"),
            "work_item_id": manifest["id"],
            "stage_status": report.get("stage_status") if report else None,
            "evidence_count": len(report.get("evidence", [])) if report else 0,
            "message": result.get("message", ""),
        }

