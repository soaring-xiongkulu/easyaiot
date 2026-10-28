from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from app.blueprints import camera


class CameraSnapshotTest(unittest.TestCase):
    def test_grab_frame_for_snapshot_skips_rtsp_startup_frames(self):
        expected = np.full((8, 12, 3), 37, dtype=np.uint8)
        calls = []

        def fake_capture(source):
            calls.append(source)
            return True, expected

        with patch.object(
            camera, "resolve_gb28181_source", side_effect=lambda source, logger=None: source
        ), patch.object(camera, "capture_rtsp_frame", side_effect=fake_capture):
            frame, error = camera.grab_frame_for_snapshot(
                SimpleNamespace(id="camera-1", source="rtsp://camera.local/live")
            )

        self.assertIsNone(error)
        self.assertIs(frame, expected)
        self.assertEqual(["rtsp://camera.local/live"], calls)

    def test_grab_frame_for_snapshot_reports_no_valid_rtsp_frame(self):
        with patch.object(
            camera, "resolve_gb28181_source", side_effect=lambda source, logger=None: source
        ), patch.object(camera, "capture_rtsp_frame", return_value=(False, None)):
            frame, error = camera.grab_frame_for_snapshot(
                SimpleNamespace(id="camera-1", source="rtsp://camera.local/live")
            )

        self.assertIsNone(frame)
        self.assertIn("有效帧", error)
        self.assertIn("灰屏", error)


if __name__ == "__main__":
    unittest.main()
