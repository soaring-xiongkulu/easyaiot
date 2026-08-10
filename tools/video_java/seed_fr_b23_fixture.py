#!/usr/bin/env python3
"""Seed FR-B23 deep-field fixtures (snap_task_list + record_videos_list).

Uses synthetic ids prefixed frb23_ where new rows are created; also ensures
vj_p2_device has list rows so field_contract deep asserts do not skip.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("FAIL: psycopg2 required (pip install psycopg2-binary)")
    raise SystemExit(1)

DEVICE_VJ = "vj_p2_device"
DEVICE_FRB = "frb23_device"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def db_url() -> str:
    return os.environ.get(
        "VIDEO_JAVA_DB_URL",
        "postgresql://postgres:iot45722414822@127.0.0.1:15432/iot-video20",
    )


def _upsert_device(cur, device_id: str, name: str) -> None:
    cur.execute(
        """
        INSERT INTO device (
          id, name, source, rtmp_stream, http_stream, manufacturer, model,
          nvr_channel, auto_snap_enabled, stream, enable_forward
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, 0, false, 0, false)
        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
        """,
        (
            device_id,
            name,
            "file://F:/acme/RUNTIME/testdata/sample.mp4",
            f"rtmp://127.0.0.1/live/{device_id}",
            f"http://127.0.0.1:8080/{device_id}",
            "fr-b23",
            "soak-fixture",
        ),
    )


def _ensure_space(cur, table: str, code: str, name: str, device_id: str, bucket: str) -> int:
    cur.execute(f"SELECT id FROM {table} WHERE device_id = %s ORDER BY id LIMIT 1", (device_id,))
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
        (name, code, bucket, "fr-b23 seed", device_id),
    )
    return int(cur.fetchone()["id"])


def _ensure_snap_task(cur, space_id: int, device_id: str, suffix: str) -> int:
    code = f"frb23_snap_{suffix}"
    cur.execute("SELECT id FROM snap_task WHERE task_code = %s", (code,))
    row = cur.fetchone()
    if row:
        return int(row["id"])
    cur.execute(
        """
        INSERT INTO snap_task (
          task_name, task_code, space_id, device_id, capture_type, cron_expression, frame_skip,
          algorithm_enabled, algorithm_type, algorithm_model_id, algorithm_threshold, algorithm_night_mode,
          alarm_enabled, alarm_type, phone_number, email, notify_users, notify_methods, alarm_suppress_time,
          auto_filename, custom_filename_prefix, is_enabled, status, run_status, total_captures
        ) VALUES (
          %s, %s, %s, %s, 0, '0 */5 * * * *', 1,
          false, NULL, NULL, NULL, false,
          false, 0, NULL, NULL, NULL, NULL, 300,
          true, NULL, false, 0, 'stopped', 0
        )
        RETURNING id
        """,
        (f"fr-b23 snap {suffix}", code, space_id, device_id),
    )
    return int(cur.fetchone()["id"])


def _ensure_record_file(cur, space_id: int, device_id: str, suffix: str) -> int:
    object_name = f"{device_id}/2026/08/11/frb23_{suffix}.mp4"
    bucket = "record-space"
    cur.execute(
        "SELECT id FROM record_file WHERE bucket_name = %s AND object_name = %s",
        (bucket, object_name),
    )
    row = cur.fetchone()
    if row:
        return int(row["id"])
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cur.execute(
        """
        INSERT INTO record_file (
          space_id, device_id, object_name, bucket_name, filename,
          file_size, content_type, url, duration, event_time, source, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        RETURNING id
        """,
        (
            space_id,
            device_id,
            object_name,
            bucket,
            f"frb23_{suffix}.mp4",
            12345,
            "video/mp4",
            f"/api/v1/buckets/{bucket}/objects/download?prefix={object_name}",
            10,
            now,
            "dvr",
        ),
    )
    return int(cur.fetchone()["id"])


def main() -> int:
    conn = psycopg2.connect(db_url())
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    created: dict[str, object] = {}

    for device_id, label in ((DEVICE_VJ, "vj_p2"), (DEVICE_FRB, "frb23")):
        _upsert_device(cur, device_id, f"FR-B23 {label} camera")
        snap_space_id = _ensure_space(
            cur, "snap_space", f"{label}_snap", f"{label} snap", device_id, "snap-space"
        )
        record_space_id = _ensure_space(
            cur, "record_space", f"{label}_record", f"{label} record", device_id, "record-space"
        )
        snap_task_id = _ensure_snap_task(cur, snap_space_id, device_id, label)
        record_file_id = _ensure_record_file(cur, record_space_id, device_id, label)
        created[device_id] = {
            "snap_space_id": snap_space_id,
            "record_space_id": record_space_id,
            "snap_task_id": snap_task_id,
            "record_file_id": record_file_id,
        }

    conn.commit()
    cur.close()
    conn.close()

    out = repo_root() / "logs" / "fr-b23-seed-fixture.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(created, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK  seeded FR-B23 fixtures → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
