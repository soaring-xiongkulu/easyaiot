#!/usr/bin/env python3
"""FR-B30 Snap/Record storage usage stats evidence (Python-first).

Python-first refs (read before Java soak):
  storage_service.py — get_bucket_size / get_device_storage_info
  snap.py — GET /video/snap/device/<id>/storage

Goals:
  1. MinIO disabled → honest zeros (not fake non-zero)
  2. MinIO enabled + objects under device prefix → real snap_size/snap_count

Artifacts: logs/fr-b30-storage-stats-{ts}.{json,md}
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from vj_common import http_json, repo_root

DEVICE_E2E = "frb30_device"
BASE_URL = "http://127.0.0.1:48096"
SNAP_BUCKET = "snap-space"
RECORD_BUCKET = "record-space"


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def step_log(steps: List[Dict[str, Any]], name: str, ok: bool, detail: str, **extra: Any) -> None:
    row = {"step": name, "ok": ok, "detail": detail, **extra}
    steps.append(row)
    flag = "OK" if ok else "FAIL"
    print(f"  [{flag}] {name}: {detail}")


def jdk_home() -> str:
    return os.environ.get("FR_B30_JAVA_HOME") or r"F:\acme\.tools\jdk-21.0.2"


def java_jar() -> Path:
    return repo_root() / "DEVICE" / "iot-video" / "iot-video-biz" / "target" / "iot-video-biz.jar"


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


def stop_java(port: int = 48096, wait_s: float = 20.0) -> None:
    try:
        proc = subprocess.run(
            ["wmic", "process", "where", "name='java.exe'", "get", "ProcessId,CommandLine", "/FORMAT:LIST"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
        current_cmd: Optional[str] = None
        current_pid: Optional[int] = None
        for line in (proc.stdout or "").splitlines():
            line = line.strip()
            if line.startswith("CommandLine="):
                current_cmd = line.split("=", 1)[1]
            elif line.startswith("ProcessId="):
                value = line.split("=", 1)[1].strip()
                current_pid = int(value) if value.isdigit() else None
                if current_pid and current_cmd and "iot-video-biz.jar" in current_cmd:
                    subprocess.run(["taskkill", "/PID", str(current_pid), "/F"], check=False, capture_output=True)
                current_cmd = None
                current_pid = None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    for _ in range(3):
        pid = pid_on_port(port)
        if pid:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False, capture_output=True)
        deadline = time.time() + wait_s / 3
        while time.time() < deadline:
            if pid_on_port(port) is None:
                break
            time.sleep(0.5)
    time.sleep(1.0)


def running_java_minio_enabled() -> Optional[bool]:
    try:
        proc = subprocess.run(
            ["wmic", "process", "where", "name='java.exe'", "get", "ProcessId,CommandLine", "/FORMAT:LIST"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
        current_cmd: Optional[str] = None
        for line in (proc.stdout or "").splitlines():
            line = line.strip()
            if line.startswith("CommandLine="):
                current_cmd = line.split("=", 1)[1]
            elif line.startswith("ProcessId=") and current_cmd and "iot-video-biz.jar" in current_cmd:
                if "--video.minio.enabled=true" in current_cmd:
                    return True
                if "--video.minio.enabled=false" in current_cmd:
                    return False
                current_cmd = None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def start_java(profile: str, log_path: Path, extra_args: Optional[List[str]] = None) -> None:
    stop_java()
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


def fr_b30_java_args(minio_enabled: bool) -> List[str]:
    endpoint, access_key, secret_key = load_minio_creds()
    args = ["--video.minio.enabled=" + ("true" if minio_enabled else "false")]
    if minio_enabled:
        args.extend(
            [
                f"--video.minio.endpoint={endpoint}",
                f"--video.minio.access-key={access_key}",
                f"--video.minio.secret-key={secret_key}",
                "--video.minio.secure=false",
            ]
        )
    return args


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
    script = repo_root() / "tools" / "video_java" / "seed_fr_b30_fixture.py"
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
    fixture_path = repo_root() / "logs" / "fr-b30-seed-fixture.json"
    if fixture_path.is_file():
        return json.loads(fixture_path.read_text(encoding="utf-8"))
    return None


def python_bucket_size(bucket: str, prefix: str, steps: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Mirror storage_service.get_bucket_size."""
    try:
        from minio import Minio
    except ImportError as e:
        step_log(steps, "minio_sdk", False, str(e))
        return 0, 0
    endpoint, access_key, secret_key = load_minio_creds()
    host = endpoint.replace("http://", "").replace("https://", "")
    secure = endpoint.startswith("https://")
    client = Minio(host, access_key=access_key, secret_key=secret_key, secure=secure)
    if not client.bucket_exists(bucket):
        return 0, 0
    total_size = 0
    file_count = 0
    for obj in client.list_objects(bucket, prefix=prefix, recursive=True):
        try:
            stat = client.stat_object(bucket, obj.object_name)
            total_size += stat.size
            file_count += 1
        except Exception:
            pass
    return total_size, file_count


def upload_test_objects(steps: List[Dict[str, Any]]) -> Tuple[int, int]:
    try:
        from minio import Minio
    except ImportError as e:
        step_log(steps, "upload_objects", False, str(e))
        return 0, 0
    endpoint, access_key, secret_key = load_minio_creds()
    host = endpoint.replace("http://", "").replace("https://", "")
    secure = endpoint.startswith("https://")
    client = Minio(host, access_key=access_key, secret_key=secret_key, secure=secure)
    for bucket in (SNAP_BUCKET, RECORD_BUCKET):
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    payload = b"fr-b30-storage-stats-test-" + os.urandom(32)
    snap_key = f"{DEVICE_E2E}/fr-b30-snap-test.jpg"
    video_key = f"{DEVICE_E2E}/fr-b30-video-test.mp4"
    client.put_object(SNAP_BUCKET, snap_key, io.BytesIO(payload), len(payload), content_type="image/jpeg")
    client.put_object(RECORD_BUCKET, video_key, io.BytesIO(payload), len(payload), content_type="video/mp4")
    snap_size, snap_count = python_bucket_size(SNAP_BUCKET, f"{DEVICE_E2E}/", steps)
    video_size, video_count = python_bucket_size(RECORD_BUCKET, f"{DEVICE_E2E}/", steps)
    step_log(
        steps,
        "upload_objects",
        snap_count >= 1 and video_count >= 1,
        f"snap={snap_size}B/{snap_count} video={video_size}B/{video_count}",
        snap_size=snap_size,
        snap_count=snap_count,
        video_size=video_size,
        video_count=video_count,
    )
    return snap_size, video_size


def fetch_storage_stats(steps: List[Dict[str, Any]], label: str) -> Optional[Dict[str, Any]]:
    url = f"{BASE_URL}/video/snap/device/{DEVICE_E2E}/storage"
    status, body, _ = http_json("GET", url, timeout=15.0)
    ok = status == 200 and isinstance(body, dict) and body.get("code") == 0
    data = body.get("data") if isinstance(body, dict) else None
    detail = f"status={status} code={body.get('code') if isinstance(body, dict) else '?'}"
    if isinstance(data, dict):
        detail += (
            f" snap_size={data.get('snap_size')} snap_count={data.get('snap_count')}"
            f" video_size={data.get('video_size')} video_count={data.get('video_count')}"
        )
    step_log(steps, f"get_storage_{label}", ok, detail, data=data if isinstance(data, dict) else None)
    return data if isinstance(data, dict) else None


def assert_zeros(data: Dict[str, Any], steps: List[Dict[str, Any]], label: str) -> bool:
    ok = (
        int(data.get("snap_size") or 0) == 0
        and int(data.get("snap_count") or 0) == 0
        and float(data.get("snap_usage_ratio") or 0) == 0.0
        and int(data.get("video_size") or 0) == 0
        and int(data.get("video_count") or 0) == 0
        and float(data.get("video_usage_ratio") or 0) == 0.0
    )
    step_log(steps, f"assert_honest_zeros_{label}", ok, "all usage fields zero when MinIO disabled")
    return ok


def assert_matches_python(
    data: Dict[str, Any],
    expected_snap_size: int,
    expected_video_size: int,
    steps: List[Dict[str, Any]],
) -> bool:
    snap_size = int(data.get("snap_size") or 0)
    snap_count = int(data.get("snap_count") or 0)
    video_size = int(data.get("video_size") or 0)
    video_count = int(data.get("video_count") or 0)
    ok = (
        snap_size == expected_snap_size
        and snap_count >= 1
        and video_size == expected_video_size
        and video_count >= 1
        and snap_size > 0
        and video_size > 0
    )
    step_log(
        steps,
        "assert_real_minio_stats",
        ok,
        f"java snap={snap_size}/{snap_count} video={video_size}/{video_count}"
        f" expected_snap={expected_snap_size} expected_video={expected_video_size}",
    )
    return ok


def write_artifacts(steps: List[Dict[str, Any]], all_ok: bool) -> Tuple[Path, Path]:
    ts = utc_ts()
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    payload = {
        "fr": "FR-B30",
        "timestamp": ts,
        "device_id": DEVICE_E2E,
        "all_ok": all_ok,
        "python_ref": "storage_service.get_device_storage_info / get_bucket_size",
        "java_ref": "SnapStorageService.enrichWithStorageStats / VideoMinioService.getBucketUsage",
        "steps": steps,
    }
    json_path = logs / f"fr-b30-storage-stats-{ts}.json"
    md_path = logs / f"fr-b30-storage-stats-{ts}.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    latest_json = logs / "fr-b30-storage-stats-latest.json"
    latest_md = logs / "fr-b30-storage-stats-latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    lines = [
        "# FR-B30 storage stats evidence",
        "",
        f"- timestamp: {ts}",
        f"- all_ok: {all_ok}",
        f"- json: `{json_path.name}`",
        "",
        "## Steps",
        "",
    ]
    for row in steps:
        flag = "OK" if row.get("ok") else "FAIL"
        lines.append(f"- [{flag}] {row.get('step')}: {row.get('detail')}")
    latest_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    md_path.write_text(latest_md.read_text(encoding="utf-8"), encoding="utf-8")
    return json_path, md_path


def run_soak(skip_java: bool = False) -> int:
    steps: List[Dict[str, Any]] = []
    seed_fixture(steps)

    if skip_java:
        step_log(steps, "skip_java", True, "build-only mode")
        write_artifacts(steps, all_ok=False)
        return 0

    if not java_jar().is_file():
        step_log(steps, "java_jar", False, f"missing {java_jar()}")
        write_artifacts(steps, all_ok=False)
        return 1

    log_path = repo_root() / "logs" / "fr-b30-java-soak.log"

    # Phase A: MinIO disabled → honest zeros
    stop_java()
    start_java("local", log_path, fr_b30_java_args(minio_enabled=False))
    health_ok = wait_health(BASE_URL)
    step_log(steps, "java_health_disabled", health_ok, BASE_URL)
    disabled_data = fetch_storage_stats(steps, "minio_disabled") if health_ok else None
    zeros_ok = assert_zeros(disabled_data, steps, "minio_disabled") if disabled_data else False

    stop_java()
    expected_snap_size, expected_video_size = upload_test_objects(steps)

    # Phase B: MinIO enabled → real stats
    start_java("local", log_path, fr_b30_java_args(minio_enabled=True))
    health_ok = wait_health(BASE_URL)
    minio_flag = running_java_minio_enabled()
    step_log(steps, "java_health_enabled", health_ok, BASE_URL, minio_enabled=minio_flag)
    enabled_data = None
    if health_ok:
        for attempt in range(6):
            enabled_data = fetch_storage_stats(steps, f"minio_enabled_try{attempt + 1}")
            if enabled_data and int(enabled_data.get("snap_count") or 0) > 0:
                break
            time.sleep(3.0)
    real_ok = (
        assert_matches_python(enabled_data, expected_snap_size, expected_video_size, steps)
        if enabled_data
        else False
    )

    stop_java()
    start_java("local", log_path, fr_b30_java_args(minio_enabled=False))
    wait_health(BASE_URL)

    all_ok = health_ok and zeros_ok and real_ok
    json_path, md_path = write_artifacts(steps, all_ok)
    print(f"\nArtifacts: {json_path}\n           {md_path}")
    return 0 if all_ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="FR-B30 storage stats soak")
    parser.add_argument("--skip-java", action="store_true", help="seed + write scaffold only")
    args = parser.parse_args()
    return run_soak(skip_java=args.skip_java)


if __name__ == "__main__":
    raise SystemExit(main())
