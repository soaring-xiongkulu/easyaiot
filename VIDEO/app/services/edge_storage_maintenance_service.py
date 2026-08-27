"""边缘录像磁盘水位清理与可靠队列周期补偿。"""
import logging
import os
import shutil
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from models import Alert, DeviceRecordingPolicy, MediaAsset, Playback, db
from app.services.edge_media_spool_service import (
    flush_pending_reports,
    flush_pending_event_reports,
    flush_pending_uploads,
    pending_asset_ids,
    protected_asset_ids,
)
from app.services.media_asset_service import parse_timestamp
from app.utils.media_path_security import resolve_allowed_media_file


logger = logging.getLogger(__name__)


def _root():
    return Path(os.path.realpath(os.path.expanduser(
        os.getenv('EDGE_RECORDING_ROOT') or os.getenv('MEDIA_HOST_DATA_ROOT') or '/data/local-storage'
    )))


def _percent(name, default):
    try:
        return min(99.0, max(1.0, float(os.getenv(name) or default)))
    except ValueError:
        return float(default)


def _expired(asset, now):
    expires_at = parse_timestamp(asset.expires_at)
    if expires_at:
        return expires_at <= now
    policy = DeviceRecordingPolicy.query.filter_by(device_id=asset.device_id).first()
    retention = policy.retention_hours if policy and policy.retention_hours is not None else 168
    if retention == 0:
        return False
    started = parse_timestamp(asset.start_time or asset.created_at)
    return bool(started and started + timedelta(hours=retention) <= now)


def cleanup_edge_storage():
    if (os.getenv('RECORDING_STORAGE_MODE') or '').strip().lower() != 'edge_local':
        return {'enabled': False, 'deleted': 0}
    root = _root()
    usage = shutil.disk_usage(root)
    used_percent = (usage.used * 100.0 / usage.total) if usage.total else 0.0
    high = _percent('EDGE_STORAGE_HIGH_WATERMARK', 85)
    low = min(high, _percent('EDGE_STORAGE_LOW_WATERMARK', 75))
    protected = protected_asset_ids() | pending_asset_ids()
    protected.update(
        value for row in db.session.query(Alert.record_asset_id).filter(Alert.record_asset_id.isnot(None)).all()
        for value in row if value
    )
    assets = (MediaAsset.query.filter_by(
        storage_scope='edge', storage_backend='local', asset_type='recording_segment', status='ready',
    ).order_by(MediaAsset.start_time.asc(), MediaAsset.created_at.asc()).all())
    now = datetime.now(timezone.utc)
    deleted = 0
    freed = 0
    for asset in assets:
        if asset.id in protected:
            continue
        if used_percent < high and not _expired(asset, now):
            continue
        path = resolve_allowed_media_file(str(root / asset.object_key), extra_roots=[root])
        size = int(asset.file_size or 0)
        if path:
            try:
                size = max(size, os.path.getsize(path))
                os.unlink(path)
            except FileNotFoundError:
                pass
            Playback.query.filter_by(file_path=str(path)).delete(synchronize_session=False)
        asset.status = 'deleted'
        asset.updated_at = now
        deleted += 1
        freed += size
        if usage.total:
            used_percent = max(0.0, (usage.used - freed) * 100.0 / usage.total)
    db.session.commit()
    critical = _percent('EDGE_STORAGE_CRITICAL_WATERMARK', 95)
    if used_percent >= critical:
        logger.error('边缘录像磁盘达到临界水位 %.1f%%，仍无可清理的非保护分片', used_percent)
    elif deleted:
        logger.info('边缘录像水位清理 deleted=%s freed=%s used=%.1f%%', deleted, freed, used_percent)
    return {
        'enabled': True,
        'deleted': deleted,
        'freed_bytes': freed,
        'used_percent': round(used_percent, 2),
        'high_watermark': high,
        'low_watermark': low,
        'critical': used_percent >= critical,
    }


def run_edge_maintenance_cycle():
    reports = flush_pending_reports()
    events = flush_pending_event_reports()
    uploads = flush_pending_uploads()
    storage = cleanup_edge_storage()
    return {'reports': reports, 'events': events, 'uploads': uploads, 'storage': storage}


def start_edge_storage_maintenance(app, stop_event=None):
    if (os.getenv('RECORDING_STORAGE_MODE') or '').strip().lower() != 'edge_local':
        return None
    stop_event = stop_event or threading.Event()
    interval = max(15, int(os.getenv('EDGE_STORAGE_MAINTENANCE_INTERVAL_SEC') or 60))

    def _loop():
        while not stop_event.is_set():
            try:
                with app.app_context():
                    run_edge_maintenance_cycle()
            except Exception:
                logger.exception('边缘存储维护周期执行失败')
                try:
                    with app.app_context():
                        db.session.rollback()
                except Exception:
                    pass
            stop_event.wait(interval)

    thread = threading.Thread(target=_loop, name='edge-storage-maintenance', daemon=True)
    thread.start()
    return thread
