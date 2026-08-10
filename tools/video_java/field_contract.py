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

# Python: models.py FaceMatchRecord.to_dict L1427-1457
FACE_MATCH_RECORD_KEYS: Set[str] = {
    "id",
    "task_id",
    "task_name",
    "device_id",
    "device_name",
    "library_id",
    "library_name",
    "face_image_path",
    "matched",
    "matched_person_name",
    "matched_person_code",
    "matched_face_entry_id",
    "similarity",
    "threshold",
    "candidates",
    "alert_id",
    "correlation_id",
    "task_type",
    "status",
    "error_message",
    "created_at",
}

# Python: models.py PlateMatchRecord.to_dict L1614-1636
PLATE_MATCH_RECORD_KEYS: Set[str] = {
    "id",
    "task_id",
    "task_name",
    "device_id",
    "device_name",
    "library_id",
    "library_name",
    "plate_no",
    "plate_color",
    "plate_image_path",
    "matched",
    "matched_plate_entry_id",
    "matched_owner_name",
    "detect_conf",
    "alert_id",
    "correlation_id",
    "task_type",
    "status",
    "error_message",
    "created_at",
}

# Python: face_model_download.py _build_status_locked L168-180
FACE_MODEL_STATUS_KEYS: Set[str] = {
    "exists",
    "filename",
    "path",
    "size_bytes",
    "downloading",
    "resumable",
    "stage",
    "progress",
    "downloaded_bytes",
    "total_bytes",
    "error",
}

# Python: camera.py list_device_locations → map item keys (device_id + lat/lng/name)
CAMERA_LOCATION_ITEM_KEYS: Set[str] = {
    "id",
    "name",
    "source",
    "directory_id",
    "online",
    "longitude",
    "latitude",
    "altitude",
    "address",
    "heading",
    "location_source",
    "location_updated_at",
    "has_location",
}

# Python: camera.py list_directories tree node L2529-2538
CAMERA_DIRECTORY_ITEM_KEYS: Set[str] = {
    "id",
    "name",
    "parent_id",
    "description",
    "sort_order",
    "device_count",
    "children",
}

# Python: nvr_service.list_nvrs
NVR_ITEM_KEYS: Set[str] = {
    "id",
    "ip",
    "port",
    "name",
    "model",
    "vendor",
    "serial_number",
    "firmware_version",
    "device_type",
    "mac",
    "scheme",
    "rtsp_url",
    "source",
    "web_url",
}

# Python: models.py DeviceTrackSession.to_dict L147-160
DEVICE_TRACK_SESSION_KEYS: Set[str] = {
    "id",
    "device_id",
    "title",
    "started_at",
    "ended_at",
    "point_count",
    "distance_m",
    "source",
    "external_key",
    "created_at",
    "updated_at",
}

# Python: models.py SnapImage.to_list_item L487-496
SNAP_IMAGE_ITEM_KEYS: Set[str] = {
    "id",
    "object_name",
    "filename",
    "size",
    "last_modified",
    "captured_at",
    "source",
    "task_id",
    "url",
    "etag",
    "content_type",
}

ARTIFACT_PREFIX = "fr-b27"
MATRIX_ARTIFACT_PREFIX = "fr-b27"
KEYS_MATRIX_ARTIFACT_PREFIX = "fr-b29"
MUTATING_MATRIX_ARTIFACT_PREFIX = "fr-b31"
POST_KEYS_MATRIX_ARTIFACT_PREFIX = "fr-b33"

MATRIX_DISCLAIMER = (
    "GET envelope matrix probes inventoried safe GET routes only (no POST/DELETE auto). "
    "Green = HTTP not 5xx and {code,msg,data} present (data may be null). "
    "This is NOT the full field-key matrix and does NOT mean COMPLETE — "
    "see docs/video-java/FULL_REPLACEMENT_GAP.md."
)

KEYS_MATRIX_DISCLAIMER = (
    "GET keys-matrix probes all inventoried safe GET JSON routes: always envelope "
    "{code,msg,data}; when a Python to_dict / blueprint mapping exists, asserts "
    "documented keys on first list item or data object (empty data → key assert "
    "deferred, not fail). Unmapped routes count envelope-only. "
    "This is NOT exhaustive 259-route field parity and does NOT mean COMPLETE — "
    "see docs/video-java/FULL_REPLACEMENT_GAP.md."
)

MUTATING_MATRIX_DISCLAIMER = (
    "POST/PUT mutating-matrix probes inventoried safe mutating routes with empty/minimal "
    "JSON bodies. Green = HTTP not 5xx and (2xx envelope {code,msg,data} OR 4xx validation/auth). "
    "Skips DELETE, destructive cleanup/remove paths, and multipart-only routes without fixtures. "
    "This is NOT POST field-key parity and does NOT mean COMPLETE — "
    "see docs/video-java/FULL_REPLACEMENT_GAP.md."
)

POST_KEYS_MATRIX_DISCLAIMER = (
    "POST keys-matrix probes curated high-value POST creates (frb33_* synthetic names) with "
    "Python-first to_dict / blueprint success body key asserts on code==0; validation 4xx "
    "assert envelope {code,msg} only. Create-then-delete where safe. "
    "This is NOT exhaustive POST field parity and does NOT mean COMPLETE — "
    "see docs/video-java/FULL_REPLACEMENT_GAP.md."
)

# Python-first: POST success envelopes — e.g. algorithm_task.py create_task L144-148,
# snap.py cleanup_device_storage L889-893, playback.py create_playback.
MUTATING_SKIP_PATH_RE = re.compile(
    r"/(cleanup|delete|remove|wipe|destroy|purge|clear-all|truncate)(/|$)",
    re.IGNORECASE,
)
MUTATING_MULTIPART_PATH_RE = re.compile(
    r"/(upload|import-template|multipart|batch-import)(/|$)",
    re.IGNORECASE,
)

# Minimal probe bodies when empty {} would always 400 on required-field routes (Python-first cites).
MUTATING_MINIMAL_BODIES: Dict[str, Dict[str, Any]] = {
    "/video/alert/hook": {
        "device_id": "vj_p2_device",
        "object": "person",
        "event": "frb31_probe",
        "time": "2026-08-11T10:00:00+08:00",
        "image_url": "/api/v1/buckets/frb31_probe/objects/download?prefix=probe.jpg",
    },
}

# Known seed ids from mini testbed (field_contract SAMPLE_CASES / certify vj_p2_*).
MATRIX_SEED_DEVICE_ID = "vj_p2_device"
MATRIX_PROBE_ID = "1"

# Non-JSON GET routes: skip envelope assert (binary / SSE).
# FR-B32: full 6-route content-type probes in fr_b32_binary_get.py (not envelope matrix):
#   alert/image, alert/record, patrol/session/{id}/events (SSE),
#   playback/thumbnail/{id} (JSON meta), record/.../video/{obj}, snap/.../image/{obj}.
# Artifact: logs/fr-b32-binary-get-latest.json — classified as content-type pass, not envelope.
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
    "/video/camera/tracks/sessions": "?device_id=vj_p2_device",
    "/video/record/space/1/videos/day": "?date=2026-08-11",
}

# Default pagination / filter query strings (from SAMPLE_CASES paths).
KEYS_MATRIX_DEFAULT_QUERY: Dict[str, str] = {
    "/video/alert/page": "?pageNo=1&pageSize=1",
    "/video/algorithm/task/list": "?pageNo=1&pageSize=1",
    "/video/camera/list": "?pageNo=1&pageSize=1",
    "/video/snap/space/list": "?pageNo=1&pageSize=1",
    "/video/record/space/list": "?pageNo=1&pageSize=1",
    "/video/stream-forward/task/list": "?pageNo=1&pageSize=1",
    "/video/playback/list": "?pageNo=1&pageSize=1",
    "/video/snap/task/list": "?pageNo=1&pageSize=1",
    "/video/record/space/{param}/videos": "?pageNo=1&pageSize=1",
    "/video/face/matching/records": "?page=1&page_size=1",
    "/video/plate/matching/records": "?page=1&page_size=1",
    "/video/scenario-pose/libraries": "",
}

# Extra path→key specs not covered by SAMPLE_CASES path normalization (Python-first).
EXTRA_ROUTE_KEY_SPECS: Dict[str, Dict[str, Any]] = {
    "/video/snap/task/{param}": {
        "id": "snap_task_get",
        "python_source": "VIDEO/_retired_python_video/models.py SnapTask.to_dict + snap.py get_task",
        "data_keys": SNAP_TASK_ITEM_KEYS,
    },
    "/video/record/space/{param}": {
        "id": "record_space_get",
        "python_source": "VIDEO/_retired_python_video/models.py RecordSpace.to_dict + record.py get_space",
        "data_keys": RECORD_SPACE_ITEM_KEYS,
    },
    "/video/stream-forward/task/{param}": {
        "id": "stream_forward_task_get_extra",
        "python_source": "VIDEO/_retired_python_video/models.py StreamForwardTask.to_dict + stream_forward.py get_task",
        "data_keys": STREAM_FORWARD_TASK_KEYS,
    },
}

# FR-B29: merged at build_route_key_specs() from keys_matrix_b29_specs (Python-first).

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
    {
        "id": "face_matching_records",
        "path": "/video/face/matching/records?page=1&page_size=1",
        "python_source": "VIDEO/_retired_python_video/models.py FaceMatchRecord.to_dict + face.py list_face_match_records",
        "data_keys": {"list", "total"},
        "list_path": ("data", "list"),
        "list_item_keys": FACE_MATCH_RECORD_KEYS,
    },
    {
        "id": "plate_matching_records",
        "path": "/video/plate/matching/records?page=1&page_size=1",
        "python_source": "VIDEO/_retired_python_video/models.py PlateMatchRecord.to_dict + plate.py list_plate_match_records",
        "data_keys": {"list", "total"},
        "list_path": ("data", "list"),
        "list_item_keys": PLATE_MATCH_RECORD_KEYS,
    },
    {
        "id": "face_model_status",
        "path": "/video/face/model/status",
        "python_source": "VIDEO/_retired_python_video/app/utils/face_model_download.py get_face_rec_model_status",
        "data_keys": FACE_MODEL_STATUS_KEYS,
    },
    {
        "id": "plate_model_status",
        "path": "/video/plate/model/status",
        "python_source": "VIDEO/_retired_python_video/app/utils/plate_model_download.py get_plate_model_status",
        "data_keys": PLATE_HEALTH_KEYS,
    },
    {
        "id": "face_library_get",
        "path": "/video/face/libraries/1",
        "path_template": "/video/face/libraries/{id}",
        "python_source": "VIDEO/_retired_python_video/models.py FaceLibrary.to_dict + face.py get_face_library",
        "data_keys": FACE_LIBRARY_ITEM_KEYS,
        "setup": {
            "method": "POST",
            "path": "/video/face/libraries",
            "body": {"name": "field-contract-face-get-probe"},
            "python_source": "face.py create_face_library POST name",
        },
    },
    {
        "id": "plate_library_get",
        "path": "/video/plate/libraries/1",
        "path_template": "/video/plate/libraries/{id}",
        "python_source": "VIDEO/_retired_python_video/models.py PlateLibrary.to_dict + plate.py get_plate_library",
        "data_keys": PLATE_LIBRARY_ITEM_KEYS,
        "setup": {
            "method": "POST",
            "path": "/video/plate/libraries",
            "body": {"name": "field-contract-plate-get-probe"},
            "python_source": "plate.py create_plate_library POST name",
        },
    },
    {
        "id": "camera_locations",
        "path": "/video/camera/locations",
        "python_source": "VIDEO/_retired_python_video/app/blueprints/camera.py list_device_locations",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": CAMERA_LOCATION_ITEM_KEYS,
    },
    {
        "id": "camera_directory_list",
        "path": "/video/camera/directory/list",
        "python_source": "VIDEO/_retired_python_video/app/blueprints/camera.py list_directories",
        "data_list": True,
        "list_item_keys": CAMERA_DIRECTORY_ITEM_KEYS,
    },
    {
        "id": "camera_nvr_list",
        "path": "/video/camera/nvr/list",
        "python_source": "VIDEO/_retired_python_video/app/services/nvr_service.py list_nvrs",
        "data_list": True,
        "list_item_keys": NVR_ITEM_KEYS,
    },
    {
        "id": "camera_tracks_sessions",
        "path": "/video/camera/tracks/sessions?device_id=vj_p2_device",
        "python_source": "VIDEO/_retired_python_video/models.py DeviceTrackSession.to_dict + camera.py tracks/sessions",
        "data_list": True,
        "list_item_keys": DEVICE_TRACK_SESSION_KEYS,
    },
    {
        "id": "snap_space_get",
        "path": "/video/snap/space/1",
        "path_template": "/video/snap/space/{id}",
        "python_source": "VIDEO/_retired_python_video/models.py SnapSpace.to_dict + snap.py get_space",
        "data_keys": SNAP_SPACE_ITEM_KEYS,
        "setup": {
            "method": "GET",
            "path": "/video/snap/space/device/vj_p2_device",
            "python_source": "snap.py get_space_by_device → extract data.id for path_template",
        },
    },
    {
        "id": "playback_get",
        "path": "/video/playback/1",
        "path_template": "/video/playback/{id}",
        "python_source": "VIDEO/_retired_python_video/models.py Playback.to_dict + playback.py get_playback",
        "data_keys": PLAYBACK_ITEM_KEYS,
        "setup": {
            "method": "POST",
            "path": "/video/playback/",
            "body": {
                "file_path": "/field-contract/playback-get-probe.mp4",
                "event_time": "2026-08-11T10:00:00+08:00",
                "device_id": "vj_p2_device",
                "device_name": "P2",
                "duration": 60,
            },
            "python_source": "playback.py create_playback POST body",
        },
    },
    {
        "id": "scenario_pose_library_get",
        "path": "/video/scenario-pose/libraries/1",
        "path_template": "/video/scenario-pose/libraries/{id}",
        "python_source": "VIDEO/_retired_python_video/models.py ScenarioPoseLibrary.to_dict + scenario_pose.py get_library",
        "data_keys": SCENARIO_POSE_LIBRARY_KEYS,
        "setup": {
            "method": "POST",
            "path": "/video/scenario-pose/libraries",
            "body": {"name": "field-contract-pose-get-probe"},
            "python_source": "scenario_pose.py create_library POST name",
        },
    },
    {
        "id": "stream_forward_task_status",
        "path": "/video/stream-forward/task/1/status",
        "path_template": "/video/stream-forward/task/{id}/status",
        "python_source": "VIDEO/_retired_python_video/app/blueprints/stream_forward.py get_task_status",
        "data_keys": {
            "task_id",
            "task_name",
            "server_ip",
            "port",
            "process_id",
            "last_heartbeat",
            "log_path",
            "status",
            "total_streams",
            "schedule_policy",
            "target_node_id",
            "node_id",
            "device_deployments",
            "deployment_count",
        },
        "setup": {
            "method": "POST",
            "path": "/video/stream-forward/task",
            "body": {
                "task_name": "field-contract-sf-status-probe",
                "device_ids": ["vj_p2_device"],
                "is_enabled": False,
            },
            "python_source": "stream_forward.py create_task POST task_name + device_ids",
        },
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


def normalize_inventory_path(path: str) -> str:
    """Normalize concrete probe paths to inventoried {param} patterns."""
    concrete = path.split("?", 1)[0]
    concrete = re.sub(r"/vj_p2_device\b", "/{param}", concrete)
    concrete = re.sub(r"/\d+(?=/|$)", "/{param}", concrete)
    return concrete


def build_route_key_specs() -> Dict[str, Dict[str, Any]]:
    """Build path→key spec map from SAMPLE_CASES + EXTRA_ROUTE_KEY_SPECS (Python-first)."""
    specs: Dict[str, Dict[str, Any]] = {}

    def ingest(path: str, case: Dict[str, Any]) -> None:
        spec: Dict[str, Any] = {
            "id": case.get("id"),
            "python_source": case.get("python_source"),
        }
        if case.get("data_keys"):
            spec["data_keys"] = set(case["data_keys"])
        if case.get("data_list"):
            spec["data_list"] = True
        if case.get("top_keys"):
            spec["top_keys"] = set(case["top_keys"])
        if case.get("list_item_keys"):
            spec["list_item_keys"] = set(case["list_item_keys"])
        list_path = case.get("list_path")
        if list_path:
            lp = list(list_path)
            if lp and lp[0] == "data":
                lp = lp[1:]
            spec["list_path"] = tuple(lp)
        specs[path] = spec

    for case in SAMPLE_CASES:
        template = case.get("path_template")
        if template:
            path = template.replace("{id}", "{param}")
        else:
            path = normalize_inventory_path(str(case["path"]))
        ingest(path, case)

    for path, extra in EXTRA_ROUTE_KEY_SPECS.items():
        merged = dict(extra)
        if "data_keys" in merged and not isinstance(merged["data_keys"], set):
            merged["data_keys"] = set(merged["data_keys"])
        if "list_item_keys" in merged and not isinstance(merged["list_item_keys"], set):
            merged["list_item_keys"] = set(merged["list_item_keys"])
        specs[path] = merged

    try:
        from keys_matrix_b29_specs import bind_field_contract_keys, B29_EXTRA_ROUTE_KEY_SPECS

        bind_field_contract_keys(sys.modules[__name__])
        for path, extra in B29_EXTRA_ROUTE_KEY_SPECS.items():
            merged = dict(extra)
            if "data_keys" in merged and not isinstance(merged["data_keys"], set):
                merged["data_keys"] = set(merged["data_keys"])
            if "list_item_keys" in merged and not isinstance(merged["list_item_keys"], set):
                merged["list_item_keys"] = set(merged["list_item_keys"])
            if "top_keys" in merged and not isinstance(merged["top_keys"], set):
                merged["top_keys"] = set(merged["top_keys"])
            specs[path] = merged
    except ImportError:
        pass

    return specs


def materialize_keys_matrix_path(path: str, *, created_ids: Optional[Dict[str, str]] = None) -> str:
    """Materialize inventoried path + default query suffixes for keys-matrix probes."""
    concrete = path
    if created_ids:
        if path in created_ids:
            concrete = path.replace("{param}", created_ids[path], 1)
        elif "{param}" in path:
            # Replace first {param} using longest matching parent prefix in created_ids
            best_parent = ""
            best_id = None
            for parent, entity_id in created_ids.items():
                if "{param}" not in parent:
                    continue
                if path.startswith(parent.rsplit("{param}", 1)[0]) and len(parent) > len(best_parent):
                    best_parent = parent
                    best_id = entity_id
            if best_id and "{param}" in concrete:
                concrete = concrete.replace("{param}", best_id, 1)
    if "{param}" in concrete:
        concrete = materialize_matrix_path(path if concrete == path else concrete)
    base = concrete.split("?", 1)[0]
    if "?" in concrete:
        return concrete
    extra = MATRIX_QUERY_SUFFIXES.get(base) or KEYS_MATRIX_DEFAULT_QUERY.get(base) or KEYS_MATRIX_DEFAULT_QUERY.get(path)
    if extra:
        return base + extra
    return concrete


def build_setup_id_map(setups: List[Dict[str, Any]]) -> Dict[str, str]:
    """Map inventoried path templates to entity ids created by SAMPLE_CASES setups."""
    case_by_id = {c["id"]: c for c in SAMPLE_CASES}
    id_map: Dict[str, str] = {}
    for setup in setups:
        if not setup.get("ok"):
            continue
        case = case_by_id.get(setup.get("case_id", ""))
        if not case:
            continue
        template = case.get("path_template")
        data = setup.get("data")
        if template and isinstance(data, dict) and data.get("id") is not None:
            norm = template.replace("{id}", "{param}").split("?", 1)[0]
            id_map[norm] = str(data["id"])

    # record_space_by_device GET setup → bind /video/record/space/{param}
    for setup in setups:
        if setup.get("case_id") != "record_space_by_device" or not setup.get("ok"):
            continue
        data = setup.get("data")
        if isinstance(data, dict) and data.get("id") is not None:
            id_map["/video/record/space/{param}"] = str(data["id"])

    algo_id = id_map.get("/video/algorithm/task/{param}")
    if algo_id:
        prefix = "/video/algorithm/task/{param}/"
        for path in build_route_key_specs().keys():
            if path.startswith(prefix):
                id_map.setdefault(path, algo_id)

    sf_id = id_map.get("/video/stream-forward/task/{param}")
    if sf_id:
        prefix = "/video/stream-forward/task/{param}/"
        for path in build_route_key_specs().keys():
            if path.startswith(prefix):
                id_map.setdefault(path, sf_id)

    nvr_id = None
    for setup in setups:
        if str(setup.get("case_id", "")).startswith("b29_nvr") and setup.get("nvr_id"):
            nvr_id = str(setup["nvr_id"])
            break
    if nvr_id:
        id_map["/video/camera/nvr/{param}"] = nvr_id

    return id_map


def run_global_setups(base_url: str, timeout: float) -> List[Dict[str, Any]]:
    """Run SAMPLE_CASES setup blocks once so list/item key probes have seed data."""
    results: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for case in SAMPLE_CASES:
        setup = case.get("setup")
        if not setup:
            continue
        key = json.dumps(setup, sort_keys=True, default=str)
        if key in seen:
            continue
        seen.add(key)
        result = run_setup(base_url, setup, timeout)
        result["case_id"] = case.get("id")
        results.append(result)
        flag = "OK" if result.get("ok") else "FAIL"
        print(f"  setup {case.get('id')}: {flag}")
    return results


def assert_keys_matrix_route(
    base_url: str,
    route: str,
    spec: Optional[Dict[str, Any]],
    timeout: float,
    *,
    created_ids: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    method, path = parse_route(route)
    probe_path = materialize_keys_matrix_path(path, created_ids=created_ids)
    skip_reason = matrix_skip_reason(path)
    result: Dict[str, Any] = {
        "route": route,
        "path": path,
        "probe_path": probe_path,
        "mapping_id": spec.get("id") if spec else None,
        "python_source": spec.get("python_source") if spec else None,
        "mode": "envelope_only" if not spec else "key_assert",
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

    if not spec:
        result["ok"] = result["fail"] == 0
        return result

    for key in sorted(spec.get("top_keys") or ()):
        present = key in body
        record(f"top.{key}", present, f"{'present' if present else 'missing'}")

    data = body.get("data")
    data_keys = spec.get("data_keys")
    if data_keys and not spec.get("data_list") and not spec.get("list_path"):
        if data is None:
            record("data_keys", True, "data null — keys deferred", skipped=True)
        else:
            miss = missing_keys(data, data_keys)
            record("data_keys", not miss, f"missing {miss}" if miss else f"{len(data_keys)} keys ok")

    if spec.get("data_list"):
        if data is None:
            record("data_is_list", True, "data null — list keys deferred", skipped=True)
        else:
            items: List[Any] = data if isinstance(data, list) else []
            item_keys = spec.get("list_item_keys") or set()
            record("data_is_list", isinstance(data, list), f"type={type(data).__name__}")
            if items and item_keys:
                miss = missing_keys(items[0], item_keys)
                record(
                    "list_item_keys",
                    not miss,
                    f"missing {miss}" if miss else f"{len(item_keys)} keys on first item",
                )
            elif item_keys:
                record("list_item_keys", True, "empty list — item keys deferred", skipped=True)

    list_path = spec.get("list_path")
    item_keys = spec.get("list_item_keys")
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


def run_keys_matrix(base_url: str, timeout: float) -> Tuple[List[Dict[str, Any]], Dict[str, Any], bool, str, List[Dict[str, Any]]]:
    server_up, health_detail = server_reachable(base_url, timeout=min(timeout, 3.0))
    specs = build_route_key_specs()
    print(f"  key mappings: {len(specs)} routes (Python-first from SAMPLE_CASES)")
    setups: List[Dict[str, Any]] = []
    if server_up:
        print("  running global setups for seed data...")
        setups = run_global_setups(base_url, timeout)
        setups.extend(run_b29_seed_setups(base_url, timeout))
    created_ids = build_setup_id_map(setups)

    routes = collect_inventoried_routes()
    rows: List[Dict[str, Any]] = []
    mapped = 0
    envelope_only = 0
    key_assert_pass = 0
    key_assert_fail = 0

    for idx, route in enumerate(routes, start=1):
        method, path = parse_route(route)
        if method != "GET":
            rows.append(
                {
                    "route": route,
                    "path": path,
                    "probe_path": materialize_keys_matrix_path(path, created_ids=created_ids),
                    "mode": "non_get_skip",
                    "asserts": 1,
                    "pass": 0,
                    "fail": 0,
                    "skip": 1,
                    "checks": [{"check": "method", "status": "skip", "detail": f"skipped {method}"}],
                    "ok": True,
                }
            )
            continue

        if not server_up:
            rows.append(
                {
                    "route": route,
                    "path": path,
                    "probe_path": materialize_keys_matrix_path(path, created_ids=created_ids),
                    "mode": "server_down",
                    "asserts": 1,
                    "pass": 0,
                    "fail": 0,
                    "skip": 1,
                    "checks": [{"check": "server", "status": "skip", "detail": "server unreachable"}],
                    "ok": True,
                }
            )
            continue

        spec = specs.get(path)
        if matrix_skip_reason(path):
            spec = None
        row = assert_keys_matrix_route(base_url, route, spec, timeout, created_ids=created_ids)
        rows.append(row)
        if row.get("mode") == "envelope_only":
            envelope_only += 1
        elif row.get("mode") == "key_assert":
            mapped += 1
            for check in row.get("checks", []):
                if check["check"] in ("list_item_keys", "nested_list_item_keys", "data_keys"):
                    if check["status"] == "pass":
                        key_assert_pass += 1
                    elif check["status"] == "fail":
                        key_assert_fail += 1

        if idx % 25 == 0 or idx == len(routes):
            print(f"  keys-matrix probed {idx}/{len(routes)}")

    summary = summarize(rows)
    summary["get_routes"] = sum(1 for r in routes if parse_route(r)[0] == "GET")
    summary["json_get_routes"] = sum(
        1 for r in routes if parse_route(r)[0] == "GET" and not matrix_skip_reason(parse_route(r)[1])
    )
    summary["mapped_routes"] = mapped
    summary["envelope_only_routes"] = envelope_only
    summary["non_json_skipped"] = sum(
        1 for r in routes if parse_route(r)[0] == "GET" and matrix_skip_reason(parse_route(r)[1])
    )
    summary["key_assert_pass"] = key_assert_pass
    summary["key_assert_fail"] = key_assert_fail
    summary["mapping_table_size"] = len(specs)
    summary["setups_run"] = len(setups)
    summary["setups_ok"] = sum(1 for s in setups if s.get("ok"))
    return rows, summary, server_up, health_detail, setups


def write_keys_matrix_artifacts(
    rows: List[Dict[str, Any]],
    summary: Dict[str, Any],
    base_url: str,
    specs: Dict[str, Dict[str, Any]],
    setups: List[Dict[str, Any]],
    *,
    server_up: bool,
    health_detail: str,
) -> Tuple[Path, Path]:
    logs_dir = repo_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = logs_dir / f"{KEYS_MATRIX_ARTIFACT_PREFIX}-keys-matrix-{ts}.json"
    md_path = logs_dir / f"{KEYS_MATRIX_ARTIFACT_PREFIX}-keys-matrix-{ts}.md"

    mapping_table = [
        {
            "path": path,
            "id": spec.get("id"),
            "python_source": spec.get("python_source"),
            "data_keys": sorted(spec["data_keys"]) if spec.get("data_keys") else None,
            "data_list": bool(spec.get("data_list")),
            "list_item_keys_count": len(spec["list_item_keys"]) if spec.get("list_item_keys") else 0,
        }
        for path, spec in sorted(specs.items())
    ]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "disclaimer": KEYS_MATRIX_DISCLAIMER,
        "server_up": server_up,
        "health_detail": health_detail,
        "summary": summary,
        "mapping_table": mapping_table,
        "setups": setups,
        "routes": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# FR-B29 GET Keys Matrix — inventoried routes (Python-first)",
        "",
        f"**Generated:** {payload['generated_at']}",
        f"**Base URL:** {base_url}",
        f"**Server up:** {server_up} ({health_detail})",
        f"**Routes:** {summary['endpoint_pass']}/{summary['endpoints']} pass",
        f"**GET inventoried:** {summary.get('get_routes', '—')} (JSON GET: {summary.get('json_get_routes', '—')})",
        f"**Mapped (key assert):** {summary.get('mapped_routes', '—')} | "
        f"**Envelope-only:** {summary.get('envelope_only_routes', '—')} | "
        f"**Non-JSON skip:** {summary.get('non_json_skipped', '—')}",
        f"**Key asserts:** pass={summary.get('key_assert_pass', 0)} fail={summary.get('key_assert_fail', 0)}",
        f"**Asserts:** pass={summary['pass']} fail={summary['fail']} skip={summary['skip']} "
        f"(total={summary['asserts']})",
        f"**Mapping table:** {summary.get('mapping_table_size', '—')} paths",
        "",
        "## Disclaimer",
        "",
        KEYS_MATRIX_DISCLAIMER,
        "",
        "## Python-first mapping table",
        "",
        "| path | id | python_source | data_keys | list_keys |",
        "|------|----|---------------|-----------|-----------|",
    ]
    for row in mapping_table:
        if row["data_keys"]:
            dk = ", ".join(row["data_keys"][:4])
            if len(row["data_keys"]) > 4:
                dk += "…"
        else:
            dk = "—"
        src = row["python_source"] or ""
        src_cell = f"{src[:60]}…" if len(src) > 60 else src
        lines.append(
            f"| `{row['path']}` | {row['id']} | {src_cell} | {dk} | {row['list_item_keys_count'] or '—'} |"
        )
    lines.extend(
        [
            "",
            "## Results",
            "",
            "| route | mode | probe_path | http | key_assert | ok |",
            "|-------|------|------------|------|------------|-----|",
        ]
    )
    for row in rows:
        http_s = row.get("http_status", "—")
        key_checks = [
            c
            for c in row.get("checks", [])
            if c["check"] in ("list_item_keys", "nested_list_item_keys", "data_keys")
        ]
        key_status = key_checks[0]["status"] if key_checks else "—"
        lines.append(
            f"| `{row['route']}` | {row.get('mode', '—')} | `{row.get('probe_path', '')}` | "
            f"{http_s} | {key_status} | {row.get('ok')} |"
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
    latest_json = logs_dir / f"{KEYS_MATRIX_ARTIFACT_PREFIX}-keys-matrix-latest.json"
    latest_md = logs_dir / f"{KEYS_MATRIX_ARTIFACT_PREFIX}-keys-matrix-latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"artifact: {json_path}")
    print(f"artifact: {md_path}")
    return json_path, md_path


def mutating_skip_reason(path: str, method: str) -> Optional[str]:
    if method == "DELETE":
        return "DELETE skipped"
    if MUTATING_SKIP_PATH_RE.search(path):
        return "destructive cleanup/remove path"
    if MUTATING_MULTIPART_PATH_RE.search(path):
        return "multipart-only without fixture"
    return None


def materialize_mutating_path(path: str) -> str:
    """Materialize inventoried POST/PUT paths with probe-safe literals."""
    concrete = path
    if "/device/" in concrete or "/device-detection/device/" in concrete:
        concrete = re.sub(r"\{param\}", MATRIX_SEED_DEVICE_ID, concrete)
    else:
        concrete = re.sub(r"\{param\}", MATRIX_PROBE_ID, concrete)
    return concrete


def mutating_probe_body(path: str) -> Dict[str, Any]:
    base = path.split("?", 1)[0]
    return dict(MUTATING_MINIMAL_BODIES.get(base, {}))


def http_mutate_json(
    base_url: str,
    method: str,
    path: str,
    payload: Dict[str, Any],
    timeout: float = 8.0,
) -> Tuple[int, Dict[str, Any], str]:
    if method == "POST":
        return http_post_json(base_url, path, payload, timeout=timeout)
    if method == "PUT":
        return http_put_json(base_url, path, payload, timeout=timeout)
    raise ValueError(f"unsupported mutating method {method}")


def assert_mutating_route(base_url: str, route: str, timeout: float) -> Dict[str, Any]:
    method, path = parse_route(route)
    probe_path = materialize_mutating_path(path)
    skip_reason = mutating_skip_reason(path, method)
    body = mutating_probe_body(path)
    result: Dict[str, Any] = {
        "route": route,
        "path": path,
        "probe_path": probe_path,
        "probe_body": body,
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

    if method not in ("POST", "PUT"):
        record("method", True, f"skipped non-mutating {method}", skipped=True)
        result["ok"] = True
        return result

    if skip_reason:
        record("skip_route", True, skip_reason, skipped=True)
        result["ok"] = True
        return result

    http_status, resp_body, raw = http_mutate_json(base_url, method, probe_path, body, timeout=timeout)
    result["http_status"] = http_status
    result["business_code"] = resp_body.get("code") if isinstance(resp_body, dict) else None

    record("http_status", http_status < 500, f"HTTP {http_status}")
    if http_status >= 500:
        result["ok"] = False
        return result

    if 400 <= http_status < 500:
        if isinstance(resp_body, dict) and {"code", "msg"} <= set(resp_body.keys()):
            record("envelope_4xx", True, "code,msg present on 4xx")
        else:
            record("envelope_4xx", True, f"HTTP {http_status} validation/auth (non-envelope ok)")
        result["ok"] = result["fail"] == 0
        return result

    if http_status < 200 or http_status >= 300:
        record("http_bucket", False, f"unexpected HTTP {http_status}")
        result["ok"] = False
        return result

    if "_raw" in resp_body and not {"code", "msg"} <= set(resp_body.keys()):
        record("envelope", True, "non-JSON 2xx — envelope deferred", skipped=True)
        result["ok"] = result["fail"] == 0
        return result

    miss_env = missing_keys(resp_body, ENVELOPE_KEYS)
    record("envelope", not miss_env, f"missing {miss_env}" if miss_env else "code,msg,data present")
    result["ok"] = result["fail"] == 0
    return result


def run_mutating_matrix(base_url: str, timeout: float) -> Tuple[List[Dict[str, Any]], Dict[str, Any], bool, str]:
    server_up, health_detail = server_reachable(base_url, timeout=min(timeout, 3.0))
    routes = collect_inventoried_routes()
    rows: List[Dict[str, Any]] = []
    post_count = 0
    put_count = 0
    skipped_destructive = 0
    skipped_multipart = 0

    for idx, route in enumerate(routes, start=1):
        method, path = parse_route(route)
        if method == "POST":
            post_count += 1
        elif method == "PUT":
            put_count += 1

        if not server_up:
            rows.append(
                {
                    "route": route,
                    "path": path,
                    "probe_path": materialize_mutating_path(path),
                    "asserts": 1,
                    "pass": 0,
                    "fail": 0,
                    "skip": 1,
                    "checks": [{"check": "server", "status": "skip", "detail": "server unreachable"}],
                    "ok": True,
                }
            )
            continue

        skip = mutating_skip_reason(path, method)
        if skip and "multipart" in skip:
            skipped_multipart += 1
        elif skip and "destructive" in skip:
            skipped_destructive += 1

        rows.append(assert_mutating_route(base_url, route, timeout))
        if idx % 25 == 0 or idx == len(routes):
            print(f"  mutating-matrix probed {idx}/{len(routes)}")

    summary = summarize(rows)
    summary["post_routes"] = post_count
    summary["put_routes"] = put_count
    summary["mutating_probed"] = post_count + put_count
    summary["skipped_destructive"] = skipped_destructive
    summary["skipped_multipart"] = skipped_multipart
    summary["skipped_non_mutating"] = sum(
        1 for r in routes if parse_route(r)[0] not in ("POST", "PUT")
    )
    return rows, summary, server_up, health_detail


def write_mutating_matrix_artifacts(
    rows: List[Dict[str, Any]],
    summary: Dict[str, Any],
    base_url: str,
    *,
    server_up: bool,
    health_detail: str,
) -> Tuple[Path, Path]:
    logs_dir = repo_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = logs_dir / f"{MUTATING_MATRIX_ARTIFACT_PREFIX}-mutating-matrix-{ts}.json"
    md_path = logs_dir / f"{MUTATING_MATRIX_ARTIFACT_PREFIX}-mutating-matrix-{ts}.md"

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "disclaimer": MUTATING_MATRIX_DISCLAIMER,
        "python_post_envelope_cites": [
            "VIDEO/_retired_python_video/app/blueprints/algorithm_task.py create_task L144-148",
            "VIDEO/_retired_python_video/app/blueprints/snap.py cleanup_device_storage L889-893",
            "VIDEO/_retired_python_video/app/blueprints/playback.py create_playback",
        ],
        "server_up": server_up,
        "health_detail": health_detail,
        "summary": summary,
        "routes": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# FR-B31 POST/PUT Mutating Envelope Matrix",
        "",
        f"**Generated:** {payload['generated_at']}",
        f"**Base URL:** {base_url}",
        f"**Server up:** {server_up} ({health_detail})",
        f"**Routes:** {summary['endpoint_pass']}/{summary['endpoints']} pass",
        f"**POST inventoried:** {summary.get('post_routes', '—')} | "
        f"**PUT inventoried:** {summary.get('put_routes', '—')}",
        f"**Skipped destructive:** {summary.get('skipped_destructive', '—')} | "
        f"**Skipped multipart:** {summary.get('skipped_multipart', '—')}",
        f"**Asserts:** pass={summary['pass']} fail={summary['fail']} skip={summary['skip']} "
        f"(total={summary['asserts']})",
        "",
        "## Disclaimer",
        "",
        MUTATING_MATRIX_DISCLAIMER,
        "",
        "## Results",
        "",
        "| route | probe_path | http | asserts | pass | fail | skip | ok |",
        "|-------|------------|------|---------|------|------|------|-----|",
    ]
    for row in rows:
        if parse_route(row["route"])[0] not in ("POST", "PUT"):
            continue
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
    latest_json = logs_dir / f"{MUTATING_MATRIX_ARTIFACT_PREFIX}-mutating-matrix-latest.json"
    latest_md = logs_dir / f"{MUTATING_MATRIX_ARTIFACT_PREFIX}-mutating-matrix-latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"artifact: {json_path}")
    print(f"artifact: {md_path}")
    return json_path, md_path


def http_delete_json(base_url: str, path: str, timeout: float = 8.0) -> Tuple[int, Dict[str, Any], str]:
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="DELETE")
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


def materialize_post_sample_body(body: Dict[str, Any], ts: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in body.items():
        if isinstance(value, str):
            out[key] = value.replace("{ts}", ts)
        else:
            out[key] = value
    return out


def keys_match_alternatives(data: Any, alternatives: Sequence[Set[str]]) -> Tuple[bool, List[str]]:
    if not isinstance(data, dict):
        return False, ["data not object"]
    for alt in alternatives:
        miss = missing_keys(data, alt)
        if not miss:
            return True, []
    union_miss: Set[str] = set()
    for alt in alternatives:
        union_miss.update(missing_keys(data, alt))
    return False, sorted(union_miss)


def run_post_cleanup(
    base_url: str,
    cleanup: Dict[str, Any],
    created_id: Any,
    timeout: float,
) -> Dict[str, Any]:
    method = str(cleanup.get("method", "DELETE")).upper()
    path = str(cleanup.get("path_template", "")).format(id=created_id)
    result: Dict[str, Any] = {"method": method, "path": path, "ok": False}
    if method != "DELETE":
        result["detail"] = f"unsupported cleanup method {method}"
        return result
    status, body, _ = http_delete_json(base_url, path, timeout=timeout)
    result["http_status"] = status
    result["code"] = body.get("code") if isinstance(body, dict) else None
    result["ok"] = status < 500 and (body.get("code") in (0, None) if isinstance(body, dict) else False)
    result["detail"] = body.get("msg") or body.get("message") or ""
    return result


def assert_post_keys_sample(
    base_url: str,
    sample: Dict[str, Any],
    timeout: float,
    *,
    ts: str,
) -> Dict[str, Any]:
    method = str(sample.get("method", "POST")).upper()
    path = str(sample["path"])
    body = materialize_post_sample_body(dict(sample.get("body") or {}), ts)
    mode = str(sample.get("mode") or "success_keys")
    result: Dict[str, Any] = {
        "id": sample.get("id"),
        "method": method,
        "path": path,
        "probe_body": body,
        "python_source": sample.get("python_source"),
        "mode": mode,
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

    prerequisite = sample.get("prerequisite")
    if prerequisite:
        pre_method = str(prerequisite.get("method", "GET")).upper()
        pre_path = str(prerequisite["path"])
        if pre_method == "GET":
            pre_status, pre_body, _ = http_get_json(base_url, pre_path, timeout=timeout)
        else:
            pre_status, pre_body, _ = http_post_json(
                base_url, pre_path, prerequisite.get("body") or {}, timeout=timeout
            )
        pre_ok = pre_status < 500 and isinstance(pre_body, dict) and pre_body.get("code") == 0
        result["prerequisite"] = {
            "method": pre_method,
            "path": pre_path,
            "http_status": pre_status,
            "code": pre_body.get("code") if isinstance(pre_body, dict) else None,
            "ok": pre_ok,
        }
        if not pre_ok:
            record("prerequisite", False, "prerequisite failed")
            result["ok"] = False
            return result
        pre_data = pre_body.get("data") if isinstance(pre_body, dict) else None
        body_key = prerequisite.get("body_key")
        data_key = prerequisite.get("data_key", "id")
        if body_key and isinstance(pre_data, dict) and pre_data.get(data_key) is not None:
            body[body_key] = pre_data[data_key]

    if method == "POST":
        http_status, resp_body, _ = http_post_json(base_url, path, body, timeout=timeout)
    elif method == "PUT":
        http_status, resp_body, _ = http_put_json(base_url, path, body, timeout=timeout)
    else:
        record("method", False, f"unsupported method {method}")
        result["ok"] = False
        return result

    result["http_status"] = http_status
    result["business_code"] = resp_body.get("code") if isinstance(resp_body, dict) else None

    record("http_status", http_status < 500, f"HTTP {http_status}")
    if http_status >= 500:
        result["ok"] = False
        return result

    expect_code = sample.get("expect_code")
    if expect_code is not None:
        record("business_code", resp_body.get("code") == expect_code, f"code={resp_body.get('code')!r}")

    if mode == "envelope_only":
        if isinstance(resp_body, dict) and {"code", "msg"} <= set(resp_body.keys()):
            record("envelope_4xx", True, "code,msg present")
        else:
            record("envelope_4xx", True, f"HTTP {http_status} validation (non-envelope ok)")
        result["ok"] = result["fail"] == 0
        return result

    miss_env = missing_keys(resp_body, ENVELOPE_KEYS)
    record("envelope", not miss_env, f"missing {miss_env}" if miss_env else "code,msg,data present")

    data = resp_body.get("data") if isinstance(resp_body, dict) else None
    alternatives = sample.get("data_keys_alternatives")
    data_keys = sample.get("data_keys")
    if alternatives:
        ok, miss = keys_match_alternatives(data, alternatives)
        record(
            "data_keys_alt",
            ok,
            "matched alternative" if ok else f"missing vs all alts: {miss}",
        )
    elif data_keys:
        miss = missing_keys(data, data_keys)
        record("data_keys", not miss, f"missing {miss}" if miss else f"{len(data_keys)} keys ok")

    result["ok"] = result["fail"] == 0

    if result.get("ok") and sample.get("cleanup") and isinstance(data, dict) and data.get("id") is not None:
        cleanup = run_post_cleanup(base_url, sample["cleanup"], data["id"], timeout)
        result["cleanup"] = cleanup
        record("cleanup", cleanup.get("ok", False), cleanup.get("detail") or cleanup.get("path", ""))

    return result


def run_post_keys_matrix(base_url: str, timeout: float) -> Tuple[List[Dict[str, Any]], Dict[str, Any], bool, str]:
    from post_keys_matrix_b33_specs import bind_post_keys_matrix_specs

    server_up, health_detail = server_reachable(base_url, timeout=min(timeout, 3.0))
    samples = bind_post_keys_matrix_specs(sys.modules[__name__])
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    rows: List[Dict[str, Any]] = []

    for idx, sample in enumerate(samples, start=1):
        if not server_up:
            rows.append(
                {
                    "id": sample.get("id"),
                    "path": sample.get("path"),
                    "mode": "server_down",
                    "asserts": 1,
                    "pass": 0,
                    "fail": 0,
                    "skip": 1,
                    "checks": [{"check": "server", "status": "skip", "detail": "server unreachable"}],
                    "ok": True,
                }
            )
            continue
        rows.append(assert_post_keys_sample(base_url, sample, timeout, ts=ts))
        flag = "OK" if rows[-1].get("ok") else "FAIL"
        print(f"  post-keys {sample.get('id')}: {flag}")

    summary = summarize(rows)
    summary["post_samples"] = len(samples)
    summary["success_key_samples"] = sum(1 for s in samples if s.get("mode", "success_keys") != "envelope_only")
    summary["envelope_only_samples"] = sum(1 for s in samples if s.get("mode") == "envelope_only")
    summary["key_assert_pass"] = sum(
        1
        for row in rows
        for check in row.get("checks", [])
        if check["check"] in ("data_keys", "data_keys_alt") and check["status"] == "pass"
    )
    summary["key_assert_fail"] = sum(
        1
        for row in rows
        for check in row.get("checks", [])
        if check["check"] in ("data_keys", "data_keys_alt") and check["status"] == "fail"
    )
    return rows, summary, server_up, health_detail, samples


def write_post_keys_matrix_artifacts(
    rows: List[Dict[str, Any]],
    summary: Dict[str, Any],
    base_url: str,
    samples: List[Dict[str, Any]],
    *,
    server_up: bool,
    health_detail: str,
) -> Tuple[Path, Path]:
    logs_dir = repo_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = logs_dir / f"{POST_KEYS_MATRIX_ARTIFACT_PREFIX}-post-keys-matrix-{ts}.json"
    md_path = logs_dir / f"{POST_KEYS_MATRIX_ARTIFACT_PREFIX}-post-keys-matrix-{ts}.md"

    mapping_table = [
        {
            "id": s.get("id"),
            "path": s.get("path"),
            "python_source": s.get("python_source"),
            "mode": s.get("mode", "success_keys"),
            "data_keys_count": len(s["data_keys"]) if s.get("data_keys") else None,
            "data_keys_alternatives": len(s.get("data_keys_alternatives") or []),
        }
        for s in samples
    ]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "disclaimer": POST_KEYS_MATRIX_DISCLAIMER,
        "server_up": server_up,
        "health_detail": health_detail,
        "summary": summary,
        "mapping_table": mapping_table,
        "samples": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# FR-B33 POST Keys Matrix — Python-first success body keys",
        "",
        f"**Generated:** {payload['generated_at']}",
        f"**Base URL:** {base_url}",
        f"**Server up:** {server_up} ({health_detail})",
        f"**Samples:** {summary['endpoint_pass']}/{summary['endpoints']} pass "
        f"(POST probes={summary.get('post_samples', '—')})",
        f"**Key asserts:** pass={summary.get('key_assert_pass', 0)} fail={summary.get('key_assert_fail', 0)}",
        f"**Asserts:** pass={summary['pass']} fail={summary['fail']} skip={summary['skip']} "
        f"(total={summary['asserts']})",
        "",
        "## Disclaimer",
        "",
        POST_KEYS_MATRIX_DISCLAIMER,
        "",
        "## Python-first mapping",
        "",
        "| id | path | mode | python_source |",
        "|----|------|------|---------------|",
    ]
    for row in mapping_table:
        src = row["python_source"] or ""
        src_cell = f"{src[:70]}…" if len(src) > 70 else src
        lines.append(f"| {row['id']} | `{row['path']}` | {row['mode']} | {src_cell} |")
    lines.extend(
        [
            "",
            "## Results",
            "",
            "| id | path | http | code | key_assert | ok |",
            "|----|------|------|------|------------|-----|",
        ]
    )
    for row in rows:
        key_checks = [
            c for c in row.get("checks", []) if c["check"] in ("data_keys", "data_keys_alt", "envelope_4xx")
        ]
        key_status = key_checks[0]["status"] if key_checks else "—"
        lines.append(
            f"| {row.get('id')} | `{row.get('path', '')}` | {row.get('http_status', '—')} | "
            f"{row.get('business_code', '—')} | {key_status} | {row.get('ok')} |"
        )
    lines.append("")
    fails = [r for r in rows if not r.get("ok")]
    if fails:
        lines.extend(["## Failures", ""])
        for row in fails:
            lines.append(f"### {row.get('id')}")
            for check in row.get("checks", []):
                if check["status"] == "fail":
                    lines.append(f"- **{check['check']}**: {check['detail']}")
            lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    latest_json = logs_dir / f"{POST_KEYS_MATRIX_ARTIFACT_PREFIX}-post-keys-matrix-latest.json"
    latest_md = logs_dir / f"{POST_KEYS_MATRIX_ARTIFACT_PREFIX}-post-keys-matrix-latest.md"
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


def http_put_json(
    base_url: str, path: str, payload: Dict[str, Any], timeout: float = 8.0
) -> Tuple[int, Dict[str, Any], str]:
    url = base_url.rstrip("/") + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="PUT",
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


def run_b29_seed_setups(base_url: str, timeout: float) -> List[Dict[str, Any]]:
    """Run FR-B29 deferred item-key seed steps (location, NVR, track session, matching)."""
    results: List[Dict[str, Any]] = []
    try:
        from seed_fr_b29_keys_matrix import run_all

        payload = run_all()
        for step in payload.get("steps", []):
            results.append({"case_id": f"b29_{step.get('step')}", **step})
            flag = "OK" if step.get("ok") else "FAIL"
            print(f"  b29-seed {step.get('step')}: {flag}")
    except Exception as exc:
        results.append({"case_id": "b29_seed", "ok": False, "detail": str(exc)})
        print(f"  b29-seed: FAIL ({exc})")
    return results


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
    elif method == "PUT":
        status, body_resp, _ = http_put_json(base_url, str(setup["path"]), body, timeout=timeout)
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
    if case.get("flat_envelope"):
        flat_keys = {"code", "msg"}
        miss_flat = missing_keys(body, flat_keys)
        record(
            "envelope",
            not miss_flat,
            "flat code,msg present" if not miss_flat else f"missing {miss_flat}",
        )
    else:
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
        check_name = "nested_list_item_keys" if "data" in list_path else "flat_list_item_keys"
        if items:
            miss = missing_keys(items[0], item_keys)
            record(
                check_name,
                not miss,
                f"missing {miss}" if miss else f"{len(item_keys)} keys on first item",
            )
        else:
            record(check_name, True, "empty list — item keys deferred", skipped=True)

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
        "--keys-matrix",
        action="store_true",
        help="FR-B28 GET keys matrix: envelope + Python-mapped item keys on all inventoried GET JSON routes",
    )
    parser.add_argument(
        "--mutating-matrix",
        action="store_true",
        help="FR-B31 POST/PUT mutating envelope matrix: thin probes on inventoried safe mutating routes",
    )
    parser.add_argument(
        "--post-keys-matrix",
        action="store_true",
        help="FR-B33 POST keys matrix: Python-first success body key asserts on curated POST creates",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="run FR-B22 hand-curated deep field samples (default when no mode flag)",
    )
    args = parser.parse_args(argv)

    run_deep = args.deep or not (
        args.matrix or args.keys_matrix or args.mutating_matrix or args.post_keys_matrix
    )
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

    if args.keys_matrix:
        route_count = len(collect_inventoried_routes())
        specs = build_route_key_specs()
        print(f"\nGET keys-matrix base_url={args.base_url} inventoried_routes={route_count}")
        km_rows, km_summary, server_up, health_detail, setups = run_keys_matrix(args.base_url, args.timeout)
        print(
            f"keys-matrix: {km_summary['endpoint_pass']}/{km_summary['endpoints']} pass | "
            f"mapped={km_summary.get('mapped_routes')} envelope_only={km_summary.get('envelope_only_routes')} | "
            f"key_asserts: pass={km_summary.get('key_assert_pass')} fail={km_summary.get('key_assert_fail')} | "
            f"asserts: pass={km_summary['pass']} fail={km_summary['fail']} skip={km_summary['skip']} "
            f"server_up={server_up}"
        )
        write_keys_matrix_artifacts(
            km_rows,
            km_summary,
            args.base_url,
            specs,
            setups,
            server_up=server_up,
            health_detail=health_detail,
        )
        print(f"\n{KEYS_MATRIX_DISCLAIMER}")
        if km_summary["fail"] != 0:
            exit_code = 1

    if args.mutating_matrix:
        route_count = len(collect_inventoried_routes())
        print(f"\nPOST/PUT mutating-matrix base_url={args.base_url} inventoried_routes={route_count}")
        mm_rows, mm_summary, server_up, health_detail = run_mutating_matrix(args.base_url, args.timeout)
        print(
            f"mutating-matrix: {mm_summary['endpoint_pass']}/{mm_summary['endpoints']} pass | "
            f"POST={mm_summary.get('post_routes')} PUT={mm_summary.get('put_routes')} | "
            f"skipped destructive={mm_summary.get('skipped_destructive')} "
            f"multipart={mm_summary.get('skipped_multipart')} | "
            f"asserts: pass={mm_summary['pass']} fail={mm_summary['fail']} skip={mm_summary['skip']} "
            f"server_up={server_up}"
        )
        write_mutating_matrix_artifacts(
            mm_rows, mm_summary, args.base_url, server_up=server_up, health_detail=health_detail
        )
        print(f"\n{MUTATING_MATRIX_DISCLAIMER}")
        if mm_summary["fail"] != 0:
            exit_code = 1

    if args.post_keys_matrix:
        print(f"\nPOST keys-matrix base_url={args.base_url}")
        pk_rows, pk_summary, server_up, health_detail, pk_samples = run_post_keys_matrix(
            args.base_url, args.timeout
        )
        print(
            f"post-keys-matrix: {pk_summary['endpoint_pass']}/{pk_summary['endpoints']} pass | "
            f"samples={pk_summary.get('post_samples')} "
            f"success_keys={pk_summary.get('success_key_samples')} "
            f"envelope_only={pk_summary.get('envelope_only_samples')} | "
            f"key_asserts: pass={pk_summary.get('key_assert_pass')} "
            f"fail={pk_summary.get('key_assert_fail')} | "
            f"asserts: pass={pk_summary['pass']} fail={pk_summary['fail']} skip={pk_summary['skip']} "
            f"server_up={server_up}"
        )
        write_post_keys_matrix_artifacts(
            pk_rows,
            pk_summary,
            args.base_url,
            pk_samples,
            server_up=server_up,
            health_detail=health_detail,
        )
        print(f"\n{POST_KEYS_MATRIX_DISCLAIMER}")
        if pk_summary["fail"] != 0:
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
