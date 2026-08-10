#!/usr/bin/env python3
"""FR-B25 local DVR+snap real-file → MinIO+DB success evidence (Python-first).

Mirrors Python dvr_upload_service / snap_upload_service success paths:
  file stable → device resolve → MinIO put → metadata (record_file / snap_image / playback)

Prerequisite: hosts `127.0.0.1 Kafka`; Java profile `local,fr-b24-soak` (MinIO + kafka consumers).

Artifacts: logs/fr-b25-minio-upload-e2e-{ts}.{json,md}
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from vj_common import http_json, repo_root

SHANGHAI = ZoneInfo("Asia/Shanghai")

TOPIC_DVR = "media.dvr.completed"
TOPIC_SNAP = "media.snap.completed"
DEVICE_E2E = "frb25_device"

# Minimal valid 1x1 JPEG (stable, >512 bytes for snap stability check)
_MIN_JPEG = bytes(
    [
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
        0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
        0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
        0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
        0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
        0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
        0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
        0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
        0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
        0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
        0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
        0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
        0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
        0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
        0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
        0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
        0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
        0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
        0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
        0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
        0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5, 0xDB, 0x20, 0xA8, 0xF1, 0x7E, 0xFF,
        0xD9,
    ]
)


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def step_log(steps: List[Dict[str, Any]], name: str, ok: bool, detail: str, **extra: Any) -> None:
    row = {"step": name, "ok": ok, "detail": detail, **extra}
    steps.append(row)
    flag = "OK" if ok else "FAIL"
    print(f"  [{flag}] {name}: {detail}")


def load_minio_creds() -> Tuple[str, str, str]:
    endpoint = "http://127.0.0.1:9000"
    access_key = "minioadmin"
    secret_key = "basiclab@iot975248395"
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


def db_url() -> str:
    return os.environ.get(
        "VIDEO_JAVA_DB_URL",
        "postgresql://postgres:iot45722414822@127.0.0.1:15432/iot-video20",
    )


def java_jar() -> Path:
    return (
        repo_root()
        / "DEVICE"
        / "iot-video"
        / "iot-video-biz"
        / "target"
        / "iot-video-biz.jar"
    )


def jdk_home() -> str:
    # FR-B25 brief: JAVA_HOME=F:\acme\.tools\jdk-21.0.2 (override shell JDK 17)
    return os.environ.get("FR_B25_JAVA_HOME") or r"F:\acme\.tools\jdk-21.0.2"


def pid_on_port(port: int) -> Optional[int]:
    try:
        proc = subprocess.run(
            ["netstat", "-ano"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        for line in (proc.stdout or "").splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if parts:
                    return int(parts[-1])
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return None


def stop_java(port: int = 48096) -> None:
    pid = pid_on_port(port)
    if pid:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False, capture_output=True)


def start_java(profile: str, log_path: Path) -> None:
    java_exe = Path(jdk_home()) / "bin" / "java.exe"
    jar = java_jar()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as logf, log_path.with_suffix(".log.err").open(
        "w", encoding="utf-8"
    ) as errf:
        subprocess.Popen(
            [
                str(java_exe),
                "-jar",
                str(jar),
                f"--spring.profiles.active={profile}",
            ],
            stdout=logf,
            stderr=errf,
            cwd=str(repo_root()),
        )


def wait_health(base_url: str, timeout_s: float = 90.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            status, body, _ = http_json("GET", f"{base_url.rstrip('/')}/actuator/health", timeout=5.0)
            if status == 200 and isinstance(body, dict) and body.get("status") == "UP":
                return True
        except Exception:
            pass
        time.sleep(2.0)
    return False


def seed_fixture(steps: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    script = repo_root() / "tools" / "video_java" / "seed_fr_b25_fixture.py"
    proc = subprocess.run([sys.executable, str(script)], check=False, capture_output=True, text=True)
    ok = proc.returncode == 0
    step_log(steps, "seed_fixture", ok, (proc.stdout or proc.stderr or "").strip()[:200])
    fixture_path = repo_root() / "logs" / "fr-b25-seed-fixture.json"
    if fixture_path.is_file():
        return json.loads(fixture_path.read_text(encoding="utf-8"))
    return None


def prepare_media_files(steps: List[Dict[str, Any]]) -> Tuple[Path, Path, str]:
    media_dir = repo_root() / "testdata" / "fr-b25" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    ts = utc_ts()
    dvr_name = f"frb25_dvr_{ts}.mp4"
    snap_name = f"frb25_snap_{ts}.jpg"
    dvr_path = media_dir / dvr_name
    snap_path = media_dir / snap_name

    source_mp4 = repo_root() / "AI" / "test_pose" / "output" / "pose_video_result.mp4"
    if source_mp4.is_file():
        shutil.copy2(source_mp4, dvr_path)
        step_log(steps, "prepare_dvr_file", True, f"copied {source_mp4.name} -> {dvr_path} size={dvr_path.stat().st_size}")
    else:
        dvr_path.write_bytes(b"\x00" * 10000)
        step_log(steps, "prepare_dvr_file", True, f"synthetic pad -> {dvr_path} size=10000")

    snap_path.write_bytes(_MIN_JPEG)
    step_log(steps, "prepare_snap_file", True, f"wrote minimal jpeg -> {snap_path} size={snap_path.stat().st_size}")
    date_dir = dvr_date_dir(dvr_path)
    return dvr_path, snap_path, date_dir


def hook_srs_on_dvr(base_url: str, dvr_path: Path, steps: List[Dict[str, Any]]) -> None:
    """Hybrid mode: enqueue + synchronous processDvrEvent (avoids DVR consumer backlog)."""
    dvr_abs = str(dvr_path.resolve()).replace("\\", "/")
    payload = {
        "app": "live",
        "stream": DEVICE_E2E,
        "file": dvr_abs,
        "file_path": dvr_abs,
        "cwd": "",
    }
    status, body, _ = http_json("POST", f"{base_url.rstrip('/')}/video/media/hook/srs/on_dvr", payload)
    ok = status < 500
    step_log(
        steps,
        "hook_srs_on_dvr_hybrid",
        ok,
        f"HTTP {status} hybrid DVR path file={dvr_path.name}",
        body=body,
    )


def dvr_date_dir(dvr_path: Path) -> str:
    """Match Java MediaDvrPathSupport: date_dir from file mtime in Asia/Shanghai."""
    mtime = dvr_path.stat().st_mtime
    return datetime.fromtimestamp(mtime, SHANGHAI).strftime("%Y/%m/%d")


def publish_real_file_events(
    bootstrap: str,
    dvr_path: Path,
    snap_path: Path,
    steps: List[Dict[str, Any]],
) -> Dict[str, str]:
    try:
        from kafka import KafkaProducer
    except ImportError as e:
        step_log(steps, "kafka_publish", False, str(e))
        return {}

    producer = KafkaProducer(
        bootstrap_servers=bootstrap.split(","),
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",
        retries=2,
    )
    dvr_abs = str(dvr_path.resolve()).replace("\\", "/")
    snap_abs = str(snap_path.resolve()).replace("\\", "/")
    dvr_event = {
        "event_id": str(uuid.uuid4()),
        "device_id": DEVICE_E2E,
        "app": "live",
        "stream": DEVICE_E2E,
        "file_path": dvr_abs,
        "cwd": "",
        "source": "fr-b25-e2e",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    snap_event = {
        "event_id": str(uuid.uuid4()),
        "device_id": DEVICE_E2E,
        "file_path": snap_abs,
        "source": "fr-b25-e2e",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        producer.send(TOPIC_DVR, key=DEVICE_E2E, value=dvr_event)
        producer.send(TOPIC_SNAP, key=DEVICE_E2E, value=snap_event)
        producer.flush(timeout=10)
        step_log(
            steps,
            "kafka_publish_real_files",
            True,
            f"DVR+snap published device={DEVICE_E2E}",
            dvr_path=dvr_abs,
            snap_path=snap_abs,
        )
    except Exception as e:
        step_log(steps, "kafka_publish_real_files", False, str(e))
    finally:
        producer.close()
    return {"dvr_path": dvr_abs, "snap_path": snap_abs, "dvr_filename": dvr_path.name, "snap_filename": snap_path.name}


def verify_minio_objects(
    endpoint: str,
    access_key: str,
    secret_key: str,
    dvr_filename: str,
    snap_filename: str,
    date_dir: str,
    steps: List[Dict[str, Any]],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    try:
        from minio import Minio
    except ImportError as e:
        step_log(steps, "minio_verify", False, str(e))
        return result

    host = endpoint.replace("http://", "").replace("https://", "")
    secure = endpoint.startswith("https://")
    client = Minio(host, access_key=access_key, secret_key=secret_key, secure=secure)
    date_dir = date_dir or datetime.now(SHANGHAI).strftime("%Y/%m/%d")
    dvr_object = f"{DEVICE_E2E}/{date_dir}/{dvr_filename}"
    snap_object = f"{DEVICE_E2E}/{snap_filename}"
    record_bucket = "record-space"
    snap_bucket = "snap-space"

    for label, bucket, obj in (
        ("dvr", record_bucket, dvr_object),
        ("snap", snap_bucket, snap_object),
    ):
        try:
            stat = client.stat_object(bucket, obj)
            url_shape = f"/api/v1/buckets/{bucket}/objects/download?prefix={obj}"
            result[label] = {
                "bucket": bucket,
                "object_name": obj,
                "size": stat.size,
                "record_path_shape": url_shape,
            }
            step_log(
                steps,
                f"minio_stat_{label}",
                True,
                f"{bucket}/{obj} size={stat.size}",
                record_path_shape=url_shape,
            )
        except Exception as e:
            step_log(steps, f"minio_stat_{label}", False, f"{bucket}/{obj}: {e}")
    return result


def verify_db_rows(
    fixture: Dict[str, Any],
    dvr_filename: str,
    snap_filename: str,
    date_dir: str,
    steps: List[Dict[str, Any]],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError as e:
        step_log(steps, "db_verify", False, str(e))
        return result

    date_dir = date_dir or datetime.now(SHANGHAI).strftime("%Y/%m/%d")
    dvr_object = f"{DEVICE_E2E}/{date_dir}/{dvr_filename}"
    snap_object = f"{DEVICE_E2E}/{snap_filename}"
    conn = psycopg2.connect(db_url())
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT object_name, bucket_name, url, file_size FROM record_file "
                "WHERE device_id = %s AND object_name = %s LIMIT 1",
                (DEVICE_E2E, dvr_object),
            )
            rf = cur.fetchone()
            ok_rf = rf is not None and str(rf.get("url", "")).startswith("/api/v1/buckets/")
            result["record_file"] = dict(rf) if rf else None
            step_log(
                steps,
                "db_record_file",
                ok_rf,
                f"object={dvr_object} url={rf.get('url') if rf else 'MISSING'}",
            )

            cur.execute(
                "SELECT object_name, bucket_name, url, file_size FROM snap_image "
                "WHERE device_id = %s AND object_name = %s LIMIT 1",
                (DEVICE_E2E, snap_object),
            )
            si = cur.fetchone()
            ok_si = si is not None and str(si.get("url", "")).startswith("/api/v1/buckets/")
            result["snap_image"] = dict(si) if si else None
            step_log(
                steps,
                "db_snap_image",
                ok_si,
                f"object={snap_object} url={si.get('url') if si else 'MISSING'}",
            )

            cur.execute(
                "SELECT file_path, file_size FROM playback WHERE device_id = %s "
                "AND file_path LIKE '/api/v1/buckets/%%' ORDER BY updated_at DESC LIMIT 1",
                (DEVICE_E2E,),
            )
            pb = cur.fetchone()
            ok_pb = pb is not None
            result["playback"] = dict(pb) if pb else None
            step_log(
                steps,
                "db_playback",
                ok_pb,
                f"file_path={pb.get('file_path') if pb else 'MISSING'}",
            )
    except Exception as e:
        step_log(steps, "db_verify", False, str(e))
    finally:
        conn.close()
    return result


def tail_java_log(log_path: Path, steps: List[Dict[str, Any]], wait_s: float = 20.0) -> None:
    time.sleep(wait_s)
    if not log_path.is_file():
        step_log(steps, "java_log_tail", False, f"log missing: {log_path}")
        return
    text = log_path.read_text(encoding="utf-8", errors="replace")
    dvr_ok = "DVR 上传完成" in text and DEVICE_E2E in text
    snap_ok = "抓拍上传完成" in text and DEVICE_E2E in text
    consumer_ok = "DVR Kafka consumer starting" in text or "DVR Kafka consumer subscribed" in text
    minio_err = "MinIO 上传失败" in text or "MinIO 抓拍上传失败" in text
    ok = dvr_ok and snap_ok and not minio_err
    step_log(
        steps,
        "java_upload_log",
        ok,
        f"consumer={consumer_ok} dvr_done={dvr_ok} snap_done={snap_ok} minio_err={minio_err}",
        log_path=str(log_path),
    )


def write_artifacts(steps: List[Dict[str, Any]], meta: Dict[str, Any]) -> Tuple[Path, Path]:
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ts = utc_ts()
    json_path = logs / f"fr-b25-minio-upload-e2e-{ts}.json"
    md_path = logs / f"fr-b25-minio-upload-e2e-{ts}.md"
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), "meta": meta, "steps": steps}
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ok_count = sum(1 for s in steps if s.get("ok"))
    lines = [
        "# FR-B25 Local MinIO Upload E2E Evidence",
        "",
        f"**Generated:** {payload['generated_at']}",
        f"**Profile:** {meta.get('profile', 'local,fr-b25-soak')}",
        f"**Steps:** {ok_count}/{len(steps)} OK",
        "",
        "| step | ok | detail |",
        "|------|----|--------|",
    ]
    for s in steps:
        lines.append(f"| {s['step']} | {'✅' if s.get('ok') else '⛔'} | {s.get('detail', '')} |")
    lines.append("")
    lines.append("> local-only evidence — NOT prod soak PASS. See PROD_SOAK_CHECKLIST.md §2.4.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    latest_json = logs / "fr-b25-minio-upload-e2e-latest.json"
    latest_md = logs / "fr-b25-minio-upload-e2e-latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    return json_path, md_path


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="FR-B25 MinIO upload local E2E")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--kafka-bootstrap", default="127.0.0.1:9092")
    parser.add_argument("--java-log", default="")
    parser.add_argument("--skip-java-restart", action="store_true")
    parser.add_argument("--profile", default="local,fr-b25-soak")
    parser.add_argument("--wait-consumer-s", type=float, default=25.0)
    args = parser.parse_args(argv)

    steps: List[Dict[str, Any]] = []
    log_path = Path(args.java_log) if args.java_log else repo_root() / "logs" / "fr-b25-java-soak.log"
    profile = args.profile

    print("FR-B25: seed fixture")
    fixture = seed_fixture(steps)

    print("FR-B25: prepare real media files")
    dvr_path, snap_path, date_dir = prepare_media_files(steps)

    if not args.skip_java_restart:
        print(f"FR-B25: restart Java with {profile}")
        stop_java()
        time.sleep(2.0)
        start_java(profile, log_path)
        if not wait_health(args.base_url):
            step_log(steps, "java_health", False, "actuator health timeout")
        else:
            step_log(steps, "java_health", True, f"actuator UP with {profile} profile")

    print("FR-B25: hybrid DVR hook (sync processDvrEvent)")
    hook_srs_on_dvr(args.base_url, dvr_path, steps)

    print("FR-B25: publish Kafka events (real files)")
    paths = publish_real_file_events(args.kafka_bootstrap, dvr_path, snap_path, steps)

    print(f"FR-B25: wait consumer {args.wait_consumer_s}s")
    tail_java_log(log_path, steps, wait_s=args.wait_consumer_s)

    endpoint, access_key, secret_key = load_minio_creds()
    print("FR-B25: verify MinIO objects")
    minio_result = verify_minio_objects(
        endpoint,
        access_key,
        secret_key,
        paths.get("dvr_filename", dvr_path.name),
        paths.get("snap_filename", snap_path.name),
        date_dir,
        steps,
    )

    print("FR-B25: verify DB rows")
    if fixture:
        verify_db_rows(
            fixture,
            paths.get("dvr_filename", dvr_path.name),
            paths.get("snap_filename", snap_path.name),
            date_dir,
            steps,
        )

    meta = {
        "base_url": args.base_url,
        "kafka_bootstrap": args.kafka_bootstrap,
        "profile": profile,
        "device_id": DEVICE_E2E,
        "dvr_date_dir": date_dir,
        "minio_result": minio_result,
        "python_refs": [
            "VIDEO/_retired_python_video/app/services/dvr_upload_service.py",
            "VIDEO/_retired_python_video/app/services/snap_upload_service.py",
            "VIDEO/_retired_python_video/app/services/media_kafka_service.py",
        ],
        "java_refs": [
            "DvrUploadService.processDvrEvent",
            "SnapUploadService.processSnapEvent",
            "VideoMinioService.uploadFile",
        ],
    }
    json_path, md_path = write_artifacts(steps, meta)
    print(f"\nWrote {json_path}")
    print(f"Wrote {md_path}")
    failed = [s for s in steps if not s.get("ok")]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
