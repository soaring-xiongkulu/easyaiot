"""任务移除模型时的区域引用保护。"""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import models
from app.services.algorithm_task_service import _validate_model_removal_region_usage


class AlgorithmTaskRegionModelGuardTest(unittest.TestCase):
    def test_unchanged_or_added_models_do_not_query_regions(self):
        query = MagicMock()
        fake_model = SimpleNamespace(query=query)
        task = SimpleNamespace(id=7, model_ids='[11, 12]')
        with patch.object(models, 'DeviceDetectionRegion', fake_model):
            _validate_model_removal_region_usage(task, [11, 12, 13])
        query.filter_by.assert_not_called()

    def test_removal_without_references_is_allowed(self):
        query = MagicMock()
        query.filter_by.return_value.all.return_value = [
            SimpleNamespace(id=1, model_ids='[11]'),
            SimpleNamespace(id=2, model_ids=None),
        ]
        task = SimpleNamespace(id=7, model_ids='[11, 12]')
        with patch.object(models, 'DeviceDetectionRegion', SimpleNamespace(query=query)):
            _validate_model_removal_region_usage(task, [11])
        query.filter_by.assert_called_once_with(task_id=7)

    def test_removal_with_task_region_reference_is_rejected(self):
        query = MagicMock()
        query.filter_by.return_value.all.return_value = [
            SimpleNamespace(id=21, model_ids='[12]'),
            SimpleNamespace(id=22, model_ids='[11, 12]'),
        ]
        task = SimpleNamespace(id=7, model_ids='[11, 12]')
        with patch.object(models, 'DeviceDetectionRegion', SimpleNamespace(query=query)):
            with self.assertRaisesRegex(ValueError, r'区域 \[21, 22\]'):
                _validate_model_removal_region_usage(task, [11])

    def test_invalid_historical_region_scope_is_not_treated_as_all_models(self):
        query = MagicMock()
        query.filter_by.return_value.all.return_value = [SimpleNamespace(id=1, model_ids='bad-json')]
        task = SimpleNamespace(id=7, model_ids='[11, 12]')
        with patch.object(models, 'DeviceDetectionRegion', SimpleNamespace(query=query)):
            _validate_model_removal_region_usage(task, [11])


if __name__ == '__main__':
    unittest.main()
