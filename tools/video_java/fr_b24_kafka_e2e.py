#!/usr/bin/env python3
"""FR-B24 local Kafka E2E evidence (Python-first).

Mirrors media_kafka_service topics + upload workers; exercises Java
DvrUploadService.processDvrEvent / SnapUploadService.processSnapEvent via
broker consume (file-missing → honest retry/DLQ OK).

Prerequisite: hosts entry `127.0.0.1 Kafka` — see VIDEO/KAFKA_HOST_CLIENTS.md

Artifacts: logs/fr-b24-kafka-e2e-{ts}.{json,md}
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from vj_common import http_json, repo_root

TOPIC_DVR = "media.dvr.completed"
TOPIC_SNAP = "media.snap.completed"
TOPIC_DVR_DLQ = "media.dvr.dlq"
TOPIC_SNAP_DLQ = "media.snap.dlq"
DEVICE_E2E = "frb24_device"


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def step_log(steps: List[Dict[str, Any]], name: str, ok: bool, detail: str, **extra: Any) -> None:
    row = {"step": name, "ok": ok, "detail": detail, **extra}
    steps.append(row)
    flag = "OK" if ok else "FAIL"
    print(f"  [{flag}] {name}: {detail}")


def probe_kafka(bootstrap: str, steps: List[Dict[str, Any]]) -> bool:
    try:
        from kafka import KafkaAdminClient, KafkaProducer
        from kafka.admin import NewTopic
    except ImportError as e:
        step_log(steps, "kafka_sdk", False, f"kafka import failed: {e}")
        return False

    try:
        admin = KafkaAdminClient(
            bootstrap_servers=bootstrap.split(","),
            client_id="fr-b24-probe",
            request_timeout_ms=10000,
        )
        topics = admin.list_topics()
        step_log(steps, "kafka_list_topics", True, f"broker={bootstrap} topics={len(topics)}")
        for topic in (TOPIC_DVR, TOPIC_SNAP, TOPIC_DVR_DLQ, TOPIC_SNAP_DLQ):
            if topic not in topics:
                try:
                    admin.create_topics([NewTopic(topic, num_partitions=1, replication_factor=1)])
                    step_log(steps, f"kafka_create_{topic}", True, "created")
                except Exception as ce:
                    step_log(steps, f"kafka_create_{topic}", False, str(ce))
        admin.close()
    except Exception as e:
        step_log(
            steps,
            "kafka_admin",
            False,
            f"{type(e).__name__}: {e} — add hosts `127.0.0.1 Kafka` (VIDEO/KAFKA_HOST_CLIENTS.md)",
        )
        return False

    try:
        producer = KafkaProducer(
            bootstrap_servers=bootstrap.split(","),
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            retries=2,
            request_timeout_ms=10000,
        )
        ping = {"event_id": str(uuid.uuid4()), "probe": "fr-b24", "created_at": datetime.now(timezone.utc).isoformat()}
        producer.send(TOPIC_DVR, key=DEVICE_E2E, value=ping)
        producer.flush(timeout=10)
        step_log(steps, "kafka_producer_ping", True, f"published probe to {TOPIC_DVR}")
        producer.close()
        return True
    except Exception as e:
        step_log(steps, "kafka_producer_ping", False, f"{type(e).__name__}: {e}")
        return False


def publish_synthetic_events(bootstrap: str, steps: List[Dict[str, Any]]) -> None:
    try:
        from kafka import KafkaProducer
    except ImportError as e:
        step_log(steps, "kafka_publish", False, str(e))
        return

    producer = KafkaProducer(
        bootstrap_servers=bootstrap.split(","),
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",
        retries=2,
    )
    missing_dvr = "/tmp/frb24_missing_does_not_exist.mp4"
    missing_snap = "/tmp/frb24_missing_snap.jpg"
    dvr_event = {
        "event_id": str(uuid.uuid4()),
        "device_id": DEVICE_E2E,
        "app": "live",
        "stream": DEVICE_E2E,
        "file_path": missing_dvr,
        "cwd": "",
        "source": "fr-b24-e2e",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    snap_event = {
        "event_id": str(uuid.uuid4()),
        "device_id": DEVICE_E2E,
        "file_path": missing_snap,
        "source": "fr-b24-e2e",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        producer.send(TOPIC_DVR, key=DEVICE_E2E, value=dvr_event)
        producer.send(TOPIC_SNAP, key=DEVICE_E2E, value=snap_event)
        producer.flush(timeout=10)
        step_log(
            steps,
            "kafka_publish_missing_file",
            True,
            "published DVR+snap (expect processDvrEvent/processSnapEvent retry, not silent)",
            dvr_topic=TOPIC_DVR,
            snap_topic=TOPIC_SNAP,
            device_id=DEVICE_E2E,
        )
    except Exception as e:
        step_log(steps, "kafka_publish_missing_file", False, str(e))
    finally:
        producer.close()


def media_hook_kafka_path(base_url: str, steps: List[Dict[str, Any]]) -> None:
    dvr_payload = {
        "app": "live",
        "stream": DEVICE_E2E,
        "file": "/tmp/frb24_hook_missing.mp4",
        "cwd": "",
    }
    status, body, _ = http_json("POST", f"{base_url.rstrip('/')}/video/media/hook/srs/on_dvr", dvr_payload)
    ok = status < 500
    step_log(steps, "hook_srs_on_dvr_kafka", ok, f"HTTP {status}", body=body)


def tail_java_log(log_path: Path, steps: List[Dict[str, Any]], wait_s: float = 12.0) -> None:
    time.sleep(wait_s)
    if not log_path.is_file():
        step_log(steps, "java_log_tail", False, f"log missing: {log_path}")
        return
    text = log_path.read_text(encoding="utf-8", errors="replace")
    needles = (
        "DVR Kafka consumer",
        "Snap Kafka consumer",
        "processDvrEvent",
        "DVR 文件未就绪",
        "抓拍文件未就绪",
        "DVR 处理失败",
        "max retries",
        "DLQ",
    )
    hits = [n for n in needles if n in text]
  # processDvrEvent may not appear as literal string in logs — also accept DVR 文件未就绪
    consumer_ok = any(x in text for x in ("DVR Kafka consumer subscribed", "DVR Kafka consumer starting"))
    process_ok = any(x in text for x in ("DVR 文件未就绪", "DVR 处理失败", "创建设备录像空间", "is_custom_save_time"))
    snap_ok = any(x in text for x in ("Snap Kafka consumer", "抓拍文件未就绪"))
    ok = consumer_ok and (process_ok or snap_ok) and "is_custom_save_time" not in text
    step_log(
        steps,
        "java_kafka_e2e",
        ok,
        f"consumer={consumer_ok} dvr_process={process_ok} snap={snap_ok} patterns={len(hits)}/{len(needles)}",
        patterns=hits,
        log_path=str(log_path),
        schema_error="is_custom_save_time" in text,
    )


def write_artifacts(steps: List[Dict[str, Any]], meta: Dict[str, Any]) -> Tuple[Path, Path]:
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ts = utc_ts()
    json_path = logs / f"fr-b24-kafka-e2e-{ts}.json"
    md_path = logs / f"fr-b24-kafka-e2e-{ts}.md"
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), "meta": meta, "steps": steps}
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ok_count = sum(1 for s in steps if s.get("ok"))
    lines = [
        "# FR-B24 Local Kafka E2E Evidence",
        "",
        f"**Generated:** {payload['generated_at']}",
        f"**Profile:** {meta.get('profile', 'local,fr-b24-soak')}",
        f"**Steps:** {ok_count}/{len(steps)} OK",
        "",
        "| step | ok | detail |",
        "|------|----|--------|",
    ]
    for s in steps:
        lines.append(f"| {s['step']} | {'✅' if s.get('ok') else '⛔'} | {s.get('detail', '')} |")
    lines.append("")
    lines.append("> local-only evidence — NOT prod soak PASS. See PROD_SOAK_CHECKLIST.md.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    latest_json = logs / "fr-b24-kafka-e2e-latest.json"
    latest_md = logs / "fr-b24-kafka-e2e-latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    return json_path, md_path


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="FR-B24 Kafka local E2E")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--kafka-bootstrap", default="127.0.0.1:9092")
    parser.add_argument("--java-log", default="")
    parser.add_argument("--wait-consumer-s", type=float, default=15.0)
    args = parser.parse_args(argv)

    steps: List[Dict[str, Any]] = []
    print("FR-B24 Kafka E2E: broker probe")
    broker_ok = probe_kafka(args.kafka_bootstrap, steps)
    if broker_ok:
        print("FR-B24 Kafka E2E: publish synthetic events")
        publish_synthetic_events(args.kafka_bootstrap, steps)
        print("FR-B24 Kafka E2E: media hook kafka path")
        media_hook_kafka_path(args.base_url, steps)

    log_path = Path(args.java_log) if args.java_log else repo_root() / "logs" / "fr-b24-java-soak.log"
    print(f"FR-B24 Kafka E2E: tail Java log {log_path}")
    tail_java_log(log_path, steps, wait_s=args.wait_consumer_s)

    meta = {
        "base_url": args.base_url,
        "kafka_bootstrap": args.kafka_bootstrap,
        "profile": "local,fr-b24-soak",
        "hosts_fix": "127.0.0.1 Kafka (VIDEO/KAFKA_HOST_CLIENTS.md)",
        "python_refs": [
            "VIDEO/_retired_python_video/app/services/media_kafka_service.py",
            "VIDEO/_retired_python_video/services/media_upload_worker/run_worker.py",
            "VIDEO/_retired_python_video/services/media_upload_worker/run_snap_worker.py",
            "VIDEO/_retired_python_video/models.py RecordSpace.save_time_custom",
        ],
        "java_refs": [
            "DvrUploadKafkaConsumerRunner",
            "SnapUploadKafkaConsumerRunner",
            "DvrUploadService.processDvrEvent",
            "SnapUploadService.processSnapEvent",
            "DeviceSpaceRepository (save_time_custom)",
        ],
    }
    json_path, md_path = write_artifacts(steps, meta)
    print(f"\nWrote {json_path}")
    print(f"Wrote {md_path}")
    failed = [s for s in steps if not s.get("ok")]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
