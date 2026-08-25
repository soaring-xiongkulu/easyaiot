"""C++ RUNTIME 多模型能力与任务级输出流兼容性回归测试。"""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.services.algorithm_task_service import _normalize_task_model_ids
from app.services.runtime_config_service import (
    _resolve_ai_rtmp_url,
    _resolve_model_paths,
    generate_runtime_inis,
)


class TestRuntimeMultiModelCompatibility(unittest.TestCase):
    def test_model_ids_are_deduplicated_and_ordered(self):
        self.assertEqual(_normalize_task_model_ids('[11, "11", 22]'), [11, 22])

    def test_resolve_model_paths_returns_all_models_in_order(self):
        task = SimpleNamespace(model_ids='[-1, -3]')
        pairs = _resolve_model_paths(task)
        self.assertEqual(len(pairs), 2)
        self.assertIn('yolo11n', pairs[0][0])
        self.assertIn('yolo26n', pairs[1][0])

    def test_resolve_model_paths_single_model_returns_single_pair(self):
        self.assertEqual(len(_resolve_model_paths(SimpleNamespace(model_ids='[-1]'))), 1)

    def test_cpp_task_ini_contains_every_model_key(self):
        task = SimpleNamespace(
            id=55,
            task_type='snap',
            model_ids='[-1, -3]',
            model_names='multi',
            alert_event_enabled=True,
            alert_class_names=None,
            detect_conf=0.5,
            alert_event_suppress_time=0,
            extract_interval=8,
            cron_expression='* * * * *',
            patrol_mode='pool',
            patrol_interval_sec=10,
            patrol_pool_size=4,
            devices=[SimpleNamespace(
                id='cam-01',
                name='cam',
                source='rtsp://127.0.0.1/live',
                ai_rtmp_stream='rtmp://media.example/ai/cam-01',
            )],
        )
        with tempfile.TemporaryDirectory() as cfg_dir:
            with patch.dict(os.environ, {'RUNTIME_CONFIG_DIR': cfg_dir}, clear=False):
                paths = generate_runtime_inis(task, log_path='', write_local=True)
                self.assertEqual(len(paths), 1)
                content = Path(paths[0]).read_text()
        # 主模型走 model_path / classes_path，其余模型走 model_path_<i> / classes_path_<i>
        self.assertIn('model_path=', content)
        self.assertIn('classes_path=', content)
        self.assertIn('model_path_1=', content)
        self.assertIn('classes_path_1=', content)
        self.assertNotIn('model_path_2=', content)

    def test_cpp_single_model_task_ini_has_no_multi_model_keys(self):
        task = SimpleNamespace(
            id=56,
            task_type='realtime',
            model_ids='[-1]',
            model_names='single',
            alert_event_enabled=True,
            alert_class_names=None,
            detect_conf=0.5,
            alert_event_suppress_time=0,
            extract_interval=8,
            cron_expression='',
            patrol_mode='pool',
            patrol_interval_sec=10,
            patrol_pool_size=4,
            devices=[SimpleNamespace(
                id='cam-02',
                name='cam',
                source='rtsp://127.0.0.1/live',
                ai_rtmp_stream='rtmp://media.example/ai/cam-02',
            )],
        )
        with tempfile.TemporaryDirectory() as cfg_dir:
            with patch.dict(os.environ, {'RUNTIME_CONFIG_DIR': cfg_dir}, clear=False):
                paths = generate_runtime_inis(task, log_path='', write_local=True)
                self.assertEqual(len(paths), 1)
                content = Path(paths[0]).read_text()
        self.assertIn('model_path=', content)
        self.assertNotIn('model_path_1=', content)

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
