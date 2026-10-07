"""Standard-library HTTP adapter for an active Genjutsu scenario."""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Type
from urllib.parse import urlsplit

from .scenario import response_for


_request_log_lock = threading.Lock()


def _encode_body(body: Any) -> tuple[bytes, str]:
    if isinstance(body, (dict, list)):
        return (
            json.dumps(body, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )
    if body is None:
        return b"", "text/plain; charset=utf-8"
    return str(body).encode("utf-8"), "text/plain; charset=utf-8"


def _append_request_log(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    with _request_log_lock:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def make_handler(
    state: dict[str, Any], request_log: Path
) -> Type[BaseHTTPRequestHandler]:
    """Build a request handler bound to one immutable active-state snapshot."""

    scenario = state["scenario"]
    scenario_name = scenario["name"]
    cast_id = state.get("cast_id")

    class GenjutsuHandler(BaseHTTPRequestHandler):
        server_version = "Genjutsu/0.1"

        def _handle(self) -> None:
            parsed = urlsplit(self.path)
            response, configured = response_for(scenario, self.command, parsed.path)

            request_size = int(self.headers.get("Content-Length", "0") or "0")
            request_body = self.rfile.read(request_size) if request_size else b""

            delay_ms = float(response.get("delay_ms", 0))
            if delay_ms:
                time.sleep(delay_ms / 1000)

            payload, default_content_type = _encode_body(response.get("body"))
            status = int(response.get("status", 200))
            headers = dict(response.get("headers", {}))

            _append_request_log(
                request_log,
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "cast_id": cast_id,
                    "scenario": scenario_name,
                    "method": self.command,
                    "path": parsed.path,
                    "query": parsed.query,
                    "request_body_bytes": len(request_body),
                    "response_status": status,
                    "configured_route": configured,
                },
            )

            self.send_response(status)
            if not any(key.lower() == "content-type" for key in headers):
                self.send_header("Content-Type", default_content_type)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("X-Genjutsu-Scenario", scenario_name)
            self.end_headers()

            if self.command != "HEAD":
                self.wfile.write(payload)

        def do_GET(self) -> None:  # noqa: N802
            self._handle()

        def do_POST(self) -> None:  # noqa: N802
            self._handle()

        def do_PUT(self) -> None:  # noqa: N802
            self._handle()

        def do_PATCH(self) -> None:  # noqa: N802
            self._handle()

        def do_DELETE(self) -> None:  # noqa: N802
            self._handle()

        def do_HEAD(self) -> None:  # noqa: N802
            self._handle()

        def do_OPTIONS(self) -> None:  # noqa: N802
            self._handle()

        def log_message(self, format: str, *args: Any) -> None:
            message = format % args
            print(f"[{scenario_name}] {self.address_string()} {message}")

    return GenjutsuHandler


def build_server(
    state: dict[str, Any], host: str, port: int, request_log: str | Path
) -> ThreadingHTTPServer:
    """Create a configured server without starting its event loop."""

    handler = make_handler(state, Path(request_log))
    return ThreadingHTTPServer((host, port), handler)


def serve(
    state: dict[str, Any], host: str, port: int, request_log: str | Path
) -> None:
    """Serve an active reality until interrupted."""

    server = build_server(state, host, port, request_log)
    actual_host, actual_port = server.server_address[:2]
    print(
        f"Genjutsu is casting '{state['scenario']['name']}' at "
        f"http://{actual_host}:{actual_port}"
    )
    print(f"Request evidence: {Path(request_log)}")
    print("Press Ctrl+C to stop the server. The reality remains active until release.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
