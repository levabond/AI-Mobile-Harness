import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from genjutsu.server import build_server


STATE = {
    "cast_id": "test-cast",
    "scenario": {
        "version": 1,
        "name": "server-test",
        "network": {
            "routes": [
                {
                    "method": "GET",
                    "path": "/profile",
                    "response": {
                        "status": 200,
                        "body": {"id": "user-1"},
                    },
                },
                {
                    "method": "POST",
                    "path": "/logout",
                    "response": {"status": 401, "body": {"error": "expired"}},
                },
            ]
        },
    },
}


class ServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.request_log = Path(self.temporary_directory.name) / "requests.jsonl"
        self.server = build_server(STATE, "127.0.0.1", 0, self.request_log)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary_directory.cleanup()

    def test_configured_route_returns_json_and_scenario_header(self) -> None:
        with urllib.request.urlopen(f"{self.base_url}/profile") as response:
            body = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["X-Genjutsu-Scenario"], "server-test")
            self.assertEqual(body["id"], "user-1")

        records = self.request_log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(records), 1)
        self.assertTrue(json.loads(records[0])["configured_route"])

    def test_failure_status_is_replayed(self) -> None:
        request = urllib.request.Request(
            f"{self.base_url}/logout", data=b"{}", method="POST"
        )
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        self.assertEqual(caught.exception.code, 401)
        self.assertEqual(json.loads(caught.exception.read())["error"], "expired")


if __name__ == "__main__":
    unittest.main()
