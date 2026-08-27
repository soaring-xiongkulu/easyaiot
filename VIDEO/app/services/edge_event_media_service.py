"""边缘事件图片与前后录像片段生成/可靠中心同步。"""
import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
import threading
import uuid
from datetime import timedelta
from pathlib import Path

from models import Alert, MediaAsset, db
from app.services.edge_media_spool_service import (
    enqueue_center_upload,
    enqueue_event_report,
    flush_pending_event_reports_async,
    flush_pending_uploads_async,
    protect_segments,
    release_segment_protection,
)
from app.services.media_asset_service import get_or_default_policy, parse_timestamp, upsert_media_asset
from app.utils.media_path_security import resolve_allowed_media_file


logger = logging.getLogger(__name__)


def _edge_mode():
    return (os.getenv('RECORDING_STORAGE_MODE') or '').strip().lower() == 'edge_local'


def _node_id():
    try:
        return int(os.getenv('COMPUTE_NODE_ID') or os.getenv('NODE_ID') or 0) or None
    except ValueError:
        return None


def _root():
    return Path(os.path.realpath(os.path.expanduser(
        os.getenv('EDGE_RECORDING_ROOT') or os.getenv('MEDIA_HOST_DATA_ROOT') or '/data/local-storage'
    )))


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as media_file:
        for chunk in iter(lambda: media_file.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_edge_event_media(alert_data):
    """在告警事件投递前登记图片并安排事件片段；不阻塞事件落库。"""
    if not _edge_mode():
        return alert_data
    device_id = str(alert_data.get('device_id') or '').strip()
    node_id = _node_id()
    if not device_id or node_id is None:
        logger.warning('edge_local 事件媒体跳过：缺少 device_id 或 COMPUTE_NODE_ID')
        return alert_data
    correlation_id = str(
        alert_data.get('correlation_id') or alert_data.get('correlationId')
        or alert_data.get('event_id') or alert_data.get('eventId') or uuid.uuid4()
    )
    alert_data['correlation_id'] = correlation_id
    policy = get_or_default_policy(device_id)
    event_time = alert_data.get('time')

    image_path = str(alert_data.get('image_path') or '').strip()
    if policy.event_image_sync and image_path:
        try:
            roots = [_root(), os.getenv('ALERT_IMAGES_DIR') or str(_root() / 'alert_images')]
            allowed = resolve_allowed_media_file(image_path, extra_roots=roots)
            if allowed is None:
                raise ValueError('告警图片不在允许的边缘媒体目录')
            asset_id = str(uuid.uuid4())
            content_type = 'image/png' if str(allowed).lower().endswith('.png') else 'image/jpeg'
            relative = os.path.relpath(str(allowed), str(_root())).replace(os.sep, '/')
            local_payload = {
                'asset_id': asset_id,
                'asset_type': 'alert_image',
                'device_id': device_id,
                'task_id': alert_data.get('task_id') or alert_data.get('taskId'),
                'source_node_id': node_id,
                'storage_node_id': node_id,
                'storage_generation': int(os.getenv('RECORDING_STORAGE_GENERATION') or 1),
                'storage_scope': 'edge',
                'storage_backend': 'local',
                'object_key': relative,
                'status': 'ready',
                'start_time': event_time,
                'file_size': os.path.getsize(allowed),
                'content_type': content_type,
                'checksum': _sha256(allowed),
            }
            upsert_media_asset(local_payload, authenticated_node_id=node_id)
            upload_payload = {
                'asset_id': asset_id,
                'asset_type': 'alert_image',
                'device_id': device_id,
                'filename': os.path.basename(allowed),
                'event_time': event_time,
                'start_time': event_time,
                'file_size': local_payload['file_size'],
                'content_type': content_type,
                'checksum': local_payload['checksum'],
                'correlation_id': correlation_id,
            }
            enqueue_center_upload(upload_payload, str(allowed))
            alert_data['_edge_image_asset_id'] = asset_id
            flush_pending_uploads_async()
        except Exception as exc:
            db.session.rollback()
            logger.warning('边缘事件图片登记失败 device=%s: %s', device_id, exc, exc_info=True)

    try:
        enqueue_event_report(alert_data)
        flush_pending_event_reports_async()
    except Exception as exc:
        logger.warning('边缘事件进入补报队列失败 device=%s: %s', device_id, exc)

    if policy.event_clip_sync and alert_data.get('task_type') not in ('snap', 'snapshot'):
        delay = max(0, int(policy.event_post_seconds or 0)) + max(
            1, int(os.getenv('EDGE_EVENT_CLIP_SETTLE_SECONDS') or 70),
        )
        app = None
        try:
            from flask import current_app
            app = current_app._get_current_object()
        except RuntimeError:
            pass

        def _run():
            try:
                if app:
                    with app.app_context():
                        build_and_enqueue_event_clip(
                            device_id, correlation_id, event_time, policy.event_pre_seconds,
                            policy.event_post_seconds, alert_data.get('task_id') or alert_data.get('taskId'),
                        )
                else:
                    build_and_enqueue_event_clip(
                        device_id, correlation_id, event_time, policy.event_pre_seconds,
                        policy.event_post_seconds, alert_data.get('task_id') or alert_data.get('taskId'),
                    )
            except Exception:
                logger.exception('边缘事件片段生成失败 device=%s correlation=%s', device_id, correlation_id)

        timer = threading.Timer(delay, _run)
        timer.daemon = True
        timer.name = f'event-clip-{device_id}'
        timer.start()
    return alert_data


def _asset_path(asset):
    path = resolve_allowed_media_file(str(_root() / asset.object_key), extra_roots=[_root()])
    return Path(path) if path else None


def build_and_enqueue_event_clip(device_id, correlation_id, event_time, pre_seconds, post_seconds,
                                 task_id=None):
    event_at = parse_timestamp(event_time)
    if event_at is None:
        raise ValueError('事件时间为空，无法生成事件片段')
    begin = event_at - timedelta(seconds=max(0, int(pre_seconds or 0)))
    end = event_at + timedelta(seconds=max(0, int(post_seconds or 0)))
    candidates = (MediaAsset.query.filter_by(
        device_id=device_id,
        asset_type='recording_segment',
        storage_scope='edge',
        status='ready',
    ).order_by(MediaAsset.start_time.asc()).all())
    segments = []
    for asset in candidates:
        start = parse_timestamp(asset.start_time)
        finish = parse_timestamp(asset.end_time)
        if finish is None and start is not None:
            fallback_ms = int(asset.duration_ms or int(os.getenv('SRS_DVR_FALLBACK_SECONDS') or 60) * 1000)
            finish = start + timedelta(milliseconds=max(1000, fallback_ms))
        if start and finish and finish >= begin and start <= end:
            path = _asset_path(asset)
            if path and path.is_file():
                segments.append((asset, path, start))
    if not segments:
        raise RuntimeError('事件时间窗口内暂无可用录像分片')
    asset_id = str(uuid.uuid4())
    protection_ref = f'event:{correlation_id}'
    protect_segments([item[0].id for item in segments], protection_ref, ttl_seconds=7 * 86400)
    output_dir = _root() / 'events' / device_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f'{asset_id}.mp4'
    ffmpeg = shutil.which(os.getenv('FFMPEG_BIN') or 'ffmpeg')
    if not ffmpeg:
        release_segment_protection(protection_ref)
        raise RuntimeError('未安装 ffmpeg，无法生成事件片段')
    concat_path = None
    try:
        with tempfile.NamedTemporaryFile('w', suffix='.txt', encoding='utf-8', delete=False) as concat_file:
            concat_path = concat_file.name
            for _, path, _ in segments:
                escaped = str(path).replace("'", "'\\''")
                concat_file.write(f"file '{escaped}'\n")
        earliest = segments[0][2]
        offset = max(0.0, (begin - earliest).total_seconds())
        wanted_duration = max(1.0, (end - begin).total_seconds())
        common = [ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-ss', f'{offset:.3f}',
                  '-i', concat_path, '-t', f'{wanted_duration:.3f}']
        copy_run = subprocess.run(
            common + ['-c', 'copy', '-movflags', '+faststart', str(output_path)],
            capture_output=True, text=True, timeout=max(120, int(wanted_duration) * 4),
        )
        if copy_run.returncode != 0 or not output_path.is_file() or output_path.stat().st_size <= 0:
            transcode = subprocess.run(
                common + ['-c:v', 'libx264', '-preset', 'veryfast', '-c:a', 'aac',
                          '-movflags', '+faststart', str(output_path)],
                capture_output=True, text=True, timeout=max(180, int(wanted_duration) * 8),
            )
            if transcode.returncode != 0:
                raise RuntimeError((transcode.stderr or copy_run.stderr or 'ffmpeg 失败')[-1000:])
        from app.services.media_dvr_utils import ffprobe_video_duration_seconds
        actual_seconds = float(ffprobe_video_duration_seconds(str(output_path)) or wanted_duration)
        payload = {
            'asset_id': asset_id,
            'asset_type': 'event_clip',
            'device_id': device_id,
            'task_id': task_id,
            'source_node_id': _node_id(),
            'storage_node_id': _node_id(),
            'storage_generation': int(os.getenv('RECORDING_STORAGE_GENERATION') or 1),
            'storage_scope': 'edge',
            'storage_backend': 'local',
            'object_key': os.path.relpath(output_path, _root()).replace(os.sep, '/'),
            'status': 'ready',
            'start_time': begin.isoformat(),
            'end_time': (begin + timedelta(seconds=actual_seconds)).isoformat(),
            'duration_ms': int(round(actual_seconds * 1000)),
            'file_size': output_path.stat().st_size,
            'content_type': 'video/mp4',
            'checksum': _sha256(output_path),
        }
        upsert_media_asset(payload, authenticated_node_id=_node_id())
        upload_payload = {
            'asset_id': asset_id,
            'asset_type': 'event_clip',
            'device_id': device_id,
            'filename': output_path.name,
            'event_time': event_at.isoformat(),
            'start_time': payload['start_time'],
            'end_time': payload['end_time'],
            'duration_ms': payload['duration_ms'],
            'file_size': payload['file_size'],
            'content_type': payload['content_type'],
            'checksum': payload['checksum'],
            'correlation_id': correlation_id,
            'protection_ref': protection_ref,
        }
        enqueue_center_upload(upload_payload, str(output_path), delete_after_upload=True)
        local_alert = Alert.query.filter_by(correlation_id=correlation_id).first()
        if local_alert:
            local_alert.record_asset_id = asset_id
            local_alert.record_path = f'/video/media/assets/{asset_id}/content'
            db.session.commit()
        flush_pending_uploads_async()
        return asset_id
    except Exception:
        db.session.rollback()
        release_segment_protection(protection_ref)
        raise
    finally:
        if concat_path:
            try:
                os.unlink(concat_path)
            except FileNotFoundError:
                pass
