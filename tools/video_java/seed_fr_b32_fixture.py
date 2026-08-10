#!/usr/bin/env python3
"""Seed FR-B32 fixture: frb32_device tiny quota + binary GET probe assets."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("FAIL: psycopg2 required")
    raise SystemExit(1)

DEVICE_ID = "frb32_device"
SNAP_BUCKET = "snap-space"
RECORD_BUCKET = "record-space"
# Tiny quota so 5×100B objects exceed 50% threshold (Python check_and_cleanup_storage L171-180).
SNAP_MAX_BYTES = 500
THRESHOLD = 0.5
CLEANUP_RATIO = 0.5


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
            "FR-B32 Cleanup + Binary GET E2E",
            "file://F:/acme/RUNTIME/testdata/sample.mp4",
            f"rtmp://127.0.0.1/live/{DEVICE_ID}",
            f"http://127.0.0.1:8080/{DEVICE_ID}",
            "fr-b32",
            "cleanup-binary-e2e",
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
        (f"FR-B32 {table}", code, bucket, "fr-b32 cleanup/binary e2e seed", DEVICE_ID),
    )
    return int(cur.fetchone()["id"])


def _ensure_storage_config(cur) -> None:
    cur.execute(
        """
        INSERT INTO device_storage_config (
          device_id,
          snap_storage_bucket, snap_storage_max_size,
          snap_storage_cleanup_enabled, snap_storage_cleanup_threshold, snap_storage_cleanup_ratio,
          video_storage_bucket, video_storage_max_size,
          video_storage_cleanup_enabled, video_storage_cleanup_threshold, video_storage_cleanup_ratio
        ) VALUES (%s, %s, %s, true, %s, %s, %s, %s, true, %s, %s)
        ON CONFLICT (device_id) DO UPDATE SET
          snap_storage_bucket = EXCLUDED.snap_storage_bucket,
          snap_storage_max_size = EXCLUDED.snap_storage_max_size,
          snap_storage_cleanup_enabled = EXCLUDED.snap_storage_cleanup_enabled,
          snap_storage_cleanup_threshold = EXCLUDED.snap_storage_cleanup_threshold,
          snap_storage_cleanup_ratio = EXCLUDED.snap_storage_cleanup_ratio,
          video_storage_bucket = EXCLUDED.video_storage_bucket,
          video_storage_max_size = EXCLUDED.video_storage_max_size,
          updated_at = NOW()
        """,
        (
            DEVICE_ID,
            SNAP_BUCKET,
            SNAP_MAX_BYTES,
            THRESHOLD,
            CLEANUP_RATIO,
            RECORD_BUCKET,
            SNAP_MAX_BYTES,
            THRESHOLD,
            CLEANUP_RATIO,
        ),
    )


def _ensure_patrol_session(cur) -> int:
    cur.execute("SELECT id FROM patrol_session WHERE session_name = %s LIMIT 1", ("fr-b32-patrol-sse",))
    row = cur.fetchone()
    if row:
        return int(row["id"])
    cur.execute(
        """
        INSERT INTO patrol_session (
          session_name, patrol_mode, interval_sec, pool_size,
          device_ids, model_ids, status,
          alert_event_enabled, alert_event_suppress_time,
          face_detection_enabled, plate_detection_enabled,
          total_patrols, total_detections,
          created_at, updated_at
        ) VALUES (%s, 'pool', 10, 2, %s, %s, 'stopped', true, 5, true, true, 0, 0, NOW(), NOW())
        RETURNING id
        """,
        ("fr-b32-patrol-sse", json.dumps([DEVICE_ID]), json.dumps([])),
    )
    return int(cur.fetchone()["id"])


def _ensure_playback(cur) -> int:
    cur.execute(
        "SELECT id FROM playback WHERE device_id = %s AND file_path LIKE %s LIMIT 1",
        (DEVICE_ID, "%fr-b32%"),
    )
    row = cur.fetchone()
    if row:
        return int(row["id"])
    thumb = str(repo_root() / "testdata" / "fr-b32" / "probe-thumb.jpg")
    cur.execute(
        """
        INSERT INTO playback (
          device_id, device_name, file_path, thumbnail_path, file_size, duration,
          event_time, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, 128, 0, NOW(), NOW(), NOW())
        RETURNING id
        """,
        (DEVICE_ID, "FR-B32 Playback Probe", "fr-b32/playback-probe.mp4", thumb),
    )
    return int(cur.fetchone()["id"])


def _write_local_probe_files() -> dict:
    probe_dir = repo_root() / "testdata" / "fr-b32"
    probe_dir.mkdir(parents=True, exist_ok=True)
    image_path = probe_dir / "probe-alert.jpg"
    record_path = probe_dir / "probe-alert.mp4"
    thumb_path = probe_dir / "probe-thumb.jpg"
    snap_local = probe_dir / "probe-snap.jpg"
    record_local = probe_dir / "probe-record.mp4"
    # Minimal JPEG / MP4-ish bytes for content-type probes (not valid media, enough for send_file).
    image_bytes = b"\xff\xd8\xff\xe0frb32_alert_image_probe" + b"\xff\xd9"
    record_bytes = b"\x00\x00\x00\x20ftypmp41frb32_alert_record_probe"
    for path, payload in (
        (image_path, image_bytes),
        (record_path, record_bytes),
        (thumb_path, image_bytes),
        (snap_local, image_bytes),
        (record_local, record_bytes),
    ):
        path.write_bytes(payload)
    def fwd(p: Path) -> str:
        return str(p).replace("\\", "/")
    return {
        "alert_image_path": fwd(image_path),
        "alert_record_path": fwd(record_path),
        "playback_thumbnail_path": fwd(thumb_path),
        "snap_local_path": fwd(snap_local),
        "record_local_path": fwd(record_local),
    }


def _ensure_snap_image_row(cur, space_id: int, paths: dict) -> str:
    object_name = "fr-b32-snap-probe.jpg"
    cur.execute("DELETE FROM snap_image WHERE space_id = %s AND object_name = %s", (space_id, object_name))
    cur.execute(
        """
        INSERT INTO snap_image (
          space_id, device_id, object_name, bucket_name, filename, file_size,
          content_type, etag, url, captured_at, source, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, NOW())
        """,
        (
            space_id,
            DEVICE_ID,
            object_name,
            SNAP_BUCKET,
            "fr-b32-snap-probe.jpg",
            64,
            "image/jpeg",
            "fr-b32-etag",
            paths["snap_local_path"],
            "fr-b32-seed",
        ),
    )
    return object_name


def _ensure_record_file_row(cur, space_id: int, paths: dict) -> str:
    object_name = "fr-b32-record-probe.mp4"
    cur.execute("DELETE FROM record_file WHERE space_id = %s AND object_name = %s", (space_id, object_name))
    cur.execute(
        """
        INSERT INTO record_file (
          space_id, device_id, object_name, bucket_name, filename, file_size,
          content_type, etag, url, duration, event_time, source, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0, NOW(), %s, NOW(), NOW())
        """,
        (
            space_id,
            DEVICE_ID,
            object_name,
            RECORD_BUCKET,
            "fr-b32-record-probe.mp4",
            64,
            "video/mp4",
            "fr-b32-etag",
            paths["record_local_path"],
            "fr-b32-seed",
        ),
    )
    return object_name


def main() -> int:
    paths = _write_local_probe_files()
    conn = psycopg2.connect(db_url())
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            _ensure_device(cur)
            snap_id = _ensure_space(cur, "snap_space", "FRB32_SNAP", SNAP_BUCKET)
            record_id = _ensure_space(cur, "record_space", "FRB32_RECORD", RECORD_BUCKET)
            _ensure_storage_config(cur)
            patrol_session_id = _ensure_patrol_session(cur)
            playback_id = _ensure_playback(cur)
            snap_object = _ensure_snap_image_row(cur, snap_id, paths)
            record_object = _ensure_record_file_row(cur, record_id, paths)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    artifact = {
        "device_id": DEVICE_ID,
        "snap_space_id": snap_id,
        "record_space_id": record_id,
        "patrol_session_id": patrol_session_id,
        "playback_id": playback_id,
        "snap_storage_max_size": SNAP_MAX_BYTES,
        "snap_storage_cleanup_threshold": THRESHOLD,
        "snap_storage_cleanup_ratio": CLEANUP_RATIO,
        "snap_object_prefix": f"{DEVICE_ID}/",
        "snap_probe_object": snap_object,
        "record_probe_object": record_object,
        "seeded_at": datetime.now(timezone.utc).isoformat(),
        **paths,
    }
    out = repo_root() / "logs" / "fr-b32-seed-fixture.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK seed fixture -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
