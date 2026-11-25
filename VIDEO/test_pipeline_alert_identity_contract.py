"""三种 Python 管线的告警载荷契约。

只读源码、不 import：run_deploy.py 一 import 就会连库拉流。字段缺省时 hook / iot-sink 只能按
“设备 + 任务类型”猜任务，不带时区的 time 会被当成东八区墙钟，task_id 为 0 时 iot-sink 不会回填。
"""
import ast
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.utils.service_urls import parse_alert_time_str

VIDEO = Path(__file__).resolve().parent
PIPELINES = {
    'realtime': VIDEO / 'services/realtime_algorithm_service/run_deploy.py',
    'snapshot': VIDEO / 'services/snapshot_algorithm_service/run_deploy.py',
    'patrol': VIDEO / 'services/patrol_algorithm_service/run_deploy.py',
}


def _alert_data_dicts(tree):
    """源码里所有 `alert_data = {…}` 的字典字面量及其所在函数。"""
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if 'alert_data' not in targets or not isinstance(node.value, ast.Dict):
            continue
        owner = parents.get(node)
        while owner is not None and not isinstance(owner, ast.FunctionDef):
            owner = parents.get(owner)
        found.append((node.value, owner))
    return found


def _fields(dict_node):
    return {key.value: value for key, value in zip(dict_node.keys, dict_node.values) if isinstance(key, ast.Constant)}


class PipelineAlertPayloadContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.alerts = {}
        for name, path in PIPELINES.items():
            tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
            cls.alerts[name] = _alert_data_dicts(tree)

    def test_each_pipeline_builds_one_flat_alert_payload(self):
        for name, dicts in self.alerts.items():
            with self.subTest(pipeline=name):
                self.assertEqual(len(dicts), 1)

    def test_every_payload_carries_a_correlation_id(self):
        for name, ((dict_node, _),) in self.alerts.items():
            with self.subTest(pipeline=name):
                self.assertIn('correlation_id', _fields(dict_node))

    def test_every_payload_carries_the_task_id(self):
        # 手工运行时 TASK_ID 为 0，iot-sink 会把 0 当成既有任务号而不回填：必须等价于缺省（None）
        for name in ('realtime', 'snapshot'):
            with self.subTest(pipeline=name):
                task_id = _fields(self.alerts[name][0][0])['task_id']
                self.assertEqual(ast.unparse(task_id), 'TASK_ID or None')

    def test_task_based_patrol_sets_task_id_after_building_the_payload(self):
        (dict_node, send_alert), = self.alerts['patrol']
        self.assertNotIn('task_id', _fields(dict_node))
        conditional_sets = [
            stmt
            for stmt in ast.walk(send_alert)
            if isinstance(stmt, ast.If)
            and ast.unparse(stmt.test) == 'session_config.task_id'
            and any(
                isinstance(item, ast.Assign)
                and isinstance(item.value, ast.Attribute)
                and ast.unparse(item.value) == 'session_config.task_id'
                and any(
                    isinstance(target, ast.Subscript)
                    and ast.unparse(target) == "alert_data['task_id']"
                    for target in item.targets
                )
                for item in stmt.body
            )
        ]
        self.assertTrue(conditional_sets, '会话式巡检没有 task_id，只能带条件地设置')

    def test_patrol_information_json_carries_the_same_correlation_id(self):
        (dict_node, _), = self.alerts['patrol']
        information = _fields(dict_node)['information']
        self.assertEqual(ast.unparse(information.func), 'json.dumps')
        inner = _fields(information.args[0])
        self.assertEqual(ast.unparse(inner['correlation_id']), ast.unparse(_fields(dict_node)['correlation_id']))

    def test_alert_time_is_never_a_naive_utc_string(self):
        for name, ((dict_node, _),) in self.alerts.items():
            with self.subTest(pipeline=name):
                expression = ast.unparse(_fields(dict_node)['time'])
                self.assertNotIn('utcnow', expression)
                self.assertTrue(
                    expression.startswith(('now_shanghai_time_str', '_shanghai_time_str', 'shanghai_time_str_from_epoch'))
                    or 'BEIJING_TZ' in expression,
                    expression,
                )

    def test_naive_utc_string_is_read_as_shanghai_wall_clock(self):
        """钉住“为什么不能用 utcnow”：不带时区的 time 会被当成东八区墙钟，差出 8 小时。"""
        now = datetime.now(timezone.utc)
        utc_wall_clock, _ = parse_alert_time_str(now.strftime('%Y-%m-%d %H:%M:%S'))
        self.assertGreater(abs(utc_wall_clock - now), timedelta(hours=7))

    def test_shanghai_wall_clock_string_parses_to_the_current_instant(self):
        from app.utils.service_urls import now_shanghai_time_str

        before = datetime.now(timezone.utc).replace(microsecond=0)  # 墙钟字符串不带亚秒
        shanghai, error = parse_alert_time_str(now_shanghai_time_str())
        after = datetime.now(timezone.utc)
        self.assertIsNone(error)
        self.assertTrue(before <= shanghai <= after)


if __name__ == '__main__':
    unittest.main()
