"""Python/C++ 生产者必须一致执行 POST fail-open/fail-closed。"""
import os
import unittest
from pathlib import Path


ROOT = Path(os.environ.get('EASYAIOT_CONTRACT_ROOT', Path(__file__).resolve().parents[1]))


class PostFailStrategyProducerContractTest(unittest.TestCase):
    def test_all_python_producers_have_explicit_closed_drop_branch(self):
        relative_paths = [
            'VIDEO/services/realtime_algorithm_service/run_deploy.py',
            'VIDEO/services/snapshot_algorithm_service/run_deploy.py',
            'VIDEO/services/patrol_algorithm_service/run_deploy.py',
        ]
        for relative in relative_paths:
            source = (ROOT / relative).read_text(encoding='utf-8')
            with self.subTest(path=relative):
                self.assertIn('post_fail_closed', source)
                self.assertIn('if post_fail_closed():', source)
                self.assertIn('return', source[source.index('if post_fail_closed():'):])

    def test_cpp_only_publishes_infer_when_ingress_is_ready(self):
        bus = (ROOT / 'RUNTIME/src/AlgoMqttBus.cpp').read_text(encoding='utf-8')
        self.assertIn('return postIngressEnabled() && postIsReady();', bus)
        self.assertIn('bool AlgoMqttBus::postFailClosed()', bus)

    def test_cpp_alarm_thread_suppresses_direct_alert_for_closed_strategy(self):
        source = (ROOT / 'RUNTIME/src/Detech.cpp').read_text(encoding='utf-8')
        closed_pos = source.index('AlgoMqttBus::postFailClosed()')
        direct_pos = source.index('AlgoMqttBus::publishAlert', closed_pos)
        self.assertLess(closed_pos, direct_pos)
        self.assertIn('direct alert suppressed', source[closed_pos:direct_pos])

    def test_cpp_region_parser_accepts_video_object_coordinates(self):
        source = (ROOT / 'RUNTIME/src/ConfigParser.cpp').read_text(encoding='utf-8')
        self.assertIn('point.isObject()', source)
        self.assertIn('point["x"].isNumeric()', source)
        self.assertIn('point["y"].isNumeric()', source)
        self.assertIn('std::isfinite(x)', source)


if __name__ == '__main__':
    unittest.main()
