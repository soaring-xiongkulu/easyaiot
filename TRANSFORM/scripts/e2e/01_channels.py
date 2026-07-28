#!/usr/bin/env python3
"""01 - 多渠道打通：设备数据 / 告警 / 视觉 → Outbox → party/http 推送到 mock 接收端。"""

from __future__ import annotations

import sys

import requests

from common import (
    CFG,
    TOPIC_ALERT,
    TOPIC_DEVICE,
    TOPIC_FACE,
    alert_message,
    api_get,
    apply_args,
    build_parser,
    device_message,
    ensure_e2e_contracts,
    fail,
    find_outbox_by_event,
    log,
    ok,
    produce,
    vision_message,
    wait_outbox_status,
    wait_until,
)


def receiver_has(event_id: str, channel: str | None = None) -> bool:
    try:
        r = requests.get(f"{CFG.receiver_url}/events/{event_id}", timeout=5)
        r.raise_for_status()
        data = r.json()
        chs = data.get("channels") or []
        if not chs:
            return False
        return channel is None or channel in chs
    except Exception:
        return False


def debug_delivery(event_id: str) -> None:
    """打印定位信息，帮助判断是 outbox 未推进还是投递端不可达。"""
    try:
        rows = find_outbox_by_event(event_id)
        log(f"DEBUG outbox[{event_id}] rows={rows}")
    except Exception as e:
        log(f"DEBUG outbox[{event_id}] query failed: {e}")
    try:
        evt = requests.get(f"{CFG.receiver_url}/events/{event_id}", timeout=5).json()
        log(f"DEBUG receiver event[{event_id}]={evt}")
    except Exception as e:
        log(f"DEBUG receiver event[{event_id}] query failed: {e}")
    try:
        stats = requests.get(f"{CFG.receiver_url}/stats", timeout=5).json()
        log(f"DEBUG receiver stats={stats.get('counts')}")
    except Exception as e:
        log(f"DEBUG receiver stats query failed: {e}")


def main() -> int:
    args = build_parser("TRANSFORM 多渠道打通验证").parse_args()
    apply_args(args)
    log("== 01 多渠道打通 ==")
    log(f"api={CFG.base} kafka={CFG.kafka} receiver={CFG.receiver_url}")

    # 健康检查
    ov = api_get("/overview")
    ok(f"transform-server 可达 overview={ov}")
    try:
        requests.get(f"{CFG.receiver_url}/health", timeout=3).raise_for_status()
    except Exception as e:
        fail(f"请先启动 mock_receiver.py ({CFG.receiver_url}): {e}")

    ensure_e2e_contracts()

    # 1) 设备数据 → ERP party
    data_id = produce(TOPIC_DEVICE, device_message())
    wait_outbox_status(data_id, {"SENT", "DELIVERED", "RELAYING"}, timeout=args.timeout)
    try:
        wait_until(lambda: receiver_has(data_id, "party-erp"), timeout=args.timeout, desc="ERP 收到设备数据")
    except Exception:
        debug_delivery(data_id)
        raise
    ok(f"DATA 渠道打通 eventId={data_id} → party-erp")

    # 2) 告警 → MES party + HTTP webhook（全类型规则）
    alert_id = produce(TOPIC_ALERT, alert_message())
    wait_outbox_status(alert_id, {"SENT", "DELIVERED", "RELAYING"}, timeout=args.timeout)
    wait_until(lambda: receiver_has(alert_id, "party-mes"), timeout=args.timeout, desc="MES 收到告警")
    wait_until(lambda: receiver_has(alert_id, "http-webhook"), timeout=args.timeout, desc="HTTP Webhook 收到告警")
    ok(f"ALERT 渠道打通 eventId={alert_id} → party-mes + http-webhook")

    # 3) 视觉 → WMS party
    face_id = produce(TOPIC_FACE, vision_message("face"))
    wait_outbox_status(face_id, {"SENT", "DELIVERED", "RELAYING"}, timeout=args.timeout)
    wait_until(lambda: receiver_has(face_id, "party-wms"), timeout=args.timeout, desc="WMS 收到视觉结果")
    ok(f"VIDEO_META 渠道打通 eventId={face_id} → party-wms")

    stats = requests.get(f"{CFG.receiver_url}/stats", timeout=5).json()
    ok(f"接收端统计 counts={stats.get('counts')}")
    workers = api_get("/cluster/workers")
    ok(f"集群约定 Group={workers.get('groups')}")
    log("01 PASS: kafka/http/party 多渠道已打通")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"01 FAIL: {e}")
        sys.exit(1)
