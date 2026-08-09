"""Phase 2 — runtime ini contract mapping tests (G-2.1)."""

from __future__ import annotations

import re
import unittest
import unittest.mock
from types import SimpleNamespace


class TestRuntimeIniContract(unittest.TestCase):
    def _minimal_task(self, **overrides):
        base = dict(
            id=99001,
            task_type='realtime',
            model_ids='[1]',
            model_names='detection',
            detect_conf=0.5,
            alert_event_enabled=True,
            alert_event_suppress_time=30,
            extract_interval=8,
            frame_skip=1,
            tracking_enabled=True,
            motion_gate_enabled=False,
            face_detection_enabled=True,
            plate_detection_enabled=False,
            face_matching_enabled=True,
            rtmp_output_url='',
            prefer_gpu=False,
            devices=[],
        )
        base.update(overrides)
        device = SimpleNamespace(
            id='dev1',
            name='cam1',
            source='rtsp://127.0.0.1/stream',
            ai_rtmp_stream='',
        )
        base['devices'] = [device]
        return SimpleNamespace(**base)

    def test_contract_sections_present(self):
        from app.services import runtime_config_service as rcs

        task = self._minimal_task()
        with unittest.mock.patch.object(rcs, '_regions_ini_block', return_value=''):
            with unittest.mock.patch.object(
                rcs, '_resolve_model_paths', return_value=('model.onnx', 'coco.names')
            ):
                with unittest.mock.patch('os.path.isfile', return_value=True):
                    path = rcs.generate_runtime_ini(task, '/tmp/runtime.log', write_local=False)
        content = getattr(rcs.generate_runtime_ini, 'last_content', '')
        self.assertIn('[tracking]', content)
        self.assertIn('[hook]', content)
        self.assertIn('face_detection_enabled=true', content)
        self.assertIn('plate_detection_enabled=false', content)
        self.assertIn('[unsupported]', content)
        # CAP-TRACKING / CAP-FACE-MATCH are implemented (cpp / VIDEO) — must NOT be unsupported
        self.assertNotIn('CAP-TRACKING=true', content)
        self.assertNotIn('CAP-FACE-MATCH=true', content)
        self.assertNotIn('CAP-FACE-FILTER=true', content)
        self.assertTrue(path.endswith('task_99001.ini'))

    def test_snap_uses_frame_skip_not_extract_interval(self):
        from app.services import runtime_config_service as rcs

        task = self._minimal_task(task_type='snap', extract_interval=12, frame_skip=3)
        with unittest.mock.patch.object(rcs, '_regions_ini_block', return_value=''):
            with unittest.mock.patch.object(
                rcs, '_resolve_model_paths', return_value=('model.onnx', 'coco.names')
            ):
                with unittest.mock.patch('os.path.isfile', return_value=True):
                    rcs.generate_runtime_ini(task, '/tmp/runtime.log', write_local=False)
        content = getattr(rcs.generate_runtime_ini, 'last_content', '')
        m = re.search(r'\[ai\][\s\S]*?frame_skip=(\d+)', content)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), '3')


if __name__ == '__main__':
    unittest.main()
