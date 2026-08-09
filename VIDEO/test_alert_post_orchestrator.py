"""Phase 3 — alert hook post-orchestration tests (G-3.1 / G-3.2)."""

from __future__ import annotations

import os
import tempfile
import unittest
import unittest.mock
from types import SimpleNamespace

import cv2
import numpy as np


class TestAlertPostOrchestrator(unittest.TestCase):
    def _cpp_task(self, **overrides):
        base = dict(
            id=91301,
            task_name='parity-face',
            task_type='realtime',
            executor='cpp',
            face_matching_enabled=True,
            plate_matching_enabled=False,
            face_library_ids='[1]',
            post_process_enabled=True,
            pose_analysis_enabled=False,
            pose_intent_enabled=False,
        )
        base.update(overrides)
        return SimpleNamespace(**base)

    def test_skips_python_executor(self):
        from app.services import alert_post_orchestrator as apo

        task = self._cpp_task(executor='python')
        with unittest.mock.patch.object(apo, '_resolve_task', return_value=task):
            summary = apo.run_post_alert_orchestration(
                {'device_id': 'dev1'},
                {'task_id': 91301},
            )
        self.assertEqual(summary['skipped_reason'], 'not_cpp_executor')

    def test_cpp_face_matching_enqueued(self):
        from app.services import alert_post_orchestrator as apo

        fd, path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)
        try:
            cv2.imwrite(path, np.zeros((64, 64, 3), dtype=np.uint8))
            task = self._cpp_task()
            alert = {
                'device_id': 'dev1',
                'device_name': 'cam1',
                'event': 'detection',
                'image_path': path,
                'correlation_id': 'corr-1',
                'information': {
                    'frame_number': 42,
                    'detections': [
                        {
                            'class_name': 'person',
                            'confidence': 0.9,
                            'bbox': [1, 2, 10, 20],
                        }
                    ],
                },
            }
            with unittest.mock.patch.object(apo, '_resolve_task', return_value=task):
                with unittest.mock.patch.object(apo, '_ensure_capture_workers'):
                    with unittest.mock.patch.object(apo, '_try_face_matching') as face_mock:
                        with unittest.mock.patch.object(apo, '_try_plate_matching'):
                            with unittest.mock.patch.object(apo, '_try_post_process_enqueue') as pp_mock:
                                summary = apo.run_post_alert_orchestration(alert, {'task_id': 91301})

            self.assertTrue(summary['face_matching'])
            self.assertTrue(summary['post_process'])
            face_mock.assert_called_once()
            pp_mock.assert_called_once()
        finally:
            if os.path.isfile(path):
                os.remove(path)

    def test_parse_cpp_information_detections(self):
        from app.services import alert_post_orchestrator as apo

        info = {
            'detection_count': 1,
            'detections': [{'class_name': 'car', 'confidence': 0.8, 'bbox': [0, 0, 1, 1]}],
            'runtime_ts_ms': 1_700_000_000_000,
        }
        dets = apo._extract_detections({}, info)
        self.assertEqual(len(dets), 1)
        self.assertEqual(dets[0]['class_name'], 'car')
        self.assertGreater(apo._extract_timestamp({}, info), 0)


if __name__ == '__main__':
    unittest.main()
