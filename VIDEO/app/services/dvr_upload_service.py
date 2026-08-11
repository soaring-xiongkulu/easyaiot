"""
DVR 段上传流水线：已迁移至 iot-sink（NFS 读盘 → MinIO → Playback/告警回填）。
VIDEO 仅转发 Hook/Kafka 事件到 sink，不再直传 MinIO。
"""
import logging
import os
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


def process_dvr_event(event: Dict[str, Any]) -> bool:
    """处理单条 DVR 事件：统一转发 iot-sink（NFS + MinIO 在 sink 侧完成）。"""
    if not event:
        return False
    return _forward_dvr_to_sink(event)
