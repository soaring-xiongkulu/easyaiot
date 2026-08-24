"""
告警图片落盘根目录解析。

与 DEVICE/docker-compose 中 iot-sink 挂载保持一致时：
  volumes:
    - ../VIDEO/alert_images:/app/alert_images

算法进程（或 VIDEO 容器）需设置：
  ALERT_IMAGES_DIR=/app/alert_images
且挂载同一宿主机目录到该路径，这样 Kafka 消息里的绝对路径在 iot-sink 容器内同样指向 `/app/alert_images/...`，MinIO 上传可读。
"""
import os
import re
from datetime import datetime
from typing import Dict, Optional


_SAFE_IMAGE_PART_PATTERN = re.compile(r'[^A-Za-z0-9._-]+')


def _safe_image_part(value, fallback: str) -> str:
    """清洗告警图片文件名片段，避免类别名形成子目录或路径穿越。"""
    normalized = _SAFE_IMAGE_PART_PATTERN.sub('-', str(value or '').strip()).strip('.-_')
    return normalized or fallback


def build_alert_image_filename(
        captured_at: datetime,
        frame_number: int,
        detection: Dict,
        *,
        event_id: Optional[str] = None,
) -> str:
    """构建模型和事件级唯一的告警图片文件名。"""
    timestamp = captured_at.strftime('%Y%m%d_%H%M%S_%f')
    model_id = _safe_image_part(detection.get('model_id'), 'unknown-model')
    track_id = _safe_image_part(detection.get('track_id', 0), '0')
    class_name = _safe_image_part(detection.get('class_name'), 'unknown')
    event_part = _safe_image_part(event_id, 'no-event')[:36]
    return (
        f'{timestamp}_frame{int(frame_number)}_model{model_id}_'
        f'track{track_id}_{class_name}_{event_part}.jpg'
    )


def resolve_alert_images_root(project_video_root: str) -> str:
    """
    解析告警图片存储根目录（其下仍为 task_{TASK_ID}/{device_id}/ 结构）。

    优先级：
    1. 环境变量 ALERT_IMAGES_DIR（Docker 推荐 /app/alert_images）
    2. 集群模式 CephFS：/mnt/easyaiot-media/alert_images
    3. 默认：{project_video_root}/alert_images（本地开发未配置时）
    """
    try:
        from cluster_storage import get_alert_images_dir
        return get_alert_images_dir(project_video_root)
    except ImportError:
        raw = (os.getenv('ALERT_IMAGES_DIR') or '').strip()
        if raw:
            return os.path.abspath(os.path.expanduser(raw))
        base = (project_video_root or '').rstrip(os.sep)
        return os.path.join(base, 'alert_images')
