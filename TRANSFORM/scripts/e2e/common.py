#!/usr/bin/env python3
"""TRANSFORM e2e 公共工具：配置、Kafka 投喂、管理 API、断言。"""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError as e:  # pragma: no cover
    raise SystemExit("缺少依赖: pip install -r requirements.txt\n" + str(e)) from e

try:
    from kafka import KafkaAdminClient, KafkaProducer
except ImportError as e:  # pragma: no cover
    raise SystemExit("缺少依赖: pip install -r requirements.txt\n" + str(e)) from e


ROOT = Path(__file__).resolve().parent


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv(ROOT / ".env")


@dataclass
class Cfg:
    kafka: str = os.getenv("KAFKA_BOOTSTRAP", "127.0.0.1:9092")
    api_base: str = os.getenv("TRANSFORM_API", "http://127.0.0.1:48096")
    gateway_api: str = os.getenv("GATEWAY_API", "http://127.0.0.1:48080/admin-api")
    use_gateway: bool = os.getenv("USE_GATEWAY", "0") == "1"
    receiver_host: str = os.getenv("RECEIVER_HOST", "127.0.0.1")
    receiver_port: int = int(os.getenv("RECEIVER_PORT", "18080"))
    timeout: float = float(os.getenv("HTTP_TIMEOUT", "10"))

    @property
    def base(self) -> str:
        return self.gateway_api.rstrip("/") if self.use_gateway else self.api_base.rstrip("/")

    @property
    def receiver_url(self) -> str:
        return f"http://{self.receiver_host}:{self.receiver_port}"


CFG = Cfg()

TOPIC_DEVICE = "iot_device_message"
TOPIC_ALERT = "iot-alert-notification"
TOPIC_SNAPSHOT = "iot-snapshot-alert"
TOPIC_FACE = "iot-face-matching"
TOPIC_PLATE = "iot-plate-matching"
TOPIC_POST = "iot-post-process-result"
TOPIC_DELIVER = "iot_transform_deliver"
TOPIC_DLQ = "iot_transform_dlq"
TOPIC_COMMAND = "iot_transform_command"
TOPIC_TELEMETRY = "iot_transform_telemetry"

GROUP_CONSUME = "transform.kafka.consume.device"
GROUP_HTTP = "transform.http.deliver"
GROUP_PARTY = "transform.party.deliver"


def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def ok(msg: str) -> None:
    log(f"OK {msg}")


def fail(msg: str) -> None:
    log(f"FAIL {msg}")
    raise AssertionError(msg)


def api_url(path: str) -> str:
    p = path if path.startswith("/") else f"/{path}"
    return f"{CFG.base}/transform{p}"


def api_get(path: str) -> Any:
    r = requests.get(api_url(path), timeout=CFG.timeout)
    r.raise_for_status()
    body = r.json()
    if isinstance(body, dict) and "code" in body:
        if body.get("code") != 0:
            fail(f"API {path} code={body.get('code')} msg={body.get('msg')}")
        return body.get("data")
    return body


def api_post(path: str, data: Optional[dict] = None, params: Optional[dict] = None) -> Any:
    r = requests.post(api_url(path), json=data or {}, params=params, timeout=CFG.timeout)
    r.raise_for_status()
    body = r.json()
    if isinstance(body, dict) and "code" in body:
        if body.get("code") != 0:
            fail(f"API POST {path} code={body.get('code')} msg={body.get('msg')}")
        return body.get("data")
    return body


def api_put(path: str, data: dict) -> Any:
    r = requests.put(api_url(path), json=data, timeout=CFG.timeout)
    r.raise_for_status()
    body = r.json()
    if isinstance(body, dict) and "code" in body:
        if body.get("code") != 0:
            fail(f"API PUT {path} code={body.get('code')} msg={body.get('msg')}")
        return body.get("data")
    return body


def kafka_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=CFG.kafka.split(","),
        key_serializer=lambda k: (k or "").encode("utf-8"),
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        acks="all",
        retries=3,
    )


def produce(topic: str, payload: dict, key: Optional[str] = None) -> str:
    event_id = payload.get("id") or str(uuid.uuid4()).replace("-", "")
    payload.setdefault("id", event_id)
    p = kafka_producer()
    try:
        fut = p.send(topic, key=key or event_id, value=payload)
        meta = fut.get(timeout=15)
        log(f"Kafka -> {topic} partition={meta.partition} offset={meta.offset} id={event_id}")
        return event_id
    finally:
        p.flush()
        p.close()


def device_message(
    *,
    device_id: str = "e2e-device-001",
    method: str = "thing.property.post",
    params: Optional[dict] = None,
) -> dict:
    return {
        "id": uuid.uuid4().hex,
        "reportTime": datetime.now(timezone.utc).isoformat(),
        "deviceId": device_id,
        "tenantId": 1,
        "serverId": "e2e-script",
        "method": method,
        "params": params or {"temperature": 36.5, "humidity": 55},
        "topic": f"/iot/e2e_product/{device_id}/property/upstream/report",
        "needReply": False,
    }


def alert_message(*, device_id: str = "e2e-cam-001", alert_id: int = 90001) -> dict:
    return {
        "id": uuid.uuid4().hex,
        "alert_id": alert_id,
        "task_id": 1,
        "task_name": "e2e-alert-task",
        "device_id": device_id,
        "device_name": "E2E Camera",
        "alert": {
            "level": "HIGH",
            "type": "intrusion",
            "imageUrl": "http://127.0.0.1/minio/e2e-snap.jpg",
            "videoUrl": "rtsp://127.0.0.1/live/e2e",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "shouldNotify": True,
    }


def vision_message(kind: str = "face") -> dict:
    return {
        "id": uuid.uuid4().hex,
        "device_id": "e2e-cam-vision",
        "match_score": 0.97,
        "image_url": f"http://127.0.0.1/minio/e2e-{kind}.jpg",
        "kind": kind,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def wait_until(predicate, timeout: float = 30.0, interval: float = 1.0, desc: str = "condition") -> Any:
    deadline = time.time() + timeout
    last = None
    last_log_at = 0.0
    while time.time() < deadline:
        last = predicate()
        if last:
            return last
        now = time.time()
        # 长等待时输出进度，避免误判“卡住”
        if now - last_log_at >= 5.0:
            left = max(0.0, deadline - now)
            log(f"等待中: {desc} (剩余 {left:.0f}s, last={last})")
            last_log_at = now
        time.sleep(interval)
    fail(f"超时等待: {desc} (last={last})")


def find_outbox_by_event(event_id: str) -> List[dict]:
    rows = api_get("/outbox") or []
    return [r for r in rows if r.get("eventId") == event_id]


def wait_outbox_status(event_id: str, statuses: set, timeout: float = 45.0) -> List[dict]:
    def _check():
        rows = find_outbox_by_event(event_id)
        if not rows:
            return None
        if all(r.get("status") in statuses for r in rows):
            return rows
        return None

    return wait_until(_check, timeout=timeout, desc=f"outbox[{event_id}] in {statuses}")


def describe_group(group_id: str) -> Dict[str, Any]:
    admin = KafkaAdminClient(bootstrap_servers=CFG.kafka.split(","), client_id="transform-e2e")
    try:
        desc = admin.describe_consumer_groups([group_id])
        info = desc[0] if desc else None
        members = []
        state = ""
        if info is None:
            return {"group": group_id, "members": [], "member_count": 0, "state": ""}
        if hasattr(info, "members"):
            for m in info.members or []:
                members.append(
                    {
                        "member_id": getattr(m, "member_id", str(m)),
                        "client_id": getattr(m, "client_id", ""),
                        "client_host": getattr(m, "client_host", ""),
                    }
                )
            state = getattr(info, "state", "")
        elif isinstance(info, dict):
            members = info.get("members") or []
            state = info.get("state", "")
        return {
            "group": group_id,
            "state": str(state),
            "member_count": len(members),
            "members": members,
        }
    finally:
        admin.close()


def ensure_e2e_contracts(receiver_base: Optional[str] = None) -> None:
    """确保 e2e 用目标系统与推送规则指向 mock 接收端。"""
    base = (receiver_base or CFG.receiver_url).rstrip("/")
    mappings = {m["id"]: m for m in (api_get("/mapping") or [])}
    if "map-identity" not in mappings:
        api_post(
            "/mapping",
            {"id": "map-identity", "name": "identity", "fields": {}, "enabled": True},
        )

    parties = {p["id"]: p for p in (api_get("/party") or [])}
    for pid, name, typ in (
        ("demo-mes", "Demo MES", "mes.rest"),
        ("demo-erp", "Demo ERP", "erp.rest"),
        ("demo-wms", "Demo WMS", "wms.rest"),
        ("e2e-http", "E2E HTTP Webhook", "mes.rest"),
    ):
        body = {"id": pid, "name": name, "type": typ, "enabled": True, "config": {}}
        if pid in parties:
            api_put(f"/party/{pid}", body)
        else:
            api_post("/party", body)

    contracts = {c["id"]: c for c in (api_get("/contract") or [])}
    wanted = [
        {
            "id": "contract-mes-alert",
            "partyId": "demo-mes",
            "flowType": "ALERT",
            "channel": "party",
            "endpoint": f"{base}/mes/alerts",
            "mappingId": "map-identity",
            "enabled": True,
            "headers": {},
        },
        {
            "id": "contract-erp-data",
            "partyId": "demo-erp",
            "flowType": "DATA",
            "channel": "party",
            "endpoint": f"{base}/erp/telemetry",
            "mappingId": "map-identity",
            "enabled": True,
            "headers": {},
        },
        {
            "id": "contract-http-webhook",
            "partyId": "e2e-http",
            "flowType": None,
            "channel": "http",
            "endpoint": f"{base}/webhook/transform",
            "mappingId": "map-identity",
            "enabled": True,
            "headers": {"partySecret": "e2e-secret"},
        },
        {
            "id": "contract-wms-vision",
            "partyId": "demo-wms",
            "flowType": "VIDEO_META",
            "channel": "party",
            "endpoint": f"{base}/wms/vision",
            "mappingId": "map-identity",
            "enabled": True,
            "headers": {},
        },
    ]
    for c in wanted:
        if c["id"] in contracts:
            api_put(f"/contract/{c['id']}", c)
        else:
            api_post("/contract", c)
    ok("已配置 e2e 目标系统与推送规则 -> " + base)


def build_parser(desc: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("--kafka", default=CFG.kafka)
    p.add_argument("--api", default=CFG.api_base, help="transform-server 直连地址")
    p.add_argument("--timeout", type=float, default=45.0)
    return p


def apply_args(args: argparse.Namespace) -> None:
    CFG.kafka = args.kafka
    CFG.api_base = args.api
