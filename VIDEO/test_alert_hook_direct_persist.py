"""alert_hook mini 直连落库逻辑单元测试。"""
import os
import unittest
from unittest.mock import MagicMock, patch

from app.services import alert_hook_service as hook_mod
from app.utils.algorithm_task_identity import AmbiguousAlgorithmTaskError


class TestAlertHookDirectPersist(unittest.TestCase):
    def test_notification_channel_key_is_stable_and_channel_specific(self):
        email = {'method': 'email', 'template_id': 11}
        reordered_email = {'template_id': 11, 'method': 'email'}
        webhook = {'method': 'http', 'template_id': 11}

        self.assertEqual(
            hook_mod._notification_channel_key(email),
            hook_mod._notification_channel_key(reordered_email),
        )
        self.assertNotEqual(
            hook_mod._notification_channel_key(email),
            hook_mod._notification_channel_key(webhook),
        )

    def setUp(self):
        self._env = os.environ.copy()
        hook_mod._last_alert_event_kafka_time.clear()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_should_use_direct_persist_in_mini(self):
        with patch.dict(os.environ, {'EASYAIOT_DEPLOY_PROFILE': 'mini'}, clear=True):
            self.assertTrue(hook_mod._should_use_direct_alert_persist())

    def test_kafka_suppression_isolated_by_event_identity(self):
        with patch.object(hook_mod.time, 'time', return_value=100.0):
            first_person = hook_mod._should_suppress_alert_event_kafka(
                9, 'dev-1', 'realtime', 5, '1:person'
            )
            first_detection = hook_mod._should_suppress_alert_event_kafka(
                9, 'dev-1', 'realtime', 5, '32:detection'
            )
            repeated_person = hook_mod._should_suppress_alert_event_kafka(
                9, 'dev-1', 'realtime', 5, '1:person'
            )

        self.assertFalse(first_person)
        self.assertFalse(first_detection)
        self.assertTrue(repeated_person)

    def test_process_alert_hook_uses_direct_persist_in_mini(self):
        alert_data = {
            'object': 'chair',
            'event': '办公室设备',
            'device_id': 'dev-1',
            'device_name': 'CH1',
            'task_type': 'realtime',
            'time': '2026-06-20 12:00:00',
        }
        task = {
            'task_id': 1,
            'task_name': '办公室设备',
            'task_type': 'realtime',
            'face_detection_enabled': False,
            'plate_detection_enabled': False,
            'alert_event_suppress_time': 5,
        }
        with patch.dict(os.environ, {'EASYAIOT_DEPLOY_PROFILE': 'mini'}, clear=True):
            with patch.object(hook_mod, '_query_alert_event_task', return_value=task):
                with patch.object(hook_mod, '_query_alert_notification_config', return_value=None):
                    with patch.object(hook_mod, '_persist_alert_directly', return_value={'status': 'success', 'alert_id': 99, 'mode': 'direct_persist'}) as persist_mock:
                        result = hook_mod.process_alert_hook(alert_data)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['alert_id'], 99)
        persist_mock.assert_called_once()

    def test_process_alert_hook_uses_explicit_task_identity_for_suppression(self):
        alert_data = {
            'task_id': 202,
            'object': 'helmet',
            'event': '安全帽检测',
            'device_id': 'dev-1',
            'device_name': 'CH1',
            'task_type': 'realtime',
        }
        task = {
            'task_id': 202,
            'task_name': '安全帽检测',
            'task_type': 'realtime',
            'face_detection_enabled': False,
            'plate_detection_enabled': False,
            'alert_event_suppress_time': 5,
        }
        with patch.object(hook_mod, '_should_use_direct_alert_persist', return_value=False):
            with patch.object(hook_mod, '_query_alert_event_task', return_value=task) as query_mock:
                with patch.object(hook_mod, '_resolve_alert_event_suppress_seconds', return_value=5):
                    with patch.object(hook_mod, '_should_suppress_alert_event_kafka', return_value=True) as suppress_mock:
                        result = hook_mod.process_alert_hook(alert_data)

        self.assertEqual(result['status'], 'suppressed')
        query_mock.assert_called_once_with('dev-1', 'realtime', 202)
        suppress_mock.assert_called_once_with(202, 'dev-1', 'realtime', 5, 'unknown:helmet')

    def test_process_alert_hook_rejects_ambiguous_legacy_event(self):
        alert_data = {
            'object': 'person',
            'event': '人员检测',
            'device_id': 'dev-1',
            'device_name': 'CH1',
            'task_type': 'realtime',
        }
        with patch.object(hook_mod, '_should_use_direct_alert_persist', return_value=False):
            with patch.object(
                    hook_mod,
                    '_query_alert_event_task',
                    side_effect=AmbiguousAlgorithmTaskError('旧版消息缺少 task_id'),
            ):
                result = hook_mod.process_alert_hook(alert_data)

        self.assertEqual(result['status'], 'rejected')
        self.assertEqual(result['reason'], 'ambiguous_task')

    def test_schema_v2_rejects_model_not_owned_by_task(self):
        alert_data = {
            'schema_version': 2,
            'task_id': 202,
            'model_ids': [99],
            'detections': [{'model_id': 99}],
        }
        task = {'task_id': 202, 'model_ids': [11, 22]}

        result = hook_mod._validate_alert_model_ownership(alert_data, task)

        self.assertEqual(result['reason'], 'foreign_model')

    def test_schema_v2_accepts_models_owned_by_task(self):
        alert_data = {
            'schema_version': 2,
            'task_id': 202,
            'model_ids': [11, 22],
            'detections': [{'model_id': 11}, {'model_id': 22}],
        }
        task = {'task_id': 202, 'model_ids': [11, 22]}

        self.assertIsNone(hook_mod._validate_alert_model_ownership(alert_data, task))


if __name__ == '__main__':
    unittest.main()
