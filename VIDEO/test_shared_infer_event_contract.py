"""Python/C++/Go 共用 InferEvent fixture 的契约回归。"""
import json
import os
import unittest
from pathlib import Path

from app.utils.algo_mqtt_bus import build_infer_event


ROOT = Path(os.environ.get('EASYAIOT_CONTRACT_ROOT', Path(__file__).resolve().parents[1]))
FIXTURES = ROOT / 'testdata' / 'contracts'


class SharedInferEventContractTest(unittest.TestCase):
    def test_all_fixtures_are_valid_json_with_pixel_bboxes(self):
        paths = sorted(FIXTURES.glob('infer_*.json'))
        self.assertEqual(5, len(paths))
        for path in paths:
            with self.subTest(path=path.name):
                event = json.loads(path.read_text(encoding='utf-8'))
                self.assertEqual('infer_event.v1', event['schema'])
                self.assertGreater(event['frame_width'], 0)
                self.assertGreater(event['frame_height'], 0)
                for detection in event['detections']:
                    self.assertEqual(4, len(detection['bbox']))
                    self.assertGreaterEqual(detection['bbox'][2], detection['bbox'][0])
                    self.assertGreaterEqual(detection['bbox'][3], detection['bbox'][1])

    def test_python_builder_matches_multi_model_fixture_identity(self):
        fixture = json.loads((FIXTURES / 'infer_multi_model.json').read_text(encoding='utf-8'))
        event = build_infer_event(
            task_id=fixture['task_id'],
            task_type=fixture['task_type'],
            device_id=fixture['device_id'],
            frame_width=fixture['frame_width'],
            frame_height=fixture['frame_height'],
            model_ids=fixture['model_ids'],
            detections=fixture['detections'],
        )
        self.assertEqual([11, 12], event['model_ids'])
        self.assertEqual([11, 12], [item['model_id'] for item in event['detections']])
        self.assertEqual(fixture['detections'][0]['bbox'], event['detections'][0]['bbox'])

    def test_negative_default_and_missing_model_remain_distinguishable(self):
        negative = json.loads((FIXTURES / 'infer_negative_default.json').read_text(encoding='utf-8'))
        missing = json.loads((FIXTURES / 'infer_missing_detection_model.json').read_text(encoding='utf-8'))
        self.assertEqual(-1, negative['detections'][0]['model_id'])
        self.assertNotIn('model_id', missing['detections'][0])

    def test_cpp_producer_writes_business_model_id_and_does_not_filter_negatives(self):
        source = (ROOT / 'RUNTIME' / 'src' / 'Detech.cpp').read_text(encoding='utf-8')
        self.assertIn('detObj["model_id"] = det.model_id;', source)
        self.assertIn('d["model_id"] = det.model_id;', source)
        self.assertNotIn('det.model_id >= 0', source)
        self.assertNotIn('det.model_id > 0', source)


if __name__ == '__main__':
    unittest.main()
