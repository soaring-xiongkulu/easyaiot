#!/usr/bin/env python3
"""P0/P1 field-level JSON contract sampling (Python-first).

Reads Python oracle response / to_dict shapes, hits live Java :48096, asserts
envelope {code,msg,data} plus documented data / list-item keys.

Usage:
  python tools/video_java/field_contract.py
  python tools/video_java/field_contract.py --base-url http://127.0.0.1:48096
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from route_inventory import repo_root

DISCLAIMER = (
    "Field-level P0/P1 sampling is NOT the full ~259-route field matrix and "
    "does NOT mean COMPLETE. Green asserts verify documented Python keys on "
    "representative GETs only — see docs/video-java/FULL_REPLACEMENT_GAP.md."
)

# Python-first: keys derived from oracle blueprint + service to_dict (cited in report).
ALERT_ITEM_KEYS: Set[str] = {
    "id",
    "object",
    "event",
    "region",
    "device_id",
    "device_name",
    "image_path",
    "record_path",
    "task_id",
    "task_name",
    "edge_node_id",
    "edge_node_name",
    "edge_node_host",
    "node_id",
    "information",
    "task_type",
    "time",
    "notify_users",
    "channels",
    "notification_sent",
    "notification_sent_time",
    "image_url",
    "business_tags",
    "correlation_id",
}

ALGORITHM_TASK_KEYS: Set[str] = {
    "id",
    "task_name",
    "task_code",
    "task_type",
    "device_ids",
    "device_names",
    "model_ids",
    "model_names",
    "detect_conf",
    "extract_interval",
    "rtmp_input_url",
    "rtmp_output_url",
    "tracking_enabled",
    "tracking_similarity_threshold",
    "tracking_max_age",
    "tracking_smooth_alpha",
    "alert_event_enabled",
    "alert_event_suppress_time",
    "alert_class_names",
    "face_detection_enabled",
    "plate_detection_enabled",
    "face_matching_enabled",
    "face_library_ids",
    "face_library_names",
    "face_matching_threshold",
    "plate_matching_enabled",
    "plate_library_ids",
    "plate_library_names",
    "matching_business_tags",
    "alert_notification_enabled",
    "alert_notification_config",
    "alarm_suppress_time",
    "last_notify_time",
    "space_id",
    "space_name",
    "cron_expression",
    "frame_skip",
    "patrol_mode",
    "patrol_interval_sec",
    "patrol_pool_size",
    "focus_device_id",
    "status",
    "is_enabled",
    "exception_reason",
    "total_frames",
    "total_detections",
    "total_captures",
    "last_process_time",
    "last_success_time",
    "last_capture_time",
    "defense_mode",
    "defense_schedule",
    "schedule_policy",
    "prefer_gpu",
    "target_node_id",
    "node_id",
    "executor",
    "runtime_bin_path",
    "runtime_control_port",
    "service_server_ip",
    "service_port",
    "service_process_id",
    "service_last_heartbeat",
    "service_log_path",
    "algorithm_services",
    "sam_supplement_enabled",
    "sam_supplement_config",
    "motion_gate_enabled",
    "motion_gate_config",
    "pose_analysis_enabled",
    "pose_analysis_config",
    "pose_intent_enabled",
    "pose_library_ids",
    "pose_library_names",
    "pose_intent_threshold",
    "pose_intent_config",
    "post_process_enabled",
    "post_process_script",
    "post_process_replicas",
    "created_at",
    "updated_at",
}

CAMERA_DEVICE_KEYS: Set[str] = {
    "id",
    "name",
    "source",
    "rtmp_stream",
    "http_stream",
    "ai_rtmp_stream",
    "ai_http_stream",
    "enable_forward",
    "stream",
    "ip",
    "port",
    "username",
    "mac",
    "manufacturer",
    "model",
    "firmware_version",
    "serial_number",
    "hardware_id",
    "support_move",
    "support_zoom",
    "directory_id",
    "rtsp_direct",
    "channel_online",
    "connection_status",
    "online",
}

SNAP_SPACE_ITEM_KEYS: Set[str] = {
    "id",
    "space_name",
    "space_code",
    "bucket_name",
    "save_mode",
    "save_time",
    "save_time_custom",
    "description",
    "device_id",
    "task_count",
    "created_at",
    "updated_at",
}

RECORD_SPACE_ITEM_KEYS: Set[str] = {
    "id",
    "space_name",
    "space_code",
    "bucket_name",
    "save_mode",
    "save_time",
    "save_time_custom",
    "description",
    "device_id",
    "created_at",
    "updated_at",
}

STREAM_FORWARD_TASK_KEYS: Set[str] = {
    "id",
    "task_name",
    "task_code",
    "device_ids",
    "device_names",
    "output_format",
    "output_quality",
    "output_bitrate",
    "status",
    "is_enabled",
    "exception_reason",
    "service_server_ip",
    "service_port",
    "service_process_id",
    "service_last_heartbeat",
    "service_log_path",
    "schedule_policy",
    "prefer_gpu",
    "target_node_id",
    "node_id",
    "device_deployments",
    "total_streams",
    "last_process_time",
    "last_success_time",
    "description",
    "created_at",
    "updated_at",
}

FACE_HEALTH_KEYS: Set[str] = {
    "milvus_uri",
    "collection_name",
    "collection_exists",
    "recognition_model_loaded",
    "recognition_model_downloading",
}

PLATE_HEALTH_KEYS: Set[str] = {
    "exists",
    "detect_model",
    "rec_model",
    "detect_path",
    "rec_path",
    "downloading",
    "stage",
    "progress",
    "error",
}

PLAYBACK_ITEM_KEYS: Set[str] = {
    "id",
    "file_path",
    "video_url",
    "event_time",
    "device_id",
    "device_name",
    "duration",
    "thumbnail_path",
    "file_size",
    "created_at",
    "updated_at",
}

PATROL_DIRECTORY_DEVICES_KEYS: Set[str] = {
    "directory_id",
    "directory_name",
    "device_ids",
    "total",
}

SAMPLE_CASES: List[Dict[str, Any]] = [
    {
        "id": "alert_count",
        "path": "/video/alert/count",
        "python_source": "VIDEO/_retired_python_video/app/services/alert_service.py get_alert_count",
        "data_keys": {"count_list", "total_count"},
    },
    {
        "id": "alert_page",
        "path": "/video/alert/page?pageNo=1&pageSize=1",
        "python_source": "VIDEO/_retired_python_video/app/services/alert_service.py get_alert_list",
        "data_keys": {"alert_list", "total"},
        "list_path": ("data", "alert_list"),
        "list_item_keys": ALERT_ITEM_KEYS,
    },
    {
        "id": "algorithm_task_list",
        "path": "/video/algorithm/task/list?pageNo=1&pageSize=1",
        "python_source": "VIDEO/_retired_python_video/models.py AlgorithmTask.to_dict + algorithm_task.py list_tasks",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": ALGORITHM_TASK_KEYS,
    },
    {
        "id": "camera_list",
        "path": "/video/camera/list?pageNo=1&pageSize=1",
        "python_source": "VIDEO/_retired_python_video/app/services/camera_service.py _to_dict",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": CAMERA_DEVICE_KEYS,
    },
    {
        "id": "camera_get",
        "path": "/video/camera/device/vj_p2_device",
        "python_source": "VIDEO/_retired_python_video/app/services/camera_service.py _to_dict",
        "data_keys": CAMERA_DEVICE_KEYS,
    },
    {
        "id": "snap_space_list",
        "path": "/video/snap/space/list?pageNo=1&pageSize=1",
        "python_source": "VIDEO/_retired_python_video/models.py SnapSpace.to_dict",
        "data_list": True,
        "top_keys": {"total", "parent_key", "breadcrumbs", "is_search", "scope"},
        "list_item_keys": SNAP_SPACE_ITEM_KEYS,
    },
    {
        "id": "record_space_list",
        "path": "/video/record/space/list?pageNo=1&pageSize=1",
        "python_source": "VIDEO/_retired_python_video/models.py RecordSpace.to_dict",
        "data_list": True,
        "top_keys": {"total", "parent_key", "breadcrumbs", "is_search", "scope"},
        "list_item_keys": RECORD_SPACE_ITEM_KEYS,
    },
    {
        "id": "stream_forward_task_list",
        "path": "/video/stream-forward/task/list?pageNo=1&pageSize=1",
        "python_source": "VIDEO/_retired_python_video/models.py StreamForwardTask.to_dict",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": STREAM_FORWARD_TASK_KEYS,
    },
    {
        "id": "patrol_directory_devices",
        "path": "/video/patrol/directory/1/devices",
        "python_source": "VIDEO/_retired_python_video/app/blueprints/patrol.py directory_patrol_devices (no GET /session/list in oracle)",
        "data_keys": PATROL_DIRECTORY_DEVICES_KEYS,
        "note": "Oracle has no GET /video/patrol/session/list; sampled directory devices instead.",
    },
    {
        "id": "face_health",
        "path": "/video/face/health",
        "python_source": "VIDEO/_retired_python_video/app/blueprints/face.py face_health + face_vector_store.ping",
        "data_keys": FACE_HEALTH_KEYS,
    },
    {
        "id": "plate_health",
        "path": "/video/plate/health",
        "python_source": "VIDEO/_retired_python_video/app/utils/plate_model_download.py get_plate_model_status",
        "data_keys": PLATE_HEALTH_KEYS,
    },
    {
        "id": "playback_list",
        "path": "/video/playback/list?pageNo=1&pageSize=1",
        "python_source": "VIDEO/_retired_python_video/models.py Playback.to_dict + playback.py list_playbacks",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": PLAYBACK_ITEM_KEYS,
    },
]

ENVELOPE_KEYS: Set[str] = {"code", "msg", "data"}


def http_get_json(base_url: str, path: str, timeout: float = 8.0) -> Tuple[int, Dict[str, Any], str]:
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8", errors="replace")
    try:
        body = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        body = {"_raw": raw}
    if not isinstance(body, dict):
        body = {"data": body}
    return status, body, raw


def missing_keys(actual: Any, expected: Set[str]) -> List[str]:
    if not isinstance(actual, dict):
        return sorted(expected)
    return sorted(k for k in expected if k not in actual)


def assert_case(base_url: str, case: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    http_status, body, _ = http_get_json(base_url, case["path"], timeout=timeout)
    result: Dict[str, Any] = {
        "id": case["id"],
        "path": case["path"],
        "python_source": case["python_source"],
        "http_status": http_status,
        "asserts": 0,
        "pass": 0,
        "fail": 0,
        "skip": 0,
        "checks": [],
        "note": case.get("note"),
    }

    def record(name: str, ok: bool, detail: str, *, skipped: bool = False) -> None:
        result["asserts"] += 1
        if skipped:
            result["skip"] += 1
            status = "skip"
        elif ok:
            result["pass"] += 1
            status = "pass"
        else:
            result["fail"] += 1
            status = "fail"
        result["checks"].append({"check": name, "status": status, "detail": detail})

    if http_status >= 500:
        record("http_status", False, f"HTTP {http_status}")
        return result
    record("http_status", http_status < 500, f"HTTP {http_status}")

    miss_env = missing_keys(body, ENVELOPE_KEYS)
    record("envelope", not miss_env, f"missing {miss_env}" if miss_env else "code,msg,data present")

    code = body.get("code")
    record("business_code", code == 0, f"code={code!r}")

    for key in sorted(case.get("top_keys") or ()):
        present = key in body
        record(f"top.{key}", present, f"{'present' if present else 'missing'}")

    data = body.get("data")
    if case.get("data_keys"):
        miss = missing_keys(data, case["data_keys"])
        record("data_keys", not miss, f"missing {miss}" if miss else f"{len(case['data_keys'])} keys ok")

    if case.get("data_list"):
        record("data_is_list", isinstance(data, list), f"type={type(data).__name__}")
        items: List[Any] = data if isinstance(data, list) else []
        item_keys = case.get("list_item_keys") or set()
        if items and item_keys:
            miss = missing_keys(items[0], item_keys)
            record(
                "list_item_keys",
                not miss,
                f"missing {miss}" if miss else f"{len(item_keys)} keys on first item",
            )
        elif item_keys:
            record("list_item_keys", True, "empty list — item keys deferred", skipped=True)

    list_path = case.get("list_path")
    item_keys = case.get("list_item_keys")
    if list_path and item_keys:
        node: Any = body
        for part in list_path:
            node = node.get(part) if isinstance(node, dict) else None
        items = node if isinstance(node, list) else []
        if items:
            miss = missing_keys(items[0], item_keys)
            record(
                "nested_list_item_keys",
                not miss,
                f"missing {miss}" if miss else f"{len(item_keys)} keys on first item",
            )
        else:
            record("nested_list_item_keys", True, "empty list — item keys deferred", skipped=True)

    result["ok"] = result["fail"] == 0
    return result


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    totals = {"endpoints": len(rows), "asserts": 0, "pass": 0, "fail": 0, "skip": 0}
    for row in rows:
        for key in ("asserts", "pass", "fail", "skip"):
            totals[key] += int(row.get(key) or 0)
    totals["endpoint_fail"] = sum(1 for r in rows if not r.get("ok"))
    totals["endpoint_pass"] = totals["endpoints"] - totals["endpoint_fail"]
    return totals


def write_artifacts(rows: List[Dict[str, Any]], summary: Dict[str, int], base_url: str) -> Tuple[Path, Path]:
    logs_dir = repo_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = logs_dir / f"fr-b19-field-contract-{ts}.json"
    md_path = logs_dir / f"fr-b19-field-contract-{ts}.md"

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "disclaimer": DISCLAIMER,
        "summary": summary,
        "cases": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# FR-B19 Field Contract — P0/P1 Python-first sampling",
        "",
        f"**Generated:** {payload['generated_at']}",
        f"**Base URL:** {base_url}",
        f"**Endpoints:** {summary['endpoint_pass']}/{summary['endpoints']} pass",
        f"**Asserts:** pass={summary['pass']} fail={summary['fail']} skip={summary['skip']} "
        f"(total={summary['asserts']})",
        "",
        "## Disclaimer",
        "",
        DISCLAIMER,
        "",
        "## Results",
        "",
        "| id | path | asserts | pass | fail | skip | ok |",
        "|----|------|---------|------|------|------|-----|",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | `{row['path']}` | {row['asserts']} | {row['pass']} | "
            f"{row['fail']} | {row['skip']} | {row.get('ok')} |"
        )
    lines.append("")
    for row in rows:
        if row.get("note"):
            lines.extend([f"### {row['id']}", "", f"Note: {row['note']}", ""])
        fails = [c for c in row.get("checks", []) if c["status"] == "fail"]
        if fails:
            lines.extend([f"### {row['id']} failures", ""])
            for check in fails:
                lines.append(f"- **{check['check']}**: {check['detail']}")
            lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    latest_json = logs_dir / "fr-b19-field-contract-latest.json"
    latest_md = logs_dir / "fr-b19-field-contract-latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"artifact: {json_path}")
    print(f"artifact: {md_path}")
    return json_path, md_path


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="P0/P1 field-level JSON contract sampling")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args(argv)

    rows = [assert_case(args.base_url, case, args.timeout) for case in SAMPLE_CASES]
    summary = summarize(rows)
    print(
        f"endpoints: {summary['endpoint_pass']}/{summary['endpoints']} pass | "
        f"asserts: pass={summary['pass']} fail={summary['fail']} skip={summary['skip']}"
    )
    for row in rows:
        flag = "OK" if row.get("ok") else "FAIL"
        print(f"  {row['id']}: {flag} ({row['pass']}/{row['asserts']} asserts)")
    write_artifacts(rows, summary, args.base_url)
    print(f"\n{DISCLAIMER}")
    return 0 if summary["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
