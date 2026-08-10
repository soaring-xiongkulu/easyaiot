"""
抓拍媒体客户端：本地 CephFS 暂存 + Kafka 入队，或直接同步上传。
"""
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

import cv2
import numpy as np

from app.services.media_kafka_service import is_snap_kafka_mode, publish_snap_event
from app.services.playback_disk_guard_service import get_snap_staging_dir

logger = logging.getLogger(__name__)


def stage_snap_frame(
    device_id: str,
    frame: np.ndarray,
    *,
    source: str = 'algorithm',
    task_id: Optional[int] = None,
    jpeg_quality: int = 90,
) -> bool:
    """将抓拍帧写入 MEDIA_SNAP_DIR 并触发上传流水线。"""
    ok, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
    if not ok:
        return False
    return stage_snap_bytes(
        device_id,
        encoded.tobytes(),
        source=source,
        task_id=task_id,
    )


def stage_snap_bytes(
    device_id: str,
    image_bytes: bytes,
    *,
    source: str = 'algorithm',
    task_id: Optional[int] = None,
) -> bool:
    snap_root = get_snap_staging_dir()
    device_dir = os.path.join(snap_root, str(device_id))
    os.makedirs(device_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{uuid.uuid4().hex[:8]}_{ts}.jpg'
    file_path = os.path.join(device_dir, filename)

    try:
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
    except OSError as e:
        logger.error('抓拍暂存失败 device=%s path=%s error=%s', device_id, file_path, e)
        return False

    from app.services.snap_upload_service import build_snap_event, process_snap_event
    event = build_snap_event(device_id, file_path, source=source, task_id=task_id)

    if is_snap_kafka_mode():
        if publish_snap_event(event):
            return True
        logger.warning('抓拍 Kafka 入队失败，回退同步上传 device=%s', device_id)

    return process_snap_event(event)
