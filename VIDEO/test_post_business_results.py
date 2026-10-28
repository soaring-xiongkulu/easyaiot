"""Business POST contracts; runs without a database or model dependencies."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / relative)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


results = module('business', 'app/services/post_plugin_results.py')
config = module('config', 'app/utils/region_hit_mode.py')
runtime = module('runtime', 'app/utils/post_pipeline_runtime.py')


class BusinessResultTest(unittest.TestCase):
    def test_real_persisted_enrichment_and_summary(self):
        info = json.dumps({'custom_post': True, 'enrichment': {
            'line_cross': {'crossed': [{'direction': 'forward'}, {'direction': 'backward'}, {'direction': 'both'}]},
            'headcount_gate': {'count': 8}, 'default_pass': {'object': 'person'},
        }})
        extracted = results.business_results(info)
        self.assertNotIn('default_pass', extracted)
        summary = dict.fromkeys(('crossings', 'forward', 'backward', 'enter', 'exit', 'dwell_alerts', 'peak_count'), 0)
        results.summarize_result(summary, extracted)
        self.assertEqual((3, 1, 1, 8), (summary['crossings'], summary['forward'], summary['backward'], summary['peak_count']))

    def test_malformed_and_non_post_alerts(self):
        for raw in ('bad json', '[]', None, {'enrichment': []}):
            self.assertEqual({}, results.business_results(raw))

    def test_runtime_prerequisites(self):
        steps = [{'plugin': 'line_cross'}]
        config.validate_post_pipeline_runtime(steps, 'realtime', True)
        for args in [('snap', True), ('realtime', False), ('realtime', True, 'cpp'), ('realtime', True, 'python', True)]:
            with self.assertRaises(ValueError):
                config.validate_post_pipeline_runtime(steps, *args)
        config.validate_post_pipeline_runtime([{'plugin': 'line_cross', 'enabled': False}], 'snap', False)

    def test_invalid_parameters(self):
        for params in ({'threshold': -1}, {'threshold': 1.5}, {'threshold': float('nan')}, {'operator': 'bad'}):
            with self.assertRaises(ValueError):
                config.validate_post_pipeline([{'plugin': 'headcount_gate', 'params': params}])

    def test_observations_not_throttled_for_enabled_business_plugins(self):
        self.assertTrue(runtime.needs_continuous_observations(SimpleNamespace(post_pipeline='[{"plugin":"line_cross"}]')))
        self.assertFalse(runtime.needs_continuous_observations(SimpleNamespace(post_pipeline=[{'plugin': 'line_cross', 'enabled': False}])))


if __name__ == '__main__':
    unittest.main()
