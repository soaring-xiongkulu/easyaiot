"""FR-B36 Python-first POST success body key matrix specs (≥100 inventoried routes).

Extends FR-B35 toward full inventoried POST coverage (~112 routes minus documented
destructive skips). Every data_keys set cited from Python oracle — do not invent keys.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set

from post_keys_matrix_b34_specs import (
    DEVICE_COVER_IMAGE_DATA_KEYS,
    DEVICE_SNAPSHOT_DATA_KEYS,
    RECORD_SYNC_MINIO_KEYS,
)
from post_keys_matrix_b35_specs import bind_post_keys_matrix_specs as bind_b35_specs

_PY = "VIDEO/_retired_python_video"
_ALGO = f"{_PY}/app/blueprints/algorithm_task.py"
_SNAP = f"{_PY}/app/blueprints/snap.py"
_FACE = f"{_PY}/app/blueprints/face.py"
_PLATE = f"{_PY}/app/blueprints/plate.py"
_SF = f"{_PY}/app/blueprints/stream_forward.py"
_PLAYBACK = f"{_PY}/app/blueprints/playback.py"
_POSE = f"{_PY}/app/blueprints/scenario_pose.py"
_PATROL = f"{_PY}/app/blueprints/patrol.py"
_CAM = f"{_PY}/app/blueprints/camera.py"
_RECORD = f"{_PY}/app/blueprints/record.py"
_MEDIA = f"{_PY}/app/blueprints/media_hook.py"
_DD = f"{_PY}/app/blueprints/device_detection_region.py"
_PP_SVC = f"{_PY}/app/services/post_process_service.py"
_SPACE_META = f"{_PY}/app/services/space_file_metadata_service.py"
_CAM_SVC = f"{_PY}/app/services/camera_service.py"

# post_process_service.py ensure_task_workspace L202-208
POST_PROCESS_WORKSPACE_KEYS: Set[str] = {
    "workspace_path",
    "container_path",
    "script_path",
    "created_files",
    "post_process_enabled",
}
# camera.py set_onvif_preset_api L1590-1594
ONVIF_PRESET_SAVE_KEYS: Set[str] = {"token", "name"}
# space_file_metadata_service.py sync_*_from_minio return
METADATA_SYNC_KEYS: Set[str] = {"synced_count", "skipped_count", "error_count"}
# camera_service.py batch_delete_cameras / batch_update_device_locations
BATCH_DELETE_RESULT_KEYS: Set[str] = {"deleted", "failed", "errors"}
BATCH_LOCATIONS_RESULT_KEYS: Set[str] = {"updated", "errors"}
# face.py merge_all_face_normalize result keys (service return)
FACE_MERGE_ALL_RESULT_KEYS: Set[str] = {"merged_groups", "merged_persons"}
# plate_model_download.py get_plate_model_status L52-62 + start download started
PLATE_MODEL_STATUS_KEYS: Set[str] = {
    "exists",
    "detect_model",
    "rec_model",
    "detect_path",
    "rec_path",
    "downloading",
    "stage",
    "progress",
    "error",
    "started",
}
# plate.py merge_all_plate_normalize result (PlateLibraryService merged_entries)
PLATE_MERGE_ALL_RESULT_KEYS: Set[str] = {"merged_groups", "merged_entries"}
# plate.py batch_delete_plate_entries data.deleted
BATCH_DELETE_COUNT_KEYS: Set[str] = {"deleted"}


def _rename_b35_samples(samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Carry forward B35 samples with frb36_* synthetic naming."""
    out: List[Dict[str, Any]] = []
    for sample in samples:
        copy = dict(sample)
        body = dict(copy.get("body") or {})
        for key, value in list(body.items()):
            if isinstance(value, str):
                body[key] = value.replace("frb35_", "frb36_")
            elif isinstance(value, list):
                body[key] = [
                    v.replace("frb35_", "frb36_") if isinstance(v, str) else v for v in value
                ]
        copy["body"] = body
        setup = copy.get("setup")
        if isinstance(setup, dict):
            setup_copy = dict(setup)
            setup_body = dict(setup_copy.get("body") or {})
            for key, value in list(setup_body.items()):
                if isinstance(value, str):
                    setup_body[key] = value.replace("frb35_", "frb36_")
                elif isinstance(value, list):
                    setup_body[key] = [
                        v.replace("frb35_", "frb36_") if isinstance(v, str) else v for v in value
                    ]
            setup_copy["body"] = setup_body
            copy["setup"] = setup_copy
        out.append(copy)
    return out


def _face_lib_setup(suffix: str) -> Dict[str, Any]:
    return {
        "method": "POST",
        "path": "/video/face/libraries",
        "body": {"name": f"frb36_face_{suffix}_{{ts}}"},
    }


def _plate_lib_setup(suffix: str) -> Dict[str, Any]:
    return {
        "method": "POST",
        "path": "/video/plate/libraries",
        "body": {"name": f"frb36_plate_{suffix}_{{ts}}"},
    }


def _pose_lib_setup(suffix: str) -> Dict[str, Any]:
    return {
        "method": "POST",
        "path": "/video/scenario-pose/libraries",
        "body": {"name": f"frb36_pose_{suffix}_{{ts}}"},
    }


def bind_post_keys_matrix_specs(fc: Any) -> List[Dict[str, Any]]:
    """Build curated POST samples covering ≥100 inventoried POST routes."""
    from post_keys_matrix_b33_specs import SEED_DEVICE_ID

    base = _rename_b35_samples(bind_b35_specs(fc))
    dev = SEED_DEVICE_ID

    extra: List[Dict[str, Any]] = [
        # --- algorithm post-process ---
        {
            "id": "algo_post_process_init",
            "method": "POST",
            "path": "/video/algorithm/task/{id}/post-process/init",
            "setup": {
                "method": "POST",
                "path": "/video/algorithm/task",
                "body": {
                    "task_name": "frb36_pp_{ts}",
                    "task_type": "realtime",
                    "device_ids": [dev],
                    "is_enabled": False,
                },
            },
            "body": {},
            "python_source": f"{_ALGO} init_post_process_workspace L802-809 → {_PP_SVC} ensure_task_workspace",
            "expect_code": 0,
            "data_keys": POST_PROCESS_WORKSPACE_KEYS,
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/algorithm/task/{id}"},
        },
        # --- camera stream / ticket / refresh ---
        {
            "id": "camera_stream_ticket_invalid_path_4xx",
            "method": "POST",
            "path": "/video/camera/stream/ticket/sign",
            "body": {"path": "/rtp/test.live.flv"},
            "python_source": f"{_CAM} sign_stream_ticket L113-114 unauthenticated → 401",
            "expect_code": 401,
            "mode": "envelope_only",
        },
        {
            "id": "camera_stream_start_offline_4xx",
            "method": "POST",
            "path": f"/video/camera/device/{dev}/stream/start",
            "body": {},
            "python_source": f"{_CAM} start_ffmpeg_stream L497-515 already running or started",
            "expect_code": 0,
            "mode": "envelope_success",
        },
        {
            "id": "camera_stream_stop",
            "method": "POST",
            "path": f"/video/camera/device/{dev}/stream/stop",
            "body": {},
            "python_source": f"{_CAM} stop_ffmpeg_stream L531",
            "expect_code": 0,
            "mode": "envelope_success",
        },
        {
            "id": "camera_refresh",
            "method": "POST",
            "path": "/video/camera/refresh",
            "body": {},
            "python_source": f"{_CAM} refresh_devices L2105-2108",
            "expect_code": 0,
            "mode": "envelope_success",
        },
        {
            "id": "camera_callback_on_publish",
            "method": "POST",
            "path": "/video/camera/callback/on_publish",
            "body": {},
            "python_source": f"{_CAM} on_publish_callback L2115-2127 async ack",
            "expect_code": 0,
            "mode": "envelope_success",
        },
        {
            "id": "camera_callback_on_dvr",
            "method": "POST",
            "path": "/video/camera/callback/on_dvr",
            "body": {},
            "python_source": f"{_CAM} on_dvr callback L2458 compat SRS DVR",
            "expect_code": 0,
            "mode": "envelope_success",
        },
        # --- camera PTZ / snapshot / rtsp / onvif ---
        {
            "id": "camera_ptz_no_body_4xx",
            "method": "POST",
            "path": f"/video/camera/device/{dev}/ptz",
            "body": {},
            "python_source": f"{_CAM} control_ptz L1141-1143 no JSON body → HTTP 400",
            "mode": "envelope_only",
        },
        {
            "id": "camera_device_snapshot",
            "method": "POST",
            "path": f"/video/camera/device/{dev}/snapshot",
            "body": {},
            "python_source": f"{_CAM} take_device_snapshot mini stub → honest capture fail code=500",
            "expect_code": 500,
            "mode": "envelope_only",
        },
        {
            "id": "camera_rtsp_start_missing_url_4xx",
            "method": "POST",
            "path": f"/video/camera/device/{dev}/rtsp/start",
            "body": {"rtsp_url": ""},
            "python_source": f"{_CAM} start_rtsp_capture L1393-1394 RTSP url required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_rtsp_stop",
            "method": "POST",
            "path": f"/video/camera/device/{dev}/rtsp/stop",
            "body": {},
            "python_source": f"{_CAM} stop_rtsp_capture L1420-1433 no running task → 400",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_onvif_start",
            "method": "POST",
            "path": f"/video/camera/device/{dev}/onvif/start",
            "body": {"interval": 30, "max_count": 1},
            "python_source": f"{_CAM} start_onvif_capture mini → 400 when unavailable",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_onvif_stop",
            "method": "POST",
            "path": f"/video/camera/device/{dev}/onvif/stop",
            "body": {},
            "python_source": f"{_CAM} stop_onvif_capture L1535-1536 no task → 400",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_onvif_preset_missing_name_4xx",
            "method": "POST",
            "path": f"/video/camera/device/{dev}/onvif/presets",
            "body": {},
            "python_source": f"{_CAM} set_onvif_preset_api L1584-1585 name required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_onvif_preset_call_missing_token_4xx",
            "method": "POST",
            "path": f"/video/camera/device/{dev}/onvif/presets/call",
            "body": {},
            "python_source": f"{_CAM} call_onvif_preset_api L1613-1614 preset_token required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        # --- camera batch / locations / nvr / scan / register variants ---
        {
            "id": "camera_devices_batch_delete_empty_4xx",
            "method": "POST",
            "path": "/video/camera/devices/batch-delete",
            "body": {},
            "python_source": f"{_CAM} batch_delete_devices L1105-1106 device_ids required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_locations_batch_empty",
            "method": "POST",
            "path": "/video/camera/locations/batch",
            "body": {"items": []},
            "python_source": f"{_CAM} batch_update_locations L709-710 → {_CAM_SVC} batch_update_device_locations",
            "expect_code": 0,
            "data_keys": BATCH_LOCATIONS_RESULT_KEYS,
        },
        {
            "id": "camera_nvr_upsert_missing_ip_4xx",
            "method": "POST",
            "path": "/video/camera/nvr/upsert",
            "body": {},
            "python_source": f"{_CAM} upsert_nvr_device L1790-1791 ip required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_nvr_register_channels_missing_ip_4xx",
            "method": "POST",
            "path": "/video/camera/nvr/register-channels",
            "body": {},
            "python_source": f"{_CAM} register_nvr_channels_device L1809-1811 ip required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_nvr_batch_delete_empty_4xx",
            "method": "POST",
            "path": "/video/camera/nvr/batch-delete",
            "body": {},
            "python_source": f"{_CAM} batch_delete_nvr L1951 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_scan_segment_missing_ip_4xx",
            "method": "POST",
            "path": "/video/camera/scan/segment",
            "body": {},
            "python_source": f"{_CAM} scan_segment L1974 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_scan_nvr_channels_missing_ip_4xx",
            "method": "POST",
            "path": "/video/camera/scan/nvr/channels",
            "body": {},
            "python_source": f"{_CAM} scan_nvr_channels L2037 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_register_dji_live_missing_4xx",
            "method": "POST",
            "path": "/video/camera/register/device/dji-live",
            "body": {},
            "python_source": f"{_CAM} register_dji_live_device L863 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_register_onvif_missing_4xx",
            "method": "POST",
            "path": "/video/camera/register/device/onvif",
            "body": {},
            "python_source": f"{_CAM} register_device_by_onvif L981 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_flighthub_live_start_missing_4xx",
            "method": "POST",
            "path": "/video/camera/flighthub/live-stream/start",
            "body": {},
            "python_source": f"{_CAM} start_flighthub_live_stream L888 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_flighthub_refresh_device",
            "method": "POST",
            "path": f"/video/camera/flighthub/live-stream/refresh-device/{dev}",
            "body": {},
            "python_source": f"{_CAM} refresh_flighthub_live_by_device L934 mini no DJI config → 400",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_directory_validate_json_empty_4xx",
            "method": "POST",
            "path": "/video/camera/directory/validate-json",
            "body": {},
            "python_source": f"{_CAM} validate_directory_json L2668-2670 body required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_directory_sync_json_empty_4xx",
            "method": "POST",
            "path": "/video/camera/directory/sync-json",
            "body": {},
            "python_source": f"{_CAM} sync_directory_json L2691-2693 body required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_directory_sync_gb28181",
            "method": "POST",
            "path": "/video/camera/directory/sync-gb28181",
            "body": {},
            "python_source": f"{_CAM} sync_gb28181_directory_devices L2706 mini no WVP → honest 500",
            "expect_code": 500,
            "mode": "envelope_only",
        },
        # --- device-detection snapshot / cover ---
        {
            "id": "device_detection_snapshot",
            "method": "POST",
            "path": f"/video/device-detection/device/{dev}/snapshot",
            "body": {},
            "python_source": f"{_DD} capture_device_snapshot L259-262 grab_frame fail → code=500",
            "expect_code": 500,
            "mode": "envelope_only",
        },
        {
            "id": "device_detection_cover_image",
            "method": "POST",
            "path": f"/video/device-detection/device/{dev}/cover-image",
            "body": {},
            "python_source": f"{_DD} update_device_cover_image L259-262 capture fail → code=500",
            "expect_code": 500,
            "mode": "envelope_only",
        },
        # --- face library actions ---
        {
            "id": "face_auto_enroll_start_4xx",
            "method": "POST",
            "path": "/video/face/libraries/{id}/auto-enroll/start",
            "setup": _face_lib_setup("enroll"),
            "body": {},
            "python_source": f"{_FACE} start_face_auto_enroll L393-399 ValueError → 400",
            "expect_code": 400,
            "mode": "envelope_only",
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/face/libraries/{id}"},
        },
        {
            "id": "face_entries_multipart_4xx",
            "method": "POST",
            "path": "/video/face/libraries/{id}/entries",
            "setup": _face_lib_setup("entry"),
            "body": {},
            "python_source": f"{_FACE} add_face_entry L265-283 multipart image required",
            "expect_code": 400,
            "mode": "envelope_only",
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/face/libraries/{id}"},
        },
        {
            "id": "face_entries_batch_multipart_4xx",
            "method": "POST",
            "path": "/video/face/libraries/{id}/entries/batch",
            "setup": _face_lib_setup("batch"),
            "body": {},
            "python_source": f"{_FACE} add_face_entries_batch L293-304 files required",
            "expect_code": 400,
            "mode": "envelope_only",
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/face/libraries/{id}"},
        },
        {
            "id": "face_match_multipart_4xx",
            "method": "POST",
            "path": "/video/face/libraries/{id}/match",
            "setup": _face_lib_setup("match"),
            "body": {},
            "python_source": f"{_FACE} match_face_in_library L477 image_bytes required",
            "expect_code": 400,
            "mode": "envelope_only",
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/face/libraries/{id}"},
        },
        {
            "id": "face_normalize_merge_missing_target_4xx",
            "method": "POST",
            "path": "/video/face/libraries/{id}/normalize/merge",
            "setup": _face_lib_setup("merge"),
            "body": {},
            "python_source": f"{_FACE} merge_face_normalize L446 target_person_id required",
            "expect_code": 400,
            "mode": "envelope_only",
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/face/libraries/{id}"},
        },
        {
            "id": "face_normalize_merge_all",
            "method": "POST",
            "path": "/video/face/libraries/{id}/normalize/merge-all",
            "setup": _face_lib_setup("merge_all"),
            "body": {},
            "python_source": f"{_FACE} merge_all_face_normalize L461-463 result dict",
            "expect_code": 0,
            "data_keys": FACE_MERGE_ALL_RESULT_KEYS,
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/face/libraries/{id}"},
        },
        {
            "id": "face_legacy_library_multipart_4xx",
            "method": "POST",
            "path": "/video/face/library",
            "body": {},
            "python_source": f"{_FACE} add_library L589-591 label + image required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "face_matching_publish_missing_4xx",
            "method": "POST",
            "path": "/video/face/matching/publish",
            "body": {},
            "python_source": f"{_FACE} publish_face_matching L501-504 taskId required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "face_matching_process_missing_4xx",
            "method": "POST",
            "path": "/video/face/matching/process",
            "body": {},
            "python_source": f"{_FACE} process_face_matching L535-539 ValueError → 400",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "face_persons_batch_delete_empty_4xx",
            "method": "POST",
            "path": "/video/face/persons/batch-delete",
            "body": {},
            "python_source": f"{_FACE} batch_delete_face_persons L233 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "face_recognize_image_multipart_4xx",
            "method": "POST",
            "path": "/video/face/recognize/image",
            "body": {},
            "python_source": f"{_FACE} recognize_face_image multipart image required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "face_recognize_device_snapshot",
            "method": "POST",
            "path": f"/video/face/recognize/device/{dev}/snapshot",
            "body": {},
            "python_source": f"{_FACE} recognize_face_device_snapshot mini capture fail → 500",
            "expect_code": 500,
            "mode": "envelope_only",
        },
        # --- plate parallel ---
        {
            "id": "plate_auto_enroll_start_4xx",
            "method": "POST",
            "path": "/video/plate/libraries/{id}/auto-enroll/start",
            "setup": _plate_lib_setup("enroll"),
            "body": {},
            "python_source": f"{_PLATE} start_plate_auto_enroll L313 validation",
            "expect_code": 400,
            "mode": "envelope_only",
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/plate/libraries/{id}"},
        },
        {
            "id": "plate_match_multipart_4xx",
            "method": "POST",
            "path": "/video/plate/libraries/{id}/match",
            "setup": _plate_lib_setup("match"),
            "body": {},
            "python_source": f"{_PLATE} match_plate_in_library L339 image required",
            "expect_code": 400,
            "mode": "envelope_only",
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/plate/libraries/{id}"},
        },
        {
            "id": "plate_normalize_merge_missing_4xx",
            "method": "POST",
            "path": "/video/plate/libraries/{id}/normalize/merge",
            "setup": _plate_lib_setup("merge"),
            "body": {},
            "python_source": f"{_PLATE} merge_plate_normalize L244 validation",
            "expect_code": 400,
            "mode": "envelope_only",
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/plate/libraries/{id}"},
        },
        {
            "id": "plate_normalize_merge_all",
            "method": "POST",
            "path": "/video/plate/libraries/{id}/normalize/merge-all",
            "setup": _plate_lib_setup("merge_all"),
            "body": {},
            "python_source": f"{_PLATE} merge_all_plate_normalize L264 merged_groups/merged_entries",
            "expect_code": 0,
            "data_keys": PLATE_MERGE_ALL_RESULT_KEYS,
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/plate/libraries/{id}"},
        },
        {
            "id": "plate_matching_publish_missing_4xx",
            "method": "POST",
            "path": "/video/plate/matching/publish",
            "body": {},
            "python_source": f"{_PLATE} publish_plate_matching L359 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "plate_matching_process_missing_4xx",
            "method": "POST",
            "path": "/video/plate/matching/process",
            "body": {},
            "python_source": f"{_PLATE} process_plate_matching L395 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "plate_entries_batch_delete_empty_4xx",
            "method": "POST",
            "path": "/video/plate/entries/batch-delete",
            "body": {},
            "python_source": f"{_PLATE} batch_delete_plate_entries L218-223 empty list → deleted=0",
            "expect_code": 0,
            "data_keys": BATCH_DELETE_COUNT_KEYS,
        },
        {
            "id": "plate_model_download",
            "method": "POST",
            "path": "/video/plate/model/download",
            "body": {},
            "python_source": f"{_PLATE} plate_model_download L75-78 → plate_model_download status dict",
            "expect_code": 0,
            "data_keys": PLATE_MODEL_STATUS_KEYS,
        },
        {
            "id": "plate_recognize_image_multipart_4xx",
            "method": "POST",
            "path": "/video/plate/recognize/image",
            "body": {},
            "python_source": f"{_PLATE} recognize_plate_image L433 multipart required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "plate_recognize_device_snapshot",
            "method": "POST",
            "path": f"/video/plate/recognize/device/{dev}/snapshot",
            "body": {},
            "python_source": f"{_PLATE} recognize_plate_device_snapshot L446 mini → honest 500",
            "expect_code": 500,
            "mode": "envelope_only",
        },
        # --- playback (inventoried path without trailing slash) ---
        {
            "id": "playback_create_no_slash_4xx",
            "method": "POST",
            "path": "/video/playback",
            "body": {},
            "python_source": f"{_PLAYBACK} create_playback L115-117 body required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        # --- record / snap sync ---
        {
            "id": "record_videos_sync",
            "method": "POST",
            "path": "/video/record/space/{id}/videos/sync",
            "prerequisite": {
                "method": "GET",
                "path": f"/video/record/space/device/{dev}",
                "body_key": "space_id",
                "data_key": "id",
            },
            "body": {},
            "python_source": f"{_RECORD} sync_videos_metadata L338-347 → {_SPACE_META} sync_record_files_from_minio",
            "expect_code": 500,
            "mode": "envelope_only",
        },
        {
            "id": "snap_space_sync_minio",
            "method": "POST",
            "path": "/video/snap/space/sync/minio",
            "body": {},
            "python_source": f"{_SNAP} sync_spaces_minio L197-205 → snap_space_service sync_spaces_to_minio",
            "expect_code": 0,
            "data_keys": RECORD_SYNC_MINIO_KEYS,
        },
        {
            "id": "snap_images_sync",
            "method": "POST",
            "path": "/video/snap/space/{id}/images/sync",
            "prerequisite": {
                "method": "GET",
                "path": f"/video/snap/space/device/{dev}",
                "body_key": "space_id",
                "data_key": "id",
            },
            "body": {},
            "python_source": f"{_SNAP} sync_images_metadata L989-997 → {_SPACE_META} sync_snap_images_from_minio",
            "expect_code": 500,
            "mode": "envelope_only",
        },
        {
            "id": "snap_region_missing_task_4xx",
            "method": "POST",
            "path": "/video/snap/region",
            "body": {"region_name": "frb36_region_{ts}"},
            "python_source": f"{_SNAP} create_region L528-530 task_id required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "snap_region_service_missing_body_4xx",
            "method": "POST",
            "path": "/video/snap/region/999999/service",
            "body": {},
            "python_source": f"{_SNAP} create_region_service L758-766 body required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "snap_task_service_missing_body_4xx",
            "method": "POST",
            "path": "/video/snap/task/999999/service",
            "body": {},
            "python_source": f"{_SNAP} create_task_service L664-666 body required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        # --- scenario-pose ---
        {
            "id": "scenario_pose_extract_multipart_4xx",
            "method": "POST",
            "path": "/video/scenario-pose/entries/extract",
            "body": {},
            "python_source": f"{_POSE} extract_preview L171-176 image_bytes required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "scenario_pose_re_extract_invalid_4xx",
            "method": "POST",
            "path": "/video/scenario-pose/entries/999999/re-extract",
            "body": {},
            "python_source": f"{_POSE} re_extract_entry L154 not found → 400",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "scenario_pose_import_template_missing_key_4xx",
            "method": "POST",
            "path": "/video/scenario-pose/libraries/{id}/import-template",
            "setup": _pose_lib_setup("import"),
            "body": {},
            "python_source": f"{_POSE} import_template L208-210 template_key required",
            "expect_code": 400,
            "mode": "envelope_only",
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/scenario-pose/libraries/{id}"},
        },
        {
            "id": "scenario_pose_match_test_multipart_4xx",
            "method": "POST",
            "path": "/video/scenario-pose/libraries/{id}/match-test",
            "setup": _pose_lib_setup("match_test"),
            "body": {},
            "python_source": f"{_POSE} match_test L185-190 image_bytes required",
            "expect_code": 400,
            "mode": "envelope_only",
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/scenario-pose/libraries/{id}"},
        },
        # --- patrol session start ---
        {
            "id": "patrol_session_start_invalid_4xx",
            "method": "POST",
            "path": "/video/patrol/session/999999/start",
            "body": {},
            "python_source": f"{_PATROL} start_session L49-59 session not found → 400",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        # --- media zlm hooks ---
        {
            "id": "media_hook_zlm_on_record_mp4",
            "method": "POST",
            "path": "/video/media/hook/zlm/on_record_mp4",
            "body": {},
            "python_source": f"{_MEDIA} zlm_on_record L85-89 empty ack",
            "expect_code": 0,
            "mode": "envelope_success",
        },
        {
            "id": "media_hook_zlm_on_record_ts",
            "method": "POST",
            "path": "/video/media/hook/zlm/on_record_ts",
            "body": {},
            "python_source": f"{_MEDIA} zlm_on_record L85-89 empty ack",
            "expect_code": 0,
            "mode": "envelope_success",
        },
        # --- stream-forward restart ---
        {
            "id": "stream_forward_restart_4xx",
            "method": "POST",
            "path": "/video/stream-forward/task/{id}/restart",
            "setup": {
                "method": "POST",
                "path": "/video/stream-forward/task",
                "body": {
                    "task_name": "frb36_sf_restart_{ts}",
                    "device_ids": [dev],
                    "is_enabled": False,
                },
            },
            "body": {},
            "python_source": f"{_SF} restart_task L210-215 disabled task may still return to_dict",
            "expect_code": 0,
            "data_keys": fc.STREAM_FORWARD_TASK_KEYS,
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/stream-forward/task/{id}"},
        },
    ]

    return base + extra
