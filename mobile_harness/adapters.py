from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .documents import utc_now, write_document, write_text
from .errors import ConfigurationError


IGNORED_PARTS = {".git", ".build", ".swiftpm", ".mobile-harness", "DerivedData", "Pods"}


def _relative_directories_with(root: Path, pattern: str) -> List[str]:
    values = set()
    for path in root.rglob(pattern):
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        values.add(str(path.parent.relative_to(root)))
    return sorted(value for value in values if value != ".")


def _hash_files(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path.name).encode("utf-8"))
        try:
            digest.update(path.read_bytes())
        except OSError:
            continue
    return digest.hexdigest()


class IOSXcodeAdapter:
    name = "ios-xcode"
    platform = "ios"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.mobile_build = self.config.get("integrations", {}).get("mobile_build", {})

    def detect(self, root: Path) -> bool:
        return bool(list(root.glob("*.xcworkspace")) or list(root.glob("*.xcodeproj")) or (root / "Package.swift").is_file())

    def discover(self, root: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        root = root.resolve()
        workspaces = sorted(root.glob("*.xcworkspace"))
        projects = sorted(root.glob("*.xcodeproj"))
        package = root / "Package.swift"
        if not (workspaces or projects or package.is_file()):
            raise ConfigurationError("No .xcworkspace, .xcodeproj, or Package.swift found for ios-xcode adapter")

        manifest_files: List[Path] = []
        project_kind: str
        commands: Dict[str, List[str]] = {}
        command_providers: Dict[str, str] = {}
        unknowns: List[Dict[str, str]] = []
        mobile_build_prefix = self._mobile_build_prefix()
        mobile_build_enabled = bool(self.mobile_build.get("enabled", False))
        if mobile_build_enabled and not mobile_build_prefix:
            unknowns.append(
                {
                    "status": "blocking",
                    "question": "MobileBuildMCP is enabled, but its configured executable is unavailable.",
                }
            )
        capabilities = {
            "build_app": "supported",
            "run_unit_tests": "supported",
            "run_lint": "supported" if shutil.which("swift") else "unsupported",
            "run_integration_tests": "unsupported",
            "run_ui_tests": "unsupported",
            "capture_screenshot": "unsupported",
            "inspect_accessibility": "unsupported",
        }

        if workspaces or projects:
            container_flag = "-workspace" if workspaces else "-project"
            container = (workspaces or projects)[0]
            manifest_files.extend(path for path in container.rglob("project.pbxproj"))
            scheme = self._first_scheme(root, container_flag, container.name)
            if scheme:
                if mobile_build_enabled and mobile_build_prefix:
                    path_flag = "--workspace-path" if workspaces else "--project-path"
                    common_options = ["--scheme", scheme, path_flag, container.name, "--output", "json"]
                    commands["build_app"] = mobile_build_prefix + ["simulator", "build"] + common_options
                    commands["run_unit_tests"] = mobile_build_prefix + ["simulator", "test"] + common_options
                    command_providers.update({"build_app": "MobileBuildMCP", "run_unit_tests": "MobileBuildMCP"})
                else:
                    common = [
                        "xcodebuild",
                        container_flag,
                        container.name,
                        "-scheme",
                        scheme,
                        "-destination",
                        "generic/platform=iOS Simulator",
                        "CODE_SIGNING_ALLOWED=NO",
                    ]
                    commands["build_app"] = common + ["build"]
                    commands["run_unit_tests"] = common + ["test"]
                    command_providers.update({"build_app": "native-xcodebuild", "run_unit_tests": "native-xcodebuild"})
            else:
                unknowns.append({"status": "blocking", "question": "No shared Xcode scheme could be resolved."})
            project_kind = "xcode-workspace" if workspaces else "xcode-project"
        else:
            package_text = package.read_text(encoding="utf-8")
            manifest_files.append(package)
            package_name = self._package_name(package_text) or root.name
            if mobile_build_enabled and mobile_build_prefix:
                commands["build_app"] = mobile_build_prefix + ["swift-package", "build", "--package-path", ".", "--output", "json"]
                commands["run_unit_tests"] = mobile_build_prefix + ["swift-package", "test", "--package-path", ".", "--output", "json"]
                command_providers.update({"build_app": "MobileBuildMCP", "run_unit_tests": "MobileBuildMCP"})
            elif not mobile_build_enabled:
                commands["build_app"] = [
                    "xcrun",
                    "swift",
                    "build",
                    "--disable-sandbox",
                    "--package-path",
                    ".",
                    "--scratch-path",
                    ".mobile-harness/build",
                ]
                commands["run_unit_tests"] = [
                    "xcrun",
                    "swift",
                    "test",
                    "--disable-sandbox",
                    "--package-path",
                    ".",
                    "--scratch-path",
                    ".mobile-harness/build",
                ]
                command_providers.update({"build_app": "native-swift", "run_unit_tests": "native-swift"})
            swift_paths = [path for path in ("Sources", "Tests") if (root / path).exists()]
            if swift_paths and shutil.which("swift"):
                commands["run_lint"] = ["xcrun", "swift", "format", "lint", "--recursive", "--strict"] + swift_paths
                command_providers["run_lint"] = "swift-format"
            project_kind = "swift-package"
            capabilities.update({"launch_device": "unsupported", "install_app": "unsupported"})
            if "SwiftUI" not in "".join(path.read_text(encoding="utf-8", errors="ignore") for path in root.glob("Sources/**/*.swift")):
                unknowns.append({"status": "assumption", "question": "SwiftUI usage was not detected in package sources."})
            if package_name:
                project_name = package_name

        source_paths = _relative_directories_with(root, "*.swift")
        test_paths = sorted(path for path in source_paths if "test" in path.lower())
        source_paths = sorted(path for path in source_paths if path not in test_paths)
        if not source_paths:
            unknowns.append({"status": "blocking", "question": "No Swift source paths were found."})
        if not test_paths:
            unknowns.append({"status": "assumption", "question": "No XCTest source paths were found."})
        if "build_app" not in commands:
            unknowns.append({"status": "blocking", "question": "A working build command could not be resolved."})

        conventions = []
        for candidate in (".swift-format", ".swiftlint.yml", "CONTRIBUTING.md", "AGENTS.md"):
            if (root / candidate).exists():
                conventions.append(candidate)
        project_name = locals().get("project_name", root.stem)
        profile = {
            "schema_version": 1,
            "project": {
                "name": project_name,
                "root": ".",
                "platform": "ios",
                "languages": ["Swift"],
                "kind": project_kind,
            },
            "adapter": self.name,
            "paths": {"sources": source_paths, "tests": test_paths, "generated": [".build", "DerivedData", "Generated"]},
            "commands": commands,
            "command_providers": command_providers,
            "conventions": conventions,
            "capabilities": capabilities,
            "freshness": {"discovered_at": utc_now(), "configuration_sha256": _hash_files(manifest_files)},
            "unknowns": unknowns,
        }
        details = {
            "modules": self._modules(root, package if package.is_file() else None),
            "has_swiftui": self._contains(root, "import SwiftUI"),
            "has_localization": bool(list(root.rglob("*.strings")) or list(root.rglob("*.xcstrings"))),
            "has_xctest": self._contains(root, "import XCTest"),
            "build_provider": command_providers.get("build_app", "unresolved"),
        }
        return profile, details

    def _mobile_build_prefix(self) -> Optional[List[str]]:
        if not self.mobile_build.get("enabled", False):
            return None
        configured = self.mobile_build.get("command", ["npx", "-y", "mobilebuildmcp@2.7.1"])
        if not isinstance(configured, list) or not configured or not all(isinstance(item, str) and item for item in configured):
            return None
        return list(configured) if shutil.which(configured[0]) else None

    def _first_scheme(self, root: Path, container_flag: str, container: str) -> Optional[str]:
        try:
            result = subprocess.run(
                ["xcodebuild", container_flag, container, "-list", "-json"],
                cwd=str(root),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=30,
                check=False,
            )
            payload = json.loads(result.stdout) if result.returncode == 0 else {}
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
            return None
        for key in ("workspace", "project"):
            schemes = payload.get(key, {}).get("schemes", [])
            if schemes:
                return schemes[0]
        return None

    @staticmethod
    def _package_name(package_text: str) -> Optional[str]:
        match = re.search(r"\bname\s*:\s*\"([^\"]+)\"", package_text)
        return match.group(1) if match else None

    @staticmethod
    def _modules(root: Path, package: Optional[Path]) -> List[str]:
        if package:
            text = package.read_text(encoding="utf-8")
            return sorted(set(re.findall(r"\.(?:target|testTarget)\s*\(\s*name\s*:\s*\"([^\"]+)\"", text)))
        return sorted({path.parent.name for path in root.rglob("*.swift") if not any(part in IGNORED_PARTS for part in path.parts)})

    @staticmethod
    def _contains(root: Path, needle: str) -> bool:
        for path in root.rglob("*.swift"):
            if any(part in IGNORED_PARTS for part in path.parts):
                continue
            try:
                if needle in path.read_text(encoding="utf-8"):
                    return True
            except OSError:
                continue
        return False


def discover_project(root: Path, config: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    adapter = IOSXcodeAdapter(config)
    if adapter.detect(root):
        return adapter.discover(root)
    raise ConfigurationError("Unsupported project: expected an iOS Xcode project/workspace or Swift Package")


def write_project_context(root: Path, context_root: Path, profile: Dict[str, Any], details: Dict[str, Any]) -> List[str]:
    context_root.mkdir(parents=True, exist_ok=True)
    write_document(context_root / "project-profile.yaml", profile)
    write_document(context_root / "commands.yaml", {"version": 1, "commands": profile["commands"]})
    write_document(context_root / "module-map.yaml", {"version": 1, "modules": details["modules"]})
    write_document(
        context_root / "design-system-map.yaml",
        {"version": 1, "swiftui_detected": details["has_swiftui"], "localization_detected": details["has_localization"]},
    )
    architecture = (
        "# Architecture map\n\n"
        f"- Project kind: `{profile['project']['kind']}`\n"
        f"- Adapter: `{profile['adapter']}`\n"
        f"- Build provider: `{details['build_provider']}`\n"
        f"- Modules: {', '.join(details['modules']) or 'none detected'}\n"
        f"- SwiftUI detected: {'yes' if details['has_swiftui'] else 'no'}\n"
    )
    write_text(context_root / "architecture-map.md", architecture)
    conventions = "# Conventions\n\n" + ("\n".join(f"- `{item}`" for item in profile["conventions"]) or "No explicit convention files detected.")
    write_text(context_root / "conventions.md", conventions)
    tests = "# Test infrastructure\n\n" + f"- XCTest detected: {'yes' if details['has_xctest'] else 'no'}\n- Test paths: {', '.join(profile['paths']['tests']) or 'none'}\n"
    write_text(context_root / "test-infrastructure.md", tests)
    risks = [item for item in profile["unknowns"] if item.get("status") in {"blocking", "assumption"}]
    write_text(context_root / "risks.md", "# Discovery risks\n\n" + ("\n".join(f"- **{item['status']}**: {item['question']}" for item in risks) or "No discovery risks recorded."))
    return [
        str(path.relative_to(root))
        for path in sorted(context_root.iterdir())
        if path.is_file()
    ]
