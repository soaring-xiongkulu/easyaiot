#!/usr/bin/env python3
"""03 - 自愈能力：坏地址失败 → 死信/失败台账 → 修复规则 → 再推成功。"""

from __future__ import annotations

import sys

import requests

from common import (
    CFG,
    TOPIC_ALERT,
    alert_message,
    api_get,
    api_post,
    api_put,
    apply_args,
    build_parser,
    ensure_e2e_contracts,
    fail,
    find_outbox_by_event,
    log,
    ok,
    produce,
    wait_until,
)


def main() -> int:
    args = build_parser("TRANSFORM 自愈/再推验证").parse_args()
    apply_args(args)
    log("== 03 自愈与再推 ==")

    api_get("/overview")
    ensure_e2e_contracts()

    bad_url = "http://127.0.0.1:18080/mes/alerts-DOES-NOT-EXIST-404"
    good_url = f"{CFG.receiver_url}/mes/alerts"

    # 1) 把 MES 告警规则改到坏地址
    api_put(
        "/contract/contract-mes-alert",
        {
            "id": "contract-mes-alert",
            "partyId": "demo-mes",
            "flowType": "ALERT",
            "channel": "party",
            "endpoint": bad_url,
            "mappingId": "map-identity",
            "enabled": True,
            "headers": {},
        },
    )
    ok(f"已将 MES 推送规则改为坏地址: {bad_url}")

    # 临时关掉 http 全量规则，避免干扰（只测 MES party 失败路径）
    api_put(
        "/contract/contract-http-webhook",
        {
            "id": "contract-http-webhook",
            "partyId": "e2e-http",
            "flowType": None,
            "channel": "http",
            "endpoint": f"{CFG.receiver_url}/webhook/transform",
            "mappingId": "map-identity",
            "enabled": False,
            "headers": {},
        },
    )

    event_id = produce(TOPIC_ALERT, alert_message(alert_id=91001))

    def failed_or_dead():
        rows = find_outbox_by_event(event_id)
        if not rows:
            return None
        # MES party 那条应失败；http 已关闭
        mes = [r for r in rows if r.get("contractId") == "contract-mes-alert"]
        if not mes:
            return None
        st = mes[0].get("status")
        if st in {"FAILED", "DEAD"}:
            return mes[0]
        return None

    bad_row = wait_until(failed_or_dead, timeout=max(args.timeout, 60), interval=2, desc="MES outbox FAILED/DEAD")
    ok(f"坏地址路径已失败 status={bad_row.get('status')} attempts={bad_row.get('attempts')}")

    # 2) 修复规则
    api_put(
        "/contract/contract-mes-alert",
        {
            "id": "contract-mes-alert",
            "partyId": "demo-mes",
            "flowType": "ALERT",
            "channel": "party",
            "endpoint": good_url,
            "mappingId": "map-identity",
            "enabled": True,
            "headers": {},
        },
    )
    ok(f"已修复 MES 推送地址: {good_url}")

    # 3) 再推（优先用 outbox replay；若已进 DLQ 则 dlq replay）
    outbox_id = bad_row.get("id")
    dlq_rows = api_get("/dlq") or []
    related_dlq = [d for d in dlq_rows if d.get("outboxId") == outbox_id or (
        d.get("envelope") or {}
    ).get("eventId") == event_id]

    if related_dlq:
        api_post(f"/dlq/{related_dlq[0]['id']}/replay")
        ok(f"已对失败待办再推 dlqId={related_dlq[0]['id']}")
    else:
        api_post(f"/outbox/{outbox_id}/replay")
        ok(f"已对推送记录再推 outboxId={outbox_id}")

    def delivered_ok():
        try:
            r = requests.get(f"{CFG.receiver_url}/events/{event_id}", timeout=5)
            r.raise_for_status()
            return "party-mes" in (r.json().get("channels") or [])
        except Exception:
            return False

    wait_until(delivered_ok, timeout=args.timeout, desc="修复后再推送达 MES")
    ok(f"自愈成功: eventId={event_id} 已送达 party-mes")

    # 恢复 http 规则
    api_put(
        "/contract/contract-http-webhook",
        {
            "id": "contract-http-webhook",
            "partyId": "e2e-http",
            "flowType": None,
            "channel": "http",
            "endpoint": f"{CFG.receiver_url}/webhook/transform",
            "mappingId": "map-identity",
            "enabled": True,
            "headers": {"partySecret": "e2e-secret"},
        },
    )

    log("03 PASS: 失败→修复→再推 自愈闭环已证明")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"03 FAIL: {e}")
        sys.exit(1)
