"""VIDEO 构建/刷新 POST 模板时的任务隔离测试。"""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import models
from app.services import post_template_client as client


def region_row(region_id, device_id, *, model_ids=None, enabled=True,
               hit_mode='center', min_overlap_ratio=0.5):
    return SimpleNamespace(
        id=region_id,
        device_id=device_id,
        region_name=f'区域-{region_id}',
        region_type='polygon',
        points='[{"x":0,"y":0},{"x":1,"y":0},{"x":1,"y":1}]',
        is_enabled=enabled,
        sort_order=region_id,
        model_ids=model_ids,
        hit_mode=hit_mode,
        min_overlap_ratio=min_overlap_ratio,
    )


class PostTemplateRegionIsolationTest(unittest.TestCase):
    def fake_region_model(self, rows):
        query = MagicMock()
        query.filter.return_value.all.return_value = rows
        return SimpleNamespace(
            query=query,
            task_id=MagicMock(),
            device_id=MagicMock(),
            is_enabled=MagicMock(),
        ), query

    def test_task_regions_queries_once_and_serializes_model_scopes(self):
        fake_model, query = self.fake_region_model([
            region_row(1, 'cam-a'),
            region_row(2, 'cam-a', model_ids='[12, 11, 12]'),
        ])
        task = SimpleNamespace(id=7, devices=[SimpleNamespace(id='cam-a')])
        with patch.object(models, 'DeviceDetectionRegion', fake_model):
            regions = client._task_regions(task)

        query.filter.assert_called_once()
        self.assertEqual([], regions[0]['model_ids'])
        self.assertEqual([12, 11, 12], regions[1]['model_ids'])
        self.assertEqual('center', regions[0]['hit_mode'])
        self.assertEqual(0.5, regions[0]['min_overlap_ratio'])
        self.assertTrue(all(item['device_id'] == 'cam-a' for item in regions))

    def test_task_regions_serialize_independent_region_hit_rules(self):
        fake_model, _ = self.fake_region_model([
            region_row(1, 'cam-a', hit_mode='center'),
            region_row(2, 'cam-a', hit_mode='overlap_ratio', min_overlap_ratio=0.7),
        ])
        task = SimpleNamespace(id=7, devices=[SimpleNamespace(id='cam-a')])
        with patch.object(models, 'DeviceDetectionRegion', fake_model):
            regions = client._task_regions(task)
        self.assertEqual('center', regions[0]['hit_mode'])
        self.assertEqual('overlap_ratio', regions[1]['hit_mode'])
        self.assertEqual(0.7, regions[1]['min_overlap_ratio'])

    def test_invalid_or_reserved_model_scope_is_not_silently_broadened(self):
        fake_model, _ = self.fake_region_model([
            region_row(1, 'cam-a', model_ids='not-json'),
            region_row(2, 'cam-a', model_ids='[]'),
            region_row(3, 'cam-a', model_ids='[0]'),
            region_row(4, 'cam-a', model_ids='[11]'),
        ])
        task = SimpleNamespace(id=7, devices=[SimpleNamespace(id='cam-a')])
        with patch.object(models, 'DeviceDetectionRegion', fake_model):
            regions = client._task_regions(task)
        self.assertEqual([4], [item['id'] for item in regions])

    def test_task_without_devices_has_no_regions_and_does_not_query_database(self):
        fake_model, query = self.fake_region_model([region_row(1, 'cam-a')])
        with patch.object(models, 'DeviceDetectionRegion', fake_model):
            self.assertEqual([], client._task_regions(SimpleNamespace(id=7, devices=[])))
        query.filter.assert_not_called()

    def test_template_carries_revision_task_models_and_only_task_regions(self):
        task = SimpleNamespace(
            id=7,
            task_name='任务A',
            task_type='realtime',
            model_ids='[-1, 12]',
            template_revision=9,
            alert_event_enabled=False,
            post_pipeline=None,
            post_process_script=None,
            devices=[SimpleNamespace(id='cam-a')],
        )
        expected_regions = [{'id': 1, 'device_id': 'cam-a'}]
        with patch.object(client, '_task_regions', return_value=expected_regions):
            template = client.build_template_from_task(task)
        self.assertEqual(9, template['revision'])
        self.assertEqual(7, template['task']['id'])
        self.assertEqual([-1, 12], template['task']['model_ids'])
        self.assertIs(expected_regions, template['regions'])

    def test_refresh_by_task_does_not_refresh_sibling_tasks(self):
        task = SimpleNamespace(id=7, run_status='running')
        task_query = MagicMock()
        task_query.get.return_value = task
        with patch.object(models, 'AlgorithmTask', SimpleNamespace(query=task_query)), \
                patch.object(client, 'put_template', return_value=True) as put:
            self.assertTrue(client.refresh_running_tasks_for_task(7))
        put.assert_called_once_with(7, task=task)

    def test_refresh_skips_stopped_task(self):
        task = SimpleNamespace(id=7, run_status='stopped')
        task_query = MagicMock()
        task_query.get.return_value = task
        with patch.object(models, 'AlgorithmTask', SimpleNamespace(query=task_query)), \
                patch.object(client, 'put_template') as put:
            self.assertFalse(client.refresh_running_tasks_for_task(7))
        put.assert_not_called()

    def test_put_template_rejects_stale_response_and_accepts_applied_response(self):
        task = SimpleNamespace(id=7)
        with patch.object(client, 'build_template_from_task', return_value={'task': {'id': 7}}), \
                patch.object(client, '_request_post', return_value=(200, {'applied': False})):
            self.assertFalse(client.put_template(7, task=task))
        with patch.object(client, 'build_template_from_task', return_value={'task': {'id': 7}}), \
                patch.object(client, '_request_post', return_value=(200, {'applied': True})):
            self.assertTrue(client.put_template(7, task=task))


if __name__ == '__main__':
    unittest.main()
