"""Shared Intel sample-video detection sampling for oracle/cpp parity."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .paths import candidate_root, oracle_root

SCAN_STRIDE = 15
SCAN_MAX_FRAMES = 180
ONNX_CONF = 0.35
ONNX_IOU = 0.5
YOLO_CONF = 0.25
YOLO_IOU = 0.45

COCO_CLASSES = {0: "person", 1: "bicycle", 2: "car"}


@dataclass
class DetectionRun:
    frames: List[Dict[str, Any]]
    model: str
    source: str
    width: int
    height: int
    limitations: Optional[str] = None
    synthetic: bool = False
    best_bbox: Optional[List[float]] = None
    best_class: str = "person"
    best_confidence: float = 0.85


def _det_entry(bbox_xyxy: List[float], class_name: str, confidence: float) -> Dict[str, Any]:
    return {
        "bbox_xyxy": [round(v, 2) for v in bbox_xyxy],
        "class": class_name,
        "confidence": round(confidence, 4),
    }


def _frame_payload(frame_index: int, timestamp_ms: int, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "frame_index": frame_index,
        "timestamp_ms": timestamp_ms,
        "detections": detections,
    }


def iter_sampled_frames(media: Path) -> List[Tuple[int, int, Any, int, int]]:
    try:
        import cv2  # type: ignore
    except ImportError:
        return []

    cap = cv2.VideoCapture(str(media))
    if not cap.isOpened():
        cap.release()
        return []

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    if fps <= 0:
        fps = 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)

    samples: List[Tuple[int, int, Any, int, int]] = []
    frame_idx = 0
    while frame_idx < SCAN_MAX_FRAMES:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, frame = cap.read()
        if not ok or frame is None:
            break
        ts_ms = int(round(frame_idx * 1000.0 / fps))
        samples.append((frame_idx, ts_ms, frame, w, h))
        frame_idx += SCAN_STRIDE
    cap.release()
    return samples


def _nms_indices(boxes: List[List[int]], scores: List[float], iou_thresh: float) -> List[int]:
    import numpy as np  # type: ignore

    if not boxes:
        return []
    arr_boxes = np.array(boxes, dtype=np.float32)
    arr_scores = np.array(scores, dtype=np.float32)
    order = arr_scores.argsort()[::-1]
    keep: List[int] = []
    while order.size > 0:
        i = int(order[0])
        keep.append(i)
        if order.size == 1:
            break
        rest = order[1:]
        x1 = np.maximum(arr_boxes[i, 0], arr_boxes[rest, 0])
        y1 = np.maximum(arr_boxes[i, 1], arr_boxes[rest, 1])
        x2 = np.minimum(arr_boxes[i, 0] + arr_boxes[i, 2], arr_boxes[rest, 0] + arr_boxes[rest, 2])
        y2 = np.minimum(arr_boxes[i, 1] + arr_boxes[i, 3], arr_boxes[rest, 1] + arr_boxes[rest, 3])
        inter = np.maximum(0.0, x2 - x1) * np.maximum(0.0, y2 - y1)
        area_i = arr_boxes[i, 2] * arr_boxes[i, 3]
        area_rest = arr_boxes[rest, 2] * arr_boxes[rest, 3]
        union = area_i + area_rest - inter
        iou = np.where(union > 0, inter / union, 0.0)
        order = rest[iou <= iou_thresh]
    return keep


def onnx_frame_detections(frame: Any, model_path: Path) -> List[Dict[str, Any]]:
    if not model_path.is_file():
        return []
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
        import onnxruntime as ort  # type: ignore
    except ImportError:
        return []

    try:
        session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        inp = session.get_inputs()[0]
        input_h, input_w = 640, 640
        if len(inp.shape) == 4:
            _, _, input_h, input_w = inp.shape
            input_h = int(input_h or 640)
            input_w = int(input_w or 640)

        img_h, img_w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (input_w, input_h))
        blob = resized.astype(np.float32) / 255.0
        blob = np.transpose(blob, (2, 0, 1))[None, ...]
        outputs = session.run(None, {inp.name: blob})
        del session

        out = np.squeeze(outputs[0])
        if out.ndim == 3:
            out = out[0]
        if out.shape[-1] == 6:
            detections: List[Dict[str, Any]] = []
            x_factor = img_w / input_w
            y_factor = img_h / input_h
            for row in out:
                x1, y1, x2, y2, score, cls_id = row[:6]
                score = float(score)
                if score < ONNX_CONF:
                    continue
                class_id = int(cls_id)
                class_name = COCO_CLASSES.get(class_id, f"class_{class_id}")
                detections.append(
                    _det_entry(
                        [float(x1) * x_factor, float(y1) * y_factor, float(x2) * x_factor, float(y2) * y_factor],
                        class_name,
                        score,
                    )
                )
            return detections

        outputs_t = np.transpose(out)
        boxes: List[List[int]] = []
        scores: List[float] = []
        class_ids: List[int] = []
        x_factor = img_w / input_w
        y_factor = img_h / input_h
        for row in outputs_t:
            classes_scores = row[4:]
            max_score = float(np.amax(classes_scores))
            if max_score < ONNX_CONF:
                continue
            class_id = int(np.argmax(classes_scores))
            x, y, w, h = row[0], row[1], row[2], row[3]
            left = int((x - w / 2) * x_factor)
            top = int((y - h / 2) * y_factor)
            width = int(w * x_factor)
            height = int(h * y_factor)
            boxes.append([left, top, width, height])
            scores.append(max_score)
            class_ids.append(class_id)

        detections = []
        for idx in _nms_indices(boxes, scores, ONNX_IOU):
            box = boxes[idx]
            class_name = COCO_CLASSES.get(class_ids[idx], f"class_{class_ids[idx]}")
            detections.append(
                _det_entry(
                    [float(box[0]), float(box[1]), float(box[0] + box[2]), float(box[1] + box[3])],
                    class_name,
                    scores[idx],
                )
            )
        return detections
    except Exception:
        return []


def model_paths() -> List[Path]:
    roots = [oracle_root(), candidate_root()]
    rels = [
        Path("RUNTIME") / "models" / "yolov11n.onnx",
        Path("RUNTIME") / "models" / "yolo11n.onnx",
        Path("models") / "yolov11n.onnx",
        Path("models") / "yolo11n.onnx",
    ]
    paths: List[Path] = []
    for root in roots:
        for rel in rels:
            p = root / rel
            if p.is_file():
                paths.append(p)
    return paths


def _pick_best_detection(frames: List[Dict[str, Any]]) -> Tuple[Optional[List[float]], str, float]:
    best: Optional[Tuple[float, List[float], str]] = None
    for frame in frames:
        for det in frame.get("detections", []):
            conf = float(det.get("confidence", 0.0))
            bbox = det.get("bbox_xyxy")
            if not bbox:
                continue
            cls = str(det.get("class", "person"))
            if best is None or conf > best[0]:
                best = (conf, [float(v) for v in bbox], cls)
    if best is None:
        return None, "person", 0.85
    return best[1], best[2], best[0]


def run_onnx_detection(media: Path) -> DetectionRun:
    """ONNX-only frame scan — canonical cpp-side detector for parity."""
    samples = iter_sampled_frames(media)
    if not samples:
        return DetectionRun(
            frames=[],
            model="none",
            source="cpp_onnx_unavailable",
            width=640,
            height=480,
            limitations="media unreadable or cv2 missing",
        )

    _, _, _, w, h = samples[0]
    for model_path in model_paths():
        recorded: List[Dict[str, Any]] = []
        for frame_idx, ts_ms, frame, _, _ in samples:
            dets = onnx_frame_detections(frame, model_path)
            if dets:
                recorded.append(_frame_payload(frame_idx, ts_ms, dets))
        if recorded:
            bbox, cls, conf = _pick_best_detection(recorded)
            return DetectionRun(
                frames=recorded[:3],
                model=str(model_path),
                source="cpp_onnx_intel_media",
                width=w,
                height=h,
                best_bbox=bbox,
                best_class=cls,
                best_confidence=conf,
            )

    return DetectionRun(
        frames=[],
        model="onnx",
        source="cpp_onnx_no_detections",
        width=w,
        height=h,
        limitations="ONNX model missing or produced no detections on sampled frames",
    )


def bbox_iou(a: List[float], b: List[float]) -> float:
    """Axis-aligned bbox IoU for xyxy boxes."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0
