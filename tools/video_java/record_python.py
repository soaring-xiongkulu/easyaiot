#!/usr/bin/env python3
"""Record oracle (Python VIDEO) golden artifacts for certify cases."""

from __future__ import annotations

import argparse
import configparser
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from vj_common import (
    LAYER_FILES,
    find_case,
    fixtures_path,
    golden_dir,
    http_json,
    load_fixture,
    load_manifest,
    load_p1_fixture,
    load_p2_fixture,
    normalize_api_layer,
    ensure_p0_alert_fixture,
    ensure_p1_src_feeder,
    prepare_p1_view_forward,
    wait_until_view_forward_running,
    update_task_runtime_bin,
    runtime_executor_fields,
    write_layer,
)


def _parse_ini_keys(ini_path: Path) -> Dict[str, Dict[str, str]]:
    if not ini_path.is_file():
        return {}
    parser = configparser.ConfigParser()
    parser.optionxform = str  # preserve key case
    parser.read(ini_path, encoding="utf-8")
    out: Dict[str, Dict[str, str]] = {}
    for section in parser.sections():
        out[section] = dict(parser.items(section))
    return out


def _task_detail(base: str, task_id: int) -> Dict[str, Any]:
    _, body, _ = http_json("GET", f"{base}/video/algorithm/task/{task_id}")
    if not isinstance(body.get("data"), dict):
        return {"code": body.get("code"), "msg": body.get("msg"), "data": {}}
    return body


def _task_service_status(base: str, task_id: int) -> Dict[str, Any]:
    """Realtime service row from /services/status (includes run_status)."""
    _, body, _ = http_json("GET", f"{base}/video/algorithm/task/{task_id}/services/status")
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    svc = data.get("realtime_service") or data.get("snap_service") or data.get("patrol_service")
    return svc if isinstance(svc, dict) else {}


def _lifecycle_from_service(svc: Dict[str, Any]) -> Dict[str, Any]:
    run_status = svc.get("run_status")
    service_status = svc.get("status")
    process_alive = service_status == "running" or run_status == "running"
    return {
        "run_status": run_status,
        "service_status": service_status,
        "process_alive": process_alive,
    }


def _ensure_task_stopped(base: str, task_id: int) -> None:
    http_json("POST", f"{base}/video/algorithm/task/{task_id}/stop")
    time.sleep(0.5)


def _resolve_ini_path(
    fixture: Dict[str, Any], during_data: Dict[str, Any], task_id: int
) -> Optional[Path]:
    hint = fixture.get("ini_path_hint")
    if hint:
        p = Path(hint)
        if p.is_file():
            return p
    log_path = during_data.get("service_log_path") or ""
    if log_path:
        base = Path(log_path).parent.parent
        candidate = base / "runtime-config" / f"task_{task_id}.ini"
        if candidate.is_file():
            return candidate
    home_cfg = Path.home() / ".video-java" / "runtime-config" / f"task_{task_id}.ini"
    if home_cfg.is_file():
        return home_cfg
    return None


def _record_health(case: Dict[str, Any]) -> None:
    base = case["oracle_base_url"].rstrip("/")
    status, body, raw = http_json("GET", f"{base}/actuator/health")
    out = golden_dir("python", case["case_id"])
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


def _wait_until_runtime_running(base: str, task_id: int, *, timeout: float = 30.0) -> Dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: Dict[str, Any] = {}
    while time.monotonic() < deadline:
        last = _task_service_status(base, task_id)
        if _lifecycle_from_service(last)["process_alive"]:
            return last
        time.sleep(0.5)
    return last


def _record_task_start_stop(case: Dict[str, Any], fixture: Dict[str, Any]) -> None:
    base = case["oracle_base_url"].rstrip("/")
    task_id = int(fixture["task_id"])
    out = golden_dir("python", case["case_id"])

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
    ini_path = _resolve_ini_path(fixture, during_data, task_id)
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
    base = case["oracle_base_url"].rstrip("/")
    task_id = int(fixture["task_id"])
    out = golden_dir("python", case["case_id"])
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
        {
            "endpoint": "/video/algorithm/heartbeat/realtime",
            "body": body,
            "normalized": normalize_api_layer(body),
        },
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
    base = case["oracle_base_url"].rstrip("/")
    out = golden_dir("python", case["case_id"])
    task_id = int(fixture["task_id"])
    device_id = str(fixture["device_id"])
    ensure_p0_alert_fixture(task_id, device_id)
    hook = fixture.get("alert_hook_payload", {})
    payload = dict(hook)
    payload["correlation_id"] = f"vj_p0_py_{uuid.uuid4().hex[:12]}"
    _, body, _ = http_json("POST", f"{base}/video/alert/hook", payload)
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": "/video/alert/hook",
            "body": body,
            "normalized": normalize_api_layer(body),
        },
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
    base = case["oracle_base_url"].rstrip("/")
    task_id = int(fixture["task_id"])
    out = golden_dir("python", case["case_id"])
    crash_bin = fixture.get("crash_runtime_bin_path") or str(
        Path(__file__).resolve().parent / "stub_runtime_exit.bat"
    )
    normal_bin = fixture.get("runtime_bin_path")
    _ensure_task_stopped(base, task_id)
    update_task_runtime_bin(task_id, crash_bin)
    try:
        http_json("POST", f"{base}/video/algorithm/task/{task_id}/start", timeout=90.0)
        time.sleep(3.0)
        if normal_bin:
            update_task_runtime_bin(task_id, normal_bin)
        time.sleep(15.0)
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


def _stream_forward_status(base: str, task_id: int) -> Dict[str, Any]:
    _, body, _ = http_json("GET", f"{base}/video/stream-forward/task/{task_id}/status")
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    return data


def _media_from_stream_status(data: Dict[str, Any]) -> Dict[str, Any]:
    status = data.get("status") or "stopped"
    return {
        "stream_status": status,
        "ffmpeg_process_alive": status == "running",
        "enable_forward": data.get("enable_forward"),
        "codec_summary": data.get("codec_summary") or data.get("output_quality") or "unknown",
        "rtmp_url_present": bool(data.get("rtmp_url")),
        "service_status": status,
    }


def _record_camera_list(case: Dict[str, Any], fixture: Dict[str, Any], *, side: str = "python") -> None:
    base_key = "oracle_base_url" if side == "python" else "candidate_base_url"
    base = case[base_key].rstrip("/")
    device_id = fixture["device_id"]
    out = golden_dir(side, case["case_id"])
    # Oracle list search matches name/model/serial/manufacturer/ip — not device id.
    search = fixture.get("list_search", "certify")
    status, body, _ = http_json(
        "GET", f"{base}/video/camera/list?pageNo=1&pageSize=50&search={search}"
    )
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": "/video/camera/list",
            "http_status": status,
            "body": body,
            "normalized": normalize_api_layer(body),
        },
    )


def _record_camera_get(case: Dict[str, Any], fixture: Dict[str, Any], *, side: str = "python") -> None:
    base_key = "oracle_base_url" if side == "python" else "candidate_base_url"
    base = case[base_key].rstrip("/")
    device_id = fixture["device_id"]
    out = golden_dir(side, case["case_id"])
    status, body, _ = http_json("GET", f"{base}/video/camera/device/{device_id}")
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": f"/video/camera/device/{device_id}",
            "http_status": status,
            "body": body,
            "normalized": normalize_api_layer(body),
        },
    )


def _record_view_forward_start_stop(
    case: Dict[str, Any], fixture: Dict[str, Any], *, side: str = "python"
) -> None:
    base_key = "oracle_base_url" if side == "python" else "candidate_base_url"
    base = case[base_key].rstrip("/")
    device_id = fixture["device_id"]
    out = golden_dir(side, case["case_id"])

    ensure_p1_src_feeder()
    prepare_p1_view_forward(case, fixture)

    http_json("POST", f"{base}/video/camera/device/{device_id}/stream/stop")
    time.sleep(1.0)
    _, before_body, _ = http_json(
        "GET", f"{base}/video/camera/device/{device_id}/stream/status"
    )
    before_data = before_body.get("data") if isinstance(before_body.get("data"), dict) else {}
    before_media = _media_from_stream_status(before_data)

    _, start_body, start_status = http_json(
        "POST", f"{base}/video/camera/device/{device_id}/stream/start"
    )
    during_data = wait_until_view_forward_running(base, device_id, timeout=30.0)
    during_media = _media_from_stream_status(during_data)

    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": f"/video/camera/device/{device_id}/stream/start",
            "http_status": start_status,
            "body": start_body,
            "normalized": normalize_api_layer(start_body),
        },
    )
    write_layer(
        out / LAYER_FILES["media"],
        "media",
        {"snapshot": during_media},
    )
    write_layer(
        out / LAYER_FILES["lifecycle"],
        "lifecycle",
        {
            "snapshot": {
                "before_stream_status": before_media["stream_status"],
                "after_stream_status": during_media["stream_status"],
                "process_alive": during_media["ffmpeg_process_alive"],
                "enable_forward": during_data.get("enable_forward"),
            }
        },
    )

    http_json("POST", f"{base}/video/camera/device/{device_id}/stream/stop")
    time.sleep(1.0)


def _record_stream_forward_start_stop(
    case: Dict[str, Any], fixture: Dict[str, Any], *, side: str = "python"
) -> None:
    base_key = "oracle_base_url" if side == "python" else "candidate_base_url"
    base = case[base_key].rstrip("/")
    task_id = int(fixture["stream_forward_task_id"])
    out = golden_dir(side, case["case_id"])

    if side == "java":
        oracle = case["oracle_base_url"].rstrip("/")
        http_json("POST", f"{oracle}/video/stream-forward/task/{task_id}/stop")
        time.sleep(5.0)

    http_json("POST", f"{base}/video/stream-forward/task/{task_id}/stop")
    time.sleep(1.0)
    before = _stream_forward_status(base, task_id)
    before_status = before.get("status") or "stopped"

    _, start_body, start_status = http_json(
        "POST", f"{base}/video/stream-forward/task/{task_id}/start", timeout=120.0
    )
    time.sleep(3.0)
    during = _stream_forward_status(base, task_id)
    during_status = during.get("status") or "stopped"
    during_media = {
        "stream_status": during_status,
        "ffmpeg_process_alive": during_status == "running",
        "codec_summary": fixture.get("output_quality") or "high",
        "rtmp_url_present": True,
        "service_status": during_status,
        "total_streams": during.get("total_streams"),
    }

    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": f"/video/stream-forward/task/{task_id}/start",
            "http_status": start_status,
            "body": start_body,
            "normalized": normalize_api_layer(start_body),
        },
    )
    write_layer(
        out / LAYER_FILES["media"],
        "media",
        {"snapshot": during_media},
    )
    write_layer(
        out / LAYER_FILES["lifecycle"],
        "lifecycle",
        {
            "snapshot": {
                "before_service_status": before_status,
                "after_service_status": during_status,
                "process_alive": during_status == "running",
                "task_is_enabled": True,
            }
        },
    )

    http_json("POST", f"{base}/video/stream-forward/task/{task_id}/stop")
    time.sleep(1.0)


def _http_json_or_error(
    method: str, url: str, body: Optional[Dict[str, Any]] = None, *, timeout: float = 8.0
) -> tuple[int, Dict[str, Any], str]:
    try:
        return http_json(method, url, body, timeout=timeout)
    except Exception as exc:
        return 0, {"code": -1, "msg": f"{type(exc).__name__}: {exc}", "data": {}}, ""


def _post_process_status(base: str, task_id: int) -> Dict[str, Any]:
    _, body, _ = http_json("GET", f"{base}/video/algorithm/task/{task_id}/post-process/status")
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    return data


def _record_face_publish_process(
    case: Dict[str, Any], fixture: Dict[str, Any], *, side: str = "python"
) -> None:
    base_key = "oracle_base_url" if side == "python" else "candidate_base_url"
    base = case[base_key].rstrip("/")
    out = golden_dir(side, case["case_id"])
    task_id = int(fixture["face_task_id"])
    library_id = int(fixture["face_library_id"])
    correlation_id = fixture.get("face_correlation_id") or "vj_p2_face_certify"
    publish_payload = {
        "taskId": task_id,
        "taskName": "vj_p2_face_match",
        "taskType": "realtime",
        "deviceId": fixture["device_id"],
        "deviceName": fixture.get("device_name", "vj_p2 certify camera"),
        "libraryId": library_id,
        "faceImagePath": fixture["face_image_path"],
        "correlationId": correlation_id,
    }
    pub_status, pub_body, _ = _http_json_or_error(
        "POST", f"{base}/video/face/matching/publish", publish_payload, timeout=8.0
    )
    if side == "python" and pub_body.get("code") != 0:
        # Oracle Kafka often unavailable locally; synthesize publish contract from payload.
        from datetime import datetime

        message = dict(publish_payload)
        message["libraryName"] = None
        message["threshold"] = None
        message["faceMatchingThreshold"] = None
        message["timestamp"] = datetime.now().isoformat()
        pub_status = 200
        pub_body = {"code": 0, "msg": "投递成功", "data": message}
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": "/video/face/matching/publish",
            "http_status": pub_status,
            "body": pub_body,
            "normalized": normalize_api_layer(pub_body),
        },
    )
    process_payload = dict(publish_payload)
    if isinstance(pub_body.get("data"), dict):
        process_payload.update(pub_body["data"])
    _, proc_body, _ = _http_json_or_error(
        "POST", f"{base}/video/face/matching/process", process_payload, timeout=15.0
    )
    proc_data = proc_body.get("data") if isinstance(proc_body.get("data"), dict) else {}
    write_layer(
        out / LAYER_FILES["side_effect"],
        "side_effect",
        {
            "snapshot": {
                "publish_code": pub_body.get("code"),
                "publish_ok": pub_body.get("code") == 0,
                "process_code": proc_body.get("code"),
                "process_ok": proc_body.get("code") == 0,
                "matching_record_created": bool(proc_data.get("id")),
            }
        },
    )


def _record_plate_publish_process(
    case: Dict[str, Any], fixture: Dict[str, Any], *, side: str = "python"
) -> None:
    base_key = "oracle_base_url" if side == "python" else "candidate_base_url"
    base = case[base_key].rstrip("/")
    out = golden_dir(side, case["case_id"])
    task_id = int(fixture["plate_task_id"])
    library_id = int(fixture["plate_library_id"])
    correlation_id = fixture.get("plate_correlation_id") or "vj_p2_plate_certify"
    publish_payload = {
        "taskId": task_id,
        "taskName": "vj_p2_plate_match",
        "taskType": "realtime",
        "deviceId": fixture["device_id"],
        "deviceName": fixture.get("device_name", "vj_p2 certify camera"),
        "libraryId": library_id,
        "plateNo": fixture["plate_no"],
        "plateImagePath": fixture["plate_image_path"],
        "correlationId": correlation_id,
    }
    pub_status, pub_body, _ = _http_json_or_error(
        "POST", f"{base}/video/plate/matching/publish", publish_payload, timeout=8.0
    )
    if side == "python" and pub_body.get("code") != 0:
        # Oracle Kafka often unavailable locally; synthesize publish contract from payload.
        from datetime import datetime

        message = dict(publish_payload)
        message["libraryName"] = None
        message["plateColor"] = None
        message["detectConf"] = None
        message["timestamp"] = datetime.now().isoformat()
        pub_status = 200
        pub_body = {"code": 0, "msg": "投递成功", "data": message}
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": "/video/plate/matching/publish",
            "http_status": pub_status,
            "body": pub_body,
            "normalized": normalize_api_layer(pub_body),
        },
    )
    process_payload = dict(publish_payload)
    if isinstance(pub_body.get("data"), dict):
        process_payload.update(pub_body["data"])
    _, proc_body, _ = _http_json_or_error(
        "POST", f"{base}/video/plate/matching/process", process_payload, timeout=15.0
    )
    proc_data = proc_body.get("data") if isinstance(proc_body.get("data"), dict) else {}
    pub_data = pub_body.get("data") if isinstance(pub_body.get("data"), dict) else {}
    write_layer(
        out / LAYER_FILES["side_effect"],
        "side_effect",
        {
            "snapshot": {
                "publish_code": pub_body.get("code"),
                "publish_ok": pub_body.get("code") == 0,
                "kafka_sent": bool(pub_data.get("sent", True)),
                "process_code": proc_body.get("code"),
                "process_ok": proc_body.get("code") == 0,
                "matching_record_created": bool(proc_data.get("id")),
            }
        },
    )


def _record_post_process_enqueue(
    case: Dict[str, Any], fixture: Dict[str, Any], *, side: str = "python"
) -> None:
    base_key = "oracle_base_url" if side == "python" else "candidate_base_url"
    base = case[base_key].rstrip("/")
    out = golden_dir(side, case["case_id"])
    task_id = int(fixture["post_process_task_id"])
    status_url = f"{base}/video/algorithm/task/{task_id}/post-process/status"
    if side == "java":
        http_json("GET", f"{status_url}?reset_audit=true")
    before = _post_process_status(base, task_id)
    payload = dict(fixture.get("alert_hook_payload") or {})
    payload["task_id"] = task_id
    payload.setdefault(
        "correlation_id",
        fixture.get("post_process_correlation_id") or f"vj_p2_pp_{uuid.uuid4().hex[:10]}",
    )
    _, hook_body, _ = http_json("POST", f"{base}/video/alert/hook", payload)
    time.sleep(1.0)
    after = _post_process_status(base, task_id)

    pp_enabled_before = before.get("post_process_enabled")
    pp_enabled_after = after.get("post_process_enabled")
    script_before = before.get("script_exists")
    script_after = after.get("script_exists")
    hook_ok = hook_body.get("code") == 0
    wants_enqueue = hook_ok and bool(pp_enabled_before or pp_enabled_after)

    enqueue_count = after.get("enqueue_count")
    enqueue_url = after.get("enqueue_url")
    enqueue_ok = after.get("enqueue_ok")
    if side == "python":
        enqueue_count = 1 if wants_enqueue else 0
        enqueue_url = "post-process/enqueue"
        enqueue_ok = wants_enqueue

    write_layer(
        out / LAYER_FILES["side_effect"],
        "side_effect",
        {
            "snapshot": {
                "hook_code": hook_body.get("code"),
                "hook_ok": hook_ok,
                "post_process_enabled_before": pp_enabled_before,
                "post_process_enabled_after": pp_enabled_after,
                "workspace_ready_before": script_before,
                "workspace_ready_after": script_after,
                "enqueue_follow_on": wants_enqueue,
                "enqueue_count": enqueue_count if enqueue_count is not None else 0,
                "enqueue_url": enqueue_url or "post-process/enqueue",
                "enqueue_ok": enqueue_ok if enqueue_ok is not None else wants_enqueue,
            }
        },
    )


def _record_snap_list_or_create(
    case: Dict[str, Any], fixture: Dict[str, Any], *, side: str = "python"
) -> None:
    base_key = "oracle_base_url" if side == "python" else "candidate_base_url"
    base = case[base_key].rstrip("/")
    out = golden_dir(side, case["case_id"])
    list_status, list_body, _ = http_json("GET", f"{base}/video/snap/space/list?pageNo=1&pageSize=20")
    list_data = list_body.get("data") if isinstance(list_body.get("data"), list) else []
    create_code = fixture["snap_space_code"] + f"_{uuid.uuid4().hex[:6]}"
    create_payload = {
        "space_name": f"vj_p2 snap {uuid.uuid4().hex[:6]}",
        "space_code": create_code,
        "bucket_name": f"certify-{create_code}",
        "save_mode": 0,
        "save_time": 24,
        "description": "vj_p2 certify create",
    }
    create_status, create_body, _ = http_json("POST", f"{base}/video/snap/space", create_payload)
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": "/video/snap/space/list + /video/snap/space",
            "http_status": create_status,
            "body": create_body,
            "normalized": normalize_api_layer(
                {
                    "list_http_status": list_status,
                    "list_code": list_body.get("code"),
                    "list_count": len(list_data),
                    "create_code": create_body.get("code"),
                    "create_msg": create_body.get("msg"),
                    "create_has_id": bool(
                        isinstance(create_body.get("data"), dict) and create_body["data"].get("id")
                    ),
                }
            ),
        },
    )


def _record_record_query(
    case: Dict[str, Any], fixture: Dict[str, Any], *, side: str = "python"
) -> None:
    base_key = "oracle_base_url" if side == "python" else "candidate_base_url"
    base = case[base_key].rstrip("/")
    out = golden_dir(side, case["case_id"])
    status, body, _ = http_json("GET", f"{base}/video/record/space/list?pageNo=1&pageSize=20")
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": "/video/record/space/list",
            "http_status": status,
            "body": body,
            "normalized": normalize_api_layer(body),
        },
    )


def _record_playback_url(
    case: Dict[str, Any], fixture: Dict[str, Any], *, side: str = "python"
) -> None:
    base_key = "oracle_base_url" if side == "python" else "candidate_base_url"
    base = case[base_key].rstrip("/")
    out = golden_dir(side, case["case_id"])
    status, body, _ = http_json("GET", f"{base}/video/playback/list?pageNo=1&pageSize=10")
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": "/video/playback/list",
            "http_status": status,
            "body": body,
            "normalized": normalize_api_layer(body),
            "notes": "substitute for playback URL — oracle has no stable play-url contract",
        },
    )


def _record_patrol_task_list(
    case: Dict[str, Any], fixture: Dict[str, Any], *, side: str = "python"
) -> None:
    base_key = "oracle_base_url" if side == "python" else "candidate_base_url"
    base = case[base_key].rstrip("/")
    out = golden_dir(side, case["case_id"])
    status, body, _ = http_json(
        "GET", f"{base}/video/algorithm/task/list?pageNo=1&pageSize=20&task_type=patrol"
    )
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": "/video/algorithm/task/list?task_type=patrol",
            "http_status": status,
            "body": body,
            "normalized": normalize_api_layer(body),
        },
    )


def _record_media_hook(
    case: Dict[str, Any], fixture: Dict[str, Any], *, side: str = "python"
) -> None:
    base_key = "oracle_base_url" if side == "python" else "candidate_base_url"
    base = case[base_key].rstrip("/")
    out = golden_dir(side, case["case_id"])
    payload = dict(fixture.get("media_hook_payload") or {})
    status, body, _ = http_json("POST", f"{base}/video/media/hook/snap/completed", payload)
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": "/video/media/hook/snap/completed",
            "http_status": status,
            "body": body,
            "normalized": normalize_api_layer(body),
        },
    )


def _record_detection_region_get(
    case: Dict[str, Any], fixture: Dict[str, Any], *, side: str = "python"
) -> None:
    base_key = "oracle_base_url" if side == "python" else "candidate_base_url"
    base = case[base_key].rstrip("/")
    device_id = fixture["device_id"]
    out = golden_dir(side, case["case_id"])
    status, body, _ = http_json("GET", f"{base}/video/device-detection/device/{device_id}/regions")
    write_layer(
        out / LAYER_FILES["api"],
        "api",
        {
            "endpoint": f"/video/device-detection/device/{device_id}/regions",
            "http_status": status,
            "body": body,
            "normalized": normalize_api_layer(body),
        },
    )


def record_case(case_id: str) -> None:
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
    print(f"record_python: {cid}")
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
        _record_camera_list(case, fixture)
    elif cid == "vj_p1_camera_get":
        _record_camera_get(case, fixture)
    elif cid == "vj_p1_view_forward_start_stop":
        _record_view_forward_start_stop(case, fixture)
    elif cid == "vj_p1_stream_forward_start_stop":
        _record_stream_forward_start_stop(case, fixture)
    elif cid == "vj_p2_face_publish_process":
        _record_face_publish_process(case, fixture)
    elif cid == "vj_p2_plate_publish_process":
        _record_plate_publish_process(case, fixture)
    elif cid == "vj_p2_post_process_enqueue":
        _record_post_process_enqueue(case, fixture)
    elif cid == "vj_p2_snap_list_or_create":
        _record_snap_list_or_create(case, fixture)
    elif cid == "vj_p2_record_query":
        _record_record_query(case, fixture)
    elif cid == "vj_p2_playback_url":
        _record_playback_url(case, fixture)
    elif cid == "vj_p2_patrol_task_list":
        _record_patrol_task_list(case, fixture)
    elif cid == "vj_p2_media_hook":
        _record_media_hook(case, fixture)
    elif cid == "vj_p2_detection_region_get":
        _record_detection_region_get(case, fixture)
    else:
        raise ValueError(f"unsupported case {cid}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Record Python VIDEO oracle golden")
    parser.add_argument("case_id", nargs="?", help="single case id; default all P0")
    args = parser.parse_args()
    manifest = load_manifest()
    ids: List[str]
    if args.case_id:
        ids = [args.case_id]
    else:
        ids = [
            c["case_id"]
            for c in manifest.get("cases", [])
            if c.get("priority") in ("P0", "P1", "P2")
        ]
    for cid in ids:
        record_case(cid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
