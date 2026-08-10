"""FR-B35 Python-first POST success body key matrix specs (≥60 samples).

Extends FR-B34 with /video/camera/audio/talk POST coverage and additional
inventoried POST actions. Every data_keys set cited from Python oracle — do not invent keys.
"""

from __future__ import annotations

import base64
from typing import Any, Dict, List, Set

from post_keys_matrix_b34_specs import (
    DEVICE_COVER_IMAGE_DATA_KEYS,
    DEVICE_SNAPSHOT_DATA_KEYS,
    FACE_ENTRY_KEYS,
    PATROL_TASK_HEARTBEAT_ACK_KEYS,
    SCENARIO_POSE_ENTRY_KEYS,
    bind_post_keys_matrix_specs as bind_b34_specs,
)

_PY = "VIDEO/_retired_python_video"
_AUDIO = f"{_PY}/app/blueprints/audio_talk.py"
_ALGO = f"{_PY}/app/blueprints/algorithm_task.py"
_SNAP = f"{_PY}/app/blueprints/snap.py"
_FACE = f"{_PY}/app/blueprints/face.py"
_SF = f"{_PY}/app/blueprints/stream_forward.py"
_CAM = f"{_PY}/app/blueprints/camera.py"
_DD = f"{_PY}/app/blueprints/device_detection_region.py"
_MEDIA = f"{_PY}/app/blueprints/media_hook.py"
_ALERT = f"{_PY}/app/blueprints/alert.py"
_MODELS = f"{_PY}/models.py"
_HOOK_SVC = f"{_PY}/app/services/alert_hook_service.py"

# audio_talk.py L133-143 start success data
AUDIO_TALK_START_SUCCESS_KEYS: Set[str] = {
    "success",
    "session_id",
    "device_id",
    "camera_ip",
    "audio_codec",
    "sample_rate",
    "volume_gain",
    "noise_suppression",
    "echo_cancellation",
}
# audio_talk.py L124-127 / L175 start|send failure data
AUDIO_TALK_ACTION_FAIL_KEYS: Set[str] = {"success"}
# audio_talk.py L158 stop success data
AUDIO_TALK_STOP_SUCCESS_KEYS: Set[str] = {"success", "session_id"}
# audio_talk.py L176 send success data
AUDIO_TALK_SEND_SUCCESS_KEYS: Set[str] = {"success"}

# Minimal PCM payload for send probe (base64 of 4 zero bytes)
_AUDIO_PROBE_B64 = base64.b64encode(bytes(4)).decode("ascii")


def _rename_b34_samples(samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Carry forward B34 samples with frb35_* synthetic naming."""
    out: List[Dict[str, Any]] = []
    for sample in samples:
        copy = dict(sample)
        body = dict(copy.get("body") or {})
        for key, value in list(body.items()):
            if isinstance(value, str):
                body[key] = value.replace("frb34_", "frb35_")
            elif isinstance(value, list):
                body[key] = [
                    v.replace("frb34_", "frb35_") if isinstance(v, str) else v for v in value
                ]
        copy["body"] = body
        out.append(copy)
    return out


def bind_post_keys_matrix_specs(fc: Any) -> List[Dict[str, Any]]:
    """Build ≥60 curated POST samples (Python-first key cites)."""
    from post_keys_matrix_b33_specs import SEED_DEVICE_ID

    base = _rename_b34_samples(bind_b34_specs(fc))
    algo_start_keys = set(fc.ALGORITHM_TASK_KEYS) | {"already_running"}
    sf_start_keys = set(fc.STREAM_FORWARD_TASK_KEYS) | {"already_running"}

    extra: List[Dict[str, Any]] = [
        # --- audio_talk prefix (POST start/stop/send) ---
        {
            "id": "audio_talk_start_missing_device_4xx",
            "method": "POST",
            "path": "/video/camera/audio/talk/start",
            "body": {},
            "python_source": f"{_AUDIO} start_audio_talk L94-95 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "audio_talk_start_invalid_device_4xx",
            "method": "POST",
            "path": "/video/camera/audio/talk/start",
            "body": {"device_id": "invalid_frb35_device"},
            "python_source": f"{_AUDIO} start_audio_talk L97-99 device not found",
            "expect_code": 404,
            "mode": "envelope_only",
        },
        {
            "id": "audio_talk_start_backchannel_fail",
            "method": "POST",
            "path": "/video/camera/audio/talk/start",
            "body": {"device_id": SEED_DEVICE_ID},
            "python_source": f"{_AUDIO} start_audio_talk L123-127 ONVIF backchannel fail",
            "expect_code": 500,
            "data_keys": AUDIO_TALK_ACTION_FAIL_KEYS,
        },
        {
            "id": "audio_talk_stop_missing_session_4xx",
            "method": "POST",
            "path": "/video/camera/audio/talk/stop",
            "body": {},
            "python_source": f"{_AUDIO} stop_audio_talk L154-155 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "audio_talk_stop_ok",
            "method": "POST",
            "path": "/video/camera/audio/talk/stop",
            "body": {"session_id": "audio_talk_frb35_probe_12345678"},
            "python_source": f"{_AUDIO} stop_audio_talk L157-158",
            "expect_code": 0,
            "data_keys": AUDIO_TALK_STOP_SUCCESS_KEYS,
        },
        {
            "id": "audio_talk_send_missing_fields_4xx",
            "method": "POST",
            "path": "/video/camera/audio/talk/send",
            "body": {},
            "python_source": f"{_AUDIO} send_audio_data L169-170 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "audio_talk_send_fail",
            "method": "POST",
            "path": "/video/camera/audio/talk/send",
            "body": {
                "session_id": "audio_talk_frb35_missing_session",
                "audio_data": _AUDIO_PROBE_B64,
            },
            "python_source": f"{_AUDIO} send_audio_data L174-175 send failure",
            "expect_code": 500,
            "data_keys": AUDIO_TALK_ACTION_FAIL_KEYS,
        },
        # --- algorithm actions (beyond B34) ---
        {
            "id": "algo_task_start_runtime_missing_4xx",
            "method": "POST",
            "path": "/video/algorithm/task/{id}/start",
            "setup": {
                "method": "POST",
                "path": "/video/algorithm/task",
                "body": {
                    "task_name": "frb35_algo_start_{ts}",
                    "task_type": "realtime",
                    "device_ids": [SEED_DEVICE_ID],
                    "is_enabled": False,
                },
            },
            "body": {},
            "python_source": f"{_ALGO} start_task L228-234 RUNTIME missing → 400",
            "expect_code": 400,
            "mode": "envelope_only",
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/algorithm/task/{id}"},
        },
        {
            "id": "algo_task_restart_runtime_missing_4xx",
            "method": "POST",
            "path": "/video/algorithm/task/{id}/restart",
            "setup": {
                "method": "POST",
                "path": "/video/algorithm/task",
                "body": {
                    "task_name": "frb35_algo_restart_{ts}",
                    "task_type": "realtime",
                    "device_ids": [SEED_DEVICE_ID],
                    "is_enabled": False,
                },
            },
            "body": {},
            "python_source": f"{_ALGO} restart_task L267-268 validation/runtime → 400",
            "expect_code": 400,
            "mode": "envelope_only",
            "cleanup_use_setup_id": True,
            "cleanup": {"method": "DELETE", "path_template": "/video/algorithm/task/{id}"},
        },
        {
            "id": "algo_heartbeat_patrol_missing_4xx",
            "method": "POST",
            "path": "/video/algorithm/heartbeat/patrol",
            "body": {},
            "python_source": f"{_ALGO} receive_patrol_task_heartbeat L351-352 validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        {
            "id": "algo_heartbeat_patrol_invalid_task_4xx",
            "method": "POST",
            "path": "/video/algorithm/heartbeat/patrol",
            "body": {"task_id": 999999999},
            "python_source": f"{_ALGO} receive_patrol_task_heartbeat L354-356 task not found",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        # --- stream-forward start ---
        {
            "id": "stream_forward_start",
            "method": "POST",
            "path": "/video/stream-forward/task/{id}/start",
            "setup": {
                "method": "POST",
                "path": "/video/stream-forward/task",
                "body": {
                    "task_name": "frb35_sf_start_{ts}",
                    "device_ids": [SEED_DEVICE_ID],
                    "is_enabled": False,
                },
            },
            "body": {},
            "python_source": f"{_SF} start_task → {_MODELS} StreamForwardTask.to_dict + already_running",
            "expect_code": 0,
            "data_keys": sf_start_keys,
            "cleanup": {"method": "DELETE", "path_template": "/video/stream-forward/task/{id}"},
        },
        # --- snap task lifecycle ---
        {
            "id": "snap_task_start",
            "method": "POST",
            "path": "/video/snap/task/{id}/start",
            "setup": {
                "method": "POST",
                "path": "/video/snap/task",
                "body": {
                    "task_name": "frb35_snap_start_{ts}",
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
            "python_source": f"{_SNAP} start_task_route L415-419 → {_MODELS} SnapTask.to_dict",
            "expect_code": 0,
            "data_keys": fc.SNAP_TASK_ITEM_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/snap/task/{id}"},
        },
        {
            "id": "snap_task_restart",
            "method": "POST",
            "path": "/video/snap/task/{id}/restart",
            "setup": {
                "method": "POST",
                "path": "/video/snap/task",
                "body": {
                    "task_name": "frb35_snap_restart_{ts}",
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
            "python_source": f"{_SNAP} restart_task_route L447-451 → {_MODELS} SnapTask.to_dict",
            "expect_code": 0,
            "data_keys": fc.SNAP_TASK_ITEM_KEYS,
            "cleanup": {"method": "DELETE", "path_template": "/video/snap/task/{id}"},
        },
        # --- device-detection success create ---
        {
            "id": "device_detection_no_algo_model_4xx",
            "method": "POST",
            "path": f"/video/device-detection/device/{SEED_DEVICE_ID}/regions",
            "body": {
                "region_name": "frb35_region_{ts}",
                "region_type": "polygon",
                "points": [[0, 0], [1, 0], [1, 1]],
            },
            "python_source": f"{_DD} create_region L73-74 device task missing model_ids",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        # --- face entry ---
        {
            "id": "face_model_download",
            "method": "POST",
            "path": "/video/face/model/download",
            "body": {},
            "python_source": f"{_FACE} face_rec_model_download L105-109 → face_model_download status dict",
            "expect_code": 0,
            "data_keys": fc.FACE_MODEL_STATUS_KEYS,
        },
        # --- media hook on_publish ack ---
        {
            "id": "media_hook_srs_on_publish",
            "method": "POST",
            "path": "/video/media/hook/srs/on_publish",
            "body": {},
            "python_source": f"{_MEDIA} srs_on_publish L48-52 → camera on_publish_callback",
            "expect_code": 0,
            "mode": "envelope_success",
        },
        # --- camera register validation ---
        {
            "id": "camera_register_missing_source_4xx",
            "method": "POST",
            "path": "/video/camera/register/device",
            "body": {"cameraType": "custom", "name": "frb35_cam_nosrc_{ts}"},
            "python_source": f"{_CAM} register_device required source validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        # --- alert hook validation ---
        {
            "id": "alert_hook_missing_device_4xx",
            "method": "POST",
            "path": "/video/alert/hook",
            "body": {
                "object": "person",
                "event": "frb35_missing_dev_{ts}",
                "time": "2026-08-11T10:00:00+08:00",
            },
            "python_source": f"{_HOOK_SVC} process_alert_hook device_id required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        # --- device-detection invalid region type ---
        {
            "id": "device_detection_invalid_region_type_4xx",
            "method": "POST",
            "path": f"/video/device-detection/device/{SEED_DEVICE_ID}/regions",
            "body": {
                "region_name": "frb35_badtype_{ts}",
                "region_type": "invalid",
                "points": [[0, 0], [1, 0], [1, 1]],
            },
            "python_source": f"{_DD} create_region L80-82 region_type validation",
            "expect_code": 400,
            "mode": "envelope_only",
        },
        # --- face library missing name (extra 4xx) ---
        {
            "id": "plate_library_missing_name_4xx",
            "method": "POST",
            "path": "/video/plate/libraries",
            "body": {},
            "python_source": f"{_PY}/app/blueprints/plate.py create_plate_library name required",
            "expect_code": 400,
            "mode": "envelope_only",
        },
    ]

    return base + extra
