"""Golden hook payload field set for G-2.2 (Phase 2 contract)."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Set

# Python realtime oracle + cpp RUNTIME must both emit these top-level keys when alerting.
HOOK_PAYLOAD_GOLDEN_KEYS: Set[str] = frozenset({
    'object',
    'event',
    'device_id',
    'device_name',
    'task_type',
    'correlation_id',
    'time',
    'image_path',
    'region',
    'information',
    'face_detection_enabled',
    'plate_detection_enabled',
})

# information JSON (string or dict) should include at minimum:
INFORMATION_GOLDEN_KEYS: Set[str] = frozenset({
    'detections',
})


def missing_hook_keys(payload: Dict[str, Any]) -> Set[str]:
    """Return golden keys absent from a hook payload dict."""
    return HOOK_PAYLOAD_GOLDEN_KEYS - set(payload.keys())


def assert_hook_payload_shape(payload: Dict[str, Any]) -> None:
    """Raise AssertionError when payload misses required golden keys."""
    missing = missing_hook_keys(payload)
    if missing:
        raise AssertionError(f'hook payload missing keys: {sorted(missing)}')


def compare_hook_field_sets(
    python_payload: Dict[str, Any],
    cpp_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """MVP field-layer diff for certify L_alarm (keys only, not values)."""
    py_keys = set(python_payload.keys())
    cpp_keys = set(cpp_payload.keys())
    golden = HOOK_PAYLOAD_GOLDEN_KEYS
    return {
        'python_only': sorted(py_keys - cpp_keys),
        'cpp_only': sorted(cpp_keys - py_keys),
        'missing_python_golden': sorted(golden - py_keys),
        'missing_cpp_golden': sorted(golden - cpp_keys),
        'ok': (
            golden <= py_keys
            and golden <= cpp_keys
            and not (py_keys ^ cpp_keys) - (py_keys | cpp_keys - golden)
        ),
    }
