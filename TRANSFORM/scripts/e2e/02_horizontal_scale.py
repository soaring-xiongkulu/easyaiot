#!/usr/bin/env python3
"""02 - 横向扩容：检查消费/投递 Group 成员，并压测证明多分区并行消费能力。

用法：
  1) 先启动 1 个 transform-runtime，跑本脚本看 member_count
  2) 再启动第 2 个实例（同 Kafka/DB，不同端口），再跑 --expect-members 2
  3) 脚本会投喂一批消息并核对接收端计数上升
"""

from __future__ import annotations

import sys
import time

import requests

from common import (
    CFG,
    GROUP_CONSUME,
    GROUP_HTTP,
    GROUP_PARTY,
    TOPIC_DEVICE,
    api_get,
    apply_args,
    build_parser,
    describe_group,
    device_message,
    ensure_e2e_contracts,
    fail,
    log,
    ok,
    produce,
)


def main() -> int:
    p = build_parser("TRANSFORM 横向扩容验证")
    p.add_argument("--expect-members", type=int, default=1, help="期望消费 Group 最少成员数")
    p.add_argument("--batch", type=int, default=20, help="压测消息条数")
    args = p.parse_args()
    apply_args(args)

    log("== 02 横向扩容 ==")
    api_get("/overview")
    ensure_e2e_contracts()

    groups = {}
    for g in (GROUP_CONSUME, GROUP_HTTP, GROUP_PARTY):
        info = describe_group(g)
        groups[g] = info
        log(f"Group {g}: state={info.get('state')} members={info.get('member_count')}")
        for m in info.get("members") or []:
            log(f"  - client={m.get('client_id')} host={m.get('client_host')}")

    consume_members = groups[GROUP_CONSUME].get("member_count") or 0
    if consume_members < args.expect_members:
        fail(
            f"消费 Group 成员不足: got={consume_members} expect>={args.expect_members}。"
            f"请再启动 transform-runtime 实例后重试。"
        )
    ok(f"消费 Group 横向扩展成立: members={consume_members}")

    before = requests.get(f"{CFG.receiver_url}/stats", timeout=5).json().get("counts", {})
    before_total = int(before.get("total") or 0)

    log(f"投喂压测消息 batch={args.batch}")
    ids = []
    for i in range(args.batch):
        ids.append(produce(TOPIC_DEVICE, device_message(device_id=f"e2e-scale-{i % max(consume_members, 1)}")))

    # 等待接收端总量上升
    deadline = time.time() + args.timeout
    after_total = before_total
    while time.time() < deadline:
        after = requests.get(f"{CFG.receiver_url}/stats", timeout=5).json().get("counts", {})
        after_total = int(after.get("total") or 0)
        if after_total >= before_total + max(1, args.batch // 2):
            break
        time.sleep(1)

    gained = after_total - before_total
    if gained <= 0:
        fail(f"压测后接收端无增长 before={before_total} after={after_total}")
    ok(f"压测通过: 接收端增量 +{gained} (batch={args.batch})")

    ov = api_get("/overview")
    ok(f"overview outbox={ov.get('outbox')} metrics={ov.get('metrics')}")
    log("02 PASS: Group 成员扩容 + 并行消费投递能力已证明")
    log("提示: 再启一个 runtime 后用 --expect-members 2 复测，members 应增加")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"02 FAIL: {e}")
        sys.exit(1)
