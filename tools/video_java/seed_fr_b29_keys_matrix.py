#!/usr/bin/env python3
"""Seed data for FR-B29 keys-matrix deferred item-key probes (Python-first setups)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None  # type: ignore

BASE_URL = os.environ.get("VIDEO_JAVA_BASE_URL", "http://127.0.0.1:48096")
DEVICE_ID = "vj_p2_device"
DB_URL = os.environ.get(
    "VIDEO_JAVA_DB_URL",
    "postgresql://postgres:iot45722414822@127.0.0.1:15432/iot-video20",
)


def _http(
    method: str, path: str, body: Optional[Dict[str, Any]] = None, timeout: float = 12.0
) -> Tuple[int, Dict[str, Any]]:
    url = BASE_URL.rstrip("/") + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8", errors="replace")
    try:
        parsed = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        parsed = {"_raw": raw}
    if not isinstance(parsed, dict):
        parsed = {"data": parsed}
    return status, parsed


def seed_device_location() -> Dict[str, Any]:
    status, body = _http(
        "PUT",
        f"/video/camera/device/{DEVICE_ID}/location",
        {"latitude": 31.2304, "longitude": 121.4737, "address": "fr-b29-keys-matrix-probe"},
    )
    return {
        "step": "device_location",
        "ok": status < 500 and body.get("code") == 0,
        "http_status": status,
        "code": body.get("code"),
        "detail": body.get("msg"),
    }


def seed_nvr() -> Dict[str, Any]:
    status, body = _http(
        "POST",
        "/video/camera/nvr/upsert",
        {"ip": "192.168.1.199", "port": 80, "name": "fr-b29-nvr-probe"},
    )
    return {
        "step": "nvr_upsert",
        "ok": status < 500 and body.get("code") == 0,
        "http_status": status,
        "code": body.get("code"),
        "nvr_id": (body.get("data") or {}).get("id") if isinstance(body.get("data"), dict) else None,
    }


def seed_track_session() -> Dict[str, Any]:
    if psycopg2 is None:
        return {"step": "track_session", "ok": False, "detail": "psycopg2 unavailable"}
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO device_track_session (
                  device_id, title, started_at, point_count, distance_m, source, created_at, updated_at
                ) VALUES (%s, %s, %s, 1, 0, %s, %s, %s)
                RETURNING id
                """,
                (
                    DEVICE_ID,
                    "fr-b29-track-session",
                    datetime.now(timezone.utc),
                    "fr-b29-seed",
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc),
                ),
            )
            row = cur.fetchone()
        conn.close()
        return {"step": "track_session", "ok": True, "session_id": row["id"] if row else None}
    except Exception as exc:
        return {"step": "track_session", "ok": False, "detail": str(exc)}


def _first_library_id(path: str) -> Optional[int]:
    status, body = _http("GET", path)
    if status < 500 and body.get("code") == 0:
        data = body.get("data")
        if isinstance(data, list) and data:
            return int(data[0].get("id"))
    return None


def _ensure_algo_task_id(*, face_library_ids: Optional[list] = None, plate_library_ids: Optional[list] = None) -> Optional[int]:
    body: Dict[str, Any] = {
        "task_name": "fr-b29-matching-probe",
        "task_type": "realtime",
        "device_ids": [DEVICE_ID],
        "is_enabled": False,
        "face_matching_enabled": True,
        "plate_matching_enabled": True,
    }
    if face_library_ids:
        body["face_library_ids"] = face_library_ids
    if plate_library_ids:
        body["plate_library_ids"] = plate_library_ids
    status, resp = _http("POST", "/video/algorithm/task", body)
    if status < 500 and resp.get("code") == 0 and isinstance(resp.get("data"), dict):
        tid = resp["data"].get("id")
        if tid is not None:
            return int(tid)
    status, resp = _http("GET", "/video/algorithm/task/list?pageNo=1&pageSize=5")
    if status < 500 and resp.get("code") == 0:
        data = resp.get("data")
        if isinstance(data, list) and data:
            task_id = int(data[0].get("id"))
            update: Dict[str, Any] = {}
            if face_library_ids:
                update["face_library_ids"] = face_library_ids
            if plate_library_ids:
                update["plate_library_ids"] = plate_library_ids
            if update:
                _http("PUT", f"/video/algorithm/task/{task_id}", update)
            return task_id
    return None


def seed_face_matching_record() -> Dict[str, Any]:
    lib_id = _first_library_id("/video/face/libraries")
    if not lib_id:
        return {"step": "face_matching", "ok": False, "detail": "no face library id"}
    task_id = _ensure_algo_task_id(face_library_ids=[lib_id])
    if not task_id:
        return {"step": "face_matching", "ok": False, "detail": "no algorithm task id"}
    status, body = _http(
        "POST",
        "/video/face/matching/process",
        {
            "taskId": task_id,
            "taskName": "fr-b29-matching-probe",
            "taskType": "realtime",
            "deviceId": DEVICE_ID,
            "deviceName": "P2",
            "faceImagePath": "/testdata/fr-b27/media/frb27_face_frb27_device.jpg",
            "correlationId": "fr-b29-face-matrix-probe",
        },
    )
    return {
        "step": "face_matching_process",
        "ok": status < 500 and body.get("code") == 0,
        "http_status": status,
        "code": body.get("code"),
        "task_id": task_id,
    }


def seed_plate_matching_record() -> Dict[str, Any]:
    lib_id = _first_library_id("/video/plate/libraries")
    if not lib_id:
        return {"step": "plate_matching", "ok": False, "detail": "no plate library id"}
    task_id = _ensure_algo_task_id(plate_library_ids=[lib_id])
    if not task_id:
        return {"step": "plate_matching", "ok": False, "detail": "no algorithm task id"}
    status, body = _http(
        "POST",
        "/video/plate/matching/process",
        {
            "taskId": task_id,
            "taskName": "fr-b29-matching-probe",
            "taskType": "realtime",
            "deviceId": DEVICE_ID,
            "deviceName": "P2",
            "plateNo": "沪AFRB29",
            "plateImagePath": "/testdata/fr-b27/media/frb27_plate_frb27_device.jpg",
            "correlationId": "fr-b29-plate-matrix-probe",
        },
    )
    return {
        "step": "plate_matching_process",
        "ok": status < 500 and body.get("code") == 0,
        "http_status": status,
        "code": body.get("code"),
        "task_id": task_id,
    }


def seed_alert_with_image() -> Dict[str, Any]:
    status, body = _http(
        "POST",
        "/video/alert/hook",
        {
            "device_id": DEVICE_ID,
            "device_name": "P2",
            "object": "person",
            "event": "fr_b29_keys_matrix",
            "region": "gate",
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "image_url": "/api/v1/buckets/field-contract/objects/download?prefix=fr-b29-probe.jpg",
            "correlation_id": "fr-b29-alert-matrix-probe",
        },
    )
    return {
        "step": "alert_hook_image",
        "ok": status < 500 and body.get("code") == 0,
        "http_status": status,
        "code": body.get("code"),
    }


def run_all() -> Dict[str, Any]:
    steps = [
        seed_alert_with_image(),
        seed_device_location(),
        seed_nvr(),
        seed_track_session(),
        seed_face_matching_record(),
        seed_plate_matching_record(),
    ]
    return {
        "base_url": BASE_URL,
        "device_id": DEVICE_ID,
        "steps": steps,
        "ok": all(s.get("ok") for s in steps),
    }


def main() -> int:
    result = run_all()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
