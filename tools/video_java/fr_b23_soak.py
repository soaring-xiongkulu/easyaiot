#!/usr/bin/env python3
"""FR-B23 local Kafka + MinIO soak evidence (Python-first).

Mirrors Python media_kafka_service topics + upload workers; exercises Java
DvrUploadKafkaConsumerRunner / SnapUploadKafkaConsumerRunner / VideoMinioService.

Artifacts: logs/fr-b23-soak-{ts}.{json,md}
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

# Python oracle topics (media_kafka_service.py)
TOPIC_DVR = "media.dvr.completed"
TOPIC_SNAP = "media.snap.completed"
TOPIC_DVR_DLQ = "media.dvr.dlq"
TOPIC_SNAP_DLQ = "media.snap.dlq"

DEVICE_SOAK = "frb23_device"


def load_minio_creds() -> Tuple[str, str, str]:
    """Read local VIDEO/.env when present (Python oracle convention)."""
    endpoint = "http://127.0.0.1:9000"
    access_key = "minioadmin"
    secret_key = "minioadmin"
    env_path = repo_root() / "VIDEO" / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip()
            if k == "MINIO_ENDPOINT" and v:
                endpoint = v if v.startswith("http") else f"http://{v}"
            elif k == "MINIO_ACCESS_KEY" and v:
                access_key = v
            elif k == "MINIO_SECRET_KEY" and v:
                secret_key = v
    return endpoint, access_key, secret_key


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def step_log(steps: List[Dict[str, Any]], name: str, ok: bool, detail: str, **extra: Any) -> None:
    row = {"step": name, "ok": ok, "detail": detail, **extra}
    steps.append(row)
    flag = "OK" if ok else "FAIL"
    print(f"  [{flag}] {name}: {detail}")


def probe_minio(endpoint: str, access_key: str, secret_key: str, steps: List[Dict[str, Any]]) -> None:
    try:
        from minio import Minio
        from minio.error import S3Error
    except ImportError as e:
        step_log(steps, "minio_sdk", False, f"minio import failed: {e}")
        return

    host = endpoint.replace("http://", "").replace("https://", "")
    secure = endpoint.startswith("https://")
    try:
        client = Minio(host, access_key=access_key, secret_key=secret_key, secure=secure)
        buckets = list(client.list_buckets())
        step_log(steps, "minio_list_buckets", True, f"{len(buckets)} bucket(s) @ {endpoint}")
        object_name = f"fr-b23/probe-{utc_ts()}.txt"
        data = b"fr-b23 local soak probe\n"
        from io import BytesIO

        bucket = "fr-b23-soak"
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
        client.put_object(bucket, object_name, BytesIO(data), len(data), content_type="text/plain")
        stat = client.stat_object(bucket, object_name)
        step_log(
            steps,
            "minio_put_object",
            True,
            f"uploaded {bucket}/{object_name} size={stat.size}",
            bucket=bucket,
            object_name=object_name,
        )
    except S3Error as e:
        step_log(steps, "minio_probe", False, f"S3Error: {e}")
    except Exception as e:
        step_log(steps, "minio_probe", False, f"{type(e).__name__}: {e}")


def probe_kafka(bootstrap: str, steps: List[Dict[str, Any]]) -> None:
    try:
        from kafka import KafkaProducer, KafkaConsumer
        from kafka.admin import KafkaAdminClient, NewTopic
    except ImportError as e:
        step_log(steps, "kafka_sdk", False, f"kafka import failed: {e}")
        return

    try:
        admin = KafkaAdminClient(
            bootstrap_servers=bootstrap.split(","),
            client_id="fr-b23-probe",
            request_timeout_ms=8000,
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
    except Exception as e:
        step_log(steps, "kafka_admin", False, f"{type(e).__name__}: {e}")
        return

    try:
        producer = KafkaProducer(
            bootstrap_servers=bootstrap.split(","),
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            retries=2,
            request_timeout_ms=10000,
        )
        ping = {"event_id": str(uuid.uuid4()), "probe": "fr-b23", "created_at": datetime.now(timezone.utc).isoformat()}
        producer.send(TOPIC_DVR, key=DEVICE_SOAK, value=ping)
        producer.flush(timeout=10)
        step_log(steps, "kafka_producer_ping", True, f"published probe to {TOPIC_DVR}")
        producer.close()
    except Exception as e:
        step_log(steps, "kafka_producer_ping", False, f"{type(e).__name__}: {e}")


def api_minio_sync(base_url: str, steps: List[Dict[str, Any]]) -> None:
    for path in ("/video/snap/space/sync/minio", "/video/record/space/sync/minio"):
        status, body, _ = http_json("POST", f"{base_url.rstrip('/')}{path}", timeout=30.0)
        data = body.get("data") if isinstance(body, dict) else body
        ok = status < 500 and isinstance(body, dict) and body.get("code") == 0
        detail = f"HTTP {status} code={body.get('code') if isinstance(body, dict) else '?'}"
        if isinstance(data, dict) and data.get("message"):
            detail += f" msg={data.get('message')}"
        step_log(steps, f"api_{path.split('/')[-3]}_sync", ok, detail, response=data)


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
    missing = "/tmp/frb23_missing_does_not_exist.mp4"
    dvr_event = {
        "event_id": str(uuid.uuid4()),
        "device_id": DEVICE_SOAK,
        "app": "live",
        "stream": DEVICE_SOAK,
        "file_path": missing,
        "cwd": "",
        "source": "fr-b23-soak",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    snap_event = {
        "event_id": str(uuid.uuid4()),
        "device_id": DEVICE_SOAK,
        "file_path": "/tmp/frb23_missing_snap.jpg",
        "source": "fr-b23-soak",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        producer.send(TOPIC_DVR, key=DEVICE_SOAK, value=dvr_event)
        producer.send(TOPIC_SNAP, key=DEVICE_SOAK, value=snap_event)
        producer.flush(timeout=10)
        step_log(
            steps,
            "kafka_publish_missing_file",
            True,
            f"published DVR+snap events (expect consumer retry/DLQ, not silent)",
            dvr_topic=TOPIC_DVR,
            snap_topic=TOPIC_SNAP,
        )
    except Exception as e:
        step_log(steps, "kafka_publish_missing_file", False, str(e))
    finally:
        producer.close()


def media_hook_kafka_path(base_url: str, steps: List[Dict[str, Any]]) -> None:
    dvr_payload = {
        "app": "live",
        "stream": DEVICE_SOAK,
        "file": "/tmp/frb23_hook_missing.mp4",
        "cwd": "",
    }
    status, body, _ = http_json("POST", f"{base_url.rstrip('/')}/video/media/hook/srs/on_dvr", dvr_payload)
    ok = status < 500
    step_log(
        steps,
        "hook_srs_on_dvr_kafka",
        ok,
        f"HTTP {status} (kafka mode should enqueue, not sync-upload)",
        body=body,
    )
    snap_payload = {
        "device_id": DEVICE_SOAK,
        "file_path": "/tmp/frb23_hook_snap_missing.jpg",
        "source": "fr-b23-soak",
    }
    try:
        status2, body2, _ = http_json(
            "POST", f"{base_url.rstrip('/')}/video/media/hook/snap/completed", snap_payload, timeout=15.0
        )
    except Exception as e:
        status2, body2 = 0, {"error": str(e)}
    ok2 = status2 < 500 if status2 else False
    step_log(steps, "hook_snap_completed_kafka", ok2, f"HTTP {status2}", body=body2)


def tail_java_log(log_path: Path, steps: List[Dict[str, Any]], wait_s: float = 8.0) -> None:
    time.sleep(wait_s)
    if not log_path.is_file():
        step_log(steps, "java_log_tail", False, f"log missing: {log_path}")
        return
    text = log_path.read_text(encoding="utf-8", errors="replace")
    needles = (
        "DVR Kafka consumer",
        "Snap Kafka consumer",
        "DVR 处理失败",
        "抓拍文件未就绪",
        "max retries",
        "DLQ",
    )
    hits = [n for n in needles if n in text]
    step_log(
        steps,
        "java_log_tail",
        bool(hits),
        f"matched {len(hits)}/{len(needles)} patterns in {log_path.name}",
        patterns=hits,
        log_path=str(log_path),
    )


def write_artifacts(steps: List[Dict[str, Any]], meta: Dict[str, Any]) -> Tuple[Path, Path]:
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ts = utc_ts()
    json_path = logs / f"fr-b23-soak-{ts}.json"
    md_path = logs / f"fr-b23-soak-{ts}.md"
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), "meta": meta, "steps": steps}
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ok_count = sum(1 for s in steps if s.get("ok"))
    lines = [
        "# FR-B23 Local Soak Evidence",
        "",
        f"**Generated:** {payload['generated_at']}",
        f"**Profile:** {meta.get('profile', 'local,fr-b23-soak')}",
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

    latest_json = logs / "fr-b23-soak-latest.json"
    latest_md = logs / "fr-b23-soak-latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    return json_path, md_path


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="FR-B23 Kafka + MinIO local soak")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--kafka-bootstrap", default="127.0.0.1:9092")
    parser.add_argument("--minio-endpoint", default="http://127.0.0.1:9000")
    parser.add_argument("--minio-access-key", default="minioadmin")
    parser.add_argument("--minio-secret-key", default="")
    parser.add_argument("--java-log", default="")
    parser.add_argument("--wait-consumer-s", type=float, default=10.0)
    args = parser.parse_args(argv)

    env_ep, env_ak, env_sk = load_minio_creds()
    minio_endpoint = args.minio_endpoint or env_ep
    minio_access = args.minio_access_key or env_ak
    minio_secret = args.minio_secret_key or env_sk

    steps: List[Dict[str, Any]] = []
    print("FR-B23 soak: MinIO probe")
    probe_minio(minio_endpoint, minio_access, minio_secret, steps)
    print("FR-B23 soak: Kafka probe")
    probe_kafka(args.kafka_bootstrap, steps)
    print("FR-B23 soak: Java MinIO sync APIs")
    api_minio_sync(args.base_url, steps)
    print("FR-B23 soak: synthetic Kafka events (missing file → honest retry)")
    publish_synthetic_events(args.kafka_bootstrap, steps)
    print("FR-B23 soak: media hook kafka path")
    media_hook_kafka_path(args.base_url, steps)

    log_path = Path(args.java_log) if args.java_log else repo_root() / "logs" / "fr-b23-java-soak.log"
    print(f"FR-B23 soak: tail Java log {log_path}")
    tail_java_log(log_path, steps, wait_s=args.wait_consumer_s)

    meta = {
        "base_url": args.base_url,
        "kafka_bootstrap": args.kafka_bootstrap,
        "minio_endpoint": args.minio_endpoint,
        "profile": "local,fr-b23-soak",
        "python_refs": [
            "VIDEO/_retired_python_video/app/services/media_kafka_service.py",
            "VIDEO/_retired_python_video/services/media_upload_worker/run_worker.py",
            "VIDEO/_retired_python_video/app/services/dvr_upload_service.py",
            "VIDEO/_retired_python_video/app/services/snap_upload_service.py",
        ],
        "java_refs": [
            "DvrUploadKafkaConsumerRunner",
            "SnapUploadKafkaConsumerRunner",
            "VideoMinioService",
            "MediaHookService",
        ],
    }
    json_path, md_path = write_artifacts(steps, meta)
    print(f"\nWrote {json_path}")
    print(f"Wrote {md_path}")
    failed = [s for s in steps if not s.get("ok")]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
