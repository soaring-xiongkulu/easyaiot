"""resolve_minio_bucket_key 桶名解析回归测试。

覆盖 issue：model_path 存纯对象键（如 yolo/yolov8/onnx/x.onnx）时，
首段被误当桶名导致下载/类别解析报“MinIO存储桶不存在”。
"""
import unittest

from app.blueprints.model import resolve_minio_bucket_key


class TestResolveMinioBucketKey(unittest.TestCase):
    def test_full_download_url_keeps_bucket_and_key(self):
        self.assertEqual(
            resolve_minio_bucket_key('/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/m.onnx'),
            ('models', 'yolo/yolov8/onnx/m.onnx'),
        )

    def test_known_bucket_prefix_unchanged(self):
        self.assertEqual(
            resolve_minio_bucket_key('models/yolo/yolov8/m.pt'),
            ('models', 'yolo/yolov8/m.pt'),
        )
        self.assertEqual(
            resolve_minio_bucket_key('exports/model_3/onnx/model.onnx'),
            ('exports', 'model_3/onnx/model.onnx'),
        )

    def test_bare_object_key_defaults_to_models_bucket(self):
        self.assertEqual(
            resolve_minio_bucket_key('yolo/yolov8/onnx/xxx.onnx'),
            ('models', 'yolo/yolov8/onnx/xxx.onnx'),
        )

    def test_invalid_ref_returns_none(self):
        self.assertEqual(resolve_minio_bucket_key(''), (None, None))
        self.assertEqual(resolve_minio_bucket_key(None), (None, None))
        self.assertEqual(resolve_minio_bucket_key('best.pt'), (None, None))


if __name__ == '__main__':
    unittest.main()
