"""当前版本 C++ 单模型能力与任务级输出流兼容性回归测试。"""
import unittest
from types import SimpleNamespace

from app.services.algorithm_task_service import (
    _fallback_multi_model_executor,
    _normalize_task_model_ids,
)
from app.services.runtime_config_service import _resolve_ai_rtmp_url


class TestRuntimeMultiModelCompatibility(unittest.TestCase):
    def test_cpp_multi_model_task_falls_back_to_python_worker(self):
        self.assertEqual(_fallback_multi_model_executor('cpp', [11, 22]), 'python')
        self.assertEqual(_fallback_multi_model_executor('runtime', '[11, 22]'), 'python')

    def test_cpp_single_model_task_stays_on_cpp_runtime(self):
        self.assertEqual(_fallback_multi_model_executor('cpp', [11]), 'cpp')
        self.assertEqual(_fallback_multi_model_executor(None, '[11]'), 'cpp')

    def test_python_multi_model_task_stays_on_python_worker(self):
        self.assertEqual(_fallback_multi_model_executor('python', [11, 22]), 'python')

    def test_model_ids_are_deduplicated_before_capability_check(self):
        self.assertEqual(_normalize_task_model_ids('[11, "11", 22]'), [11, 22])
        self.assertEqual(_fallback_multi_model_executor('cpp', '[11, "11"]'), 'cpp')

    def test_cpp_output_url_is_unique_per_task_on_same_camera(self):
        device = SimpleNamespace(
            id='camera-01',
            ai_rtmp_stream='rtmp://media.example/ai/camera-01',
        )
        task_a = SimpleNamespace(id=101, rtmp_output_url=None)
        task_b = SimpleNamespace(id=202, rtmp_output_url=None)

        url_a = _resolve_ai_rtmp_url(device, task_a)
        url_b = _resolve_ai_rtmp_url(device, task_b)

        self.assertEqual(url_a, 'rtmp://media.example/ai/t101_camera-01')
        self.assertEqual(url_b, 'rtmp://media.example/ai/t202_camera-01')
        self.assertNotEqual(url_a, url_b)


if __name__ == '__main__':
    unittest.main()
