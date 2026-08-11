#!/usr/bin/env python3
"""VIDEO + RUNTIME 事件面链路冒烟验证（不依赖完整拉流）。

验证项：
1. VIDEO 不再注册 /video/alert/hook
2. algo_mqtt_bus 信封规范化 +（可选）MQTT 发布
3. HTTP 心跳 URL 契约仍指向 VIDEO
4. RUNTIME ini 不再依赖 alert_hook_url
"""
from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
import urllib.error
import urllib.request
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


def main() -> int:
    print('=== EasyAIoT VIDEO/RUNTIME 链路验证 ===')

    # 1) blueprint 无 /hook 路由
    alert_py = (VIDEO / 'app/blueprints/alert.py').read_text(encoding='utf-8')
    check('VIDEO alert.py 已移除 /hook 路由', "@alert_bp.route('/hook'" not in alert_py and 'def alert_hook' not in alert_py)

    # 2) Python 算法无 HTTP hook 回退
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

    # 3) MQTT bus 规范化
    os.environ['ALGO_BUS_TRANSPORT'] = 'mqtt'
    os.environ.pop('MQTT_BROKER_URLS', None)
    from app.utils.algo_mqtt_bus import bus_enabled, _normalize_alert_payload, publish_alert

    check('bus_enabled 默认 True', bus_enabled() is True)
    payload = _normalize_alert_payload(
        {
            'object': 'person',
            'event': 'detection',
            'device_id': 'cam_verify_1',
            'device_name': 'verify-cam',
            'time': '2026-08-11 10:00:00',
            'image_path': '/tmp/verify.jpg',
            'information': '{"task_id":1}',
            'task_type': 'realtime',
        },
        snapshot=False,
    )
    check('告警 payload 含嵌套 alert', isinstance(payload.get('alert'), dict))
    check('image_path 进入 alert', payload['alert'].get('image_path') == '/tmp/verify.jpg')

    # 无 broker 时 publish 应失败但不抛异常
    check('无 broker 时 publish_alert 返回 False', publish_alert(payload, snapshot=False) is False)

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
        status_hook = http_status(hook_url, method='POST', body=b'{}')
        check(
            'VIDEO /video/alert/hook 已不存在 (404/405)',
            status_hook in (404, 405),
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

    # 6) RUNTIME 示例 ini 无 hook
    ini = (ROOT / 'RUNTIME/config/config.example.ini').read_text(encoding='utf-8')
    check('config.example.ini 无 alert_hook_url', 'alert_hook_url=' not in ini and 'hook_url=http' not in ini)
    check('config.example.ini 含 [mqtt]', '[mqtt]' in ini)

    task_ini = (ROOT / 'RUNTIME/config/task_1.ini').read_text(encoding='utf-8')
    check('task_1.ini 无 alert_hook_url', 'alert_hook_url=' not in task_ini)
    check('task_1.ini 含 mqtt_broker_urls', 'mqtt_broker_urls=' in task_ini)

    # 7) RUNTIME 源码无 HTTP hook 回退路径
    detech = (ROOT / 'RUNTIME/src/Detech.cpp').read_text(encoding='utf-8')
    check(
        'Detech.cpp 告警走 MQTT 且无 /video/alert/hook POST',
        'AlgoMqttBus::publishAlert' in detech and '/video/alert/hook' not in detech,
    )

    print('---')
    print(f'结果: PASS={PASS} FAIL={FAIL}')
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
