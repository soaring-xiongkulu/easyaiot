"""Motion gate + tracking oracle sampling for G-4.2 parity golden."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .detect_sample import bbox_iou


@dataclass
class MotionSampleResult:
    baseline_triggers: int
    motion_triggers: int
    infer_submits: int
    infer_skips_motion: int
    frames: List[Dict[str, Any]]


@dataclass
class TrackSampleResult:
    frames: List[Dict[str, Any]]
    track_switch_count: int


def _import_motion_gate():
    candidate = Path(__file__).resolve().parents[2]
    for video_root in (
        candidate / "VIDEO",
        Path(os.environ.get("ACME_ORACLE_ROOT", "F:/acme")) / "VIDEO",
    ):
        if video_root.is_dir() and str(video_root) not in sys.path:
            sys.path.insert(0, str(video_root))
    from app.utils.motion_gate import MotionGate, MotionGateConfig  # type: ignore

    return MotionGate, MotionGateConfig


class OracleSimpleTracker:
    """Minimal IoU tracker for oracle golden (aligned with VIDEO SimpleTracker core)."""

    def __init__(self, similarity_threshold: float = 0.2, max_age: int = 25, smooth_alpha: float = 0.25):
        self.similarity_threshold = similarity_threshold
        self.max_age = max_age
        self.smooth_alpha = smooth_alpha
        self.tracks: Dict[int, Dict[str, Any]] = {}
        self.next_id = 1

    @staticmethod
    def _similarity(box1: List[float], box2: List[float]) -> float:
        return bbox_iou(box1, box2)

    def update(self, detections: List[Dict[str, Any]], frame_number: int) -> List[Dict[str, Any]]:
        remove = [tid for tid, tr in self.tracks.items() if tr["age"] > self.max_age]
        for tid in remove:
            del self.tracks[tid]

        matched: set[int] = set()
        out: List[Dict[str, Any]] = []
        for det in detections:
            bbox = [float(v) for v in (det.get("bbox") or det.get("bbox_xyxy") or [])]
            best_tid = None
            best_sim = 0.0
            for tid, tr in self.tracks.items():
                if tid in matched:
                    continue
                sim = self._similarity(bbox, tr["bbox"])
                if sim > best_sim and sim >= self.similarity_threshold:
                    best_sim = sim
                    best_tid = tid
            if best_tid is not None:
                matched.add(best_tid)
                tr = self.tracks[best_tid]
                old = tr["bbox"]
                tr["bbox"] = [
                    old[0] * self.smooth_alpha + bbox[0] * (1 - self.smooth_alpha),
                    old[1] * self.smooth_alpha + bbox[1] * (1 - self.smooth_alpha),
                    old[2] * self.smooth_alpha + bbox[2] * (1 - self.smooth_alpha),
                    old[3] * self.smooth_alpha + bbox[3] * (1 - self.smooth_alpha),
                ]
                tr["class_name"] = det.get("class_name") or det.get("class")
                tr["confidence"] = det.get("confidence", 0.0)
                tr["age"] = 0
                tr["last_seen"] = frame_number
                out.append({**det, "track_id": best_tid, "bbox": tr["bbox"]})
            else:
                tid = self.next_id
                self.next_id += 1
                self.tracks[tid] = {
                    "bbox": bbox,
                    "class_name": det.get("class_name") or det.get("class"),
                    "confidence": det.get("confidence", 0.0),
                    "age": 0,
                    "last_seen": frame_number,
                }
                out.append({**det, "track_id": tid, "bbox": bbox})

        for tid, tr in self.tracks.items():
            if tid not in matched:
                tr["age"] += 1
        return out


def _iter_frames(media: Path, stride: int, max_frames: int) -> List[Tuple[int, Any]]:
    try:
        import cv2  # type: ignore
    except ImportError:
        return []

    cap = cv2.VideoCapture(str(media))
    if not cap.isOpened():
        return []
    out: List[Tuple[int, Any]] = []
    idx = 0
    while idx < max_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok or frame is None:
            break
        out.append((idx, frame))
        idx += stride
    cap.release()
    return out


def sample_motion_gate(
    media: Path,
    *,
    frame_skip: int = 4,
    preset: str = "sensitive",
    sample_sec: float = 22.0,
    fps: float = 25.0,
) -> MotionSampleResult:
    MotionGate, MotionGateConfig = _import_motion_gate()
    cfg = MotionGateConfig(enabled=True, preset=preset)
    gate = MotionGate(cfg)

    cap_frames = _iter_frames(media, stride=1, max_frames=int(sample_sec * fps) + 1)
    if not cap_frames:
        return MotionSampleResult(0, 0, 0, 0, [])

    frames_out: List[Dict[str, Any]] = []
    infer_submits = 0
    infer_skips = 0
    motion_triggers = 0
    baseline = 0
    max_frame = int(sample_sec * fps)

    for frame_index in range(0, max_frame, max(1, frame_skip)):
        pick = cap_frames[min(len(cap_frames) - 1, frame_index)]
        frame = pick[1]
        baseline += 1
        result = gate.on_sample_frame("oracle", frame, frame_index)
        submit = result.triggered or result.reason in ("warmup", "disabled")
        if submit:
            infer_submits += 1
        else:
            infer_skips += 1
        if result.triggered:
            motion_triggers += 1
        frames_out.append(
            {
                "frame_index": frame_index,
                "triggered": bool(result.triggered),
                "reason": result.reason,
                "score": round(float(result.score), 6),
                "changed_area_ratio": round(float(result.changed_area_ratio), 6),
                "infer_skipped": not submit,
            }
        )

    return MotionSampleResult(
        baseline_triggers=baseline,
        motion_triggers=motion_triggers,
        infer_submits=infer_submits,
        infer_skips_motion=infer_skips,
        frames=frames_out,
    )


def sample_tracking(
    media: Path,
    *,
    onnx_model: Path,
    frame_skip: int = 4,
    similarity_threshold: float = 0.2,
    sample_sec: float = 22.0,
    fps: float = 25.0,
) -> TrackSampleResult:
    from .record_oracle_smoke import _onnx_frame_detections

    tracker = OracleSimpleTracker(
        similarity_threshold=similarity_threshold,
        max_age=25,
        smooth_alpha=0.25,
    )

    cap_frames = _iter_frames(media, stride=1, max_frames=int(sample_sec * fps) + 1)
    frames_out: List[Dict[str, Any]] = []
    max_track_id = 0
    max_frame = int(sample_sec * fps)

    for frame_index in range(0, max_frame, max(1, frame_skip)):
        if not cap_frames:
            break
        pick = cap_frames[min(len(cap_frames) - 1, frame_index)]
        frame = pick[1]
        raw = _onnx_frame_detections(frame, onnx_model)
        detections = [
            {
                "bbox": d["bbox_xyxy"],
                "class_id": 0,
                "class_name": d["class"],
                "confidence": d["confidence"],
            }
            for d in raw
        ]
        tracked = tracker.update(detections, frame_index)
        frame_dets: List[Dict[str, Any]] = []
        for det in tracked:
            tid = int(det.get("track_id", 0))
            max_track_id = max(max_track_id, tid)
            bbox = det.get("bbox") or det.get("bbox_xyxy") or []
            frame_dets.append(
                {
                    "bbox_xyxy": [round(float(v), 2) for v in bbox],
                    "class": str(det.get("class_name", "person")),
                    "confidence": round(float(det.get("confidence", 0.0)), 4),
                    "track_id": tid,
                }
            )
        if frame_dets:
            frames_out.append({"frame_index": frame_index, "detections": frame_dets})

    return TrackSampleResult(frames=frames_out, track_switch_count=max_track_id)


def load_cpp_parity_sample(log_path: Path) -> Dict[str, Any]:
    sample_path = log_path / "parity_sample.json"
    if not sample_path.is_file():
        return {}
    return json.loads(sample_path.read_text(encoding="utf-8"))


def track_id_mapping_ratio(py_frames: List[Dict[str, Any]], cpp_frames: List[Dict[str, Any]]) -> float:
    if not py_frames or not cpp_frames:
        return 0.0
    matched = 0
    total = 0
    for py_frame, cpp_frame in zip(py_frames, cpp_frames):
        py_dets = py_frame.get("detections") or []
        cpp_dets = cpp_frame.get("detections") or []
        for py_det in py_dets:
            total += 1
            py_bbox = py_det.get("bbox_xyxy") or []
            py_tid = py_det.get("track_id")
            best_iou = 0.0
            best_tid = None
            for cpp_det in cpp_dets:
                cb = cpp_det.get("bbox_xyxy") or []
                if len(py_bbox) == 4 and len(cb) == 4:
                    iou = bbox_iou(py_bbox, cb)
                    if iou > best_iou:
                        best_iou = iou
                        best_tid = cpp_det.get("track_id")
            if best_iou >= 0.5 and best_tid is not None and py_tid == best_tid:
                matched += 1
    return matched / total if total else 0.0


def cpp_track_stability_ratio(cpp_frames: List[Dict[str, Any]]) -> float:
    stable = 0
    pairs = 0
    prev: Dict[int, List[float]] = {}
    for frame in cpp_frames:
        for det in frame.get("detections") or []:
            tid = int(det.get("track_id") or -1)
            bbox = det.get("bbox_xyxy") or []
            if tid < 0 or len(bbox) != 4:
                continue
            if tid in prev:
                pairs += 1
                if bbox_iou(prev[tid], bbox) >= 0.3:
                    stable += 1
            prev[tid] = bbox
    return stable / pairs if pairs else 1.0
