"""芯片算法运行时选择（generic / RK3588）回归测试。"""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.services import runtime_config_service as rcs


def _write_executable(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('#!/bin/sh\nexit 0\n', encoding='utf-8')
    path.chmod(0o755)
    return path


class RuntimeTargetParsingTest(unittest.TestCase):
    def test_parse_supported_targets_and_aliases(self):
        self.assertEqual(rcs.parse_runtime_target('auto'), 'auto')
        self.assertEqual(rcs.parse_runtime_target(''), 'auto')
        self.assertEqual(rcs.parse_runtime_target('rk3588'), 'rk3588')
        self.assertEqual(rcs.parse_runtime_target('RKnN-RK3588'), 'rk3588')
        self.assertEqual(rcs.parse_runtime_target('runtime-rk3588'), 'rk3588')
        self.assertEqual(rcs.parse_runtime_target('generic'), 'generic')
        self.assertEqual(rcs.parse_runtime_target('onnx'), 'generic')

    def test_parse_unknown_target_fails_loudly(self):
        with self.assertRaises(ValueError):
            rcs.parse_runtime_target('nvidia-orin')

    def test_normalize_is_lenient_for_legacy_db_values(self):
        self.assertEqual(rcs.normalize_runtime_target('nvidia-orin'), 'auto')
        self.assertEqual(rcs.normalize_runtime_target(None), 'auto')

    def test_module_and_env_keys_are_target_specific(self):
        self.assertEqual(rcs.runtime_module_name('rk3588'), 'RUNTIME-RK3588')
        self.assertEqual(rcs.runtime_module_name('generic'), 'RUNTIME')
        self.assertEqual(rcs.runtime_bin_env_key('rk3588'), 'RUNTIME_RK3588_BIN')
        self.assertEqual(rcs.runtime_bin_env_key('generic'), 'RUNTIME_BIN')


class RuntimeTargetResolutionTest(unittest.TestCase):
    def test_explicit_task_target_wins_over_host(self):
        task = SimpleNamespace(runtime_target='rk3588')
        with patch.object(rcs, '_host_is_rk3588', return_value=False):
            self.assertEqual(rcs.resolve_runtime_target(task), 'rk3588')

    def test_requested_target_wins_over_task_and_env(self):
        task = SimpleNamespace(runtime_target='rk3588')
        with patch.dict(os.environ, {'EASYAIOT_RUNTIME_TARGET': 'rk3588'}, clear=True):
            self.assertEqual(rcs.resolve_runtime_target(task, 'generic'), 'generic')

    def test_auto_uses_env_target_before_chip_detection(self):
        with patch.dict(os.environ, {'EASYAIOT_RUNTIME_TARGET': 'rk3588'}, clear=True), patch.object(
            rcs, '_host_is_rk3588', return_value=False
        ):
            self.assertEqual(rcs.resolve_runtime_target(None, 'auto'), 'rk3588')

    def test_auto_detects_rk3588_from_device_tree(self):
        with tempfile.NamedTemporaryFile('w', delete=False) as fh:
            fh.write('rockchip,rk3588-evb7-v11\0rockchip,rk3588\0')
            probe_path = fh.name
        try:
            with patch.dict(os.environ, {}, clear=True), patch.object(
                rcs, '_HOST_CHIP_PROBE_PATHS', (probe_path,)
            ):
                self.assertTrue(rcs._host_is_rk3588())
                self.assertEqual(rcs.resolve_runtime_target(None, 'auto'), 'rk3588')
        finally:
            os.unlink(probe_path)

    def test_remote_placement_rejects_rk3588(self):
        with self.assertRaises(ValueError):
            rcs.resolve_remote_runtime_target(SimpleNamespace(runtime_target='rk3588'))
        self.assertEqual(
            rcs.resolve_remote_runtime_target(SimpleNamespace(runtime_target='auto')),
            'generic',
        )
        self.assertEqual(
            rcs.resolve_remote_runtime_target(SimpleNamespace(runtime_target='generic')),
            'generic',
        )


class RuntimeModelContractTest(unittest.TestCase):
    def test_rk3588_requires_models(self):
        with self.assertRaises(ValueError):
            rcs.validate_runtime_model_contract('rk3588', [])
        with self.assertRaises(ValueError):
            rcs.validate_runtime_model_contract('rk3588', None)

    def test_rk3588_rejects_incompatible_builtin_models(self):
        for model_id in (-1, -3):
            with self.assertRaises(ValueError):
                rcs.validate_runtime_model_contract('rk3588', [model_id])

    def test_rk3588_accepts_yolov8n_builtin_and_business_models(self):
        self.assertEqual(rcs.validate_runtime_model_contract('rk3588', [-2]), 'rk3588')
        self.assertEqual(rcs.validate_runtime_model_contract('rk3588', '[12, "13"]'), 'rk3588')

    def test_generic_does_not_apply_rknn_contract(self):
        self.assertEqual(rcs.validate_runtime_model_contract('generic', [-1]), 'generic')
        self.assertEqual(rcs.validate_runtime_model_contract('generic', []), 'generic')


class RuntimeTargetPathsTest(unittest.TestCase):
    def test_rk3588_env_does_not_poison_generic_runtime_bin(self):
        rk_bin = '/opt/easyaiot/RUNTIME-RK3588/build/RUNTIME'
        with patch.dict(os.environ, {'RUNTIME_BIN': '/opt/easyaiot/RUNTIME/build/RUNTIME'}, clear=True):
            rcs._remember_runtime_bin('rk3588', rk_bin)
            self.assertEqual(os.environ.get('RUNTIME_RK3588_BIN'), rk_bin)
            self.assertEqual(
                os.environ.get('RUNTIME_BIN'), '/opt/easyaiot/RUNTIME/build/RUNTIME'
            )

    def test_resolve_runtime_bin_never_falls_back_to_generic_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            generic_bin = _write_executable(Path(tmp) / 'generic' / 'RUNTIME')
            rk_bin = _write_executable(Path(tmp) / 'rk3588' / 'RUNTIME')
            with patch.dict(os.environ, {'RUNTIME_BIN': str(generic_bin)}, clear=True):
                resolved = rcs.resolve_runtime_bin(None, runtime_target='rk3588')
                self.assertNotEqual(resolved, str(generic_bin))
            with patch.dict(
                os.environ,
                {'RUNTIME_BIN': str(generic_bin), 'RUNTIME_RK3588_BIN': str(rk_bin)},
                clear=True,
            ):
                self.assertEqual(
                    rcs.resolve_runtime_bin(None, runtime_target='rk3588'), str(rk_bin)
                )

    def test_config_dir_is_target_specific(self):
        with tempfile.TemporaryDirectory() as generic_dir, tempfile.TemporaryDirectory() as rk_dir:
            with patch.dict(
                os.environ,
                {'RUNTIME_CONFIG_DIR': generic_dir, 'RUNTIME_RK3588_CONFIG_DIR': rk_dir},
                clear=True,
            ):
                self.assertEqual(rcs.runtime_config_dir('generic'), Path(generic_dir))
                self.assertEqual(rcs.runtime_config_dir('rk3588'), Path(rk_dir))

    def test_rk3588_library_path_excludes_generic_ort_cuda_paths(self):
        with patch.dict(
            os.environ,
            {'LD_LIBRARY_PATH': '/opt/easyaiot/RUNTIME/lib:/opt/easyaiot/ort-lib'},
            clear=True,
        ):
            lib_path = rcs.runtime_library_path_env('rk3588')
        self.assertNotIn('/RUNTIME/lib', lib_path)
        self.assertNotIn('ort-lib', lib_path)
        self.assertNotIn('runtime-conda-lib', lib_path)
        self.assertNotIn('cuda-lib', lib_path)

    def test_version_info_reports_hardware_only_for_rk3588(self):
        with tempfile.TemporaryDirectory() as tmp:
            rk_bin = _write_executable(Path(tmp) / 'RUNTIME-RK3588' / 'RUNTIME')
            with patch.dict(os.environ, {'RUNTIME_RK3588_BIN': str(rk_bin)}, clear=True):
                info = rcs.read_runtime_version_info(runtime_target='rk3588')
        self.assertEqual(info['target'], 'rk3588')
        self.assertEqual(info['module'], 'RUNTIME-RK3588')
        self.assertTrue(info['hardwareOnly'])
        self.assertTrue(info['ready'])
        self.assertEqual(info['binPath'], str(rk_bin))


class RknnRuntimeIniTest(unittest.TestCase):
    def _task(self):
        return SimpleNamespace(
            id=901,
            task_type='snap',
            model_ids='[-2]',
            model_names='rk',
            runtime_target='rk3588',
            alert_event_enabled=False,
            alert_class_names=None,
            detect_conf=0.5,
            alert_event_suppress_time=0,
            extract_interval=8,
            cron_expression='* * * * *',
            patrol_mode='pool',
            patrol_interval_sec=10,
            patrol_pool_size=4,
            devices=[SimpleNamespace(
                id='cam-rk',
                name='cam-rk',
                source='rtsp://127.0.0.1/live',
                ai_rtmp_stream='rtmp://media.example/ai/cam-rk',
            )],
        )

    def test_rk3588_ini_uses_rknn_and_npu_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            model_path = Path(tmp) / 'models' / 'yolov8n-rk3588-int8.rknn'
            model_path.parent.mkdir()
            model_path.write_bytes(b'rknn')
            names_path = model_path.parent / 'coco.names'
            names_path.write_text('person\n', encoding='utf-8')
            with patch.dict(
                os.environ, {'RUNTIME_RK3588_CONFIG_DIR': tmp}, clear=True
            ), patch.object(
                rcs,
                '_resolve_rknn_models_with_ids',
                return_value=[(-2, str(model_path), str(names_path))],
            ):
                paths = rcs.generate_runtime_inis(
                    self._task(), log_path=os.path.join(tmp, 'log'), write_local=True
                )
                content = Path(paths[0]).read_text(encoding='utf-8')
        self.assertIn('target=rk3588', content)
        self.assertIn(f'model_path={model_path}', content)
        self.assertIn('threads=3', content)
        self.assertIn('[rk3588]', content)
        self.assertIn('npu_workers=3', content)
        self.assertNotIn('prefer_gpu=', content)


if __name__ == '__main__':
    unittest.main()
