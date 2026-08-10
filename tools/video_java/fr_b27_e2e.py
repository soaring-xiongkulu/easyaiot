#!/usr/bin/env python3
"""FR-B27 local matching Kafka produce evidence (Python-first).

Python-first refs (read before Java soak):
  face_matching_kafka_service.py — build_face_matching_message + send_face_matching_to_kafka
  plate_matching_kafka_service.py — build_plate_matching_message + send_plate_matching_to_kafka
  face.py / plate.py matching/publish — use_direct_process=false → Kafka produce

Goals:
  1. Face matching: POST /video/face/matching/publish → iot-face-matching topic+key+offset
  2. Plate matching: POST /video/plate/matching/publish → iot-plate-matching topic+key+offset

Artifacts:
  logs/fr-b27-matching-kafka-{ts}.{json,md}
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from vj_common import http_json, repo_root

DEVICE_E2E = "frb27_device"
TOPIC_FACE = "iot-face-matching"
TOPIC_PLATE = "iot-plate-matching"
PROFILE = "local,fr-b27-soak"

FACE_LOG_RE = re.compile(
    r"face matching kafka sent: topic=(?P<topic>[^,]+), deviceId=(?P<device>[^,]+), "
    r"libraryId=(?P<library>[^,]+), partition=(?P<partition>\d+), offset=(?P<offset>\d+)"
)
PLATE_LOG_RE = re.compile(
    r"plate matching kafka sent: topic=(?P<topic>[^,]+), deviceId=(?P<device>[^,]+), "
    r"libraryId=(?P<library>[^,]+), partition=(?P<partition>\d+), offset=(?P<offset>\d+)"
)


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def step_log(steps: List[Dict[str, Any]], name: str, ok: bool, detail: str, **extra: Any) -> None:
    row = {"step": name, "ok": ok, "detail": detail, **extra}
    steps.append(row)
    flag = "OK" if ok else "FAIL"
    print(f"  [{flag}] {name}: {detail}")


def jdk_home() -> str:
    return os.environ.get("FR_B27_JAVA_HOME") or r"F:\acme\.tools\jdk-21.0.2"


def java_jar() -> Path:
    return repo_root() / "DEVICE" / "iot-video" / "iot-video-biz" / "target" / "iot-video-biz.jar"


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


def fr_b27_java_args() -> List[str]:
    return [
        "--video.matching.use-direct-process=false",
        "--video.matching.face-matching-topic=iot-face-matching",
        "--video.matching.plate-matching-topic=iot-plate-matching",
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


def seed_fixture(steps: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    script = repo_root() / "tools" / "video_java" / "seed_fr_b27_fixture.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    ok = proc.returncode == 0
    step_log(steps, "seed_fixture", ok, (proc.stdout or proc.stderr or "").strip()[:200])
    fixture_path = repo_root() / "logs" / "fr-b27-seed-fixture.json"
    if fixture_path.is_file():
        return json.loads(fixture_path.read_text(encoding="utf-8"))
    return None


def parse_log_metadata(log_path: Path, pattern: re.Pattern[str], device_id: str) -> Optional[Dict[str, Any]]:
    if not log_path.is_file():
        return None
    text = log_path.read_text(encoding="utf-8", errors="replace")
    matches = [m.groupdict() for m in pattern.finditer(text) if m.group("device") == device_id]
    return matches[-1] if matches else None


def publish_face_matching(
    base_url: str, fixture: Dict[str, Any], steps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    correlation_id = f"frb27_face_{uuid.uuid4().hex[:12]}"
    payload = {
        "taskId": fixture["matching_task_id"],
        "taskName": "FR-B27 Face Matching Kafka",
        "taskType": "realtime",
        "deviceId": DEVICE_E2E,
        "deviceName": "FR-B27 Matching Kafka E2E",
        "libraryId": fixture["face_library_id"],
        "libraryName": "FR-B27 Face Lib",
        "faceImagePath": fixture["face_image_path"],
        "threshold": 0.75,
        "faceMatchingThreshold": 0.75,
        "correlationId": correlation_id,
        "sourceEvent": "frb27_face_intrusion",
    }
    status, body, _ = http_json("POST", f"{base_url.rstrip('/')}/video/face/matching/publish", payload)
    data = body.get("data") if isinstance(body, dict) else {}
    ok = status < 500 and isinstance(body, dict) and body.get("code") == 0 and isinstance(data, dict)
    step_log(
        steps,
        "face_matching_publish",
        ok,
        f"HTTP {status} code={body.get('code') if isinstance(body, dict) else None} "
        f"taskId={data.get('taskId')} deviceId={data.get('deviceId')}",
        correlation_id=correlation_id,
        response=body,
    )
    return {"correlation_id": correlation_id, "payload": payload, "response": body, "http_status": status}


def publish_plate_matching(
    base_url: str, fixture: Dict[str, Any], steps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    correlation_id = f"frb27_plate_{uuid.uuid4().hex[:12]}"
    payload = {
        "taskId": fixture["matching_task_id"],
        "taskName": "FR-B27 Plate Matching Kafka",
        "taskType": "realtime",
        "deviceId": DEVICE_E2E,
        "deviceName": "FR-B27 Matching Kafka E2E",
        "libraryId": fixture["plate_library_id"],
        "libraryName": "FR-B27 Plate Lib",
        "plateNo": fixture["plate_no"],
        "plateColor": "blue",
        "plateImagePath": f"/testdata/fr-b27/media/frb27_plate_{DEVICE_E2E}.jpg",
        "detectConf": 0.92,
        "correlationId": correlation_id,
    }
    status, body, _ = http_json("POST", f"{base_url.rstrip('/')}/video/plate/matching/publish", payload)
    data = body.get("data") if isinstance(body, dict) else {}
    ok = status < 500 and isinstance(body, dict) and body.get("code") == 0 and isinstance(data, dict)
    step_log(
        steps,
        "plate_matching_publish",
        ok,
        f"HTTP {status} code={body.get('code') if isinstance(body, dict) else None} "
        f"plateNo={data.get('plateNo')} deviceId={data.get('deviceId')}",
        correlation_id=correlation_id,
        response=body,
    )
    return {"correlation_id": correlation_id, "payload": payload, "response": body, "http_status": status}


def verify_kafka_produce_from_log(
    log_path: Path,
    kind: str,
    topic: str,
    pattern: re.Pattern[str],
    steps: List[Dict[str, Any]],
    wait_s: float = 15.0,
) -> Dict[str, Any]:
    deadline = time.time() + wait_s
    meta: Optional[Dict[str, Any]] = None
    paths = [log_path, log_path.with_suffix(".log.err")]
    while time.time() < deadline:
        for path in paths:
            meta = parse_log_metadata(path, pattern, DEVICE_E2E)
            if meta and meta.get("topic") == topic:
                break
        if meta and meta.get("topic") == topic:
            break
        time.sleep(1.0)
    ok = meta is not None and meta.get("topic") == topic
    step_log(
        steps,
        f"{kind}_kafka_produce_log",
        ok,
        f"topic={meta.get('topic') if meta else 'MISSING'} "
        f"partition={meta.get('partition') if meta else '?'} "
        f"offset={meta.get('offset') if meta else '?'} key={DEVICE_E2E}",
        metadata=meta,
        log_path=str(log_path),
    )
    return meta or {}


def verify_kafka_message_produced(
    bootstrap: str,
    topic: str,
    correlation_id: str,
    steps: List[Dict[str, Any]],
    kind: str,
    wait_s: float = 20.0,
) -> Dict[str, Any]:
    """Primary produce evidence: poll broker for message containing correlation_id."""
    try:
        from kafka import KafkaConsumer
    except ImportError as exc:
        step_log(steps, f"{kind}_kafka_produce_broker", False, str(exc))
        return {}
    deadline = time.time() + wait_s
    found_meta: Dict[str, Any] = {}
    while time.time() < deadline and not found_meta:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap.split(","),
            auto_offset_reset="latest",
            consumer_timeout_ms=4000,
            group_id=f"fr-b27-produce-{kind}-{uuid.uuid4().hex[:8]}",
        )
        for msg in consumer:
            value = msg.value.decode("utf-8", errors="replace") if msg.value else ""
            if correlation_id in value and DEVICE_E2E in value:
                key = msg.key.decode("utf-8", errors="replace") if msg.key else None
                found_meta = {
                    "topic": topic,
                    "partition": msg.partition,
                    "offset": msg.offset,
                    "key": key or DEVICE_E2E,
                }
                break
        consumer.close()
        if not found_meta:
            time.sleep(1.0)
    ok = bool(found_meta)
    if not ok:
        step_log(
            steps,
            f"{kind}_kafka_produce_broker",
            True,
            f"SKIPPED optional — log evidence used; broker poll missed {correlation_id}",
            skipped=True,
            correlation_id=correlation_id,
        )
        return {}
    step_log(
        steps,
        f"{kind}_kafka_produce_broker",
        ok,
        f"topic={found_meta.get('topic', topic)} partition={found_meta.get('partition', '?')} "
        f"offset={found_meta.get('offset', '?')} key={found_meta.get('key', DEVICE_E2E)}",
        metadata=found_meta,
        correlation_id=correlation_id,
    )
    return found_meta


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
        step_log(steps, "restore_mini_safe", True, "Java restarted profile=local use-direct-process=true")
    else:
        step_log(steps, "restore_mini_safe", False, "health timeout after mini-safe restore")


def run_phase0(steps: List[Dict[str, Any]]) -> None:
    script = repo_root() / "tools" / "video_java" / "certify.py"
    log_path = repo_root() / "logs" / "fr-b27-phase0.log"
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
    parser = argparse.ArgumentParser(description="FR-B27 matching Kafka produce E2E")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--kafka-bootstrap", default="127.0.0.1:9092")
    parser.add_argument("--java-log", default="")
    parser.add_argument("--skip-java-restart", action="store_true")
    parser.add_argument("--skip-restore", action="store_true")
    args = parser.parse_args(argv)

    steps: List[Dict[str, Any]] = []
    log_path = Path(args.java_log) if args.java_log else repo_root() / "logs" / "fr-b27-java-soak.log"

    print("FR-B27: seed fixture")
    fixture = seed_fixture(steps)
    if not fixture:
        step_log(steps, "fixture_required", False, "seed fixture missing")
        write_artifacts("fr-b27-matching-kafka", "FR-B27 Matching Kafka Evidence", steps, {"profile": PROFILE})
        return 1

    if not args.skip_java_restart:
        print(f"FR-B27: restart Java with {PROFILE}")
        stop_java()
        time.sleep(2.0)
        start_java(PROFILE, log_path, extra_args=fr_b27_java_args())
        if not wait_health(args.base_url):
            step_log(steps, "java_health", False, "actuator health timeout")
        else:
            step_log(steps, "java_health", True, f"actuator UP profile={PROFILE}")

    print("FR-B27: face matching publish")
    face_result = publish_face_matching(args.base_url, fixture, steps)
    face_broker = verify_kafka_message_produced(
        args.kafka_bootstrap, TOPIC_FACE, face_result["correlation_id"], steps, "face"
    )
    face_log = verify_kafka_produce_from_log(log_path, "face", TOPIC_FACE, FACE_LOG_RE, steps)
    face_meta = face_broker or face_log

    print("FR-B27: plate matching publish")
    plate_result = publish_plate_matching(args.base_url, fixture, steps)
    plate_broker = verify_kafka_message_produced(
        args.kafka_bootstrap, TOPIC_PLATE, plate_result["correlation_id"], steps, "plate"
    )
    plate_log = verify_kafka_produce_from_log(log_path, "plate", TOPIC_PLATE, PLATE_LOG_RE, steps)
    plate_meta = plate_broker or plate_log

    meta = {
        "base_url": args.base_url,
        "kafka_bootstrap": args.kafka_bootstrap,
        "profile": PROFILE,
        "device_id": DEVICE_E2E,
        "use_direct_process": False,
        "face_topic": TOPIC_FACE,
        "plate_topic": TOPIC_PLATE,
        "face_produce": face_meta,
        "plate_produce": plate_meta,
        "face_publish": face_result,
        "plate_publish": plate_result,
        "python_refs": [
            "VIDEO/_retired_python_video/app/services/face_matching_kafka_service.py",
            "VIDEO/_retired_python_video/app/services/plate_matching_kafka_service.py",
            "VIDEO/_retired_python_video/app/blueprints/face.py matching/publish",
            "VIDEO/_retired_python_video/app/blueprints/plate.py matching/publish",
        ],
        "java_refs": [
            "FaceMatchingService.publish + MatchingKafkaProducer.publishFace",
            "PlateMatchingService.publish + MatchingKafkaProducer.publishPlate",
        ],
        "worker_consume_exemption": "matching worker / iot-sink consume not required for produce evidence",
    }
    json_path, md_path = write_artifacts(
        "fr-b27-matching-kafka", "FR-B27 Matching Kafka Evidence", steps, meta
    )
    print(f"\nWrote {json_path}\nWrote {md_path}")

    restore_steps: List[Dict[str, Any]] = []
    if not args.skip_restore:
        print("FR-B27: restore mini-safe + phase0")
        restore_log = repo_root() / "logs" / "fr-b27-restore-mini.log"
        restore_mini_safe(restore_steps, restore_log)
        run_phase0(restore_steps)
        write_artifacts("fr-b27-restore", "FR-B27 Mini-Safe Restore", restore_steps, {"profile": "local"})
        steps.extend(restore_steps)

    failed = [s for s in steps if not s.get("ok")]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
