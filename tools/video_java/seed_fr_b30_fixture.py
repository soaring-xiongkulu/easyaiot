#!/usr/bin/env python3
"""Seed FR-B30 device storage stats fixture (frb30_device + bucket config)."""

from __future__ import annotations

import json
import os
from pathlib import Path

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("FAIL: psycopg2 required")
    raise SystemExit(1)

DEVICE_ID = "frb30_device"
SNAP_BUCKET = "snap-space"
RECORD_BUCKET = "record-space"
SNAP_MAX_BYTES = 1_073_741_824  # 1 GiB


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def db_url() -> str:
    return os.environ.get(
        "VIDEO_JAVA_DB_URL",
        "postgresql://postgres:iot45722414822@127.0.0.1:15432/iot-video20",
    )


def main() -> int:
    conn = psycopg2.connect(db_url())
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO device (
                  id, name, source, rtmp_stream, http_stream, manufacturer, model,
                  nvr_channel, auto_snap_enabled, stream, enable_forward
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 0, false, 0, false)
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                """,
                (
                    DEVICE_ID,
                    "FR-B30 Storage Stats E2E",
                    "file://F:/acme/RUNTIME/testdata/sample.mp4",
                    f"rtmp://127.0.0.1/live/{DEVICE_ID}",
                    f"http://127.0.0.1:8080/{DEVICE_ID}",
                    "fr-b30",
                    "storage-stats-e2e",
                ),
            )
            cur.execute(
                """
                INSERT INTO device_storage_config (
                  device_id,
                  snap_storage_bucket, snap_storage_max_size,
                  snap_storage_cleanup_enabled, snap_storage_cleanup_threshold, snap_storage_cleanup_ratio,
                  video_storage_bucket, video_storage_max_size,
                  video_storage_cleanup_enabled, video_storage_cleanup_threshold, video_storage_cleanup_ratio
                ) VALUES (%s, %s, %s, true, 0.8, 0.3, %s, %s, true, 0.8, 0.3)
                ON CONFLICT (device_id) DO UPDATE SET
                  snap_storage_bucket = EXCLUDED.snap_storage_bucket,
                  snap_storage_max_size = EXCLUDED.snap_storage_max_size,
                  video_storage_bucket = EXCLUDED.video_storage_bucket,
                  video_storage_max_size = EXCLUDED.video_storage_max_size,
                  updated_at = NOW()
                """,
                (DEVICE_ID, SNAP_BUCKET, SNAP_MAX_BYTES, RECORD_BUCKET, SNAP_MAX_BYTES),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    artifact = {
        "device_id": DEVICE_ID,
        "snap_storage_bucket": SNAP_BUCKET,
        "video_storage_bucket": RECORD_BUCKET,
        "snap_storage_max_size": SNAP_MAX_BYTES,
    }
    out = repo_root() / "logs" / "fr-b30-seed-fixture.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"OK seed fixture -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
