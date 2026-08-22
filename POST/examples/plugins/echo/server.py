#!/usr/bin/env python3
"""Minimal POST external plugin Sidecar (echo enrich).

Endpoints:
  GET  /healthz
  POST /v1/process  -> post_plugin_delta.v1
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def _json(self, code: int, body: dict):
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path.split("?", 1)[0] in ("/healthz", "/health"):
            self._json(200, {"ok": True})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path != "/v1/process":
            self._json(404, {"error": "not found"})
            return
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            req = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self._json(400, {"error": "invalid json"})
            return
        params = req.get("params") or {}
        ctx = req.get("context") or {}
        dets = ctx.get("detections") or []
        self._json(200, {
            "schema": "post_plugin_delta.v1",
            "detections": None,
            "enrichment_patch": {
                "echo": True,
                "plugin_id": req.get("plugin_id"),
                "detections_in": len(dets),
                "params": params,
            },
            "layers_append": [],
            "decision": None,
            "drop_reason": "",
            "skip_rest": False,
        })


def main():
    import os
    port = int(os.environ.get("PORT", "8091"))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
