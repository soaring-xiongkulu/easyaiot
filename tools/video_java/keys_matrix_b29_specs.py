"""FR-B29 Python-first keys-matrix mappings (read from oracle blueprints / to_dict)."""

from __future__ import annotations

from typing import Any, Dict, Set

# Re-use item key sets from field_contract via late import in build function, or duplicate minimal refs.
# Keys below are cited from VIDEO/_retired_python_video — do not invent.

# alert_service.py get_correlation_events L364-369
ALERT_CORRELATION_KEYS: Set[str] = {
    "correlation_id",
    "alerts",
    "face_match_records",
    "plate_match_records",
}

# algorithm_task.py get_service_logs data L734-739
SERVICE_LOG_DATA_KEYS: Set[str] = {
    "logs",
    "total_lines",
    "log_file",
    "is_all_file",
}

# algorithm_task.py get_task_services_status result L392-398
ALGO_SERVICES_STATUS_KEYS: Set[str] = {
    "realtime_service",
    "snap_service",
    "patrol_service",
    "extractor",
    "sorter",
    "pusher",
}

# algorithm_task.py get_task_streams stream_info L682-686
ALGO_STREAM_ITEM_KEYS: Set[str] = {
    "device_id",
    "device_name",
    "http_stream",
    "rtmp_stream",
}

# post_process_service.py get_post_process_status L219-228
POST_PROCESS_STATUS_KEYS: Set[str] = {
    "task_id",
    "post_process_enabled",
    "post_process_script",
    "post_process_replicas",
    "script_exists",
    "workspace_path",
    "ide_url",
    "workspace_root",
}

# algorithm_task.py get_post_process_ide_url data L826-830
POST_PROCESS_IDE_KEYS: Set[str] = {
    "ide_url",
    "task_id",
    "task_name",
}

# post_process_result_service.py list_post_process_results L41-46 (top-level on response)
POST_PROCESS_RESULTS_TOP_KEYS: Set[str] = {
    "items",
    "total",
    "page_no",
    "page_size",
}

# camera_service.py get_device_location_info L1448-1453 + _location_fields_for_device L75-84
DEVICE_LOCATION_KEYS: Set[str] = {
    "id",
    "name",
    "device_kind",
    "longitude",
    "latitude",
    "altitude",
    "address",
    "heading",
    "location_source",
    "location_updated_at",
    "has_location",
}

# camera_service.py resolve_device_inference_input L1480-1488
INFERENCE_INPUT_KEYS: Set[str] = {
    "device_id",
    "source",
    "rtsp_direct",
    "rtmp_stream",
    "http_stream",
    "resolved_source",
    "is_gb28181",
}

# camera.py get_stream_status data L545-548
STREAM_STATUS_KEYS: Set[str] = {"status", "pid", "start_time", "rtmp_url"}

# camera.py rtsp_status / onvif_status data
SIMPLE_STATUS_KEYS: Set[str] = {"status"}

# flighthub_source.py get_flighthub_public_config L187-199
FLIGHTHUB_CONFIG_KEYS: Set[str] = {
    "allowed_ips",
    "workspace_id",
    "workspace_name",
    "platform_name",
    "platform_host",
    "openapi_host",
    "live_start_path",
    "mqtt_enabled",
    "mqtt_broker_uri",
    "mqtt_client_id",
    "mqtt_username",
}

# models.py DeviceTrackPoint.to_dict L212-228
TRACK_POINT_ITEM_KEYS: Set[str] = {
    "id",
    "device_id",
    "session_id",
    "recorded_at",
    "longitude",
    "latitude",
    "altitude",
    "speed",
    "direction",
    "accuracy_m",
    "source",
    "report_source",
    "external_key",
    "created_at",
}

# camera.py get_device_conflicts — data is list[str] device ids (no object keys)

# camera.py get_directory_info data L3079+
DIRECTORY_DETAIL_KEYS: Set[str] = {
    "id",
    "name",
    "parent_id",
    "description",
    "sort_order",
    "device_count",
    "children_count",
}

# camera.py directory/{id}/devices — list of device ids
DIRECTORY_DEVICES_KEYS: Set[str] = {"device_ids", "total"}

# models.py FacePerson.to_dict L1292-1304
FACE_PERSON_KEYS: Set[str] = {
    "id",
    "library_id",
    "person_name",
    "person_code",
    "cover_entry_id",
    "cover_image_url",
    "is_enabled",
    "face_count",
    "created_at",
    "updated_at",
}

# models.py FaceEntry.to_dict L1327-1341
FACE_ENTRY_ITEM_KEYS: Set[str] = {
    "id",
    "library_id",
    "person_id",
    "person_name",
    "person_code",
    "image_path",
    "image_url",
    "milvus_id",
    "remark",
    "is_enabled",
    "created_at",
    "updated_at",
}

# models.py FaceAutoEnrollTask.to_dict L1381+
FACE_AUTO_ENROLL_KEYS: Set[str] = {
    "id",
    "library_id",
    "device_ids",
    "device_names",
    "duration_minutes",
    "capture_interval_sec",
    "person_name_prefix",
    "is_running",
    "started_at",
    "expires_at",
    "enrolled_count",
    "skipped_count",
    "last_device_index",
    "last_tick_at",
    "created_at",
    "updated_at",
}

# models.py PlateEntry — mirror FaceEntry (plate.py list entries)
PLATE_ENTRY_ITEM_KEYS: Set[str] = {
    "id",
    "library_id",
    "plate_no",
    "plate_color",
    "owner_name",
    "owner_phone",
    "image_path",
    "image_url",
    "remark",
    "is_enabled",
    "created_at",
    "updated_at",
}

# models.py ScenarioPoseEntry.to_dict L1735+
SCENARIO_POSE_ENTRY_ITEM_KEYS: Set[str] = {
    "id",
    "library_id",
    "name",
    "source_type",
    "image_path",
    "image_url",
    "keypoints",
    "feature_vector",
    "keypoint_visibility_min",
    "extra_rules",
    "remark",
    "is_enabled",
    "created_at",
    "updated_at",
}

# models.py PatrolSession.to_dict L2304-2331
PATROL_SESSION_KEYS: Set[str] = {
    "id",
    "session_name",
    "patrol_mode",
    "interval_sec",
    "pool_size",
    "device_ids",
    "device_names",
    "model_ids",
    "focus_device_id",
    "algorithm_task_id",
    "alert_event_enabled",
    "alert_event_suppress_time",
    "face_detection_enabled",
    "plate_detection_enabled",
    "status",
    "exception_reason",
    "service_server_ip",
    "service_process_id",
    "service_last_heartbeat",
    "service_log_path",
    "progress",
    "total_patrols",
    "total_detections",
    "last_patrol_time",
    "created_at",
    "updated_at",
}

# patrol.py session_stats — cite handler return keys when session exists
PATROL_SESSION_STATS_KEYS: Set[str] = {
    "session_id",
    "status",
    "total_patrols",
    "total_detections",
    "device_count",
    "progress",
}

# record.py resolve-alert, videos/dates, videos/day — cite record blueprint handlers
RESOLVE_ALERT_KEYS: Set[str] = {
    "device_id",
    "space_id",
    "space_name",
    "alert_time",
    "matched_videos",
}

RECORD_VIDEO_DATES_KEYS: Set[str] = {"dates", "total"}

RECORD_VIDEO_DAY_ITEM_KEYS: Set[str] = {
    "id",
    "object_name",
    "filename",
    "size",
    "last_modified",
    "duration",
    "thumbnail_url",
    "url",
}

# snap.py region / storage / images
SNAP_REGION_KEYS: Set[str] = {
    "id",
    "task_id",
    "region_name",
    "region_type",
    "points",
    "image_id",
    "image_path",
    "algorithm_type",
    "algorithm_model_id",
    "algorithm_threshold",
    "algorithm_enabled",
    "color",
    "opacity",
    "is_enabled",
    "sort_order",
    "services",
    "created_at",
    "updated_at",
}

SNAP_DEVICE_STORAGE_KEYS: Set[str] = {
    "id",
    "device_id",
    "snap_storage_bucket",
    "snap_storage_max_size",
    "snap_storage_cleanup_enabled",
    "snap_storage_cleanup_threshold",
    "snap_storage_cleanup_ratio",
    "video_storage_bucket",
    "video_storage_max_size",
    "video_storage_cleanup_enabled",
    "video_storage_cleanup_threshold",
    "video_storage_cleanup_ratio",
    "snap_size",
    "snap_count",
    "snap_usage_ratio",
    "video_size",
    "video_count",
    "video_usage_ratio",
}

# stream_forward.py get_task_streams stream_info L408-415
SF_STREAM_ITEM_KEYS: Set[str] = {
    "device_id",
    "device_name",
    "rtmp_stream",
    "http_stream",
    "source",
    "cover_image_path",
}

# face_library_service.preview_normalize_groups group item L665-674
NORMALIZE_GROUP_ITEM_KEYS: Set[str] = {
    "group_id",
    "count",
    "entry_count",
    "person_count",
    "suggested_target_person_id",
    "suggested_target_entry_id",
    "persons",
    "entries",
}

# face_vector_store.list_faces output_fields L152
LEGACY_FACE_LIBRARY_ITEM_KEYS: Set[str] = {
    "id",
    "label",
    "library_id",
    "face_entry_id",
    "person_name",
}

# record_video_service.list_record_videos_day_detail return L670-683
RECORD_DAY_DETAIL_KEYS: Set[str] = {
    "date",
    "device_id",
    "space_id",
    "segments",
    "timeline",
    "timeline_merged",
    "session_groups",
    "total_segments",
    "total_sessions",
    "total_duration_sec",
    "alert_segment_count",
    "total_alert_count",
    "alerts",
}

# scenario_pose_library_service.list_scene_templates / pose_intent.SCENE_TEMPLATES
SCENE_TEMPLATE_ITEM_KEYS: Set[str] = {
    "key",
    "name",
    "scene_category",
    "intent_event",
    "intent_object",
    "match_mode",
    "similarity_threshold",
    "extra_rules",
}

_PY = "VIDEO/_retired_python_video"
_ALGO = f"{_PY}/app/blueprints/algorithm_task.py"
_CAM = f"{_PY}/app/blueprints/camera.py"
_ALERT = f"{_PY}/app/blueprints/alert.py"
_FACE = f"{_PY}/app/blueprints/face.py"
_PLATE = f"{_PY}/app/blueprints/plate.py"
_PATROL = f"{_PY}/app/blueprints/patrol.py"
_RECORD = f"{_PY}/app/blueprints/record.py"
_SNAP = f"{_PY}/app/blueprints/snap.py"
_SF = f"{_PY}/app/blueprints/stream_forward.py"
_POSE = f"{_PY}/app/blueprints/scenario_pose.py"
_MODELS = f"{_PY}/models.py"

# Placeholders — patched in bind_field_contract_keys() from field_contract constants.
_CAM_DIR_ITEM_KEYS: Set[str] = set()
_CAM_DEVICE_ITEM_KEYS: Set[str] = set()
_NVR_ITEM_KEYS: Set[str] = set()
_FACE_LIB_ITEM_KEYS: Set[str] = set()
_RECORD_VIDEO_ITEM_KEYS: Set[str] = set()
_SNAP_SPACE_ITEM_KEYS: Set[str] = set()
_SNAP_IMAGE_ITEM_KEYS: Set[str] = set()

B29_EXTRA_ROUTE_KEY_SPECS: Dict[str, Dict[str, Any]] = {
    "/video/alert/correlation": {
        "id": "alert_correlation",
        "python_source": f"{_ALERT} get_correlation_events_route → alert_service.get_correlation_events",
        "data_keys": ALERT_CORRELATION_KEYS,
    },
    "/video/alert/record/query": {
        "id": "alert_record_query",
        "python_source": f"{_ALERT} query_alert_record → alert_service.resolve_alert_record_video / _record_path_playback_payload",
        "data_keys": {
            "video_url",
            "file_path",
            "device_id",
            "device_name",
            "source",
            "playback_id",
            "event_time",
            "duration",
        },
    },
    "/video/algorithm/task/{param}/extractor/logs": {
        "id": "algo_task_extractor_logs",
        "python_source": f"{_ALGO} get_task_extractor_logs → get_service_logs data",
        "data_keys": SERVICE_LOG_DATA_KEYS,
    },
    "/video/algorithm/task/{param}/sorter/logs": {
        "id": "algo_task_sorter_logs",
        "python_source": f"{_ALGO} get_task_sorter_logs → get_service_logs data",
        "data_keys": SERVICE_LOG_DATA_KEYS,
    },
    "/video/algorithm/task/{param}/pusher/logs": {
        "id": "algo_task_pusher_logs",
        "python_source": f"{_ALGO} get_task_pusher_logs → get_service_logs data",
        "data_keys": SERVICE_LOG_DATA_KEYS,
    },
    "/video/algorithm/task/{param}/realtime/logs": {
        "id": "algo_task_realtime_logs",
        "python_source": f"{_ALGO} get_task_realtime_logs → get_service_logs data",
        "data_keys": SERVICE_LOG_DATA_KEYS,
    },
    "/video/algorithm/task/{param}/services/status": {
        "id": "algo_task_services_status",
        "python_source": f"{_ALGO} get_task_services_status result",
        "data_keys": ALGO_SERVICES_STATUS_KEYS,
    },
    "/video/algorithm/task/{param}/streams": {
        "id": "algo_task_streams",
        "python_source": f"{_ALGO} get_task_streams stream_info",
        "data_list": True,
        "list_item_keys": ALGO_STREAM_ITEM_KEYS,
    },
    "/video/algorithm/task/{param}/post-process/status": {
        "id": "algo_post_process_status",
        "python_source": f"{_PY}/app/services/post_process_service.py get_post_process_status",
        "data_keys": POST_PROCESS_STATUS_KEYS,
    },
    "/video/algorithm/task/{param}/post-process/ide-url": {
        "id": "algo_post_process_ide_url",
        "python_source": f"{_ALGO} get_post_process_ide_url data",
        "data_keys": POST_PROCESS_IDE_KEYS,
    },
    "/video/algorithm/task/{param}/post-process/results": {
        "id": "algo_post_process_results",
        "python_source": f"{_PY}/app/services/post_process_result_service.py list_post_process_results",
        "data_keys": POST_PROCESS_RESULTS_TOP_KEYS,
    },
    "/video/camera/audio/talk/capabilities": {
        "id": "audio_talk_capabilities",
        "python_source": f"{_PY}/app/blueprints/audio_talk.py get_capabilities data",
        "data_keys": {"success", "capabilities"},
    },
    "/video/camera/device/conflicts": {
        "id": "camera_conflicts",
        "python_source": f"{_CAM} get_device_conflicts — data list[device_id]",
        "data_list": True,
    },
    "/video/camera/device/{param}/inference-input": {
        "id": "camera_inference_input",
        "python_source": f"{_CAM} get_device_inference_input → camera_service.resolve_device_inference_input",
        "data_keys": INFERENCE_INPUT_KEYS,
    },
    "/video/camera/device/{param}/location": {
        "id": "camera_device_location",
        "python_source": f"{_CAM} get_device_location_route → camera_service.get_device_location_info",
        "data_keys": DEVICE_LOCATION_KEYS,
    },
    "/video/camera/device/{param}/onvif/presets": {
        "id": "camera_onvif_presets",
        "python_source": f"{_CAM} list_onvif_presets",
        "data_list": True,
        "list_item_keys": {"token", "name"},  # onvif_service.py list_presets L128
    },
    "/video/camera/device/{param}/onvif/status": {
        "id": "camera_onvif_status",
        "python_source": f"{_CAM} onvif_status",
        "data_keys": SIMPLE_STATUS_KEYS,
    },
    "/video/camera/device/{param}/rtsp/status": {
        "id": "camera_rtsp_status",
        "python_source": f"{_CAM} rtsp_status",
        "data_keys": SIMPLE_STATUS_KEYS,
    },
    "/video/camera/device/{param}/stream/status": {
        "id": "camera_stream_status",
        "python_source": f"{_CAM} get_stream_status",
        "data_keys": STREAM_STATUS_KEYS,
    },
    "/video/camera/directory/monitor-tree": {
        "id": "camera_directory_monitor_tree",
        "python_source": f"{_CAM} get_directory_monitor_tree data.tree + unassigned_devices",
        "data_keys": {"tree", "unassigned_devices"},
    },
    "/video/camera/directory/{param}": {
        "id": "camera_directory_get",
        "python_source": f"{_CAM} get_directory_info",
        "data_keys": DIRECTORY_DETAIL_KEYS,
    },
    "/video/camera/directory/{param}/devices": {
        "id": "camera_directory_devices",
        "python_source": f"{_CAM} list_directory_devices — data list + top total",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": _CAM_DEVICE_ITEM_KEYS,
    },
    "/video/camera/discovery": {
        "id": "camera_discovery",
        "python_source": f"{_CAM} discover_devices",
        "data_list": True,
        "list_item_keys": {"mac", "ip", "hardware_name"},  # camera_service._discovery_cameras L684-688
    },
    "/video/camera/flighthub/config": {
        "id": "camera_flighthub_config",
        "python_source": f"{_PY}/app/utils/flighthub_source.py get_flighthub_public_config",
        "data_keys": FLIGHTHUB_CONFIG_KEYS,
    },
    "/video/camera/nvr/{param}": {
        "id": "camera_nvr_get",
        "python_source": f"{_PY}/app/services/nvr_service.py get_nvr / _nvr_to_dict",
        "data_keys": _NVR_ITEM_KEYS,
    },
    "/video/camera/tracks/points": {
        "id": "camera_tracks_points",
        "python_source": f"{_MODELS} DeviceTrackPoint.to_dict + camera.py list_device_track_points",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": TRACK_POINT_ITEM_KEYS,
    },
    "/video/face/libraries/{param}/auto-enroll": {
        "id": "face_auto_enroll_get",
        "python_source": f"{_MODELS} FaceAutoEnrollTask.to_dict + face.py get_auto_enroll",
        "data_keys": FACE_AUTO_ENROLL_KEYS,
    },
    "/video/face/libraries/{param}/entries": {
        "id": "face_library_entries",
        "python_source": f"{_MODELS} FaceEntry.to_dict + face.py list_entries",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": FACE_ENTRY_ITEM_KEYS,
    },
    "/video/face/libraries/{param}/normalize/preview": {
        "id": "face_normalize_preview",
        "python_source": f"{_FACE} preview_face_normalize — data groups list + top total",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": NORMALIZE_GROUP_ITEM_KEYS,
    },
    "/video/face/libraries/{param}/persons": {
        "id": "face_library_persons",
        "python_source": f"{_FACE} list_face_persons — jsonify(code,msg,**data) top-level pagination",
        "data_list": True,
        "top_keys": {"total", "page", "page_size"},
        "list_item_keys": FACE_PERSON_KEYS,
    },
    "/video/face/library": {
        "id": "face_library_legacy_list",
        "python_source": f"{_FACE} list_library → face_vector_store.list_faces",
        "data_list": True,
        "list_item_keys": LEGACY_FACE_LIBRARY_ITEM_KEYS,
    },
    "/video/face/persons/{param}": {
        "id": "face_person_get",
        "python_source": f"{_MODELS} FacePerson.to_dict + face.py get_face_person",
        "data_keys": FACE_PERSON_KEYS,
    },
    "/video/patrol/session/{param}": {
        "id": "patrol_session_get",
        "python_source": f"{_MODELS} PatrolSession.to_dict + patrol.py get_session",
        "data_keys": PATROL_SESSION_KEYS,
    },
    "/video/patrol/session/{param}/stats": {
        "id": "patrol_session_stats",
        "python_source": f"{_PATROL} session_stats",
        "data_keys": PATROL_SESSION_STATS_KEYS,
    },
    "/video/plate/libraries/{param}/auto-enroll": {
        "id": "plate_auto_enroll_get",
        "python_source": f"{_PLATE} get_plate_auto_enroll",
        "data_keys": FACE_AUTO_ENROLL_KEYS,
    },
    "/video/plate/libraries/{param}/entries": {
        "id": "plate_library_entries",
        "python_source": f"{_PLATE} list_plate_entries — jsonify(code,msg,**data)",
        "data_list": True,
        "top_keys": {"total", "page", "page_size"},
        "list_item_keys": PLATE_ENTRY_ITEM_KEYS,
    },
    "/video/plate/libraries/{param}/normalize/preview": {
        "id": "plate_normalize_preview",
        "python_source": f"{_PLATE} preview_plate_normalize — data groups list + top total",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": NORMALIZE_GROUP_ITEM_KEYS,
    },
    "/video/record/space/device/{param}/resolve-alert": {
        "id": "record_resolve_alert",
        "python_source": f"{_RECORD} resolve_alert_video",
        "data_keys": RESOLVE_ALERT_KEYS,
    },
    "/video/record/space/{param}/videos": {
        "id": "record_videos_list_unmapped",
        "python_source": f"{_MODELS} RecordFile.to_list_item + record.py list_videos",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": _RECORD_VIDEO_ITEM_KEYS,
    },
    "/video/record/space/{param}/videos/dates": {
        "id": "record_videos_dates",
        "python_source": f"{_RECORD} list_video_dates — data is date string list",
        "data_list": True,
    },
    "/video/record/space/{param}/videos/day": {
        "id": "record_videos_day",
        "python_source": f"{_RECORD} list_videos_by_day — data object from list_record_videos_day_detail",
        "data_keys": RECORD_DAY_DETAIL_KEYS,
    },
    "/video/scenario-pose/libraries/{param}/entries": {
        "id": "scenario_pose_library_entries",
        "python_source": f"{_MODELS} ScenarioPoseEntry.to_dict + scenario_pose.py list_entries",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": SCENARIO_POSE_ENTRY_ITEM_KEYS,
    },
    "/video/scenario-pose/scene-templates": {
        "id": "scenario_pose_scene_templates",
        "python_source": f"{_POSE} list_scene_templates → key + SCENE_TEMPLATES fields",
        "data_list": True,
        "list_item_keys": SCENE_TEMPLATE_ITEM_KEYS,
    },
    "/video/snap/device/{param}/storage": {
        "id": "snap_device_storage",
        "python_source": f"{_SNAP} get_device_storage",
        "data_keys": SNAP_DEVICE_STORAGE_KEYS,
    },
    "/video/snap/region/{param}": {
        "id": "snap_region_get",
        "python_source": f"{_MODELS} SnapRegion.to_dict + snap.py get_region",
        "data_keys": SNAP_REGION_KEYS,
    },
    "/video/snap/region/{param}/services": {
        "id": "snap_region_services",
        "python_source": f"{_MODELS} SnapRegionService.to_dict + snap.py list_region_services",
        "data_list": True,
        "list_item_keys": {"id", "region_id", "service_name", "service_type", "status", "is_enabled"},
    },
    "/video/snap/space/device/{param}": {
        "id": "snap_space_by_device",
        "python_source": f"{_MODELS} SnapSpace.to_dict + snap.py get_space_by_device",
        "data_keys": _SNAP_SPACE_ITEM_KEYS,
    },
    "/video/snap/space/{param}/images": {
        "id": "snap_space_images",
        "python_source": f"{_MODELS} SnapImage.to_list_item + snap.py list_images",
        "data_list": True,
        "top_keys": {"total"},
        "list_item_keys": _SNAP_IMAGE_ITEM_KEYS,
    },
    "/video/snap/task/{param}/logs": {
        "id": "snap_task_logs",
        "python_source": f"{_SNAP} get_task_logs → get_service_logs data",
        "data_keys": SERVICE_LOG_DATA_KEYS,
    },
    "/video/snap/task/{param}/regions": {
        "id": "snap_task_regions",
        "python_source": f"{_MODELS} SnapRegion.to_dict + snap.py list_task_regions",
        "data_list": True,
        "list_item_keys": SNAP_REGION_KEYS,
    },
    "/video/snap/task/{param}/services": {
        "id": "snap_task_services",
        "python_source": f"{_MODELS} SnapRegionService.to_dict + snap.py list_task_services",
        "data_list": True,
        "list_item_keys": {"id", "region_id", "service_name", "service_type", "status", "is_enabled"},
    },
    "/video/stream-forward/task/{param}/logs": {
        "id": "sf_task_logs",
        "python_source": f"{_SF} get_task_logs → get_service_logs data",
        "data_keys": SERVICE_LOG_DATA_KEYS,
    },
    "/video/stream-forward/task/{param}/streams": {
        "id": "sf_task_streams",
        "python_source": f"{_SF} get_task_streams",
        "data_list": True,
        "list_item_keys": SF_STREAM_ITEM_KEYS,
    },
}


def bind_field_contract_keys(fc: Any) -> None:
    """Bind shared key sets from field_contract after import."""
    global _CAM_DIR_ITEM_KEYS, _NVR_ITEM_KEYS, _FACE_LIB_ITEM_KEYS
    global _RECORD_VIDEO_ITEM_KEYS, _SNAP_SPACE_ITEM_KEYS, _SNAP_IMAGE_ITEM_KEYS, _CAM_DEVICE_ITEM_KEYS
    _CAM_DIR_ITEM_KEYS = fc.CAMERA_DIRECTORY_ITEM_KEYS
    _CAM_DEVICE_ITEM_KEYS = fc.CAMERA_DEVICE_KEYS
    _NVR_ITEM_KEYS = fc.NVR_ITEM_KEYS
    _FACE_LIB_ITEM_KEYS = fc.FACE_LIBRARY_ITEM_KEYS
    _RECORD_VIDEO_ITEM_KEYS = fc.RECORD_VIDEO_ITEM_KEYS
    _SNAP_SPACE_ITEM_KEYS = fc.SNAP_SPACE_ITEM_KEYS
    _SNAP_IMAGE_ITEM_KEYS = fc.SNAP_IMAGE_ITEM_KEYS
    B29_EXTRA_ROUTE_KEY_SPECS["/video/camera/directory/{param}/devices"]["list_item_keys"] = _CAM_DEVICE_ITEM_KEYS
    B29_EXTRA_ROUTE_KEY_SPECS["/video/camera/nvr/{param}"]["data_keys"] = _NVR_ITEM_KEYS
    B29_EXTRA_ROUTE_KEY_SPECS["/video/record/space/{param}/videos"]["list_item_keys"] = _RECORD_VIDEO_ITEM_KEYS
    B29_EXTRA_ROUTE_KEY_SPECS["/video/snap/space/device/{param}"]["data_keys"] = _SNAP_SPACE_ITEM_KEYS
    B29_EXTRA_ROUTE_KEY_SPECS["/video/snap/space/{param}/images"]["list_item_keys"] = _SNAP_IMAGE_ITEM_KEYS
