#!/usr/bin/env python3
"""模拟外部系统接收端：MES / ERP / WMS / HTTP Webhook。

默认监听 18080，与种子合同 endpoint 对齐。
GET /stats 查看各渠道收到条数；GET /events 查看最近事件。
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Deque, Dict, List
from urllib.parse import urlparse


class Store:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.counts: Dict[str, int] = defaultdict(int)
        self.events: Deque[dict] = deque(maxlen=500)
        self.by_event_id: Dict[str, List[str]] = defaultdict(list)

    def add(self, channel: str, path: str, headers: dict, body: dict) -> None:
        with self.lock:
            self.counts[channel] += 1
            self.counts["total"] += 1
            event_id = (
                headers.get("X-Transform-Event-Id")
                or body.get("eventId")
                or (body.get("id") if isinstance(body.get("id"), str) else None)
                or ""
            )
            if event_id:
                self.by_event_id[event_id].append(channel)
            self.events.appendleft(
                {
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "channel": channel,
                    "path": path,
                    "eventId": event_id,
                    "signature": headers.get("X-Transform-Signature", ""),
                    "bodyKeys": sorted(list(body.keys()))[:20],
                }
            )

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "counts": dict(self.counts),
                "recent": list(self.events)[:30],
                "eventIndexSize": len(self.by_event_id),
            }

    def has_event(self, event_id: str, channel: str | None = None) -> bool:
        with self.lock:
            chs = self.by_event_id.get(event_id) or []
            if not chs:
                return False
            if channel is None:
                return True
            return channel in chs


STORE = Store()


def classify(path: str) -> str:
    if path.startswith("/mes/"):
        return "party-mes"
    if path.startswith("/erp/"):
        return "party-erp"
    if path.startswith("/wms/"):
        return "party-wms"
    if path.startswith("/webhook/"):
        return "http-webhook"
    return "other"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:  # quieter
        pass

    def _json(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._json(200, {"ok": True})
            return
        if path == "/stats":
            self._json(200, STORE.snapshot())
            return
        if path.startswith("/events/"):
            event_id = path.split("/events/", 1)[1]
            with STORE.lock:
                channels = list(STORE.by_event_id.get(event_id) or [])
            self._json(200, {"eventId": event_id, "channels": channels})
            return
        self._json(404, {"error": "not found"})

    ALLOWED = {
        "/mes/alerts",
        "/erp/telemetry",
        "/wms/vision",
        "/webhook/transform",
    }

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            body = {"raw": raw.decode("utf-8", errors="ignore")}
        headers = {k: v for k, v in self.headers.items()}
        if path not in self.ALLOWED:
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] REJECT path={path} "
                f"eventId={headers.get('X-Transform-Event-Id', '')}",
                flush=True,
            )
            self._json(404, {"accepted": False, "error": "unknown endpoint", "path": path})
            return
        channel = classify(path)
        STORE.add(channel, path, headers, body if isinstance(body, dict) else {"payload": body})
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] recv {channel} path={path} "
            f"eventId={headers.get('X-Transform-Event-Id', '')}",
            flush=True,
        )
        self._json(200, {"accepted": True, "channel": channel})


def main() -> None:
    ap = argparse.ArgumentParser(description="TRANSFORM e2e mock receiver")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=18080)
    args = ap.parse_args()
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"mock receiver listening on http://{args.host}:{args.port}", flush=True)
    print("endpoints: /mes/alerts /erp/telemetry /wms/vision /webhook/transform /stats", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("bye", flush=True)


if __name__ == "__main__":
    main()
