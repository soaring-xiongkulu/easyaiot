"""车牌抓取与识别服务（固定 ONNX 模型，供独立队列 Worker 使用）"""
import logging
import os
import threading
from typing import Any, Dict, List, Optional

import numpy as np

from app.utils.plate_model_paths import PLATE_DETECT_MODEL_PATH, PLATE_REC_MODEL_PATH
from app.utils.plate_recognition.pipeline import PlatePipeline, PlateResult

logger = logging.getLogger(__name__)

PLATE_CAPTURE_CONF_THRESHOLD = float(os.getenv('PLATE_CAPTURE_CONF_THRESHOLD', '0.25'))
PLATE_CAPTURE_TILT_THRESHOLD = float(os.getenv('PLATE_CAPTURE_TILT_THRESHOLD', '3.0'))

_pipeline: Optional[PlatePipeline] = None
_lock = threading.Lock()


def get_plate_pipeline() -> PlatePipeline:
    global _pipeline
    with _lock:
        if _pipeline is None:
            _pipeline = PlatePipeline(
                PLATE_DETECT_MODEL_PATH,
                PLATE_REC_MODEL_PATH,
                tilt_threshold=PLATE_CAPTURE_TILT_THRESHOLD,
            )
            logger.info(
                "车牌识别流水线已加载: detect=%s, rec=%s",
                PLATE_DETECT_MODEL_PATH,
                PLATE_REC_MODEL_PATH,
            )
        return _pipeline


def detect_and_recognize_plates(frame: np.ndarray) -> List[Dict[str, Any]]:
    """检测并识别帧中所有车牌，返回结构化结果列表。"""
    pipeline = get_plate_pipeline()
    results: List[PlateResult] = pipeline.predict(frame, conf=PLATE_CAPTURE_CONF_THRESHOLD)
    output: List[Dict[str, Any]] = []
    for item in results:
        if not item.plate_no:
            continue
        output.append({
            'plate_no': item.plate_no,
            'plate_color': item.plate_color,
            'detect_conf': item.detect_conf,
            'plate_type': item.plate_type,
            'tilt_angle': item.tilt_angle,
            'is_tilted': item.is_tilted,
            'rect': item.rect,
            'landmarks': item.landmarks,
        })
    return output
