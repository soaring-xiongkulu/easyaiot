"""算法总线关闭（edge 单体无 Kafka/iot-sink）时，人脸/车牌库匹配在 VIDEO 本进程完成的单元测试。"""
import os
import socket
import sys
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

try:
    import kafka  # noqa: F401
    import onnxruntime  # noqa: F401
except ModuleNotFoundError:
    # 轻量环境只验证路由层：缺推理引擎 / Kafka 客户端时用替身占位
    for _name in ('onnxruntime', 'kafka', 'kafka.errors'):
        sys.modules.setdefault(_name, MagicMock())

from flask import Flask, current_app

from app.blueprints import face as face_views
from app.blueprints import plate as plate_views
from app.services import library_matching_service


def _closed_port() -> int:
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


def _post(app, view, payload):
    """在请求上下文里直接调用视图，返回 (HTTP 状态码, 响应 JSON)。"""
    with app.test_request_context('/publish', method='POST', json=payload):
        result = view()
    status = getattr(result, 'status_code', None)
    if status is None:
        result, status = result
    return status, result.get_json()


def _wait_until(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


class TestMatchingPublishLocalDispatch(unittest.TestCase):
    def setUp(self):
        self._saved_env = os.environ.copy()
        self.app = Flask(__name__)
        self.app.register_blueprint(face_views.face_bp, url_prefix='/video/face')
        self.app.register_blueprint(plate_views.plate_bp, url_prefix='/video/plate')
        self.face_payload = {
            'taskId': 7,
            'taskName': '入口监控',
            'taskType': 'realtime',
            'deviceId': 'cam-1',
            'deviceName': '入口',
            'faceImagePath': '/data/face_images/task_7/cam-1/matching/f1.jpg',
            'threshold': 0.8,
            'bbox': [1, 2, 30, 40],
            'confidence': 0.93,
            'correlationId': 'corr-1',
        }
        self.plate_payload = {
            'taskId': 7,
            'taskName': '入口监控',
            'taskType': 'realtime',
            'deviceId': 'cam-1',
            'deviceName': '入口',
            'plateNo': '京A12345',
            'plateImagePath': '/data/plate_images/task_7/cam-1/p1.jpg',
        }

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._saved_env)

    def _env(self, transport):
        # 开发机上可能正跑着真实 EMQX/iot-sink，MQTT 一律指向关闭端口
        return patch.dict(os.environ, {
            'ALGO_BUS_TRANSPORT': transport,
            'MQTT_BROKER_URLS': f'127.0.0.1:{_closed_port()}',
        }, clear=True)

    def test_face_publish_matches_in_process_when_bus_disabled(self):
        done = threading.Event()
        apps = []

        def handler(message):
            apps.append(current_app._get_current_object())
            done.set()

        with self._env('http'), \
                patch.object(face_views.face_library_service, 'process_face_matching_message', side_effect=handler) as process, \
                patch('app.services.face_matching_kafka_service.send_face_matching_to_kafka') as send_kafka:
            status, body = _post(self.app, face_views.publish_face_matching, self.face_payload)

        self.assertEqual(status, 200)
        self.assertEqual(body['code'], 0)
        send_kafka.assert_not_called()
        self.assertTrue(done.wait(5))
        self.assertEqual(apps, [self.app])
        message = process.call_args.args[0]
        self.assertEqual(message['taskId'], 7)
        self.assertEqual(message['faceImagePath'], self.face_payload['faceImagePath'])
        self.assertEqual(message['correlationId'], 'corr-1')

    def test_plate_publish_matches_in_process_when_bus_disabled(self):
        done = threading.Event()

        def handler(message):
            done.set()

        with self._env('http'), \
                patch.object(plate_views.plate_library_service, 'process_plate_matching_message', side_effect=handler) as process, \
                patch('app.services.plate_matching_kafka_service.send_plate_matching_to_kafka') as send_kafka:
            status, body = _post(self.app, plate_views.publish_plate_matching, self.plate_payload)

        self.assertEqual(status, 200)
        self.assertEqual(body['data'], {'sent': True})
        send_kafka.assert_not_called()
        self.assertTrue(done.wait(5))
        message = process.call_args.args[0]
        self.assertEqual(message['taskId'], 7)
        self.assertEqual(message['plateNo'], '京A12345')
        self.assertEqual(message['plateImagePath'], self.plate_payload['plateImagePath'])

    def test_face_publish_keeps_kafka_when_bus_enabled(self):
        with self._env('mqtt'), \
                patch.object(library_matching_service, 'run_matching_locally') as run_locally, \
                patch('app.services.face_matching_kafka_service.send_face_matching_to_kafka', return_value=True) as send_kafka:
            status, body = _post(self.app, face_views.publish_face_matching, self.face_payload)

        self.assertEqual(status, 200)
        self.assertEqual(body['code'], 0)
        send_kafka.assert_called_once()
        self.assertEqual(send_kafka.call_args.args[0]['taskId'], 7)
        run_locally.assert_not_called()

    def test_face_publish_kafka_failure_still_returns_500_when_bus_enabled(self):
        with self._env('mqtt'), \
                patch.object(library_matching_service, 'run_matching_locally') as run_locally, \
                patch('app.services.face_matching_kafka_service.send_face_matching_to_kafka', return_value=False):
            status, body = _post(self.app, face_views.publish_face_matching, self.face_payload)

        self.assertEqual(status, 500)
        run_locally.assert_not_called()

    def test_plate_publish_reports_kafka_unavailable_when_bus_enabled(self):
        with self._env('mqtt'), \
                patch.object(library_matching_service, 'run_matching_locally') as run_locally, \
                patch('app.services.plate_matching_kafka_service.send_plate_matching_to_kafka', return_value=False):
            status, body = _post(self.app, plate_views.publish_plate_matching, self.plate_payload)

        self.assertEqual(status, 200)
        self.assertEqual(body['data'], {'sent': False})
        run_locally.assert_not_called()

    def test_publish_validation_unchanged_when_bus_disabled(self):
        with self._env('http'), \
                patch.object(library_matching_service, 'run_matching_locally') as run_locally:
            missing_task, _ = _post(self.app, face_views.publish_face_matching, {'faceImagePath': '/data/f.jpg'})
            missing_plate, _ = _post(self.app, plate_views.publish_plate_matching, {'taskId': 7})

        self.assertEqual((missing_task, missing_plate), (400, 400))
        run_locally.assert_not_called()

    def test_local_run_logs_expected_skip_without_raising(self):
        def handler(message):
            raise ValueError('任务未配置有效的人脸库')

        with self._env('http'), self.app.test_request_context(), \
                patch.object(library_matching_service.logger, 'warning') as warn:
            library_matching_service.run_matching_locally(handler, {'taskId': 7})
            self.assertTrue(_wait_until(lambda: warn.called))

        warn.assert_called_once()
        self.assertIn('任务未配置有效的人脸库', str(warn.call_args.args[-1]))

    def test_local_run_logs_unexpected_failure_without_raising(self):
        def handler(message):
            raise RuntimeError('onnx session failed')

        with self._env('http'), self.app.test_request_context(), \
                patch.object(library_matching_service.logger, 'error') as error:
            library_matching_service.run_matching_locally(handler, {'taskId': 7})
            self.assertTrue(_wait_until(lambda: error.called))

        error.assert_called_once()


if __name__ == '__main__':
    unittest.main()
