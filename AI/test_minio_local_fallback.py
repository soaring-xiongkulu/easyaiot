"""download_from_minio 对象存储缺失时回退本地存储的测试。"""
import os
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

from flask import Flask
from minio.error import S3Error

from app.services.minio_service import ModelService


def _s3_error(code):
    """S3Error 的签名为 (response, code, message, ...)，注意首个参数不是 code。"""
    return S3Error(None, code, 'missing', 'resource', 'request-id', 'host-id')


class TestMinioLocalFallback(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.logger.setLevel('CRITICAL')
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.addCleanup(self.ctx.pop)

        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.local_src = os.path.join(self.tmpdir.name, 'seed.pt')
        with open(self.local_src, 'wb') as fh:
            fh.write(b'model-weights')
        self.dest = os.path.join(self.tmpdir.name, 'dest', 'model.pt')

    def _run(self, client=None, enabled=True, local_result=None, local_side_effect=None):
        ctxs = [
            patch('app.utils.service_urls.minio_storage_enabled', return_value=enabled),
            patch(
                'app.services.local_storage_service.ensure_local_object',
                return_value=local_result,
                side_effect=local_side_effect,
            ),
        ]
        if client is not None:
            ctxs.append(
                patch.object(ModelService, 'get_minio_client', return_value=client)
            )
        with ExitStack() as stack:
            for ctx in ctxs:
                stack.enter_context(ctx)
            return ModelService.download_from_minio('models', 'yolo/x.pt', self.dest)

    def test_disabled_storage_copies_local_object(self):
        ok, err = self._run(enabled=False, local_result=self.local_src)

        self.assertTrue(ok)
        self.assertIsNone(err)
        with open(self.dest, 'rb') as fh:
            self.assertEqual(fh.read(), b'model-weights')

    def test_missing_key_in_object_store_falls_back_to_local(self):
        client = MagicMock()
        client.stat_object.side_effect = _s3_error('NoSuchKey')

        ok, err = self._run(client=client, local_result=self.local_src)

        self.assertTrue(ok)
        self.assertIsNone(err)
        client.fget_object.assert_not_called()
        with open(self.dest, 'rb') as fh:
            self.assertEqual(fh.read(), b'model-weights')

    def test_missing_bucket_in_object_store_falls_back_to_local(self):
        client = MagicMock()
        client.stat_object.side_effect = _s3_error('NoSuchBucket')

        ok, err = self._run(client=client, local_result=self.local_src)

        self.assertTrue(ok)
        self.assertIsNone(err)
        client.fget_object.assert_not_called()

    def test_missing_everywhere_returns_specific_error(self):
        client = MagicMock()
        client.stat_object.side_effect = _s3_error('NoSuchKey')

        ok, err = self._run(client=client, local_result=None)

        self.assertFalse(ok)
        self.assertEqual(err, 'Minio对象不存在: models/yolo/x.pt')
        self.assertFalse(os.path.exists(self.dest))

    def test_illegal_local_path_returns_reason(self):
        client = MagicMock()
        client.stat_object.side_effect = _s3_error('NoSuchKey')

        ok, err = self._run(client=client, local_side_effect=ValueError('../etc/passwd'))

        self.assertFalse(ok)
        self.assertIn('本地对象路径非法', err)

    def test_existing_object_uses_object_store_only(self):
        client = MagicMock()
        client.stat_object.return_value = object()

        def fake_fget_object(bucket, key, path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as fh:
                fh.write(b'from-s3')

        client.fget_object.side_effect = fake_fget_object

        ok, err = self._run(client=client, local_result=self.local_src)

        self.assertTrue(ok)
        self.assertIsNone(err)
        with open(self.dest, 'rb') as fh:
            self.assertEqual(fh.read(), b'from-s3')


if __name__ == '__main__':
    unittest.main()
