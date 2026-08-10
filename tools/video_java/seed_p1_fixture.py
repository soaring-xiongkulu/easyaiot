#!/usr/bin/env python3
"""Seed or locate Phase 1 certify fixture device + stream-forward task (test-only)."""

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
    return repo_root() / "testdata" / "video-java" / "fixtures" / "vj_p1.json"


def main() -> int:
    fixture_path = load_fixture_path()
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    device_id = fixture["device_id"]
    prefix = fixture["task_name_prefix"]
    source = fixture.get("source") or "file://F:/acme/RUNTIME/testdata/sample.mp4"
    rtmp = fixture.get("rtmp_stream") or "rtmp://127.0.0.1/live/vj_p1"
    http_stream = fixture.get("http_stream") or "http://127.0.0.1:8080/vj_p1"

    conn = psycopg2.connect(db_url())
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute(
        """
        INSERT INTO device (
          id, name, source, rtmp_stream, http_stream, manufacturer, model,
          nvr_channel, auto_snap_enabled, stream, enable_forward
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, 0, false, 0, false)
        ON CONFLICT (id) DO UPDATE SET
          name = EXCLUDED.name,
          source = EXCLUDED.source,
          rtmp_stream = EXCLUDED.rtmp_stream,
          http_stream = EXCLUDED.http_stream,
          enable_forward = false
        """,
        (
            device_id,
            fixture.get("device_name", "vj_p1 certify camera"),
            source,
            rtmp,
            http_stream,
            "certify",
            "fixture",
        ),
    )

    cur.execute(
        """
        SELECT id FROM stream_forward_task
        WHERE task_name LIKE %s
        ORDER BY id DESC LIMIT 1
        """,
        (prefix + "%",),
    )
    row = cur.fetchone()
    if row:
        task_id = int(row["id"])
        print(f"OK  reusing stream_forward_task_id={task_id}")
    else:
        code = f"vj_p1_{uuid.uuid4().hex[:8]}"
        cur.execute(
            """
            INSERT INTO stream_forward_task (
              task_name, task_code, output_format, output_quality,
              status, is_enabled, schedule_policy, prefer_gpu, total_streams
            ) VALUES (%s, %s, 'rtmp', 'high', 0, false, 'local', false, 0)
            RETURNING id
            """,
            (f"{prefix}certify", code),
        )
        task_id = int(cur.fetchone()["id"])
        print(f"OK  created stream_forward_task_id={task_id}")

    cur.execute(
        """
        INSERT INTO stream_forward_task_device (stream_forward_task_id, device_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """,
        (task_id, device_id),
    )
    cur.execute(
        """
        UPDATE stream_forward_task
        SET is_enabled = false,
            schedule_policy = 'local',
            total_streams = 1
        WHERE id = %s
        """,
        (task_id,),
    )
    conn.commit()
    cur.close()
    conn.close()

    fixture["stream_forward_task_id"] = task_id
    fixture_path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK  updated {fixture_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
