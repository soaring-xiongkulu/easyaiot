"""大疆司空 FlightHub 直播接入（机场 / 无人机共用同一 OpenAPI）。

无人机与机场在协议层面无差异，均调用司空
``POST /openapi/v0.1/live-stream/start``；差异仅体现在展示元数据：
``device_type`` / ``model``（``DJI Dock Live`` vs ``DJI Drone Live``）。
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, unquote

import requests

_logger = logging.getLogger(__name__)

DJI_MANUFACTURER = 'DJI'
DJI_MODEL_DOCK = 'DJI Dock Live'
DJI_MODEL_DRONE = 'DJI Drone Live'
DEFAULT_LIVE_START_PATH = '/openapi/v0.1/live-stream/start'
_CONNECTION_STATUS_RE = re.compile(
    r'^dji_live\|(?P<device_type>dock|drone)\|cam=(?P<camera_index>.+)$'
)


def flighthub_env(name: str, default: str = '') -> str:
    return (os.getenv(name) or default or '').strip()


def normalize_flighthub_host(host: str) -> str:
    host = (host or '').strip().rstrip('/')
    if not host:
        return ''
    if not host.startswith(('http://', 'https://')):
        host = f'https://{host}'
    return host


def normalize_device_type(value: Any, model: str = '', name: str = '') -> str:
    raw = str(value or '').strip().lower()
    if raw in ('dock', 'airport', 'hangar'):
        return 'dock'
    if raw in ('drone', 'uav', 'aircraft'):
        return 'drone'
    text = f'{model or ""} {name or ""}'
    if re.search(r'drone|无人机|Drone\s*Live', text, re.I):
        return 'drone'
    if re.search(r'dock|机场|Dock\s*Live', text, re.I):
        return 'dock'
    return 'dock'


def model_for_device_type(device_type: str) -> str:
    return DJI_MODEL_DOCK if normalize_device_type(device_type) == 'dock' else DJI_MODEL_DRONE


def build_connection_status(device_type: str, camera_index: str) -> str:
    dtype = normalize_device_type(device_type)
    cam = (camera_index or '').strip()
    return f'dji_live|{dtype}|cam={cam}'


def parse_connection_status(value: Optional[str]) -> Tuple[str, str]:
    text = (value or '').strip()
    matched = _CONNECTION_STATUS_RE.match(text)
    if not matched:
        return '', ''
    return matched.group('device_type'), matched.group('camera_index')


def extract_camera_index_from_source(source: str) -> str:
    value = (source or '').strip()
    if not value.startswith('volc://'):
        return ''
    try:
        query = unquote(value[len('volc://'):])
        room_id = (parse_qs(query).get('room_id') or [''])[0]
        if '_' in room_id:
            return room_id.split('_', 1)[1].strip()
    except Exception:
        return ''
    return ''


def resolve_camera_index(data: Optional[dict] = None, source: str = '', connection_status: str = '') -> str:
    data = data or {}
    for key in ('camera_index', 'cameraIndex'):
        value = str(data.get(key) or '').strip()
        if value:
            return value
    _, stored = parse_connection_status(connection_status)
    if stored:
        return stored
    return extract_camera_index_from_source(source)


def skylink_request_payload(data: dict) -> dict:
    return {
        'sn': (data.get('sn') or data.get('serial_number') or '').strip(),
        'camera_index': str(data.get('camera_index') or '').strip(),
        'video_expire': int(data.get('video_expire') or 3600),
        'quality_type': data.get('quality_type') or 'adaptive',
    }


def find_live_provider(payload: Any) -> Optional[dict]:
    if isinstance(payload, dict):
        for key in ('provider', 'live', 'live_info', 'liveStream', 'live_stream', 'data', 'result'):
            found = find_live_provider(payload.get(key))
            if found:
                return found
        url = payload.get('url') or payload.get('play_url') or payload.get('live_url') or payload.get('stream_url')
        if url:
            return payload
        for value in payload.values():
            found = find_live_provider(value)
            if found:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = find_live_provider(item)
            if found:
                return found
    return None


def provider_url(provider: Optional[dict]) -> str:
    if not isinstance(provider, dict):
        return ''
    for key in ('url', 'play_url', 'live_url', 'stream_url', 'rtmp_url', 'flv_url', 'hls_url'):
        value = provider.get(key)
        if value:
            return str(value).strip()
    return ''


def is_direct_live_url(url: str) -> bool:
    lower = (url or '').strip().lower()
    return lower.startswith(('rtmp://', 'rtsp://', 'http://', 'https://')) and not lower.startswith('volc://')


def is_sdk_live_provider(provider: Optional[dict], url: str = '') -> bool:
    provider = provider or {}
    url_type = str(provider.get('url_type') or provider.get('type') or '').lower()
    effective_url = url or provider_url(provider)
    return (not is_direct_live_url(effective_url)) or url_type in ('volc', 'agora', 'webrtc', 'sdk')


def build_register_info(data: dict, source: str) -> Dict[str, Any]:
    project_uuid = (data.get('project_uuid') or data.get('workspace_id') or '').strip()
    device_type = normalize_device_type(
        data.get('device_type'),
        model=str(data.get('model') or ''),
        name=str(data.get('name') or ''),
    )
    camera_index = resolve_camera_index(data)
    serial = (data.get('serial_number') or data.get('sn') or data.get('dock_sn') or data.get('drone_sn') or '').strip()
    return {
        'name': (data.get('name') or ('大疆机场直播' if device_type == 'dock' else '大疆无人机直播')).strip(),
        'source': source,
        'cameraType': 'custom',
        'username': project_uuid,
        'password': '',
        'skylink_token': (
            data.get('skylink_token') or data.get('user_token') or data.get('x_user_token') or ''
        ).strip(),
        'manufacturer': data.get('manufacturer') or DJI_MANUFACTURER,
        'model': data.get('model') or model_for_device_type(device_type),
        'serial_number': serial,
        'hardware_id': data.get('hardware_id') or (f'flighthub:{project_uuid}' if project_uuid else ''),
        'firmware_version': (data.get('api_host') or data.get('platform_host') or '').strip(),
        'enable_forward': bool(data.get('enable_forward', False)),
        'port': data.get('port', 554),
        'address': data.get('address'),
        'longitude': data.get('longitude'),
        'latitude': data.get('latitude'),
        'altitude': data.get('altitude'),
        'connection_status': build_connection_status(device_type, camera_index),
        'device_type': device_type,
        'camera_index': camera_index,
    }


def get_flighthub_public_config() -> Dict[str, Any]:
    return {
        'allowed_ips': [x for x in flighthub_env('FLIGHTHUB_ALLOWED_IPS').split(',') if x],
        'workspace_id': flighthub_env('FLIGHTHUB_WORKSPACE_ID'),
        'workspace_name': flighthub_env('FLIGHTHUB_WORKSPACE_NAME'),
        'platform_name': flighthub_env('FLIGHTHUB_PLATFORM_NAME'),
        'platform_host': flighthub_env('FLIGHTHUB_PLATFORM_HOST', flighthub_env('FLIGHTHUB_OPENAPI_HOST')),
        'openapi_host': flighthub_env('FLIGHTHUB_OPENAPI_HOST'),
        'live_start_path': flighthub_env('FLIGHTHUB_LIVE_START_PATH', DEFAULT_LIVE_START_PATH),
        'mqtt_enabled': flighthub_env('FLIGHTHUB_MQTT_ENABLED', 'false').lower() == 'true',
        'mqtt_broker_uri': flighthub_env('FLIGHTHUB_MQTT_BROKER_URI'),
        'mqtt_client_id': flighthub_env('FLIGHTHUB_MQTT_CLIENT_ID'),
        'mqtt_username': flighthub_env('FLIGHTHUB_MQTT_USERNAME'),
    }


def start_flighthub_live(data: dict) -> Dict[str, Any]:
    """调用司空开启直播，返回标准化结果。

    成功直拉地址：
      ``{'ok': True, 'provider': ..., 'url': ..., 'url_type': ..., 'raw': ...}``
    SDK 型供应商：
      ``{'ok': False, 'code': 409, 'msg': ..., 'provider': ..., 'url_type': ..., 'raw': ...}``
    """
    api_host = normalize_flighthub_host(
        data.get('api_host') or data.get('platform_host') or flighthub_env('FLIGHTHUB_OPENAPI_HOST')
    )
    api_path = (
        data.get('api_path') or flighthub_env('FLIGHTHUB_LIVE_START_PATH', DEFAULT_LIVE_START_PATH)
    ).strip()
    project_uuid = (
        data.get('project_uuid') or data.get('workspace_id') or flighthub_env('FLIGHTHUB_WORKSPACE_ID')
    ).strip()
    user_token = (data.get('user_token') or flighthub_env('FLIGHTHUB_USER_TOKEN')).strip()
    if not api_host or not api_path or not project_uuid or not user_token:
        return {
            'ok': False,
            'code': 400,
            'msg': 'api_host, api_path, project_uuid and user_token are required',
            'raw': None,
        }

    url = f"{api_host}{api_path if api_path.startswith('/') else '/' + api_path}"
    try:
        response = requests.post(
            url,
            json=skylink_request_payload(data),
            headers={
                'X-Project-Uuid': project_uuid,
                'X-User-Token': user_token,
                'Content-Type': 'application/json',
            },
            timeout=20,
        )
    except requests.RequestException as exc:
        _logger.error('FlightHub OpenAPI request failed: %s', exc, exc_info=True)
        return {'ok': False, 'code': 502, 'msg': f'FlightHub request failed: {exc}', 'raw': None}

    try:
        body = response.json()
    except ValueError:
        body = {'raw': response.text}

    if response.status_code >= 400:
        return {
            'ok': False,
            'code': response.status_code,
            'msg': 'FlightHub request failed',
            'raw': body,
        }

    provider = find_live_provider(body) or {}
    play_url = provider_url(provider)
    url_type = str(provider.get('url_type') or provider.get('type') or '').lower()
    if not play_url:
        return {
            'ok': False,
            'code': 502,
            'msg': 'FlightHub did not return a live url',
            'raw': body,
        }
    if is_sdk_live_provider(provider, play_url):
        return {
            'ok': False,
            'code': 409,
            'msg': 'FlightHub returned SDK live provider',
            'provider': provider,
            'url_type': url_type or provider.get('type'),
            'suggestion': (
                '请在司空侧切换为 RTMP/HTTP-FLV/HLS 等可直拉供应商，'
                '或由前端 SDK / 直播桥接服务接入后再转本地 SRS。'
            ),
            'raw': body,
        }
    return {
        'ok': True,
        'code': 0,
        'provider': provider,
        'url': play_url,
        'url_type': url_type,
        'raw': body,
    }


def is_dji_device(manufacturer: str = '', model: str = '', hardware_id: str = '', source: str = '') -> bool:
    text = ' '.join([manufacturer or '', model or '', hardware_id or '', source or ''])
    return bool(re.search(r'DJI|Dock\s*Live|Drone\s*Live|flighthub:|volc://', text, re.I))


def resolve_device_type_from_record(
    device_type: str = '',
    model: str = '',
    name: str = '',
    connection_status: str = '',
) -> str:
    stored_type, _ = parse_connection_status(connection_status)
    if stored_type:
        return stored_type
    return normalize_device_type(device_type, model=model, name=name)
