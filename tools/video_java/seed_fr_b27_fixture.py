#!/usr/bin/env python3
"""Seed FR-B27 matching Kafka fixture (frb27_device + face/plate libraries + matching task)."""

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

DEVICE_ID = "frb27_device"
TASK_PREFIX = "frb27_match"
FACE_LIB_CODE = "FRB27_FACE"
PLATE_LIB_CODE = "FRB27_PLATE"


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
            "FR-B27 Matching Kafka E2E",
            "file://F:/acme/RUNTIME/testdata/sample.mp4",
            f"rtmp://127.0.0.1/live/{DEVICE_ID}",
            f"http://127.0.0.1:8080/{DEVICE_ID}",
            "fr-b27",
            "matching-kafka-e2e",
        ),
    )


def _ensure_face_library(cur) -> int:
    cur.execute("SELECT id FROM face_library WHERE code = %s LIMIT 1", (FACE_LIB_CODE,))
    row = cur.fetchone()
    if row:
        return int(row["id"])
    cur.execute(
        """
        INSERT INTO face_library (name, code, description, similarity_threshold, is_enabled, face_count)
        VALUES (%s, %s, %s, 0.75, true, 0)
        RETURNING id
        """,
        ("FR-B27 Face Lib", FACE_LIB_CODE, "fr-b27 matching kafka seed"),
    )
    return int(cur.fetchone()["id"])


def _ensure_plate_library(cur) -> int:
    cur.execute("SELECT id FROM plate_library WHERE code = %s LIMIT 1", (PLATE_LIB_CODE,))
    row = cur.fetchone()
    if row:
        return int(row["id"])
    cur.execute(
        """
        INSERT INTO plate_library (name, code, description, is_enabled, plate_count)
        VALUES (%s, %s, %s, true, 0)
        RETURNING id
        """,
        ("FR-B27 Plate Lib", PLATE_LIB_CODE, "fr-b27 matching kafka seed"),
    )
    return int(cur.fetchone()["id"])


def _ensure_matching_task(cur, face_lib_id: int, plate_lib_id: int) -> int:
    cur.execute(
        """
        SELECT id FROM algorithm_task
        WHERE task_name LIKE %s AND task_type = 'realtime'
        ORDER BY id DESC LIMIT 1
        """,
        (TASK_PREFIX + "%",),
    )
    row = cur.fetchone()
    face_ids = json.dumps([face_lib_id])
    plate_ids = json.dumps([plate_lib_id])
    if row:
        task_id = int(row["id"])
    else:
        code = f"frb27_{uuid.uuid4().hex[:8]}"
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
              face_matching_threshold,
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
              true, true,
              true, true,
              %s, %s,
              0.75,
              false, 300,
              25, 0, true, 'stopped', 'local', false,
              0, 0, 0,
              false, false, false, false,
              false, 1, 'full',
              'cpp'
            )
            RETURNING id
            """,
            (f"{TASK_PREFIX}_e2e", code, face_ids, plate_ids),
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
            face_matching_enabled = true,
            plate_matching_enabled = true,
            face_library_ids = %s,
            plate_library_ids = %s,
            face_matching_threshold = 0.75,
            run_status = 'stopped',
            executor = 'cpp'
        WHERE id = %s
        """,
        (face_ids, plate_ids, task_id),
    )
    return task_id


def main() -> int:
    conn = psycopg2.connect(db_url())
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            _ensure_device(cur)
            face_lib_id = _ensure_face_library(cur)
            plate_lib_id = _ensure_plate_library(cur)
            task_id = _ensure_matching_task(cur, face_lib_id, plate_lib_id)
        conn.commit()
        out = {
            "device_id": DEVICE_ID,
            "face_library_id": face_lib_id,
            "plate_library_id": plate_lib_id,
            "matching_task_id": task_id,
            "face_image_path": f"/testdata/fr-b27/media/frb27_face_{DEVICE_ID}.jpg",
            "plate_no": "沪AFRB27",
        }
        path = repo_root() / "logs" / "fr-b27-seed-fixture.json"
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
