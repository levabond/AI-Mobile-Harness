import json
import tempfile
import unittest
from pathlib import Path

from genjutsu.scenario import ScenarioError
from genjutsu.state import cast_scenario, load_active_state, release_active_state


SCENARIO = {
    "version": 1,
    "name": "empty",
    "network": {"routes": []},
}


class StateTests(unittest.TestCase):
    def test_cast_load_and_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_file = Path(directory) / "state" / "active.json"
            cast = cast_scenario(SCENARIO, "scenario.json", state_file)

            self.assertTrue(state_file.exists())
            self.assertEqual(load_active_state(state_file)["cast_id"], cast["cast_id"])
            self.assertTrue(release_active_state(state_file))
            self.assertFalse(release_active_state(state_file))

    def test_integrity_check_detects_modified_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_file = Path(directory) / "active.json"
            cast_scenario(SCENARIO, "scenario.json", state_file)

            state = json.loads(state_file.read_text(encoding="utf-8"))
            state["scenario"]["name"] = "modified"
            state_file.write_text(json.dumps(state), encoding="utf-8")

            with self.assertRaisesRegex(ScenarioError, "integrity check"):
                load_active_state(state_file)


if __name__ == "__main__":
    unittest.main()
