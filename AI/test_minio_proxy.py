"""MinIO download proxy response header tests."""
import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.parse import unquote

from flask import Flask
from minio.error import S3Error
from werkzeug.test import Client
from werkzeug.wrappers import Response

from app.blueprints.minio_proxy import minio_proxy_bp


def _s3_error(code):
    """S3Error 的签名为 (response, code, message, ...)，注意首个参数不是 code。"""
    return S3Error(None, code, 'missing', 'resource', 'request-id', 'host-id')


class TestMinioProxy(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(minio_proxy_bp)
        self.client = Client(self.app, Response)

    def assert_unicode_filename(self, response, disposition, filename):
        header = response.headers['Content-Disposition']
        header.encode('latin-1', 'strict')
        self.assertTrue(header.startswith(f'{disposition}; '), header)
        self.assertIn('filename="download.jpg"', header)

        marker = "filename*=UTF-8''"
        self.assertIn(marker, header)
        encoded_filename = header.split(marker, 1)[1]
        self.assertEqual(unquote(encoded_filename), filename)

    def test_downloads_minio_object_with_chinese_filename(self):
        content = b'jpeg-data'
        object_key = 'nested/path/中文封面.jpg'
        minio_response = MagicMock()
        minio_response.read.return_value = content
        minio_client = MagicMock()
        minio_client.bucket_exists.return_value = True
        minio_client.stat_object.return_value = SimpleNamespace(content_type='image/jpeg', size=len(content))
        minio_client.get_object.return_value = minio_response

        with patch(
            'app.utils.service_urls.minio_storage_enabled', return_value=True
        ), patch(
            'app.blueprints.minio_proxy.ModelService.get_minio_client',
            return_value=minio_client,
        ):
            response = self.client.get(
                '/api/v1/buckets/snap-space/objects/download',
                query_string={'prefix': object_key},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, content)
        self.assertEqual(response.content_type, 'image/jpeg')
        self.assert_unicode_filename(response, 'inline', '中文封面.jpg')
        minio_client.get_object.assert_called_once_with(
            'snap-space', object_key, offset=0, length=len(content)
        )
        minio_response.close.assert_called_once_with()
        minio_response.release_conn.assert_called_once_with()

    def test_downloads_local_object_with_chinese_filename(self):
        content = b'local-image'
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = Path(tmpdir) / '中文封面.jpg'
            local_path.write_bytes(content)
            with patch(
                'app.utils.service_urls.minio_storage_enabled', return_value=False
            ), patch(
                'app.services.local_storage_service.ensure_local_object',
                return_value=str(local_path),
            ):
                response = self.client.get(
                    '/api/v1/buckets/snap-space/objects/download',
                    query_string={'prefix': '中文封面.jpg'},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, content)
        self.assertEqual(response.content_type, 'image/jpeg')
        self.assert_unicode_filename(response, 'inline', '中文封面.jpg')

    def test_preserves_ascii_filename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = Path(tmpdir) / 'cover.jpg'
            local_path.write_bytes(b'image')
            with patch(
                'app.utils.service_urls.minio_storage_enabled', return_value=False
            ), patch(
                'app.services.local_storage_service.ensure_local_object',
                return_value=str(local_path),
            ):
                response = self.client.get(
                    '/api/v1/buckets/snap-space/objects/download',
                    query_string={'prefix': 'cover.jpg'},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers['Content-Disposition'],
            'inline; filename="cover.jpg"',
        )

    def test_range_request_streams_only_requested_bytes(self):
        content = b'0123456789'
        minio_response = MagicMock()
        minio_response.read.return_value = content[2:6]
        minio_client = MagicMock()
        minio_client.bucket_exists.return_value = True
        minio_client.stat_object.return_value = SimpleNamespace(content_type='video/mp4', size=len(content))
        minio_client.get_object.return_value = minio_response

        with patch('app.utils.service_urls.minio_storage_enabled', return_value=True), patch(
            'app.blueprints.minio_proxy.ModelService.get_minio_client', return_value=minio_client
        ):
            response = self.client.get(
                '/api/v1/buckets/record-space/objects/download',
                query_string={'prefix': 'clip.mp4'},
                headers={'Range': 'bytes=2-5'},
            )

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response.data, b'2345')
        self.assertEqual(response.headers['Content-Range'], 'bytes 2-5/10')
        self.assertEqual(response.headers['Accept-Ranges'], 'bytes')
        minio_client.get_object.assert_called_once_with(
            'record-space', 'clip.mp4', offset=2, length=4
        )

    def test_head_does_not_open_object_body(self):
        minio_client = MagicMock()
        minio_client.bucket_exists.return_value = True
        minio_client.stat_object.return_value = SimpleNamespace(content_type='video/mp4', size=100)

        with patch('app.utils.service_urls.minio_storage_enabled', return_value=True), patch(
            'app.blueprints.minio_proxy.ModelService.get_minio_client', return_value=minio_client
        ):
            response = self.client.head(
                '/api/v1/buckets/record-space/objects/download',
                query_string={'prefix': 'clip.mp4'},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Length'], '100')
        minio_client.get_object.assert_not_called()

    def _make_local_object(self, tmpdir, name, content):
        local_path = Path(tmpdir) / name
        local_path.write_bytes(content)
        return str(local_path)

    def test_bucket_missing_falls_back_to_local(self):
        content = b'seed-model'
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = self._make_local_object(tmpdir, 'yolov11.pt', content)
            minio_client = MagicMock()
            minio_client.bucket_exists.return_value = False
            with patch(
                'app.utils.service_urls.minio_storage_enabled', return_value=True
            ), patch(
                'app.blueprints.minio_proxy.ModelService.get_minio_client',
                return_value=minio_client,
            ), patch(
                'app.services.local_storage_service.ensure_local_object',
                return_value=local_path,
            ):
                response = self.client.get(
                    '/api/v1/buckets/models/objects/download',
                    query_string={'prefix': 'yolo/yolov11/yolov11.pt'},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, content)
        self.assertEqual(response.headers['Accept-Ranges'], 'bytes')
        minio_client.get_object.assert_not_called()

    def test_missing_object_falls_back_to_local(self):
        content = b'seed-onnx'
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = self._make_local_object(tmpdir, 'yolov8.onnx', content)
            minio_client = MagicMock()
            minio_client.bucket_exists.return_value = True
            minio_client.stat_object.side_effect = _s3_error('NoSuchKey')
            with patch(
                'app.utils.service_urls.minio_storage_enabled', return_value=True
            ), patch(
                'app.blueprints.minio_proxy.ModelService.get_minio_client',
                return_value=minio_client,
            ), patch(
                'app.services.local_storage_service.ensure_local_object',
                return_value=local_path,
            ):
                response = self.client.head(
                    '/api/v1/buckets/models/objects/download',
                    query_string={'prefix': 'yolo/yolov8/onnx/yolov8.onnx'},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Accept-Ranges'], 'bytes')
        minio_client.get_object.assert_not_called()

    def test_missing_bucket_on_stat_falls_back_to_local(self):
        content = b'seed-pt'
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = self._make_local_object(tmpdir, 'best.pt', content)
            minio_client = MagicMock()
            minio_client.bucket_exists.return_value = True
            minio_client.stat_object.side_effect = _s3_error('NoSuchBucket')
            with patch(
                'app.utils.service_urls.minio_storage_enabled', return_value=True
            ), patch(
                'app.blueprints.minio_proxy.ModelService.get_minio_client',
                return_value=minio_client,
            ), patch(
                'app.services.local_storage_service.ensure_local_object',
                return_value=local_path,
            ):
                response = self.client.get(
                    '/api/v1/buckets/models/objects/download',
                    query_string={'prefix': 'yolo/best.pt'},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, content)

    def test_missing_object_without_local_copy_returns_404(self):
        minio_client = MagicMock()
        minio_client.bucket_exists.return_value = True
        minio_client.stat_object.side_effect = _s3_error('NoSuchKey')
        with patch(
            'app.utils.service_urls.minio_storage_enabled', return_value=True
        ), patch(
            'app.blueprints.minio_proxy.ModelService.get_minio_client',
            return_value=minio_client,
        ), patch(
            'app.services.local_storage_service.ensure_local_object',
            return_value=None,
        ):
            response = self.client.get(
                '/api/v1/buckets/models/objects/download',
                query_string={'prefix': 'yolo/gone.pt'},
            )

        self.assertEqual(response.status_code, 404)
        self.assertIn('对象不存在', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
