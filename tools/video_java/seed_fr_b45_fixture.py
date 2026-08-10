#!/usr/bin/env python3
"""Seed FR-B45 plate matching→alert fixture (frb45_device + plate library task)."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("FAIL: psycopg2 required")
    raise SystemExit(1)

DEVICE_ID = "frb45_device"
TASK_PREFIX = "frb45_match"
PLATE_LIB_CODE = "FRB45_PLATE"


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
            "FR-B45 Plate Matching Alert E2E",
            "file://F:/acme/RUNTIME/testdata/sample.mp4",
            f"rtmp://127.0.0.1/live/{DEVICE_ID}",
            f"http://127.0.0.1:8080/{DEVICE_ID}",
            "fr-b45",
            "plate-matching-alert-e2e",
        ),
    )


def _ensure_matching_task(cur, plate_lib_id: Optional[int] = None, task_id: Optional[int] = None) -> int:
    plate_ids = json.dumps([plate_lib_id]) if plate_lib_id else "[]"
    if task_id:
        cur.execute(
            """
            UPDATE algorithm_task
            SET is_enabled = true,
                plate_matching_enabled = true,
                plate_library_ids = %s,
                run_status = 'stopped',
                executor = 'cpp'
            WHERE id = %s
            """,
            (plate_ids, task_id),
        )
        return int(task_id)

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
        tid = int(row["id"])
        cur.execute(
            """
            UPDATE algorithm_task
            SET is_enabled = true,
                plate_matching_enabled = true,
                plate_library_ids = %s,
                run_status = 'stopped',
                executor = 'cpp'
            WHERE id = %s
            """,
            (plate_ids, tid),
        )
        return tid

    code = f"frb45_{uuid.uuid4().hex[:8]}"
    cur.execute(
        """
        INSERT INTO algorithm_task (
          task_name, task_code, task_type, detect_conf,
          tracking_enabled, tracking_similarity_threshold, tracking_max_age,
          tracking_smooth_alpha,
          alert_event_enabled, alert_event_suppress_time,
          face_detection_enabled, plate_detection_enabled,
          face_matching_enabled, plate_matching_enabled,
          face_library_ids, plate_library_ids,
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
          false, true,
          false, true,
          '[]', %s,
          false, 300,
          25, 0, true, 'stopped', 'local', false,
          0, 0, 0,
          false, false, false, false,
          false, 1, 'full',
          'cpp'
        )
        RETURNING id
        """,
        (f"{TASK_PREFIX}_e2e", code, plate_ids),
    )
    return int(cur.fetchone()["id"])


def seed_fixture(plate_lib_id: Optional[int] = None, task_id: Optional[int] = None) -> Dict[str, Any]:
    conn = psycopg2.connect(db_url())
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            _ensure_device(cur)
            resolved_task_id = _ensure_matching_task(cur, plate_lib_id=plate_lib_id, task_id=task_id)
            cur.execute(
                """
                INSERT INTO algorithm_task_device (task_id, device_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (resolved_task_id, DEVICE_ID),
            )
        conn.commit()
        return {
            "device_id": DEVICE_ID,
            "task_id": resolved_task_id,
            "plate_lib_id": plate_lib_id,
        }
    finally:
        conn.close()


def main() -> int:
    out = seed_fixture()
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
