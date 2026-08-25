"""节点本地摄像头发现、扫描与源流探测。

协议实现复用控制面同步到 /opt/easyaiot/VIDEO 的轻量 VIDEO 模块；所有调用仅返回
结果，不在节点侧写业务数据库。
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from typing import Any, Dict


def _video_root() -> str:
    return (os.getenv('VIDEO_ROOT') or '/opt/easyaiot/VIDEO').rstrip('/')


def _ensure_video_imports() -> None:
    root = _video_root()
    if root not in sys.path:
        sys.path.insert(0, root)


def discover() -> list[dict[str, Any]]:
    from wsdiscovery import WSDiscovery
    from wsdiscovery.scope import Scope

    wsd = WSDiscovery()
    wsd.start()
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    try:
        services = wsd.searchServices(
            scopes=[Scope('onvif://www.onvif.org/Profile')], timeout=3
        )
        for svc in services:
            ip = None
            for addr in svc.getXAddrs() or []:
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', str(addr))
                if match:
                    ip = match.group(1)
                    break
            if not ip or ip in seen:
                continue
            seen.add(ip)
            scopes = [str(scope) for scope in (svc.getScopes() or [])]
            mac = next((s.split('/MAC/', 1)[1] for s in scopes if '/MAC/' in s), None)
            name = next((s.split('/name/', 1)[1] for s in scopes if '/name/' in s), None)
            result.append({'ip': ip, 'mac': mac, 'hardware_name': name})
    finally:
        wsd.stop()
        if hasattr(wsd, '_stopThreads'):
            wsd._stopThreads()
    return result


def scan_segment(payload: Dict[str, Any]) -> list[dict[str, Any]]:
    _ensure_video_imports()
    from app.services.hik_scan_service import scan_segment as run_scan

    return run_scan(
        str(payload.get('targets') or '').strip(),
        ports_spec=str(payload.get('ports') or '80,443,8000,8443'),
        username=(str(payload.get('username') or '').strip() or None),
        password=payload.get('password'),
        credentials=payload.get('credentials'),
        concurrency=int(payload.get('concurrency') or 200),
        timeout=float(payload.get('timeout') or 3.0),
        only_hits=bool(payload.get('only_hits', True)),
        nvr_only=bool(payload.get('nvr_only', False)),
        exclude_nvr=bool(payload.get('exclude_nvr', False)),
    )


def probe_onvif(payload: Dict[str, Any]) -> dict[str, Any]:
    _ensure_video_imports()
    from app.services.onvif_service import OnvifCamera

    ip = str(payload.get('ip') or '').strip()
    username = str(payload.get('username') or '').strip()
    password = str(payload.get('password') or '')
    port = int(payload.get('port') or 80)
    if not ip or not password:
        raise ValueError('IP 和密码不能为空')
    candidates = [username] if username else ['admin', 'Administrator', 'root', '']
    last_error: Exception | None = None
    for candidate in candidates:
        try:
            camera = OnvifCamera(ip, port, candidate, password)
            info = dict(camera.get_info())
            # Agent 响应只返回发现结果，密码不在节点间回传。
            info.pop('password', None)
            info['username'] = candidate
            return info
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f'ONVIF 登录失败: {last_error}')


def nvr_channels(payload: Dict[str, Any]) -> dict[str, Any]:
    _ensure_video_imports()
    from app.services.hik_scan_service import enumerate_nvr_channels

    ip = str(payload.get('ip') or '').strip()
    if not ip:
        raise ValueError('NVR IP 不能为空')
    return enumerate_nvr_channels(
        ip,
        int(payload.get('port') or 80),
        username=(str(payload.get('username') or '').strip() or None),
        password=payload.get('password'),
        credentials=payload.get('credentials'),
        timeout=float(payload.get('timeout') or 5.0),
        vendor=(str(payload.get('vendor') or '').strip() or None),
        probe_cameras=bool(payload.get('probe_cameras', False)),
        only_mounted=bool(payload.get('only_mounted', True)),
        channel_filter=(str(payload.get('channel_filter') or '').strip() or None),
    )


def probe_stream(payload: Dict[str, Any]) -> dict[str, Any]:
    source = str(payload.get('source') or '').strip()
    if not source:
        raise ValueError('源流地址不能为空')
    timeout = max(1.0, min(float(payload.get('timeout') or 8.0), 30.0))
    command = [
        os.getenv('FFPROBE_PATH', 'ffprobe'),
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height,avg_frame_rate',
        '-of', 'json',
        source,
    ]
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError as exc:
        raise RuntimeError('节点未安装 ffprobe，请先部署 FFmpeg 工具链') from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f'源流探测超时（{int(timeout)} 秒）') from exc
    if completed.returncode != 0:
        detail = (completed.stderr or '').strip().splitlines()
        raise RuntimeError(detail[-1][:300] if detail else '无法读取源流')
    import json
    data = json.loads(completed.stdout or '{}')
    streams = data.get('streams') or []
    if not streams:
        raise RuntimeError('源流中未发现视频轨道')
    return {'ok': True, 'stream': streams[0]}
