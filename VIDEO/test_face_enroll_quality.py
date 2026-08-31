import unittest
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import numpy as np

from app.services.face_recognition_service import FaceRecognitionService


class FaceEnrollQualityTest(unittest.TestCase):
    def setUp(self):
        self.service = FaceRecognitionService.__new__(FaceRecognitionService)
        self.service._embed_crop = lambda crop: np.ones(512, dtype=np.float32)

    def test_no_detection_never_falls_back_to_whole_frame(self):
        image = np.full((480, 640, 3), 127, dtype=np.uint8)
        with patch.object(self.service, '_extract_faces', return_value=[]):
            result = self.service.extract_and_crop_largest_face(image)
        self.assertIsNone(result)

    def test_blurry_face_is_rejected(self):
        image = np.full((480, 640, 3), 127, dtype=np.uint8)
        face = SimpleNamespace(
            bbox=np.array([100, 100, 300, 300]), crop=image[100:300, 100:300],
            normed_embedding=np.ones(512), det_score=0.99, kps=np.zeros((5, 2)),
        )
        with patch.object(self.service, '_extract_faces', return_value=[face]):
            result = self.service.extract_and_crop_largest_face(image)
        self.assertIsNone(result)

    def test_clear_face_is_accepted_with_quality_metrics(self):
        image = np.full((480, 640, 3), 127, dtype=np.uint8)
        crop = image[100:300, 100:300]
        for offset in range(0, 200, 10):
            cv2.line(crop, (offset, 0), (199 - offset, 199), (0, 0, 0), 2)
        face = SimpleNamespace(
            bbox=np.array([100, 100, 300, 300]), crop=crop,
            normed_embedding=np.ones(512), det_score=0.99, kps=np.zeros((5, 2)),
        )
        with patch.object(self.service, '_extract_faces', return_value=[face]):
            result = self.service.extract_and_crop_largest_face(image)
        self.assertIsNotNone(result)
        self.assertGreater(result['quality']['blur_score'], 35)
        self.assertEqual(result['bbox'], [100, 100, 300, 300])


if __name__ == '__main__':
    unittest.main()
