"""algo_mqtt_bus 单元测试：算法总线关闭时 publish_alert 回退 HTTP 告警 hook（edge 单体无 MQTT/iot-sink）。"""
import json
import logging
import os
import socket
import sys
import tempfile
import threading
import unittest
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import MagicMock, patch

from app.utils import algo_mqtt_bus as bus


def _closed_port() -> int:
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


def _flat_alert() -> dict:
    """Python 算法管线构造的扁平告警字段。"""
    return {
        'object': 'person',
        'event': 'detection',
        'device_id': 'cam-1',
        'device_name': '入口',
        'task_id': 7,
        'task_name': '入口监控',
        'task_type': 'realtime',
        'time': '2026-11-24 10:00:00',
        'image_path': '/app/alert_images/task_7/cam-1/a.jpg',
        'information': json.dumps({'task_id': 7}),
        'correlation_id': 'corr-1',
    }


def _edge_env(**overrides) -> dict:
    # 开发机上可能正跑着真实 EMQX/iot-sink：默认把 MQTT 指向关闭端口、总线置为关闭，
    # 任何用例都不能把测试告警发到真实总线
    env = {
        'ALGO_BUS_TRANSPORT': 'http',
        'MQTT_BROKER_URLS': f'127.0.0.1:{_closed_port()}',
    }
    env.update(overrides)
    return env


def _quiet_logs(testcase, *names, level=logging.WARNING) -> None:
    """收敛被测代码的日志：导入过巡检会话服务的环境里 root logger 已被配上 handler，INFO 会直接刷屏。"""
    for name in names:
        logger = logging.getLogger(name)
        testcase.addCleanup(logger.setLevel, logger.level)
        logger.setLevel(level)


class _StubHook:
    """本地假 VIDEO 告警 hook：记录请求，按 status/body 应答。"""

    def __init__(self):
        self.requests = []
        self.status = 200
        self.body = json.dumps({'code': 0, 'msg': 'success', 'data': {'status': 'success', 'alert_id': 1}}).encode()
        hook = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get('Content-Length') or 0)
                hook.requests.append({
                    'path': self.path,
                    'content_type': self.headers.get('Content-Type'),
                    'json': json.loads(self.rfile.read(length)),
                })
                self.send_response(hook.status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(hook.body)

            def log_message(self, *args):
                pass

        self._server = HTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    @property
    def url(self):
        return f'http://127.0.0.1:{self._server.server_port}/video/alert/hook'

    def close(self):
        self._server.shutdown()
        self._server.server_close()


class TestPublishAlertHttpFallback(unittest.TestCase):
    def setUp(self):
        self.hook = _StubHook()
        self.addCleanup(self.hook.close)
        self.alert = _flat_alert()
        env = patch.dict(os.environ, _edge_env(ALERT_HOOK_URL=self.hook.url), clear=True)
        env.start()
        self.addCleanup(env.stop)
        _quiet_logs(self, 'algo_mqtt_bus', 'app')

    def _env(self, transport, hook_url=None):
        return _edge_env(ALERT_HOOK_URL=hook_url or self.hook.url) | {'ALGO_BUS_TRANSPORT': transport}

    def test_disabled_bus_posts_flat_alert_to_hook(self):
        self.assertFalse(bus.bus_enabled())
        self.assertTrue(bus.publish_alert(self.alert))

        self.assertEqual([r['json'] for r in self.hook.requests], [self.alert])
        self.assertEqual(self.hook.requests[0]['path'], '/video/alert/hook')
        self.assertEqual(self.hook.requests[0]['content_type'], 'application/json')

    def test_all_disable_values_share_the_http_fallback(self):
        for transport in ('http', 'off', '0', 'false', 'no'):
            with self.subTest(transport=transport), patch.dict(os.environ, self._env(transport), clear=True):
                self.assertFalse(bus.bus_enabled())
                self.assertTrue(bus.publish_alert(self.alert))
        self.assertEqual(len(self.hook.requests), 5)

    def test_snapshot_alert_uses_hook_without_mqtt_envelope(self):
        snap_alert = dict(self.alert, task_type='snapshot')
        self.assertTrue(bus.publish_alert(snap_alert, snapshot=True))
        self.assertEqual(self.hook.requests[0]['json'], snap_alert)

    def test_snapshot_flag_fills_task_type_for_the_hook(self):
        # 管线用 snapshot=True 选择 MQTT 主题；HTTP 请求没有主题，任务类型必须写进载荷
        snap_alert = {key: value for key, value in self.alert.items() if key != 'task_type'}
        self.assertTrue(bus.publish_alert(snap_alert, snapshot=True))
        self.assertEqual(self.hook.requests[0]['json']['task_type'], 'snap')

    def test_business_failure_code_is_reported_as_failure(self):
        # hook 对业务失败也返回 HTTP 200，只能靠响应体 code 判断
        self.hook.body = json.dumps({'code': 400, 'msg': '告警数据不能为空'}, ensure_ascii=False).encode()
        with self.assertLogs(bus.logger, level='WARNING') as logs:
            self.assertFalse(bus.publish_alert(self.alert))
        self.assertIn('code=400', logs.output[0])

    def test_http_error_is_failure_without_raising(self):
        self.hook.status = 500
        with self.assertLogs(bus.logger, level='WARNING') as logs:
            self.assertFalse(bus.publish_alert(self.alert))
        self.assertIn('status=500', logs.output[0])

    def test_unreachable_hook_is_failure_without_raising(self):
        closed_hook = f'http://127.0.0.1:{_closed_port()}/video/alert/hook'
        with self.assertLogs(bus.logger, level='WARNING') as logs, \
                patch.dict(os.environ, self._env('http', closed_hook), clear=True):
            self.assertFalse(bus.publish_alert(self.alert))
        self.assertIn('不可达', logs.output[0])

    def test_missing_hook_url_drops_alert(self):
        with self.assertLogs(bus.logger, level='WARNING') as logs, \
                patch.object(bus, 'alert_hook_url', return_value=''):
            self.assertFalse(bus.publish_alert(self.alert))
        self.assertIn('未配置告警 hook', logs.output[0])
        self.assertEqual(self.hook.requests, [])

    def test_non_json_native_value_does_not_drop_alert(self):
        alert = dict(self.alert, confidence=Decimal('0.93'))
        self.assertTrue(bus.publish_alert(alert))
        self.assertEqual(self.hook.requests[0]['json']['confidence'], '0.93')

    def test_enabled_bus_uses_mqtt_envelope_and_never_calls_hook(self):
        with patch.dict(os.environ, self._env('mqtt'), clear=True), patch.object(bus, '_publish', return_value=True) as mqtt_publish:
            self.assertTrue(bus.bus_enabled())
            self.assertTrue(bus.publish_alert(self.alert))

        self.assertEqual(self.hook.requests, [])
        topic, msg_type, payload = mqtt_publish.call_args.args
        self.assertEqual((topic, msg_type), ('mqtt/iot-alert-notification', 'alert.notification'))
        self.assertEqual(payload['alert']['image_path'], self.alert['image_path'])

    def test_enabled_bus_failure_does_not_fall_back_to_http(self):
        # 有总线的形态（mini/standard/full）保持原语义：MQTT 失败不绕过 iot-sink 直写
        with patch.dict(os.environ, self._env('mqtt'), clear=True), patch.object(bus, '_publish', return_value=False):
            self.assertFalse(bus.publish_alert(self.alert))
        self.assertEqual(self.hook.requests, [])

    def test_edge_profile_resolves_local_video_hook(self):
        with patch.dict(os.environ, {'EASYAIOT_DEPLOY_PROFILE': 'edge'}, clear=True):
            self.assertEqual(bus.alert_hook_url(), 'http://127.0.0.1:6000/video/alert/hook')

    def test_bus_enabled_reads_process_env_by_default_and_a_mapping_on_request(self):
        self.assertFalse(bus.bus_enabled())
        self.assertFalse(bus.bus_enabled({'ALGO_BUS_TRANSPORT': ' HTTP '}))
        self.assertTrue(bus.bus_enabled({'ALGO_BUS_TRANSPORT': 'mqtt'}))
        self.assertTrue(bus.bus_enabled({}))


class TestLaunchersDisablePostForHttpAlerts(unittest.TestCase):
    """拉起算法子进程时的环境：HTTP 告警形态下必须关掉子进程的 POST，否则管线走不到 HTTP 回退。"""

    def setUp(self):
        # 防御性场景：父进程环境里 POST 仍是开启状态（旧版 compose 的 environment 兜底、手工导出），
        # 拉起算法子进程时也必须把它关掉，否则管线走不到 HTTP 回退
        env = patch.dict(os.environ, _edge_env(
            POST_ENABLED='true',
            POST_INGRESS_TRANSPORT='mqtt',
            POST_FAIL_STRATEGY='closed',
            POST_BASE_URL='',
            NACOS_SERVER='',
        ), clear=True)
        env.start()
        self.addCleanup(env.stop)
        _quiet_logs(self, 'algo_mqtt_bus', 'app')
        _quiet_logs(self, 'app.services.algorithm_task_daemon', level=logging.ERROR)  # 隔离环境没有 DATABASE_URL
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name

    def _daemon(self, **attrs):
        from app.services.algorithm_task_daemon import AlgorithmTaskDaemon
        # 不经 __init__：它会启动守护线程并拉起真实的算法进程
        daemon = AlgorithmTaskDaemon.__new__(AlgorithmTaskDaemon)
        daemon._task_id = 7
        daemon._log_path = self.tmp
        daemon._task_type = 'realtime'
        daemon._executor = 'python'
        daemon._extra_env = {}
        for key, value in attrs.items():
            setattr(daemon, key, value)
        return daemon

    def _python_pipeline_env(self, daemon):
        with patch.object(type(daemon), '_get_conda_python', return_value=None):
            _, _, env = daemon._get_deploy_args()
        return env

    def _cpp_runtime_env(self, daemon):
        binary = os.path.join(self.tmp, 'RUNTIME')
        with open(binary, 'w', encoding='utf-8') as handle:
            handle.write('#!/bin/sh\n')
        os.chmod(binary, 0o755)
        ini = os.path.join(self.tmp, 'task.ini')
        with open(ini, 'w', encoding='utf-8') as handle:
            handle.write('[video_task]\n')
        daemon._executor = 'cpp'
        daemon._runtime_target = 'generic'
        daemon._runtime_bin = binary
        daemon._runtime_ini = ini
        daemon._runtime_inis = [ini]
        _, _, env = daemon._get_cpp_deploy_args_for_ini(ini)
        return env

    def test_python_pipeline_gets_post_disabled_in_http_alert_mode(self):
        env = self._python_pipeline_env(self._daemon())
        self.assertEqual((env['ALGO_BUS_TRANSPORT'], env['POST_ENABLED']), ('http', 'false'))

    def test_cpp_runtime_gets_post_disabled_in_http_alert_mode(self):
        self.assertEqual(self._cpp_runtime_env(self._daemon())['POST_ENABLED'], 'false')

    def test_patrol_session_gets_post_disabled_in_http_alert_mode(self):
        try:
            from app.services import patrol_session_service
        except ModuleNotFoundError as exc:
            self.skipTest(f'当前环境缺少巡检会话服务的依赖：{exc}')
        session = patrol_session_service.PatrolSessionDaemon.__new__(patrol_session_service.PatrolSessionDaemon)
        session._session_id = 3
        session._log_path = self.tmp
        env = session._build_env()
        self.assertEqual((env['ALGO_BUS_TRANSPORT'], env['POST_ENABLED']), ('http', 'false'))

    def test_post_stays_enabled_when_alerts_go_over_mqtt(self):
        with patch.dict(os.environ, {'ALGO_BUS_TRANSPORT': 'mqtt'}):
            pipeline_env = self._python_pipeline_env(self._daemon())
            runtime_env = self._cpp_runtime_env(self._daemon())
        self.assertEqual((pipeline_env['POST_ENABLED'], runtime_env['POST_ENABLED']), ('true', 'true'))

    def test_task_level_transport_override_is_honored(self):
        with patch.dict(os.environ, {'ALGO_BUS_TRANSPORT': 'mqtt'}):
            env = self._python_pipeline_env(self._daemon(_extra_env={'ALGO_BUS_TRANSPORT': 'http'}))
        self.assertEqual(env['POST_ENABLED'], 'false')

    def test_pipelines_reach_the_http_fallback_only_with_post_disabled(self):
        with patch.object(bus, 'post_is_ready', return_value=False):  # edge 未部署 POST
            # 修正前：POST 未就绪 + closed 策略，告警在到达 publish_alert 之前就被抑制
            self.assertEqual(bus.post_delivery_mode(), 'drop')
            self.assertTrue(bus.post_fail_closed())
            env = self._python_pipeline_env(self._daemon())
            with patch.dict(os.environ, env, clear=True):
                self.assertEqual(bus.post_delivery_mode(), 'direct')
                self.assertFalse(bus.post_fail_closed())


class TestFallbackAgainstRealHookRoute(unittest.TestCase):
    """回退逻辑与真实 /video/alert/hook 之间的契约：路由应答决定“投递成功/失败”，hook 服务决定是否落库。"""

    _TASK = {
        'task_id': 7,
        'task_name': '入口监控',
        'task_type': 'realtime',
        'model_ids': [3, 5],
        'face_detection_enabled': False,
        'plate_detection_enabled': False,
    }
    _DETECTIONS = [{'class_name': 'person', 'model_id': 3, 'bbox': [1, 2, 3, 4], 'confidence': 0.9}]

    def setUp(self):
        try:
            try:
                import kafka  # noqa: F401
                import onnxruntime  # noqa: F401
            except ModuleNotFoundError:  # 路由层依赖的告警服务会加载 Kafka 客户端
                for name in ('onnxruntime', 'kafka', 'kafka.errors'):
                    sys.modules.setdefault(name, MagicMock())
            from app.blueprints import alert as alert_views
            from flask import Flask
            from werkzeug.serving import make_server
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest(f'当前环境缺少 /video/alert/hook 路由的依赖：{exc}')

        env = patch.dict(os.environ, _edge_env(), clear=True)
        env.start()
        self.addCleanup(env.stop)

        app = Flask('alert-hook-contract')
        app.register_blueprint(alert_views.alert_bp, url_prefix='/video/alert')
        self.server = make_server('127.0.0.1', 0, app, threaded=True)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self._stop_server)
        os.environ['ALERT_HOOK_URL'] = f'http://127.0.0.1:{self.server.server_port}/video/alert/hook'

        werkzeug_logger = logging.getLogger('werkzeug')
        self.addCleanup(werkzeug_logger.setLevel, werkzeug_logger.level)
        werkzeug_logger.setLevel(logging.ERROR)
        _quiet_logs(self, 'algo_mqtt_bus', 'app')
        self.alert = _flat_alert()

    def _stop_server(self):
        self.server.shutdown()
        self.server.server_close()

    def _hook_returning(self, result):
        return patch('app.services.alert_hook_service.process_alert_hook', return_value=result)

    def test_persisted_alert_is_success_and_payload_arrives_unchanged(self):
        with self._hook_returning({'status': 'success', 'alert_id': 8834}) as process_hook:
            self.assertTrue(bus.publish_alert(self.alert))
        process_hook.assert_called_once_with(self.alert)

    def test_skipped_alert_counts_as_delivered(self):
        # 是否落库由 hook 按任务配置决定（如未启用告警事件），投递本身是成功的
        with self._hook_returning({'status': 'skipped', 'reason': 'alert_event_disabled'}):
            self.assertTrue(bus.publish_alert(self.alert))

    def test_failed_hook_is_reported_as_failure(self):
        with self._hook_returning({'status': 'failed', 'error': 'db down'}):
            self.assertFalse(bus.publish_alert(self.alert))

    def test_empty_alert_is_rejected_without_calling_the_service(self):
        with self._hook_returning({'status': 'success'}) as process_hook:
            self.assertFalse(bus.publish_alert({}))
        process_hook.assert_not_called()


if __name__ == '__main__':
    unittest.main()
