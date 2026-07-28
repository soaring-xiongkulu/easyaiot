#!/usr/bin/env python3
"""步骤 03：心跳验收。

主路径：Kafka iot_transform_heartbeat
兜底：管理 API /transform/cluster/instances（PG 同源，端口可变场景更稳）
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

DIR = Path(__file__).resolve().parent
TOPIC = "iot_transform_heartbeat"
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


def api_instances(api_bases: list[str]) -> list[dict]:
    import requests

    last = ""
    for base in api_bases:
        try:
            r = requests.get(f"{base.rstrip('/')}/transform/cluster/instances", timeout=5)
            r.raise_for_status()
            body = r.json()
            data = body.get("data") if isinstance(body, dict) and "code" in body else body
            if isinstance(body, dict) and body.get("code", 0) not in (0, None):
                last = str(body.get("msg"))
                continue
            if isinstance(data, list):
                return data
        except Exception as e:
            last = str(e)
    if last:
        print(f"  api_probe_warn: {last}", flush=True)
    return []


def main() -> int:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", default=os.getenv("KAFKA_BOOTSTRAP", "127.0.0.1:9092"))
    ap.add_argument("--timeout", type=int, default=int(os.getenv("HEARTBEAT_TIMEOUT", "120")))
    ap.add_argument("--expect", type=int, default=0)
    ap.add_argument("--node-id", default="")
    ap.add_argument("--api", default=os.getenv("TRANSFORM_API", "") or os.getenv("LOCAL_TRANSFORM_API", "http://127.0.0.1:48096"))
    ap.add_argument("--instances-file", default=str(STATE))
    ap.add_argument("--local", action="store_true", help="本机默认模式：不强制 instanceId 清单")
    args = ap.parse_args()

    expected_ids: list[str] = []
    api_bases = [b for b in [args.api] if b]
    if Path(args.instances_file).is_file():
        rows = json.loads(Path(args.instances_file).read_text(encoding="utf-8") or "[]")
        expected_ids = [r["instanceId"] for r in rows if r.get("instanceId")]
        for r in rows:
            port = r.get("port")
            if port:
                api_bases.append(f"http://127.0.0.1:{port}")
    # 去重保序
    seen_b: list[str] = []
    for b in api_bases:
        if b not in seen_b:
            seen_b.append(b)
    api_bases = seen_b

    expect = args.expect or len(expected_ids) or int(os.getenv("PIPELINE_COUNT", "1"))
    if expect < 1:
        print("FAIL expect < 1", file=sys.stderr)
        return 1

    try:
        from kafka import KafkaConsumer
    except ImportError:
        print("FAIL need kafka-python", file=sys.stderr)
        return 2

    group = f"transform.pipeline.test.hb.{int(time.time() * 1000)}"
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=args.bootstrap.split(","),
        group_id=group,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        consumer_timeout_ms=1500,
        value_deserializer=lambda b: b.decode("utf-8", errors="replace"),
    )

    seen: set[str] = set()
    deadline = time.time() + args.timeout
    print(
        f"[03] heartbeat topic={TOPIC} expect={expect} "
        f"ids={expected_ids or ('*' if args.local else '*')} "
        f"node={args.node_id or '*'} api={api_bases}",
        flush=True,
    )

    def matched_enough() -> bool:
        if expected_ids:
            return set(expected_ids).issubset(seen)
        return len(seen) >= expect

    while time.time() < deadline:
        for msg in consumer:
            try:
                data = json.loads(msg.value)
            except Exception:
                continue
            if data.get("kind") and data.get("kind") != "HEARTBEAT":
                continue
            iid = str(data.get("instanceId") or "")
            nid = str(data.get("nodeId") or "")
            if not iid:
                continue
            if expected_ids and iid not in expected_ids:
                continue
            if args.node_id and nid and nid != args.node_id:
                continue
            if iid not in seen:
                seen.add(iid)
                print(
                    f"  HEARTBEAT instance={iid} node={nid} port={data.get('port')} "
                    f"seen={len(seen)}/{expect}",
                    flush=True,
                )
            if matched_enough():
                print("OK heartbeat via Kafka", flush=True)
                consumer.close()
                return 0

        # API 兜底（PG 同源）：端口可变时更稳
        rows = api_instances(api_bases)
        online = []
        for r in rows:
            status = str(r.get("status") or "")
            is_online = bool(r.get("online")) or status in ("ONLINE", "READY")
            if not is_online:
                continue
            iid = str(r.get("instanceId") or "")
            nid = str(r.get("nodeId") or "")
            if expected_ids and iid not in expected_ids:
                continue
            if args.node_id and nid and nid != args.node_id:
                continue
            if iid:
                online.append(iid)
                seen.add(iid)
        if expected_ids and set(expected_ids).issubset(seen):
            print(f"OK heartbeat via API fallback matched={sorted(expected_ids)}", flush=True)
            consumer.close()
            return 0
        if not expected_ids and len(set(online) or seen) >= expect:
            print(f"OK heartbeat via API fallback online={len(set(online) or seen)}", flush=True)
            consumer.close()
            return 0
        time.sleep(1)

    print(f"FAIL TIMEOUT seen={sorted(seen)} expect={expect} ids={expected_ids}", file=sys.stderr)
    consumer.close()
    return 1


if __name__ == "__main__":
    sys.exit(main())
