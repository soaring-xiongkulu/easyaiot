"""任务级区域 HTTP API 状态码与响应契约测试。"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask

from app.blueprints import device_detection_region as api
from app.services.device_detection_region_service import RegionRevisionConflict


class DeviceDetectionRegionAPIContractTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)

    def call_replace(self, body):
        with self.app.test_request_context(json=body, method='PUT'):
            return api.replace_task_device_regions(7, 'cam-a')

    def test_batch_put_requires_expected_revision(self):
        response, status = self.call_replace({'regions': []})
        self.assertEqual(400, status)
        self.assertIn('expected_revision', response.get_json()['msg'])

    def test_batch_put_maps_revision_conflict_to_http_409(self):
        with patch.object(api, 'replace_device_regions', side_effect=RegionRevisionConflict('冲突')):
            response, status = self.call_replace({'expected_revision': 2, 'regions': []})
        self.assertEqual(409, status)
        self.assertEqual(409, response.get_json()['code'])

    def test_batch_put_maps_validation_failure_to_http_400(self):
        with patch.object(api, 'replace_device_regions', side_effect=ValueError('非法模型')):
            response, status = self.call_replace({'expected_revision': 2, 'regions': []})
        self.assertEqual(400, status)
        self.assertEqual('非法模型', response.get_json()['msg'])

    def test_batch_put_returns_revision_and_runtime_sync_status(self):
        region = SimpleNamespace(to_dict=lambda: {'id': 1, 'model_scope': 'selected', 'model_ids': [11]})
        with patch.object(api, 'replace_device_regions', return_value=([region], 3)) as replace, \
                patch.object(api, '_refresh_task_runtime', return_value='pending') as refresh:
            response = self.call_replace({'expected_revision': 2, 'regions': [{'region_name': 'A'}]})
        payload = response.get_json()
        self.assertEqual(0, payload['code'])
        self.assertEqual(3, payload['revision'])
        self.assertEqual('pending', payload['runtime_sync_status'])
        self.assertEqual([11], payload['data'][0]['model_ids'])
        replace.assert_called_once_with(
            device_id='cam-a', task_id=7,
            regions_data=[{'region_name': 'A'}], expected_revision=2,
        )
        refresh.assert_called_once_with(7)

    def test_legacy_device_endpoints_require_task_id(self):
        with self.app.test_request_context('/video/device-detection/device/cam-a/regions', method='GET'):
            response, status = api.list_device_regions('cam-a')
        self.assertEqual(400, status)
        self.assertIn('task_id', response.get_json()['msg'])

        with self.app.test_request_context('/video/device-detection/device/cam-a/regions', method='POST'):
            response, status = api.create_region('cam-a')
        self.assertEqual(400, status)
        self.assertIn('task_id', response.get_json()['msg'])

    def test_runtime_refresh_skips_stopped_task_and_reports_pending_on_failure(self):
        stopped = SimpleNamespace(id=7, run_status='stopped')
        query = SimpleNamespace(get=lambda _task_id: stopped)
        with patch.object(api, 'AlgorithmTask', SimpleNamespace(query=query)):
            self.assertEqual('not_running', api._refresh_task_runtime(7))

        running = SimpleNamespace(id=7, run_status='running')
        query = SimpleNamespace(get=lambda _task_id: running)
        with patch.object(api, 'AlgorithmTask', SimpleNamespace(query=query)), \
                patch('app.services.post_template_client.refresh_running_tasks_for_task', return_value=False):
            self.assertEqual('pending', api._refresh_task_runtime(7))


if __name__ == '__main__':
    unittest.main()
