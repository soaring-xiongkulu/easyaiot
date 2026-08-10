#!/usr/bin/env python3
"""Seed FR-B26 pure Kafka DVR + Alert Kafka fixture (frb26_device + spaces + alert task)."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("FAIL: psycopg2 required")
    raise SystemExit(1)

DEVICE_ID = "frb26_device"
TASK_PREFIX = "frb26_alert"


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
            "FR-B26 Pure Kafka DVR + Alert E2E",
            "file://F:/acme/RUNTIME/testdata/sample.mp4",
            f"rtmp://127.0.0.1/live/{DEVICE_ID}",
            f"http://127.0.0.1:8080/{DEVICE_ID}",
            "fr-b26",
            "kafka-alert-e2e",
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
        (f"FR-B26 {table}", code, bucket, "fr-b26 pure kafka e2e seed", DEVICE_ID),
    )
    return int(cur.fetchone()["id"])


def _ensure_alert_task(cur) -> int:
    cur.execute(
        """
        SELECT id FROM algorithm_task
        WHERE task_name LIKE %s AND task_type = 'realtime'
        ORDER BY id DESC LIMIT 1
        """,
        (TASK_PREFIX + "%",),
    )
    row = cur.fetchone()
    if row:
        task_id = int(row["id"])
    else:
        code = f"frb26_{uuid.uuid4().hex[:8]}"
        cur.execute(
            """
            INSERT INTO algorithm_task (
              task_name, task_code, task_type, detect_conf,
              tracking_enabled, tracking_similarity_threshold, tracking_max_age,
              tracking_smooth_alpha,
              alert_event_enabled, alert_event_suppress_time,
              face_detection_enabled, plate_detection_enabled,
              face_matching_enabled, plate_matching_enabled,
              alert_notification_enabled, alarm_suppress_time,
              frame_skip, status, is_enabled, run_status, schedule_policy, prefer_gpu,
              total_frames, total_detections, total_captures,
              sam_supplement_enabled, motion_gate_enabled,
              pose_analysis_enabled, pose_intent_enabled,
              post_process_enabled, post_process_replicas, defense_mode,
              executor
            ) VALUES (
              %s, %s, 'realtime', 0.5,
              false, 0.2, 25, 0.25,
              true, 0,
              false, false, false, false,
              false, 300,
              25, 0, true, 'stopped', 'local', false,
              0, 0, 0,
              false, false, false, false,
              false, 1, 'full',
              'cpp'
            )
            RETURNING id
            """,
            (f"{TASK_PREFIX}_e2e", code),
        )
        task_id = int(cur.fetchone()["id"])

    cur.execute(
        """
        INSERT INTO algorithm_task_device (task_id, device_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """,
        (task_id, DEVICE_ID),
    )
    cur.execute(
        """
        UPDATE algorithm_task
        SET is_enabled = true,
            alert_event_enabled = true,
            alert_event_suppress_time = 0,
            run_status = 'stopped',
            executor = 'cpp'
        WHERE id = %s
        """,
        (task_id,),
    )
    return task_id


def main() -> int:
    conn = psycopg2.connect(db_url())
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            _ensure_device(cur)
            snap_id = _ensure_space(cur, "snap_space", "FRB26_SNAP", "snap-space")
            record_id = _ensure_space(cur, "record_space", "FRB26_RECORD", "record-space")
            task_id = _ensure_alert_task(cur)
        conn.commit()
        out = {
            "device_id": DEVICE_ID,
            "snap_space_id": snap_id,
            "record_space_id": record_id,
            "alert_task_id": task_id,
        }
        path = repo_root() / "logs" / "fr-b26-seed-fixture.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print(f"OK seeded {DEVICE_ID} task_id={task_id} -> {path}")
        return 0
    except Exception as e:
        conn.rollback()
        print(f"FAIL: {e}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
