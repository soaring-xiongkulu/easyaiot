"""媒体路径允许根和目录逃逸测试。"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services.local_storage_service import local_object_path
from app.utils.media_path_security import resolve_allowed_media_file


class TestMediaPathSecurity(unittest.TestCase):
    def test_allows_file_under_configured_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            media_file = Path(tmpdir) / 'alerts' / 'a.jpg'
            media_file.parent.mkdir()
            media_file.write_bytes(b'image')
            with patch.dict(os.environ, {'ALERT_IMAGES_DIR': tmpdir}, clear=False):
                resolved = resolve_allowed_media_file(str(media_file))
        self.assertEqual(resolved, media_file.resolve())

    def test_rejects_file_outside_configured_root(self):
        with tempfile.TemporaryDirectory() as media_dir, tempfile.TemporaryDirectory() as other_dir:
            outside = Path(other_dir) / 'secret.txt'
            outside.write_text('secret')
            with patch.dict(
                os.environ,
                {
                    'ALERT_IMAGES_DIR': media_dir,
                    'EDGE_RECORDING_ROOT': media_dir,
                    'LOCAL_STORAGE_ROOT': media_dir,
                    'EASYAIOT_MEDIA_ROOT': media_dir,
                    'MEDIA_HOST_DATA_ROOT': media_dir,
                    'SRS_HOST_DATA_ROOT': media_dir,
                },
                clear=False,
            ):
                resolved = resolve_allowed_media_file(str(outside))
        self.assertIsNone(resolved)

    def test_local_object_path_rejects_parent_escape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {'LOCAL_STORAGE_ROOT': tmpdir}, clear=False):
                with self.assertRaises(ValueError):
                    local_object_path('bucket', '../../secret.txt')


if __name__ == '__main__':
    unittest.main()
