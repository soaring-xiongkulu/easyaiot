"""
媒体 Janitor：孤儿 DVR/抓拍文件扫描、重新入队、磁盘紧急保护。
"""
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from app.services.media_dvr_utils import parse_srs_dvr_path_date
from app.services.media_kafka_service import (
    build_event_from_srs_hook,
    is_kafka_upload_mode,
    is_snap_kafka_mode,
    publish_dvr_event,
    publish_snap_event,
)
from app.services.playback_disk_guard_service import (
    emergency_free_disk,
    get_disk_usage_percent,
    get_snap_staging_dir,
    get_srs_record_dir,
    iter_flv_files,
    is_cleanup_enabled,
    remove_playback_file,
)

logger = logging.getLogger(__name__)

JpgEntry = Tuple[str, float, int]


def is_janitor_enabled() -> bool:
    raw = os.getenv('MEDIA_JANITOR_ENABLED', 'true')
    return raw.strip().lower() in ('1', 'true', 'yes', 'on')


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)).strip())
    except ValueError:
        return default


def iter_jpg_files(root: str) -> List[JpgEntry]:
    if not os.path.isdir(root):
        return []
    entries: List[JpgEntry] = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if not name.lower().endswith(('.jpg', '.jpeg')):
                continue
            file_path = os.path.join(dirpath, name)
            if not os.path.isfile(file_path):
                continue
            try:
                stat = os.stat(file_path)
                entries.append((file_path, stat.st_mtime, stat.st_size))
            except OSError:
                pass
    entries.sort(key=lambda item: item[1])
    return entries


def _parse_device_from_playback_path(file_path: str) -> str:
    from app.services.dvr_device_resolver import parse_infer_stream_device_id

    parts = [p for p in file_path.replace('\\', '/').split('/') if p]
    if 'playbacks' in parts:
        pi = parts.index('playbacks')
        if pi + 2 < len(parts):
            segment = parts[pi + 2]
            return parse_infer_stream_device_id(segment) or segment
    return ''


def _parse_device_from_snap_path(file_path: str) -> str:
    parts = [p for p in file_path.replace('\\', '/').split('/') if p]
    if 'snaps' in parts:
        pi = parts.index('snaps')
        if pi + 1 < len(parts):
            return parts[pi + 1]
    if len(parts) >= 2:
        return parts[-2]
    return ''


def _is_dvr_already_uploaded(device_id: str, absolute_path: str) -> bool:
    from models import RecordFile
    date_dir, _ = parse_srs_dvr_path_date(absolute_path)
    filename = os.path.basename(absolute_path)
    if not date_dir:
        date_dir = datetime.fromtimestamp(os.path.getmtime(absolute_path)).strftime('%Y/%m/%d')
    object_name = f'{device_id}/{date_dir}/{filename}'
    return RecordFile.query.filter_by(device_id=device_id, object_name=object_name).first() is not None


def _is_snap_already_uploaded(device_id: str, absolute_path: str) -> bool:
    from models import SnapImage
    object_name = f'{device_id}/{os.path.basename(absolute_path)}'
    return SnapImage.query.filter_by(device_id=device_id, object_name=object_name).first() is not None


def _device_exists(device_id: str) -> bool:
    from models import Device
    return bool(device_id and Device.query.get(device_id))


def scan_orphan_dvr_files() -> List[Dict]:
    min_age_min = _env_int('JANITOR_ORPHAN_MIN_AGE_MINUTES', 10)
    cutoff = time.time() - min_age_min * 60
    orphans = []
    for path, mtime, size in iter_flv_files(get_srs_record_dir()):
        if mtime >= cutoff or size <= 0:
            continue
        abs_path = os.path.normpath(path)
        device_id = _parse_device_from_playback_path(abs_path)
        if not device_id:
            continue
        if _is_dvr_already_uploaded(device_id, abs_path):
            remove_playback_file(abs_path, reason='Janitor-已上传')
            continue
        if not _device_exists(device_id):
            remove_playback_file(abs_path, reason='Janitor-设备已删除')
            continue
        orphans.append({
            'device_id': device_id,
            'file_path': abs_path,
            'mtime': mtime,
            'size': size,
        })
    return orphans


def scan_orphan_snap_files() -> List[Dict]:
    min_age_min = _env_int('JANITOR_ORPHAN_MIN_AGE_MINUTES', 10)
    cutoff = time.time() - min_age_min * 60
    orphans = []
    for path, mtime, size in iter_jpg_files(get_snap_staging_dir()):
        if mtime >= cutoff or size <= 0:
            continue
        abs_path = os.path.normpath(path)
        device_id = _parse_device_from_snap_path(abs_path)
        if not device_id:
            continue
        if _is_snap_already_uploaded(device_id, abs_path):
            remove_playback_file(abs_path, reason='Janitor-抓拍已上传')
            continue
        if not _device_exists(device_id):
            remove_playback_file(abs_path, reason='Janitor-设备已删除')
            continue
        orphans.append({
            'device_id': device_id,
            'file_path': abs_path,
            'mtime': mtime,
            'size': size,
        })
    return orphans


def requeue_orphan_dvr(orphan: Dict) -> bool:
    if is_kafka_upload_mode():
        hook = {
            'stream': orphan['device_id'],
            'file': orphan['file_path'],
            'app': 'live',
        }
        event = build_event_from_srs_hook(hook, device_id=orphan['device_id'])
        event['event_id'] = str(uuid.uuid4())
        event['janitor_requeue'] = True
        event['created_at'] = datetime.now(timezone.utc).isoformat()
        return publish_dvr_event(event)

    from app.services.dvr_upload_service import process_dvr_event
    event = build_event_from_srs_hook(
        {'stream': orphan['device_id'], 'file': orphan['file_path']},
        device_id=orphan['device_id'],
    )
    return process_dvr_event(event)


def requeue_orphan_snap(orphan: Dict) -> bool:
    from app.services.snap_upload_service import build_snap_event
    event = build_snap_event(orphan['device_id'], orphan['file_path'], source='janitor')
    if is_snap_kafka_mode():
        return publish_snap_event(event)
    from app.services.snap_upload_service import process_snap_event
    return process_snap_event(event)


def run_janitor_cycle() -> Dict:
    if not is_janitor_enabled():
        return {'enabled': False}

    stats: Dict = {
        'enabled': True,
        'dvr_orphans': 0,
        'dvr_requeued': 0,
        'snap_orphans': 0,
        'snap_requeued': 0,
    }

    dvr_orphans = scan_orphan_dvr_files()
    stats['dvr_orphans'] = len(dvr_orphans)
    for item in dvr_orphans:
        try:
            if requeue_orphan_dvr(item):
                stats['dvr_requeued'] += 1
        except Exception as e:
            logger.error('Janitor DVR 重入队失败 file=%s error=%s', item.get('file_path'), e)

    snap_orphans = scan_orphan_snap_files()
    stats['snap_orphans'] = len(snap_orphans)
    for item in snap_orphans:
        try:
            if requeue_orphan_snap(item):
                stats['snap_requeued'] += 1
        except Exception as e:
            logger.error('Janitor 抓拍重入队失败 file=%s error=%s', item.get('file_path'), e)

    if is_cleanup_enabled():
        record_dir = get_srs_record_dir()
        disk_pct = get_disk_usage_percent(record_dir)
        stats['disk_percent'] = round(disk_pct, 2)
        critical = _env_float('PLAYBACK_DISK_CRITICAL_PERCENT', 90)
        if disk_pct >= critical:
            stats['emergency'] = emergency_free_disk()
            logger.warning('Janitor 触发磁盘紧急清理: %.1f%%', disk_pct)

    logger.info(
        'Janitor 周期完成: dvr_orphans=%s requeued=%s snap_orphans=%s requeued=%s disk=%s%%',
        stats['dvr_orphans'], stats['dvr_requeued'],
        stats['snap_orphans'], stats['snap_requeued'],
        stats.get('disk_percent', '-'),
    )
    return stats
