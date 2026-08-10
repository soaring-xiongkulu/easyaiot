"""
人体姿态分析工具（基于 ultralytics YOLO Pose，参照 AI 模块 pose_inference.py）。
"""
from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_model_cache: dict = {}

DEFAULT_POSE_MODEL = 'yolo26n-pose.pt'
DEFAULT_POSE_CONF = 0.25
POSE_TYPE = 'body17'
KEYPOINT_COUNT = 17

# COCO-17 骨架连接
COCO_SKELETON = [
    (0, 1), (0, 2), (1, 3), (2, 4),
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12),
    (11, 13), (13, 15), (12, 14), (14, 16),
]

PERSON_CLASS_NAMES = frozenset({
    'person', 'people', 'human', '行人', '人体', '人',
})


def _parse_keypoints(result) -> List[Dict[str, Any]]:
    persons = []
    if result.keypoints is None or result.keypoints.data is None:
        return persons
    for kp in result.keypoints.data.cpu().tolist():
        pts = [
            [round(float(x), 1), round(float(y), 1), round(float(c), 4)]
            for x, y, c in kp
        ]
        persons.append({'keypoints': pts})
    return persons


def resolve_pose_model_path(model_file_path: Optional[str] = None) -> str:
    """解析姿态模型路径：环境变量 > AI 根目录 > VIDEO 根目录 > ultralytics 自动下载。"""
    filename = (model_file_path or DEFAULT_POSE_MODEL).strip() or DEFAULT_POSE_MODEL
    if os.path.isabs(filename) and os.path.isfile(filename):
        return filename

    env_path = (os.getenv('POSE_MODEL_PATH') or '').strip()
    if env_path and os.path.isfile(env_path):
        return env_path

    video_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    candidates = [
        os.path.join(video_root, filename),
        os.path.join(video_root, 'models', filename),
    ]

    ai_root = (os.getenv('NODE_REMOTE_AI_ROOT') or os.getenv('AI_ROOT') or '').strip()
    if not ai_root:
        ai_root = os.path.abspath(os.path.join(video_root, '..', 'AI'))
    candidates.extend([
        os.path.join(ai_root, filename),
        os.path.join(ai_root, 'models', filename),
    ])

    for path in candidates:
        if os.path.isfile(path):
            return path

    return filename


def _get_yolo_pose_model(abs_path: str):
    from ultralytics import YOLO

    path = resolve_pose_model_path(abs_path)
    mtime = os.path.getmtime(path) if os.path.isfile(path) else 0
    cache_key = (path, mtime)
    with _lock:
        if cache_key in _model_cache:
            return _model_cache[cache_key]
        model = YOLO(path)
        _model_cache[cache_key] = model
        return model


def load_pose_model(config: Optional[Dict[str, Any]] = None):
    """加载并缓存姿态模型。"""
    cfg = config or {}
    model_path = cfg.get('model_file_path') or DEFAULT_POSE_MODEL
    try:
        model = _get_yolo_pose_model(model_path)
        logger.info('人体姿态模型已加载: %s', resolve_pose_model_path(model_path))
        return model
    except Exception as exc:
        logger.error('人体姿态模型加载失败: %s', exc)
        return None


def _default_pose_config() -> Dict[str, Any]:
    return {
        'enabled': False,
        'model_file_path': DEFAULT_POSE_MODEL,
        'conf': DEFAULT_POSE_CONF,
        'trigger': 'on_interval',
        'interval_frames': 12,
    }


def load_pose_config_from_env() -> Dict[str, Any]:
    """从环境变量加载姿态分析配置（算法子进程）。"""
    enabled = (os.getenv('POSE_ANALYSIS_ENABLED') or '').strip().lower() in ('1', 'true', 'yes')
    cfg = _default_pose_config()
    cfg['enabled'] = enabled
    if not enabled:
        return cfg

    raw = (os.getenv('POSE_ANALYSIS_CONFIG') or '').strip()
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                cfg.update(parsed)
        except Exception:
            pass

    cfg['model_file_path'] = (
        os.getenv('POSE_MODEL_FILE_PATH')
        or cfg.get('model_file_path')
        or DEFAULT_POSE_MODEL
    )
    try:
        cfg['conf'] = float(os.getenv('POSE_CONF', cfg.get('conf', DEFAULT_POSE_CONF)))
    except (TypeError, ValueError):
        cfg['conf'] = DEFAULT_POSE_CONF
    cfg['trigger'] = os.getenv('POSE_TRIGGER', cfg.get('trigger', 'on_interval'))
    try:
        cfg['interval_frames'] = int(os.getenv('POSE_INTERVAL_FRAMES', cfg.get('interval_frames', 12)))
    except (TypeError, ValueError):
        cfg['interval_frames'] = 12
    cfg['enabled'] = True
    return cfg


def load_pose_config_from_task(task) -> Dict[str, Any]:
    """从 AlgorithmTask 加载姿态分析配置。"""
    cfg = _default_pose_config()
    if not task or not (
        bool(getattr(task, 'pose_analysis_enabled', False))
        or bool(getattr(task, 'pose_intent_enabled', False))
    ):
        return cfg

    cfg['enabled'] = True
    raw = getattr(task, 'pose_analysis_config', None)
    if raw:
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else (raw or {})
            if isinstance(parsed, dict):
                cfg.update(parsed)
        except Exception:
            pass
    cfg['enabled'] = True
    return cfg


def _has_person_detection(detections: Optional[List[Dict[str, Any]]]) -> bool:
    if not detections:
        return False
    for det in detections:
        name = str(det.get('class_name', '')).strip().lower()
        if name in PERSON_CLASS_NAMES:
            return True
    return False


def should_run_pose_analysis(
    config: Dict[str, Any],
    *,
    frame_number: int,
    detections: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    if not config or not config.get('enabled'):
        return False
    trigger = str(config.get('trigger', 'on_interval')).lower()
    if trigger == 'always':
        return True
    if trigger == 'on_person':
        return _has_person_detection(detections)
    interval = max(1, int(config.get('interval_frames', 12)))
    return frame_number % interval == 0


def run_pose_analysis(
    model,
    frame_bgr: np.ndarray,
    conf: float = DEFAULT_POSE_CONF,
) -> List[Dict[str, Any]]:
    """对单帧执行姿态估计，返回 persons 列表。"""
    if model is None or frame_bgr is None or getattr(frame_bgr, 'size', 0) == 0:
        return []
    try:
        result = model.predict(frame_bgr, conf=conf, verbose=False)[0]
        return _parse_keypoints(result)
    except Exception as exc:
        logger.warning('姿态分析推理失败: %s', exc)
        return []


def plot_pose_on_frame(
    model,
    frame_bgr: np.ndarray,
    conf: float = DEFAULT_POSE_CONF,
) -> tuple[np.ndarray, List[Dict[str, Any]]]:
    """推理并返回带骨架标注的帧与关键点。"""
    if model is None or frame_bgr is None or getattr(frame_bgr, 'size', 0) == 0:
        return frame_bgr, []
    try:
        result = model.predict(frame_bgr, conf=conf, verbose=False)[0]
        persons = _parse_keypoints(result)
        plotted = result.plot()
        return plotted, persons
    except Exception as exc:
        logger.warning('姿态分析绘制失败: %s', exc)
        return frame_bgr, []


def draw_pose_skeleton(
    frame_bgr: np.ndarray,
    persons: List[Dict[str, Any]],
    *,
    keypoint_threshold: float = 0.25,
) -> np.ndarray:
    """在帧上绘制 COCO-17 骨架（用于推流叠层，避免重复推理）。"""
    if frame_bgr is None or not persons:
        return frame_bgr
    output = frame_bgr.copy()
    for person in persons:
        keypoints = person.get('keypoints') or []
        if len(keypoints) < KEYPOINT_COUNT:
            continue
        for i, j in COCO_SKELETON:
            if i >= len(keypoints) or j >= len(keypoints):
                continue
            x1, y1, c1 = keypoints[i]
            x2, y2, c2 = keypoints[j]
            if c1 < keypoint_threshold or c2 < keypoint_threshold:
                continue
            cv2.line(
                output,
                (int(x1), int(y1)),
                (int(x2), int(y2)),
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
        for x, y, c in keypoints:
            if c < keypoint_threshold:
                continue
            cv2.circle(output, (int(x), int(y)), 3, (0, 0, 255), -1, cv2.LINE_AA)
    return output


def serialize_pose_persons(persons: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """序列化姿态结果供告警/后处理透传。"""
    if not persons:
        return []
    return [
        {
            'keypoints': person.get('keypoints') or [],
            'keypointCount': KEYPOINT_COUNT,
            'poseType': POSE_TYPE,
        }
        for person in persons
    ]


def build_pose_result_payload(persons: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        'count': len(persons),
        'persons': serialize_pose_persons(persons),
        'keypointCount': KEYPOINT_COUNT,
        'poseType': POSE_TYPE,
    }


_pose_model_singleton = None
_pose_model_lock = threading.Lock()


def get_pose_model_for_task(config: Optional[Dict[str, Any]] = None):
    """Worker 侧单例加载姿态模型（iot-sink 后处理进程内使用）。"""
    global _pose_model_singleton
    with _pose_model_lock:
        if _pose_model_singleton is None:
            _pose_model_singleton = load_pose_model(config)
        return _pose_model_singleton


def run_pose_analysis_from_image_path(
    image_path: str,
    config: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """从告警图片路径执行姿态分析（供 iot-sink Worker 异步调用）。"""
    if not image_path or not os.path.isfile(image_path):
        logger.warning('姿态分析跳过：图片不存在 %s', image_path)
        return []
    try:
        frame = cv2.imread(image_path)
        if frame is None or frame.size == 0:
            logger.warning('姿态分析跳过：无法读取图片 %s', image_path)
            return []
    except Exception as exc:
        logger.warning('姿态分析读图失败 %s: %s', image_path, exc)
        return []

    cfg = config or _default_pose_config()
    model = get_pose_model_for_task(cfg)
    if model is None:
        return []
    conf = float(cfg.get('conf', DEFAULT_POSE_CONF))
    return run_pose_analysis(model, frame, conf=conf)
