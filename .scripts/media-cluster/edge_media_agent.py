#!/usr/bin/env python3
"""Lightweight edge-local DVR index, report spool and authenticated playback API.

The media node intentionally does not need the full VIDEO image.  SRS writes
segments to the node disk and calls this process; metadata is durably queued in
SQLite and reported to the control plane.  Playback supports HTTP Range so the
control plane can proxy seekable recordings from private edge networks.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import mimetypes
import os
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.client import HTTPConnection, HTTPSConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


LOG = logging.getLogger("easyaiot.edge_media_agent")
MAX_BODY = 2 * 1024 * 1024
SRS_CONTAINER_ROOT = "/mnt/easyaiot-media"


def load_env_file(path: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as env_file:
            for raw in env_file:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except FileNotFoundError:
        return


load_env_file(os.getenv("EDGE_MEDIA_ENV_FILE", "/opt/easyaiot/media-cluster/recording-storage.env"))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


class EdgeMediaStore:
    def __init__(self, root: str, db_path: str | None = None):
        self.root = Path(root).expanduser().resolve()
        self.state_dir = self.root / ".state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = str(Path(db_path).resolve()) if db_path else str(self.state_dir / "edge-media.db")
        self._lock = threading.RLock()
        self._init_schema()

    def connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS media_asset_spool (
                    asset_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    task_id TEXT,
                    file_path TEXT NOT NULL,
                    object_key TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_ms INTEGER,
                    file_size INTEGER NOT NULL,
                    content_type TEXT,
                    report_state TEXT NOT NULL DEFAULT 'pending',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    next_attempt_at REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_edge_spool_pending "
                "ON media_asset_spool(report_state, next_attempt_at)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_report_spool (
                    correlation_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    next_attempt_at REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_upload_spool (
                    asset_id TEXT PRIMARY KEY,
                    local_path TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    upload_state TEXT NOT NULL DEFAULT 'pending',
                    delete_after_upload INTEGER NOT NULL DEFAULT 0,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    next_attempt_at REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_clip_spool (
                    correlation_id TEXT PRIMARY KEY,
                    asset_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    task_id TEXT,
                    event_time TEXT NOT NULL,
                    pre_seconds INTEGER NOT NULL,
                    post_seconds INTEGER NOT NULL,
                    due_at REAL NOT NULL,
                    clip_state TEXT NOT NULL DEFAULT 'pending',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def resolve_srs_path(self, raw_path: str) -> Path:
        if not raw_path:
            raise ValueError("DVR hook missing file_path")
        raw = Path(raw_path)
        if raw.is_absolute() and str(raw).startswith(SRS_CONTAINER_ROOT + os.sep):
            raw = self.root / raw.relative_to(SRS_CONTAINER_ROOT)
        elif not raw.is_absolute():
            raw = self.root / raw
        resolved = raw.expanduser().resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("DVR path escapes edge recording root") from exc
        if not resolved.is_file():
            raise FileNotFoundError(str(resolved))
        return resolved

    def resolve_event_path(self, raw_path: str) -> Path:
        if not raw_path:
            raise ValueError("alert hook missing image_path")
        raw = Path(raw_path)
        if raw.is_absolute() and str(raw).startswith(SRS_CONTAINER_ROOT + os.sep):
            raw = self.root / raw.relative_to(SRS_CONTAINER_ROOT)
        elif not raw.is_absolute():
            raw = self.root / raw
        resolved = raw.expanduser().resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("alert image path escapes edge recording root") from exc
        if not resolved.is_file():
            raise FileNotFoundError(str(resolved))
        return resolved

    @staticmethod
    def _checksum(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as media_file:
            for chunk in iter(lambda: media_file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def enqueue_alert(
        self,
        event: dict,
        node_id: int,
        generation: int,
        pre_seconds: int,
        post_seconds: int,
        clip_settle_seconds: int,
    ) -> dict:
        device_id = str(event.get("device_id") or "").strip()
        event_time = str(event.get("time") or event.get("timestamp") or "").strip()
        if not device_id or not event_time:
            raise ValueError("alert hook missing device_id/time")
        correlation_id = str(
            event.get("correlation_id") or event.get("correlationId")
            or event.get("event_id") or event.get("eventId") or uuid.uuid4()
        ).strip()
        payload = dict(event)
        payload["correlation_id"] = correlation_id
        # 边缘绝对路径不能进入中心库；图片/录像只通过资产上传完成回调关联。
        payload["image_path"] = None
        payload["image_url"] = None
        payload["record_path"] = None
        now = iso_time(utc_now())
        image_asset_id = None
        clip_asset_id = None
        with self._lock, self.connect() as conn:
            conn.execute(
                """
                INSERT INTO event_report_spool(
                    correlation_id, payload_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(correlation_id) DO UPDATE SET
                    payload_json=excluded.payload_json, next_attempt_at=0,
                    last_error=NULL, updated_at=excluded.updated_at
                """,
                (correlation_id, json.dumps(payload, ensure_ascii=False), now, now),
            )

            image_path_raw = str(event.get("image_path") or "").strip()
            if image_path_raw:
                try:
                    image_path = self.resolve_event_path(image_path_raw)
                    image_asset_id = str(uuid.uuid5(
                        uuid.NAMESPACE_URL, f"easyaiot:alert-image:{node_id}:{correlation_id}"
                    ))
                    content_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
                    upload = {
                        "asset_id": image_asset_id,
                        "asset_type": "alert_image",
                        "device_id": device_id,
                        "task_id": event.get("task_id") or event.get("taskId"),
                        "filename": image_path.name,
                        "event_time": event_time,
                        "start_time": event_time,
                        "file_size": image_path.stat().st_size,
                        "content_type": content_type,
                        "checksum": self._checksum(image_path),
                        "correlation_id": correlation_id,
                    }
                    conn.execute(
                        """
                        INSERT INTO event_upload_spool(
                            asset_id, local_path, payload_json, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(asset_id) DO UPDATE SET
                            local_path=excluded.local_path, payload_json=excluded.payload_json,
                            next_attempt_at=0, last_error=NULL, updated_at=excluded.updated_at
                        """,
                        (image_asset_id, str(image_path), json.dumps(upload, ensure_ascii=False), now, now),
                    )
                except (ValueError, FileNotFoundError, OSError) as exc:
                    LOG.warning(
                        "alert image skipped correlation=%s path=%s: %s",
                        correlation_id, image_path_raw, exc,
                    )

            task_type = str(event.get("task_type") or "realtime").strip().lower()
            if task_type not in ("snap", "snapshot"):
                clip_asset_id = str(uuid.uuid5(
                    uuid.NAMESPACE_URL, f"easyaiot:event-clip:{node_id}:{correlation_id}"
                ))
                conn.execute(
                    """
                    INSERT INTO event_clip_spool(
                        correlation_id, asset_id, device_id, task_id, event_time,
                        pre_seconds, post_seconds, due_at, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(correlation_id) DO UPDATE SET
                        device_id=excluded.device_id, task_id=excluded.task_id,
                        event_time=excluded.event_time, pre_seconds=excluded.pre_seconds,
                        post_seconds=excluded.post_seconds,
                        due_at=CASE WHEN event_clip_spool.clip_state='ready'
                            THEN event_clip_spool.due_at ELSE excluded.due_at END,
                        updated_at=excluded.updated_at
                    """,
                    (
                        correlation_id, clip_asset_id, device_id,
                        str(event.get("task_id") or event.get("taskId") or "") or None,
                        event_time, max(0, pre_seconds), max(0, post_seconds),
                        time.time() + max(0, post_seconds) + max(1, clip_settle_seconds), now, now,
                    ),
                )
        return {
            "correlation_id": correlation_id,
            "image_asset_id": image_asset_id,
            "clip_asset_id": clip_asset_id,
        }

    def add_dvr(self, event: dict, node_id: int, generation: int) -> dict:
        stream = str(event.get("device_id") or event.get("stream") or "").strip()
        if not stream:
            raise ValueError("DVR hook missing stream/device_id")
        file_path = self.resolve_srs_path(str(event.get("file_path") or event.get("file") or ""))
        stat = file_path.stat()
        try:
            duration_seconds = max(0.0, float(event.get("duration") or event.get("dvr_duration") or 0))
        except (TypeError, ValueError):
            duration_seconds = 0.0
        duration_ms = int(round(duration_seconds * 1000)) if duration_seconds else None
        file_completed_at = datetime.fromtimestamp(stat.st_mtime, timezone.utc)
        start = file_completed_at - timedelta(milliseconds=duration_ms) if duration_ms else file_completed_at
        end = file_completed_at if duration_ms else None
        asset_id = str(uuid.uuid4())
        object_key = file_path.relative_to(self.root).as_posix()
        content_type = mimetypes.guess_type(file_path.name)[0] or (
            "video/x-flv" if file_path.suffix.lower() == ".flv" else "video/mp4"
        )
        now = iso_time(utc_now())
        row = {
            "asset_id": asset_id,
            "asset_type": "recording_segment",
            "device_id": stream,
            "task_id": event.get("task_id"),
            "source_node_id": node_id,
            "storage_node_id": node_id,
            "storage_generation": generation,
            "storage_scope": "edge",
            "storage_backend": "local",
            "object_key": object_key,
            "status": "ready",
            "start_time": iso_time(start),
            "end_time": iso_time(end) if end else None,
            "duration_ms": duration_ms,
            "file_size": stat.st_size,
            "content_type": content_type,
        }
        with self._lock, self.connect() as conn:
            conn.execute(
                """
                INSERT INTO media_asset_spool(
                    asset_id, device_id, task_id, file_path, object_key, start_time,
                    end_time, duration_ms, file_size, content_type, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset_id, stream, str(event.get("task_id")) if event.get("task_id") is not None else None,
                    str(file_path), object_key, row["start_time"], row["end_time"], duration_ms,
                    stat.st_size, content_type, now, now,
                ),
            )
        return row

    def pending(self, limit: int = 100) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM media_asset_spool WHERE report_state != 'reported' "
                "AND next_attempt_at <= ? ORDER BY created_at LIMIT ?",
                (time.time(), limit),
            ).fetchall()

    def as_report(self, row: sqlite3.Row, node_id: int, generation: int) -> dict:
        return {
            "asset_id": row["asset_id"],
            "asset_type": "recording_segment",
            "device_id": row["device_id"],
            "task_id": row["task_id"],
            "source_node_id": node_id,
            "storage_node_id": node_id,
            "storage_generation": generation,
            "storage_scope": "edge",
            "storage_backend": "local",
            "object_key": row["object_key"],
            "status": "ready",
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "duration_ms": row["duration_ms"],
            "file_size": row["file_size"],
            "content_type": row["content_type"],
        }

    def mark_reported(self, asset_ids: list[str]):
        if not asset_ids:
            return
        now = iso_time(utc_now())
        with self._lock, self.connect() as conn:
            conn.executemany(
                "UPDATE media_asset_spool SET report_state='reported', last_error=NULL, updated_at=? "
                "WHERE asset_id=?",
                [(now, asset_id) for asset_id in asset_ids],
            )

    def mark_failed(self, rows: list[sqlite3.Row], error: str):
        now = iso_time(utc_now())
        with self._lock, self.connect() as conn:
            for row in rows:
                attempts = int(row["attempts"] or 0) + 1
                delay = min(300, 2 ** min(attempts, 8))
                conn.execute(
                    "UPDATE media_asset_spool SET report_state='pending', attempts=?, last_error=?, "
                    "next_attempt_at=?, updated_at=? WHERE asset_id=?",
                    (attempts, error[:1000], time.time() + delay, now, row["asset_id"]),
                )

    def asset(self, asset_id: str):
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM media_asset_spool WHERE asset_id=?", (asset_id,)
            ).fetchone()

    def pending_event_reports(self, limit: int = 100) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM event_report_spool WHERE next_attempt_at <= ? "
                "ORDER BY created_at LIMIT ?", (time.time(), limit),
            ).fetchall()

    def mark_events_reported(self, correlation_ids: list[str]):
        if not correlation_ids:
            return
        with self._lock, self.connect() as conn:
            conn.executemany(
                "DELETE FROM event_report_spool WHERE correlation_id=?",
                [(value,) for value in correlation_ids],
            )

    def mark_events_failed(self, rows: list[sqlite3.Row], error: str):
        now = iso_time(utc_now())
        with self._lock, self.connect() as conn:
            for row in rows:
                attempts = int(row["attempts"] or 0) + 1
                delay = min(300, 2 ** min(attempts, 8))
                conn.execute(
                    "UPDATE event_report_spool SET attempts=?, last_error=?, next_attempt_at=?, "
                    "updated_at=? WHERE correlation_id=?",
                    (attempts, error[:1000], time.time() + delay, now, row["correlation_id"]),
                )

    def pending_uploads(self, limit: int = 20) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM event_upload_spool WHERE next_attempt_at <= ? "
                "ORDER BY created_at LIMIT ?", (time.time(), limit),
            ).fetchall()

    def mark_upload_state(self, asset_id: str, state: str):
        with self._lock, self.connect() as conn:
            conn.execute(
                "UPDATE event_upload_spool SET upload_state=?, last_error=NULL, updated_at=? "
                "WHERE asset_id=?", (state, iso_time(utc_now()), asset_id),
            )

    def mark_upload_complete(self, row: sqlite3.Row):
        with self._lock, self.connect() as conn:
            conn.execute("DELETE FROM event_upload_spool WHERE asset_id=?", (row["asset_id"],))
            conn.execute("DELETE FROM event_clip_spool WHERE asset_id=?", (row["asset_id"],))
        if int(row["delete_after_upload"] or 0):
            try:
                Path(row["local_path"]).unlink()
            except FileNotFoundError:
                pass

    def mark_upload_failed(self, row: sqlite3.Row, error: str):
        attempts = int(row["attempts"] or 0) + 1
        delay = min(300, 2 ** min(attempts, 8))
        with self._lock, self.connect() as conn:
            conn.execute(
                "UPDATE event_upload_spool SET attempts=?, last_error=?, next_attempt_at=?, "
                "updated_at=? WHERE asset_id=?",
                (attempts, error[:1000], time.time() + delay, iso_time(utc_now()), row["asset_id"]),
            )

    def due_clip_jobs(self, limit: int = 5) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM event_clip_spool WHERE clip_state='pending' AND due_at <= ? "
                "ORDER BY due_at LIMIT ?", (time.time(), limit),
            ).fetchall()

    def recording_segments(self, device_id: str) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM media_asset_spool WHERE device_id=? ORDER BY start_time",
                (device_id,),
            ).fetchall()

    def enqueue_clip_upload(self, job: sqlite3.Row, path: Path, payload: dict):
        now = iso_time(utc_now())
        with self._lock, self.connect() as conn:
            conn.execute(
                """
                INSERT INTO event_upload_spool(
                    asset_id, local_path, payload_json, delete_after_upload, created_at, updated_at
                ) VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET
                    local_path=excluded.local_path, payload_json=excluded.payload_json,
                    next_attempt_at=0, last_error=NULL, updated_at=excluded.updated_at
                """,
                (job["asset_id"], str(path), json.dumps(payload, ensure_ascii=False), now, now),
            )
            conn.execute(
                "UPDATE event_clip_spool SET clip_state='ready', last_error=NULL, updated_at=? "
                "WHERE correlation_id=?", (now, job["correlation_id"]),
            )

    def mark_clip_failed(self, job: sqlite3.Row, error: str):
        attempts = int(job["attempts"] or 0) + 1
        with self._lock, self.connect() as conn:
            conn.execute(
                "UPDATE event_clip_spool SET attempts=?, last_error=?, due_at=?, updated_at=? "
                "WHERE correlation_id=?",
                (
                    attempts, error[:1000], time.time() + min(300, 2 ** min(attempts, 8)),
                    iso_time(utc_now()), job["correlation_id"],
                ),
            )

    def status(self) -> dict:
        with self.connect() as conn:
            counts = {
                row["report_state"]: row["count"]
                for row in conn.execute(
                    "SELECT report_state, COUNT(*) AS count FROM media_asset_spool GROUP BY report_state"
                )
            }
            event_pending = conn.execute("SELECT COUNT(*) FROM event_report_spool").fetchone()[0]
            upload_pending = conn.execute("SELECT COUNT(*) FROM event_upload_spool").fetchone()[0]
            clip_pending = conn.execute(
                "SELECT COUNT(*) FROM event_clip_spool WHERE clip_state='pending'"
            ).fetchone()[0]
        return {
            "asset_reports": counts,
            "event_reports_pending": event_pending,
            "event_uploads_pending": upload_pending,
            "event_clips_pending": clip_pending,
            "database": self.db_path,
        }


class EdgeMediaAgent:
    def __init__(self):
        self.root = os.path.realpath(os.path.expanduser(
            os.getenv("EDGE_RECORDING_ROOT") or os.getenv("MEDIA_HOST_DATA_ROOT") or "/data/local-storage"
        ))
        self.node_id = int(os.getenv("COMPUTE_NODE_ID") or os.getenv("NODE_ID") or 0)
        self.generation = int(os.getenv("RECORDING_STORAGE_GENERATION") or 1)
        self.token = (os.getenv("MEDIA_INTERNAL_TOKEN") or "").strip()
        self.report_url = (os.getenv("MEDIA_ASSET_REPORT_URL") or "").strip()
        if self.node_id <= 0:
            raise RuntimeError("COMPUTE_NODE_ID is required")
        if not self.token:
            raise RuntimeError("MEDIA_INTERNAL_TOKEN is required")
        if not self.report_url:
            raise RuntimeError("MEDIA_ASSET_REPORT_URL is required")
        self.store = EdgeMediaStore(self.root)
        self.event_report_url = self.report_url.replace(
            "/assets/report-batch", "/events/report-batch"
        )
        self.upload_ticket_url = self.report_url.rsplit("/", 1)[0] + "/upload-ticket"
        self.upload_complete_url = self.report_url.rsplit("/", 1)[0] + "/upload-complete"
        self.event_pre_seconds = max(0, int(os.getenv("EDGE_EVENT_PRE_SECONDS") or 10))
        self.event_post_seconds = max(0, int(os.getenv("EDGE_EVENT_POST_SECONDS") or 10))
        self.clip_settle_seconds = max(1, int(os.getenv("EDGE_EVENT_CLIP_SETTLE_SECONDS") or 5))
        self._event_flush_lock = threading.Lock()

    def authorized(self, headers, asset_id: str | None = None, query: dict | None = None) -> bool:
        provided = (headers.get("X-Media-Internal-Token") or "").strip()
        if provided and hmac.compare_digest(self.token, provided):
            return True
        if not asset_id or not query:
            return False
        try:
            expires = int((query.get("expires") or ["0"])[0])
        except (TypeError, ValueError):
            return False
        now = int(time.time())
        if expires < now or expires > now + 600:
            return False
        supplied = str((query.get("signature") or [""])[0])
        expected = hmac.new(
            self.token.encode("utf-8"), f"{asset_id}:{expires}".encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return bool(supplied and hmac.compare_digest(expected, supplied))

    def flush(self) -> dict:
        rows = self.store.pending()
        if not rows:
            return {"attempted": 0, "reported": 0, "pending": 0}
        items = [self.store.as_report(row, self.node_id, self.generation) for row in rows]
        body = json.dumps({"items": items}, ensure_ascii=False).encode("utf-8")
        request = Request(
            self.report_url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-Media-Internal-Token": self.token,
                "X-Node-Id": str(self.node_id),
            },
        )
        try:
            with urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8") or "{}")
                if response.status < 200 or response.status >= 300 or payload.get("code") != 0:
                    raise RuntimeError(f"report rejected: http={response.status} body={payload}")
            self.store.mark_reported([row["asset_id"] for row in rows])
            return {"attempted": len(rows), "reported": len(rows), "pending": 0}
        except (HTTPError, URLError, OSError, ValueError, RuntimeError) as exc:
            self.store.mark_failed(rows, str(exc))
            LOG.warning("asset report retained for retry: %s", exc)
            return {"attempted": len(rows), "reported": 0, "pending": len(rows), "error": str(exc)}

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "X-Media-Internal-Token": self.token,
            "X-Node-Id": str(self.node_id),
        }

    def _post_json(self, url: str, payload: dict, timeout: int = 15) -> dict:
        request = Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers=self._headers(),
        )
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8") or "{}")
            if response.status < 200 or response.status >= 300 or result.get("code") != 0:
                raise RuntimeError(f"request rejected: http={response.status} body={result}")
            return result

    @staticmethod
    def _put_file(upload_url: str, path: Path, content_type: str):
        parsed = urlparse(upload_url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("upload ticket contains invalid URL")
        connection_cls = HTTPSConnection if parsed.scheme == "https" else HTTPConnection
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        connection = connection_cls(parsed.hostname, port, timeout=120)
        target = parsed.path or "/"
        if parsed.query:
            target += "?" + parsed.query
        try:
            size = path.stat().st_size
            connection.putrequest("PUT", target, skip_host=True)
            connection.putheader("Host", parsed.netloc)
            connection.putheader("Content-Type", content_type or "application/octet-stream")
            connection.putheader("Content-Length", str(size))
            connection.endheaders()
            with path.open("rb") as media_file:
                for chunk in iter(lambda: media_file.read(1024 * 1024), b""):
                    connection.send(chunk)
            response = connection.getresponse()
            response_body = response.read(4096)
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(
                    f"upload rejected: http={response.status} body={response_body.decode(errors='replace')}"
                )
        finally:
            connection.close()

    def enqueue_alert(self, event: dict) -> dict:
        result = self.store.enqueue_alert(
            event,
            self.node_id,
            self.generation,
            self.event_pre_seconds,
            self.event_post_seconds,
            self.clip_settle_seconds,
        )
        self.flush_event_media_async()
        return result

    def flush_event_reports(self) -> dict:
        rows = self.store.pending_event_reports()
        if not rows:
            return {"attempted": 0, "reported": 0}
        try:
            self._post_json(
                self.event_report_url,
                {"items": [json.loads(row["payload_json"]) for row in rows]},
            )
            self.store.mark_events_reported([row["correlation_id"] for row in rows])
            return {"attempted": len(rows), "reported": len(rows)}
        except (HTTPError, URLError, OSError, ValueError, RuntimeError) as exc:
            self.store.mark_events_failed(rows, str(exc))
            LOG.warning("event reports retained for retry: %s", exc)
            return {"attempted": len(rows), "reported": 0, "error": str(exc)}

    def flush_event_uploads(self) -> dict:
        rows = self.store.pending_uploads()
        completed = 0
        for row in rows:
            payload = json.loads(row["payload_json"])
            try:
                path = Path(row["local_path"])
                if row["upload_state"] != "uploaded":
                    if not path.is_file():
                        raise FileNotFoundError(str(path))
                    ticket = self._post_json(self.upload_ticket_url, payload)
                    upload_url = str((ticket.get("data") or {}).get("upload_url") or "")
                    if not upload_url:
                        raise RuntimeError("upload ticket missing upload_url")
                    self._put_file(upload_url, path, str(payload.get("content_type") or ""))
                    self.store.mark_upload_state(row["asset_id"], "uploaded")
                linked = self._post_json(self.upload_complete_url, payload)
                if not bool((linked.get("data") or {}).get("linked")):
                    raise RuntimeError("control-plane event is not ready for asset linking")
                self.store.mark_upload_complete(row)
                completed += 1
            except (HTTPError, URLError, OSError, ValueError, RuntimeError) as exc:
                self.store.mark_upload_failed(row, str(exc))
                LOG.warning("event media retained for retry asset=%s: %s", row["asset_id"], exc)
        return {"attempted": len(rows), "completed": completed}

    @staticmethod
    def _parse_time(value: str) -> datetime:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _build_event_clip(self, job: sqlite3.Row) -> tuple[Path, dict]:
        event_at = self._parse_time(job["event_time"])
        begin = event_at - timedelta(seconds=max(0, int(job["pre_seconds"] or 0)))
        end = event_at + timedelta(seconds=max(0, int(job["post_seconds"] or 0)))
        segments = []
        for row in self.store.recording_segments(job["device_id"]):
            start = self._parse_time(row["start_time"])
            if row["end_time"]:
                finish = self._parse_time(row["end_time"])
            else:
                fallback_ms = int(row["duration_ms"] or 60000)
                finish = start + timedelta(milliseconds=max(1000, fallback_ms))
            if finish >= begin and start <= end:
                path = self.store.resolve_srs_path(row["file_path"])
                segments.append((path, start))
        if not segments:
            raise RuntimeError("event time window has no recording segments")

        output_dir = self.store.root / "events" / job["device_id"]
        output_dir.mkdir(parents=True, exist_ok=True)
        ffmpeg = shutil.which(os.getenv("FFMPEG_BIN") or "ffmpeg")
        output_path = output_dir / f"{job['asset_id']}.mp4"
        actual_begin = max(begin, segments[0][1])
        actual_end = end
        if ffmpeg:
            concat_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    "w", suffix=".txt", encoding="utf-8", delete=False
                ) as concat_file:
                    concat_path = concat_file.name
                    for path, _ in segments:
                        escaped = str(path).replace("'", "'\\''")
                        concat_file.write(f"file '{escaped}'\n")
                offset = max(0.0, (begin - segments[0][1]).total_seconds())
                wanted = max(1.0, (end - begin).total_seconds())
                common = [
                    ffmpeg, "-y", "-f", "concat", "-safe", "0", "-ss", f"{offset:.3f}",
                    "-i", concat_path, "-t", f"{wanted:.3f}",
                ]
                run = subprocess.run(
                    common + ["-c", "copy", "-movflags", "+faststart", str(output_path)],
                    capture_output=True, text=True, timeout=max(120, int(wanted) * 4),
                )
                if run.returncode != 0 or not output_path.is_file() or output_path.stat().st_size <= 0:
                    run = subprocess.run(
                        common + [
                            "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac",
                            "-movflags", "+faststart", str(output_path),
                        ],
                        capture_output=True, text=True, timeout=max(180, int(wanted) * 8),
                    )
                    if run.returncode != 0:
                        raise RuntimeError((run.stderr or "ffmpeg failed")[-1000:])
            finally:
                if concat_path:
                    try:
                        os.unlink(concat_path)
                    except FileNotFoundError:
                        pass
        else:
            # 极简边缘机未安装 ffmpeg 时仍保留一段完整 DVR，避免事件无录像。
            source = segments[0][0]
            output_path = output_dir / f"{job['asset_id']}{source.suffix.lower() or '.flv'}"
            shutil.copyfile(source, output_path)
        if not output_path.is_file() or output_path.stat().st_size <= 0:
            raise RuntimeError("event clip output is empty")
        duration_ms = max(1000, int((actual_end - actual_begin).total_seconds() * 1000))
        content_type = "video/x-flv" if output_path.suffix.lower() == ".flv" else "video/mp4"
        payload = {
            "asset_id": job["asset_id"],
            "asset_type": "event_clip",
            "device_id": job["device_id"],
            "task_id": job["task_id"],
            "filename": output_path.name,
            "event_time": event_at.isoformat(),
            "start_time": actual_begin.isoformat(),
            "end_time": actual_end.isoformat(),
            "duration_ms": duration_ms,
            "file_size": output_path.stat().st_size,
            "content_type": content_type,
            "checksum": self.store._checksum(output_path),
            "correlation_id": job["correlation_id"],
        }
        return output_path, payload

    def process_due_event_clips(self) -> dict:
        jobs = self.store.due_clip_jobs()
        built = 0
        for job in jobs:
            try:
                path, payload = self._build_event_clip(job)
                self.store.enqueue_clip_upload(job, path, payload)
                built += 1
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
                self.store.mark_clip_failed(job, str(exc))
                LOG.warning(
                    "event clip retained for retry correlation=%s: %s", job["correlation_id"], exc
                )
        return {"attempted": len(jobs), "built": built}

    def flush_event_media(self) -> dict:
        if not self._event_flush_lock.acquire(blocking=False):
            return {"busy": True}
        try:
            events = self.flush_event_reports()
            clips = self.process_due_event_clips()
            uploads = self.flush_event_uploads()
            return {"events": events, "clips": clips, "uploads": uploads}
        finally:
            self._event_flush_lock.release()

    def flush_event_media_async(self):
        worker = threading.Thread(
            target=self.flush_event_media, daemon=True, name="edge-event-media-flush"
        )
        worker.start()
        return worker

    def health(self) -> dict:
        stat = os.statvfs(self.root)
        return {
            "mode": os.getenv("RECORDING_STORAGE_MODE", "edge_local"),
            "generation": self.generation,
            "node_id": self.node_id,
            "storage": {
                "root": self.root,
                "root_ready": os.path.isdir(self.root) and os.access(self.root, os.W_OK),
                "total_bytes": stat.f_blocks * stat.f_frsize,
                "free_bytes": stat.f_bavail * stat.f_frsize,
            },
            "spool": self.store.status(),
        }


class Handler(BaseHTTPRequestHandler):
    server_version = "EasyAIoTEdgeMedia/1.0"

    @property
    def agent(self) -> EdgeMediaAgent:
        return self.server.agent  # type: ignore[attr-defined]

    def log_message(self, fmt, *args):
        LOG.info("%s - %s", self.address_string(), fmt % args)

    def json_response(self, status: int, payload: dict, head_only: bool = False):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def read_json(self) -> dict:
        try:
            size = int(self.headers.get("Content-Length") or 0)
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        if size <= 0 or size > MAX_BODY:
            raise ValueError("request body size is invalid")
        value = json.loads(self.rfile.read(size).decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("JSON body must be an object")
        return value

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/video/alert/hook":
            try:
                event = self.read_json()
                queued = self.agent.enqueue_alert(event)
                LOG.info(
                    "alert queued device=%s correlation=%s image=%s clip=%s",
                    event.get("device_id"), queued["correlation_id"],
                    queued["image_asset_id"], queued["clip_asset_id"],
                )
                self.json_response(HTTPStatus.OK, {
                    "code": 0, "msg": "success", "message": "success",
                    "data": {"status": "queued", **queued},
                })
            except (ValueError, FileNotFoundError) as exc:
                LOG.warning("alert hook rejected: %s", exc)
                self.json_response(HTTPStatus.BAD_REQUEST, {"code": 400, "msg": str(exc)})
            except Exception as exc:
                LOG.exception("alert hook failed")
                self.json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"code": 500, "msg": str(exc)})
            return
        if parsed.path == "/video/media/hook/srs/on_dvr":
            try:
                event = self.read_json()
                asset = self.agent.store.add_dvr(event, self.agent.node_id, self.agent.generation)
                result = self.agent.flush()
                LOG.info(
                    "DVR indexed device=%s asset=%s path=%s report=%s",
                    asset["device_id"], asset["asset_id"], asset["object_key"], result,
                )
                self.json_response(HTTPStatus.OK, {"code": 0})
            except (ValueError, FileNotFoundError) as exc:
                LOG.warning("DVR hook rejected: %s", exc)
                self.json_response(HTTPStatus.BAD_REQUEST, {"code": 1, "msg": str(exc)})
            except Exception as exc:
                LOG.exception("DVR hook failed")
                self.json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"code": 1, "msg": str(exc)})
            return
        if parsed.path == "/video/internal/edge-media/spool/flush":
            if not self.agent.authorized(self.headers):
                self.json_response(HTTPStatus.FORBIDDEN, {"code": 403, "msg": "invalid media token"})
                return
            self.json_response(HTTPStatus.OK, {
                "code": 0,
                "msg": "success",
                "data": {
                    "assets": self.agent.flush(),
                    "events": self.agent.flush_event_media(),
                },
            })
            return
        self.json_response(HTTPStatus.NOT_FOUND, {"code": 404, "msg": "not found"})

    def do_HEAD(self):
        self._do_get(head_only=True)

    def do_GET(self):
        self._do_get(head_only=False)

    def _do_get(self, head_only: bool):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if parsed.path == "/actuator/health":
            self.json_response(HTTPStatus.OK, {"status": "UP"}, head_only)
            return
        if parsed.path == "/video/internal/edge-media/health":
            if not self.agent.authorized(self.headers):
                self.json_response(HTTPStatus.FORBIDDEN, {"code": 403, "msg": "invalid media token"}, head_only)
                return
            self.json_response(HTTPStatus.OK, {"code": 0, "msg": "success", "data": self.agent.health()}, head_only)
            return
        prefix = "/video/internal/edge-media/assets/"
        suffix = "/content"
        if parsed.path.startswith(prefix) and parsed.path.endswith(suffix):
            asset_id = parsed.path[len(prefix):-len(suffix)].strip("/")
            if not self.agent.authorized(self.headers, asset_id, query):
                self.json_response(HTTPStatus.FORBIDDEN, {"code": 403, "msg": "invalid media token"}, head_only)
                return
            row = self.agent.store.asset(asset_id)
            if row is None:
                self.json_response(HTTPStatus.NOT_FOUND, {"code": 404, "msg": "asset not found"}, head_only)
                return
            try:
                path = self.agent.store.resolve_srs_path(row["file_path"])
                self.send_media(path, row["content_type"], head_only)
            except FileNotFoundError:
                self.json_response(HTTPStatus.GONE, {"code": 410, "msg": "asset file expired"}, head_only)
            except ValueError as exc:
                self.json_response(HTTPStatus.FORBIDDEN, {"code": 403, "msg": str(exc)}, head_only)
            return
        self.json_response(HTTPStatus.NOT_FOUND, {"code": 404, "msg": "not found"}, head_only)

    def send_media(self, path: Path, content_type: str | None, head_only: bool):
        size = path.stat().st_size
        start, end = 0, max(0, size - 1)
        status = HTTPStatus.OK
        range_header = (self.headers.get("Range") or "").strip()
        if range_header:
            if not range_header.startswith("bytes=") or "," in range_header:
                self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                return
            raw_start, raw_end = range_header[6:].split("-", 1)
            try:
                if raw_start:
                    start = int(raw_start)
                    end = int(raw_end) if raw_end else end
                elif raw_end:
                    count = int(raw_end)
                    start = max(0, size - count)
            except ValueError:
                self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                return
            if start < 0 or start >= size or end < start:
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return
            end = min(end, size - 1)
            status = HTTPStatus.PARTIAL_CONTENT
        length = end - start + 1 if size else 0
        self.send_response(status)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if status == HTTPStatus.PARTIAL_CONTENT:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if head_only or length <= 0:
            return
        with open(path, "rb") as media_file:
            media_file.seek(start)
            remaining = length
            while remaining:
                chunk = media_file.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, agent):
        super().__init__(address, Handler)
        self.agent = agent


def retry_loop(agent: EdgeMediaAgent, interval: int):
    while True:
        time.sleep(interval)
        try:
            agent.flush()
            agent.flush_event_media()
        except Exception:
            LOG.exception("background report flush failed")


def main():
    logging.basicConfig(
        level=os.getenv("EDGE_MEDIA_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    agent = EdgeMediaAgent()
    interval = max(5, int(os.getenv("EDGE_MEDIA_RETRY_SECONDS") or 15))
    worker = threading.Thread(target=retry_loop, args=(agent, interval), daemon=True, name="edge-media-spool")
    worker.start()
    host = os.getenv("EDGE_MEDIA_BIND", "0.0.0.0")
    port = int(os.getenv("EDGE_MEDIA_PORT") or 6000)
    LOG.info("edge media agent listening on %s:%s root=%s node=%s", host, port, agent.root, agent.node_id)
    Server((host, port), agent).serve_forever()


if __name__ == "__main__":
    main()
