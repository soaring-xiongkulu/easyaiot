"""节点级 CameraSourceManager 独立服务入口。"""
from __future__ import annotations

import json
import hmac
import logging
import os
import signal
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


VIDEO_ROOT = Path(__file__).resolve().parents[2]
if str(VIDEO_ROOT) not in sys.path:
    sys.path.insert(0, str(VIDEO_ROOT))

from app.services.camera_source_manager import CameraSourceManager

try:
    from app.utils.video_env import load_video_env

    load_video_env(override=False)
except ModuleNotFoundError:
    # 独立轻量运行环境可完全依赖父进程继承的环境变量。
    pass

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)


def _escape_prometheus_label(value) -> str:
    """按 Prometheus 文本格式转义标签值。"""
    return (
        str(value)
        .replace('\\', '\\\\')
        .replace('\n', '\\n')
        .replace('"', '\\"')
    )


class CameraSourceRequestHandler(BaseHTTPRequestHandler):
    """CameraSourceManager 本机控制接口。"""

    manager: CameraSourceManager = None
    require_token = False
    control_token = ''

    def log_message(self, format_string, *args):
        logger.debug('控制接口: ' + format_string, *args)

    def _send_json(self, status_code: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict:
        content_length = int(self.headers.get('Content-Length', '0') or '0')
        if content_length <= 0:
            return {}
        max_body_bytes = max(
            1024,
            int(os.getenv('CAMERA_SOURCE_MAX_REQUEST_BYTES', '65536')),
        )
        if content_length > max_body_bytes:
            raise ValueError(f'请求体超过限制: {content_length}>{max_body_bytes}')
        raw_data = self.rfile.read(content_length)
        return json.loads(raw_data.decode('utf-8'))

    def _is_authorized(self) -> bool:
        if not self.require_token:
            return True
        supplied_token = self.headers.get('X-Camera-Source-Token', '')
        return bool(supplied_token) and hmac.compare_digest(
            supplied_token,
            self.control_token,
        )

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path == '/health':
            self._send_json(200, {
                'status': 'ok',
                'service': 'camera_source_manager',
                'protocol_version': 1,
                'pid': os.getpid(),
            })
            return
        if not self._is_authorized():
            self._send_json(401, {'status': 'error', 'error': 'unauthorized'})
            return
        if parsed.path == '/status':
            device_id = parse_qs(parsed.query).get('device_id', [None])[0]
            data = self.manager.status(device_id)
            self._send_json(200, {'status': 'ok', 'data': data})
            return
        if parsed.path == '/metrics':
            self._send_metrics()
            return
        self._send_json(404, {'status': 'error', 'error': 'not_found'})

    def do_POST(self):
        try:
            if not self._is_authorized():
                self._send_json(401, {'status': 'error', 'error': 'unauthorized'})
                return
            payload = self._read_json()
            if self.path == '/subscribe':
                wait_timeout = min(
                    15.0,
                    max(0.0, float(payload.get('wait_timeout', 5.0))),
                )
                data = self.manager.subscribe(
                    payload.get('task_id'),
                    payload.get('device_id'),
                    payload.get('source_url'),
                    original_source=payload.get('original_source'),
                    is_gb28181=bool(payload.get('is_gb28181', False)),
                    subscriber_id=payload.get('subscriber_id'),
                    wait_timeout=wait_timeout,
                )
                self._send_json(200, {'status': 'ok', 'data': data})
                return
            if self.path == '/unsubscribe':
                self.manager.unsubscribe(
                    payload.get('task_id'),
                    payload.get('device_id'),
                    subscriber_id=payload.get('subscriber_id'),
                )
                self._send_json(200, {'status': 'ok'})
                return
            self._send_json(404, {'status': 'error', 'error': 'not_found'})
        except (TypeError, ValueError) as exc:
            self._send_json(400, {'status': 'error', 'error': str(exc)})
        except Exception as exc:
            logger.error('控制接口处理失败: %s', exc, exc_info=True)
            self._send_json(500, {'status': 'error', 'error': str(exc)})

    def _send_metrics(self) -> None:
        sessions = self.manager.status() or []
        active_source_count = sum(
            1 for item in sessions
            if item.get('status') not in ('failed', 'stopped')
        )
        lines = [
            '# HELP camera_source_count 当前共享摄像头源流数量',
            '# TYPE camera_source_count gauge',
            f'camera_source_count {active_source_count}',
            '# HELP camera_source_up 摄像头共享源会话是否可用',
            '# TYPE camera_source_up gauge',
        ]
        for item in sessions:
            device_label = _escape_prometheus_label(item.get('device_id', ''))
            labels = f'device_id="{device_label}"'
            source_up = 1 if item.get('status') == 'streaming' else 0
            lines.append(f'camera_source_up{{{labels}}} {source_up}')
            lines.append(
                f'camera_source_subscriber_count{{{labels}}} {item.get("subscriber_count", 0)}'
            )
            lines.append(f'camera_source_decode_fps{{{labels}}} {item.get("decode_fps", 0)}')
            lines.append(
                f'camera_source_reconnect_count{{{labels}}} {item.get("reconnect_count", 0)}'
            )
            lines.append(
                f'camera_source_last_frame_timestamp_seconds{{{labels}}} {item.get("last_frame_time") or 0}'
            )
        data = ('\n'.join(lines) + '\n').encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class CameraSourceHttpServer(ThreadingHTTPServer):
    """关闭时不等待可能仍在处理的订阅请求线程。"""

    daemon_threads = True
    allow_reuse_address = True


def _parent_watchdog(server: ThreadingHTTPServer, parent_pid: int) -> None:
    """VIDEO 父进程退出后停止源流服务，避免遗留孤儿进程。"""
    if parent_pid <= 0:
        return
    while True:
        time.sleep(2.0)
        try:
            os.kill(parent_pid, 0)
        except OSError:
            logger.warning('VIDEO 父进程已退出，停止 CameraSourceManager')
            server.shutdown()
            return


def main() -> None:
    host = (os.getenv('CAMERA_SOURCE_MANAGER_HOST') or '127.0.0.1').strip()
    port = int(os.getenv('CAMERA_SOURCE_MANAGER_PORT', '6010'))
    parent_pid = int(os.getenv('CAMERA_SOURCE_PARENT_PID', '0') or '0')
    control_token = (os.getenv('CAMERA_SOURCE_MANAGER_TOKEN') or '').strip()
    loopback_hosts = {'127.0.0.1', 'localhost', '::1'}
    if host not in loopback_hosts and not control_token:
        raise RuntimeError(
            'CameraSourceManager 非回环绑定时必须配置 CAMERA_SOURCE_MANAGER_TOKEN'
        )
    manager = CameraSourceManager()
    CameraSourceRequestHandler.manager = manager
    CameraSourceRequestHandler.require_token = host not in loopback_hosts
    CameraSourceRequestHandler.control_token = control_token
    server = CameraSourceHttpServer((host, port), CameraSourceRequestHandler)

    def stop_handler(_signal_number, _frame):
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)
    watchdog = threading.Thread(
        target=_parent_watchdog,
        args=(server, parent_pid),
        daemon=True,
        name='camera_source_parent_watchdog',
    )
    watchdog.start()
    logger.info('CameraSourceManager 启动: http://%s:%s pid=%s', host, port, os.getpid())
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        server.server_close()
        manager.close()
        logger.info('CameraSourceManager 已停止')


if __name__ == '__main__':
    main()
