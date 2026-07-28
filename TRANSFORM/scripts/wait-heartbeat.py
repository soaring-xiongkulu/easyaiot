#!/usr/bin/env python3
"""等待 iot_transform_heartbeat 约定 topic，验收 TRANSFORM 实例存活。

端口可变时不以 HTTP 探活为主：看到匹配的心跳即视为部署成功。

用法:
  python3 wait-heartbeat.py --bootstrap 127.0.0.1:9092 --expect 2 --timeout 120
  python3 wait-heartbeat.py --bootstrap ... --instance-id tr-1-xxx --timeout 90
  python3 wait-heartbeat.py --bootstrap ... --node-id node-12 --expect 3
"""
from __future__ import annotations

import argparse
import json
import sys
import time


TOPIC = "iot_transform_heartbeat"


def main() -> int:
    ap = argparse.ArgumentParser(description="Wait for TRANSFORM Kafka heartbeat")
    ap.add_argument("--bootstrap", default="127.0.0.1:9092")
    ap.add_argument("--topic", default=TOPIC)
    ap.add_argument("--expect", type=int, default=1, help="期望不同 instanceId 数量")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--instance-id", default="", help="只等指定实例")
    ap.add_argument("--node-id", default="", help="只统计该 nodeId")
    ap.add_argument("--group", default="", help="消费组；默认临时唯一组")
    args = ap.parse_args()

    try:
        from kafka import KafkaConsumer  # type: ignore
    except ImportError:
        print("ERROR: need kafka-python (pip install kafka-python)", file=sys.stderr)
        return 2

    group = args.group or f"transform.hb.wait.{int(time.time() * 1000)}"
    consumer = KafkaConsumer(
        args.topic,
        bootstrap_servers=args.bootstrap.split(","),
        group_id=group,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        consumer_timeout_ms=2000,
        value_deserializer=lambda b: b.decode("utf-8", errors="replace"),
    )

    seen: set[str] = set()
    deadline = time.time() + args.timeout
    print(
        f"waiting topic={args.topic} bootstrap={args.bootstrap} "
        f"expect={args.expect} timeout={args.timeout}s "
        f"instance={args.instance_id or '*'} node={args.node_id or '*'}",
        flush=True,
    )

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
            status = str(data.get("status") or "")
            if args.instance_id and iid != args.instance_id:
                continue
            if args.node_id and nid != args.node_id:
                continue
            if status and status not in ("ONLINE", "READY", "STARTING", ""):
                continue
            if not iid:
                continue
            if iid not in seen:
                seen.add(iid)
                port = data.get("port")
                print(
                    f"HEARTBEAT ok instance={iid} node={nid} port={port} "
                    f"seen={len(seen)}/{args.expect}",
                    flush=True,
                )
            if args.instance_id and iid == args.instance_id:
                print("READY", flush=True)
                consumer.close()
                return 0
            if len(seen) >= args.expect:
                print("READY", flush=True)
                consumer.close()
                return 0
        time.sleep(0.2)

    print(
        f"TIMEOUT seen={sorted(seen)} expect={args.expect}",
        file=sys.stderr,
        flush=True,
    )
    consumer.close()
    return 1


if __name__ == "__main__":
    sys.exit(main())
