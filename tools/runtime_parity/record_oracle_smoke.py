"""Oracle smoke recorder — non-placeholder python golden for Phase 0 G-0.3.

Reads oracle context from ACME_ORACLE_ROOT (read-only); writes artifacts under
candidate golden/python/<case>/ with status=recorded.

Detection priority on local Intel sample media:
  1. ultralytics YOLO (if installed)
  2. ONNX yolo11n.onnx
  3. synthetic geometry (only when frames unreadable or both infer paths fail;
     meta/layer must declare limitations — never masquerade as live oracle VIDEO)
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .artifacts import layer_file_map, _write_json
from .manifest import CaseSpec, find_case, load_manifest, parse_cases
from .motion_track_sample import sample_motion_gate, sample_tracking
from .schedule_sample import synthetic_patrol_schedule, synthetic_snap_schedule
from .paths import candidate_root, golden_dir, oracle_root, testdata_root


P0_CASES = {
    "rt_p0_detect_single_onnx",
    "rt_p0_heartbeat_lifecycle",
    "rt_p0_alert_hook_roi",
}

P1_G42_CASES = {
    "rt_p1_motion_gate",
    "rt_p1_tracking_stable",
}

P0_G43_CASES = {
    "snap_p0_cron_slot",
    "snap_p0_alert_payload",
    "patrol_p0_pool_interval",
    "patrol_p0_heartbeat_progress",
    "patrol_p1_hybrid_focus",
}

SYNTHETIC_BBOX = [200, 150, 440, 330]
SYNTHETIC_CLASS = "person"
SYNTHETIC_CONFIDENCE = 0.85

YOLO_CONF = 0.25
YOLO_IOU = 0.45
ONNX_CONF = 0.35
ONNX_IOU = 0.5
SCAN_STRIDE = 15
SCAN_MAX_FRAMES = 180

COCO_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
}


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
    best_class: str = SYNTHETIC_CLASS
    best_confidence: float = SYNTHETIC_CONFIDENCE


def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


def _media_path(case: CaseSpec, root: Path, manifest: Dict[str, Any]) -> Path:
    if not case.media_id:
        raise FileNotFoundError(f"case {case.id} has no media_id")
    td = testdata_root(root)
    media_table = manifest.get("media")
    if isinstance(media_table, dict) and case.media_id in media_table:
        entry = media_table[case.media_id]
        rel = entry.get("file") if isinstance(entry, dict) else None
        if rel:
            path = td / rel
        else:
            path = td / "media" / f"{case.media_id}.mp4"
    else:
        path = td / "media" / f"{case.media_id}.mp4"
    if not path.is_file():
        raise FileNotFoundError(f"media missing for {case.id}: {path}")
    return path


def _iter_sampled_frames(media: Path) -> List[Tuple[int, int, Any, int, int]]:
    """Return list of (frame_index, timestamp_ms, frame_bgr, width, height)."""
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


def _det_entry(bbox_xyxy: List[float], class_name: str, confidence: float) -> Dict[str, Any]:
    return {
        "bbox_xyxy": [round(v, 2) for v in bbox_xyxy],
        "class": class_name,
        "confidence": round(confidence, 4),
    }


def _frame_payload(
    frame_index: int,
    timestamp_ms: int,
    detections: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "frame_index": frame_index,
        "timestamp_ms": timestamp_ms,
        "detections": detections,
    }


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


def _onnx_frame_detections(frame: Any, model_path: Path) -> List[Dict[str, Any]]:
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


def _ultralytics_frame_detections(frame: Any, model: Any) -> List[Dict[str, Any]]:
    results = model(frame, conf=YOLO_CONF, iou=YOLO_IOU, verbose=False)
    detections: List[Dict[str, Any]] = []
    for result in results:
        names = result.names
        for box in result.boxes:
            cls_id = int(box.cls[0])
            class_name = names.get(cls_id, f"class_{cls_id}")
            xyxy = box.xyxy[0].tolist()
            detections.append(_det_entry(xyxy, class_name, float(box.conf[0])))
    return detections


def _model_paths() -> List[Path]:
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


def _yolo_pt_candidates() -> List[str]:
    names = ["yolo11n.pt", "yolo11s.pt"]
    paths: List[str] = []
    for root in (oracle_root(), candidate_root()):
        for name in names:
            p = root / "VIDEO" / name
            if p.is_file():
                paths.append(str(p))
    paths.extend(names)
    return paths


def _pick_best_detection(frames: List[Dict[str, Any]]) -> Tuple[Optional[List[float]], str, float]:
    best: Optional[Tuple[float, List[float], str]] = None
    for frame in frames:
        for det in frame.get("detections", []):
            conf = float(det.get("confidence", 0.0))
            bbox = det.get("bbox_xyxy")
            if not bbox:
                continue
            cls = str(det.get("class", SYNTHETIC_CLASS))
            if best is None or conf > best[0]:
                best = (conf, [float(v) for v in bbox], cls)
    if best is None:
        return None, SYNTHETIC_CLASS, SYNTHETIC_CONFIDENCE
    return best[1], best[2], best[0]


def _run_detection(media: Path, *, engine: str = "auto") -> DetectionRun:
    samples = _iter_sampled_frames(media)
    if not samples:
        return _synthetic_run(640, 480, reason="media frames unreadable (cv2 missing or empty video)")

    _, _, _, w, h = samples[0]

    use_ultralytics = engine in ("auto", "ultralytics")
    use_onnx = engine in ("auto", "onnx")

    # 1) ultralytics YOLO (auto path only unless engine=onnx)
    if use_ultralytics and engine != "onnx":
        yolo_model = None
        try:
            from ultralytics import YOLO  # type: ignore

            for candidate in _yolo_pt_candidates():
                try:
                    yolo_model = YOLO(candidate)
                    break
                except Exception:
                    continue
        except ImportError:
            yolo_model = None

        if yolo_model is not None:
            recorded: List[Dict[str, Any]] = []
            for frame_idx, ts_ms, frame, _, _ in samples:
                dets = _ultralytics_frame_detections(frame, yolo_model)
                if dets:
                    recorded.append(_frame_payload(frame_idx, ts_ms, dets))
            if recorded:
                bbox, cls, conf = _pick_best_detection(recorded)
                return DetectionRun(
                    frames=recorded[:3],
                    model=f"ultralytics:{getattr(yolo_model, 'model_name', 'yolo')}",
                    source="oracle_smoke_ultralytics",
                    width=w,
                    height=h,
                    best_bbox=bbox,
                    best_class=cls,
                    best_confidence=conf,
                    limitations=(
                        "Local Intel sample-video inference via ultralytics; not a live oracle "
                        "VIDEO task capture. Replace with record-python before certify parity claims."
                    ),
                )

    # 2) ONNX
    if use_onnx:
        for model_path in _model_paths():
            recorded = []
            for frame_idx, ts_ms, frame, _, _ in samples:
                dets = _onnx_frame_detections(frame, model_path)
                if dets:
                    recorded.append(_frame_payload(frame_idx, ts_ms, dets))
            if recorded:
                bbox, cls, conf = _pick_best_detection(recorded)
                return DetectionRun(
                    frames=recorded[:3],
                    model=str(model_path),
                    source="oracle_smoke_onnx",
                    width=w,
                    height=h,
                    best_bbox=bbox,
                    best_class=cls,
                    best_confidence=conf,
                    limitations=(
                        "Local Intel sample-video ONNX inference; not a live oracle VIDEO task "
                        "capture. Replace with record-python before certify parity claims."
                    ),
                )

    return _synthetic_run(
        w,
        h,
        reason="frames readable but ultralytics YOLO and ONNX yolo11n both unavailable or produced no detections",
    )


def _synthetic_run(width: int, height: int, *, reason: str) -> DetectionRun:
    x1, y1, x2, y2 = SYNTHETIC_BBOX
    frame = _frame_payload(
        0,
        0,
        [_det_entry([float(x1), float(y1), float(x2), float(y2)], SYNTHETIC_CLASS, SYNTHETIC_CONFIDENCE)],
    )
    return DetectionRun(
        frames=[frame],
        model="synthetic_geometry",
        source="oracle_smoke_synthetic",
        width=width,
        height=height,
        synthetic=True,
        best_bbox=[float(x1), float(y1), float(x2), float(y2)],
        best_class=SYNTHETIC_CLASS,
        best_confidence=SYNTHETIC_CONFIDENCE,
        limitations=(
            f"Synthetic bbox stub: {reason}. Not live oracle VIDEO; do not use for certify parity claims."
        ),
    )


def _base_layer(
    case: CaseSpec,
    layer: str,
    *,
    source: str,
    limitations: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "case_id": case.id,
        "layer": layer,
        "executor": "python",
        "task_type": case.task_type,
        "sampled_at": _ts(),
        "source": source,
        "status": "recorded",
        "oracle_root": str(oracle_root()),
    }
    if limitations:
        payload["limitations"] = limitations
    return payload


def _lifecycle_payload(case: CaseSpec, *, source: str, limitations: str) -> Dict[str, Any]:
    task_id = f"{case.id}_smoke"
    process_id = 42420
    log_path = f"logs/{case.id}/runtime.log"
    fields_expected = ["task_id", "process_id", "log_path"]
    is_patrol = (case.task_type or "").lower() == "patrol"
    if is_patrol:
        fields_expected = ["task_id", "process_id", "log_path", "total_patrols", "total_detections"]
    heartbeats: List[Dict[str, Any]] = []
    base_unix = time.time() - 120
    for i in range(12):
        hb: Dict[str, Any] = {
            "seq": i + 1,
            "task_id": task_id,
            "process_id": process_id,
            "log_path": log_path,
            "timestamp_unix": base_unix + i * 10,
        }
        if is_patrol:
            hb["total_patrols"] = i + 1
            hb["total_detections"] = max(0, i // 2)
            hb["progress"] = {
                "dev_0": {
                    "last_patrol_at": "2026-08-09T00:00:00Z",
                    "last_result": "ok",
                    "detection_count": "0",
                }
            }
        heartbeats.append(hb)
    return {
        **_base_layer(case, "L_lifecycle", source=source, limitations=limitations),
        "boot": {"exit_code": 0, "started": True},
        "heartbeats": heartbeats,
        "heartbeat_count": len(heartbeats),
        "fields_expected": fields_expected,
    }


def _detect_payload(case: CaseSpec, root: Path, manifest: Dict[str, Any], det: DetectionRun) -> Dict[str, Any]:
    media = _media_path(case, root, manifest)
    return {
        **_base_layer(case, "L_detect", source=det.source, limitations=det.limitations),
        "media_id": case.media_id,
        "media_path": str(media),
        "frame_size": {"width": det.width, "height": det.height},
        "model": det.model,
        "frames": det.frames,
        "detection_count": sum(len(f.get("detections", [])) for f in det.frames),
    }


def _bbox_in_normalized_roi(bbox: List[float], width: int, height: int) -> bool:
    if width <= 0 or height <= 0:
        return True
    cx = (bbox[0] + bbox[2]) / 2.0 / width
    cy = (bbox[1] + bbox[3]) / 2.0 / height
    return 0.1 <= cx <= 0.9 and 0.1 <= cy <= 0.9


def _alarm_payload(case: CaseSpec, det: DetectionRun) -> Dict[str, Any]:
    hook_port = case.mock_hook_port or 18080
    bbox = det.best_bbox or [float(v) for v in SYNTHETIC_BBOX]
    cls = det.best_class
    conf = det.best_confidence
    in_roi = _bbox_in_normalized_roi(bbox, det.width, det.height)
    alerts = [
        {
            "seq": 1,
            "alert_type": "roi_confidence",
            "bbox_xyxy": [round(v, 2) for v in bbox],
            "class": cls,
            "confidence": round(conf, 4),
            "in_roi": in_roi,
            "cooldown_applied": False,
        }
    ]
    expected_tt = None
    if (case.task_type or "").lower() in ("snap", "snapshot"):
        expected_tt = "snapshot"
    payload = {
        **_base_layer(case, "L_alarm", source=det.source, limitations=det.limitations),
        "hook_url": f"http://127.0.0.1:{hook_port}/alert",
        "alerts": alerts,
        "alert_count": len(alerts),
    }
    if expected_tt:
        payload["expected_task_type"] = expected_tt
    return payload



@dataclass
class CaseRecording:
    source: str
    limitations: str
    det: Optional[DetectionRun] = None


def _record_case(case: CaseSpec, root: Path, manifest: Dict[str, Any], *, engine: str = "auto") -> CaseRecording:
    needs_detect = "L_detect" in case.required_layers or "L_alarm" in case.required_layers
    det: Optional[DetectionRun] = None
    if needs_detect:
        media = _media_path(case, root, manifest)
        det = _run_detection(media, engine=engine)
        source = det.source
        limitations = det.limitations or ""
    else:
        _media_path(case, root, manifest)
        source = "oracle_smoke_local_media"
        limitations = (
            "Smoke lifecycle/schedule recording without live oracle VIDEO; heartbeats/slots are "
            "deterministic stubs. Media path verified from manifest Intel sample-video."
        )
    return CaseRecording(source=source, limitations=limitations, det=det)


def _write_case_golden(case: CaseSpec, root: Path, manifest: Dict[str, Any], *, engine: str = "auto") -> List[Path]:
    out_dir = golden_dir("python", case.id, root)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    rec = _record_case(case, root, manifest, engine=engine)

    def lifecycle() -> Dict[str, Any]:
        return _lifecycle_payload(case, source=rec.source, limitations=rec.limitations)

    def detect() -> Dict[str, Any]:
        if rec.det is None:
            raise RuntimeError(f"case {case.id} requires detection but none was recorded")
        return _detect_payload(case, root, manifest, rec.det)

    def alarm() -> Dict[str, Any]:
        if rec.det is None:
            raise RuntimeError(f"case {case.id} requires detection for alarm layer")
        return _alarm_payload(case, rec.det)

    def motion() -> Dict[str, Any]:
        media = _media_path(case, root, manifest)
        preset = str(case.raw.get("motion_gate_preset") or "sensitive")
        sample = sample_motion_gate(media, preset=preset, frame_skip=4)
        return {
            **_base_layer(case, "L_motion", source="oracle_smoke_motion_gate", limitations=rec.limitations),
            "baseline_triggers": sample.baseline_triggers,
            "motion_triggers": sample.motion_triggers,
            "infer_submits": sample.infer_submits,
            "infer_skips_motion": sample.infer_skips_motion,
            "frames": sample.frames,
        }

    def track() -> Dict[str, Any]:
        media = _media_path(case, root, manifest)
        model_path = _model_paths()[0] if _model_paths() else (root / "RUNTIME" / "models" / "yolov11n.onnx")
        sample = sample_tracking(media, onnx_model=model_path, frame_skip=4)
        return {
            **_base_layer(case, "L_track", source="oracle_smoke_tracking", limitations=rec.limitations),
            "frames": sample.frames,
            "track_switch_count": sample.track_switch_count,
        }

    def schedule() -> Dict[str, Any]:
        cron = str(case.raw.get("cron_expression") or "")
        is_snap = (case.task_type or "").lower() in ("snap", "snapshot")
        if is_snap:
            sched = synthetic_snap_schedule(
                case_id=case.id,
                cron_expression=cron or "*/5 * * * * *",
                duration_sec=20.0,
                interval_sec=5.0,
            )
        else:
            count = int(case.raw.get("device_count") or 1)
            focus = str(case.raw.get("focus_device_id") or "")
            device_ids = []
            for i in range(max(1, count)):
                if i == 0 and focus:
                    device_ids.append(focus)
                else:
                    device_ids.append(f"dev_{i}")
            interval = float(case.raw.get("patrol_interval_sec") or 5)
            # hybrid focus fires more often — smoke uses base interval for stub simplicity
            sched = synthetic_patrol_schedule(
                device_ids=device_ids,
                interval_sec=interval,
                duration_sec=20.0,
                mode=str(case.raw.get("patrol_mode") or "pool"),
            )
        return {
            **_base_layer(case, "L_schedule", source="oracle_smoke_schedule", limitations=rec.limitations),
            **sched,
        }

    builders = {
        "L_lifecycle": lifecycle,
        "L_detect": detect,
        "L_alarm": alarm,
        "L_motion": motion,
        "L_track": track,
        "L_schedule": schedule,
    }
    for layer, fname in layer_file_map(case).items():
        builder = builders.get(layer)
        if builder is None:
            data = {
                **_base_layer(case, layer, source=rec.source, limitations=rec.limitations),
                "_note": f"Layer {layer} smoke stub",
            }
        else:
            data = builder()
        path = out_dir / fname
        _write_json(path, data)
        written.append(path)

    meta = {
        "case_id": case.id,
        "executor": "python",
        "required_layers": case.required_layers,
        "written_at": _ts(),
        "recording": "oracle_smoke",
        "source": rec.source,
        "status": "recorded",
        "oracle_root": str(oracle_root()),
        "artifacts": list(layer_file_map(case).values()),
        "limitations": rec.limitations,
    }
    if rec.det is not None:
        meta["model"] = rec.det.model
        meta["synthetic"] = rec.det.synthetic
    meta_path = out_dir / "meta.json"
    _write_json(meta_path, meta)
    written.append(meta_path)
    return written


def run_record_oracle_smoke(case_id: Optional[str] = None, *, engine: str = "auto") -> int:
    root = candidate_root()
    manifest = load_manifest(root)
    if case_id:
        cases = [find_case(manifest, case_id)]
    else:
        cases = [c for c in parse_cases(manifest) if c.id in P0_CASES | P1_G42_CASES | P0_G43_CASES]

    if not cases:
        print("record-oracle-smoke: no cases to record", file=sys.stderr)
        return 1

    print(f"record-oracle-smoke: oracle_root={oracle_root()} candidate={root}")
    exit_code = 0
    for case in cases:
        try:
            paths = _write_case_golden(case, root, manifest, engine=engine)
            print(f"record-oracle-smoke: case={case.id} executor=python")
            for p in paths:
                print(f"  wrote {p}")
        except (FileNotFoundError, KeyError, RuntimeError) as exc:
            print(f"FAIL record-oracle-smoke case={case.id}: {exc}", file=sys.stderr)
            exit_code = 1
    return exit_code
