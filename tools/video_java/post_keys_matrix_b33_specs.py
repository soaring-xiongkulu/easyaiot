"""FR-B33 Python-first POST success body key matrix specs.

Every data_keys set is cited from VIDEO/_retired_python_video to_dict / blueprint
success body — do not invent keys.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set

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
_MODELS = f"{_PY}/models.py"
_HOOK_SVC = f"{_PY}/app/services/alert_hook_service.py"

# alert_hook_service.py L922-927 (kafka success)
ALERT_HOOK_KAFKA_SUCCESS_KEYS: Set[str] = {"status", "topic", "partition", "offset"}
# alert_hook_service.py L802 / L821 (skipped / suppressed)
ALERT_HOOK_SKIPPED_KEYS: Set[str] = {"status", "reason"}
# Java mini direct_persist — AlertHookService.java L115-119 (documented alt for local mini)
ALERT_HOOK_DIRECT_PERSIST_KEYS: Set[str] = {"status", "alert_id", "mode"}

# camera.py register_device L844-848
CAMERA_REGISTER_DATA_KEYS: Set[str] = {"id"}

from keys_matrix_b29_specs import PATROL_SESSION_KEYS

SEED_DEVICE_ID = "vj_p2_device"
ALERT_SKIP_DEVICE_ID = "frb32_device"


def bind_post_keys_matrix_specs(fc: Any) -> List[Dict[str, Any]]:
    """Build sample list using key sets from field_contract (Python-first)."""
    return [
        {
            "id": "algo_task_create",
            "method": "POST",
            "path": "/video/algorithm/task",
            "body": {
                "task_name": "frb33_algo_{ts}",
                "task_type": "realtime",
                "device_ids": [SEED_DEVICE_ID],
                "is_enabled": False,
            },
            "python_source": f"{_ALGO} create_task L144-148 → {_MODELS} AlgorithmTask.to_dict",
            "expect_code": 0,
            "data_keys": fc.ALGORITHM_TASK_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/algorithm/task/{id}"},
        },
        {
            "id": "snap_task_create",
            "method": "POST",
            "path": "/video/snap/task",
            "prerequisite": {
                "method": "GET",
                "path": f"/video/snap/space/device/{SEED_DEVICE_ID}",
                "body_key": "space_id",
                "data_key": "id",
                "python_source": f"{_SNAP} get_space_by_device",
            },
            "body": {
                "task_name": "frb33_snap_{ts}",
                "space_id": None,
                "device_id": SEED_DEVICE_ID,
            },
            "python_source": f"{_SNAP} create_task L309-313 → {_MODELS} SnapTask.to_dict + device_name",
            "expect_code": 0,
            "data_keys": fc.SNAP_TASK_ITEM_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/snap/task/{id}"},
        },
        {
            "id": "face_library_create",
            "method": "POST",
            "path": "/video/face/libraries",
            "body": {"name": "frb33_face_{ts}"},
            "python_source": f"{_FACE} create_face_library L154 → {_MODELS} FaceLibrary.to_dict",
            "expect_code": 0,
            "data_keys": fc.FACE_LIBRARY_ITEM_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/face/libraries/{id}"},
        },
        {
            "id": "plate_library_create",
            "method": "POST",
            "path": "/video/plate/libraries",
            "body": {"name": "frb33_plate_{ts}"},
            "python_source": f"{_PLATE} create_plate_library L122 → {_MODELS} PlateLibrary.to_dict",
            "expect_code": 0,
            "data_keys": fc.PLATE_LIBRARY_ITEM_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/plate/libraries/{id}"},
        },
        {
            "id": "stream_forward_create",
            "method": "POST",
            "path": "/video/stream-forward/task",
            "body": {
                "task_name": "frb33_sf_{ts}",
                "device_ids": [SEED_DEVICE_ID],
                "is_enabled": False,
            },
            "python_source": f"{_SF} create_task L103-107 → {_MODELS} StreamForwardTask.to_dict",
            "expect_code": 0,
            "data_keys": fc.STREAM_FORWARD_TASK_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/stream-forward/task/{id}"},
        },
        {
            "id": "playback_create",
            "method": "POST",
            "path": "/video/playback/",
            "body": {
                "file_path": "/frb33/playback_{ts}.mp4",
                "event_time": "2026-08-11T10:00:00+08:00",
                "device_id": SEED_DEVICE_ID,
                "device_name": "P2",
                "duration": 60,
            },
            "python_source": f"{_PLAYBACK} create_playback L150-154 → {_MODELS} Playback.to_dict",
            "expect_code": 0,
            "data_keys": fc.PLAYBACK_ITEM_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/playback/{id}"},
        },
        {
            "id": "scenario_pose_library_create",
            "method": "POST",
            "path": "/video/scenario-pose/libraries",
            "body": {"name": "frb33_pose_{ts}"},
            "python_source": f"{_POSE} create_library L63 → {_MODELS} ScenarioPoseLibrary.to_dict",
            "expect_code": 0,
            "data_keys": fc.SCENARIO_POSE_LIBRARY_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/scenario-pose/libraries/{id}"},
        },
        {
            "id": "patrol_session_create",
            "method": "POST",
            "path": "/video/patrol/session",
            "body": {
                "session_name": "frb33_patrol_{ts}",
                "device_ids": [SEED_DEVICE_ID],
                "model_ids": [1],
            },
            "python_source": f"{_PATROL} create_session L32 → {_MODELS} PatrolSession.to_dict",
            "expect_code": 0,
            "data_keys": PATROL_SESSION_KEYS,
        },
        {
            "id": "camera_register",
            "method": "POST",
            "path": "/video/camera/register/device",
            "body": {
                "cameraType": "custom",
                "name": "frb33_cam_{ts}",
                "source": "file://F:/acme/RUNTIME/testdata/sample.mp4",
            },
            "python_source": f"{_CAM} register_device L844-848 data.id",
            "expect_code": 0,
            "data_keys": CAMERA_REGISTER_DATA_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/camera/device/{id}"},
        },
        {
            "id": "alert_hook_skipped",
            "method": "POST",
            "path": "/video/alert/hook",
            "body": {
                "device_id": ALERT_SKIP_DEVICE_ID,
                "device_name": "FR-B32",
                "object": "person",
                "event": "frb33_skip_{ts}",
                "time": "2026-08-11T10:00:00+08:00",
                "image_url": "/api/v1/buckets/frb33/objects/download?prefix=probe.jpg",
            },
            "python_source": f"{_HOOK_SVC} process_alert_hook L802 skipped",
            "expect_code": 0,
            "data_keys": ALERT_HOOK_SKIPPED_KEYS,
        },
        {
            "id": "alert_hook_success",
            "method": "POST",
            "path": "/video/alert/hook",
            "body": {
                "device_id": SEED_DEVICE_ID,
                "device_name": "P2",
                "object": "person",
                "event": "frb33_ok_{ts}",
                "time": "2026-08-11T10:00:00+08:00",
                "image_url": "/api/v1/buckets/frb33/objects/download?prefix=probe.jpg",
            },
            "python_source": (
                f"{_HOOK_SVC} L922-927 kafka success OR Java mini AlertHookService direct_persist L115-119"
            ),
            "expect_code": 0,
            "data_keys_alternatives": [
                ALERT_HOOK_KAFKA_SUCCESS_KEYS,
                ALERT_HOOK_DIRECT_PERSIST_KEYS,
            ],
        },
        {
            "id": "algo_empty_body_4xx",
            "method": "POST",
            "path": "/video/algorithm/task",
            "body": {},
            "python_source": f"{_ALGO} create_task L72-73 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "snap_task_missing_name_4xx",
            "method": "POST",
            "path": "/video/snap/task",
            "body": {"space_id": 1, "device_id": SEED_DEVICE_ID},
            "python_source": f"{_SNAP} create_task L269-270 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "face_library_missing_name_4xx",
            "method": "POST",
            "path": "/video/face/libraries",
            "body": {},
            "python_source": f"{_FACE} create_face_library ValueError name required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "playback_missing_fields_4xx",
            "method": "POST",
            "path": "/video/playback/",
            "body": {"device_id": SEED_DEVICE_ID},
            "python_source": f"{_PLAYBACK} create_playback L120-123 required_fields",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "snap_space_create_forbidden",
            "method": "POST",
            "path": "/video/snap/space",
            "body": {"space_name": "frb33_space_{ts}"},
            "python_source": f"{_SNAP} create_space L104-109 forbidden 403",
            "expect_code": 403,
            "mode": "envelope_only",
        },
    ]
