#!/usr/bin/env python3
"""FR-B32 MinIO over-quota cleanup real-delete E2E (Python-first).

Python refs (read before Java):
  storage_service.py check_and_cleanup_storage L150-205
  storage_service.py cleanup_old_files L89-147

Artifacts: logs/fr-b32-cleanup-e2e.*
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

from field_contract import http_post_json
from vj_common import http_json, repo_root

DEVICE_ID = "frb32_device"
BASE_URL = "http://127.0.0.1:48096"
SNAP_BUCKET = "snap-space"
OBJECT_COUNT = 5
OBJECT_SIZE = 100
PYTHON_CITE = (
    "VIDEO/_retired_python_video/app/services/storage_service.py "
    "check_and_cleanup_storage L150-205; cleanup_old_files L89-147"
)


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def step_log(steps: List[Dict[str, Any]], name: str, ok: bool, detail: str, **extra: Any) -> None:
    row = {"step": name, "ok": ok, "detail": detail, **extra}
    steps.append(row)
    flag = "OK" if ok else "FAIL"
    print(f"  [{flag}] {name}: {detail}")


def load_fixture() -> Dict[str, Any]:
    path = repo_root() / "logs" / "fr-b32-seed-fixture.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing seed fixture: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def seed_fixture(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    script = repo_root() / "tools" / "video_java" / "seed_fr_b32_fixture.py"
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
    return load_fixture() if ok else {}


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


def minio_client():
    from minio import Minio

    endpoint, access_key, secret_key = load_minio_creds()
    host = endpoint.replace("http://", "").replace("https://", "")
    secure = endpoint.startswith("https://")
    return Minio(host, access_key=access_key, secret_key=secret_key, secure=secure)


def bucket_count(bucket: str, prefix: str) -> Tuple[int, int]:
    """Return (size_bytes, object_count)."""
    client = minio_client()
    if not client.bucket_exists(bucket):
        return 0, 0
    total = 0
    count = 0
    for obj in client.list_objects(bucket, prefix=prefix, recursive=True):
        try:
            stat = client.stat_object(bucket, obj.object_name)
            total += stat.size
            count += 1
        except Exception:
            pass
    return total, count


def purge_device_prefix(steps: List[Dict[str, Any]], bucket: str, prefix: str) -> None:
    try:
        client = minio_client()
        if not client.bucket_exists(bucket):
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
            return
        removed = 0
        for obj in client.list_objects(bucket, prefix=prefix, recursive=True):
            client.remove_object(bucket, obj.object_name)
            removed += 1
        step_log(steps, f"purge_{bucket}", True, f"removed {removed} objects under {prefix}")
    except Exception as exc:
        step_log(steps, f"purge_{bucket}", False, str(exc))


def upload_over_quota_objects(steps: List[Dict[str, Any]], prefix: str) -> int:
    try:
        client = minio_client()
        if not client.bucket_exists(SNAP_BUCKET):
            client.make_bucket(SNAP_BUCKET)
        payload = b"x" * OBJECT_SIZE
        for i in range(OBJECT_COUNT):
            key = f"{prefix}fr-b32-cleanup-{i:02d}.bin"
            client.put_object(SNAP_BUCKET, key, io.BytesIO(payload), len(payload), content_type="application/octet-stream")
            time.sleep(0.05)
        _, count = bucket_count(SNAP_BUCKET, prefix)
        ok = count >= OBJECT_COUNT
        step_log(steps, "upload_over_quota", ok, f"uploaded {OBJECT_COUNT}×{OBJECT_SIZE}B count={count}")
        return count
    except Exception as exc:
        step_log(steps, "upload_over_quota", False, str(exc))
        return 0


def post_cleanup(steps: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    status, body, _ = http_post_json(BASE_URL, f"/video/snap/device/{DEVICE_ID}/storage/cleanup", {})
    data = body.get("data") if isinstance(body, dict) else None
    ok = status < 500 and isinstance(body, dict) and body.get("code") == 0 and isinstance(data, dict)
    deleted = int((data or {}).get("snap_deleted_count") or 0)
    cleaned = bool((data or {}).get("snap_cleaned"))
    step_log(
        steps,
        "post_storage_cleanup",
        ok and cleaned and deleted >= 1,
        f"http={status} snap_cleaned={cleaned} snap_deleted_count={deleted}",
        http_status=status,
        data=data,
    )
    return data if isinstance(data, dict) else None


def write_artifacts(steps: List[Dict[str, Any]], all_ok: bool, before: int, after: int) -> Tuple[Path, Path]:
    ts = utc_ts()
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    payload = {
        "fr": "FR-B32",
        "kind": "cleanup-e2e",
        "timestamp": ts,
        "device_id": DEVICE_ID,
        "python_cite": PYTHON_CITE,
        "java_cite": "SnapStorageService.cleanup / VideoMinioService.cleanupOldFiles",
        "object_count_before": before,
        "object_count_after": after,
        "objects_deleted": max(0, before - after),
        "all_ok": all_ok,
        "steps": steps,
    }
    json_path = logs / f"fr-b32-cleanup-e2e-{ts}.json"
    md_path = logs / f"fr-b32-cleanup-e2e-{ts}.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# FR-B32 Cleanup E2E Evidence",
        "",
        f"**Generated:** {payload['timestamp']}",
        f"**Python cite:** {PYTHON_CITE}",
        f"**Before/after object count:** {before} → {after} (deleted {payload['objects_deleted']})",
        f"**All OK:** {all_ok}",
        "",
        "## Steps",
        "",
    ]
    for row in steps:
        flag = "OK" if row.get("ok") else "FAIL"
        lines.append(f"- [{flag}] `{row['step']}` — {row.get('detail', '')}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for name in ("fr-b32-cleanup-e2e-latest.json", "fr-b32-cleanup-e2e-latest.md"):
        latest = logs / name
        src = json_path if name.endswith(".json") else md_path
        latest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return json_path, md_path


def run_cleanup_e2e(*, assume_java_minio: bool = True) -> Tuple[int, List[Dict[str, Any]]]:
    steps: List[Dict[str, Any]] = []
    fixture = seed_fixture(steps)
    prefix = fixture.get("snap_object_prefix") or f"{DEVICE_ID}/"

    purge_device_prefix(steps, SNAP_BUCKET, prefix)
    _, before_upload = bucket_count(SNAP_BUCKET, prefix)
    step_log(steps, "count_before_upload", True, f"count={before_upload}")

    uploaded = upload_over_quota_objects(steps, prefix)
    size_before, before_cleanup = bucket_count(SNAP_BUCKET, prefix)
    step_log(
        steps,
        "count_before_cleanup",
        before_cleanup >= OBJECT_COUNT,
        f"count={before_cleanup} size={size_before}B",
    )

    if not assume_java_minio:
        step_log(steps, "skip_cleanup_api", True, "assume_java_minio=False")
        write_artifacts(steps, False, before_cleanup, before_cleanup)
        return 1, steps

    data = post_cleanup(steps)
    time.sleep(1.0)
    size_after, after_cleanup = bucket_count(SNAP_BUCKET, prefix)
    step_log(steps, "count_after_cleanup", after_cleanup < before_cleanup, f"count={after_cleanup} size={size_after}B")

    deleted_api = int((data or {}).get("snap_deleted_count") or 0)
    delete_ok = after_cleanup < before_cleanup and deleted_api >= 1
    step_log(steps, "assert_real_delete", delete_ok, f"api_deleted={deleted_api} minio_delta={before_cleanup - after_cleanup}")

    all_ok = all(s.get("ok") for s in steps if s["step"] not in ("count_before_upload",))
    json_path, md_path = write_artifacts(steps, all_ok, before_cleanup, after_cleanup)
    print(f"\nCleanup artifacts: {json_path}\n                  {md_path}")
    return 0 if all_ok else 1, steps


def main() -> int:
    parser = argparse.ArgumentParser(description="FR-B32 cleanup real-delete E2E")
    parser.add_argument("--assume-java-minio", action="store_true", default=True)
    parser.add_argument("--no-assume-java-minio", dest="assume_java_minio", action="store_false")
    args = parser.parse_args()
    code, _ = run_cleanup_e2e(assume_java_minio=args.assume_java_minio)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
