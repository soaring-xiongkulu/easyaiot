"""模型权重对象路径解析（_resolve_object_ref_candidates）回归测试。

覆盖 issue：model_path/onnx_model_path 存纯对象键（如 yolo/yolov8/onnx/x.onnx）
时，首段被误当桶名导致 NoSuchBucket（Web 界面报“MinIO存储桶不存在”）。
"""
import unittest

from app.services.runtime_config_service import _resolve_object_ref_candidates


class TestResolveObjectRefCandidates(unittest.TestCase):
    def test_full_download_url_keeps_bucket_and_key(self):
        ref = '/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/onnx/m.onnx'
        self.assertEqual(
            _resolve_object_ref_candidates(ref),
            [('models', 'yolo/yolov8/onnx/m.onnx')],
        )

    def test_full_download_url_with_other_bucket(self):
        ref = '/api/v1/buckets/export-bucket/objects/download?prefix=model_3/onnx/model.onnx'
        self.assertEqual(
            _resolve_object_ref_candidates(ref),
            [('export-bucket', 'model_3/onnx/model.onnx')],
        )

    def test_known_bucket_prefix_unchanged(self):
        self.assertEqual(
            _resolve_object_ref_candidates('models/yolo/yolov8/m.pt'),
            [('models', 'yolo/yolov8/m.pt')],
        )

    def test_exports_prefix_maps_to_export_bucket(self):
        candidates = _resolve_object_ref_candidates('exports/model_3/onnx/model.onnx')
        self.assertEqual(candidates[0], ('export-bucket', 'exports/model_3/onnx/model.onnx'))
        self.assertEqual(candidates[1], ('exports', 'model_3/onnx/model.onnx'))

    def test_bare_object_key_defaults_to_models_bucket_first(self):
        # 纯对象键：models 桶候选优先，原首段解释保留兜底
        self.assertEqual(
            _resolve_object_ref_candidates('yolo/yolov8/onnx/xxx.onnx'),
            [('models', 'yolo/yolov8/onnx/xxx.onnx'), ('yolo', 'yolov8/onnx/xxx.onnx')],
        )

    def test_single_segment_falls_back_to_models_bucket(self):
        self.assertEqual(
            _resolve_object_ref_candidates('weights.onnx'),
            [('models', 'weights.onnx')],
        )

    def test_absolute_path_and_http_ref_rejected(self):
        self.assertEqual(_resolve_object_ref_candidates('/data/models/m.onnx'), [])
        self.assertEqual(_resolve_object_ref_candidates('http://x/m.onnx'), [])
        self.assertEqual(_resolve_object_ref_candidates(''), [])
        self.assertEqual(_resolve_object_ref_candidates(None), [])


if __name__ == '__main__':
    unittest.main()
