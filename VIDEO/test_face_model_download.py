"""人脸模型断点下载单元测试"""
import os
import tempfile
import unittest
import zipfile
from unittest import mock

from app.utils import face_model_download as fmd


class TestFaceModelDownloadHelpers(unittest.TestCase):
    def test_build_status_shows_resumable_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            model_path = os.path.join(tmp, 'face_rec.onnx')
            zip_path = os.path.join(tmp, 'buffalo_l.zip.downloading')
            with open(zip_path, 'wb') as f:
                f.write(b'x' * (50 * 1024 * 1024))

            with mock.patch.object(fmd, 'FACE_MATCH_MODEL_PATH', model_path), mock.patch.object(
                fmd, '_state', {
                    'status': 'error',
                    'stage': 'error',
                    'progress': 0,
                    'downloaded_bytes': 0,
                    'total_bytes': fmd.ESTIMATED_ZIP_SIZE_BYTES,
                    'error': 'network error',
                }
            ):
                status = fmd.get_face_rec_model_status()

            self.assertFalse(status['exists'])
            self.assertTrue(status['resumable'])
            self.assertEqual(status['downloaded_bytes'], 50 * 1024 * 1024)
            self.assertGreater(status['progress'], 0)

    def test_prepare_model_target_clears_nonempty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            model_path = os.path.join(tmp, 'face_rec.onnx')
            os.makedirs(model_path)
            with open(os.path.join(model_path, 'stale'), 'wb') as f:
                f.write(b'x')
            with mock.patch.object(fmd, 'FACE_MATCH_MODEL_PATH', model_path):
                fmd._prepare_model_target()
            self.assertFalse(os.path.exists(model_path))

    def test_prepare_model_target_clears_downloading_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            model_path = os.path.join(tmp, 'face_rec.onnx')
            downloading_path = f'{model_path}.downloading'
            os.makedirs(downloading_path)
            with mock.patch.object(fmd, 'FACE_MATCH_MODEL_PATH', model_path):
                fmd._prepare_model_target()
            self.assertFalse(os.path.exists(downloading_path))

    def test_extract_and_replace_clears_target_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            model_path = os.path.join(tmp, 'face_rec.onnx')
            detect_path = os.path.join(tmp, 'scrfd_10g.onnx')
            zip_path = os.path.join(tmp, 'buffalo_l.zip')
            onnx_member = os.path.join(tmp, 'w600k_r50.onnx')
            detect_member = os.path.join(tmp, 'det_10g.onnx')
            with open(onnx_member, 'wb') as f:
                f.write(b'0' * 1024)
            with open(detect_member, 'wb') as f:
                f.write(b'1' * 1024)
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.write(onnx_member, arcname='w600k_r50.onnx')
                zf.write(detect_member, arcname='det_10g.onnx')
            os.makedirs(model_path)
            onnx_partial = f'{model_path}.downloading'

            with mock.patch.object(fmd, 'FACE_MATCH_MODEL_PATH', model_path), mock.patch.object(
                fmd, 'FACE_DETECT_MODEL_PATH', detect_path
            ), mock.patch.object(
                fmd, '_zip_partial_path', return_value=zip_path
            ), mock.patch.object(
                fmd, '_onnx_partial_path', return_value=onnx_partial
            ), mock.patch.object(fmd, '_is_zip_complete', return_value=True):
                fmd._do_download()

            self.assertTrue(os.path.isfile(model_path))
            self.assertGreater(os.path.getsize(model_path), 0)
            self.assertTrue(os.path.isfile(detect_path))
            self.assertGreater(os.path.getsize(detect_path), 0)
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, 'buffalo_l.zip')
            onnx_path = os.path.join(tmp, 'w600k_r50.onnx')
            with open(onnx_path, 'wb') as f:
                f.write(b'0' * 1024)
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.write(onnx_path, arcname='w600k_r50.onnx')
            self.assertTrue(fmd._is_zip_complete(zip_path))

    def test_download_resumes_with_range_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            model_path = os.path.join(tmp, 'face_rec.onnx')
            zip_path = os.path.join(tmp, 'buffalo_l.zip.downloading')
            existing = b'a' * (20 * 1024 * 1024)
            with open(zip_path, 'wb') as f:
                f.write(existing)

            captured = {}

            class FakeResponse:
                status = 206
                headers = {
                    'Content-Length': str(len(existing)),
                    'Content-Range': f'bytes {len(existing)}-{len(existing) * 2 - 1}/{len(existing) * 2}',
                }

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

                def getcode(self):
                    return 206

                def read(self, size=-1):
                    if not hasattr(self, '_sent'):
                        self._sent = True
                        return existing
                    return b''

            def fake_urlopen(req, timeout=0):
                captured['range'] = req.headers.get('Range')
                return FakeResponse()

            with mock.patch.object(fmd, 'FACE_MATCH_MODEL_PATH', model_path), mock.patch(
                'urllib.request.urlopen', side_effect=fake_urlopen
            ):
                fmd._download_with_progress('http://example.com/buffalo_l.zip', zip_path)

            self.assertEqual(captured.get('range'), f'bytes={len(existing)}-')
            self.assertEqual(os.path.getsize(zip_path), len(existing) * 2)


if __name__ == '__main__':
    unittest.main()
