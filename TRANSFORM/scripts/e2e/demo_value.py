#!/usr/bin/env python3
"""业务价值演示：无 iot-sink，模拟投喂 → 看 TRANSFORM 消费/落盘/转发/推送结果。

输出一份可读的「价值报告」，便于现场演示。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from common import (
    CFG,
    TOPIC_ALERT,
    TOPIC_DEVICE,
    TOPIC_FACE,
    api_get,
    apply_args,
    alert_message,
    build_parser,
    device_message,
    ensure_e2e_contracts,
    fail,
    find_outbox_by_event,
    log,
    ok,
    produce,
    vision_message,
    wait_until,
)
from simulate_iot_sink import ensure_topics, scenario_factory_floor


def banner(title: str) -> None:
    print("\n" + "═" * 64, flush=True)
    print(f"  {title}", flush=True)
    print("═" * 64, flush=True)


def check_prereq() -> None:
    banner("① 环境检查（无需 iot-sink / DEVICE 业务模块）")
    try:
        ov = api_get("/overview")
        ok(f"transform-runtime 可达 overview={json.dumps(ov, ensure_ascii=False)}")
    except Exception as e:
        fail(
            f"transform-runtime 不可达 ({CFG.base}): {e}\n"
            "请先启动: bash TRANSFORM/scripts/run-runtime.sh"
        )
    try:
        requests.get(f"{CFG.receiver_url}/health", timeout=3).raise_for_status()
        ok(f"外部系统模拟器就绪 {CFG.receiver_url} （扮演 MES/ERP/WMS/Webhook）")
    except Exception as e:
        fail(f"请先启动 mock_receiver.py: {e}")
    ensure_topics(CFG.kafka)
    ensure_e2e_contracts()


def receiver_channels(event_id: str) -> List[str]:
    try:
        r = requests.get(f"{CFG.receiver_url}/events/{event_id}", timeout=5)
        r.raise_for_status()
        return list(r.json().get("channels") or [])
    except Exception:
        return []


def wait_pipeline(event_id: str, want_channels: List[str], timeout: float) -> Dict[str, Any]:
    def _ready():
        rows = find_outbox_by_event(event_id)
        if not rows:
            return None
        chs = receiver_channels(event_id)
        # 至少一条 outbox 进入转发/投递完成态，且期望渠道命中
        status_ok = any(r.get("status") in {"SENT", "DELIVERED", "RELAYING"} for r in rows)
        channel_ok = all(c in chs for c in want_channels)
        if status_ok and channel_ok:
            return {"outbox": rows, "channels": chs}
        return None

    return wait_until(_ready, timeout=timeout, interval=1.0, desc=f"链路完成 event={event_id}")


def list_backup_files(event_id: str) -> List[str]:
    roots = [
        Path(os.getenv("TRANSFORM_BACKUP_DIR", "./data/transform-backup")),
        Path("data/transform-backup"),
        Path("/projects/new/easyaiot/TRANSFORM/data/transform-backup"),
        Path("/projects/new/easyaiot/TRANSFORM/transform-runtime/data/transform-backup"),
        Path.cwd() / "data" / "transform-backup",
    ]
    found: List[str] = []
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob(f"{event_id}.json"):
            found.append(str(p))
    return found


def print_story_result(title: str, story: str, event_id: str, topic: str, result: Dict[str, Any]) -> None:
    print(f"\n▶ {title}", flush=True)
    print(f"  业务价值 : {story}", flush=True)
    print(f"  模拟投喂 : Topic={topic}  eventId={event_id}", flush=True)
    print("  链路结果 :", flush=True)
    for row in result.get("outbox") or []:
        print(
            f"    - 落盘/转发/投递  contract={row.get('contractId')}  "
            f"channel={row.get('channel')}  status={row.get('status')}",
            flush=True,
        )
    chs = result.get("channels") or []
    print(f"  外部系统已收到 : {chs if chs else '(尚未)'}", flush=True)
    backups = list_backup_files(event_id)
    if backups:
        print(f"  本地备份落盘   : {backups[0]}", flush=True)
    else:
        print("  本地备份落盘   : （若 runtime 工作目录不在本机可见路径，请到 TRANSFORM_BACKUP_DIR 查看）", flush=True)


def run_core_stories(timeout: float) -> List[Dict[str, Any]]:
    banner("② 模拟 iot-sink 投喂（直接写 Kafka，代替真实 sink）")
    stories = []

    # 精选 3 条最能体现价值的故事（完整场景可用 simulate_iot_sink.py）
    selected = [
        (
            TOPIC_DEVICE,
            "产线温湿度 → ERP",
            device_message(
                device_id="line-A-temp-01",
                params={"temperature": 42.8, "humidity": 61, "line": "A"},
            ),
            "设备 DATA 流：无需改 ERP，按推送规则自动入 ERP 遥测",
            ["party-erp"],
        ),
        (
            TOPIC_ALERT,
            "围栏入侵告警 → MES + 值班 Webhook",
            alert_message(device_id="cam-gate-01", alert_id=88011),
            "告警 ALERT 流 fan-out：MES 工单 + HTTP Webhook 同时触达",
            ["party-mes", "http-webhook"],
        ),
        (
            TOPIC_FACE,
            "车间人脸核验 → WMS",
            vision_message("face"),
            "视觉 VIDEO_META：核验结果推 WMS，支撑门禁/仓储联动",
            ["party-wms"],
        ),
    ]

    for topic, title, payload, story, want in selected:
        log(f"投喂: {title} -> {topic}")
        event_id = produce(topic, payload)
        result = wait_pipeline(event_id, want, timeout=timeout)
        print_story_result(title, story, event_id, topic, result)
        stories.append(
            {
                "title": title,
                "story": story,
                "topic": topic,
                "eventId": event_id,
                "outbox": result.get("outbox"),
                "channels": result.get("channels"),
            }
        )
    return stories


def print_value_report(stories: List[Dict[str, Any]]) -> None:
    banner("③ 价值报告（你现在看到的能力）")
    overview = api_get("/overview") or {}
    stats = requests.get(f"{CFG.receiver_url}/stats", timeout=5).json()
    workers = api_get("/cluster/workers") or {}

    print(
        """
  没有启动 iot-sink / 设备接入 / 视频算法服务，也能证明：

  1. 【消费】TRANSFORM 订阅与 sink 同名的 Kafka Topic，吃到业务事件
  2. 【落盘】权威任务写入 PostgreSQL Outbox（可查 /transform/outbox）
  3. 【转发】Outbox 中继到内部 Topic iot_transform_deliver
  4. 【推送】按渠道推到 MES / ERP / WMS / HTTP Webhook（本演示用 mock）
  5. 【备份】accept 时本地 JSON 镜像（TRANSFORM_BACKUP_DIR）
  6. 【可扩展】多实例自动加入约定 Group（见 cluster/workers）
""".rstrip(),
        flush=True,
    )

    print("\n  本次故事回放:", flush=True)
    for s in stories:
        chs = ",".join(s.get("channels") or [])
        statuses = ",".join(sorted({r.get("status") for r in (s.get("outbox") or [])}))
        print(f"   • {s['title']}", flush=True)
        print(f"     eventId={s['eventId']}  status=[{statuses}]  外部系统=[{chs}]", flush=True)

    print("\n  运行时概览:", flush=True)
    print(f"   parties={overview.get('parties')} contracts={overview.get('contracts')} "
          f"outbox={overview.get('outbox')} dlq={overview.get('dlq')}", flush=True)
    print(f"   metrics={overview.get('metrics')}", flush=True)
    print(f"   groups={workers.get('groups')}", flush=True)
    print(f"   mock 接收统计={stats.get('counts')}", flush=True)

    print(
        f"""
  下一步可看：
   • 管理 API  : {CFG.base}/transform/outbox
   • mock 统计 : {CFG.receiver_url}/stats
   • 全场景投喂: python simulate_iot_sink.py
   • 扩容自愈  : python 02_horizontal_scale.py / 03_self_heal.py
   • 详细步骤  : TRANSFORM/docs/07-流程测试设计与详细步骤.md
""",
        flush=True,
    )
    ok("业务价值演示完成：消费 / 落盘 / 转发 / 推送 已打通")


def main() -> int:
    p = build_parser("TRANSFORM 业务价值演示（模拟 iot-sink，无需真实模块）")
    p.add_argument("--full-scenario", action="store_true", help="额外跑完整工厂场景投喂")
    args = p.parse_args()
    apply_args(args)

    banner(f"TRANSFORM 价值演示  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(
        "  说明: 本演示用脚本代替 iot-sink，向 Kafka 写入真实 Topic 名的消息；\n"
        "        不依赖 DEVICE / VIDEO / AI 等模块启动。",
        flush=True,
    )

    check_prereq()
    stories = run_core_stories(timeout=args.timeout)

    if args.full_scenario:
        banner("④ 追加完整工厂场景投喂")
        for topic, title, payload, story in scenario_factory_floor():
            eid = produce(topic, payload)
            log(f"{title} eventId={eid}")
            time.sleep(0.2)
        time.sleep(3)
        stats = requests.get(f"{CFG.receiver_url}/stats", timeout=5).json()
        ok(f"全场景投喂后 mock counts={stats.get('counts')}")

    print_value_report(stories)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"DEMO FAIL: {e}")
        sys.exit(1)
