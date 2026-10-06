from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .documents import redact, timestamp_id, utc_now, write_document, write_text


@dataclass(frozen=True)
class CommandResult:
    operation: str
    command: List[str]
    exit_code: Optional[int]
    status: str
    started_at: str
    finished_at: str
    log_path: str
    metadata_path: str
    timed_out: bool = False

    def as_check(self) -> Dict[str, Any]:
        return {
            "status": "passed" if self.status == "passed" else "failed",
            "evidence": self.metadata_path,
            "details": {"exit_code": self.exit_code, "log": self.log_path, "timed_out": self.timed_out},
        }


class CommandRunner:
    def __init__(self, project_root: Path, run_root: Path, timeout_seconds: int = 600):
        self.project_root = project_root
        self.evidence_root = run_root / "evidence"
        self.timeout_seconds = timeout_seconds

    def run(self, operation: str, command: List[str]) -> CommandResult:
        if not command or not all(isinstance(part, str) and part for part in command):
            raise ValueError(f"Invalid command for {operation}: expected a non-empty string array")
        evidence_id = f"{operation}-{timestamp_id()}"
        log_path = self.evidence_root / f"{evidence_id}.log"
        metadata_path = self.evidence_root / f"{evidence_id}.json"
        started_at = utc_now()
        timed_out = False
        exit_code: Optional[int]
        cache_root = self.project_root / ".mobile-harness/cache"
        clang_cache = cache_root / "clang-modules"
        swift_cache = cache_root / "swift-modules"
        clang_cache.mkdir(parents=True, exist_ok=True)
        swift_cache.mkdir(parents=True, exist_ok=True)
        environment = os.environ.copy()
        environment["CLANG_MODULE_CACHE_PATH"] = str(clang_cache)
        environment["SWIFTPM_MODULECACHE_OVERRIDE"] = str(swift_cache)
        try:
            completed = subprocess.run(
                command,
                cwd=str(self.project_root),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=self.timeout_seconds,
                check=False,
                env=environment,
            )
            output = completed.stdout or ""
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            output += f"\nCommand timed out after {self.timeout_seconds} seconds.\n"
            exit_code = None
            timed_out = True
        except OSError as exc:
            output = f"Unable to execute command: {exc}\n"
            exit_code = None
        finished_at = utc_now()
        status = "passed" if exit_code == 0 and not timed_out else "failed"
        safe_output = redact(output)
        write_text(log_path, safe_output)
        safe_command = [redact(part) for part in command]
        metadata = {
            "schema_version": 1,
            "operation": operation,
            "command": safe_command,
            "working_directory": ".",
            "started_at": started_at,
            "finished_at": finished_at,
            "exit_code": exit_code,
            "timed_out": timed_out,
            "status": status,
            "log": str(log_path.relative_to(self.project_root)),
        }
        write_document(metadata_path, metadata)
        return CommandResult(
            operation=operation,
            command=safe_command,
            exit_code=exit_code,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            log_path=str(log_path.relative_to(self.project_root)),
            metadata_path=str(metadata_path.relative_to(self.project_root)),
            timed_out=timed_out,
        )
