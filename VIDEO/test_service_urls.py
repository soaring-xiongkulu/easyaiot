"""service_urls 单元测试。"""
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from app.utils.service_urls import (
    SHANGHAI_TZ,
    epoch_to_shanghai_datetime,
    is_mini_deploy_profile,
    minio_storage_enabled,
    now_shanghai_naive,
    resolve_alert_hook_url,
    shanghai_isoformat,
    should_use_gateway_for_video_api,
    is_local_filesystem_path,
    build_alert_image_api_url,
    build_snap_image_api_url,
)


class TestServiceUrls(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_mini_profile_uses_direct_video_api(self):
        with patch.dict(os.environ, {
            'EASYAIOT_DEPLOY_PROFILE': 'mini',
            'GATEWAY_URL': 'http://localhost:48099',
            'VIDEO_SERVICE_PORT': '6000',
        }, clear=True):
            self.assertTrue(is_mini_deploy_profile())
            self.assertFalse(should_use_gateway_for_video_api())

    def test_gateway_port_48099_without_profile_is_mini(self):
        with patch.dict(os.environ, {
            'GATEWAY_URL': 'http://localhost:48099',
            'VIDEO_SERVICE_PORT': '6000',
        }, clear=True):
            self.assertTrue(is_mini_deploy_profile())

    def test_standard_profile_not_mini_with_stale_gateway_port(self):
        with patch.dict(os.environ, {
            'EASYAIOT_DEPLOY_PROFILE': 'standard',
            'GATEWAY_URL': 'http://localhost:48099',
            'VIDEO_SERVICE_PORT': '6000',
        }, clear=True):
            self.assertFalse(is_mini_deploy_profile())
            self.assertTrue(minio_storage_enabled())
            self.assertTrue(should_use_gateway_for_video_api())

    def test_full_gateway_uses_admin_api_prefix(self):
        with patch.dict(os.environ, {
            'GATEWAY_URL': 'http://gateway.example.com:48080',
            'VIDEO_SERVICE_PORT': '6000',
        }, clear=True):
            self.assertFalse(is_mini_deploy_profile())
            self.assertTrue(should_use_gateway_for_video_api())

    def test_alert_hook_url_helper_still_resolvable_but_unused(self):
        """resolve_alert_hook_url 保留给遗留脚本；正式事件面已无 /video/alert/hook。"""
        with patch.dict(os.environ, {
            'ALERT_HOOK_URL': 'http://custom:7000/hook',
            'GATEWAY_URL': 'http://localhost:48099',
        }, clear=True):
            self.assertEqual(resolve_alert_hook_url(), 'http://custom:7000/hook')

    def test_mini_profile_enables_minio_when_unified(self):
        with patch.dict(os.environ, {
            'EASYAIOT_DEPLOY_PROFILE': 'mini',
            'GATEWAY_URL': 'http://localhost:48080',
            'MINIO_ENABLED': 'true',
        }, clear=True):
            self.assertTrue(is_mini_deploy_profile())
            self.assertTrue(minio_storage_enabled())

    def test_minio_enabled_override(self):
        with patch.dict(os.environ, {
            'EASYAIOT_DEPLOY_PROFILE': 'mini',
            'MINIO_ENABLED': 'true',
        }, clear=True):
            self.assertTrue(minio_storage_enabled())

    def test_local_filesystem_path_detection(self):
        self.assertTrue(is_local_filesystem_path('/data/snaps/a.jpg'))
        self.assertFalse(is_local_filesystem_path('/api/v1/buckets/x'))
        self.assertFalse(is_local_filesystem_path('/video/alert/image?path=x'))

    def test_build_media_api_urls(self):
        self.assertIn('/video/alert/image?path=', build_alert_image_api_url('/data/a.jpg'))
        self.assertEqual(
            build_snap_image_api_url(3, 'dev1/a.jpg'),
            '/video/snap/space/3/image/dev1/a.jpg',
        )

    def test_epoch_to_shanghai_datetime(self):
        ts = datetime(2026, 7, 9, 15, 29, 0, tzinfo=SHANGHAI_TZ).timestamp()
        aware = epoch_to_shanghai_datetime(ts)
        self.assertEqual(aware.tzinfo, SHANGHAI_TZ)
        self.assertEqual(aware.strftime('%Y-%m-%d %H:%M:%S'), '2026-07-09 15:29:00')

    def test_shanghai_isoformat_from_naive_wall_clock(self):
        naive = datetime(2026, 7, 9, 15, 29, 0)
        self.assertEqual(shanghai_isoformat(naive), '2026-07-09T15:29:00+08:00')

    def test_now_shanghai_naive_matches_fixed_clock(self):
        fixed_now = datetime(2026, 7, 9, 15, 29, 0, tzinfo=SHANGHAI_TZ)
        with patch('app.utils.service_urls.datetime') as mock_dt:
            mock_dt.now.return_value = fixed_now
            self.assertEqual(now_shanghai_naive(), datetime(2026, 7, 9, 15, 29, 0))

    def test_shanghai_isoformat_from_utc_aware(self):
        utc = datetime(2026, 7, 9, 7, 29, 0, tzinfo=timezone.utc)
        self.assertEqual(shanghai_isoformat(utc), '2026-07-09T15:29:00+08:00')


if __name__ == '__main__':
    unittest.main()
