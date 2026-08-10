#!/usr/bin/env python3
"""Seed FR-B25 MinIO upload E2E fixture (frb25_device + spaces)."""

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

DEVICE_ID = "frb25_device"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def db_url() -> str:
    return os.environ.get(
        "VIDEO_JAVA_DB_URL",
        "postgresql://postgres:iot45722414822@127.0.0.1:15432/iot-video20",
    )


def _ensure_device(cur) -> None:
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
            "FR-B25 MinIO Upload E2E",
            "file://F:/acme/RUNTIME/testdata/sample.mp4",
            f"rtmp://127.0.0.1/live/{DEVICE_ID}",
            f"http://127.0.0.1:8080/{DEVICE_ID}",
            "fr-b25",
            "minio-upload-e2e",
        ),
    )


def _ensure_space(cur, table: str, code: str, bucket: str) -> int:
    cur.execute(f"SELECT id FROM {table} WHERE device_id = %s LIMIT 1", (DEVICE_ID,))
    row = cur.fetchone()
    if row:
        return int(row["id"])
    cur.execute(
        f"""
        INSERT INTO {table} (
          space_name, space_code, bucket_name, save_mode, save_time, save_time_custom,
          description, device_id
        ) VALUES (%s, %s, %s, 0, 24, false, %s, %s)
        RETURNING id
        """,
        (f"FR-B25 {table}", code, bucket, "fr-b25 minio upload e2e seed", DEVICE_ID),
    )
    return int(cur.fetchone()["id"])


def main() -> int:
    conn = psycopg2.connect(db_url())
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            _ensure_device(cur)
            snap_id = _ensure_space(cur, "snap_space", "FRB25_SNAP", "snap-space")
            record_id = _ensure_space(cur, "record_space", "FRB25_RECORD", "record-space")
        conn.commit()
        out = {
            "device_id": DEVICE_ID,
            "snap_space_id": snap_id,
            "record_space_id": record_id,
        }
        path = repo_root() / "logs" / "fr-b25-seed-fixture.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print(f"OK seeded {DEVICE_ID} -> {path}")
        return 0
    except Exception as e:
        conn.rollback()
        print(f"FAIL: {e}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
