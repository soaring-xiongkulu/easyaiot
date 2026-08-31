"""算法任务区域命中模式配置契约测试。"""
import json
import unittest
from pathlib import Path

from app.services.algorithm_task_service import _serialize_post_pipeline
from app.services.post_plugin_service import BUILTIN_PLUGIN_CATALOG
from app.utils.region_hit_mode import SELECTABLE_REGION_HIT_MODES
from models import AlgorithmTask


class RegionHitModeConfigTest(unittest.TestCase):
    def pipeline(self, mode, ratio=None):
        params = {'hit_mode': mode}
        if ratio is not None:
            params['min_overlap_ratio'] = ratio
        return [{'plugin': 'region_gate', 'enabled': True, 'params': params}]

    def test_all_selectable_modes_are_accepted(self):
        for mode in SELECTABLE_REGION_HIT_MODES:
            with self.subTest(mode=mode):
                serialized = _serialize_post_pipeline(self.pipeline(mode, 0.5))
                self.assertEqual(mode, json.loads(serialized)[0]['params']['hit_mode'])

    def test_legacy_modes_remain_executable_but_are_not_in_catalog(self):
        for mode in ('any_corner', 'any', 'all', 'bottom'):
            with self.subTest(mode=mode):
                self.assertIsNotNone(_serialize_post_pipeline(self.pipeline(mode)))

        region_gate = next(item for item in BUILTIN_PLUGIN_CATALOG if item['id'] == 'region_gate')
        enum = region_gate['params_schema']['properties']['hit_mode']['enum']
        self.assertEqual(list(SELECTABLE_REGION_HIT_MODES), enum)
        self.assertNotIn('any_corner', enum)

    def test_unknown_mode_is_rejected(self):
        with self.assertRaisesRegex(ValueError, '不支持的区域命中模式'):
            _serialize_post_pipeline(self.pipeline('not_supported'))

    def test_overlap_ratio_range_and_type_are_validated(self):
        for invalid in (0, -0.1, 1.01, '0.5', True, float('inf'), float('nan')):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    _serialize_post_pipeline(self.pipeline('overlap_ratio', invalid))
        for valid in (0.01, 0.5, 1):
            with self.subTest(valid=valid):
                self.assertIsNotNone(
                    _serialize_post_pipeline(self.pipeline('overlap_ratio', valid))
                )

    def test_pipeline_string_is_normalized_after_validation(self):
        raw = json.dumps(self.pipeline('fully_inside'), separators=(',', ':'))
        self.assertEqual(self.pipeline('fully_inside'), json.loads(_serialize_post_pipeline(raw)))

    def test_algorithm_task_parses_saved_pipeline_for_api_response(self):
        pipeline = self.pipeline('overlap_ratio', 0.5)
        task = AlgorithmTask(post_pipeline=json.dumps(pipeline, ensure_ascii=False))
        self.assertEqual(pipeline, task._parse_post_pipeline())

    def test_running_update_contract_allows_only_post_pipeline_and_pushes_template(self):
        source = Path(__file__).parent.joinpath(
            'app/services/algorithm_task_service.py'
        ).read_text(encoding='utf-8')
        self.assertIn("if keys - {'post_pipeline'}:", source)
        self.assertIn("put_template(task.id, task=task)", source)
        self.assertIn("task.template_revision = int(", source)


if __name__ == '__main__':
    unittest.main()
