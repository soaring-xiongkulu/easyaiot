#!/usr/bin/env python3
"""模拟 iot-sink：不启动 DEVICE/iot-sink，直接向 sink Kafka Topic 投喂业务消息。

用途：让 TRANSFORM 消费到与真实 sink 同名的 Topic，打通
  消费 → 落盘(Outbox/备份) → 转发(deliver) → 推送(MES/ERP/WMS/Webhook)
从而看见业务价值。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import List, Tuple

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

from common import (
    CFG,
    TOPIC_ALERT,
    TOPIC_DEVICE,
    TOPIC_FACE,
    TOPIC_PLATE,
    TOPIC_POST,
    TOPIC_SNAPSHOT,
    TOPIC_DELIVER,
    TOPIC_DLQ,
    alert_message,
    apply_args,
    build_parser,
    device_message,
    log,
    ok,
    produce,
    vision_message,
)


SINK_TOPICS = [
    TOPIC_DEVICE,
    TOPIC_ALERT,
    TOPIC_SNAPSHOT,
    TOPIC_FACE,
    TOPIC_PLATE,
    TOPIC_POST,
]

INTERNAL_TOPICS = [
    TOPIC_DELIVER,
    TOPIC_DLQ,
    "iot_transform_archive",
    "iot_transform_command",
    "iot_transform_telemetry",
]


def ensure_topics(bootstrap: str, partitions: int = 3) -> None:
    admin = KafkaAdminClient(bootstrap_servers=bootstrap.split(","), client_id="transform-sim-sink")
    try:
        existing = set(admin.list_topics())
        to_create = [
            NewTopic(name=t, num_partitions=partitions, replication_factor=1)
            for t in SINK_TOPICS + INTERNAL_TOPICS
            if t not in existing
        ]
        if not to_create:
            ok(f"Kafka Topic 已就绪 count={len(SINK_TOPICS + INTERNAL_TOPICS)}")
            return
        try:
            admin.create_topics(to_create, validate_only=False)
        except TopicAlreadyExistsError:
            pass
        ok(f"已创建 Topic: {[t.name for t in to_create]}")
    finally:
        admin.close()


def scenario_factory_floor() -> List[Tuple[str, str, dict, str]]:
    """车间场景：温湿度上报 + 入侵告警 + 人脸核验 + 车牌 + 后处理结果。"""
    cases: List[Tuple[str, str, dict, str]] = []

    data = device_message(
        device_id="line-A-temp-01",
        params={"temperature": 42.8, "humidity": 61, "line": "A", "station": "焊机-3"},
    )
    cases.append(
        (
            TOPIC_DEVICE,
            "设备遥测 → ERP",
            data,
            "产线温湿度上报，TRANSFORM 按 DATA 规则推到 ERP 遥测接口",
        )
    )

    alert = alert_message(device_id="cam-gate-01", alert_id=88001)
    alert["alert"]["type"] = "intrusion"
    alert["alert"]["level"] = "HIGH"
    alert["task_name"] = "围栏入侵检测"
    cases.append(
        (
            TOPIC_ALERT,
            "安防告警 → MES + Webhook",
            alert,
            "摄像头告警 fan-out：MES 工单侧 + HTTP Webhook 值班台",
        )
    )

    snap = {
        "id": alert["id"] + "snap",
        "device_id": "cam-gate-01",
        "image_url": "http://127.0.0.1/minio/snap-intrusion.jpg",
        "alert_id": 88001,
        "timestamp": alert["timestamp"],
    }
    cases.append(
        (
            TOPIC_SNAPSHOT,
            "抓拍告警 → 告警流",
            snap,
            "抓拍图地址进入 ALERT 流（可与通知类合同匹配）",
        )
    )

    face = vision_message("face")
    face["device_id"] = "cam-workshop-face"
    face["person_name"] = "张工"
    face["match_score"] = 0.98
    cases.append(
        (
            TOPIC_FACE,
            "人脸核验 → WMS",
            face,
            "视觉 VIDEO_META：人员核验结果推到 WMS",
        )
    )

    plate = vision_message("plate")
    plate["device_id"] = "cam-dock-01"
    plate["plate_no"] = "粤B·D12345"
    plate["match_score"] = 0.95
    cases.append(
        (
            TOPIC_PLATE,
            "车牌识别 → WMS",
            plate,
            "月台车辆识别结果推到 WMS",
        )
    )

    post = {
        "id": __import__("uuid").uuid4().hex,
        "device_id": "cam-qc-01",
        "result": "ng",
        "defect": "scratch",
        "image_url": "http://127.0.0.1/minio/qc-scratch.jpg",
        "video_url": "rtsp://127.0.0.1/live/qc-01",
        "timestamp": alert["timestamp"],
    }
    cases.append(
        (
            TOPIC_POST,
            "质检后处理 → 视觉流",
            post,
            "后处理结果（图/视频地址）进入 VIDEO_META / 相关流",
        )
    )
    return cases


def main() -> int:
    p = build_parser("模拟 iot-sink：向 Kafka sink Topic 投喂（无需启动 iot-sink）")
    p.add_argument("--ensure-topics", action="store_true", default=True, help="自动创建缺失 Topic")
    p.add_argument("--no-ensure-topics", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="只打印将投喂的消息，不发 Kafka")
    p.add_argument("--scenario", default="factory", choices=["factory"])
    p.add_argument("--repeat", type=int, default=1, help="整套场景重复次数")
    p.add_argument("--delay", type=float, default=0.3, help="消息间隔秒")
    args = p.parse_args()
    apply_args(args)

    log("=" * 60)
    log("本脚本 = 虚拟 iot-sink（不启动 DEVICE/iot-sink 模块）")
    log(f"Kafka={CFG.kafka}")
    log("投喂 Topic = 与真实 sink 约定同名，TRANSFORM 可直接消费")
    log("=" * 60)

    if not args.no_ensure_topics:
        ensure_topics(CFG.kafka)

    cases = scenario_factory_floor()
    produced = []
    for r in range(args.repeat):
        if args.repeat > 1:
            log(f"--- round {r + 1}/{args.repeat} ---")
        for topic, title, payload, story in cases:
            if args.repeat > 1:
                # 重复时换新 id，避免 outbox 唯一键吞掉
                payload = dict(payload)
                payload["id"] = __import__("uuid").uuid4().hex
            log(f"场景: {title}")
            log(f"  价值: {story}")
            log(f"  Topic: {topic}")
            if args.dry_run:
                log("  payload: " + json.dumps(payload, ensure_ascii=False)[:200])
                continue
            event_id = produce(topic, payload)
            produced.append({"title": title, "topic": topic, "eventId": event_id, "story": story})
            time.sleep(args.delay)

    print(json.dumps({"produced": produced}, ensure_ascii=False, indent=2))
    ok(f"模拟 sink 投喂完成 count={len(produced)}（TRANSFORM 将消费这些 Topic）")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"FAIL: {e}")
        sys.exit(1)
