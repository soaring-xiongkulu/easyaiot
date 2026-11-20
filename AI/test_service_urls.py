"""AI service_urls 与 local_storage 单元测试。"""
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from app.utils.service_urls import is_mini_deploy_profile, minio_storage_enabled
from app.services.local_storage_service import (
    build_minio_download_url,
    local_object_path,
    materialize_seed_object,
    migrate_seed_data_to_local_storage,
    read_local_object,
    save_local_object,
)


class TestAiServiceUrls(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_mini_profile_disables_minio(self):
        with patch.dict(os.environ, {'EASYAIOT_DEPLOY_PROFILE': 'mini'}, clear=True):
            self.assertTrue(is_mini_deploy_profile())
            self.assertFalse(minio_storage_enabled())

    def test_mini_profile_can_explicitly_enable_minio(self):
        with patch.dict(os.environ, {
            'EASYAIOT_DEPLOY_PROFILE': 'mini',
            'MINIO_ENABLED': 'true',
        }, clear=True):
            self.assertTrue(is_mini_deploy_profile())
            self.assertTrue(minio_storage_enabled())

    def test_standard_profile_enables_minio_even_with_mini_gateway_port(self):
        with patch.dict(os.environ, {
            'EASYAIOT_DEPLOY_PROFILE': 'standard',
            'GATEWAY_URL': 'http://localhost:48099',
        }, clear=True):
            self.assertFalse(is_mini_deploy_profile())
            self.assertTrue(minio_storage_enabled())


class TestLocalStorage(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.copy()
        self._tmpdir = tempfile.mkdtemp()
        self._seed_root = os.path.join(self._tmpdir, 'minio_seed')
        self._local_root = os.path.join(self._tmpdir, 'local-storage')

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _env_patch(self):
        return patch.dict(os.environ, {
            'EASYAIOT_DEPLOY_PROFILE': 'mini',
            'LOCAL_STORAGE_ROOT': self._local_root,
            'MINIO_SEED_DATA_ROOT': self._seed_root,
        }, clear=True)

    def _write_seed_object(self, bucket: str, key: str, content: bytes) -> None:
        path = os.path.join(self._seed_root, bucket, *key.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(content)

    def test_save_and_read_local_object(self):
        with self._env_patch():
            src = os.path.join(self._tmpdir, 'src.png')
            with open(src, 'wb') as handle:
                handle.write(b'png-data')
            ok, err = save_local_object('models', 'images/test.png', src)
            self.assertTrue(ok, err)
            content, ctype, read_err = read_local_object('models', 'images/test.png')
            self.assertIsNone(read_err)
            self.assertEqual(content, b'png-data')
            url = build_minio_download_url('models', 'images/test.png')
            self.assertIn('/api/v1/buckets/models/objects/download', url)

    def test_materialize_seed_object(self):
        with self._env_patch():
            self._write_seed_object('models', 'images/demo.png', b'from-seed')
            dest = local_object_path('models', 'images/demo.png')
            self.assertTrue(materialize_seed_object('models', 'images/demo.png', dest))
            with open(dest, 'rb') as handle:
                self.assertEqual(handle.read(), b'from-seed')

    def test_read_local_object_lazy_loads_from_seed(self):
        with self._env_patch():
            self._write_seed_object('models', 'images/lazy.png', b'lazy-load')
            content, _, read_err = read_local_object('models', 'images/lazy.png')
            self.assertIsNone(read_err)
            self.assertEqual(content, b'lazy-load')
            self.assertTrue(os.path.isfile(local_object_path('models', 'images/lazy.png')))

    def test_migrate_seed_data_to_local_storage(self):
        with self._env_patch():
            self._write_seed_object('models', 'images/a.png', b'a')
            self._write_seed_object('models', 'images/b.png', b'b')
            copied, skipped = migrate_seed_data_to_local_storage(buckets=['models'])
            self.assertEqual(copied, 2)
            self.assertEqual(skipped, 0)
            copied2, skipped2 = migrate_seed_data_to_local_storage(buckets=['models'])
            self.assertEqual(copied2, 0)
            self.assertEqual(skipped2, 2)


if __name__ == '__main__':
    unittest.main()
