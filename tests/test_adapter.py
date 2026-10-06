import unittest
from pathlib import Path

from mobile_harness.adapters import discover_project
from mobile_harness.errors import ConfigurationError


ROOT = Path(__file__).resolve().parent.parent


class AdapterTests(unittest.TestCase):
    def test_discovers_swift_package_fixture(self):
        profile, details = discover_project(ROOT / "evals/fixtures/ios-small-clean")

        self.assertEqual(profile["adapter"], "ios-xcode")
        self.assertEqual(profile["project"]["kind"], "swift-package")
        self.assertIn("build_app", profile["commands"])
        self.assertIn("run_unit_tests", profile["commands"])
        self.assertEqual(profile["command_providers"]["build_app"], "native-swift")
        self.assertIn("ProfileFeature", details["modules"])

    def test_routes_builds_through_mobilebuildmcp_when_enabled(self):
        config = {
            "integrations": {
                "mobile_build": {
                    "enabled": True,
                    "command": ["npx", "-y", "mobilebuildmcp@2.7.1"],
                }
            }
        }

        profile, details = discover_project(ROOT / "evals/fixtures/ios-small-clean", config)

        self.assertEqual(profile["command_providers"]["build_app"], "MobileBuildMCP")
        self.assertEqual(profile["commands"]["build_app"][:5], ["npx", "-y", "mobilebuildmcp@2.7.1", "swift-package", "build"])
        self.assertEqual(details["build_provider"], "MobileBuildMCP")

    def test_rejects_malformed_fixture(self):
        with self.assertRaises(ConfigurationError):
            discover_project(ROOT / "evals/fixtures/malformed-project")


if __name__ == "__main__":
    unittest.main()
