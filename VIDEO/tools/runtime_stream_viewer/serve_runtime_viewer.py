#!/usr/bin/env python3
"""
启动 RUNTIME 原画/AI 并排预览页，并可选探测 SRS HTTP-FLV 流是否在推。

用法示例：
  python3 tools/runtime_stream_viewer/serve_runtime_viewer.py \\
    --device-id 1786351452026243807 --host 172.16.13.220:8080

  # 仅探测流，不启 HTTP
  python3 tools/runtime_stream_viewer/serve_runtime_viewer.py --probe-only \\
    --device-id 1786351452026243807 --host 172.16.13.220:8080
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import quote, urlencode


HERE = Path(__file__).resolve().parent
DEFAULT_HOST = os.getenv("SRS_HTTP_HOST", "127.0.0.1:8080")
DEFAULT_DEVICE = os.getenv("RUNTIME_VIEWER_DEVICE_ID", "")
DEFAULT_PORT = int(os.getenv("RUNTIME_VIEWER_PORT", "8899") or "8899")
DEFAULT_BIND = os.getenv("RUNTIME_VIEWER_BIND", "0.0.0.0")


def _normalize_host(host: str) -> str:
    h = (host or "").strip()
    h = h.replace("http://", "").replace("https://", "").rstrip("/")
    return h


def flv_url(host: str, app: str, device_id: str) -> str:
    return f"http://{_normalize_host(host)}/{app.strip('/')}/{device_id}.flv"


def probe_flv(url: str, timeout: float = 3.0) -> Tuple[bool, str]:
    """HEAD/GET 探测 HTTP-FLV；SRS 对 FLV 常返回 200 + video/x-flv。"""
    req = urllib.request.Request(url, method="GET", headers={"Range": "bytes=0-0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = resp.headers.get("Content-Type", "")
            code = getattr(resp, "status", None) or resp.getcode()
            # 读一点确认有数据
            chunk = resp.read(16)
            ok = 200 <= int(code) < 300 and (b"" != chunk or "flv" in ctype.lower())
            detail = f"HTTP {code} Content-Type={ctype} bytes={len(chunk)}"
            return ok, detail
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def probe_srs_api(api_base: str, device_id: str, timeout: float = 3.0) -> None:
    """打印 SRS /api/v1/streams 中匹配 device_id 的流。"""
    url = api_base.rstrip("/") + "/api/v1/streams/"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"[SRS API] 不可用 {url}: {e}")
        return

    streams = data.get("streams") or []
    matched = [s for s in streams if device_id in str(s.get("name") or "")]
    if not matched:
        print(f"[SRS API] 未找到含 {device_id} 的流（共 {len(streams)} 路）")
        return
    print(f"[SRS API] 匹配 {len(matched)} 路:")
    for s in matched:
        pub = s.get("publish") or {}
        kbps = (s.get("kbps") or {}).get("recv_30s")
        print(
            f"  app={s.get('app')} name={s.get('name')} "
            f"active={pub.get('active')} kbps={kbps}"
        )


def build_viewer_url(listen_host: str, listen_port: int, args: argparse.Namespace) -> str:
    q = {
        "host": _normalize_host(args.host),
        "device_id": args.device_id,
        "live_app": args.live_app,
        "ai_app": args.ai_app,
    }
    return f"http://{listen_host}:{listen_port}/index.html?{urlencode(q)}"


def pick_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        if self.path.endswith(".html") or self.path.startswith("/?"):
            super().log_message(fmt, *args)

    def end_headers(self) -> None:
        # 避免浏览器缓存旧 HTML
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def run_probe(args: argparse.Namespace) -> int:
    host = _normalize_host(args.host)
    device_id = args.device_id
    if not device_id:
        print("错误: 请指定 --device-id", file=sys.stderr)
        return 2

    live = flv_url(host, args.live_app, device_id)
    ai = flv_url(host, args.ai_app, device_id)
    print("=" * 60)
    print("RUNTIME 流探测")
    print("=" * 60)
    print(f"device_id : {device_id}")
    print(f"SRS HTTP  : {host}")
    print(f"原画 FLV  : {live}")
    print(f"AI FLV    : {ai}")
    print("-" * 60)

    ok_live, detail_live = probe_flv(live, timeout=args.timeout)
    ok_ai, detail_ai = probe_flv(ai, timeout=args.timeout)
    print(f"live : {'OK' if ok_live else 'FAIL'}  ({detail_live})")
    print(f"ai   : {'OK' if ok_ai else 'FAIL'}  ({detail_ai})")

    if args.srs_api:
        print("-" * 60)
        probe_srs_api(args.srs_api, device_id, timeout=args.timeout)

    print("=" * 60)
    if ok_live and ok_ai:
        print("结果: 原画与 AI 均可达")
        return 0
    if ok_live or ok_ai:
        print("结果: 部分可达（请检查推流转发 / 算法任务是否都在跑）")
        return 1
    print("结果: 均不可达（检查 SRS、任务、device_id）")
    return 1


def run_server(args: argparse.Namespace) -> int:
    if not HERE.joinpath("index.html").is_file():
        print(f"错误: 找不到 {HERE / 'index.html'}", file=sys.stderr)
        return 2

    # 先探测（不阻塞启动）
    if args.device_id and not args.no_probe:
        code = run_probe(args)
        if code == 2:
            return code
        print()

    handler = partial(QuietHandler, directory=str(HERE))
    try:
        httpd = ThreadingHTTPServer((args.bind, args.port), handler)
    except OSError as e:
        print(f"错误: 无法监听 {args.bind}:{args.port}: {e}", file=sys.stderr)
        return 2

    lan = pick_lan_ip()
    local_url = build_viewer_url("127.0.0.1", args.port, args)
    lan_url = build_viewer_url(lan, args.port, args)

    print("=" * 60)
    print("RUNTIME 预览页已启动")
    print("=" * 60)
    print(f"目录     : {HERE}")
    print(f"监听     : {args.bind}:{args.port}")
    print(f"本机打开 : {local_url}")
    print(f"局域网   : {lan_url}")
    if not args.device_id:
        print("提示     : 未指定 --device-id，可在页面表单里填写后点「应用并播放」")
    print("按 Ctrl+C 停止")
    print("=" * 60)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        httpd.server_close()
    return 0


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="启动 RUNTIME 原画/AI 并排预览页，并探测 SRS HTTP-FLV",
    )
    p.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"SRS HTTP-FLV 主机:端口（默认 {DEFAULT_HOST}，可用 SRS_HTTP_HOST）",
    )
    p.add_argument(
        "--device-id",
        default=DEFAULT_DEVICE,
        help="设备 ID（可用 RUNTIME_VIEWER_DEVICE_ID）",
    )
    p.add_argument("--live-app", default="live", help="原画 SRS app，默认 live")
    p.add_argument("--ai-app", default="ai", help="AI SRS app，默认 ai")
    p.add_argument(
        "--bind",
        default=DEFAULT_BIND,
        help=f"HTTP 监听地址，默认 {DEFAULT_BIND}",
    )
    p.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"HTTP 端口，默认 {DEFAULT_PORT}",
    )
    p.add_argument(
        "--srs-api",
        default=os.getenv("SRS_API", "http://127.0.0.1:1985"),
        help="SRS HTTP API（默认 http://127.0.0.1:1985）",
    )
    p.add_argument("--timeout", type=float, default=3.0, help="探测超时秒数")
    p.add_argument("--probe-only", action="store_true", help="仅探测流，不启 HTTP")
    p.add_argument("--no-probe", action="store_true", help="启服务前不做探测")
    return p.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    args = parse_args(argv)
    if args.probe_only:
        return run_probe(args)
    return run_server(args)


if __name__ == "__main__":
    sys.exit(main())
