"""Phase 2 — hook payload golden field tests (G-2.2)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_PARITY = _REPO / 'tools' / 'runtime_parity'
if str(_PARITY) not in sys.path:
    sys.path.insert(0, str(_PARITY))

from hook_payload_fields import (
    HOOK_PAYLOAD_GOLDEN_KEYS,
    assert_hook_payload_shape,
    compare_hook_field_sets,
    missing_hook_keys,
)


class TestHookPayloadFields(unittest.TestCase):
    def test_python_oracle_shape(self):
        payload = {
            'object': 'person',
            'event': 'detection',
            'device_id': 'd1',
            'device_name': 'cam',
            'task_type': 'realtime',
            'correlation_id': 'uuid',
            'time': '2026-08-09 12:00:00',
            'image_path': '/tmp/a.jpg',
            'region': 'roi1',
            'information': '{"detections":[]}',
            'face_detection_enabled': True,
            'plate_detection_enabled': False,
        }
        assert_hook_payload_shape(payload)
        self.assertEqual(missing_hook_keys(payload), set())

    def test_cpp_contract_shape_after_phase2(self):
        payload = {
            'object': 'person',
            'event': 'detection',
            'device_id': 'd1',
            'device_name': 'cam',
            'task_type': 'realtime',
            'correlation_id': '123_2026-08-09T12:00:00Z',
            'time': '2026-08-09T12:00:00Z',
            'image_path': '/tmp/a.jpg',
            'region': 'default',
            'information': '{"detections":[]}',
            'face_detection_enabled': True,
            'plate_detection_enabled': True,
        }
        assert_hook_payload_shape(payload)

    def test_compare_field_sets_mvp(self):
        py = {k: None for k in HOOK_PAYLOAD_GOLDEN_KEYS}
        cpp = dict(py)
        result = compare_hook_field_sets(py, cpp)
        self.assertTrue(result['ok'])
        self.assertEqual(result['missing_cpp_golden'], [])


if __name__ == '__main__':
    unittest.main()
