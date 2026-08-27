"""VIDEO MinIO 兼容代理的流式 Range 测试。"""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask
from werkzeug.test import Client
from werkzeug.wrappers import Response

from app.blueprints.minio_proxy import minio_proxy_bp


class TestVideoMinioProxyRange(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(minio_proxy_bp)
        self.client = Client(app, Response)

    def _client(self, content_type='video/mp4', size=10):
        body = MagicMock()
        body.read.return_value = b'2345'
        client = MagicMock()
        client.bucket_exists.return_value = True
        client.stat_object.return_value = SimpleNamespace(content_type=content_type, size=size)
        client.get_object.return_value = body
        return client, body

    def test_range_returns_partial_content_without_buffering_whole_object(self):
        minio_client, body = self._client()
        with patch('app.utils.service_urls.minio_storage_enabled', return_value=True), patch(
            'app.blueprints.minio_proxy.ModelService.get_minio_client', return_value=minio_client
        ):
            response = self.client.get(
                '/api/v1/buckets/record-space/objects/download',
                query_string={'prefix': 'device/clip.mp4'},
                headers={'Range': 'bytes=2-5'},
            )

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response.data, b'2345')
        self.assertEqual(response.headers['Content-Range'], 'bytes 2-5/10')
        self.assertEqual(response.headers['Accept-Ranges'], 'bytes')
        minio_client.get_object.assert_called_once_with(
            'record-space', 'device/clip.mp4', offset=2, length=4
        )
        body.close.assert_called_once_with()
        body.release_conn.assert_called_once_with()

    def test_unsatisfied_range_returns_416(self):
        minio_client, _ = self._client()
        with patch('app.utils.service_urls.minio_storage_enabled', return_value=True), patch(
            'app.blueprints.minio_proxy.ModelService.get_minio_client', return_value=minio_client
        ):
            response = self.client.get(
                '/api/v1/buckets/record-space/objects/download',
                query_string={'prefix': 'device/clip.mp4'},
                headers={'Range': 'bytes=20-30'},
            )

        self.assertEqual(response.status_code, 416)
        self.assertEqual(response.headers['Content-Range'], 'bytes */10')
        minio_client.get_object.assert_not_called()

    def test_head_reads_metadata_only(self):
        minio_client, _ = self._client(size=100)
        with patch('app.utils.service_urls.minio_storage_enabled', return_value=True), patch(
            'app.blueprints.minio_proxy.ModelService.get_minio_client', return_value=minio_client
        ):
            response = self.client.head(
                '/api/v1/buckets/record-space/objects/download',
                query_string={'prefix': 'device/clip.mp4'},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Length'], '100')
        minio_client.get_object.assert_not_called()


if __name__ == '__main__':
    unittest.main()
