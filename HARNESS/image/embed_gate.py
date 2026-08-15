#!/usr/bin/env python3
"""EasyAIoT HARNESS embed gate.

Only allow top-level document access when embed=idea (or embed=1) is present;
otherwise redirect to the IDEA portal. Embedded iframe / same-origin follow-up
requests are allowed via cookie set on first embed load.
"""
from __future__ import annotations

import http.client
import os
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

UPSTREAM_HOST = os.environ.get("HARNESS_DSH_INTERNAL_HOST", "127.0.0.1")
UPSTREAM_PORT = int(os.environ.get("HARNESS_DSH_INTERNAL_PORT", "3081"))
LISTEN_PORT = int(os.environ.get("HARNESS_LISTEN_PORT", "3080"))
IDEA_URL = (os.environ.get("EASYAIOT_IDEA_URL") or "http://127.0.0.1:9300").rstrip("/")
COOKIE_NAME = "easyaiot_harness_embed"
COOKIE_VAL = "1"
HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def idea_redirect(extra: str = "harness=1") -> str:
    sep = "&" if "?" in IDEA_URL else "?"
    return f"{IDEA_URL}{sep}{extra}"


def has_embed_cookie(cookie_header: str) -> bool:
    if not cookie_header:
        return False
    for part in cookie_header.split(";"):
        k, _, v = part.strip().partition("=")
        if k == COOKIE_NAME and v.strip() == COOKIE_VAL:
            return True
    return False


def is_embed_query(path: str) -> bool:
    q = parse_qs(urlparse(path).query)
    emb = (q.get("embed") or [""])[0].lower()
    return emb in {"idea", "1", "portal", "true", "yes"}


def is_top_level_document(headers) -> bool:
    dest = (headers.get("Sec-Fetch-Dest") or "").lower()
    mode = (headers.get("Sec-Fetch-Mode") or "").lower()
    accept = (headers.get("Accept") or "").lower()
    ua = (headers.get("User-Agent") or "").lower()
    if dest == "iframe":
        return False
    if dest == "document":
        return True
    if mode == "navigate" and "text/html" in accept:
        return True
    # curl / healthcheck / 非浏览器：放行
    if not dest and (
        not ua
        or "curl/" in ua
        or "wget/" in ua
        or "python-requests" in ua
        or "health" in ua
    ):
        return False
    if not dest and not mode and "text/html" in accept and headers.get("Upgrade-Insecure-Requests"):
        return True
    return False


class GateHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        sys_stderr = __import__("sys").stderr
        sys_stderr.write("[harness-gate] " + (fmt % args) + "\n")

    def _deny_standalone(self) -> None:
        loc = idea_redirect()
        body = (
            "<!doctype html><meta charset=utf-8>"
            "<title>请使用 IDEA 门户</title>"
            f"<p>HARNESS 需在 EasyAIoT IDEA 门户中打开。</p>"
            f"<p><a href=\"{loc}\">前往 AI 助手</a></p>"
        ).encode("utf-8")
        self.send_response(302)
        self.send_header("Location", loc)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _should_block(self) -> bool:
        if not is_top_level_document(self.headers):
            return False
        if is_embed_query(self.path):
            return False
        if has_embed_cookie(self.headers.get("Cookie", "")):
            return False
        # Allow healthchecks / non-HTML probes without Accept html
        accept = (self.headers.get("Accept") or "").lower()
        if accept and "text/html" not in accept and "*/*" not in accept:
            return False
        return True

    def _proxy(self, method: str) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length > 0 else None

        headers = {}
        for k, v in self.headers.items():
            if k.lower() in HOP_BY_HOP:
                continue
            headers[k] = v
        # 必须保留浏览器原始 Host（如 172.x:3080），否则 dsh trusted-host / CSRF 会 403
        if "Host" not in headers and "host" not in {k.lower() for k in headers}:
            headers["Host"] = self.headers.get("Host") or f"{UPSTREAM_HOST}:{UPSTREAM_PORT}"
        headers["Connection"] = "close"
        # 避免把绝对 URL 指到错误上游
        headers.pop("Forwarded", None)

        conn = http.client.HTTPConnection(UPSTREAM_HOST, UPSTREAM_PORT, timeout=120)
        try:
            conn.request(method, self.path, body=body, headers=headers)
            resp = conn.getresponse()
            raw = resp.read()

            self.send_response(resp.status)
            set_embed_cookie = is_embed_query(self.path)
            for k, v in resp.getheaders():
                if k.lower() in HOP_BY_HOP:
                    continue
                if k.lower() == "set-cookie" and COOKIE_NAME in v:
                    continue
                self.send_header(k, v)
            if set_embed_cookie:
                self.send_header(
                    "Set-Cookie",
                    f"{COOKIE_NAME}={COOKIE_VAL}; Path=/; SameSite=Lax; Max-Age=86400",
                )
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            if method != "HEAD":
                self.wfile.write(raw)
        except (TimeoutError, socket.error, http.client.HTTPException) as exc:
            msg = f"upstream error: {exc}".encode()
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
        finally:
            conn.close()

    def do_GET(self) -> None:
        if self._should_block():
            self._deny_standalone()
            return
        self._proxy("GET")

    def do_HEAD(self) -> None:
        if self._should_block():
            self._deny_standalone()
            return
        self._proxy("HEAD")

    def do_POST(self) -> None:
        self._proxy("POST")

    def do_PUT(self) -> None:
        self._proxy("PUT")

    def do_PATCH(self) -> None:
        self._proxy("PATCH")

    def do_DELETE(self) -> None:
        self._proxy("DELETE")

    def do_OPTIONS(self) -> None:
        self._proxy("OPTIONS")


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", LISTEN_PORT), GateHandler)
    print(
        f"[harness-gate] 0.0.0.0:{LISTEN_PORT} -> {UPSTREAM_HOST}:{UPSTREAM_PORT} "
        f"(standalone -> {IDEA_URL})",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
