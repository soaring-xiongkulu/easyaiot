"""
算法任务统一检测入口：Ultralytics(.pt) 与 ONNXInference(.onnx)
"""
import threading
from typing import Any, Callable, Dict, List, Optional

from app.utils.onnx_inference import ONNXInference

# Ultralytics YOLO 非线程安全：多 worker 并发 predict 会在 fuse()/setup_model 竞态（AttributeError: bn）
_MODEL_INFER_LOCKS: Dict[int, threading.Lock] = {}
_MODEL_INFER_LOCKS_GUARD = threading.Lock()


def _get_model_infer_lock(model: Any) -> threading.Lock:
    key = id(model)
    with _MODEL_INFER_LOCKS_GUARD:
        lock = _MODEL_INFER_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _MODEL_INFER_LOCKS[key] = lock
        return lock


def is_onnx_detector(model: Any) -> bool:
    return isinstance(model, ONNXInference)


def is_end2end_ultralytics_model(model: Any) -> bool:
    """YOLO26 等 end2end 模型内置 NMS，推理参数需与普通 YOLO 区分。"""
    if is_yolo26_model(model):
        return True
    if is_onnx_detector(model):
        return False
    inner = getattr(model, 'model', None)
    if inner is not None and bool(getattr(inner, 'end2end', False)):
        return True
    yaml_cfg = getattr(inner, 'yaml', None) if inner is not None else None
    if isinstance(yaml_cfg, dict) and yaml_cfg.get('end2end'):
        return True
    return False


def is_yolo26_model(
    model: Any,
    *,
    model_path: str = '',
    model_id: Optional[int] = None,
) -> bool:
    """识别 YOLO26 模型（兼容 end2end 属性未暴露的旧版 ultralytics 加载结果）。"""
    if model_id == -3:
        return True
    path_lower = str(model_path or '').lower()
    if 'yolo26' in path_lower:
        return True
    if is_onnx_detector(model):
        return False
    overrides = getattr(model, 'overrides', None) or {}
    if 'yolo26' in str(overrides.get('model', '')).lower():
        return True
    inner = getattr(model, 'model', None)
    if inner is not None:
        if bool(getattr(inner, 'end2end', False)):
            return True
        yaml_cfg = getattr(inner, 'yaml', None)
        if isinstance(yaml_cfg, dict):
            yaml_file = str(yaml_cfg.get('yaml_file', '')).lower()
            if 'yolo26' in yaml_file or yaml_cfg.get('end2end'):
                return True
    return False


def warmup_model_detection(
    model: Any,
    *,
    infer_device: str = 'cpu',
    imgsz: int = 640,
    conf: float = 0.25,
    iou: float = 0.45,
) -> None:
    """单线程预热：完成 fuse 与 predictor 初始化，避免多 worker 并发首次 predict 竞态。"""
    import numpy as np

    size = max(32, int(imgsz))
    dummy = np.zeros((size, size, 3), dtype=np.uint8)
    run_model_detection(
        model,
        dummy,
        conf=conf,
        iou=iou,
        imgsz=imgsz,
        infer_device=infer_device,
    )


def run_model_detection(
    model: Any,
    frame,
    *,
    conf: float = 0.25,
    iou: float = 0.45,
    imgsz: int = 640,
    infer_device: str = 'cpu',
    should_keep: Optional[Callable[[str], bool]] = None,
) -> List[Dict[str, Any]]:
    """对单帧执行检测，返回统一格式的检测列表。"""
    with _get_model_infer_lock(model):
        if is_onnx_detector(model):
            _, raw_detections = model.detect(frame, conf_threshold=conf, iou_threshold=iou, draw=False)
            detections = []
            for det in raw_detections:
                class_name = det['class_name']
                if should_keep and not should_keep(class_name):
                    continue
                x1, y1, x2, y2 = det['bbox']
                detections.append({
                    'class_id': int(det.get('class', 0)),
                    'class_name': class_name,
                    'confidence': float(det['confidence']),
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                })
            return detections

        predict_kwargs = dict(
            conf=conf,
            iou=iou,
            imgsz=imgsz,
            verbose=False,
            half=False,
            device=infer_device,
        )
        if is_end2end_ultralytics_model(model) or is_yolo26_model(model):
            # YOLO26 end2end：显式放宽 max_det，避免内置 NMS 后仅剩少量高置信大目标
            predict_kwargs['max_det'] = 300
            # end2end 模型 iou 仅作用于内置 NMS，略提高可保留更多重叠目标（如人群）
            predict_kwargs['iou'] = max(iou, 0.7)
        results = model(frame, **predict_kwargs)
        result = results[0]
        detections = []
        if result.boxes is None or len(result.boxes) == 0:
            return detections

        boxes = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy().astype(int)
        names = getattr(model, 'names', {})

        for box, score, cls_id in zip(boxes, confidences, class_ids):
            x1, y1, x2, y2 = map(int, box)
            class_name = names[cls_id] if names else f'class_{cls_id}'
            if should_keep and not should_keep(class_name):
                continue
            detections.append({
                'class_id': int(cls_id),
                'class_name': class_name,
                'confidence': float(score),
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
            })
        return detections
