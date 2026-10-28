"""训练场投放：前端模拟人 → 真实 InferEvent → POST 引擎。

生产链路（run.py 注册的 /video/post blueprint）与隔离回归 mock 共用本服务。
模拟目标固定使用 9_000_000+ 的 track_id 段，与真实轨迹天然可区分。
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

SIM_TRACK_MIN = 9_000_000
SIM_TRACK_MAX = 9_999_999
MAX_ACTORS = 100
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
# POST 模板缓存为滑动 TTL：持续有帧则每帧 Touch 续期，空闲超时才 task_cache_miss。
# 投放前按该窗口节流重推模板，保证长期空闲后第一帧也能命中。
TEMPLATE_REFRESH_SEC = 120
_last_template_push: Dict[int, float] = {}


class TrainFrameError(ValueError):
    """入参不合法（前端可直接重试修正）。"""


def _task_model_ids(task) -> List[int]:
    raw = getattr(task, 'model_ids', None)
    if not raw:
        return []
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        return []
    if not isinstance(data, list):
        return []
    return [int(x) for x in data if isinstance(x, (int, float)) and int(x) != 0]


def _ensure_template(task) -> None:
    from app.services.post_template_client import put_template

    now = time.monotonic()
    task_id = int(task.id)
    if now - _last_template_push.get(task_id, 0.0) < TEMPLATE_REFRESH_SEC:
        return
    if put_template(task_id, task=task):
        _last_template_push[task_id] = now


def publish_train_frame(task, device, actors: List[Dict[str, Any]]) -> int:
    """发布一帧模拟检测，返回该帧携带的模拟目标数。空 actors 发布 keepalive 帧。"""
    from app.utils.algo_mqtt_bus import build_infer_event, publish_infer_event

    model_ids = _task_model_ids(task)
    if not model_ids:
        raise TrainFrameError('任务未关联识别模型，无法投放模拟目标')

    _ensure_template(task)
    dets = []
    for a in actors:
        track_id = int(a.get('track_id') or 0)
        if not SIM_TRACK_MIN <= track_id <= SIM_TRACK_MAX:
            raise TrainFrameError(f'track_id 必须在 {SIM_TRACK_MIN}~{SIM_TRACK_MAX} 模拟段内')
        x = min(1.0, max(0.0, float(a.get('x', 0.5))))
        y = min(1.0, max(0.0, float(a.get('y', 0.5))))
        dets.append({
            'model_id': model_ids[0],
            'class_name': 'person',
            'class_id': 0,
            'confidence': 0.95,
            'track_id': track_id,
            'bbox': [(x - 0.02) * FRAME_WIDTH, (y - 0.08) * FRAME_HEIGHT,
                     (x + 0.02) * FRAME_WIDTH, y * FRAME_HEIGHT],
        })

    event = build_infer_event(
        task_id=int(task.id),
        task_type=str(getattr(task, 'task_type', None) or 'realtime'),
        device_id=str(device.id),
        detections=dets,
        task_name=str(getattr(task, 'task_name', None) or ''),
        device_name=str(getattr(device, 'name', None) or device.id),
        frame_width=FRAME_WIDTH,
        frame_height=FRAME_HEIGHT,
        model_ids=model_ids,
        hints={'keepalive': True} if not dets else None,
    )
    if not publish_infer_event(event):
        raise RuntimeError('MQTT 发布失败：请检查消息总线连通性')
    return len(dets)
