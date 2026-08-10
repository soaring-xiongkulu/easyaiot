#!/usr/bin/env python3
"""Seed or locate Phase 2 certify fixture rows (test-only)."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from bucket_naming import certify_bucket_name

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("FAIL: psycopg2 required (pip install psycopg2-binary)")
    raise SystemExit(1)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def db_url() -> str:
    return os.environ.get(
        "VIDEO_JAVA_DB_URL",
        "postgresql://postgres:iot45722414822@127.0.0.1:15432/iot-video20",
    )


def load_fixture_path() -> Path:
    return repo_root() / "testdata" / "video-java" / "fixtures" / "vj_p2.json"


def _upsert_device(cur, device_id: str, name: str) -> None:
    cur.execute(
        """
        INSERT INTO device (
          id, name, source, rtmp_stream, http_stream, manufacturer, model,
          nvr_channel, auto_snap_enabled, stream, enable_forward
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, 0, false, 0, false)
        ON CONFLICT (id) DO UPDATE SET
          name = EXCLUDED.name,
          source = EXCLUDED.source
        """,
        (
            device_id,
            name,
            "file://F:/acme/RUNTIME/testdata/sample.mp4",
            "rtmp://127.0.0.1/live/vj_p2",
            "http://127.0.0.1:8080/vj_p2",
            "certify",
            "fixture",
        ),
    )


def _ensure_library(cur, table: str, code: str, name: str) -> int:
    cur.execute(f"SELECT id FROM {table} WHERE code = %s", (code,))
    row = cur.fetchone()
    if row:
        return int(row["id"])
    if table == "face_library":
        cur.execute(
            """
            INSERT INTO face_library (
              name, code, description, is_enabled, similarity_threshold, face_count
            ) VALUES (%s, %s, %s, true, 0.55, 0)
            RETURNING id
            """,
            (name, code, "vj_p2 certify fixture"),
        )
    else:
        cur.execute(
            """
            INSERT INTO plate_library (
              name, code, description, is_enabled, plate_count
            ) VALUES (%s, %s, %s, true, 0)
            RETURNING id
            """,
            (name, code, "vj_p2 certify fixture"),
        )
    return int(cur.fetchone()["id"])


def _ensure_task(
    cur,
    *,
    prefix: str,
    suffix: str,
    task_type: str,
    device_id: str,
    extra_updates: str = "",
    extra_params: tuple = (),
) -> int:
    pattern = f"{prefix}{suffix}%"
    cur.execute(
        """
        SELECT id FROM algorithm_task
        WHERE task_name LIKE %s AND task_type = %s
        ORDER BY id DESC LIMIT 1
        """,
        (pattern, task_type),
    )
    row = cur.fetchone()
    if row:
        task_id = int(row["id"])
    else:
        code = f"vj_p2_{uuid.uuid4().hex[:8]}"
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
              executor, patrol_mode, patrol_interval_sec, patrol_pool_size
            ) VALUES (
              %s, %s, %s, 0.5,
              false, 0.2, 25, 0.25,
              true, 5,
              false, false, false, false,
              false, 300,
              25, 0, false, 'stopped', 'local', false,
              0, 0, 0,
              false, false, false, false,
              false, 1, 'full',
              'cpp', 'pool', 10, 4
            )
            RETURNING id
            """,
            (f"{prefix}{suffix}", code, task_type),
        )
        task_id = int(cur.fetchone()["id"])
        print(f"OK  created {suffix} task_id={task_id}")
    cur.execute(
        """
        INSERT INTO algorithm_task_device (task_id, device_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """,
        (task_id, device_id),
    )
    if extra_updates:
        cur.execute(
            f"UPDATE algorithm_task SET {extra_updates} WHERE id = %s",
            (*extra_params, task_id),
        )
    return task_id


def _ensure_space(cur, table: str, code: str, name: str, device_id: str) -> int:
    bucket = certify_bucket_name(code)
    cur.execute(f"SELECT id, bucket_name FROM {table} WHERE space_code = %s", (code,))
    row = cur.fetchone()
    if row:
        space_id = int(row["id"])
        if row.get("bucket_name") != bucket:
            cur.execute(
                f"UPDATE {table} SET bucket_name = %s WHERE id = %s",
                (bucket, space_id),
            )
            print(f"OK  migrated {table} id={space_id} bucket_name -> {bucket}")
        return space_id
    cur.execute(
        f"""
        INSERT INTO {table} (
          space_name, space_code, bucket_name, save_mode, save_time, save_time_custom,
          description, device_id
        ) VALUES (%s, %s, %s, 0, 24, false, %s, %s)
        RETURNING id
        """,
        (name, code, bucket, "vj_p2 certify space", device_id),
    )
    return int(cur.fetchone()["id"])


def _ensure_region(cur, device_id: str) -> int:
    cur.execute(
        """
        SELECT id FROM device_detection_region
        WHERE device_id = %s AND region_name = %s
        ORDER BY id DESC LIMIT 1
        """,
        (device_id, "vj_p2_zone"),
    )
    row = cur.fetchone()
    if row:
        return int(row["id"])
    points = json.dumps([[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]])
    cur.execute(
        """
        INSERT INTO device_detection_region (
          device_id, region_name, region_type, points, color, opacity, is_enabled, sort_order
        ) VALUES (%s, %s, 'polygon', %s, '#FF5252', 0.3, true, 0)
        RETURNING id
        """,
        (device_id, "vj_p2_zone", points),
    )
    return int(cur.fetchone()["id"])


def main() -> int:
    fixture_path = load_fixture_path()
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    device_id = fixture["device_id"]
    prefix = fixture["task_name_prefix"]

    conn = psycopg2.connect(db_url())
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    _upsert_device(cur, device_id, fixture.get("device_name", "vj_p2 certify camera"))

    face_library_id = _ensure_library(
        cur, "face_library", fixture["face_library_code"], "vj_p2 face lib"
    )
    plate_library_id = _ensure_library(
        cur, "plate_library", fixture["plate_library_code"], "vj_p2 plate lib"
    )

    face_task_id = _ensure_task(
        cur,
        prefix=prefix,
        suffix="face_match",
        task_type="realtime",
        device_id=device_id,
        extra_updates=(
            "face_matching_enabled = true, face_library_ids = %s, "
            "alert_event_enabled = false, "
            "is_enabled = false, run_status = 'stopped'"
        ),
        extra_params=(json.dumps([face_library_id]),),
    )
    plate_task_id = _ensure_task(
        cur,
        prefix=prefix,
        suffix="plate_match",
        task_type="realtime",
        device_id=device_id,
        extra_updates=(
            "plate_matching_enabled = true, plate_library_ids = %s, "
            "alert_event_enabled = false, "
            "is_enabled = false, run_status = 'stopped'"
        ),
        extra_params=(json.dumps([plate_library_id]),),
    )
    post_process_task_id = _ensure_task(
        cur,
        prefix=prefix,
        suffix="post_process",
        task_type="realtime",
        device_id=device_id,
        extra_updates=(
            "post_process_enabled = true, post_process_script = %s, "
            "alert_event_enabled = true, "
            "is_enabled = true, run_status = 'stopped'"
        ),
        extra_params=("post_process.py",),
    )
    patrol_task_id = _ensure_task(
        cur,
        prefix=prefix,
        suffix="patrol",
        task_type="patrol",
        device_id=device_id,
        extra_updates="is_enabled = false, run_status = 'stopped'",
    )

    snap_space_id = _ensure_space(
        cur, "snap_space", fixture["snap_space_code"], "vj_p2 snap", device_id
    )
    record_space_id = _ensure_space(
        cur, "record_space", fixture["record_space_code"], "vj_p2 record", device_id
    )
    region_id = _ensure_region(cur, device_id)

    conn.commit()
    cur.close()
    conn.close()

    fixture["face_library_id"] = face_library_id
    fixture["plate_library_id"] = plate_library_id
    fixture["face_task_id"] = face_task_id
    fixture["plate_task_id"] = plate_task_id
    fixture["post_process_task_id"] = post_process_task_id
    fixture["patrol_task_id"] = patrol_task_id
    fixture["snap_space_id"] = snap_space_id
    fixture["record_space_id"] = record_space_id
    fixture["detection_region_id"] = region_id
    hook = fixture.get("media_hook_payload") or {}
    hook["task_id"] = face_task_id
    hook["space_id"] = snap_space_id
    fixture["media_hook_payload"] = hook
    alert = fixture.get("alert_hook_payload") or {}
    alert["task_id"] = post_process_task_id
    fixture["alert_hook_payload"] = alert

    fixture_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK  updated {fixture_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
