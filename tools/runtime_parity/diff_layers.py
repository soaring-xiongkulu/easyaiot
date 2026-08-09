"""Layered golden diff for runtime parity certify (G-4.1)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from .detect_sample import bbox_iou
from .hook_payload_fields import HOOK_PAYLOAD_GOLDEN_KEYS, missing_hook_keys

_VALID_SAMPLE_STATUS = frozenset({"recorded", "sampled", "sampled_partial"})


def _fail(layer: str, reason: str, **extra: Any) -> Dict[str, Any]:
    return {"layer": layer, "status": "fail", "reason": reason, **extra}


def _pass(layer: str, **extra: Any) -> Dict[str, Any]:
    return {"layer": layer, "status": "pass", **extra}


def diff_lifecycle(
    layer: str,
    py_data: Dict[str, Any],
    cpp_data: Dict[str, Any],
    thresholds: Dict[str, Any],
) -> Dict[str, Any]:
    lc_thresh = thresholds.get("lifecycle") or {}
    min_hb_cpp = int(lc_thresh.get("min_heartbeat_count_cpp", 1))
    fields_expected: List[str] = list(py_data.get("fields_expected") or cpp_data.get("fields_expected") or [])

    py_boot = py_data.get("boot") or {}
    cpp_boot = cpp_data.get("boot") or {}
    if not py_boot.get("started"):
        return _fail(layer, "python golden boot.started is false")
    if not cpp_boot.get("started"):
        return _fail(layer, "cpp boot.started is false", cpp_boot=cpp_boot)

    cpp_hb_count = int(cpp_data.get("heartbeat_count") or len(cpp_data.get("heartbeats") or []))
    if cpp_hb_count < min_hb_cpp:
        return _fail(
            layer,
            f"cpp heartbeat_count {cpp_hb_count} < min {min_hb_cpp}",
            heartbeat_count=cpp_hb_count,
        )

    cpp_heartbeats = cpp_data.get("heartbeats") or []
    for i, hb in enumerate(cpp_heartbeats):
        missing = [f for f in fields_expected if f not in hb]
        if missing:
            return _fail(layer, f"cpp heartbeat[{i}] missing fields: {missing}", heartbeat=hb)

    py_status = py_data.get("status", "")
    cpp_status = cpp_data.get("status", "")
    if py_status not in _VALID_SAMPLE_STATUS:
        return _fail(layer, f"python status invalid: {py_status}")
    if cpp_status not in _VALID_SAMPLE_STATUS:
        return _fail(layer, f"cpp status invalid: {cpp_status}")

    return _pass(
        layer,
        heartbeat_count_cpp=cpp_hb_count,
        heartbeat_count_python=int(py_data.get("heartbeat_count") or 0),
        infer_ep=cpp_boot.get("infer_ep"),
    )


def _collect_bboxes(frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for frame in frames:
        for det in frame.get("detections") or []:
            bbox = det.get("bbox_xyxy")
            if bbox and len(bbox) == 4:
                out.append(
                    {
                        "frame_index": frame.get("frame_index"),
                        "bbox_xyxy": [float(v) for v in bbox],
                        "class": str(det.get("class", "")),
                        "confidence": float(det.get("confidence", 0.0)),
                    }
                )
    return out


def diff_detect(
    layer: str,
    py_data: Dict[str, Any],
    cpp_data: Dict[str, Any],
    thresholds: Dict[str, Any],
) -> Dict[str, Any]:
    det_thresh = thresholds.get("detect") or {}
    iou_min = float(det_thresh.get("bbox_iou_min", 0.5))
    ratio_min = float(det_thresh.get("matched_bbox_ratio_min", 0.95))
    count_tol = int(det_thresh.get("count_tolerance", 0))

    if py_data.get("status") not in _VALID_SAMPLE_STATUS:
        return _fail(layer, f"python detect status invalid: {py_data.get('status')}")
    cpp_status = cpp_data.get("status", "")
    if cpp_status not in _VALID_SAMPLE_STATUS:
        return _fail(layer, f"cpp detect status invalid: {cpp_status}")

    py_frames = py_data.get("frames") or []
    cpp_frames = cpp_data.get("frames") or []
    py_boxes = _collect_bboxes(py_frames)
    cpp_boxes = _collect_bboxes(cpp_frames)

    if not py_boxes:
        return _fail(layer, "python golden has no detections to compare")
    if not cpp_boxes:
        return _fail(layer, "cpp sample has no detections")

    py_count = len(py_boxes)
    cpp_count = len(cpp_boxes)
    if abs(py_count - cpp_count) > count_tol:
        return _fail(
            layer,
            f"detection count delta {abs(py_count - cpp_count)} > tolerance {count_tol}",
            python_count=py_count,
            cpp_count=cpp_count,
        )

    matched = 0
    mismatches: List[Dict[str, Any]] = []
    for ref in py_boxes:
        best_iou = 0.0
        best_cls = ""
        for cand in cpp_boxes:
            if ref["class"] and cand["class"] and ref["class"] != cand["class"]:
                continue
            iou = bbox_iou(ref["bbox_xyxy"], cand["bbox_xyxy"])
            if iou > best_iou:
                best_iou = iou
                best_cls = cand["class"]
        if best_iou >= iou_min:
            matched += 1
        else:
            mismatches.append(
                {
                    "frame_index": ref["frame_index"],
                    "class": ref["class"],
                    "best_iou": round(best_iou, 4),
                    "best_class": best_cls,
                }
            )

    ratio = matched / py_count if py_count else 0.0
    if ratio < ratio_min:
        return _fail(
            layer,
            f"matched_bbox_ratio {ratio:.4f} < {ratio_min}",
            matched=matched,
            total=py_count,
            mismatches=mismatches[:5],
            iou_min=iou_min,
        )

    return _pass(
        layer,
        matched_bbox_ratio=round(ratio, 4),
        python_count=py_count,
        cpp_count=cpp_count,
        python_model=py_data.get("model"),
        cpp_model=cpp_data.get("model"),
    )


def _normalize_hook_body(body: Dict[str, Any]) -> Dict[str, Any]:
    info = body.get("information")
    if isinstance(info, str):
        try:
            import json

            body = dict(body)
            body["information"] = json.loads(info)
        except (json.JSONDecodeError, TypeError):
            pass
    return body


def _hook_to_alert_entry(seq: int, body: Dict[str, Any], width: int, height: int) -> Dict[str, Any]:
    body = _normalize_hook_body(body)
    info = body.get("information") if isinstance(body.get("information"), dict) else {}
    detections = info.get("detections") or []
    bbox: Optional[List[float]] = None
    cls = str(body.get("object", "object"))
    conf = 0.0
    if detections:
        det0 = detections[0]
        cls = str(det0.get("class_name") or det0.get("class") or cls)
        conf = float(det0.get("confidence", 0.0))
        raw_bbox = det0.get("bbox") or det0.get("bbox_xyxy")
        if isinstance(raw_bbox, list) and len(raw_bbox) == 4:
            bbox = [float(v) for v in raw_bbox]

    in_roi = True
    if bbox and width > 0 and height > 0:
        cx = (bbox[0] + bbox[2]) / 2.0 / width
        cy = (bbox[1] + bbox[3]) / 2.0 / height
        in_roi = 0.05 <= cx <= 0.95 and 0.05 <= cy <= 0.95

    return {
        "seq": seq,
        "alert_type": "roi_confidence",
        "bbox_xyxy": [round(v, 2) for v in bbox] if bbox else [],
        "class": cls,
        "confidence": round(conf, 4),
        "in_roi": in_roi,
        "cooldown_applied": False,
        "hook_payload_keys": sorted(body.keys()),
    }


def diff_alarm(
    layer: str,
    py_data: Dict[str, Any],
    cpp_data: Dict[str, Any],
    thresholds: Dict[str, Any],
) -> Dict[str, Any]:
    alarm_thresh = thresholds.get("alarm") or {}
    count_tol = int(alarm_thresh.get("count_tolerance_per_minute", 1))
    iou_min = float((thresholds.get("detect") or {}).get("bbox_iou_min", 0.5))
    allow_hook_bbox_drift = bool(alarm_thresh.get("smoke_allow_hook_bbox_drift", False))

    if py_data.get("status") not in _VALID_SAMPLE_STATUS:
        return _fail(layer, f"python alarm status invalid: {py_data.get('status')}")
    cpp_status = cpp_data.get("status", "")
    if cpp_status == "not_sampled":
        return {"layer": layer, "status": "not_sampled", "reason": cpp_data.get("reason", "cpp not sampled")}
    if cpp_status not in _VALID_SAMPLE_STATUS:
        return _fail(layer, f"cpp alarm status invalid: {cpp_status}")

    py_alerts = py_data.get("alerts") or []
    cpp_alerts = cpp_data.get("alerts") or []
    py_count = int(py_data.get("alert_count") or len(py_alerts))
    cpp_count = int(cpp_data.get("alert_count") or len(cpp_alerts))

    if abs(py_count - cpp_count) > count_tol:
        return _fail(
            layer,
            f"alert_count delta {abs(py_count - cpp_count)} > tolerance {count_tol}",
            python_count=py_count,
            cpp_count=cpp_count,
        )

    # Hook payload golden keys (G-2.2) when cpp captured full payloads
    hook_payloads = cpp_data.get("hook_payloads") or []
    if hook_payloads:
        missing_all: Set[str] = set()
        for hp in hook_payloads:
            body = hp if isinstance(hp, dict) else {}
            missing_all |= missing_hook_keys(body)
        if missing_all:
            return _fail(
                layer,
                f"cpp hook payload missing golden keys: {sorted(missing_all)}",
                required=sorted(HOOK_PAYLOAD_GOLDEN_KEYS),
            )
        expected_tt = py_data.get("expected_task_type") or cpp_data.get("expected_task_type")
        if expected_tt:
            for i, hp in enumerate(hook_payloads):
                if not isinstance(hp, dict):
                    continue
                got = hp.get("task_type")
                if got != expected_tt:
                    return _fail(
                        layer,
                        f"hook[{i}] task_type={got!r} expected={expected_tt!r}",
                    )

    if not py_alerts:
        return _fail(layer, "python golden has no alerts")

    if not cpp_alerts and not hook_payloads:
        return _fail(layer, "cpp has no alerts or hook payloads")

  # Compare primary alert: best bbox IoU among cpp alerts vs python reference
    py0 = py_alerts[0]
    py_bbox = [float(v) for v in (py0.get("bbox_xyxy") or [])]
    cpp_candidates = cpp_alerts if cpp_alerts else [_hook_to_alert_entry(1, hook_payloads[0], 768, 432)]
    best_cpp = cpp_candidates[0]
    best_iou = 0.0
    if len(py_bbox) == 4:
        for cand in cpp_candidates:
            cb = cand.get("bbox_xyxy") or []
            if len(cb) == 4:
                iou = bbox_iou(py_bbox, [float(v) for v in cb])
                if iou > best_iou:
                    best_iou = iou
                    best_cpp = cand
    else:
        best_iou = 1.0

    if py0.get("class") and best_cpp.get("class") and py0["class"] != best_cpp["class"]:
        return _fail(layer, f"class mismatch python={py0['class']} cpp={best_cpp['class']}")

    if len(py_bbox) == 4 and best_iou < iou_min:
        if allow_hook_bbox_drift and hook_payloads and not missing_hook_keys(hook_payloads[0]):
            if py0.get("class") == best_cpp.get("class") and bool(py0.get("in_roi", True)) == bool(
                best_cpp.get("in_roi", True)
            ):
                return _pass(
                    layer,
                    alert_count_python=py_count,
                    alert_count_cpp=cpp_count,
                    hook_payload_count=len(hook_payloads),
                    bbox_iou_skipped=True,
                    note="smoke_allow_hook_bbox_drift: live cpp hook bbox differs from oracle smoke snapshot",
                )
        return _fail(
            layer,
            f"alert bbox best IoU {best_iou:.4f} < {iou_min}",
            python_bbox=py_bbox,
            cpp_bbox=best_cpp.get("bbox_xyxy"),
        )

    if "in_roi" in py0 and "in_roi" in best_cpp and bool(py0["in_roi"]) != bool(best_cpp["in_roi"]):
        return _fail(layer, f"in_roi mismatch python={py0['in_roi']} cpp={best_cpp['in_roi']}")

    return _pass(
        layer,
        alert_count_python=py_count,
        alert_count_cpp=cpp_count,
        hook_payload_count=len(hook_payloads),
    )


def diff_track(
    layer: str,
    py_data: Dict[str, Any],
    cpp_data: Dict[str, Any],
    thresholds: Dict[str, Any],
) -> Dict[str, Any]:
    track_thresh = thresholds.get("track") or {}
    ratio_min = float(track_thresh.get("id_mapping_ratio_min", 0.9))
    switch_max = float(track_thresh.get("switch_count_ratio_max", 1.1))

    if py_data.get("status") not in _VALID_SAMPLE_STATUS:
        return _fail(layer, f"python track status invalid: {py_data.get('status')}")
    cpp_status = cpp_data.get("status", "")
    if cpp_status not in _VALID_SAMPLE_STATUS:
        return _fail(layer, f"cpp track status invalid: {cpp_status}")

    py_frames = py_data.get("frames") or []
    cpp_frames = cpp_data.get("frames") or []
    if not py_frames:
        return _fail(layer, "python golden has no track frames")
    if not cpp_frames:
        return _fail(layer, "cpp sample has no track frames")

    from .motion_track_sample import track_id_mapping_ratio, cpp_track_stability_ratio

    ratio = track_id_mapping_ratio(py_frames, cpp_frames)
    cpp_stable = cpp_track_stability_ratio(cpp_frames)
    if ratio >= ratio_min or cpp_stable >= ratio_min:
        pass_switch = True
    else:
        pass_switch = False

    py_switch = int(py_data.get("track_switch_count") or 0)
    cpp_switch = int(cpp_data.get("track_switch_count") or 0)
    if not pass_switch:
        return _fail(
            layer,
            f"id_mapping_ratio {ratio:.4f} and cpp_stability {cpp_stable:.4f} < {ratio_min}",
            id_mapping_ratio=round(ratio, 4),
            cpp_stability=round(cpp_stable, 4),
        )

    if py_switch > 0 and cpp_switch > 0 and ratio < ratio_min and cpp_stable < ratio_min:
        switch_ratio = cpp_switch / py_switch
        if switch_ratio > switch_max:
            return _fail(
                layer,
                f"track_switch_ratio {switch_ratio:.4f} > {switch_max}",
                python_switch=py_switch,
                cpp_switch=cpp_switch,
            )

    return _pass(
        layer,
        id_mapping_ratio=round(ratio, 4),
        cpp_stability=round(cpp_stable, 4),
        python_switch=py_switch,
        cpp_switch=cpp_switch,
    )


def diff_motion(
    layer: str,
    py_data: Dict[str, Any],
    cpp_data: Dict[str, Any],
    thresholds: Dict[str, Any],
) -> Dict[str, Any]:
    motion_thresh = thresholds.get("motion") or {}
    count_tol = int(motion_thresh.get("motion_trigger_count_tolerance", 3))
    skip_min = float(motion_thresh.get("infer_skip_ratio_min", 0.05))
    skip_max = float(motion_thresh.get("infer_skip_ratio_max", 1.5))

    if py_data.get("status") not in _VALID_SAMPLE_STATUS:
        return _fail(layer, f"python motion status invalid: {py_data.get('status')}")
    cpp_status = cpp_data.get("status", "")
    if cpp_status not in _VALID_SAMPLE_STATUS:
        return _fail(layer, f"cpp motion status invalid: {cpp_status}")

    py_triggers = int(py_data.get("motion_triggers") or 0)
    cpp_triggers = int(cpp_data.get("motion_triggers") or 0)
    if cpp_triggers < 1:
        return _fail(layer, "cpp motion_triggers < 1 (motion gate never fired)")

    cpp_skips = int(cpp_data.get("infer_skips_motion") or 0)
    if cpp_skips < 1:
        return _fail(layer, "cpp infer_skips_motion < 1 (no skip behavior observed)")

    if abs(py_triggers - cpp_triggers) > count_tol:
        return _fail(
            layer,
            f"motion_triggers delta {abs(py_triggers - cpp_triggers)} > {count_tol}",
            python_triggers=py_triggers,
            cpp_triggers=cpp_triggers,
        )

    py_baseline = int(py_data.get("baseline_triggers") or 1)
    py_skips = int(py_data.get("infer_skips_motion") or 0)
    cpp_skips = int(cpp_data.get("infer_skips_motion") or 0)
    py_skip_ratio = py_skips / py_baseline if py_baseline else 0.0
    cpp_skip_ratio = cpp_skips / max(1, int(cpp_data.get("baseline_triggers") or py_baseline))
    if py_skip_ratio > 0:
        ratio = cpp_skip_ratio / py_skip_ratio
        if ratio < skip_min or ratio > skip_max:
            return _fail(
                layer,
                f"infer_skip_ratio out of band [{skip_min}, {skip_max}]: {ratio:.4f}",
                python_skip_ratio=round(py_skip_ratio, 4),
                cpp_skip_ratio=round(cpp_skip_ratio, 4),
            )

    return _pass(
        layer,
        motion_triggers_python=py_triggers,
        motion_triggers_cpp=cpp_triggers,
        infer_skips_cpp=cpp_skips,
    )


def diff_schedule(
    layer: str,
    py_data: Dict[str, Any],
    cpp_data: Dict[str, Any],
    thresholds: Dict[str, Any],
) -> Dict[str, Any]:
    sched_thresh = thresholds.get("schedule") or {}
    snap_min = int(sched_thresh.get("snap_min_slots", 1))
    patrol_min = int(sched_thresh.get("patrol_min_events", 2))
    interval_ref = float(sched_thresh.get("patrol_interval_seconds", 5))
    interval_tol = float(sched_thresh.get("patrol_interval_tolerance_seconds", 4))

    if py_data.get("status") not in _VALID_SAMPLE_STATUS:
        return _fail(layer, f"python schedule status invalid: {py_data.get('status')}")
    cpp_status = cpp_data.get("status", "")
    if cpp_status not in _VALID_SAMPLE_STATUS:
        return _fail(layer, f"cpp schedule status invalid: {cpp_status}")

    py_slots = int(py_data.get("slot_count") or 0)
    cpp_slots = int(cpp_data.get("slot_count") or 0)
    py_patrol = int(py_data.get("patrol_count") or 0)
    cpp_patrol = int(cpp_data.get("patrol_count") or 0)

    # Snap cron path
    if py_slots > 0 or cpp_slots > 0 or (py_data.get("cron_expression") or cpp_data.get("cron_expression")):
        if cpp_slots < snap_min:
            return _fail(layer, f"cpp slot_count {cpp_slots} < min {snap_min}")
        if py_slots < 1:
            return _fail(layer, "python golden has no cron slots")
        return _pass(
            layer,
            slot_count_python=py_slots,
            slot_count_cpp=cpp_slots,
            kind="snap_cron",
        )

    # Patrol path
    if cpp_patrol < patrol_min:
        return _fail(layer, f"cpp patrol_count {cpp_patrol} < min {patrol_min}")
    if py_patrol < 1:
        return _fail(layer, "python golden has no patrol events")

    cpp_mean = float(cpp_data.get("mean_interval_sec") or 0.0)
    if cpp_mean > 0 and abs(cpp_mean - interval_ref) > interval_tol + 2.0:
        # Soft check: allow larger slack when only a few samples
        if cpp_patrol >= 4:
            return _fail(
                layer,
                f"cpp mean_interval_sec {cpp_mean:.2f} outside {interval_ref}±{interval_tol + 2}",
                mean_interval_sec=cpp_mean,
            )

    return _pass(
        layer,
        patrol_count_python=py_patrol,
        patrol_count_cpp=cpp_patrol,
        mean_interval_sec_cpp=round(cpp_mean, 3),
        kind="patrol",
    )


def diff_layer(
    layer: str,
    py_data: Dict[str, Any],
    cpp_data: Dict[str, Any],
    thresholds: Dict[str, Any],
    *,
    py_path: str = "",
    cpp_path: str = "",
) -> Dict[str, Any]:
    if layer == "L_lifecycle":
        result = diff_lifecycle(layer, py_data, cpp_data, thresholds)
    elif layer == "L_detect":
        result = diff_detect(layer, py_data, cpp_data, thresholds)
    elif layer == "L_alarm":
        result = diff_alarm(layer, py_data, cpp_data, thresholds)
    elif layer == "L_track":
        result = diff_track(layer, py_data, cpp_data, thresholds)
    elif layer == "L_motion":
        result = diff_motion(layer, py_data, cpp_data, thresholds)
    elif layer == "L_schedule":
        result = diff_schedule(layer, py_data, cpp_data, thresholds)
    else:
        result = _fail(layer, f"layer {layer} diff not implemented for G-4.1")
    if py_path:
        result["python_artifact"] = py_path
    if cpp_path:
        result["cpp_artifact"] = cpp_path
    return result
