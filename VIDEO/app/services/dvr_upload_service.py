"""
DVR 段处理：

- standard/full/mini（默认）：转发 iot-sink（NFS 读盘 → MinIO → Playback/告警回填）
- edge / 本地存储：VIDEO 本机落 Playback + 回写告警 record_path（不经 MinIO/sink）
"""
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

_SINK_DVR_HOOK = (
    (os.getenv('SINK_DVR_HOOK_URL') or os.getenv('IOT_SINK_MEDIA_HOOK_URL') or '').strip().rstrip('/')
)
if not _SINK_DVR_HOOK:
    use_gateway = (os.getenv('IOT_SINK_USE_GATEWAY') or '1').strip().lower() not in ('0', 'false', 'no', 'off')
    gateway = (os.getenv('GATEWAY_URL') or os.getenv('JAVA_BACKEND_URL') or 'http://127.0.0.1:48080').strip().rstrip('/')
    if use_gateway:
        _SINK_DVR_HOOK = f'{gateway}/admin-api/sink/media/hook/srs/on_dvr'
    else:
        _sink_base = (os.getenv('IOT_SINK_BASE_URL') or 'http://127.0.0.1:48092').strip().rstrip('/')
        _SINK_DVR_HOOK = f'{_sink_base}/media/hook/srs/on_dvr'


def _truthy(name: str) -> bool:
    return (os.getenv(name) or '').strip().lower() in ('1', 'true', 'yes', 'on')


def _should_persist_dvr_locally() -> bool:
    """edge / 显式本地落盘 / 关闭 MinIO 时走 VIDEO 本地 DVR。"""
    if _truthy('DVR_LOCAL_PERSIST') or _truthy('ALERT_USE_DIRECT_PERSIST'):
        return True
    try:
        from app.utils.service_urls import is_edge_deploy_profile, minio_storage_enabled

        if is_edge_deploy_profile():
            return True
        if not minio_storage_enabled():
            return True
    except Exception:
        pass
    return False


def _forward_dvr_to_sink(event: Dict[str, Any]) -> bool:
    """转发 DVR 事件到 iot-sink MediaHookController。"""
    url = _SINK_DVR_HOOK
    if not url:
        logger.error('未配置 SINK_DVR_HOOK_URL，无法上传 DVR')
        return False
    try:
        resp = requests.post(url, json=event, timeout=120)
        if resp.status_code >= 400:
            logger.error('iot-sink DVR Hook HTTP %s body=%s', resp.status_code, resp.text[:500])
            return False
        logger.info('DVR 已转发 iot-sink url=%s stream=%s', url, event.get('stream'))
        return True
    except Exception as e:
        logger.error('转发 iot-sink DVR 失败 url=%s error=%s', url, e, exc_info=True)
        return False


def _persist_dvr_locally(event: Dict[str, Any]) -> bool:
    """edge/本地存储：登记 Playback 并回写告警 record_path（保留本地文件）。"""
    from models import Device, Playback, db
    from app.services.alert_service import patch_alerts_record
    from app.services.media_dvr_utils import (
        ffprobe_video_duration_seconds,
        parse_srs_dvr_segment_start_from_filename,
        resolve_playback_absolute_path,
        wait_dvr_file_stable,
    )
    from app.utils.service_urls import epoch_to_shanghai_datetime

    stream = (event.get('stream') or '').strip()
    file_path = (event.get('file_path') or event.get('file') or '').strip()
    cwd = (event.get('cwd') or '').strip()
    device_id = (event.get('device_id') or stream or '').strip()
    if not file_path:
        logger.warning('本地 DVR：缺少 file_path event=%s', event)
        return False

    absolute = resolve_playback_absolute_path(file_path, cwd)
    file_size = wait_dvr_file_stable(absolute)
    if file_size <= 0:
        logger.warning('本地 DVR：文件未就绪 path=%s', absolute)
        return False

    device = None
    if device_id:
        device = Device.query.filter_by(id=device_id).first()
    if device is None and stream:
        device = Device.query.filter_by(id=stream).first()
    if device is None and stream:
        device = Device.query.filter(Device.rtmp_stream.contains(f'/{stream}')).first()
    if device is None:
        logger.info('本地 DVR：设备不存在，丢弃 stream=%s file=%s', stream, absolute)
        return True

    resolved_id = device.id
    device_name = device.name or resolved_id
    shanghai = timezone(timedelta(hours=8))
    segment_start = parse_srs_dvr_segment_start_from_filename(absolute)
    if segment_start is not None:
        event_time = segment_start
    else:
        try:
            event_time = epoch_to_shanghai_datetime(os.path.getmtime(absolute))
        except OSError:
            event_time = datetime.now(shanghai)

    duration = int(ffprobe_video_duration_seconds(absolute) or 0)
    if duration <= 0:
        duration = 30

    # 库中存宿主机绝对路径；前端经 resolve_playback_display_url 转 VIDEO API
    store_path = absolute
    try:
        existing = Playback.query.filter(
            Playback.device_id == resolved_id,
            Playback.file_path == store_path,
        ).first()
        now = datetime.now(shanghai)
        if existing:
            existing.event_time = event_time
            existing.duration = duration
            existing.file_size = file_size
            existing.device_name = device_name
            existing.updated_at = now
        else:
            db.session.add(
                Playback(
                    file_path=store_path,
                    event_time=event_time,
                    device_id=resolved_id,
                    device_name=device_name,
                    duration=duration,
                    file_size=file_size,
                    created_at=now,
                    updated_at=now,
                )
            )
        db.session.commit()
    except Exception as e:
        logger.error('本地 DVR：写入 Playback 失败 device=%s error=%s', resolved_id, e, exc_info=True)
        db.session.rollback()
        return False

    # 同步写入 record_file，否则录像空间「录像回放」读不到片段
    try:
        from models import RecordSpace
        from app.services.space_file_metadata_service import upsert_record_file
        record_space = RecordSpace.query.filter_by(device_id=resolved_id).first()
        if record_space:
            object_name = os.path.basename(absolute)
            upsert_record_file(
                space_id=record_space.id,
                device_id=resolved_id,
                object_name=object_name,
                bucket_name=record_space.bucket_name or 'record-space',
                filename=object_name,
                file_size=file_size,
                url=store_path,
                duration=duration,
                event_time=event_time.replace(tzinfo=None) if event_time.tzinfo else event_time,
                source='dvr',
            )
    except Exception as e:
        logger.warning('本地 DVR：写入 record_file 失败 device=%s error=%s', resolved_id, e)

    try:
        patch_alerts_record(
            {
                'device_id': resolved_id,
                'event_time': event_time.astimezone(shanghai).strftime('%Y-%m-%d %H:%M:%S'),
                'duration': duration,
                'file_path': store_path,
            }
        )
    except Exception as e:
        logger.warning('本地 DVR：回写告警 record_path 失败 device=%s error=%s', resolved_id, e)

    logger.info(
        '本地 DVR 已落盘 device=%s path=%s size=%s duration=%s',
        resolved_id,
        store_path,
        file_size,
        duration,
    )
    return True


def process_dvr_event(event: Dict[str, Any]) -> bool:
    """处理单条 DVR 事件：edge/本地存储本机落盘，否则转发 iot-sink。"""
    if not event:
        return False
    if _should_persist_dvr_locally():
        return _persist_dvr_locally(event)
    return _forward_dvr_to_sink(event)
