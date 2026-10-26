"""模型存储路径处理回归测试：桶名解析与入库规范化。

覆盖 issue：model_path 存纯对象键（如 yolo/yolov8/onnx/x.onnx）时，
首段被误当桶名导致下载/类别解析报“MinIO存储桶不存在”。
"""
import unittest

from app.blueprints.model import (
    _normalize_model_storage_path,
    resolve_minio_bucket_key,
)


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


class TestNormalizeModelStoragePath(unittest.TestCase):
    def test_bare_yolo_object_key_gets_models_prefix(self):
        self.assertEqual(
            _normalize_model_storage_path('yolo/yolov8/onnx/xxx.onnx'),
            'models/yolo/yolov8/onnx/xxx.onnx',
        )
        self.assertEqual(
            _normalize_model_storage_path('yolo/yolov11/best.pt'),
            'models/yolo/yolov11/best.pt',
        )

    def test_full_download_url_unchanged(self):
        ref = '/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/m.onnx'
        self.assertEqual(_normalize_model_storage_path(ref), ref)

    def test_known_bucket_prefix_unchanged(self):
        self.assertEqual(_normalize_model_storage_path('models/yolo/yolov8/m.pt'), 'models/yolo/yolov8/m.pt')
        self.assertEqual(_normalize_model_storage_path('exports/model_3/onnx/model.onnx'), 'exports/model_3/onnx/model.onnx')

    def test_local_paths_unchanged(self):
        # 本地相对/绝对路径承载本地文件语义（推理侧直接 os.path.join），不得改写
        self.assertEqual(_normalize_model_storage_path('data/datasets/3/best.pt'), 'data/datasets/3/best.pt')
        self.assertEqual(_normalize_model_storage_path('/opt/easyaiot/models/m.onnx'), '/opt/easyaiot/models/m.onnx')

    def test_single_segment_and_empty_unchanged(self):
        self.assertEqual(_normalize_model_storage_path('best.pt'), 'best.pt')
        self.assertEqual(_normalize_model_storage_path(''), '')
        self.assertEqual(_normalize_model_storage_path(None), '')


if __name__ == '__main__':
    unittest.main()
