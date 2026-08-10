#!/usr/bin/env python3
"""Seed or locate Phase 0 certify fixture task (test-only)."""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

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
    return repo_root() / "testdata" / "video-java" / "fixtures" / "vj_p0.json"


def stub_runtime_path() -> str:
    return str((repo_root() / "tools" / "video_java" / "stub_runtime.bat").resolve())


def main() -> int:
    fixture_path = load_fixture_path()
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    device_id = fixture["device_id"]
    prefix = fixture["task_name_prefix"]

    conn = psycopg2.connect(db_url())
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute(
        """
        INSERT INTO device (
          id, name, source, rtmp_stream, http_stream, manufacturer, model,
          nvr_channel, auto_snap_enabled, stream
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, 0, false, 0)
        ON CONFLICT (id) DO UPDATE SET
          name = EXCLUDED.name,
          source = EXCLUDED.source
        """,
        (
            device_id,
            "vj_p0 certify camera",
            "file://F:/acme/RUNTIME/testdata/sample.mp4",
            "rtmp://127.0.0.1/live/vj_p0",
            "http://127.0.0.1:8080/vj_p0",
            "certify",
            "fixture",
        ),
    )

    cur.execute(
        """
        SELECT id FROM algorithm_task
        WHERE task_name LIKE %s AND executor = 'cpp' AND task_type = 'realtime'
        ORDER BY id DESC LIMIT 1
        """,
        (prefix + "%",),
    )
    row = cur.fetchone()
    if row:
        task_id = int(row["id"])
        print(f"OK  reusing task_id={task_id}")
    else:
        code = f"vj_p0_{uuid.uuid4().hex[:8]}"
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
              true, 5,
              false, false, false, false,
              false, 300,
              25, 0, false, 'stopped', 'local', false,
              0, 0, 0,
              false, false, false, false,
              false, 1, 'full',
              'cpp'
            )
            RETURNING id
            """,
            (f"{prefix}certify", code),
        )
        task_id = int(cur.fetchone()["id"])
        print(f"OK  created task_id={task_id}")

    cur.execute(
        """
        INSERT INTO algorithm_task_device (task_id, device_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """,
        (task_id, device_id),
    )
    cur.execute(
        """
        UPDATE algorithm_task
        SET is_enabled = true,
            run_status = 'stopped',
            executor = 'cpp',
            alert_event_enabled = true,
            runtime_bin_path = %s
        WHERE id = %s
        """,
        (stub_runtime_path(), task_id),
    )
    conn.commit()
    cur.close()
    conn.close()

    fixture["task_id"] = task_id
    fixture["runtime_bin_path"] = stub_runtime_path()
    fixture_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK  updated {fixture_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
