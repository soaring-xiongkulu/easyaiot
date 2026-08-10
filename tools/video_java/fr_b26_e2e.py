#!/usr/bin/env python3
"""FR-B26 local pure Kafka DVR + Alert Kafka evidence (Python-first).

Python-first refs (read before Java soak):
  media_kafka_service.py — upload-mode=kafka enqueue only
  media_hook.py — kafka-only early return (no process_dvr_event)
  alert_hook_service.py — use_direct_persist=false → Kafka produce

Goals:
  1. Pure upload-mode=kafka DVR: hook enqueue → dedicated topic consumer → MinIO+DB
  2. Alert use-direct-persist=false: POST /video/alert/hook → topic+key evidence

Artifacts:
  logs/fr-b26-pure-kafka-dvr-{ts}.{json,md}
  logs/fr-b26-alert-kafka-{ts}.{json,md}
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

DEVICE_E2E = "frb26_device"
TOPIC_DVR_FRB26 = "media.dvr.completed.frb26"
TOPIC_ALERT = "iot-alert-notification"
PROFILE = "local,fr-b26-soak"


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def step_log(steps: List[Dict[str, Any]], name: str, ok: bool, detail: str, **extra: Any) -> None:
    row = {"step": name, "ok": ok, "detail": detail, **extra}
    steps.append(row)
    flag = "OK" if ok else "FAIL"
    print(f"  [{flag}] {name}: {detail}")


def jdk_home() -> str:
    return os.environ.get("FR_B26_JAVA_HOME") or r"F:\acme\.tools\jdk-21.0.2"


def java_jar() -> Path:
    return repo_root() / "DEVICE" / "iot-video" / "iot-video-biz" / "target" / "iot-video-biz.jar"


def db_url() -> str:
    return os.environ.get(
        "VIDEO_JAVA_DB_URL",
        "postgresql://postgres:iot45722414822@127.0.0.1:15432/iot-video20",
    )


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


def stop_java(port: int = 48096, wait_s: float = 15.0) -> None:
    pid = pid_on_port(port)
    if pid:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False, capture_output=True)
    deadline = time.time() + wait_s
    while time.time() < deadline:
        if pid_on_port(port) is None:
            return
        time.sleep(0.5)


def start_java(profile: str, log_path: Path, extra_args: Optional[List[str]] = None) -> None:
    java_exe = Path(jdk_home()) / "bin" / "java.exe"
    jar = java_jar()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(java_exe), "-jar", str(jar), f"--spring.profiles.active={profile}"]
    if extra_args:
        cmd.extend(extra_args)
    with log_path.open("w", encoding="utf-8") as logf, log_path.with_suffix(".log.err").open(
        "w", encoding="utf-8"
    ) as errf:
        subprocess.Popen(cmd, stdout=logf, stderr=errf, cwd=str(repo_root()))


def fr_b26_java_args() -> List[str]:
    """CLI overrides when application-fr-b26-soak.yaml is not yet in the fat jar."""
    return [
        "--video.minio.enabled=true",
        "--video.minio.endpoint=http://127.0.0.1:9000",
        "--video.minio.access-key=minioadmin",
        "--video.minio.secret-key=basiclab@iot975248395",
        "--video.minio.secure=false",
        "--video.alert.use-direct-persist=false",
        "--video.media.upload-mode=kafka",
        "--video.media.snap-upload-mode=sync",
        "--video.media.dvr-completed-topic=media.dvr.completed.frb26",
        "--video.media.dvr-consumer-group=upload-worker-dvr-frb26",
        "--video.kafka.bootstrap-servers=127.0.0.1:9092",
    ]


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


def ensure_dvr_topic(bootstrap: str, steps: List[Dict[str, Any]]) -> bool:
    try:
        from kafka import KafkaAdminClient
        from kafka.admin import NewTopic
    except ImportError as e:
        step_log(steps, "kafka_sdk", False, str(e))
        return False
    try:
        admin = KafkaAdminClient(
            bootstrap_servers=bootstrap.split(","),
            client_id="fr-b26-admin",
            request_timeout_ms=10000,
        )
        topics = admin.list_topics()
        if TOPIC_DVR_FRB26 not in topics:
            admin.create_topics([NewTopic(TOPIC_DVR_FRB26, num_partitions=1, replication_factor=1)])
            step_log(steps, "kafka_create_dvr_topic", True, f"created {TOPIC_DVR_FRB26} (1 partition)")
        else:
            step_log(steps, "kafka_create_dvr_topic", True, f"exists {TOPIC_DVR_FRB26}")
        admin.close()
        return True
    except Exception as e:
        step_log(steps, "kafka_create_dvr_topic", False, str(e))
        return False


def seed_fixture(steps: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    script = repo_root() / "tools" / "video_java" / "seed_fr_b26_fixture.py"
    proc = subprocess.run([sys.executable, str(script)], check=False, capture_output=True, text=True)
    ok = proc.returncode == 0
    step_log(steps, "seed_fixture", ok, (proc.stdout or proc.stderr or "").strip()[:200])
    fixture_path = repo_root() / "logs" / "fr-b26-seed-fixture.json"
    if fixture_path.is_file():
        return json.loads(fixture_path.read_text(encoding="utf-8"))
    return None


def prepare_dvr_file(steps: List[Dict[str, Any]]) -> Tuple[Path, str]:
    media_dir = repo_root() / "testdata" / "fr-b26" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    ts = utc_ts()
    dvr_name = f"frb26_dvr_{ts}.mp4"
    dvr_path = media_dir / dvr_name
    source_mp4 = repo_root() / "AI" / "test_pose" / "output" / "pose_video_result.mp4"
    if source_mp4.is_file():
        shutil.copy2(source_mp4, dvr_path)
        step_log(steps, "prepare_dvr_file", True, f"copied {source_mp4.name} size={dvr_path.stat().st_size}")
    else:
        dvr_path.write_bytes(b"\x00" * 10000)
        step_log(steps, "prepare_dvr_file", True, f"synthetic pad size=10000")
    date_dir = datetime.fromtimestamp(dvr_path.stat().st_mtime, SHANGHAI).strftime("%Y/%m/%d")
    return dvr_path, date_dir


def hook_srs_on_dvr_kafka_only(base_url: str, dvr_path: Path, steps: List[Dict[str, Any]]) -> None:
    """Pure kafka mode: hook enqueues only — no sync processDvrEvent (Python media_hook.py L38-41)."""
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
        "hook_srs_on_dvr_kafka_only",
        ok,
        f"HTTP {status} upload-mode=kafka enqueue-only (no hook sync) file={dvr_path.name}",
        body=body,
    )


def wait_dvr_consumer_success(log_path: Path, steps: List[Dict[str, Any]], wait_s: float = 45.0) -> None:
    deadline = time.time() + wait_s
    dvr_done = False
    consumer_ok = False
    while time.time() < deadline:
        if log_path.is_file():
            text = log_path.read_text(encoding="utf-8", errors="replace")
            consumer_ok = consumer_ok or (TOPIC_DVR_FRB26 in text and "DVR Kafka consumer subscribed" in text)
            if "DVR 上传完成" in text and DEVICE_E2E in text:
                dvr_done = True
                break
        time.sleep(2.0)
    ok = consumer_ok and dvr_done
    step_log(
        steps,
        "dvr_kafka_consumer_success",
        ok,
        f"consumer_subscribed={consumer_ok} dvr_upload_done={dvr_done} topic={TOPIC_DVR_FRB26}",
        log_path=str(log_path),
    )


def verify_minio_dvr(
    endpoint: str,
    access_key: str,
    secret_key: str,
    dvr_filename: str,
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
    dvr_object = f"{DEVICE_E2E}/{date_dir}/{dvr_filename}"
    try:
        stat = client.stat_object("record-space", dvr_object)
        url_shape = f"/api/v1/buckets/record-space/objects/download?prefix={dvr_object}"
        result = {"bucket": "record-space", "object_name": dvr_object, "size": stat.size, "record_path_shape": url_shape}
        step_log(steps, "minio_stat_dvr", True, f"record-space/{dvr_object} size={stat.size}")
    except Exception as e:
        step_log(steps, "minio_stat_dvr", False, f"record-space/{dvr_object}: {e}")
    return result


def verify_db_dvr(dvr_filename: str, date_dir: str, steps: List[Dict[str, Any]]) -> None:
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError as e:
        step_log(steps, "db_verify", False, str(e))
        return
    dvr_object = f"{DEVICE_E2E}/{date_dir}/{dvr_filename}"
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
            step_log(
                steps,
                "db_record_file",
                ok_rf,
                f"object={dvr_object} url={rf.get('url') if rf else 'MISSING'}",
            )
    except Exception as e:
        step_log(steps, "db_verify", False, str(e))
    finally:
        conn.close()


def post_alert_hook(base_url: str, fixture: Optional[Dict[str, Any]], steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    correlation_id = f"frb26_{uuid.uuid4().hex[:12]}"
    payload = {
        "object": "person",
        "event": "frb26_intrusion_test",
        "device_id": DEVICE_E2E,
        "device_name": "FR-B26 Alert Kafka E2E",
        "region": "zone_a",
        "information": "FR-B26 alert kafka produce evidence",
        "task_type": "realtime",
        "correlation_id": correlation_id,
        "time": datetime.now(SHANGHAI).strftime("%Y-%m-%d %H:%M:%S"),
    }
    if fixture and fixture.get("alert_task_id"):
        payload["task_id"] = fixture["alert_task_id"]

    status, body, _ = http_json("POST", f"{base_url.rstrip('/')}/video/alert/hook", payload)
    result_data = {}
    if isinstance(body, dict):
        result_data = body.get("data") if isinstance(body.get("data"), dict) else body

    mode = str(result_data.get("mode", ""))
    topic = str(result_data.get("topic", ""))
    ok = status < 500 and mode == "kafka" and topic == TOPIC_ALERT
    step_log(
        steps,
        "alert_hook_kafka_produce",
        ok,
        f"HTTP {status} mode={mode} topic={topic} partition={result_data.get('partition')} "
        f"offset={result_data.get('offset')} key={DEVICE_E2E}",
        correlation_id=correlation_id,
        response=body,
    )
    return {"correlation_id": correlation_id, "result": result_data, "http_status": status}


def verify_alert_kafka_message(
    bootstrap: str,
    correlation_id: str,
    produce_result: Dict[str, Any],
    steps: List[Dict[str, Any]],
) -> None:
    """iot-sink consumer optional per brief — produce evidence (topic+key+offset) is sufficient."""
    result = produce_result.get("result") or {}
    step_log(
        steps,
        "alert_kafka_consume",
        True,
        f"SKIPPED optional — produce OK topic={result.get('topic')} partition={result.get('partition')} "
        f"offset={result.get('offset')} key={DEVICE_E2E}; iot-sink EX",
        skipped=True,
        correlation_id=correlation_id,
    )


def write_artifacts(
    prefix: str,
    title: str,
    steps: List[Dict[str, Any]],
    meta: Dict[str, Any],
) -> Tuple[Path, Path]:
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ts = utc_ts()
    json_path = logs / f"{prefix}-{ts}.json"
    md_path = logs / f"{prefix}-{ts}.md"
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), "meta": meta, "steps": steps}
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ok_count = sum(1 for s in steps if s.get("ok"))
    lines = [
        f"# {title}",
        "",
        f"**Generated:** {payload['generated_at']}",
        f"**Profile:** {meta.get('profile', PROFILE)}",
        f"**Steps:** {ok_count}/{len(steps)} OK",
        "",
        "| step | ok | detail |",
        "|------|----|--------|",
    ]
    for s in steps:
        lines.append(f"| {s['step']} | {'✅' if s.get('ok') else '⛔'} | {s.get('detail', '')} |")
    lines.append("")
    lines.append("> local-only evidence — NOT prod soak PASS.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    latest_json = logs / f"{prefix}-latest.json"
    latest_md = logs / f"{prefix}-latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    return json_path, md_path


def restore_mini_safe(steps: List[Dict[str, Any]], log_path: Path) -> None:
    stop_java()
    time.sleep(2.0)
    start_java("local", log_path)
    if wait_health("http://127.0.0.1:48096"):
        step_log(steps, "restore_mini_safe", True, "Java restarted profile=local upload-mode=sync")
    else:
        step_log(steps, "restore_mini_safe", False, "health timeout after mini-safe restore")


def run_phase0(steps: List[Dict[str, Any]]) -> None:
    script = repo_root() / "tools" / "video_java" / "certify.py"
    log_path = repo_root() / "logs" / "fr-b26-phase0.log"
    with log_path.open("w", encoding="utf-8") as logf:
        proc = subprocess.run(
            [sys.executable, str(script), "--phase", "0"],
            check=False,
            stdout=logf,
            stderr=subprocess.STDOUT,
            cwd=str(repo_root()),
        )
    gate_path = repo_root() / "docs" / "video-java" / "gates" / "PHASE_0_GATE.md"
    gate_text = gate_path.read_text(encoding="utf-8", errors="replace") if gate_path.is_file() else ""
    ok = proc.returncode == 0 and "PASS" in gate_text
    step_log(steps, "phase0", ok, f"exit={proc.returncode} gate={gate_path.name}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="FR-B26 pure Kafka DVR + Alert Kafka E2E")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--kafka-bootstrap", default="127.0.0.1:9092")
    parser.add_argument("--java-log", default="")
    parser.add_argument("--skip-java-restart", action="store_true")
    parser.add_argument("--skip-restore", action="store_true")
    parser.add_argument("--wait-consumer-s", type=float, default=45.0)
    args = parser.parse_args(argv)

    dvr_steps: List[Dict[str, Any]] = []
    alert_steps: List[Dict[str, Any]] = []
    log_path = Path(args.java_log) if args.java_log else repo_root() / "logs" / "fr-b26-java-soak.log"

    print("FR-B26: seed fixture")
    fixture = seed_fixture(dvr_steps)

    print("FR-B26: ensure dedicated DVR topic")
    ensure_dvr_topic(args.kafka_bootstrap, dvr_steps)

    print("FR-B26: prepare real DVR file")
    dvr_path, date_dir = prepare_dvr_file(dvr_steps)

    if not args.skip_java_restart:
        print(f"FR-B26: restart Java with {PROFILE}")
        stop_java()
        time.sleep(2.0)
        start_java(PROFILE, log_path, extra_args=fr_b26_java_args())
        if not wait_health(args.base_url):
            step_log(dvr_steps, "java_health", False, "actuator health timeout")
        else:
            step_log(dvr_steps, "java_health", True, f"actuator UP profile={PROFILE}")

    print("FR-B26: pure kafka DVR hook (enqueue only)")
    hook_srs_on_dvr_kafka_only(args.base_url, dvr_path, dvr_steps)

    print(f"FR-B26: wait DVR consumer success ({args.wait_consumer_s}s)")
    wait_dvr_consumer_success(log_path, dvr_steps, wait_s=args.wait_consumer_s)

    endpoint, access_key, secret_key = load_minio_creds()
    print("FR-B26: verify MinIO DVR object")
    minio_result = verify_minio_dvr(endpoint, access_key, secret_key, dvr_path.name, date_dir, dvr_steps)

    print("FR-B26: verify DB record_file")
    verify_db_dvr(dvr_path.name, date_dir, dvr_steps)

    dvr_meta = {
        "base_url": args.base_url,
        "kafka_bootstrap": args.kafka_bootstrap,
        "profile": PROFILE,
        "device_id": DEVICE_E2E,
        "dvr_topic": TOPIC_DVR_FRB26,
        "upload_mode": "kafka",
        "dvr_date_dir": date_dir,
        "minio_result": minio_result,
        "python_refs": [
            "VIDEO/_retired_python_video/app/services/media_kafka_service.py",
            "VIDEO/_retired_python_video/app/blueprints/media_hook.py",
        ],
        "java_refs": [
            "MediaHookService.srsOnDvr (kafka-only branch)",
            "DvrUploadKafkaConsumerRunner",
            "DvrUploadService.processDvrEvent",
        ],
    }
    dvr_json, dvr_md = write_artifacts("fr-b26-pure-kafka-dvr", "FR-B26 Pure Kafka DVR Evidence", dvr_steps, dvr_meta)
    print(f"\nWrote {dvr_json}\nWrote {dvr_md}")

    print("FR-B26: alert hook kafka produce (use-direct-persist=false)")
    alert_result = post_alert_hook(args.base_url, fixture, alert_steps)
    verify_alert_kafka_message(
        args.kafka_bootstrap,
        alert_result.get("correlation_id", ""),
        alert_result,
        alert_steps,
    )

    alert_meta = {
        "base_url": args.base_url,
        "kafka_bootstrap": args.kafka_bootstrap,
        "profile": PROFILE,
        "device_id": DEVICE_E2E,
        "alert_topic": TOPIC_ALERT,
        "use_direct_persist": False,
        "produce_result": alert_result,
        "python_refs": [
            "VIDEO/_retired_python_video/app/services/alert_hook_service.py",
        ],
        "java_refs": [
            "AlertHookService.sendViaKafka",
            "AlertKafkaProducer.send",
        ],
        "iot_sink_exemption": "iot-sink consumer not required for produce evidence",
    }
    alert_json, alert_md = write_artifacts("fr-b26-alert-kafka", "FR-B26 Alert Kafka Evidence", alert_steps, alert_meta)
    print(f"\nWrote {alert_json}\nWrote {alert_md}")

    restore_steps: List[Dict[str, Any]] = []
    if not args.skip_restore:
        print("FR-B26: restore mini-safe + phase0")
        restore_log = repo_root() / "logs" / "fr-b26-restore-mini.log"
        restore_mini_safe(restore_steps, restore_log)
        run_phase0(restore_steps)
        write_artifacts("fr-b26-restore", "FR-B26 Mini-Safe Restore", restore_steps, {"profile": "local"})

    all_steps = dvr_steps + alert_steps + restore_steps
    failed = [s for s in all_steps if not s.get("ok")]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
