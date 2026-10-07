import json
import tempfile
import unittest
from pathlib import Path

from genjutsu.scenario import (
    ScenarioError,
    find_route,
    load_scenario,
    response_for,
    validate_scenario,
)


VALID_SCENARIO = {
    "version": 1,
    "name": "profile",
    "network": {
        "routes": [
            {
                "method": "GET",
                "path": "/profile",
                "response": {"status": 200, "body": {"id": "user-1"}},
            }
        ]
    },
}


class ScenarioTests(unittest.TestCase):
    def test_valid_scenario_has_no_errors(self) -> None:
        self.assertEqual(validate_scenario(VALID_SCENARIO), [])

    def test_duplicate_routes_are_rejected(self) -> None:
        scenario = json.loads(json.dumps(VALID_SCENARIO))
        scenario["network"]["routes"].append(
            {
                "method": "get",
                "path": "/profile",
                "response": {"status": 201},
            }
        )
        errors = validate_scenario(scenario)
        self.assertTrue(any("duplicates route" in error for error in errors))

    def test_invalid_file_reports_contract_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text('{"version": 1}', encoding="utf-8")
            with self.assertRaisesRegex(ScenarioError, "name must be"):
                load_scenario(path)

    def test_route_matching_is_exact(self) -> None:
        self.assertIsNotNone(find_route(VALID_SCENARIO, "get", "/profile"))
        self.assertIsNone(find_route(VALID_SCENARIO, "GET", "/Profile"))

    def test_missing_route_has_diagnostic_response(self) -> None:
        response, configured = response_for(VALID_SCENARIO, "GET", "/missing")
        self.assertFalse(configured)
        self.assertEqual(response["status"], 404)
        self.assertEqual(response["body"]["error"], "genjutsu_route_not_found")


if __name__ == "__main__":
    unittest.main()
