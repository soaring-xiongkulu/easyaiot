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
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from contract_regression import collect_inventoried_routes, parse_route, server_reachable
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

# Python: VideoPingController (Java mini liveness); contract_regression SMOKE for /video/media → /video/ping
MEDIA_PING_KEYS: Set[str] = {"service", "phase"}

# Python: audio_talk.py health() → data.status, onvif_available, audio_talk_available
AUDIO_TALK_HEALTH_KEYS: Set[str] = {
    "status",
    "onvif_available",
    "audio_talk_available",
}

# Python: models.py DeviceDetectionRegion.to_dict (device_detection_region.py list_device_regions)
DEVICE_DETECTION_ITEM_KEYS: Set[str] = {
    "id",
    "device_id",
    "region_name",
    "region_type",
    "points",
    "image_id",
    "image_path",
    "color",
    "opacity",
    "is_enabled",
    "sort_order",
    "model_ids",
    "created_at",
    "updated_at",
}

# Python: models.py ScenarioPoseLibrary.to_dict + list_libraries entry_count
SCENARIO_POSE_LIBRARY_KEYS: Set[str] = {
    "id",
    "name",
    "code",
    "scene_category",
    "business_tags",
    "description",
    "similarity_threshold",
    "match_mode",
    "intent_event",
    "intent_object",
    "alert_level",
    "is_enabled",
    "entry_count",
    "created_at",
    "updated_at",
}

# Python: alert_service.py get_dashboard_statistics L861-932
ALERT_STATISTICS_KEYS: Set[str] = {
    "alarm_count",
    "today_alarm_count",
    "camera_count",
    "algorithm_count",
    "model_count",
}

# Python: models.py FaceLibrary.to_dict L1251-1273
FACE_LIBRARY_ITEM_KEYS: Set[str] = {
    "id",
    "name",
    "code",
    "business_tags",
    "description",
    "similarity_threshold",
    "is_enabled",
    "face_count",
    "created_at",
    "updated_at",
}

# Python: models.py PlateLibrary.to_dict L1476-1497
PLATE_LIBRARY_ITEM_KEYS: Set[str] = {
    "id",
    "name",
    "code",
    "business_tags",
    "description",
    "is_enabled",
    "plate_count",
    "created_at",
    "updated_at",
}

# Python: models.py SnapTask.to_dict L561-608
SNAP_TASK_ITEM_KEYS: Set[str] = {
    "id",
    "task_name",
    "task_code",
    "space_id",
    "space_name",
    "device_id",
    "device_name",
    "capture_type",
    "cron_expression",
    "frame_skip",
    "algorithm_enabled",
    "algorithm_type",
    "algorithm_model_id",
    "algorithm_threshold",
    "algorithm_night_mode",
    "alarm_enabled",
    "alarm_type",
    "phone_number",
    "email",
    "notify_users",
    "notify_methods",
    "alarm_suppress_time",
    "last_notify_time",
    "auto_filename",
    "custom_filename_prefix",
    "status",
    "is_enabled",
    "run_status",
    "exception_reason",
    "total_captures",
    "last_capture_time",
    "last_success_time",
    "pusher_id",
    "pusher_name",
    "created_at",
    "updated_at",
}

# Python: models.py RecordFile.to_list_item L421-443
RECORD_VIDEO_ITEM_KEYS: Set[str] = {
    "id",
    "object_name",
    "filename",
    "size",
    "last_modified",
    "etag",
    "content_type",
    "url",
    "duration",
    "thumbnail_url",
}

# Python: playback.py get_playback_statistics L292-300
PLAYBACK_STATISTICS_KEYS: Set[str] = {
    "total_count",
    "total_duration",
    "total_size",
}

ARTIFACT_PREFIX = "fr-b23"
MATRIX_ARTIFACT_PREFIX = "fr-b23"

MATRIX_DISCLAIMER = (
    "GET envelope matrix probes inventoried safe GET routes only (no POST/DELETE auto). "
    "Green = HTTP not 5xx and {code,msg,data} present (data may be null). "
    "This is NOT the full field-key matrix and does NOT mean COMPLETE — "
    "see docs/video-java/FULL_REPLACEMENT_GAP.md."
)

# Known seed ids from mini testbed (field_contract SAMPLE_CASES / certify vj_p2_*).
MATRIX_SEED_DEVICE_ID = "vj_p2_device"
MATRIX_PROBE_ID = "1"

# Non-JSON GET routes: skip envelope assert (binary / SSE).
MATRIX_SKIP_PATHS: Set[str] = {
    "/video/alert/image",
    "/video/alert/record",
}

MATRIX_SKIP_SUFFIXES: Tuple[str, ...] = (
    "/events",  # patrol SSE text/event-stream
)

# Optional query suffixes after path materialization (Python-first: required params from blueprints).
MATRIX_QUERY_SUFFIXES: Dict[str, str] = {
    "/video/alert/correlation": "?correlation_id=matrix-probe",
    "/video/alert/record/query": "?device_id=vj_p2_device&alert_time=2026-08-11T10:00:00%2B08:00",
    "/video/camera/audio/talk/capabilities": "?device_id=vj_p2_device",
    "/video/camera/tracks/points": "?device_id=vj_p2_device",
    "/video/record/space/1/videos/day": "?date=2026-08-11",
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
        "python_source": "VIDEO/_retired_python_video/app/services/alert_service.py get_alert_list + _get_alert_filter_query (image_url required)",
        "data_keys": {"alert_list", "total"},
        "list_path": ("data", "alert_list"),
        "list_item_keys": ALERT_ITEM_KEYS,
        "setup": {
            "method": "POST",
            "path": "/video/alert/hook",
            "body": {
                "device_id": "vj_p2_device",
                "device_name": "P2",
                "object": "person",
                "event": "field_contract_probe",
                "region": "gate",
                "time": "2026-08-11T10:00:00+08:00",
                "image_url": "/api/v1/buckets/field-contract/objects/download?prefix=probe.jpg",
            },
            "python_source": "alert_service._get_alert_filter_query L192-195 requires non-empty image_url",
        },
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
        "setup": {
            "method": "POST",
            "path": "/video/playback/",
            "body": {
                "file_path": "/field-contract/playback-probe.mp4",
                "event_time": "2026-08-11T10:00:00+08:00",
                "device_id": "vj_p2_device",
                "device_name": "P2",
                "duration": 60,
            },
            "python_source": "playback.py create_playback POST body (required fields L120)",
        },
    },
    {
        "id": "media_ping",
        "path": "/video/ping",
        "python_source": "tools/video_java/contract_regression.py SMOKE_ENDPOINTS[/video/media] → /video/ping; Java VideoPingController",
        "data_keys": MEDIA_PING_KEYS,
        "note": "Oracle media_hook blueprint has no GET ping; inventoried media-prefix liveness uses /video/ping.",
    },
    {
        "id": "device_detection_regions",
        "path": "/video/device-detection/device/vj_p2_device/regions",
        "python_source": "VIDEO/_retired_python_video/models.py DeviceDetectionRegion.to_dict + device_detection_region.py list_device_regions",
        "data_list": True,
        "list_item_keys": DEVICE_DETECTION_ITEM_KEYS,
    },
    {
        "id": "audio_talk_health",
        "path": "/video/camera/audio/talk/health",
        "python_source": "VIDEO/_retired_python_video/app/blueprints/audio_talk.py health()",
        "data_keys": AUDIO_TALK_HEALTH_KEYS,
    },
    {
        "id": "scenario_pose_libraries",
        "path": "/video/scenario-pose/libraries",
        "python_source": "VIDEO/_retired_python_video/models.py ScenarioPoseLibrary.to_dict + scenario_pose_library_service.list_libraries",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": SCENARIO_POSE_LIBRARY_KEYS,
        "setup": {
            "method": "POST",
            "path": "/video/scenario-pose/libraries",
            "body": {"name": "field-contract-probe-lib"},
            "python_source": "scenario_pose.py create_library POST body name",
        },
    },
    {
        "id": "algorithm_task_get",
        "path": "/video/algorithm/task/1",
        "path_template": "/video/algorithm/task/{id}",
        "python_source": "VIDEO/_retired_python_video/models.py AlgorithmTask.to_dict + algorithm_task.py get_task",
        "data_keys": ALGORITHM_TASK_KEYS,
        "setup": {
            "method": "POST",
            "path": "/video/algorithm/task",
            "body": {
                "task_name": "field-contract-algo-probe",
                "task_type": "realtime",
                "device_ids": ["vj_p2_device"],
                "is_enabled": False,
            },
            "python_source": "algorithm_task.py create_task POST task_name required",
        },
    },
    {
        "id": "stream_forward_task_get",
        "path": "/video/stream-forward/task/1",
        "path_template": "/video/stream-forward/task/{id}",
        "python_source": "VIDEO/_retired_python_video/models.py StreamForwardTask.to_dict + stream_forward.py get_task",
        "data_keys": STREAM_FORWARD_TASK_KEYS,
        "setup": {
            "method": "POST",
            "path": "/video/stream-forward/task",
            "body": {
                "task_name": "field-contract-sf-probe",
                "device_ids": ["vj_p2_device"],
                "is_enabled": False,
            },
            "python_source": "stream_forward.py create_task POST task_name + device_ids",
        },
    },
    {
        "id": "face_libraries",
        "path": "/video/face/libraries",
        "python_source": "VIDEO/_retired_python_video/models.py FaceLibrary.to_dict + face.py list_face_libraries",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": FACE_LIBRARY_ITEM_KEYS,
        "setup": {
            "method": "POST",
            "path": "/video/face/libraries",
            "body": {"name": "field-contract-face-lib"},
            "python_source": "face.py create_face_library POST name",
        },
    },
    {
        "id": "plate_libraries",
        "path": "/video/plate/libraries",
        "python_source": "VIDEO/_retired_python_video/models.py PlateLibrary.to_dict + plate.py list_plate_libraries",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": PLATE_LIBRARY_ITEM_KEYS,
        "setup": {
            "method": "POST",
            "path": "/video/plate/libraries",
            "body": {"name": "field-contract-plate-lib"},
            "python_source": "plate.py create_plate_library POST name",
        },
    },
    {
        "id": "alert_statistics",
        "path": "/video/alert/statistics",
        "python_source": "VIDEO/_retired_python_video/app/services/alert_service.py get_dashboard_statistics",
        "data_keys": ALERT_STATISTICS_KEYS,
    },
    {
        "id": "snap_task_list",
        "path": "/video/snap/task/list?pageNo=1&pageSize=1",
        "python_source": "VIDEO/_retired_python_video/models.py SnapTask.to_dict + snap.py list_tasks",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": SNAP_TASK_ITEM_KEYS,
        "setup": {
            "method": "POST",
            "path": "/video/snap/task",
            "body": {
                "task_name": "field-contract-snap-probe",
                "space_id": 1,
                "device_id": "vj_p2_device",
            },
            "python_source": "snap.py create_task POST task_name + space_id + device_id",
            "prerequisite": {
                "method": "GET",
                "path": "/video/snap/space/device/vj_p2_device",
                "body_key": "space_id",
                "data_key": "id",
                "python_source": "snap.py get_space_by_device resolves space_id for vj_p2_device",
            },
        },
    },
    {
        "id": "record_space_by_device",
        "path": "/video/record/space/device/vj_p2_device",
        "python_source": "VIDEO/_retired_python_video/models.py RecordSpace.to_dict + record.py get_space_by_device",
        "data_keys": RECORD_SPACE_ITEM_KEYS,
    },
    {
        "id": "record_videos_list",
        "path": "/video/record/space/1/videos?pageNo=1&pageSize=1",
        "path_template": "/video/record/space/{id}/videos?pageNo=1&pageSize=1",
        "python_source": "VIDEO/_retired_python_video/models.py RecordFile.to_list_item + record.py list_videos",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": RECORD_VIDEO_ITEM_KEYS,
        "setup": {
            "method": "GET",
            "path": "/video/record/space/device/vj_p2_device",
            "python_source": "record.py get_space_by_device → extract data.id for path_template",
        },
    },
    {
        "id": "playback_statistics",
        "path": "/video/playback/statistics",
        "python_source": "VIDEO/_retired_python_video/app/blueprints/playback.py get_playback_statistics",
        "data_keys": PLAYBACK_STATISTICS_KEYS,
    },
]

ENVELOPE_KEYS: Set[str] = {"code", "msg", "data"}


def materialize_matrix_path(path: str) -> str:
    """Replace {param} with probe-safe literals (seed device id where applicable)."""
    concrete = path
    if "/device/" in concrete or "/device-detection/device/" in concrete:
        concrete = re.sub(r"\{param\}", MATRIX_SEED_DEVICE_ID, concrete)
    else:
        concrete = re.sub(r"\{param\}", MATRIX_PROBE_ID, concrete)
    suffix = MATRIX_QUERY_SUFFIXES.get(concrete)
    if suffix:
        concrete += suffix
    return concrete


def matrix_skip_reason(path: str) -> Optional[str]:
    if path in MATRIX_SKIP_PATHS:
        return "non-JSON binary/stream GET"
    for suffix in MATRIX_SKIP_SUFFIXES:
        if path.endswith(suffix):
            return "non-JSON SSE GET"
    return None


def assert_matrix_route(base_url: str, route: str, timeout: float) -> Dict[str, Any]:
    method, path = parse_route(route)
    probe_path = materialize_matrix_path(path)
    skip_reason = matrix_skip_reason(path)
    result: Dict[str, Any] = {
        "route": route,
        "path": path,
        "probe_path": probe_path,
        "asserts": 0,
        "pass": 0,
        "fail": 0,
        "skip": 0,
        "checks": [],
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

    if method != "GET":
        record("method", True, f"skipped non-GET {method}", skipped=True)
        result["ok"] = True
        return result

    if skip_reason:
        record("non_json", True, skip_reason, skipped=True)
        result["ok"] = True
        return result

    http_status, body, _ = http_get_json(base_url, probe_path, timeout=timeout)
    result["http_status"] = http_status
    result["business_code"] = body.get("code") if isinstance(body, dict) else None

    record("http_status", http_status < 500, f"HTTP {http_status}")

    if http_status >= 500:
        result["ok"] = False
        return result

    miss_env = missing_keys(body, ENVELOPE_KEYS)
    record("envelope", not miss_env, f"missing {miss_env}" if miss_env else "code,msg,data present")

    result["ok"] = result["fail"] == 0
    return result


def run_matrix(base_url: str, timeout: float) -> Tuple[List[Dict[str, Any]], Dict[str, Any], bool, str]:
    server_up, health_detail = server_reachable(base_url, timeout=min(timeout, 3.0))
    routes = collect_inventoried_routes()
    rows: List[Dict[str, Any]] = []
    for idx, route in enumerate(routes, start=1):
        if not server_up:
            method, path = parse_route(route)
            rows.append(
                {
                    "route": route,
                    "path": path,
                    "probe_path": materialize_matrix_path(path),
                    "asserts": 1,
                    "pass": 0,
                    "fail": 0,
                    "skip": 1,
                    "checks": [{"check": "server", "status": "skip", "detail": "server unreachable"}],
                    "ok": True,
                }
            )
            continue
        rows.append(assert_matrix_route(base_url, route, timeout))
        if idx % 25 == 0 or idx == len(routes):
            print(f"  matrix probed {idx}/{len(routes)}")
    summary = summarize(rows)
    summary["get_routes"] = sum(1 for r in routes if parse_route(r)[0] == "GET")
    summary["matrix_skipped"] = sum(1 for row in rows if any(c.get("status") == "skip" for c in row.get("checks", [])))
    return rows, summary, server_up, health_detail


def write_matrix_artifacts(
    rows: List[Dict[str, Any]],
    summary: Dict[str, int],
    base_url: str,
    *,
    server_up: bool,
    health_detail: str,
) -> Tuple[Path, Path]:
    logs_dir = repo_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = logs_dir / f"{MATRIX_ARTIFACT_PREFIX}-field-matrix-{ts}.json"
    md_path = logs_dir / f"{MATRIX_ARTIFACT_PREFIX}-field-matrix-{ts}.md"

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "disclaimer": MATRIX_DISCLAIMER,
        "server_up": server_up,
        "health_detail": health_detail,
        "summary": summary,
        "routes": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        f"# FR-B22 GET Envelope Matrix — inventoried safe GET routes",
        "",
        f"**Generated:** {payload['generated_at']}",
        f"**Base URL:** {base_url}",
        f"**Server up:** {server_up} ({health_detail})",
        f"**Routes:** {summary['endpoint_pass']}/{summary['endpoints']} pass",
        f"**GET inventoried:** {summary.get('get_routes', '—')}",
        f"**Asserts:** pass={summary['pass']} fail={summary['fail']} skip={summary['skip']} "
        f"(total={summary['asserts']})",
        "",
        "## Disclaimer",
        "",
        MATRIX_DISCLAIMER,
        "",
        "## Results",
        "",
        "| route | probe_path | http | asserts | pass | fail | skip | ok |",
        "|-------|------------|------|---------|------|------|------|-----|",
    ]
    for row in rows:
        http_s = row.get("http_status", "—")
        lines.append(
            f"| `{row['route']}` | `{row.get('probe_path', '')}` | {http_s} | {row['asserts']} | "
            f"{row['pass']} | {row['fail']} | {row['skip']} | {row.get('ok')} |"
        )
    lines.append("")
    fails = [r for r in rows if not r.get("ok")]
    if fails:
        lines.extend(["## Failures", ""])
        for row in fails:
            lines.append(f"### {row['route']}")
            for check in row.get("checks", []):
                if check["status"] == "fail":
                    lines.append(f"- **{check['check']}**: {check['detail']}")
            lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    latest_json = logs_dir / f"{MATRIX_ARTIFACT_PREFIX}-field-matrix-latest.json"
    latest_md = logs_dir / f"{MATRIX_ARTIFACT_PREFIX}-field-matrix-latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"artifact: {json_path}")
    print(f"artifact: {md_path}")
    return json_path, md_path




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


def http_post_json(
    base_url: str, path: str, payload: Dict[str, Any], timeout: float = 8.0
) -> Tuple[int, Dict[str, Any], str]:
    url = base_url.rstrip("/") + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
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


def run_setup(base_url: str, setup: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    method = str(setup.get("method", "POST")).upper()
    result: Dict[str, Any] = {
        "method": method,
        "path": setup.get("path"),
        "python_source": setup.get("python_source"),
        "ok": False,
    }

    prerequisite = setup.get("prerequisite")
    body = dict(setup.get("body") or {})
    if prerequisite:
        pre_method = str(prerequisite.get("method", "GET")).upper()
        pre_path = str(prerequisite["path"])
        if pre_method == "GET":
            pre_status, pre_body, _ = http_get_json(base_url, pre_path, timeout=timeout)
        else:
            pre_status, pre_body, _ = http_post_json(
                base_url, pre_path, prerequisite.get("body") or {}, timeout=timeout
            )
        result["prerequisite"] = {
            "method": pre_method,
            "path": pre_path,
            "http_status": pre_status,
            "code": pre_body.get("code") if isinstance(pre_body, dict) else None,
            "ok": pre_status < 500 and isinstance(pre_body, dict) and pre_body.get("code") == 0,
        }
        if not result["prerequisite"]["ok"]:
            result["detail"] = "prerequisite failed"
            return result
        pre_data = pre_body.get("data") if isinstance(pre_body, dict) else None
        body_key = prerequisite.get("body_key")
        data_key = prerequisite.get("data_key", "id")
        if body_key and isinstance(pre_data, dict) and pre_data.get(data_key) is not None:
            body[body_key] = pre_data[data_key]

    if method == "GET":
        status, body_resp, _ = http_get_json(base_url, str(setup["path"]), timeout=timeout)
    elif method == "POST":
        status, body_resp, _ = http_post_json(base_url, str(setup["path"]), body, timeout=timeout)
    else:
        result["detail"] = f"unsupported setup method {method}"
        return result

    result["http_status"] = status
    result["code"] = body_resp.get("code") if isinstance(body_resp, dict) else None
    result["data"] = body_resp.get("data") if isinstance(body_resp, dict) else None
    result["ok"] = status < 500 and body_resp.get("code") == 0
    result["detail"] = body_resp.get("msg") or body_resp.get("message") or ""
    return result


def resolve_case_path(case: Dict[str, Any]) -> str:
    template = case.get("path_template")
    setup_result = case.get("setup_result") or {}
    if template and setup_result.get("ok"):
        data = setup_result.get("data")
        if isinstance(data, dict) and data.get("id") is not None:
            return template.format(id=data["id"])
    return str(case["path"])


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
        "setup": case.get("setup_result"),
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
    json_path = logs_dir / f"{ARTIFACT_PREFIX}-field-contract-{ts}.json"
    md_path = logs_dir / f"{ARTIFACT_PREFIX}-field-contract-{ts}.md"

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "disclaimer": DISCLAIMER,
        "summary": summary,
        "cases": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        f"# FR-B22 Field Contract — 14-prefix P0/P1 Python-first sampling",
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
    latest_json = logs_dir / f"{ARTIFACT_PREFIX}-field-contract-latest.json"
    latest_md = logs_dir / f"{ARTIFACT_PREFIX}-field-contract-latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"artifact: {json_path}")
    print(f"artifact: {md_path}")
    return json_path, md_path


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="P0/P1 field-level JSON contract sampling")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument(
        "--matrix",
        action="store_true",
        help="auto GET envelope matrix over inventoried safe GET routes",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="run FR-B22 hand-curated deep field samples (default when no mode flag)",
    )
    args = parser.parse_args(argv)

    run_deep = args.deep or not args.matrix
    exit_code = 0

    if run_deep:
        rows: List[Dict[str, Any]] = []
        for case in SAMPLE_CASES:
            case_copy = dict(case)
            if case_copy.get("setup"):
                case_copy["setup_result"] = run_setup(args.base_url, case_copy["setup"], args.timeout)
            case_copy["path"] = resolve_case_path(case_copy)
            rows.append(assert_case(args.base_url, case_copy, args.timeout))
        summary = summarize(rows)
        print(
            f"deep endpoints: {summary['endpoint_pass']}/{summary['endpoints']} pass | "
            f"asserts: pass={summary['pass']} fail={summary['fail']} skip={summary['skip']}"
        )
        for row in rows:
            flag = "OK" if row.get("ok") else "FAIL"
            print(f"  {row['id']}: {flag} ({row['pass']}/{row['asserts']} asserts)")
        write_artifacts(rows, summary, args.base_url)
        print(f"\n{DISCLAIMER}")
        if summary["fail"] != 0:
            exit_code = 1

    if args.matrix:
        route_count = len(collect_inventoried_routes())
        print(f"\nGET matrix base_url={args.base_url} inventoried_routes={route_count}")
        matrix_rows, matrix_summary, server_up, health_detail = run_matrix(args.base_url, args.timeout)
        print(
            f"matrix: {matrix_summary['endpoint_pass']}/{matrix_summary['endpoints']} pass | "
            f"asserts: pass={matrix_summary['pass']} fail={matrix_summary['fail']} "
            f"skip={matrix_summary['skip']} server_up={server_up}"
        )
        write_matrix_artifacts(
            matrix_rows, matrix_summary, args.base_url, server_up=server_up, health_detail=health_detail
        )
        print(f"\n{MATRIX_DISCLAIMER}")
        if matrix_summary["fail"] != 0:
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
