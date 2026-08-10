"""
流媒体集群 Hook 入口（SRS / ZLM）→ Kafka 异步入队或同步上传。
"""
import logging

from flask import Blueprint, jsonify, request

from app.services.dvr_device_resolver import resolve_device_from_hook
from app.services.dvr_upload_service import process_dvr_event
from app.services.media_kafka_service import (
    build_event_from_srs_hook,
    build_event_from_zlm_hook,
    enqueue_srs_dvr_hook,
    enqueue_zlm_record_hook,
    is_hybrid_upload_mode,
    is_kafka_upload_mode,
    is_snap_kafka_mode,
    publish_dvr_event,
    publish_snap_event,
)
from app.services.snap_upload_service import build_snap_event, process_snap_event

logger = logging.getLogger(__name__)

media_hook_bp = Blueprint('media_hook', __name__)


def _hook_ok():
    return jsonify({'code': 0, 'msg': None})


@media_hook_bp.route('/hook/srs/on_dvr', methods=['POST'])
def srs_on_dvr():
    data = request.get_json(silent=True) or {}
    if not data.get('stream') and not data.get('file'):
        return _hook_ok()
    device_id, _ = resolve_device_from_hook(data.get('stream', ''), data.get('file', ''))
    if is_kafka_upload_mode():
        enqueue_srs_dvr_hook(data, device_id=device_id)
        if not is_hybrid_upload_mode():
            return _hook_ok()
    event = build_event_from_srs_hook(data, device_id=device_id)
    if is_hybrid_upload_mode() or not is_kafka_upload_mode():
        process_dvr_event(event)
    return _hook_ok()


@media_hook_bp.route('/hook/srs/on_publish', methods=['POST'])
def srs_on_publish():
    """转发至现有 on_publish 逻辑（流冲突检测）。"""
    from app.blueprints.camera import on_publish_callback
    return on_publish_callback()


@media_hook_bp.route('/hook/srs/on_unpublish', methods=['POST'])
def srs_on_unpublish():
    return _hook_ok()


@media_hook_bp.route('/hook/snap/completed', methods=['POST'])
def snap_completed():
    """抓拍完成通知：本地文件已落盘，请求上传 MinIO。"""
    data = request.get_json(silent=True) or {}
    device_id = (data.get('device_id') or '').strip()
    file_path = data.get('file_path') or data.get('file') or ''
    if not device_id or not file_path:
        return _hook_ok()
    event = build_snap_event(
        device_id,
        file_path,
        source=data.get('source') or 'algorithm',
        task_id=data.get('task_id'),
        space_id=data.get('space_id'),
    )
    if is_snap_kafka_mode():
        publish_snap_event(event)
        return _hook_ok()
    process_snap_event(event)
    return _hook_ok()


@media_hook_bp.route('/hook/zlm/on_record_mp4', methods=['POST'])
@media_hook_bp.route('/hook/zlm/on_record_ts', methods=['POST'])
def zlm_on_record():
    data = request.get_json(silent=True) or {}
    file_path = data.get('file_path', '') or data.get('file_name', '')
    stream = data.get('stream', '') or ''
    if not file_path and not stream:
        return _hook_ok()
    device_id, _ = resolve_device_from_hook(stream, file_path)
    if is_kafka_upload_mode():
        enqueue_zlm_record_hook(data, device_id=device_id)
        if not is_hybrid_upload_mode():
            return _hook_ok()
    event = build_event_from_zlm_hook(data, device_id=device_id)
    if is_hybrid_upload_mode() or not is_kafka_upload_mode():
        process_dvr_event(event)
    return _hook_ok()
