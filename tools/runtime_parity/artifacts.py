"""Golden artifact skeleton writers (MVP placeholders)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .manifest import CaseSpec


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def layer_file_map(case: CaseSpec) -> Dict[str, str]:
    """Map layer id to artifact filename."""
    mapping = {
        "L_lifecycle": "lifecycle.json",
        "L_detect": "detect.json",
        "L_track": "track.json",
        "L_overlay": "overlay.json",
        "L_stream": "stream.json",
        "L_schedule": "schedule.json",
        "L_motion": "motion.json",
        "L_alarm": "alarm.json",
        "L_kafka": "kafka.json",
        "L_face": "face_match.json",
        "L_plate": "plate_match.json",
        "L_post": "post_process.json",
        "L_perf": "perf.json",
        "L_e2e_alarm": "e2e_alarm.json",
    }
    return {layer: mapping[layer] for layer in case.required_layers if layer in mapping}


def skeleton_for_layer(layer: str, case: CaseSpec, executor: str) -> Dict[str, Any]:
    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    base = {
        "case_id": case.id,
        "layer": layer,
        "executor": executor,
        "task_type": case.task_type,
        "sampled_at": ts,
        "source": "runtime_parity_gate_mvp",
    }

    if layer == "L_lifecycle":
        return {
            **base,
            "status": "placeholder",
            "boot": {"exit_code": None, "started": False},
            "heartbeats": [],
            "heartbeat_count": 0,
            "fields_expected": ["task_id", "process_id", "log_path"],
            "_note": "Replace via record-python against oracle VIDEO/RUNTIME",
        }
    if layer == "L_detect":
        return {
            **base,
            "status": "placeholder",
            "frames": [],
            "detection_count": 0,
            "model": "onnx",
            "_note": "bbox list per frame; IoU diff in certify",
        }
    if layer == "L_alarm":
        return {
            **base,
            "status": "placeholder",
            "alerts": [],
            "alert_count": 0,
            "hook_url": f"http://127.0.0.1:{case.mock_hook_port or 18080}/alert",
            "_note": "Compare with golden/video/<case>/ hook captures",
        }
    if layer == "L_track":
        return {
            **base,
            "status": "placeholder",
            "frames": [],
            "track_switch_count": 0,
            "_note": "Per-frame detections with track_id; id mapping ratio in certify",
        }
    if layer == "L_motion":
        return {
            **base,
            "status": "placeholder",
            "baseline_triggers": 0,
            "motion_triggers": 0,
            "infer_submits": 0,
            "infer_skips_motion": 0,
            "frames": [],
            "_note": "Motion gate stats from RUNTIME parity_sample.json",
        }
    if layer == "L_schedule":
        return {
            **base,
            "status": "placeholder",
            "slot_count": 0,
            "patrol_count": 0,
            "events": [],
            "mean_interval_sec": 0.0,
            "device_intervals": {},
            "_note": "Snap cron slots / patrol intervals from parity_sample.json schedule",
        }
    if layer == "L_overlay":
        return {
            **base,
            "status": "placeholder",
            "sample_count": 0,
            "drawn_count": 0,
            "p50_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "frames": [],
            "_note": "Overlay draw latency P95 from RUNTIME parity_sample.json",
        }
    if layer == "L_stream":
        return {
            **base,
            "status": "placeholder",
            "width": 0,
            "height": 0,
            "fps": 0.0,
            "bitrate_kbps": 0.0,
            "pushed_ok": 0,
            "gray_frame_count": 0,
            "ffprobe": {},
            "_note": "RTMP stream profile via encoder meta + ffprobe",
        }
    if layer == "L_kafka":
        return {
            **base,
            "status": "placeholder",
            "topic": "",
            "events": [],
            "publish_count": 0,
            "suppress_count": 0,
        }
    if layer == "L_face":
        return {
            **base,
            "status": "placeholder",
            "publish_count": 0,
            "process_count": 0,
            "hit_count": 0,
        }
    if layer == "L_plate":
        return {
            **base,
            "status": "placeholder",
            "publish_count": 0,
            "process_count": 0,
            "hit_count": 0,
        }
    if layer == "L_post":
        return {
            **base,
            "status": "placeholder",
            "enqueue_count": 0,
        }
    if layer == "L_perf":
        return {
            **base,
            "status": "placeholder",
            "alert_latency_p50_ms": 0.0,
            "alert_latency_p95_ms": 0.0,
            "fps": 0.0,
            "cpu_percent": 0.0,
            "rss_mb": 0.0,
        }
    if layer == "L_e2e_alarm":
        return {
            **base,
            "status": "placeholder",
            "alerts": [],
            "alert_count": 0,
            "e2e": True,
        }
    return {**base, "status": "placeholder", "_note": f"Layer {layer} MVP skeleton"}


def write_skeleton_golden(
    out_dir: Path,
    case: CaseSpec,
    executor: str,
    *,
    runtime_found: Optional[bool] = None,
) -> List[str]:
    """Write required layer JSON files; return relative paths written."""
    written: List[str] = []
    for layer, fname in layer_file_map(case).items():
        data = skeleton_for_layer(layer, case, executor)
        if executor == "cpp" and runtime_found is False:
            data["status"] = "not_sampled"
            data["reason"] = "RUNTIME binary not found"
        path = out_dir / fname
        _write_json(path, data)
        written.append(str(path))
    meta = {
        "case_id": case.id,
        "executor": executor,
        "required_layers": case.required_layers,
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "artifacts": list(layer_file_map(case).values()),
    }
    _write_json(out_dir / "meta.json", meta)
    written.append(str(out_dir / "meta.json"))
    return written
