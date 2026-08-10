"""FR-B34 Python-first POST success body key matrix specs (≥40 samples).

Extends FR-B33 curated samples across all 14 inventoried prefixes where possible.
Every data_keys set is cited from VIDEO/_retired_python_video to_dict / blueprint —
do not invent keys.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set

from post_keys_matrix_b33_specs import (
    ALERT_HOOK_DIRECT_PERSIST_KEYS,
    ALERT_HOOK_KAFKA_SUCCESS_KEYS,
    ALERT_HOOK_SKIPPED_KEYS,
    ALERT_SKIP_DEVICE_ID,
    CAMERA_REGISTER_DATA_KEYS,
    SEED_DEVICE_ID,
    bind_post_keys_matrix_specs as bind_b33_specs,
)

_PY = "VIDEO/_retired_python_video"
_ALGO = f"{_PY}/app/blueprints/algorithm_task.py"
_SNAP = f"{_PY}/app/blueprints/snap.py"
_FACE = f"{_PY}/app/blueprints/face.py"
_PLATE = f"{_PY}/app/blueprints/plate.py"
_SF = f"{_PY}/app/blueprints/stream_forward.py"
_PLAYBACK = f"{_PY}/app/blueprints/playback.py"
_POSE = f"{_PY}/app/blueprints/scenario_pose.py"
_PATROL = f"{_PY}/app/blueprints/patrol.py"
_ALERT = f"{_PY}/app/blueprints/alert.py"
_CAM = f"{_PY}/app/blueprints/camera.py"
_RECORD = f"{_PY}/app/blueprints/record.py"
_MEDIA = f"{_PY}/app/blueprints/media_hook.py"
_DD = f"{_PY}/app/blueprints/device_detection_region.py"
_MODELS = f"{_PY}/models.py"
_HOOK_SVC = f"{_PY}/app/services/alert_hook_service.py"
_RECORD_SVC = f"{_PY}/app/services/record_space_service.py"

# algorithm_task.py L328-335 / stream_forward.py L266-273 heartbeat ack
TASK_HEARTBEAT_ACK_KEYS: Set[str] = {"task_id", "task_name"}
# algorithm_task.py L376 patrol task heartbeat ack
PATROL_TASK_HEARTBEAT_ACK_KEYS: Set[str] = {"task_id"}
# record_space_service.py sync_spaces_to_minio return dict
RECORD_SYNC_MINIO_KEYS: Set[str] = {"total_spaces", "created_count", "skipped_count", "error_count"}
# camera.py L2797-2806 create_directory data
CAMERA_DIRECTORY_CREATE_KEYS: Set[str] = {"id", "name", "parent_id", "description", "sort_order"}
# camera.py L810-815 ensure-spaces data top-level
CAMERA_ENSURE_SPACES_KEYS: Set[str] = {"snap_space", "record_space"}
# device_detection_region.py L280-288 snapshot data
DEVICE_SNAPSHOT_DATA_KEYS: Set[str] = {"image_id", "image_url", "width", "height"}
# device_detection_region.py L230-239 cover-image data
DEVICE_COVER_IMAGE_DATA_KEYS: Set[str] = {
    "cover_image_path",
    "image_url",
    "image_id",
    "width",
    "height",
}
# stream_forward.py ensure_device_task L527-531
STREAM_FORWARD_ENSURE_KEYS: Set[str] = {"task_id", "task_name", "task_code", "is_enabled"}
# models.py FaceEntry.to_dict L1327-1341
FACE_ENTRY_KEYS: Set[str] = {
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
# models.py PlateEntry.to_dict L1517-1531
PLATE_ENTRY_KEYS: Set[str] = {
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
# models.py ScenarioPoseEntry.to_dict L1735-1750
SCENARIO_POSE_ENTRY_KEYS: Set[str] = {
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
# models.py FaceAutoEnrollTask.to_dict L1381-1397
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
# models.py PlateAutoEnrollTask.to_dict L1570-1585
PLATE_AUTO_ENROLL_KEYS: Set[str] = {
    "id",
    "library_id",
    "device_ids",
    "device_names",
    "duration_minutes",
    "capture_interval_sec",
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

from keys_matrix_b29_specs import PATROL_SESSION_KEYS


def _rename_b33_samples(samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Carry forward B33 samples with frb34_* synthetic naming."""
    out: List[Dict[str, Any]] = []
    for sample in samples:
        copy = dict(sample)
        body = dict(copy.get("body") or {})
        for key, value in list(body.items()):
            if isinstance(value, str):
                body[key] = value.replace("frb33_", "frb34_")
            elif isinstance(value, list):
                body[key] = [
                    v.replace("frb33_", "frb34_") if isinstance(v, str) else v for v in value
                ]
        copy["body"] = body
        out.append(copy)
    return out


def bind_post_keys_matrix_specs(fc: Any) -> List[Dict[str, Any]]:
    """Build ≥40 curated POST samples (Python-first key cites)."""
    base = _rename_b33_samples(bind_b33_specs(fc))
    algo_start_keys = set(fc.ALGORITHM_TASK_KEYS) | {"already_running"}
    sf_start_keys = set(fc.STREAM_FORWARD_TASK_KEYS) | {"already_running"}

    extra: List[Dict[str, Any]] = [
        # --- record prefix ---
        {
            "id": "record_space_create_forbidden",
            "method": "POST",
            "path": "/video/record/space",
            "body": {"space_name": "frb34_rec_{ts}"},
            "python_source": f"{_RECORD} create_space L92-98 forbidden 403",
            "expect_code": 403,
            "mode": "envelope_only",
        },
        {
            "id": "record_space_sync_minio",
            "method": "POST",
            "path": "/video/record/space/sync/minio",
            "body": {},
            "python_source": f"{_RECORD} sync_spaces_minio L186-195 → {_RECORD_SVC} sync_spaces_to_minio",
            "expect_code": 0,
            "data_keys": RECORD_SYNC_MINIO_KEYS,
        },
        # --- media prefix ---
        {
            "id": "media_hook_snap_completed",
            "method": "POST",
            "path": "/video/media/hook/snap/completed",
            "body": {
                "device_id": SEED_DEVICE_ID,
                "file_path": "/tmp/frb34_snap_probe.jpg",
                "source": "frb34",
            },
            "python_source": f"{_MEDIA} snap_completed L60-79 → _hook_ok code+msg",
            "expect_code": 0,
            "mode": "envelope_success",
        },
        {
            "id": "media_hook_srs_on_dvr_empty",
            "method": "POST",
            "path": "/video/media/hook/srs/on_dvr",
            "body": {},
            "python_source": f"{_MEDIA} srs_on_dvr L32-36 empty → _hook_ok",
            "expect_code": 0,
            "mode": "envelope_success",
        },
        {
            "id": "media_hook_srs_on_unpublish",
            "method": "POST",
            "path": "/video/media/hook/srs/on_unpublish",
            "body": {},
            "python_source": f"{_MEDIA} srs_on_unpublish L55-57 → _hook_ok",
            "expect_code": 0,
            "mode": "envelope_success",
        },
        # --- device-detection prefix ---
        {
            "id": "device_detection_region_missing_name_4xx",
            "method": "POST",
            "path": f"/video/device-detection/device/{SEED_DEVICE_ID}/regions",
            "body": {
                "region_type": "polygon",
                "points": [[0, 0], [1, 0], [1, 1]],
            },
            "python_source": f"{_DD} create_region L76-78 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "device_detection_invalid_device_4xx",
            "method": "POST",
            "path": "/video/device-detection/device/invalid_frb34_device/regions",
            "body": {
                "region_name": "frb34_region_{ts}",
                "region_type": "polygon",
                "points": [[0, 0], [1, 0], [1, 1]],
            },
            "python_source": f"{_DD} create_region L51-52 device not found",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        # --- camera prefix (beyond register) ---
        {
            "id": "camera_directory_create",
            "method": "POST",
            "path": "/video/camera/directory",
            "body": {"name": "frb34_dir_{ts}", "description": "frb34"},
            "python_source": f"{_CAM} create_directory L2797-2806",
            "expect_code": 0,
            "data_keys": CAMERA_DIRECTORY_CREATE_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/camera/directory/{id}"},
        },
        {
            "id": "camera_directory_missing_name_4xx",
            "method": "POST",
            "path": "/video/camera/directory",
            "body": {"description": "frb34"},
            "python_source": f"{_CAM} create_directory L2771-2773 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "camera_ensure_spaces",
            "method": "POST",
            "path": f"/video/camera/device/{SEED_DEVICE_ID}/ensure-spaces",
            "body": {},
            "python_source": f"{_CAM} ensure_device_spaces_route L810-815",
            "expect_code": 0,
            "data_keys": CAMERA_ENSURE_SPACES_KEYS,
        },
        # --- algorithm actions ---
        {
            "id": "algo_task_stop",
            "method": "POST",
            "path": "/video/algorithm/task/{id}/stop",
            "setup": {
                "method": "POST",
                "path": "/video/algorithm/task",
                "body": {
                    "task_name": "frb34_algo_stop_{ts}",
                    "task_type": "realtime",
                    "device_ids": [SEED_DEVICE_ID],
                    "is_enabled": False,
                },
            },
            "body": {},
            "python_source": f"{_ALGO} stop_task L245-248 → {_MODELS} AlgorithmTask.to_dict",
            "expect_code": 0,
            "data_keys": fc.ALGORITHM_TASK_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/algorithm/task/{id}"},
        },
        {
            "id": "algo_heartbeat_realtime",
            "method": "POST",
            "path": "/video/algorithm/heartbeat/realtime",
            "setup": {
                "method": "POST",
                "path": "/video/algorithm/task",
                "body": {
                    "task_name": "frb34_algo_hb_{ts}",
                    "task_type": "realtime",
                    "device_ids": [SEED_DEVICE_ID],
                    "is_enabled": False,
                },
            },
            "body": {"server_ip": "127.0.0.1", "port": 1, "process_id": 1},
            "body_from_setup": {"task_id": "id"},
            "python_source": f"{_ALGO} receive_realtime_heartbeat L328-335",
            "expect_code": 0,
            "data_keys": TASK_HEARTBEAT_ACK_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/algorithm/task/{id}"},
        },
        {
            "id": "algo_heartbeat_missing_task_4xx",
            "method": "POST",
            "path": "/video/algorithm/heartbeat/realtime",
            "body": {},
            "python_source": f"{_ALGO} receive_realtime_heartbeat L293-297 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        # --- stream-forward actions ---
        {
            "id": "stream_forward_stop",
            "method": "POST",
            "path": "/video/stream-forward/task/{id}/stop",
            "setup": {
                "method": "POST",
                "path": "/video/stream-forward/task",
                "body": {
                    "task_name": "frb34_sf_stop_{ts}",
                    "device_ids": [SEED_DEVICE_ID],
                    "is_enabled": False,
                },
            },
            "body": {},
            "python_source": f"{_SF} stop_task L193-196 → {_MODELS} StreamForwardTask.to_dict",
            "expect_code": 0,
            "data_keys": fc.STREAM_FORWARD_TASK_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/stream-forward/task/{id}"},
        },
        {
            "id": "sf_heartbeat",
            "method": "POST",
            "path": "/video/stream-forward/heartbeat",
            "setup": {
                "method": "POST",
                "path": "/video/stream-forward/task",
                "body": {
                    "task_name": "frb34_sf_hb_{ts}",
                    "device_ids": [SEED_DEVICE_ID],
                    "is_enabled": False,
                },
            },
            "body": {"server_ip": "127.0.0.1", "port": 1, "process_id": 1},
            "body_from_setup": {"task_id": "id"},
            "python_source": f"{_SF} receive_heartbeat L266-273",
            "expect_code": 0,
            "data_keys": TASK_HEARTBEAT_ACK_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/stream-forward/task/{id}"},
        },
        {
            "id": "stream_forward_missing_name_4xx",
            "method": "POST",
            "path": "/video/stream-forward/task",
            "body": {"device_ids": [SEED_DEVICE_ID]},
            "python_source": f"{_SF} create_task task_name required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        # --- snap actions ---
        {
            "id": "snap_task_stop",
            "method": "POST",
            "path": "/video/snap/task/{id}/stop",
            "setup": {
                "method": "POST",
                "path": "/video/snap/task",
                "body": {
                    "task_name": "frb34_snap_stop_{ts}",
                    "space_id": None,
                    "device_id": SEED_DEVICE_ID,
                },
                "prerequisite": {
                    "method": "GET",
                    "path": f"/video/snap/space/device/{SEED_DEVICE_ID}",
                    "body_key": "space_id",
                    "data_key": "id",
                },
            },
            "body": {},
            "python_source": f"{_SNAP} stop_task_route L433-437 → {_MODELS} SnapTask.to_dict",
            "expect_code": 0,
            "data_keys": fc.SNAP_TASK_ITEM_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/snap/task/{id}"},
        },
        # --- patrol actions ---
        {
            "id": "stream_forward_ensure_task",
            "method": "POST",
            "path": f"/video/stream-forward/device/{SEED_DEVICE_ID}/ensure-task",
            "body": {},
            "python_source": f"{_SF} ensure_device_task L524-532",
            "expect_code": 0,
            "data_keys": STREAM_FORWARD_ENSURE_KEYS,
        },
        {
            "id": "patrol_session_stop",
            "method": "POST",
            "path": "/video/patrol/session/{id}/stop",
            "setup": {
                "method": "POST",
                "path": "/video/patrol/session",
                "body": {
                    "session_name": "frb34_patrol_stop_{ts}",
                    "device_ids": [SEED_DEVICE_ID],
                    "model_ids": [1],
                },
            },
            "body": {},
            "python_source": f"{_PATROL} stop_session L70 → {_MODELS} PatrolSession.to_dict",
            "expect_code": 0,
            "data_keys": PATROL_SESSION_KEYS,
        },
        {
            "id": "patrol_heartbeat",
            "method": "POST",
            "path": "/video/patrol/heartbeat",
            "setup": {
                "method": "POST",
                "path": "/video/patrol/session",
                "body": {
                    "session_name": "frb34_patrol_hb_{ts}",
                    "device_ids": [SEED_DEVICE_ID],
                    "model_ids": [1],
                },
            },
            "body": {"server_ip": "127.0.0.1", "process_id": 1},
            "body_from_setup": {"session_id": "id"},
            "python_source": f"{_PATROL} patrol_heartbeat L174 success code+msg",
            "expect_code": 0,
            "mode": "envelope_success",
        },
        {
            "id": "patrol_session_missing_models_4xx",
            "method": "POST",
            "path": "/video/patrol/session",
            "body": {
                "session_name": "frb34_patrol_nomodel_{ts}",
                "device_ids": [SEED_DEVICE_ID],
                "model_ids": [],
            },
            "python_source": f"{_PATROL} create_session → patrol_session_service L75-76 model_ids required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        # --- face / plate / scenario-pose ---
        {
            "id": "plate_entry_create",
            "method": "POST",
            "path": "/video/plate/libraries/{id}/entries",
            "setup": {
                "method": "POST",
                "path": "/video/plate/libraries",
                "body": {"name": "frb34_plate_ent_{ts}"},
            },
            "body": {"plate_no": "frb34{ts}"},
            "python_source": f"{_PLATE} add_plate_entry L182 → {_MODELS} PlateEntry.to_dict",
            "expect_code": 0,
            "data_keys": PLATE_ENTRY_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/plate/libraries/{id}"},
        },
        {
            "id": "scenario_pose_rule_entry",
            "method": "POST",
            "path": "/video/scenario-pose/libraries/{id}/entries",
            "setup": {
                "method": "POST",
                "path": "/video/scenario-pose/libraries",
                "body": {"name": "frb34_pose_ent_{ts}"},
            },
            "body": {
                "source_type": "rule",
                "name": "frb34_rule_{ts}",
                "extra_rules": {"min_persons": 1},
            },
            "python_source": f"{_POSE} add_entry L118-125 → {_MODELS} ScenarioPoseEntry.to_dict",
            "expect_code": 0,
            "data_keys": SCENARIO_POSE_ENTRY_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/scenario-pose/libraries/{id}"},
        },
        {
            "id": "scenario_pose_missing_name_4xx",
            "method": "POST",
            "path": "/video/scenario-pose/libraries",
            "body": {},
            "python_source": f"{_POSE} create_library name required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "face_auto_enroll_stop",
            "method": "POST",
            "path": "/video/face/libraries/{id}/auto-enroll/stop",
            "setup": {
                "method": "POST",
                "path": "/video/face/libraries",
                "body": {"name": "frb34_face_ae_{ts}"},
                "followups": [
                    {
                        "method": "PUT",
                        "path": "/video/face/libraries/{id}/auto-enroll",
                        "body": {
                            "device_ids": [SEED_DEVICE_ID],
                            "duration_minutes": 60,
                            "capture_interval_sec": 5,
                        },
                    }
                ],
            },
            "body": {},
            "python_source": f"{_FACE} stop_face_auto_enroll L408 → {_MODELS} FaceAutoEnrollTask.to_dict",
            "expect_code": 0,
            "data_keys": FACE_AUTO_ENROLL_KEYS,
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/face/libraries/{id}"},
        },
        {
            "id": "plate_auto_enroll_stop",
            "method": "POST",
            "path": "/video/plate/libraries/{id}/auto-enroll/stop",
            "setup": {
                "method": "POST",
                "path": "/video/plate/libraries",
                "body": {"name": "frb34_plate_ae_{ts}"},
                "followups": [
                    {
                        "method": "PUT",
                        "path": "/video/plate/libraries/{id}/auto-enroll",
                        "body": {
                            "device_ids": [SEED_DEVICE_ID],
                            "duration_minutes": 60,
                            "capture_interval_sec": 5,
                        },
                    }
                ],
            },
            "body": {},
            "python_source": f"{_PLATE} stop_plate_auto_enroll → {_MODELS} PlateAutoEnrollTask.to_dict",
            "expect_code": 0,
            "data_keys": PLATE_AUTO_ENROLL_KEYS,
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/plate/libraries/{id}"},
        },
    ]

    return base + extra
