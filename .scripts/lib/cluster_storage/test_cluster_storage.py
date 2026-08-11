"""cluster_storage 模块单元测试。"""
import os
import sys
import unittest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_LIB_ROOT = os.path.join(_REPO_ROOT, '.scripts', 'lib')
for _p in (_LIB_ROOT,):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from cluster_storage import (  # noqa: E402
    apply_cluster_env_defaults,
    get_ai_datasets_dir,
    get_ai_models_dir,
    get_ai_train_dir,
    get_mount_root,
    get_playbacks_dir,
    get_snaps_dir,
    is_cluster_mode,
    resolve_container_path,
    verify_ceph_mount,
)


class ClusterStorageTest(unittest.TestCase):
    def setUp(self):
        self._saved = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._saved)

    def test_cluster_mode_defaults(self):
        os.environ['CLUSTER_MODE'] = 'true'
        os.environ.pop('MEDIA_HOST_DATA_ROOT', None)
        applied = apply_cluster_env_defaults(force=True)
        self.assertIn('MEDIA_HOST_DATA_ROOT', applied)
        self.assertEqual(get_mount_root(), '/mnt/easyaiot-media')
        self.assertEqual(get_playbacks_dir(), '/mnt/easyaiot-media/playbacks')
        self.assertEqual(get_snaps_dir(), '/mnt/easyaiot-media/snaps')

    def test_ai_paths_in_cluster_mode(self):
        os.environ['CLUSTER_MODE'] = 'true'
        apply_cluster_env_defaults(force=True)
        self.assertEqual(get_ai_datasets_dir(), '/mnt/easyaiot-media/ai/datasets')
        self.assertEqual(get_ai_models_dir(), '/mnt/easyaiot-media/ai/models')
        self.assertEqual(get_ai_train_dir(42), '/mnt/easyaiot-media/ai/train/train_42')

    def test_resolve_container_path(self):
        os.environ['MEDIA_HOST_DATA_ROOT'] = '/mnt/easyaiot-media'
        mapped = resolve_container_path('/data/playbacks/live/dev1/2026/01/01/123.flv')
        self.assertEqual(
            mapped,
            '/mnt/easyaiot-media/playbacks/live/dev1/2026/01/01/123.flv',
        )

    def test_standalone_mode(self):
        os.environ.pop('CLUSTER_MODE', None)
        os.environ.pop('MEDIA_HOST_DATA_ROOT', None)
        self.assertFalse(is_cluster_mode())

    def test_cluster_mode_rejects_unmounted_writable_dir(self):
        os.environ['CLUSTER_MODE'] = 'true'
        os.environ['MEDIA_HOST_DATA_ROOT'] = '/tmp/easyaiot-not-a-real-mount-xyz'
        # 目录不存在 → False
        self.assertFalse(verify_ceph_mount('/tmp/easyaiot-not-a-real-mount-xyz'))


if __name__ == '__main__':
    unittest.main()
