#!/usr/bin/env python3
"""步骤 04：集群 API 验收 + 下行 PING。"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, List

DIR = Path(__file__).resolve().parent
STATE = DIR / ".state" / "instances.json"


def load_dotenv() -> None:
    env = DIR / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def http_get(url: str, timeout: float) -> Any:
    import requests

    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    body = r.json()
    if isinstance(body, dict) and "code" in body:
        if body.get("code") != 0:
            raise RuntimeError(f"API {url} code={body.get('code')} msg={body.get('msg')}")
        return body.get("data")
    return body


def http_post(url: str, data: dict, timeout: float) -> Any:
    import requests

    r = requests.post(url, json=data, timeout=timeout)
    r.raise_for_status()
    body = r.json()
    if isinstance(body, dict) and "code" in body:
        if body.get("code") != 0:
            raise RuntimeError(f"API POST {url} code={body.get('code')} msg={body.get('msg')}")
        return body.get("data")
    return body


def is_online(row: dict) -> bool:
    if row.get("online") is True:
        return True
    return str(row.get("status") or "") in ("ONLINE", "READY")


def main() -> int:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=os.getenv("TRANSFORM_API", "") or os.getenv("LOCAL_TRANSFORM_API", "http://127.0.0.1:48096"))
    ap.add_argument("--expect-online", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--instances-file", default=str(STATE))
    ap.add_argument("--node-id", default="")
    ap.add_argument("--local", action="store_true")
    args = ap.parse_args()

    try:
        import requests  # noqa: F401
    except ImportError:
        print("FAIL need requests", file=sys.stderr)
        return 2

    instances_meta: List[dict] = []
    if Path(args.instances_file).is_file():
        instances_meta = json.loads(Path(args.instances_file).read_text(encoding="utf-8") or "[]")

    expect = args.expect_online or len([r for r in instances_meta if r.get("instanceId")]) or int(
        os.getenv("PIPELINE_COUNT", "1")
    )
    expected_ids = {r["instanceId"] for r in instances_meta if r.get("instanceId")}

    bases: List[str] = []
    if args.api:
        bases.append(args.api.rstrip("/"))
    for row in instances_meta:
        port = row.get("port")
        if port:
            bases.append(f"http://127.0.0.1:{port}")
    # local 默认也加一下，PG 同源时可从本机总览看到旁路实例
    local_api = os.getenv("LOCAL_TRANSFORM_API", "http://127.0.0.1:48096").rstrip("/")
    if local_api not in bases:
        bases.append(local_api)
    uniq: List[str] = []
    for b in bases:
        if b not in uniq:
            uniq.append(b)
    bases = uniq

    timeout_http = float(os.getenv("HTTP_TIMEOUT", "10"))
    print(f"[04] cluster API expect_online>={expect} bases={bases} local={args.local}", flush=True)
    deadline = time.time() + args.timeout
    last_err = ""

    while time.time() < deadline:
        for base in bases:
            try:
                data = http_get(f"{base}/transform/cluster/instances", timeout_http) or []
                if not isinstance(data, list):
                    continue
                all_online = [r for r in data if is_online(r)]
                if expected_ids:
                    matched = {r.get("instanceId") for r in data if r.get("instanceId") in expected_ids}
                    online_matched = [r for r in all_online if r.get("instanceId") in expected_ids]
                    if expected_ids.issubset(matched) and len(online_matched) >= min(expect, len(expected_ids)):
                        print(f"OK instances via {base}: online_matched={len(online_matched)} total_online={len(all_online)}", flush=True)
                        for r in data:
                            if r.get("instanceId") in expected_ids:
                                print(
                                    f"  - {r.get('instanceId')} status={r.get('status')} online={r.get('online')} "
                                    f"host={r.get('host')} node={r.get('nodeId')}",
                                    flush=True,
                                )
                        cmd = {
                            "commandId": uuid.uuid4().hex,
                            "type": "PING",
                            "targetInstanceId": "*",
                            "targetNodeId": args.node_id or "",
                            "payload": {},
                            "issuedAt": int(time.time() * 1000),
                        }
                        resp = http_post(f"{base}/transform/cluster/command", cmd, timeout_http)
                        print(f"OK PING issued commandId={resp.get('commandId') if isinstance(resp, dict) else resp}", flush=True)
                        overview = http_get(f"{base}/transform/overview", timeout_http) or {}
                        print(
                            f"OK overview onlineInstances={overview.get('onlineInstances')} instances={overview.get('instances')}",
                            flush=True,
                        )
                        return 0
                else:
                    # local / 无清单：只要总览有足够 ONLINE
                    filtered = all_online
                    if args.node_id:
                        filtered = [r for r in all_online if str(r.get("nodeId") or "") in ("", args.node_id)]
                    if len(filtered) >= expect or (args.local and len(all_online) >= 1):
                        print(
                            f"OK online via {base}: matched={len(filtered)} total_online={len(all_online)}",
                            flush=True,
                        )
                        for r in all_online[:10]:
                            print(
                                f"  - {r.get('instanceId')} status={r.get('status')} node={r.get('nodeId')}",
                                flush=True,
                            )
                        cmd = {
                            "commandId": uuid.uuid4().hex,
                            "type": "PING",
                            "targetInstanceId": "*",
                            "issuedAt": int(time.time() * 1000),
                        }
                        resp = http_post(f"{base}/transform/cluster/command", cmd, timeout_http)
                        print(f"OK PING issued commandId={resp.get('commandId') if isinstance(resp, dict) else resp}", flush=True)
                        return 0
            except Exception as e:
                last_err = str(e)
        time.sleep(2)

    print(f"FAIL cluster API timeout last_err={last_err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
