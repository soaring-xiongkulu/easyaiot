#!/usr/bin/env python3
"""FR-B45 — plate matching Kafka publish → Java consumer → alert evidence.

Python-first:
- plate_matching_kafka_service.send_plate_matching_to_kafka L63-88
- plate.py publish_plate_matching L359-387
- library_matching_service.process_plate_matching_message L303-382

Java:
- PlateMatchingService.publish + MatchingKafkaProducer.publishPlate
- PlateMatchingKafkaConsumerRunner → PlateMatchingService.process

Artifacts: logs/fr-b45-plate-kafka-alert-latest.{json,md}
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from field_contract import server_reachable
from fr_b37_multipart import create_library, delete_path
from seed_fr_b45_fixture import seed_fixture
from vj_common import http_json, repo_root

_PY_LIB_MATCH = "VIDEO/_retired_python_video/app/services/library_matching_service.py"
_PY_PLATE_KAFKA = "VIDEO/_retired_python_video/app/services/plate_matching_kafka_service.py"
_PY_PLATE_BP = "VIDEO/_retired_python_video/app/blueprints/plate.py"
_JAVA_CONSUMER = "DEVICE/iot-video/.../PlateMatchingKafkaConsumerRunner.java"
_EVENT_PLATE = "plate_library_match"

DISCLAIMER = (
    "FR-B45 Kafka path requires broker + fr-b45-soak (consumer enabled, use-direct-process=false). "
    "Local-only evidence — not COMPLETE."
)


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def enroll_plate(base_url: str, ts: str, plate_no: str, timeout: float) -> Tuple[Optional[int], Optional[int]]:
    lib_id = create_library(base_url, "/video/plate/libraries", f"frb45_kafka_plate_{ts}", timeout)
    if lib_id is None:
        return None, None
    status, body, _ = http_json(
        "POST",
        f"{base_url.rstrip('/')}/video/plate/libraries/{lib_id}/entries",
        {
            "plate_no": plate_no,
            "plate_color": "blue",
            "owner_name": f"frb45_kafka_owner_{ts}",
            "is_enabled": True,
        },
        timeout=timeout,
    )
    entry_id = None
    if isinstance(body, dict) and body.get("code") == 0:
        entry_id = (body.get("data") or {}).get("id")
    else:
        delete_path(base_url, f"/video/plate/libraries/{lib_id}", timeout)
        return None, None
    return lib_id, entry_id


def wait_plate_alert(
    base_url: str,
    correlation_id: str,
    timeout_s: float,
    poll_s: float = 2.0,
) -> Tuple[Optional[Dict[str, Any]], int]:
    deadline = time.time() + timeout_s
    last_count = 0
    while time.time() < deadline:
        status, body, _ = http_json(
            "GET",
            f"{base_url.rstrip('/')}/video/alert/correlation?correlation_id={correlation_id}",
            timeout=10.0,
        )
        if status < 500 and isinstance(body, dict) and body.get("code") == 0:
            data = body.get("data") or {}
            alerts = data.get("alerts") or []
            last_count = len(alerts)
            for alert in alerts:
                if isinstance(alert, dict) and alert.get("event") == _EVENT_PLATE:
                    return alert, last_count
        time.sleep(poll_s)
    return None, last_count


def probe_plate_kafka_alert(
    base_url: str,
    ts: str,
    plate_no: str,
    task_id: int,
    plate_lib_id: int,
    timeout: float,
    wait_alert_s: float,
) -> Dict[str, Any]:
    correlation_id = f"frb45_kafka_plate_{ts}"
    row: Dict[str, Any] = {
        "id": "plate_kafka_publish_consume_alert",
        "path": "POST /video/plate/matching/publish → Kafka → PlateMatchingKafkaConsumerRunner",
        "python_source": (
            f"{_PY_PLATE_BP} publish_plate_matching → "
            f"{_PY_PLATE_KAFKA} send_plate_matching_to_kafka L63-88 → "
            f"{_PY_LIB_MATCH} process_plate_matching_message"
        ),
        "java_consumer": _JAVA_CONSUMER,
        "checks": [],
        "correlation_id": correlation_id,
        "plate_no": plate_no,
    }
    payload = {
        "taskId": task_id,
        "taskName": f"frb45_kafka_match_{ts}",
        "taskType": "realtime",
        "deviceId": "frb45_device",
        "deviceName": "FR-B45 Plate Kafka Alert",
        "libraryId": plate_lib_id,
        "plateNo": plate_no,
        "plateColor": "blue",
        "correlationId": correlation_id,
    }
    status, body, _ = http_json(
        "POST",
        f"{base_url.rstrip('/')}/video/plate/matching/publish",
        payload,
        timeout=timeout,
    )
    row["publish_http_status"] = status
    row["publish_business_code"] = body.get("code") if isinstance(body, dict) else None
    row["publish_data"] = body.get("data") if isinstance(body, dict) else None

    ok = status < 500 and isinstance(body, dict) and body.get("code") == 0
    if not ok:
        row["checks"].append(
            {
                "check": "kafka_publish",
                "status": "fail",
                "detail": f"HTTP {status} code={body.get('code') if isinstance(body, dict) else None}",
            }
        )
        row["ok"] = False
        return row
    row["checks"].append({"check": "kafka_publish", "status": "pass"})

    alert, alert_count = wait_plate_alert(base_url, correlation_id, wait_alert_s)
    row["alert_wait_s"] = wait_alert_s
    row["alerts_in_correlation"] = alert_count
    if alert:
        row["alert_id"] = alert.get("id")
        row["alert_event"] = alert.get("event")
        row["checks"].append(
            {
                "check": "kafka_consume_alert",
                "status": "pass",
                "detail": f"event={_EVENT_PLATE} id={alert.get('id')}",
            }
        )
        row["ok"] = True
    else:
        row["checks"].append(
            {
                "check": "kafka_consume_alert",
                "status": "fail",
                "detail": f"no {_EVENT_PLATE} alert after {wait_alert_s}s (page_count={alert_count})",
            }
        )
        row["ok"] = False

    return row


def write_artifacts(payload: Dict[str, Any]) -> Tuple[Path, Path]:
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ts = payload.get("generated_at", utc_ts())
    json_path = logs / f"fr-b45-plate-kafka-alert-{ts}.json"
    md_path = logs / f"fr-b45-plate-kafka-alert-{ts}.md"
    latest_json = logs / "fr-b45-plate-kafka-alert-latest.json"
    latest_md = logs / "fr-b45-plate-kafka-alert-latest.md"
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    json_path.write_text(text, encoding="utf-8")
    latest_json.write_text(text, encoding="utf-8")

    lines = [
        "# FR-B45 plate Kafka→consumer→alert probes",
        "",
        f"- generated_at: {payload.get('generated_at')}",
        f"- base_url: {payload.get('base_url')}",
        f"- profile_hint: {payload.get('profile_hint')}",
        "",
        "## Results",
        "",
        "| id | publish | ok | alert_id |",
        "|----|---------|-----|----------|",
    ]
    for row in payload.get("probes", []):
        lines.append(
            f"| {row.get('id')} | {row.get('publish_business_code', '—')} | "
            f"{row.get('ok')} | {row.get('alert_id', '—')} |"
        )
    lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"artifact: {json_path}")
    print(f"artifact: {md_path}")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="FR-B45 plate Kafka consume → alert probes")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--wait-alert-s", type=float, default=30.0)
    parser.add_argument("--skip-seed", action="store_true")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    plate_no = f"KFB45{ts[-6:]}"
    server_up, health_detail = server_reachable(args.base_url, timeout=min(args.timeout, 5.0))

    fixture: Dict[str, Any] = {}
    if not args.skip_seed:
        try:
            fixture = seed_fixture()
        except Exception as exc:
            print(f"seed warning: {exc}")

    probes: List[Dict[str, Any]] = []
    if not server_up:
        probes.append({"id": "server", "ok": False, "checks": [{"check": "server", "status": "skip", "detail": health_detail}]})
    else:
        plate_lib_id, entry_id = enroll_plate(args.base_url, ts, plate_no, args.timeout)
        if plate_lib_id is None:
            probes.append({"id": "plate_enroll", "ok": False})
        else:
            task_id = fixture.get("task_id")
            if task_id is None:
                probes.append({"id": "fixture", "ok": False})
            else:
                seed_fixture(plate_lib_id=plate_lib_id, task_id=task_id)
                probes.append(
                    probe_plate_kafka_alert(
                        args.base_url,
                        ts,
                        plate_no,
                        int(task_id),
                        int(plate_lib_id),
                        args.timeout,
                        args.wait_alert_s,
                    )
                )
            if entry_id:
                delete_path(args.base_url, f"/video/plate/entries/{entry_id}", args.timeout)
            if plate_lib_id:
                delete_path(args.base_url, f"/video/plate/libraries/{plate_lib_id}", args.timeout)

    passed = sum(1 for p in probes if p.get("ok"))
    payload = {
        "generated_at": utc_ts(),
        "base_url": args.base_url,
        "server_up": server_up,
        "health_detail": health_detail,
        "profile_hint": "local,fr-b45-soak (plate-matching-consumer-enabled=true)",
        "seed_fixture": fixture,
        "probes": probes,
        "summary": {"pass": passed, "total": len(probes)},
        "disclaimer": DISCLAIMER,
    }
    write_artifacts(payload)
    print(f"\nfr-b45-plate-kafka-alert: {passed}/{len(probes)} pass")
    return 0 if passed == len(probes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
