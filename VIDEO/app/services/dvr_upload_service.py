"""
DVR 段处理：

- standard/full/mini（默认）：转发 iot-sink（NFS 读盘 → MinIO → Playback/告警回填）
- edge / 本地存储：VIDEO 本机落 Playback + 回写告警 record_path（不经 MinIO/sink）
"""
import logging
import os
import uuid
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
    configured_mode = (os.getenv('RECORDING_STORAGE_MODE') or '').strip().lower()
    if configured_mode == 'edge_local':
        return True
    if configured_mode == 'central_shared':
        return False
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
    task_id = event.get('task_id')
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
    if device is None and stream:
        from app.services.dvr_device_resolver import resolve_stream_identity_from_hook

        resolved_task_id, resolved_device_id, resolved_device = resolve_stream_identity_from_hook(
            stream, absolute
        )
        if resolved_device is not None:
            device = resolved_device
            device_id = resolved_device_id or device_id
            task_id = task_id if task_id is not None else resolved_task_id
    if device is None:
        logger.info('本地 DVR：设备不存在，丢弃 stream=%s file=%s', stream, absolute)
        return True

    resolved_id = device.id
    from app.services.media_asset_service import get_or_default_policy
    recording_policy = get_or_default_policy(resolved_id)
    recording_mode = recording_policy.recording_mode or 'continuous'
    if recording_mode == 'off':
        try:
            from app.utils.media_path_security import resolve_allowed_media_file
            recording_root = os.path.realpath(os.path.expanduser(
                os.getenv('EDGE_RECORDING_ROOT') or os.getenv('MEDIA_HOST_DATA_ROOT') or '/data/local-storage'
            ))
            disposable = resolve_allowed_media_file(absolute, extra_roots=[recording_root])
            if disposable:
                os.unlink(disposable)
        except OSError as exc:
            logger.warning('已关闭录像的分片清理失败 device=%s path=%s: %s', resolved_id, absolute, exc)
        return True
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

    probed_duration = float(ffprobe_video_duration_seconds(absolute) or 0)
    hook_duration = event.get('duration') or event.get('dvr_duration')
    try:
        duration_seconds = probed_duration if probed_duration > 0 else max(0.0, float(hook_duration or 0))
    except (TypeError, ValueError):
        duration_seconds = probed_duration
    duration = max(1, int(round(duration_seconds))) if duration_seconds > 0 else 0

    # 库中存宿主机绝对路径；前端经 resolve_playback_display_url 转 VIDEO API
    store_path = absolute
    try:
        existing = Playback.query.filter(
            Playback.device_id == resolved_id,
            Playback.file_path == store_path,
        ).first()
        now = datetime.now(shanghai)
        if existing:
            existing.task_id = task_id
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
                    task_id=task_id,
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

    asset_id = None
    if (os.getenv('RECORDING_STORAGE_MODE') or '').strip().lower() == 'edge_local':
        try:
            from app.services.media_asset_service import upsert_media_asset
            from app.services.edge_media_spool_service import enqueue_asset_report, flush_pending_reports_async
            from app.utils.media_path_security import resolve_allowed_media_file

            recording_root = os.path.realpath(os.path.expanduser(
                os.getenv('EDGE_RECORDING_ROOT') or os.getenv('MEDIA_HOST_DATA_ROOT') or '/data/local-storage'
            ))
            allowed = resolve_allowed_media_file(absolute, extra_roots=[recording_root])
            if allowed is None:
                raise ValueError(f'DVR 文件不在边缘录像根目录内: {absolute}')
            object_key = os.path.relpath(str(allowed), recording_root).replace(os.sep, '/')
            asset_id = str(uuid.uuid4())
            duration_ms = int(round(duration_seconds * 1000)) if duration_seconds > 0 else None
            end_time = event_time + timedelta(milliseconds=duration_ms) if duration_ms else None
            report_payload = {
                'asset_id': asset_id,
                'asset_type': 'recording_segment',
                'device_id': resolved_id,
                'task_id': task_id,
                'source_node_id': int(os.getenv('COMPUTE_NODE_ID') or os.getenv('NODE_ID') or 0) or None,
                'storage_node_id': int(os.getenv('COMPUTE_NODE_ID') or os.getenv('NODE_ID') or 0) or None,
                'storage_generation': int(os.getenv('RECORDING_STORAGE_GENERATION') or 1),
                'storage_scope': 'edge',
                'storage_backend': 'local',
                'object_key': object_key,
                'status': 'ready',
                'start_time': event_time.isoformat(),
                'end_time': end_time.isoformat() if end_time else None,
                'duration_ms': duration_ms,
                'file_size': file_size,
                'content_type': 'video/x-flv' if absolute.lower().endswith('.flv') else 'video/mp4',
            }
            if recording_mode == 'event_only':
                ring_seconds = max(
                    300,
                    int(recording_policy.event_pre_seconds or 0)
                    + int(recording_policy.event_post_seconds or 0)
                    + int(os.getenv('EDGE_EVENT_CLIP_SETTLE_SECONDS') or 70) + 120,
                )
                report_payload['expires_at'] = (datetime.now(timezone.utc) + timedelta(seconds=ring_seconds)).isoformat()
            if report_payload['source_node_id'] is None:
                raise ValueError('edge_local 未配置 COMPUTE_NODE_ID/NODE_ID')
            upsert_media_asset(report_payload, authenticated_node_id=report_payload['source_node_id'])
            # event_only 分片只是边缘环形缓存，不进入中心连续录像时间轴。
            if recording_mode == 'continuous':
                enqueue_asset_report(report_payload)
                flush_pending_reports_async()
        except Exception as e:
            logger.error('边缘 DVR：登记统一资产失败 device=%s error=%s', resolved_id, e, exc_info=True)
            return False
    else:
        # 旧本地/mini 模式仍写入 record_file；该函数会登记中心兼容资产。
        try:
            from models import RecordSpace
            from app.services.space_file_metadata_service import upsert_record_file
            record_space = RecordSpace.query.filter_by(device_id=resolved_id).first()
            if record_space:
                filename = os.path.basename(absolute)
                task_prefix = f'task_{int(task_id)}/' if task_id is not None else ''
                object_name = f'{task_prefix}{filename}'
                upsert_record_file(
                    space_id=record_space.id,
                    device_id=resolved_id,
                    task_id=task_id,
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
        if recording_mode == 'event_only':
            raise LookupError('event_only 等待事件片段生成，不回写环形缓存分片')
        patch_alerts_record(
            {
                'device_id': resolved_id,
                'task_id': task_id,
                'event_time': event_time.astimezone(shanghai).strftime('%Y-%m-%d %H:%M:%S'),
                'duration': duration,
                'file_path': f'/video/media/assets/{asset_id}/content' if asset_id else store_path,
            }
        )
    except LookupError:
        pass
    except Exception as e:
        logger.warning('本地 DVR：回写告警 record_path 失败 device=%s error=%s', resolved_id, e)

    logger.info(
        '本地 DVR 已落盘 task=%s device=%s path=%s size=%s duration=%s asset=%s',
        task_id,
        resolved_id,
        store_path,
        file_size,
        duration,
        asset_id,
    )
    return True


def process_dvr_event(event: Dict[str, Any]) -> bool:
    """处理单条 DVR 事件：edge/本地存储本机落盘，否则转发 iot-sink。"""
    if not event:
        return False
    if _should_persist_dvr_locally():
        return _persist_dvr_locally(event)
    return _forward_dvr_to_sink(event)
