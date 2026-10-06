import tempfile
import unittest
from pathlib import Path

from mobile_harness.documents import load_document, redact, write_document


class DocumentTests(unittest.TestCase):
    def test_round_trips_json_compatible_yaml(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "artifact.yaml"
            write_document(path, {"version": 1, "value": "ok"})
            self.assertEqual(load_document(path), {"version": 1, "value": "ok"})

    def test_redacts_common_secrets(self):
        value = "Authorization: Bearer abc123\napi_key=super-secret\nghp-abcdefghijklmnop"
        redacted = redact(value)
        self.assertNotIn("abc123", redacted)
        self.assertNotIn("super-secret", redacted)
        self.assertNotIn("ghp-abcdefghijklmnop", redacted)
        self.assertGreaterEqual(redacted.count("[REDACTED]"), 3)


if __name__ == "__main__":
    unittest.main()

