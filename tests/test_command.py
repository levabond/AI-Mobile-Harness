import tempfile
import unittest
from pathlib import Path

from mobile_harness.command import CommandRunner
from mobile_harness.documents import load_document


class CommandRunnerTests(unittest.TestCase):
    def test_records_exit_code_and_redacted_log(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            run_root = project / ".mobile-harness/runs/test"
            result = CommandRunner(project, run_root).run(
                "sample", ["/usr/bin/printf", "api_key=do-not-store"]
            )

            self.assertEqual(result.status, "passed")
            metadata = load_document(project / result.metadata_path)
            self.assertEqual(metadata["exit_code"], 0)
            self.assertEqual(metadata["status"], "passed")
            self.assertNotIn("do-not-store", " ".join(metadata["command"]))
            log = (project / result.log_path).read_text(encoding="utf-8")
            self.assertNotIn("do-not-store", log)


if __name__ == "__main__":
    unittest.main()
