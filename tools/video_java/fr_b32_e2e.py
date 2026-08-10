#!/usr/bin/env python3
"""FR-B32 orchestrator: cleanup real-delete E2E + 6 binary GET probes + mini-safe restore + phase0."""

from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fr_b30_e2e import (
    fr_b30_java_args,
    java_jar,
    jdk_home,
    load_minio_creds,
    start_java,
    stop_java,
    wait_health,
)
from fr_b32_binary_get import run_binary_get_probes
from fr_b32_cleanup_e2e import run_cleanup_e2e
from vj_common import repo_root


def step_log(steps: List[Dict[str, Any]], name: str, ok: bool, detail: str, **extra: Any) -> None:
    row = {"step": name, "ok": ok, "detail": detail, **extra}
    steps.append(row)
    flag = "OK" if ok else "FAIL"
    print(f"  [{flag}] {name}: {detail}")


def upload_binary_probe_objects(steps: List[Dict[str, Any]]) -> None:
    """Upload MinIO objects for snap/record binary GET 2xx probes."""
    import json

    fixture_path = repo_root() / "logs" / "fr-b32-seed-fixture.json"
    if not fixture_path.is_file():
        step_log(steps, "upload_binary_probes", False, "missing seed fixture")
        return
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    try:
        from minio import Minio
    except ImportError as exc:
        step_log(steps, "upload_binary_probes", False, str(exc))
        return
    endpoint, access_key, secret_key = load_minio_creds()
    host = endpoint.replace("http://", "").replace("https://", "")
    secure = endpoint.startswith("https://")
    client = Minio(host, access_key=access_key, secret_key=secret_key, secure=secure)
    snap_bucket = "snap-space"
    record_bucket = "record-space"
    for bucket in (snap_bucket, record_bucket):
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    snap_key = fixture.get("snap_probe_object", "frb32_device/fr-b32-snap-probe.jpg")
    record_key = fixture.get("record_probe_object", "frb32_device/fr-b32-record-probe.mp4")
    img = b"\xff\xd8\xff\xe0frb32_snap" + b"\xff\xd9"
    vid = b"\x00\x00\x00\x20ftypmp41frb32_record"
    client.put_object(snap_bucket, snap_key, io.BytesIO(img), len(img), content_type="image/jpeg")
    client.put_object(record_bucket, record_key, io.BytesIO(vid), len(vid), content_type="video/mp4")
    step_log(steps, "upload_binary_probes", True, f"snap={snap_key} record={record_key}")


def restore_mini_safe(steps: List[Dict[str, Any]], log_path: Path) -> None:
    stop_java()
    time.sleep(2.0)
    start_java("local", log_path, fr_b30_java_args(minio_enabled=False))
    if wait_health("http://127.0.0.1:48096"):
        step_log(steps, "restore_mini_safe", True, "Java profile=local minio.enabled=false")
    else:
        step_log(steps, "restore_mini_safe", False, "health timeout after mini-safe restore")


def run_phase0(steps: List[Dict[str, Any]]) -> None:
    script = repo_root() / "tools" / "video_java" / "certify.py"
    log_path = repo_root() / "logs" / "certify-frb32-phase0.log"
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
    step_log(steps, "phase0", ok, f"exit={proc.returncode} log={log_path.name}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="FR-B32 full E2E orchestrator")
    parser.add_argument("--skip-java", action="store_true")
    parser.add_argument("--skip-restore", action="store_true")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    args = parser.parse_args(argv)

    restore_steps: List[Dict[str, Any]] = []
    exit_code = 0

    if args.skip_java:
        print("FR-B32: skip-java — seed only")
        subprocess.run([sys.executable, str(repo_root() / "tools" / "video_java" / "seed_fr_b32_fixture.py")])
        return 0

    if not java_jar().is_file():
        print(f"FAIL: missing {java_jar()}")
        return 1

    log_path = repo_root() / "logs" / "fr-b32-java-soak.log"

    print("FR-B32: start Java MinIO enabled")
    stop_java()
    start_java("local", log_path, fr_b30_java_args(minio_enabled=True))
    if not wait_health(args.base_url):
        print("FAIL: Java health timeout")
        return 1

    prep: List[Dict[str, Any]] = []
    upload_binary_probe_objects(prep)

    print("FR-B32: cleanup real-delete E2E")
    cleanup_code, _ = run_cleanup_e2e(assume_java_minio=True)
    exit_code |= cleanup_code

    print("FR-B32: binary/SSE GET content-type probes")
    binary_code, _ = run_binary_get_probes(args.base_url)
    exit_code |= binary_code

    if not args.skip_restore:
        print("FR-B32: restore mini-safe + phase0")
        restore_mini_safe(restore_steps, repo_root() / "logs" / "fr-b32-restore-mini.log")
        run_phase0(restore_steps)
        if not all(s.get("ok") for s in restore_steps):
            exit_code |= 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
