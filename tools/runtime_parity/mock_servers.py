"""In-process mock heartbeat / alert-hook servers for cpp sampling."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional


class _CaptureState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.heartbeats: List[Dict[str, Any]] = []
        self.hooks: List[Dict[str, Any]] = []


def _make_handler(state: _CaptureState, path_prefix: str, kind: str):
    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            pass

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length) if length else b""
            body_text = raw.decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body_text) if body_text.strip() else {}
            except json.JSONDecodeError:
                parsed = {"_raw": body_text}

            record = {
                "received_at_unix": time.time(),
                "path": self.path,
                "body": parsed,
            }
            with state.lock:
                if kind == "heartbeat":
                    state.heartbeats.append(record)
                else:
                    state.hooks.append(record)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

    return _Handler


class MockServers:
    """Threaded HTTP servers for RUNTIME heartbeat + alert hook sampling."""

    def __init__(self) -> None:
        self._state = _CaptureState()
        self._heartbeat_srv: Optional[HTTPServer] = None
        self._hook_srv: Optional[HTTPServer] = None
        self._threads: List[threading.Thread] = []
        self.heartbeat_port: int = 0
        self.hook_port: int = 0

    def start(self, *, heartbeat: bool = True, hook: bool = False) -> None:
        if heartbeat:
            srv = HTTPServer(("127.0.0.1", 0), _make_handler(self._state, "/video/algorithm/heartbeat", "heartbeat"))
            self.heartbeat_port = srv.server_address[1]
            t = threading.Thread(target=srv.serve_forever, daemon=True)
            t.start()
            self._heartbeat_srv = srv
            self._threads.append(t)

        if hook:
            srv = HTTPServer(("127.0.0.1", 0), _make_handler(self._state, "/alert", "hook"))
            self.hook_port = srv.server_address[1]
            t = threading.Thread(target=srv.serve_forever, daemon=True)
            t.start()
            self._hook_srv = srv
            self._threads.append(t)

    def stop(self) -> None:
        if self._heartbeat_srv:
            self._heartbeat_srv.shutdown()
            self._heartbeat_srv = None
        if self._hook_srv:
            self._hook_srv.shutdown()
            self._hook_srv = None

    @property
    def heartbeats(self) -> List[Dict[str, Any]]:
        with self._state.lock:
            return list(self._state.heartbeats)

    @property
    def hooks(self) -> List[Dict[str, Any]]:
        with self._state.lock:
            return list(self._state.hooks)

    def heartbeat_url(self) -> str:
        return f"http://127.0.0.1:{self.heartbeat_port}/video/algorithm/heartbeat/realtime"

    def hook_url(self) -> str:
        return f"http://127.0.0.1:{self.hook_port}/alert"
