"""
固定人脸抓取服务：始终使用 VIDEO 根目录 face_det.onnx
"""
import logging
import os
import threading
from typing import Dict, List, Optional

import numpy as np

from app.utils.face_model_paths import (
    FACE_CAPTURE_CLASS_NAMES,
    FACE_CAPTURE_MODEL_PATH,
)
from app.utils.onnx_inference import ONNXInference, get_classes_from_onnx_model

logger = logging.getLogger(__name__)

_detector_lock = threading.Lock()
_detector_instance: Optional[ONNXInference] = None


def _resolve_gpu_id() -> Optional[int]:
    use_gpu = os.getenv('USE_GPU', 'False').lower() == 'true'
    if not use_gpu:
        return None
    raw = os.getenv('FACE_CAPTURE_GPU_ID', os.getenv('GPU_IDS', '0')).strip()
    if not raw:
        return 0
    try:
        return int(raw.split(',')[0].strip())
    except ValueError:
        return 0


def get_face_capture_detector() -> ONNXInference:
    global _detector_instance
    if _detector_instance is not None:
        return _detector_instance

    with _detector_lock:
        if _detector_instance is not None:
            return _detector_instance

        if not os.path.isfile(FACE_CAPTURE_MODEL_PATH):
            raise FileNotFoundError(
                f'人脸抓取模型不存在: {FACE_CAPTURE_MODEL_PATH}，'
                f'请将头部检测 ONNX 放到 VIDEO 根目录并命名为 {os.path.basename(FACE_CAPTURE_MODEL_PATH)}'
            )

        classes_dict = get_classes_from_onnx_model(FACE_CAPTURE_MODEL_PATH) or FACE_CAPTURE_CLASS_NAMES
        conf = float(os.getenv('FACE_CAPTURE_CONF_THRESHOLD', '0.45'))
        iou = float(os.getenv('FACE_CAPTURE_IOU_THRESHOLD', '0.5'))
        _detector_instance = ONNXInference(
            FACE_CAPTURE_MODEL_PATH,
            conf_threshold=conf,
            iou_threshold=iou,
            classes_dict=classes_dict,
            device_id=_resolve_gpu_id(),
        )
        logger.info(
            '人脸抓取模型已加载: path=%s, classes=%s, conf=%s',
            FACE_CAPTURE_MODEL_PATH,
            _detector_instance.classes_dict,
            conf,
        )
        return _detector_instance


def detect_faces(frame: np.ndarray, conf_threshold: Optional[float] = None) -> List[Dict]:
    """对单帧运行固定头部检测模型，返回检测列表（bbox 为 x1,y1,x2,y2）"""
    detector = get_face_capture_detector()
    _, detections = detector.detect(
        frame,
        conf_threshold=conf_threshold,
        draw=False,
    )
    return detections or []
