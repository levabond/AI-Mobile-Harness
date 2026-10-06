import shutil
import tempfile
import unittest
from pathlib import Path

from mobile_harness.documents import load_document
from mobile_harness.orchestrator import Orchestrator


ROOT = Path(__file__).resolve().parent.parent


class OrchestratorTests(unittest.TestCase):
    def test_profile_details_vertical_slice_reaches_evidence_backed_final_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "fixture"
            shutil.copytree(ROOT / "evals/fixtures/ios-small-clean", project)
            request = load_document(ROOT / "examples/profile-details-request.yaml")
            orchestrator = Orchestrator(project)
            manifest = orchestrator.start(
                "feature",
                "Profile Details",
                profile="standard",
                requested_id="profile-details",
                risk_factors=["user_visible_change", "navigation_change"],
                request=request,
            )

            outcome = orchestrator.run_workflow(manifest["id"])

            self.assertEqual(outcome["decision"], "ready_with_accepted_risk")
            report = load_document(project / ".mobile-harness/runs/profile-details/final-report.yaml")
            self.assertEqual(report["stage_status"], {"verification": "passed", "review": "passed", "qa": "passed"})
            self.assertEqual(report["methodology"]["rnd"], "superpowers:brainstorming")
            self.assertEqual(report["methodology"]["build_provider"], "native-swift")
            self.assertGreaterEqual(len(report["evidence"]), 4)
            verification = load_document(project / ".mobile-harness/runs/profile-details/verification/result.yaml")
            self.assertEqual(verification["methodology"]["process"], "superpowers:verification-before-completion")
            self.assertTrue(verification["methodology"]["fresh_evidence"])
            self.assertEqual(verification["checks"]["build"]["details"]["provider"], "native-swift")
            for relative in report["evidence"]:
                self.assertTrue((project / relative).is_file(), relative)

    def test_rnd_requires_superpowers_design_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "fixture"
            shutil.copytree(ROOT / "evals/fixtures/ios-small-clean", project)
            orchestrator = Orchestrator(project)
            manifest = orchestrator.start("feature", "Unapproved feature", requested_id="unapproved")
            orchestrator.run_stage("discovery", manifest["id"])

            outcome = orchestrator.run_stage("rnd", manifest["id"])

            self.assertEqual(outcome["status"], "approval_required")
            method = load_document(project / ".mobile-harness/runs/unapproved/rnd/methodology.yaml")
            self.assertEqual(method["process"], "superpowers:brainstorming")
            self.assertEqual(method["gate"], "approval_required")


if __name__ == "__main__":
    unittest.main()
