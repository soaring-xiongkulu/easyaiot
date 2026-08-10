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
    normalize_api_layer,
    write_layer,
)

# Reuse oracle-aligned helpers from record_python (same lifecycle contract as certify diff).
from record_python import (  # noqa: E402
    _ensure_task_stopped,
    _lifecycle_from_service,
    _parse_ini_keys,
    _resolve_ini_path,
    _task_detail,
    _task_service_status,
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
        "POST", f"{base}/video/algorithm/task/{task_id}/start"
    )
    time.sleep(2.0)
    during = _task_detail(base, task_id)
    during_data = during.get("data") or {}
    during_svc = _task_service_status(base, task_id)
    during_lc = _lifecycle_from_service(during_svc)
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
    payload = {
        "task_id": task_id,
        "server_ip": "127.0.0.1",
        "port": fixture.get("control_port", 8001),
        "process_id": 12345,
        "log_path": fixture.get("log_path", f"/tmp/task_{task_id}"),
    }
    _, body, _ = http_json("POST", f"{base}/video/algorithm/heartbeat/realtime", payload)
    after = _task_detail(base, task_id)
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
                "run_status": after.get("data", {}).get("run_status"),
                "service_server_ip": after.get("data", {}).get("service_server_ip"),
                "service_port": after.get("data", {}).get("service_port"),
                "heartbeat_ok": body.get("code") == 0,
            }
        },
    )


def _record_alert_hook(case: Dict[str, Any], fixture: Dict[str, Any]) -> None:
    base = case["candidate_base_url"].rstrip("/")
    out = golden_dir("java", case["case_id"])
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
                "device_id": payload.get("device_id"),
                "object": payload.get("object"),
                "event": payload.get("event"),
            }
        },
    )


def run_case(case_id: str) -> None:
    manifest = load_manifest()
    case = find_case(manifest, case_id)
    fixture = load_fixture() if case_id != "vj_p0_health" else {}
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
        ids = [c["case_id"] for c in manifest.get("cases", []) if c.get("priority") == "P0"]
    for cid in ids:
        run_case(cid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
