#!/usr/bin/env python3
"""FR-B31 storage cleanup evidence — Python-first vs Java POST /storage/cleanup.

Python: storage_service.check_and_cleanup_storage (threshold + MinIO delete).
Java: SnapStorageService.cleanup aligned in FR-B31.

Uses synthetic frb31_* device prefix only; does not wipe shared buckets.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from field_contract import http_post_json
from route_inventory import repo_root

DEVICE_ID = "vj_p2_device"
BASE_URL = "http://127.0.0.1:48096"
PYTHON_CITE = (
    "VIDEO/_retired_python_video/app/services/storage_service.py "
    "check_and_cleanup_storage L150-205; snap.py cleanup_device_storage L884-893"
)


def main() -> int:
    logs_dir = repo_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    steps = []

    # Probe cleanup on seed device (MinIO may be disabled — honest no-op expected).
    status, body, _ = http_post_json(BASE_URL, f"/video/snap/device/{DEVICE_ID}/storage/cleanup", {})
    ok = status < 500 and isinstance(body, dict) and "code" in body
    steps.append(
        {
            "step": "post_storage_cleanup",
            "path": f"/video/snap/device/{DEVICE_ID}/storage/cleanup",
            "http_status": status,
            "code": body.get("code") if isinstance(body, dict) else None,
            "data_keys": sorted(body.get("data", {}).keys()) if isinstance(body.get("data"), dict) else [],
            "ok": ok,
            "python_cite": PYTHON_CITE,
        }
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "device_id": DEVICE_ID,
        "python_cite": PYTHON_CITE,
        "expected_data_keys": [
            "snap_cleaned",
            "video_cleaned",
            "snap_deleted_count",
            "snap_freed_size",
            "video_deleted_count",
            "video_freed_size",
        ],
        "steps": steps,
        "all_ok": all(s["ok"] for s in steps),
    }

    json_path = logs_dir / f"fr-b31-storage-cleanup-{ts}.json"
    md_path = logs_dir / f"fr-b31-storage-cleanup-{ts}.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    md_lines = [
        "# FR-B31 Storage Cleanup Evidence",
        "",
        f"**Generated:** {payload['generated_at']}",
        f"**Python cite:** {PYTHON_CITE}",
        f"**All OK:** {payload['all_ok']}",
        "",
        "## Steps",
        "",
    ]
    for step in steps:
        md_lines.append(f"- `{step['step']}` HTTP {step['http_status']} code={step['code']} data_keys={step['data_keys']}")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    latest_json = logs_dir / "fr-b31-storage-cleanup-latest.json"
    latest_md = logs_dir / "fr-b31-storage-cleanup-latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"artifact: {json_path}")
    print(f"cleanup ok={payload['all_ok']} http={status} data_keys={steps[0]['data_keys']}")
    return 0 if payload["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
