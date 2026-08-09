#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock alert hook for runtime-parity testbed.

Records POST body, timestamp, and selected headers to:
  testdata/runtime-parity/golden/video/<case_id>/hook_<n>.json

Usage:
  python docs/runtime-parity/testbed/mock_alert_hook.py --port 18080 --case rt_p0_alert_hook_roi
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


def _resolve_golden_dir(case_id: str) -> Path:
    """Resolve output dir under candidate or oracle root."""
    for env_name in ("ACME_CANDIDATE_ROOT", "ACME_ORACLE_ROOT"):
        root = os.environ.get(env_name, "").strip()
        if root:
            base = Path(root).resolve()
            out = base / "testdata" / "runtime-parity" / "golden" / "video" / case_id
            out.mkdir(parents=True, exist_ok=True)
            return out
  # fallback: cwd-relative
    out = Path.cwd() / "testdata" / "runtime-parity" / "golden" / "video" / case_id
    out.mkdir(parents=True, exist_ok=True)
    return out


class _HookState:
    counter: int = 0
    case_id: str = ""
    out_dir: Optional[Path] = None


def _make_handler(state: _HookState):
    class AlertHookHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            sys.stderr.write(f"[mock_alert_hook] {self.address_string()} - {fmt % args}\n")

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length) if length else b""
            body_text = raw.decode("utf-8", errors="replace")

            parsed_body: object
            try:
                parsed_body = json.loads(body_text) if body_text.strip() else {}
            except json.JSONDecodeError:
                parsed_body = {"_raw": body_text}

            state.counter += 1
            record = {
                "seq": state.counter,
                "case_id": state.case_id,
                "received_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
                "received_at_unix": time.time(),
                "path": self.path,
                "headers": {
                    k: v
                    for k, v in self.headers.items()
                    if k.lower() in ("content-type", "x-request-id", "user-agent")
                },
                "body": parsed_body,
            }

            assert state.out_dir is not None
            out_file = state.out_dir / f"hook_{state.counter:04d}.json"
            out_file.write_text(
                json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            self.log_message("saved %s (%d bytes)", out_file, len(raw))

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"ok": True, "seq": state.counter}).encode("utf-8")
            )

        def do_GET(self) -> None:  # noqa: N802
            if urlparse(self.path).path.rstrip("/") in ("/health", "/healthz", ""):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                payload = {
                    "ok": True,
                    "service": "mock_alert_hook",
                    "case_id": state.case_id,
                    "records": state.counter,
                }
                self.wfile.write(json.dumps(payload).encode("utf-8"))
                return
            self.send_response(404)
            self.end_headers()

    return AlertHookHandler


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Mock alert hook for runtime-parity")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=18080, help="Bind port")
    parser.add_argument(
        "--case",
        required=True,
        help="Case id; writes to golden/video/<case>/",
    )
    args = parser.parse_args(argv)

    state = _HookState()
    state.case_id = args.case
    state.out_dir = _resolve_golden_dir(args.case)

    handler = _make_handler(state)
    server = HTTPServer((args.host, args.port), handler)
    print(
        f"mock_alert_hook: case={args.case} listen={args.host}:{args.port} "
        f"out={state.out_dir}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nmock_alert_hook: stopped", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
