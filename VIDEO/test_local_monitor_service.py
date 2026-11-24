import unittest

from app.services.local_monitor_service import collect_local_metrics


class LocalMonitorServiceTest(unittest.TestCase):
    def test_collect_metrics_has_card_contract(self):
        data = collect_local_metrics()
        self.assertIn('collectedAt', data)
        self.assertGreaterEqual(data['cpu']['logicalCores'], 1)
        self.assertGreater(data['memory']['totalBytes'], 0)
        self.assertGreater(data['disk']['totalBytes'], 0)
        self.assertIn('rxBytesPerSec', data['network'])
        self.assertIn('runningTasks', data['runtime'])
        self.assertIn(data['runtime']['target'], ('auto', 'generic', 'rk3588'))


if __name__ == '__main__':
    unittest.main()
