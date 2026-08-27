"""边缘媒体资产可靠上报队列（SQLite WAL，独立于业务数据库/NFS）。"""
import json
import logging
import os
import sqlite3
import threading
import time
from pathlib import Path

import requests


logger = logging.getLogger(__name__)
_flush_lock = threading.Lock()


def _recording_root() -> Path:
    raw = os.getenv('EDGE_RECORDING_ROOT') or os.getenv('MEDIA_HOST_DATA_ROOT') or '/data/local-storage'
    return Path(os.path.expandvars(os.path.expanduser(raw))).resolve(strict=False)


def _database_path() -> Path:
    explicit = (os.getenv('EDGE_MEDIA_SPOOL_DB') or '').strip()
    return Path(explicit).expanduser() if explicit else _recording_root() / '.state' / 'media-spool.db'


def _connect():
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS media_report_queue (
            asset_id TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            retry_count INTEGER NOT NULL DEFAULT 0,
            next_retry_at INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS media_upload_queue (
            asset_id TEXT PRIMARY KEY,
            local_path TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            retry_count INTEGER NOT NULL DEFAULT 0,
            next_retry_at INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            delete_after_upload INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS event_report_queue (
            correlation_id TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            retry_count INTEGER NOT NULL DEFAULT 0,
            next_retry_at INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS media_segment_protection (
            asset_id TEXT NOT NULL,
            ref_key TEXT NOT NULL,
            protected_until INTEGER NOT NULL,
            PRIMARY KEY(asset_id, ref_key)
        )
    ''')
    conn.commit()
    return conn


def enqueue_asset_report(payload):
    asset_id = str(payload.get('asset_id') or '').strip()
    if not asset_id:
        raise ValueError('边缘资产上报缺少 asset_id')
    now = int(time.time())
    with _connect() as conn:
        conn.execute('''
            INSERT INTO media_report_queue (
                asset_id, payload_json, status, retry_count, next_retry_at, created_at, updated_at
            ) VALUES (?, ?, 'pending', 0, 0, ?, ?)
            ON CONFLICT(asset_id) DO UPDATE SET
                payload_json=excluded.payload_json,
                status='pending',
                next_retry_at=0,
                updated_at=excluded.updated_at
        ''', (asset_id, json.dumps(payload, ensure_ascii=False), now, now))
        conn.commit()


def _report_url():
    explicit = (os.getenv('MEDIA_ASSET_REPORT_URL') or '').strip()
    if explicit:
        return explicit
    gateway = (os.getenv('GATEWAY_URL') or os.getenv('JAVA_BACKEND_URL') or '').strip().rstrip('/')
    return f'{gateway}/admin-api/video/internal/media/assets/report-batch' if gateway else ''


def _main_media_url(endpoint: str):
    explicit = (os.getenv(f'MEDIA_ASSET_{endpoint.upper().replace("-", "_")}_URL') or '').strip()
    if explicit:
        return explicit
    report_url = _report_url()
    if not report_url:
        return ''
    return report_url.rsplit('/', 1)[0] + '/' + endpoint


def enqueue_center_upload(payload, local_path, *, delete_after_upload=False):
    asset_id = str(payload.get('asset_id') or '').strip()
    path = os.path.realpath(os.path.expanduser(str(local_path or '')))
    if not asset_id or not os.path.isfile(path):
        raise ValueError('事件媒体上传缺少 asset_id 或本地文件')
    now = int(time.time())
    with _connect() as conn:
        conn.execute('''
            INSERT INTO media_upload_queue (
                asset_id, local_path, payload_json, status, retry_count, next_retry_at,
                delete_after_upload, created_at, updated_at
            ) VALUES (?, ?, ?, 'pending', 0, 0, ?, ?, ?)
            ON CONFLICT(asset_id) DO UPDATE SET
                local_path=excluded.local_path,
                payload_json=excluded.payload_json,
                status=CASE WHEN media_upload_queue.status='uploaded' THEN 'uploaded' ELSE 'pending' END,
                next_retry_at=0,
                delete_after_upload=excluded.delete_after_upload,
                updated_at=excluded.updated_at
        ''', (asset_id, path, json.dumps(payload, ensure_ascii=False),
              1 if delete_after_upload else 0, now, now))
        conn.commit()


def enqueue_event_report(payload):
    correlation_id = str(payload.get('correlation_id') or '').strip()
    if not correlation_id:
        raise ValueError('边缘事件补报缺少 correlation_id')
    event = dict(payload)
    event['image_path'] = None
    event['image_url'] = None
    event['record_path'] = None
    event.pop('_edge_image_asset_id', None)
    now = int(time.time())
    with _connect() as conn:
        conn.execute('''
            INSERT INTO event_report_queue(
                correlation_id, payload_json, retry_count, next_retry_at, created_at, updated_at
            ) VALUES (?, ?, 0, 0, ?, ?)
            ON CONFLICT(correlation_id) DO UPDATE SET
                payload_json=excluded.payload_json, next_retry_at=0, updated_at=excluded.updated_at
        ''', (correlation_id, json.dumps(event, ensure_ascii=False, default=str), now, now))
        conn.commit()


def protect_segments(asset_ids, ref_key, ttl_seconds=86400):
    until = int(time.time()) + max(60, int(ttl_seconds))
    with _connect() as conn:
        conn.executemany('''
            INSERT INTO media_segment_protection(asset_id, ref_key, protected_until)
            VALUES (?, ?, ?)
            ON CONFLICT(asset_id, ref_key) DO UPDATE SET protected_until=excluded.protected_until
        ''', [(str(asset_id), str(ref_key), until) for asset_id in asset_ids])
        conn.commit()


def release_segment_protection(ref_key):
    with _connect() as conn:
        conn.execute('DELETE FROM media_segment_protection WHERE ref_key=?', (str(ref_key),))
        conn.commit()


def protected_asset_ids():
    now = int(time.time())
    with _connect() as conn:
        conn.execute('DELETE FROM media_segment_protection WHERE protected_until < ?', (now,))
        rows = conn.execute('SELECT DISTINCT asset_id FROM media_segment_protection').fetchall()
        conn.commit()
    return {row[0] for row in rows}


def pending_asset_ids():
    with _connect() as conn:
        report = conn.execute('SELECT asset_id FROM media_report_queue').fetchall()
        uploads = conn.execute('SELECT asset_id FROM media_upload_queue').fetchall()
    return {row[0] for row in report + uploads}


def flush_pending_reports(batch_size=100):
    if not _flush_lock.acquire(blocking=False):
        return {'sent': 0, 'pending': None, 'busy': True}
    try:
        url = _report_url()
        node_id = (os.getenv('COMPUTE_NODE_ID') or os.getenv('NODE_ID') or '').strip()
        token = (os.getenv('MEDIA_INTERNAL_TOKEN') or '').strip()
        if not url or not node_id or not token:
            return {'sent': 0, 'pending': None, 'configured': False}
        now = int(time.time())
        with _connect() as conn:
            rows = conn.execute('''
                SELECT asset_id, payload_json, retry_count
                FROM media_report_queue
                WHERE status = 'pending' AND next_retry_at <= ?
                ORDER BY created_at ASC LIMIT ?
            ''', (now, max(1, min(500, int(batch_size))))).fetchall()
        if not rows:
            return {'sent': 0, 'pending': 0}
        payloads = [json.loads(row[1]) for row in rows]
        try:
            response = requests.post(
                url,
                json={'items': payloads},
                headers={'X-Node-Id': node_id, 'X-Media-Internal-Token': token},
                timeout=(5, 15),
            )
            response.raise_for_status()
            body = response.json()
            if body.get('code') != 0:
                raise RuntimeError(body.get('msg') or '主节点拒绝媒体资产上报')
            with _connect() as conn:
                conn.executemany('DELETE FROM media_report_queue WHERE asset_id = ?', [(row[0],) for row in rows])
                conn.commit()
            logger.info('边缘媒体资产已补报 count=%s url=%s', len(rows), url)
            return {'sent': len(rows), 'pending': 0}
        except Exception as exc:
            error = str(exc)[:1000]
            with _connect() as conn:
                for asset_id, _, retry_count in rows:
                    retry = retry_count + 1
                    delay = min(3600, 2 ** min(retry, 10))
                    conn.execute('''
                        UPDATE media_report_queue
                        SET retry_count=?, next_retry_at=?, last_error=?, updated_at=?
                        WHERE asset_id=?
                    ''', (retry, now + delay, error, now, asset_id))
                conn.commit()
            logger.warning('边缘媒体资产上报失败 count=%s error=%s', len(rows), error)
            return {'sent': 0, 'pending': len(rows), 'error': error}
    finally:
        _flush_lock.release()


def flush_pending_reports_async():
    thread = threading.Thread(target=flush_pending_reports, name='edge-media-spool-flush', daemon=True)
    thread.start()
    return thread


def flush_pending_event_reports(batch_size=100):
    report_url = _report_url()
    if not report_url:
        return {'sent': 0, 'pending': None, 'configured': False}
    event_url = report_url.replace('/assets/report-batch', '/events/report-batch')
    node_id = (os.getenv('COMPUTE_NODE_ID') or os.getenv('NODE_ID') or '').strip()
    token = (os.getenv('MEDIA_INTERNAL_TOKEN') or '').strip()
    if not node_id or not token:
        return {'sent': 0, 'pending': None, 'configured': False}
    now = int(time.time())
    with _connect() as conn:
        rows = conn.execute('''
            SELECT correlation_id, payload_json, retry_count FROM event_report_queue
            WHERE next_retry_at <= ? ORDER BY created_at ASC LIMIT ?
        ''', (now, max(1, min(500, int(batch_size))))).fetchall()
    if not rows:
        return {'sent': 0, 'pending': 0}
    try:
        response = requests.post(
            event_url,
            json={'items': [json.loads(row[1]) for row in rows]},
            headers={'X-Node-Id': node_id, 'X-Media-Internal-Token': token},
            timeout=(5, 15),
        )
        response.raise_for_status()
        body = response.json()
        if body.get('code') != 0:
            raise RuntimeError(body.get('msg') or '主节点拒绝事件补报')
        with _connect() as conn:
            conn.executemany('DELETE FROM event_report_queue WHERE correlation_id=?', [(row[0],) for row in rows])
            conn.commit()
        return {'sent': len(rows), 'pending': 0}
    except Exception as exc:
        with _connect() as conn:
            for correlation_id, _, retry_count in rows:
                retry = retry_count + 1
                conn.execute('''
                    UPDATE event_report_queue SET retry_count=?, next_retry_at=?, last_error=?, updated_at=?
                    WHERE correlation_id=?
                ''', (retry, now + min(3600, 2 ** min(retry, 10)), str(exc)[:1000], now, correlation_id))
            conn.commit()
        logger.warning('边缘事件补报失败 count=%s error=%s', len(rows), exc)
        return {'sent': 0, 'pending': len(rows), 'error': str(exc)}


def flush_pending_event_reports_async():
    thread = threading.Thread(target=flush_pending_event_reports, name='edge-event-report-flush', daemon=True)
    thread.start()
    return thread


def flush_pending_uploads(batch_size=20):
    ticket_url = _main_media_url('upload-ticket')
    complete_url = _main_media_url('upload-complete')
    node_id = (os.getenv('COMPUTE_NODE_ID') or os.getenv('NODE_ID') or '').strip()
    token = (os.getenv('MEDIA_INTERNAL_TOKEN') or '').strip()
    if not ticket_url or not complete_url or not node_id or not token:
        return {'sent': 0, 'pending': None, 'configured': False}
    now = int(time.time())
    with _connect() as conn:
        rows = conn.execute('''
            SELECT asset_id, local_path, payload_json, status, retry_count, delete_after_upload
            FROM media_upload_queue
            WHERE next_retry_at <= ? ORDER BY created_at ASC LIMIT ?
        ''', (now, max(1, min(100, int(batch_size))))).fetchall()
    sent = 0
    headers = {'X-Node-Id': node_id, 'X-Media-Internal-Token': token}
    for asset_id, local_path, payload_json, status, retry_count, delete_after in rows:
        payload = json.loads(payload_json)
        try:
            if status != 'uploaded':
                if not os.path.isfile(local_path):
                    raise FileNotFoundError(local_path)
                ticket = requests.post(ticket_url, json=payload, headers=headers, timeout=(5, 15))
                ticket.raise_for_status()
                ticket_body = ticket.json()
                if ticket_body.get('code') != 0:
                    raise RuntimeError(ticket_body.get('msg') or '主节点拒绝上传凭证')
                upload_url = ticket_body['data']['upload_url']
                with open(local_path, 'rb') as media_file:
                    upload = requests.put(
                        upload_url,
                        data=media_file,
                        headers={'Content-Type': payload.get('content_type') or 'application/octet-stream'},
                        timeout=(5, 120),
                    )
                upload.raise_for_status()
                with _connect() as conn:
                    conn.execute(
                        "UPDATE media_upload_queue SET status='uploaded', updated_at=? WHERE asset_id=?",
                        (int(time.time()), asset_id),
                    )
                    conn.commit()
            completed = requests.post(complete_url, json=payload, headers=headers, timeout=(5, 15))
            completed.raise_for_status()
            completed_body = completed.json()
            if completed_body.get('code') != 0:
                raise RuntimeError(completed_body.get('msg') or '主节点拒绝上传完成回调')
            if not completed_body.get('data', {}).get('linked', False):
                raise RuntimeError('主节点事件尚未落库，等待关联')
            with _connect() as conn:
                conn.execute('DELETE FROM media_upload_queue WHERE asset_id=?', (asset_id,))
                conn.commit()
            release_segment_protection(payload.get('protection_ref') or asset_id)
            if delete_after:
                try:
                    os.unlink(local_path)
                except FileNotFoundError:
                    pass
            sent += 1
        except Exception as exc:
            retry = retry_count + 1
            delay = min(3600, 2 ** min(retry, 10))
            with _connect() as conn:
                conn.execute('''
                    UPDATE media_upload_queue
                    SET retry_count=?, next_retry_at=?, last_error=?, updated_at=? WHERE asset_id=?
                ''', (retry, int(time.time()) + delay, str(exc)[:1000], int(time.time()), asset_id))
                conn.commit()
            logger.warning('事件媒体补传失败 asset=%s error=%s', asset_id, exc)
    return {'sent': sent, 'pending': max(0, len(rows) - sent)}


def flush_pending_uploads_async():
    thread = threading.Thread(target=flush_pending_uploads, name='edge-media-upload-flush', daemon=True)
    thread.start()
    return thread


def spool_status():
    with _connect() as conn:
        pending = conn.execute("SELECT COUNT(*) FROM media_report_queue WHERE status='pending'").fetchone()[0]
        retries = conn.execute('SELECT COALESCE(SUM(retry_count), 0) FROM media_report_queue').fetchone()[0]
        last_error = conn.execute('''
            SELECT last_error FROM media_report_queue
            WHERE last_error IS NOT NULL ORDER BY updated_at DESC LIMIT 1
        ''').fetchone()
        upload_pending = conn.execute('SELECT COUNT(*) FROM media_upload_queue').fetchone()[0]
        event_pending = conn.execute('SELECT COUNT(*) FROM event_report_queue').fetchone()[0]
        upload_error = conn.execute('''
            SELECT last_error FROM media_upload_queue
            WHERE last_error IS NOT NULL ORDER BY updated_at DESC LIMIT 1
        ''').fetchone()
    return {
        'pending_count': pending,
        'retry_count': retries,
        'last_error': last_error[0] if last_error else None,
        'upload_pending_count': upload_pending,
        'event_pending_count': event_pending,
        'upload_last_error': upload_error[0] if upload_error else None,
        'database_path': str(_database_path()),
    }
