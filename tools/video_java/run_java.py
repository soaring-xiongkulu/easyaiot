#!/usr/bin/env python3
"""Sample Java candidate golden artifacts (mirror record_python)."""

from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

from vj_common import (
    LAYER_FILES,
    find_case,
    golden_dir,
    http_json,
    load_fixture,
    load_manifest,
    load_p1_fixture,
    load_p2_fixture,
    normalize_api_layer,
    ensure_p0_alert_fixture,
    update_task_runtime_bin,
    runtime_executor_fields,
    write_layer,
)

# Reuse oracle-aligned helpers from record_python (same lifecycle contract as certify diff).
from record_python import (  # noqa: E402
    _ensure_task_stopped,
    _lifecycle_from_service,
    _parse_ini_keys,
    _record_camera_get,
    _record_camera_list,
    _record_detection_region_get,
    _record_media_hook,
    _record_patrol_task_list,
    _record_playback_url,
    _record_record_query,
    _record_face_publish_process,
    _record_plate_publish_process,
    _record_post_process_enqueue,
    _record_snap_list_or_create,
    _record_stream_forward_start_stop,
    _record_view_forward_start_stop,
    _resolve_ini_path,
    _task_detail,
    _task_service_status,
    _wait_until_runtime_running,
)


def _record_health(case: Dict[str, Any]) -> None:
    base = case["candidate_base_url"].rstrip("/")
    status, body, raw = http_json("GET", f"{base}/actuator/health")
    out = golden_dir("java", case["case_id"])
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": "/actuator/health",
            "http_status": status,
            "body": body,
            "normalized": normalize_api_layer(body),
            "raw": raw[:500],
        },
    )


def _record_task_start_stop(case: Dict[str, Any], fixture: Dict[str, Any]) -> None:
    base = case["candidate_base_url"].rstrip("/")
    task_id = int(fixture["task_id"])
    out = golden_dir("java", case["case_id"])
    _ensure_task_stopped(base, task_id)
    before_svc = _task_service_status(base, task_id)
    before_lc = _lifecycle_from_service(before_svc)
    _, start_body, start_status = http_json(
        "POST", f"{base}/video/algorithm/task/{task_id}/start", timeout=90.0
    )
    during_svc = _wait_until_runtime_running(base, task_id)
    during = _task_detail(base, task_id)
    during_data = during.get("data") or {}
    during_lc = _lifecycle_from_service(during_svc)
    executor_fields = runtime_executor_fields(during_data, during_svc)
    ini_hint = fixture.get("java_ini_path_hint") or fixture.get("ini_path_hint")
    fixture_ini = dict(fixture)
    if ini_hint:
        fixture_ini["ini_path_hint"] = ini_hint
    ini_path = _resolve_ini_path(fixture_ini, during_data, task_id)
    ini_keys = _parse_ini_keys(ini_path) if ini_path and ini_path.is_file() else {}
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": f"/video/algorithm/task/{task_id}/start",
            "http_status": start_status,
            "body": start_body,
            "normalized": normalize_api_layer(start_body),
        },
    )
    write_layer(
        out / LAYER_FILES["lifecycle"],
        "lifecycle",
        {
            "snapshot": {
                "before_run_status": before_lc["run_status"],
                "after_run_status": during_lc["run_status"],
                "is_enabled": during_data.get("is_enabled"),
                "process_alive": during_lc["process_alive"],
                "executor": during_data.get("executor"),
                **executor_fields,
            }
        },
    )
    write_layer(
        out / LAYER_FILES["ini"],
        "ini",
        {"ini_path": str(ini_path) if ini_path else None, "keys": ini_keys},
    )
    http_json("POST", f"{base}/video/algorithm/task/{task_id}/stop")
    time.sleep(1.0)


def _record_heartbeat(case: Dict[str, Any], fixture: Dict[str, Any]) -> None:
    base = case["candidate_base_url"].rstrip("/")
    task_id = int(fixture["task_id"])
    out = golden_dir("java", case["case_id"])
    _ensure_task_stopped(base, task_id)
    control_port = int(fixture.get("control_port", 8001 + task_id % 1000))
    log_path = fixture.get("log_path") or str(Path.home() / ".video-java" / "logs" / f"task_{task_id}")
    payload = {
        "task_id": task_id,
        "server_ip": "127.0.0.1",
        "port": control_port,
        "process_id": 12345,
        "log_path": log_path,
    }
    _, body, _ = http_json("POST", f"{base}/video/algorithm/heartbeat/realtime", payload)
    after = _task_detail(base, task_id)
    after_data = after.get("data") or {}
    after_svc = _task_service_status(base, task_id)
    after_lc = _lifecycle_from_service(after_svc)
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {"endpoint": "/video/algorithm/heartbeat/realtime", "body": body, "normalized": normalize_api_layer(body)},
    )
    write_layer(
        out / LAYER_FILES["lifecycle"],
        "lifecycle",
        {
            "snapshot": {
                "run_status": after_lc["run_status"],
                "service_server_ip": after_data.get("service_server_ip"),
                "service_port": after_data.get("service_port"),
                "heartbeat_ok": body.get("code") == 0,
            }
        },
    )


def _record_alert_hook(case: Dict[str, Any], fixture: Dict[str, Any]) -> None:
    base = case["candidate_base_url"].rstrip("/")
    out = golden_dir("java", case["case_id"])
    task_id = int(fixture["task_id"])
    device_id = str(fixture["device_id"])
    ensure_p0_alert_fixture(task_id, device_id)
    payload = dict(fixture.get("alert_hook_payload", {}))
    payload["correlation_id"] = f"vj_p0_java_{uuid.uuid4().hex[:12]}"
    _, body, _ = http_json("POST", f"{base}/video/alert/hook", payload)
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {"endpoint": "/video/alert/hook", "body": body, "normalized": normalize_api_layer(body)},
    )
    write_layer(
        out / LAYER_FILES["alarm"],
        "alarm",
        {
            "snapshot": {
                "hook_status": data.get("status") or body.get("msg"),
                "mode": data.get("mode"),
                "alert_id_present": bool(data.get("alert_id")),
                "device_id": payload.get("device_id"),
                "object": payload.get("object"),
                "event": payload.get("event"),
            }
        },
    )


def _record_restart(case: Dict[str, Any], fixture: Dict[str, Any]) -> None:
    base = case["candidate_base_url"].rstrip("/")
    task_id = int(fixture["task_id"])
    out = golden_dir("java", case["case_id"])
    crash_bin = fixture.get("crash_runtime_bin_path") or str(
        Path(__file__).resolve().parent / "stub_runtime_exit.bat"
    )
    normal_bin = fixture.get("runtime_bin_path")
    _ensure_task_stopped(base, task_id)
    update_task_runtime_bin(task_id, crash_bin)
    try:
        http_json("POST", f"{base}/video/algorithm/task/{task_id}/start", timeout=90.0)
        time.sleep(3.0)
        time.sleep(8.0)
        after_svc = _task_service_status(base, task_id)
        after_lc = _lifecycle_from_service(after_svc)
        write_layer(
            out / LAYER_FILES["lifecycle"],
            "lifecycle",
            {
                "snapshot": {
                    "process_alive_after_restart": after_lc["process_alive"],
                    "unexpected_exit_recovered": after_lc["process_alive"],
                }
            },
        )
    finally:
        http_json("POST", f"{base}/video/algorithm/task/{task_id}/stop")
        time.sleep(1.0)
        if normal_bin:
            update_task_runtime_bin(task_id, normal_bin)


def _write_java_fail(case_id: str, layer: str, reason: str) -> None:
    out = golden_dir("java", case_id)
    fname = LAYER_FILES.get(layer, f"{layer}.json")
    path = out / fname
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {"layer": layer, "status": "fail", "reason": reason}
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_p1_with_failover(case: Dict[str, Any], fixture: Dict[str, Any], recorder) -> None:
    """Run P1 recorder against candidate; write honest fail golden if endpoint missing."""
    cid = case["case_id"]
    base = case["candidate_base_url"].rstrip("/")
    probe = {
        "vj_p1_camera_list": "/video/camera/list?pageNo=1&pageSize=1",
        "vj_p1_camera_get": f"/video/camera/device/{fixture['device_id']}",
        "vj_p1_view_forward_start_stop": f"/video/camera/device/{fixture['device_id']}/stream/status",
        "vj_p1_stream_forward_start_stop": f"/video/stream-forward/task/{fixture['stream_forward_task_id']}/status",
    }.get(cid, "/video/camera/list?pageNo=1&pageSize=1")
    status, _, _ = http_json("GET", f"{base}{probe}")
    if status == 404:
        layers = case.get("layers", ["api"])
        for layer in layers:
            _write_java_fail(cid, layer, f"candidate endpoint missing (HTTP {status} on {probe})")
        if "api" not in layers:
            _write_java_fail(cid, "api", f"candidate endpoint missing (HTTP {status})")
        return
    recorder(case, fixture, side="java")


def _run_p2_with_failover(case: Dict[str, Any], fixture: Dict[str, Any], recorder) -> None:
    """Run P2 recorder against candidate; write honest fail golden if endpoint missing."""
    cid = case["case_id"]
    base = case["candidate_base_url"].rstrip("/")
    probe = {
        "vj_p2_snap_list_or_create": "/video/snap/space/list?pageNo=1&pageSize=1",
        "vj_p2_record_query": "/video/record/space/list?pageNo=1&pageSize=1",
        "vj_p2_playback_url": "/video/playback/list?pageNo=1&pageSize=1",
        "vj_p2_patrol_task_list": "/video/algorithm/task/list?pageNo=1&pageSize=1&task_type=patrol",
        "vj_p2_media_hook": "/video/media/hook/snap/completed",
        "vj_p2_detection_region_get": f"/video/device-detection/device/{fixture['device_id']}/regions",
        "vj_p2_face_publish_process": "/video/face/matching/publish",
        "vj_p2_plate_publish_process": "/video/plate/matching/publish",
        "vj_p2_post_process_enqueue": "/video/alert/hook",
    }.get(cid, "/video/snap/space/list?pageNo=1&pageSize=1")
    if cid == "vj_p2_media_hook":
        status, _, _ = http_json("POST", f"{base}{probe}", fixture.get("media_hook_payload") or {})
    elif cid == "vj_p2_face_publish_process":
        status, _, _ = http_json(
            "POST",
            f"{base}{probe}",
            {"taskId": fixture["face_task_id"], "faceImagePath": fixture["face_image_path"]},
            timeout=5.0,
        )
    elif cid == "vj_p2_plate_publish_process":
        status, _, _ = http_json(
            "POST",
            f"{base}{probe}",
            {"taskId": fixture["plate_task_id"], "plateNo": fixture["plate_no"]},
            timeout=5.0,
        )
    elif cid == "vj_p2_post_process_enqueue":
        payload = dict(fixture.get("alert_hook_payload") or {})
        payload["task_id"] = fixture["post_process_task_id"]
        status, _, _ = http_json("POST", f"{base}{probe}", payload, timeout=5.0)
    else:
        status, _, _ = http_json("GET", f"{base}{probe}")
    if status == 404:
        layers = case.get("layers", ["api"])
        for layer in layers:
            _write_java_fail(cid, layer, f"candidate endpoint missing (HTTP {status} on {probe})")
        if "api" not in layers:
            _write_java_fail(cid, "api", f"candidate endpoint missing (HTTP {status})")
        return
    recorder(case, fixture, side="java")


def _run_p2_honest_fail(case: Dict[str, Any]) -> None:
    """P2 scaffold: endpoints not implemented yet — write honest fail goldens."""
    cid = case["case_id"]
    layers = case.get("layers", ["api"])
    reason = "candidate Phase 2 endpoints not implemented"
    for layer in layers:
        _write_java_fail(cid, layer, reason)


def run_case(case_id: str) -> None:
    manifest = load_manifest()
    case = find_case(manifest, case_id)
    if case_id.startswith("vj_p1_"):
        fixture = load_p1_fixture()
    elif case_id.startswith("vj_p2_"):
        fixture = load_p2_fixture()
    elif case_id != "vj_p0_health":
        fixture = load_fixture()
    else:
        fixture = {}
    cid = case["case_id"]
    print(f"run_java: {cid}")
    if cid == "vj_p0_health":
        _record_health(case)
    elif cid == "vj_p0_task_start_stop":
        _record_task_start_stop(case, fixture)
    elif cid == "vj_p0_heartbeat":
        _record_heartbeat(case, fixture)
    elif cid == "vj_p0_alert_hook":
        _record_alert_hook(case, fixture)
    elif cid == "vj_p0_restart":
        _record_restart(case, fixture)
    elif cid == "vj_p1_camera_list":
        _run_p1_with_failover(case, fixture, _record_camera_list)
    elif cid == "vj_p1_camera_get":
        _run_p1_with_failover(case, fixture, _record_camera_get)
    elif cid == "vj_p1_view_forward_start_stop":
        _run_p1_with_failover(case, fixture, _record_view_forward_start_stop)
    elif cid == "vj_p1_stream_forward_start_stop":
        _run_p1_with_failover(case, fixture, _record_stream_forward_start_stop)
    elif cid == "vj_p2_face_publish_process":
        _run_p2_with_failover(case, fixture, _record_face_publish_process)
    elif cid == "vj_p2_plate_publish_process":
        _run_p2_with_failover(case, fixture, _record_plate_publish_process)
    elif cid == "vj_p2_post_process_enqueue":
        _run_p2_with_failover(case, fixture, _record_post_process_enqueue)
    elif cid == "vj_p2_snap_list_or_create":
        _run_p2_with_failover(case, fixture, _record_snap_list_or_create)
    elif cid == "vj_p2_record_query":
        _run_p2_with_failover(case, fixture, _record_record_query)
    elif cid == "vj_p2_playback_url":
        _run_p2_with_failover(case, fixture, _record_playback_url)
    elif cid == "vj_p2_patrol_task_list":
        _run_p2_with_failover(case, fixture, _record_patrol_task_list)
    elif cid == "vj_p2_media_hook":
        _run_p2_with_failover(case, fixture, _record_media_hook)
    elif cid == "vj_p2_detection_region_get":
        _run_p2_with_failover(case, fixture, _record_detection_region_get)
    else:
        raise ValueError(f"unsupported case {cid}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sample Java VIDEO candidate golden")
    parser.add_argument("case_id", nargs="?", help="single case id; default all P0")
    args = parser.parse_args()
    manifest = load_manifest()
    ids: List[str]
    if args.case_id:
        ids = [args.case_id]
    else:
        ids = [c["case_id"] for c in manifest.get("cases", []) if c.get("priority") in ("P0", "P1", "P2")]
    for cid in ids:
        run_case(cid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
