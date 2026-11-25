#!/usr/bin/env python3
"""VIDEO + RUNTIME 事件面链路冒烟验证（不依赖完整拉流）。

验证项：
1. VIDEO 注册 /video/alert/hook（算法总线关闭时的 HTTP 告警入口）
2. Python 算法进程不直连 hook，告警统一经 algo_mqtt_bus；拉起方在 HTTP 告警形态下关闭子进程 POST
3. algo_mqtt_bus：MQTT 信封规范化 +（可选）MQTT 发布；总线关闭时回退 HTTP hook
4. HTTP 心跳 URL 契约仍指向 VIDEO
5. RUNTIME：MQTT 为默认告警通道，总线关闭时互斥回退 alert_hook_url
"""
from __future__ import annotations

import json
import os
import re
import socket
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIDEO = ROOT / 'VIDEO'
sys.path.insert(0, str(VIDEO))

PASS = 0
FAIL = 0


def check(name: str, ok: bool, detail: str = '') -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f'[PASS] {name}' + (f' — {detail}' if detail else ''))
    else:
        FAIL += 1
        print(f'[FAIL] {name}' + (f' — {detail}' if detail else ''))


def tcp_open(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_status(url: str, method: str = 'GET', body: bytes | None = None) -> int | None:
    req = urllib.request.Request(url, data=body, method=method)
    if body is not None:
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


def start_stub_hook(state: dict, received: list) -> HTTPServer:
    """本地假 VIDEO 告警 hook：record 收到的 JSON，按 state['status'] 应答。"""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802 — http.server 约定的方法名
            length = int(self.headers.get('Content-Length') or 0)
            received.append(json.loads(self.rfile.read(length) or b'{}'))
            self.send_response(state['status'])
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(
                b'{"code":0,"msg":"success","data":{"status":"success","alert_id":1}}'
                if state['status'] == 200
                else b'{"code":500,"msg":"failed"}'
            )

        def log_message(self, *args: object) -> None:
            pass

    server = HTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def ini_values_set(text: str, key: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(rf'^{key}=(.*)$', text, re.M) if m.group(1).strip()]


def main() -> int:
    print('=== EasyAIoT VIDEO/RUNTIME 链路验证 ===')

    # 1) blueprint 注册 /hook 路由
    alert_py = (VIDEO / 'app/blueprints/alert.py').read_text(encoding='utf-8')
    check('VIDEO alert.py 注册 /hook 路由', "@alert_bp.route('/hook'" in alert_py and 'def alert_hook' in alert_py)

    # 2) Python 算法不直连 hook（回退逻辑收敛在 algo_mqtt_bus.publish_alert）
    for rel in (
        'services/realtime_algorithm_service/run_deploy.py',
        'services/snapshot_algorithm_service/run_deploy.py',
        'services/patrol_algorithm_service/run_deploy.py',
    ):
        text = (VIDEO / rel).read_text(encoding='utf-8')
        check(
            f'{rel} 无 ALERT_HOOK_URL / requests.post hook',
            'ALERT_HOOK_URL' not in text and '/video/alert/hook' not in text,
        )

    # 2b) 拉起算法子进程时，HTTP 告警形态下必须关闭 POST：否则 POST 未就绪按 closed 策略抑制，
    #     告警根本到不了 publish_alert 的 HTTP 回退
    for rel in ('app/services/algorithm_task_daemon.py', 'app/services/patrol_session_service.py'):
        text = (VIDEO / rel).read_text(encoding='utf-8')
        check(f'{rel} HTTP 告警时关闭子进程 POST', 'disable_post_for_http_alerts(env)' in text)

    # 3) MQTT bus 规范化
    saved_brokers = os.environ.get('MQTT_BROKER_URLS')
    os.environ['ALGO_BUS_TRANSPORT'] = 'mqtt'
    # “无 broker”必须指向确定的空端口：开发机常驻 EMQX 时，默认的 127.0.0.1:1883 会把这条告警真实发出去
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        os.environ['MQTT_BROKER_URLS'] = f'127.0.0.1:{probe.getsockname()[1]}'
    from app.utils.algo_mqtt_bus import bus_enabled, _normalize_alert_payload, publish_alert

    check('bus_enabled 默认 True', bus_enabled() is True)
    flat_alert = {
        'object': 'person',
        'event': 'detection',
        'device_id': 'cam_verify_1',
        'device_name': 'verify-cam',
        'time': '2026-08-11 10:00:00',
        'image_path': '/tmp/verify.jpg',
        'information': '{"task_id":1}',
        'task_type': 'realtime',
    }
    payload = _normalize_alert_payload(flat_alert, snapshot=False)
    check('告警 payload 含嵌套 alert', isinstance(payload.get('alert'), dict))
    check('image_path 进入 alert', payload['alert'].get('image_path') == '/tmp/verify.jpg')

    # 无 broker 时 publish 应失败但不抛异常
    check('无 broker 时 publish_alert 返回 False', publish_alert(payload, snapshot=False) is False)
    if saved_brokers is None:
        os.environ.pop('MQTT_BROKER_URLS', None)
    else:
        os.environ['MQTT_BROKER_URLS'] = saved_brokers

    # 3b) 总线关闭：回退 HTTP hook，发的是扁平字段而不是 MQTT 信封
    state = {'status': 200}
    received: list = []
    stub = start_stub_hook(state, received)
    try:
        os.environ['ALGO_BUS_TRANSPORT'] = 'http'
        os.environ['ALERT_HOOK_URL'] = f'http://127.0.0.1:{stub.server_port}/video/alert/hook'
        check('ALGO_BUS_TRANSPORT=http 时 bus_enabled 为 False', bus_enabled() is False)
        check('总线关闭时 publish_alert 走 HTTP hook', publish_alert(flat_alert, snapshot=False) is True)
        check('HTTP hook 收到扁平告警（非 MQTT 信封）', received == [flat_alert])
        state['status'] = 500
        check('hook 返回 500 时 publish_alert 返回 False 且不抛异常', publish_alert(flat_alert, snapshot=False) is False)
    finally:
        stub.shutdown()
        stub.server_close()
        os.environ['ALGO_BUS_TRANSPORT'] = 'mqtt'
        os.environ.pop('ALERT_HOOK_URL', None)

    # 4) 可选：对真实 broker 发布
    broker = (os.getenv('MQTT_BROKER_URLS') or '').strip() or '127.0.0.1:1883'
    host, _, port_s = broker.partition(':')
    port = int(port_s or '1883')
    if tcp_open(host, port):
        os.environ['MQTT_BROKER_URLS'] = f'{host}:{port}'
        # reload brokers from env
        from importlib import reload
        import app.utils.algo_mqtt_bus as bus

        reload(bus)
        ok = bus.publish_alert(
            {
                'object': 'person',
                'event': 'mqtt_chain_verify',
                'device_id': 'cam_verify_mqtt',
                'device_name': 'mqtt-verify',
                'time': '2026-08-11 10:00:01',
                'image_path': str(Path(tempfile.gettempdir()) / 'easyaiot_verify.jpg'),
                'task_type': 'realtime',
                'information': json.dumps({'verify': True, 'task_id': 900001}),
            },
            snapshot=False,
        )
        check(f'MQTT 发布到 {host}:{port}', ok is True)
    else:
        print(f'[SKIP] MQTT broker {host}:{port} 不可达 — 跳过实发')

    # 5) VIDEO heartbeat 契约（若服务在跑）
    video_base = (os.getenv('VIDEO_BASE_URL') or 'http://127.0.0.1:6000').rstrip('/')
    hb_url = f'{video_base}/video/algorithm/heartbeat/realtime'
    hook_url = f'{video_base}/video/alert/hook'
    hb_body = json.dumps(
        {
            'task_id': 900001,
            'server_ip': '127.0.0.1',
            'port': 8001,
            'process_id': os.getpid(),
            'log_path': '/tmp/verify.log',
        }
    ).encode()

    # 解析 host
    from urllib.parse import urlparse

    vu = urlparse(video_base)
    video_up = tcp_open(vu.hostname or '127.0.0.1', vu.port or 80)
    if video_up:
        # 空请求体也会得到 HTTP 200：hook 的业务码放在响应体 code 里
        status_hook = http_status(hook_url, method='POST', body=b'{}')
        check(
            'VIDEO /video/alert/hook 已注册 (200)',
            status_hook == 200,
            f'status={status_hook}',
        )
        status_hb = http_status(hb_url, method='POST', body=hb_body)
        check(
            'VIDEO heartbeat 接口可达',
            status_hb is not None and status_hb < 500,
            f'status={status_hb}',
        )
    else:
        print(f'[SKIP] VIDEO {video_base} 未启动 — 跳过 HTTP 实探')

    # 6) RUNTIME ini：MQTT 为默认通道，alert_hook_url 仅在 algo_bus_transport=http 时生效
    ini = (ROOT / 'RUNTIME/config/config.example.ini').read_text(encoding='utf-8')
    check('config.example.ini 默认 algo_bus_transport=mqtt', bool(re.search(r'^algo_bus_transport=mqtt\s*$', ini, re.M)))
    check('config.example.ini alert_hook_url 未硬编码地址', not ini_values_set(ini, 'alert_hook_url'))
    check('config.example.ini 含 [mqtt]', '[mqtt]' in ini)

    task_ini = (ROOT / 'RUNTIME/config/task_1.ini').read_text(encoding='utf-8')
    check('task_1.ini alert_hook_url 未硬编码地址', not ini_values_set(task_ini, 'alert_hook_url'))
    check('task_1.ini 含 mqtt_broker_urls', 'mqtt_broker_urls=' in task_ini)

    # 7) RUNTIME 源码：MQTT 与 HTTP hook 两条告警通道并存且互斥
    detech = (ROOT / 'RUNTIME/src/Detech.cpp').read_text(encoding='utf-8')
    check(
        'Detech.cpp 告警走 MQTT，总线关闭时互斥回退 HTTP hook',
        'AlgoMqttBus::publishAlert' in detech and 'httpAlertFallbackEnabled(_config)' in detech,
    )

    print('---')
    print(f'结果: PASS={PASS} FAIL={FAIL}')
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
