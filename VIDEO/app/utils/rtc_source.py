"""RTC / go2rtc 摄像头接入（Tapo、Tuya、Ring 等消费级 P2P 协议）。"""
from __future__ import annotations

import logging
import os
import re
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

_logger = logging.getLogger(__name__)

RTC_CONNECTION_STATUS_RE = re.compile(
    r'^rtc\|(?P<platform>[a-z0-9_]+)(?:\|stream=(?P<stream_name>.+))?$'
)


def rtc_env(name: str, default: str = '') -> str:
    return (os.getenv(name) or default or '').strip()


def rtc_service_url() -> str:
    return rtc_env('RTC_SERVICE_URL', 'http://127.0.0.1:6100').rstrip('/')


def rtc_rtsp_host() -> str:
    return rtc_env('RTC_RTSP_HOST', '127.0.0.1')


def rtc_rtsp_port() -> int:
    try:
        return int(rtc_env('RTC_RTSP_PORT', '8554'))
    except ValueError:
        return 8554


def rtc_go2rtc_web_url() -> str:
    return rtc_env('RTC_GO2RTC_WEB_URL', 'http://127.0.0.1:1984').rstrip('/')


def is_rtc_device(device) -> bool:
    hardware_id = (getattr(device, 'hardware_id', None) or '').strip()
    connection_status = (getattr(device, 'connection_status', None) or '').strip()
    return hardware_id.startswith('rtc:') or connection_status.startswith('rtc|')


def parse_rtc_connection_status(value: Optional[str]) -> tuple[str, str]:
    text = (value or '').strip()
    matched = RTC_CONNECTION_STATUS_RE.match(text)
    if not matched:
        return '', ''
    return matched.group('platform') or '', matched.group('stream_name') or ''


def build_connection_status(platform: str, stream_name: str) -> str:
    platform = (platform or '').strip().lower()
    stream_name = (stream_name or '').strip()
    if stream_name:
        return f'rtc|{platform}|stream={stream_name}'
    return f'rtc|{platform}'


def _rtc_request(method: str, path: str, **kwargs) -> requests.Response:
    url = f"{rtc_service_url()}{path}"
    kwargs.setdefault('timeout', float(rtc_env('RTC_REQUEST_TIMEOUT', '30')))
    resp = requests.request(method, url, **kwargs)
    resp.raise_for_status()
    return resp


def list_rtc_platforms() -> list[dict[str, Any]]:
    resp = _rtc_request('GET', '/api/platforms')
    payload = resp.json()
    return payload.get('platforms') or []


def build_rtc_stream_url(platform: str, params: dict[str, Any]) -> str:
    resp = _rtc_request(
        'POST',
        '/api/streams/build-url',
        json={'platform': platform, 'params': params},
    )
    data = resp.json()
    source = (data.get('source') or '').strip()
    if not source:
        raise ValueError('RTC 服务未返回有效源流 URL')
    return source


def register_rtc_stream(
    stream_name: str,
    *,
    platform: str = '',
    params: Optional[dict[str, Any]] = None,
    source: str = '',
    update: bool = False,
) -> dict[str, Any]:
    body: dict[str, Any] = {'name': stream_name, 'update': update}
    if platform:
        body['platform'] = platform
        body['params'] = params or {}
    elif source:
        body['source'] = source
    else:
        raise ValueError('platform 或 source 至少提供一个')

    resp = _rtc_request('POST', '/api/streams', json=body)
    data = resp.json()
    play_urls = data.get('play_urls') or {}
    rtsp_url = (play_urls.get('rtsp') or '').strip()
    if not rtsp_url:
        rtsp_url = f"rtsp://{rtc_rtsp_host()}:{rtc_rtsp_port()}/{stream_name}"
    data['rtsp_url'] = rtsp_url
    return data


def delete_rtc_stream(stream_name: str) -> None:
    if not stream_name:
        return
    try:
        params = urlencode({'src': stream_name})
        _rtc_request('DELETE', f'/api/streams?{params}')
    except Exception as exc:
        _logger.warning('删除 RTC 流 %s 失败: %s', stream_name, exc)


def resolve_rtc_stream_name(device) -> str:
    hardware_id = (getattr(device, 'hardware_id', None) or '').strip()
    if hardware_id.startswith('rtc:'):
        parts = hardware_id.split(':', 2)
        if len(parts) >= 3 and parts[2]:
            return parts[2]
    _, stream_name = parse_rtc_connection_status(getattr(device, 'connection_status', None))
    if stream_name:
        return stream_name
    device_id = (getattr(device, 'id', None) or '').strip()
    return device_id


def cleanup_rtc_stream_for_device(device) -> None:
    if not is_rtc_device(device):
        return
    delete_rtc_stream(resolve_rtc_stream_name(device))


def get_rtc_public_config() -> Dict[str, Any]:
    return {
        'service_url': rtc_service_url(),
        'go2rtc_web_url': rtc_go2rtc_web_url(),
        'rtsp_host': rtc_rtsp_host(),
        'rtsp_port': rtc_rtsp_port(),
    }


def _vendor_for_platform(platform: str) -> str:
    mapping = {
        'tapo': 'TP-Link',
        'tuya': 'Tuya',
        'ring': 'Amazon Ring',
        'nest': 'Google',
        'xiaomi': 'Xiaomi',
        'wyze': 'Wyze',
        'doorbird': 'DoorBird',
        'gopro': 'GoPro',
        'roborock': 'Roborock',
    }
    return mapping.get((platform or '').lower(), 'RTC')


def _model_for_platform(platform: str) -> str:
    mapping = {
        'tapo': 'Tapo Camera',
        'tuya': 'Tuya Camera',
        'ring': 'Ring Camera',
        'nest': 'Nest Camera',
        'xiaomi': 'Mi Home Camera',
        'wyze': 'Wyze Camera',
        'doorbird': 'DoorBird',
        'gopro': 'GoPro Camera',
        'roborock': 'Roborock Vacuum Cam',
    }
    return mapping.get((platform or '').lower(), 'RTC Camera')


def build_register_info(data: dict, rtsp_url: str, *, platform: str, stream_name: str) -> Dict[str, Any]:
    platform = (platform or '').strip().lower()
    params = data.get('params') or {}
    return {
        'id': stream_name,
        'name': (data.get('name') or _model_for_platform(platform)).strip(),
        'source': rtsp_url,
        'cameraType': 'custom',
        'manufacturer': data.get('manufacturer') or _vendor_for_platform(platform),
        'model': data.get('model') or _model_for_platform(platform),
        'ip': data.get('ip') or params.get('host') or params.get('endpoint') or '',
        'port': data.get('port') or 8554,
        'username': data.get('username') or params.get('username') or params.get('email') or '',
        'password': data.get('password') or params.get('password') or '',
        'enable_forward': bool(data.get('enable_forward', True)),
        'hardware_id': f'rtc:{platform}:{stream_name}',
        'connection_status': build_connection_status(platform, stream_name),
        'directory_id': data.get('directory_id'),
        'address': data.get('address'),
        'longitude': data.get('longitude'),
        'latitude': data.get('latitude'),
        'altitude': data.get('altitude'),
    }


def register_rtc_live(data: dict) -> Dict[str, Any]:
    """注册 RTC 流并返回 VIDEO 登记所需信息。"""
    platform = (data.get('platform') or '').strip().lower()
    params = data.get('params') or {}
    source = (data.get('source') or '').strip()
    stream_name = (data.get('stream_name') or data.get('id') or str(time.time_ns())).strip()
    update = bool(data.get('update'))

    if not platform and not source:
        return {'ok': False, 'code': 400, 'msg': 'platform 或 source 至少提供一个'}

    try:
        result = register_rtc_stream(
            stream_name,
            platform=platform,
            params=params,
            source=source,
            update=update,
        )
    except requests.RequestException as exc:
        _logger.error('RTC 流注册失败: %s', exc, exc_info=True)
        return {'ok': False, 'code': 502, 'msg': f'RTC 服务不可用: {exc}'}

    rtsp_url = result.get('rtsp_url') or ''
    register_info = build_register_info(
        data,
        rtsp_url,
        platform=platform or 'custom',
        stream_name=stream_name,
    )
    return {
        'ok': True,
        'stream_name': stream_name,
        'platform': platform or 'custom',
        'source': result.get('source') or source,
        'rtsp_url': rtsp_url,
        'play_urls': result.get('play_urls') or {},
        'register_info': register_info,
    }
