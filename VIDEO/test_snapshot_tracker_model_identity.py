import math
import sys
import types
import unittest

try:
    import numpy  # noqa: F401
except ImportError:
    sys.modules['numpy'] = types.SimpleNamespace(sqrt=math.sqrt)

from services.snapshot_algorithm_service.app.utils.tracker import SimpleTracker


class SnapshotTrackerModelIdentityTest(unittest.TestCase):
    def test_identical_boxes_from_different_models_keep_separate_tracks(self):
        tracker = SimpleTracker()
        detections = [
            {
                'model_id': 11,
                'bbox': [10, 10, 100, 100],
                'class_id': 0,
                'class_name': 'person',
                'confidence': 0.9,
            },
            {
                'model_id': 22,
                'bbox': [10, 10, 100, 100],
                'class_id': 0,
                'class_name': 'person',
                'confidence': 0.8,
            },
        ]

        tracked = tracker.update(detections, frame_number=1, current_time=1.0)

        self.assertEqual(2, len(tracked))
        self.assertEqual({11, 22}, {item['model_id'] for item in tracked})
        self.assertEqual(2, len({item['track_id'] for item in tracked}))


if __name__ == '__main__':
    unittest.main()
