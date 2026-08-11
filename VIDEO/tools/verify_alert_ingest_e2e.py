#!/usr/bin/env python3
"""可重复的告警入库验收（不依赖拉流 / YOLO / Ceph）。

分层：
  L0 契约   — hook 已下线、心跳仍在、MQTT 信封可规范化
  L1 入库   — MQTT → iot-sink → iot-video20.alert（按 correlation_id 断言）
  L2 图片   — 写入 ALERT_IMAGES_DIR 下真实 JPG，断言 image_url 非空（共享目录契约；
              Ceph 只是挂载实现之一，本脚本用本地同路径即可）

用法（仓库根或任意目录）：
  python3 VIDEO/tools/verify_alert_ingest_e2e.py
  python3 VIDEO/tools/verify_alert_ingest_e2e.py --skip-media
  VIDEO_DB_URL=postgresql://postgres:iot45722414822@127.0.0.1:5432/iot-video20 \\
    MQTT_BROKER_URLS=127.0.0.1:1883 python3 VIDEO/tools/verify_alert_ingest_e2e.py

环境变量：
  MQTT_BROKER_URLS   默认 127.0.0.1:1883
  VIDEO_BASE_URL     默认 http://127.0.0.1:6000
  ALERT_IMAGES_DIR   默认 <repo>/VIDEO/alert_images
  VERIFY_DEVICE_ID   默认 camera_atomic_001（须已绑定启用告警的 algorithm_task）
  VERIFY_TASK_ID     默认 1
  VIDEO_DB_* / PG*   或 VIDEO_DB_URL；也可用 DOCKER_PG_CONTAINER=postgres-server
  E2E_TIMEOUT_SEC    轮询入库超时，默认 20
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import struct
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlparse

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
    req = urlrequest.Request(url, data=body, method=method)
    if body is not None:
        req.add_header('Content-Type', 'application/json')
    try:
        with urlrequest.urlopen(req, timeout=5) as resp:
            return resp.status
    except urlerror.HTTPError as e:
        return e.code
    except Exception:
        return None


def _mqtt_encode_str(s: str | bytes) -> bytes:
    b = s.encode() if isinstance(s, str) else s
    return struct.pack('!H', len(b)) + b


def _mqtt_encode_len(n: int) -> bytes:
    out = bytearray()
    while True:
        byte = n % 128
        n //= 128
        if n:
            byte |= 0x80
        out.append(byte)
        if not n:
            break
    return bytes(out)


def mqtt_publish(host: str, port: int, topic: str, payload: bytes, client_id: str) -> None:
    """最小 MQTT 3.1.1 CONNECT + PUBLISH QoS0（无第三方依赖）。"""
    s = socket.create_connection((host, port), timeout=5)
    try:
        vh = b'\x00\x04MQTT\x04\x02\x00\x3c'
        rem = vh + _mqtt_encode_str(client_id)
        s.sendall(bytes([0x10]) + _mqtt_encode_len(len(rem)) + rem)
        connack = s.recv(4)
        if len(connack) < 4 or connack[0] != 0x20 or connack[3] != 0:
            raise RuntimeError(f'MQTT CONNACK failed: {connack.hex() if connack else "empty"}')
        msg = _mqtt_encode_str(topic) + payload
        s.sendall(bytes([0x30]) + _mqtt_encode_len(len(msg)) + msg)
        time.sleep(0.15)
    finally:
        s.close()


def write_tiny_jpeg(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image

        Image.new('RGB', (64, 64), color=(220, 40, 40)).save(path, 'JPEG')
        return
    except Exception:
        pass
    # 最小合法 JPEG
    path.write_bytes(
        bytes.fromhex(
            'ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707070909080a0c140d0c0b0b0c191213'
            '0f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432ffdb0043010909090c0b0c'
            '180d0d1832211c2132323232323232323232323232323232323232323232323232323232323232323232323232323232323232'
            '323232ffc00011080001000103011100021100031101ffc40014000100000000000000000000000000000008ffc40014100100'
            '000000000000000000000000000000ffda000c0301000210031000003f00bf80ffd9'
        )
    )


def _psql_docker(sql: str, container: str) -> str:
    proc = subprocess.run(
        [
            'docker',
            'exec',
            '-i',
            container,
            'psql',
            '-U',
            'postgres',
            '-d',
            'iot-video20',
            '-t',
            '-A',
            '-c',
            sql,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'psql failed')
    return proc.stdout.strip()


def _psql_local(sql: str) -> str:
    url = (os.getenv('VIDEO_DB_URL') or '').strip()
    if url:
        try:
            import psycopg2  # type: ignore
        except ImportError as e:
            raise RuntimeError('VIDEO_DB_URL 已设置但未安装 psycopg2') from e
        conn = psycopg2.connect(url)
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                return '\n'.join('|'.join('' if c is None else str(c) for c in r) for r in rows)
        finally:
            conn.close()

    env = os.environ.copy()
    host = env.get('VIDEO_DB_HOST') or env.get('PGHOST') or '127.0.0.1'
    port = env.get('VIDEO_DB_PORT') or env.get('PGPORT') or '5432'
    user = env.get('VIDEO_DB_USER') or env.get('PGUSER') or 'postgres'
    password = env.get('VIDEO_DB_PASSWORD') or env.get('PGPASSWORD') or 'iot45722414822'
    db = env.get('VIDEO_DB_NAME') or env.get('PGDATABASE') or 'iot-video20'
    env['PGPASSWORD'] = password
    proc = subprocess.run(
        [
            'psql',
            '-h',
            host,
            '-p',
            str(port),
            '-U',
            user,
            '-d',
            db,
            '-t',
            '-A',
            '-c',
            sql,
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or 'psql failed')
    return proc.stdout.strip()


def query_sql(sql: str) -> str:
    container = (os.getenv('DOCKER_PG_CONTAINER') or 'postgres-server').strip()
    # 优先 docker（本仓库本地 compose 最稳），失败再本地 psql/psycopg2
    try:
        proc = subprocess.run(
            ['docker', 'inspect', '-f', '{{.State.Running}}', container],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0 and proc.stdout.strip() == 'true':
            return _psql_docker(sql, container)
    except Exception:
        pass
    return _psql_local(sql)


def wait_alert_row(
    correlation_id: str,
    timeout_sec: float,
    *,
    require_image_url: bool = False,
) -> Optional[dict[str, Any]]:
    deadline = time.time() + timeout_sec
    sql = (
        "SELECT id, object, event, device_id, task_id, "
        "COALESCE(image_url,'') AS image_url, correlation_id "
        f"FROM alert WHERE correlation_id = '{correlation_id}' "
        'ORDER BY id DESC LIMIT 1'
    )
    last_err = ''
    last_row: Optional[dict[str, Any]] = None
    while time.time() < deadline:
        try:
            out = query_sql(sql)
            if out:
                parts = out.split('|')
                if len(parts) >= 7:
                    last_row = {
                        'id': parts[0],
                        'object': parts[1],
                        'event': parts[2],
                        'device_id': parts[3],
                        'task_id': parts[4],
                        'image_url': parts[5],
                        'correlation_id': parts[6],
                    }
                    if not require_image_url or last_row['image_url']:
                        return last_row
        except Exception as e:
            last_err = str(e)
        time.sleep(0.5)
    if last_err:
        print(f'[WARN] DB poll last error: {last_err}')
    return last_row


def run_l0_contract(video_base: str) -> None:
    print('\n--- L0 契约 ---')
    alert_py = (VIDEO / 'app/blueprints/alert.py').read_text(encoding='utf-8')
    check('源码无 /video/alert/hook', "@alert_bp.route('/hook'" not in alert_py)

    os.environ.setdefault('ALGO_BUS_TRANSPORT', 'mqtt')
    from app.utils.algo_mqtt_bus import bus_enabled, _normalize_alert_payload

    check('ALGO_BUS 默认开启', bus_enabled() is True)
    norm = _normalize_alert_payload(
        {
            'object': 'person',
            'event': 'detection',
            'device_id': 'x',
            'image_path': '/tmp/a.jpg',
            'time': '2026-01-01 00:00:00',
        }
    )
    check('信封含嵌套 alert.object', norm.get('alert', {}).get('object') == 'person')

    vu = urlparse(video_base)
    if tcp_open(vu.hostname or '127.0.0.1', vu.port or 80):
        hook = http_status(f'{video_base}/video/alert/hook', method='POST', body=b'{}')
        check('运行中 hook 404/405', hook in (404, 405), f'status={hook}')
        hb = http_status(
            f'{video_base}/video/algorithm/heartbeat/realtime',
            method='POST',
            body=json.dumps(
                {
                    'task_id': int(os.getenv('VERIFY_TASK_ID') or '1'),
                    'device_id': os.getenv('VERIFY_DEVICE_ID') or 'camera_atomic_001',
                    'status': 'running',
                }
            ).encode(),
        )
        check('heartbeat 可达(<500)', hb is not None and hb < 500, f'status={hb}')
    else:
        print(f'[SKIP] VIDEO {video_base} 未启动')


def run_l1_l2_ingest(*, skip_media: bool, timeout_sec: float) -> None:
    print('\n--- L1/L2 MQTT→入库 ---')
    broker = (os.getenv('MQTT_BROKER_URLS') or '127.0.0.1:1883').strip()
    host, _, port_s = broker.partition(':')
    port = int(port_s or '1883')
    if not tcp_open(host, port):
        check(f'MQTT broker {host}:{port} 可达', False)
        return
    check(f'MQTT broker {host}:{port} 可达', True)

    device_id = (os.getenv('VERIFY_DEVICE_ID') or 'camera_atomic_001').strip()
    task_id = int(os.getenv('VERIFY_TASK_ID') or '1')
    alert_dir = Path(
        (os.getenv('ALERT_IMAGES_DIR') or str(VIDEO / 'alert_images')).strip()
    ).resolve()
    corr = str(uuid.uuid4())
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    image_path = ''
    if not skip_media:
        img = alert_dir / 'e2e_verify' / f'ingest_{corr[:8]}.jpg'
        write_tiny_jpeg(img)
        image_path = str(img)
        check('测试 JPG 已写入共享目录', img.is_file(), str(img))
    else:
        print('[SKIP] --skip-media：不写图片，只断言落库字段')

    # RUNTIME / algo_mqtt_bus 同构信封
    inner = {
        'device_id': device_id,
        'device_name': 'e2e-verify-cam',
        'task_id': task_id,
        'task_name': 'e2e-verify',
        'task_type': 'realtime',
        'correlation_id': corr,
        'timestamp': now,
        'alert': {
            'object': 'person',
            'event': 'detection',
            'region': '',
            'information': 'verify_alert_ingest_e2e',
            'time': now,
            'image_path': image_path,
            'task_type': 'realtime',
        },
    }
    envelope = {
        'version': '1.0',
        'msgId': str(uuid.uuid4()),
        'msgType': 'alert.notification',
        'tenant': 'default',
        'ts': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
        'payload': inner,
    }
    body = json.dumps(envelope, ensure_ascii=False).encode()
    try:
        mqtt_publish(
            host,
            port,
            'mqtt/iot-alert-notification',
            body,
            client_id=f'e2e-ingest-{corr[:8]}',
        )
        check('MQTT 已发布 mqtt/iot-alert-notification', True, f'corr={corr}')
    except Exception as e:
        check('MQTT 已发布 mqtt/iot-alert-notification', False, str(e))
        return

    row = wait_alert_row(corr, timeout_sec, require_image_url=not skip_media)
    if not row:
        check(
            'alert 表出现 correlation_id 行',
            False,
            '超时：确认 iot-sink 在跑且已订阅 $share/algo-sink/mqtt/iot-alert-notification',
        )
        return

    check('alert 入库成功', True, f"id={row['id']} object={row['object']}")
    check('object 非空', bool(row['object']), row['object'])
    check('device_id 匹配', row['device_id'] == device_id, row['device_id'])
    check('event=detection', row['event'] == 'detection', row['event'])

    if not skip_media:
        check(
            'L2 image_url 已归档(MinIO)',
            bool(row['image_url']),
            row['image_url'][:80] if row['image_url'] else 'empty — 检查 ALERT_IMAGES_DIR 与 sink 是否同路径',
        )


def main() -> int:
    parser = argparse.ArgumentParser(description='MQTT 告警入库可重复验收')
    parser.add_argument('--skip-media', action='store_true', help='跳过图片/MinIO 断言')
    parser.add_argument('--contract-only', action='store_true', help='只跑 L0')
    parser.add_argument('--timeout', type=float, default=float(os.getenv('E2E_TIMEOUT_SEC') or '20'))
    args = parser.parse_args()

    video_base = (os.getenv('VIDEO_BASE_URL') or 'http://127.0.0.1:6000').rstrip('/')
    print('=== EasyAIoT 告警入库 E2E ===')
    print(f'VIDEO={video_base} MQTT={os.getenv("MQTT_BROKER_URLS") or "127.0.0.1:1883"}')

    run_l0_contract(video_base)
    if not args.contract_only:
        run_l1_l2_ingest(skip_media=args.skip_media, timeout_sec=args.timeout)

    print('---')
    print(f'结果: PASS={PASS} FAIL={FAIL}')
    if FAIL:
        print(
            '提示: L1 失败时先确认 iot-sink 订阅 EMQX、'
            'VERIFY_DEVICE_ID 已绑定 alert_event_enabled+is_enabled 的任务。'
        )
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
