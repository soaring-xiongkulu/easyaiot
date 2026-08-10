"""
从 WVP/国标服务同步通道到 VIDEO device 表，供设备目录与分屏监控展示。
"""
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from app.utils.gb28181_source import GB28181_SOURCE_PREFIX, _candidate_bases
from app.services.camera_service import (
    get_or_create_default_directory,
    gb28181_device_stream_urls,
    sync_unassigned_devices_to_default_directory,
)
from models import Device, db

logger = logging.getLogger(__name__)


class Gb28181SyncError(RuntimeError):
    """国标通道同步失败（WVP 不可达或接口异常）。"""


def _request_headers() -> dict:
    """优先使用当前 HTTP 请求携带的 JWT（与前端 WVP 网关一致），否则回退环境变量。"""
    headers: dict = {}
    try:
        from flask import has_request_context, request

        if has_request_context():
            auth = (request.headers.get('X-Authorization') or request.headers.get('Authorization') or '').strip()
            if auth:
                headers['X-Authorization'] = auth if auth.lower().startswith('bearer ') else f'Bearer {auth}'
                return headers
    except Exception:
        pass

    jwt_token = (os.getenv('JWT_TOKEN') or '').strip()
    if jwt_token:
        headers['X-Authorization'] = (
            jwt_token if jwt_token.lower().startswith('bearer ') else f'Bearer {jwt_token}'
        )
    return headers


def _http_timeout() -> Tuple[int, int]:
    """(connect, read) 秒；连接快速失败，避免目录接口被 WVP 拖死。"""
    connect = int(os.getenv('GB28181_HTTP_CONNECT_TIMEOUT', '3'))
    read = int(os.getenv('GB28181_HTTP_READ_TIMEOUT', '15'))
    return connect, read


def _extract_list(body: Any) -> List[dict]:
    """与前端 normalizePageResponse 一致，兼容 WVP PageInfo 及网关双层 data 包装。"""
    if isinstance(body, list):
        return body
    if not isinstance(body, dict):
        return []

    page = body.get('data', body)
    if isinstance(page, list):
        return page
    if not isinstance(page, dict):
        return []

    inner = page.get('data', page)
    if isinstance(inner, list):
        return inner
    if isinstance(inner, dict):
        return inner.get('list') or inner.get('records') or inner.get('rows') or []

    return page.get('list') or page.get('records') or page.get('rows') or []


def _query_api_roots() -> List[str]:
    """候选 WVP device/query 根路径（与 gb28181_source 网关配置一致，按优先级尝试）。"""
    roots: List[str] = []
    seen: set[str] = set()
    for base in _candidate_bases():
        b = (base or '').strip().rstrip('/')
        if not b:
            continue
        if b.endswith('/device/query'):
            root = b
        elif b.endswith('/gb28181'):
            root = f'{b}/device/query'
        elif b.endswith('/api'):
            root = f'{b}/device/query'
        else:
            root = f'{b}/device/query'
        if root not in seen:
            seen.add(root)
            roots.append(root)
    return roots


def _normalize_channel(item: dict, sip_device_id: str) -> Optional[Tuple[str, str, str]]:
    """返回 (sip_device_id, channel_gb_id, display_name)。字段顺序与前端 normalizeWvpChannelItem 对齐。"""
    sip = sip_device_id.strip()
    parent = str(
        item.get('parentDeviceId')
        or item.get('parentId')
        or item.get('gbParentId')
        or sip
        or '',
    ).strip()

    channel_id = str(
        item.get('channelId')
        or item.get('deviceChannelId')
        or item.get('gbDeviceId')
        or '',
    ).strip()

    if not channel_id:
        dev_id = str(item.get('deviceId') or '').strip()
        if dev_id and dev_id != parent and dev_id != sip:
            channel_id = dev_id

    if not channel_id and item.get('id') is not None:
        raw_id = str(item.get('id')).strip()
        if raw_id and raw_id != parent and raw_id != sip:
            channel_id = raw_id

    if not parent or not channel_id:
        return None

    name = (
        item.get('name')
        or item.get('channelName')
        or item.get('deviceName')
        or item.get('gbName')
        or channel_id
    )
    return parent, channel_id, str(name).strip()


def _virtual_device_id(sip_device_id: str, channel_id: str) -> str:
    return f'gb28181_{sip_device_id}_{channel_id}'


def parse_gb28181_virtual_device_id(device_id: str) -> Optional[Tuple[str, str]]:
    """解析 device 表中国标通道虚拟 ID：gb28181_{sipDeviceId}_{channelId}。"""
    device_id = (device_id or '').strip()
    prefix = 'gb28181_'
    if not device_id.startswith(prefix):
        return None
    rest = device_id[len(prefix):]
    if not rest or '_' not in rest:
        return None
    sip_device_id, channel_id = rest.rsplit('_', 1)
    sip_device_id = sip_device_id.strip()
    channel_id = channel_id.strip()
    if not sip_device_id or not channel_id:
        return None
    return sip_device_id, channel_id


def ensure_gb28181_virtual_device(
    device_id: str,
    *,
    name: str | None = None,
    location: dict | None = None,
) -> Device:
    """
    国标通道在设置坐标/查询详情时按需写入 device 表，避免未执行目录同步时找不到设备。
    """
    parsed = parse_gb28181_virtual_device_id(device_id)
    if not parsed:
        raise ValueError(f'无效的国标虚拟设备 ID: {device_id}')
    sip_device_id, channel_id = parsed
    existing = Device.query.get(device_id)
    if existing:
        return existing

    default_dir_id = get_or_create_default_directory().id
    display_name = (name or channel_id or device_id).strip()
    _upsert_gb_device(
        sip_device_id,
        channel_id,
        display_name,
        default_dir_id,
        location=location or {},
    )
    device = Device.query.get(device_id)
    if not device:
        raise ValueError(f'创建国标设备 {device_id} 失败')
    return device


def _parse_coord(value: Any) -> Optional[float]:
    """解析单个坐标值，空值或无法转为 float 返回 None。"""
    if value in (None, ''):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_coord_pair(item: dict, lng_key: str, lat_key: str) -> Optional[Tuple[float, float]]:
    """按坐标对提取：经纬度需同时有效且不为 (0,0)（WVP 未上报默认值），否则该来源视为无坐标。"""
    lng = _parse_coord(item.get(lng_key))
    lat = _parse_coord(item.get(lat_key))
    if lng is None or lat is None:
        return None
    if lng == 0 and lat == 0:
        return None
    return lng, lat


def _extract_channel_location(item: dict) -> dict:
    """
    从 WVP 通道数据提取位置信息。

    坐标按对回退：优先 WVP 主坐标 gbLongitude/gbLatitude（WGS-84，Catalog 到达时由
    WVP 归一写入，UI 编辑也写它），缺失或为 (0,0) 时回退国标 Catalog 原始上报坐标
    longitude/latitude，均无效视为未上报坐标。
    """
    pair = (
        _extract_coord_pair(item, 'gbLongitude', 'gbLatitude')
        or _extract_coord_pair(item, 'longitude', 'latitude')
    )
    address = item.get('address') or item.get('gbAddress')
    addr = str(address).strip() if address not in (None, '') else None

    if pair is None and not addr:
        return {}
    return {
        'longitude': pair[0] if pair else None,
        'latitude': pair[1] if pair else None,
        'address': addr,
        'location_source': 'gb28181',
    }


def _apply_gb_location(device, location: dict) -> bool:
    """写入国标位置；不覆盖用户手动维护的位置。"""
    if not location:
        return False
    if device.location_source == 'manual':
        return False

    changed = False
    lng = location.get('longitude')
    lat = location.get('latitude')
    if lng is not None and lat is not None:
        if device.longitude != lng or device.latitude != lat:
            device.longitude = lng
            device.latitude = lat
            changed = True
    addr = location.get('address')
    if addr and device.address != addr:
        device.address = addr
        changed = True
    if changed:
        device.location_source = 'gb28181'
        device.location_updated_at = datetime.utcnow()
    return changed


# GB28181 通道目录属性 → Device 列。WVP 通道 JSON 用 gb 前缀键(CommonGBChannel)，
# 老结构(DeviceChannel)用无前缀键，故按 gbX 优先、X 回退读取。
_CHANNEL_ATTR_KEYS = (
    ('ptz_type', ('gbPtzType', 'ptzType')),
    ('direction_type', ('gbDirectionType', 'directionType')),
    ('position_type', ('gbPositionType', 'positionType')),
    ('room_type', ('gbRoomType', 'roomType')),
    ('use_type', ('gbUseType', 'useType')),
    ('supply_light_type', ('gbSupplyLightType', 'supplyLightType')),
)


def _parse_int(value) -> Optional[int]:
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_channel_attributes(item: dict) -> dict:
    """从 WVP 通道数据提取相机结构/方位/业务分类等目录属性（缺失则不含该键）。"""
    attrs: dict = {}
    for col, keys in _CHANNEL_ATTR_KEYS:
        raw = next((item.get(k) for k in keys if item.get(k) not in (None, '')), None)
        parsed = _parse_int(raw)
        if parsed is not None:
            attrs[col] = parsed
    resolution = next(
        (item.get(k) for k in ('gbResolution', 'resolution') if item.get(k) not in (None, '')),
        None,
    )
    if resolution is not None:
        attrs['resolution'] = str(resolution).strip()[:100]
    return attrs


def _apply_gb_attributes(device, attributes: dict) -> bool:
    """写入国标目录属性（设备固有属性，非用户维护，直接覆盖）。"""
    if not attributes:
        return False
    changed = False
    for col in ('ptz_type', 'direction_type', 'position_type',
                'room_type', 'use_type', 'supply_light_type', 'resolution'):
        if col in attributes and getattr(device, col, None) != attributes[col]:
            setattr(device, col, attributes[col])
            changed = True
    return changed


def _upsert_gb_device(
    sip_device_id: str,
    channel_id: str,
    name: str,
    default_dir_id: int,
    *,
    location: dict | None = None,
    attributes: dict | None = None,
) -> bool:
    mapped_id = _virtual_device_id(sip_device_id, channel_id)
    source = f'{GB28181_SOURCE_PREFIX}{sip_device_id}/{channel_id}'
    # 国标通道播放走 WVP 点播，live 流地址留空；算法任务需 ai_rtmp_stream 推送检测结果
    rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream = gb28181_device_stream_urls(mapped_id)

    device = Device.query.get(mapped_id)
    if device:
        changed = False
        if device.name != name:
            device.name = name
            changed = True
        if device.source != source:
            device.source = source
            changed = True
        if not device.directory_id:
            device.directory_id = default_dir_id
            changed = True
        if device.rtmp_stream or device.http_stream:
            device.rtmp_stream = rtmp_stream
            device.http_stream = http_stream
            changed = True
        if not (device.ai_rtmp_stream or '').strip():
            device.ai_rtmp_stream = ai_rtmp_stream
            changed = True
        if not (device.ai_http_stream or '').strip():
            device.ai_http_stream = ai_http_stream
            changed = True
        if _apply_gb_location(device, location or {}):
            changed = True
        if _apply_gb_attributes(device, attributes or {}):
            changed = True
        if changed:
            db.session.commit()
        return False

    loc = location or {}
    attrs = attributes or {}
    device = Device(
        id=mapped_id,
        name=name or mapped_id,
        source=source,
        rtmp_stream=rtmp_stream,
        http_stream=http_stream,
        ai_rtmp_stream=ai_rtmp_stream,
        ai_http_stream=ai_http_stream,
        manufacturer='GB28181',
        model='GB28181-Channel',
        serial_number=sip_device_id,
        hardware_id=channel_id,
        nvr_channel=0,
        directory_id=default_dir_id,
        longitude=loc.get('longitude'),
        latitude=loc.get('latitude'),
        address=loc.get('address'),
        location_source='gb28181' if loc.get('longitude') is not None and loc.get('latitude') is not None else None,
        location_updated_at=datetime.utcnow() if loc.get('longitude') is not None and loc.get('latitude') is not None else None,
        ptz_type=attrs.get('ptz_type'),
        direction_type=attrs.get('direction_type'),
        position_type=attrs.get('position_type'),
        room_type=attrs.get('room_type'),
        use_type=attrs.get('use_type'),
        supply_light_type=attrs.get('supply_light_type'),
        resolution=attrs.get('resolution'),
    )
    db.session.add(device)
    db.session.commit()
    return True


def _fetch_json_list(url: str, *, headers: dict, timeout: Tuple[int, int], params: dict) -> List[dict]:
    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return _extract_list(response.json())


def _trigger_wvp_channel_sync(api_root: str, sip_id: str, headers: dict, timeout: Tuple[int, int]) -> None:
    try:
        requests.get(f'{api_root}/devices/{sip_id}/sync', headers=headers, timeout=timeout)
    except Exception as e:
        logger.debug(f'触发 WVP 通道同步 {sip_id} 失败: {e}')


def _pull_wvp_gb_devices(api_root: str, headers: dict, timeout: Tuple[int, int]) -> List[dict]:
    return _fetch_json_list(
        f'{api_root}/devices',
        headers=headers,
        timeout=timeout,
        params={'page': 1, 'count': 10000},
    )


def backfill_gb28181_ai_stream_urls() -> int:
    """为 device 表中 source 为 gb28181:// 且缺少 AI 推流地址的记录补全字段。"""
    prefix = GB28181_SOURCE_PREFIX.lower()
    updated = 0
    for device in Device.query.filter(Device.source.isnot(None)).all():
        source = (device.source or '').strip()
        if not source.lower().startswith(prefix):
            continue
        need_ai = not (device.ai_rtmp_stream or '').strip() or not (device.ai_http_stream or '').strip()
        if not need_ai:
            continue
        _, _, ai_rtmp, ai_http = gb28181_device_stream_urls(device.id)
        if not (device.ai_rtmp_stream or '').strip():
            device.ai_rtmp_stream = ai_rtmp
        if not (device.ai_http_stream or '').strip():
            device.ai_http_stream = ai_http
        updated += 1
    if updated:
        db.session.commit()
        logger.info(f'国标设备 AI 推流地址回填完成，更新 {updated} 条')
    return updated


def sync_gb28181_channels_from_payload(
    channels: List[dict],
    *,
    strict: bool = False,
) -> Dict[str, Any]:
    """
    将前端经 dev-api/gb28181 拉取的通道列表写入 device 表（与分屏监控同一 WVP 网关路径）。
    """
    stats: Dict[str, Any] = {
        'created': 0,
        'wvp_device_count': 0,
        'channels_seen': 0,
        'api_base': 'frontend-wvp',
        'errors': [],
        'upsert_errors': [],
    }
    if not channels:
        msg = '未收到国标通道数据'
        stats['errors'].append(msg)
        if strict:
            raise Gb28181SyncError(msg)
        return stats

    default_dir = get_or_create_default_directory()
    created = 0
    channels_seen = 0
    sip_ids: set[str] = set()

    for item in channels:
        if not isinstance(item, dict):
            continue
        sip = str(
            item.get('sipDeviceId')
            or item.get('sip_device_id')
            or item.get('deviceIdentification')
            or '',
        ).strip()
        ch_id = str(
            item.get('channelId')
            or item.get('channel_id')
            or item.get('gbDeviceId')
            or '',
        ).strip()
        name = str(item.get('name') or item.get('channelName') or ch_id).strip()
        if not sip or not ch_id:
            continue
        sip_ids.add(sip)
        channels_seen += 1
        try:
            if _upsert_gb_device(
                sip, ch_id, name, default_dir.id,
                location=_extract_channel_location(item),
                attributes=_extract_channel_attributes(item),
            ):
                created += 1
        except Exception as e:
            db.session.rollback()
            err_msg = f'{sip}/{ch_id}: {e}'
            logger.warning(f'同步国标通道失败 {err_msg}')
            stats['upsert_errors'].append(err_msg)

    sync_unassigned_devices_to_default_directory()
    stats['created'] = created
    stats['channels_seen'] = channels_seen
    stats['wvp_device_count'] = len(sip_ids)
    if created:
        logger.info(f'国标通道（前端 WVP）同步完成，新增 {created} 个')
    return stats


def sync_gb28181_channels_to_devices(*, strict: bool = False) -> Dict[str, Any]:
    """
    拉取 WVP 国标设备与通道，写入/更新 device 表并归入默认分组。

    返回统计：created、wvp_device_count、channels_seen、api_base、errors 等。
    strict=True 时 WVP 不可达会抛出 Gb28181SyncError（供手动同步接口使用）。
    """
    api_roots = _query_api_roots()
    stats: Dict[str, Any] = {
        'created': 0,
        'wvp_device_count': 0,
        'channels_seen': 0,
        'api_base': None,
        'errors': [],
    }

    if not api_roots:
        msg = (
            '未配置国标服务地址，请设置 GATEWAY_URL（如 http://127.0.0.1:48080）'
            ' 或 GB28181_SERVICE_URL（如 http://127.0.0.1:48088/api）'
        )
        logger.warning(msg)
        stats['errors'].append(msg)
        if strict:
            raise Gb28181SyncError(msg)
        return stats

    headers = _request_headers()
    timeout = _http_timeout()
    gb_devices: List[dict] = []
    api_root: Optional[str] = None
    fetch_errors: List[str] = []

    for root in api_roots:
        try:
            batch = _pull_wvp_gb_devices(root, headers, timeout)
            if batch:
                gb_devices = batch
                api_root = root
                break
            fetch_errors.append(f'{root}: 设备列表为空')
        except Exception as e:
            fetch_errors.append(f'{root}: {e}')

    stats['errors'] = fetch_errors
    stats['api_base'] = api_root

    if not gb_devices:
        msg = '拉取国标设备列表失败或列表为空'
        if fetch_errors:
            msg = f'{msg}（{"; ".join(fetch_errors)}）'
        logger.warning(msg)
        stats['errors'] = fetch_errors or [msg]
        if strict:
            raise Gb28181SyncError(msg)
        return stats

    stats['wvp_device_count'] = len(gb_devices)
    default_dir = get_or_create_default_directory()
    created = 0
    channels_seen = 0

    for gb_dev in gb_devices:
        sip_id = str(
            gb_dev.get('deviceId')
            or gb_dev.get('deviceIdentification')
            or gb_dev.get('id')
            or '',
        ).strip()
        if not sip_id or not api_root:
            continue

        try:
            channels = _fetch_json_list(
                f'{api_root}/devices/{sip_id}/channels',
                headers=headers,
                timeout=timeout,
                params={'page': 1, 'count': 10000},
            )
        except Exception as e:
            logger.debug(f'拉取国标设备 {sip_id} 通道失败: {e}')
            channels = []

        if not channels and int(gb_dev.get('channelCount') or 0) > 0:
            _trigger_wvp_channel_sync(api_root, sip_id, headers, timeout)
            try:
                channels = _fetch_json_list(
                    f'{api_root}/devices/{sip_id}/channels',
                    headers=headers,
                    timeout=timeout,
                    params={'page': 1, 'count': 10000},
                )
            except Exception as e:
                logger.debug(f'WVP 通道同步后重拉 {sip_id} 失败: {e}')

        for ch in channels:
            normalized = _normalize_channel(ch, sip_id)
            if not normalized:
                continue
            channels_seen += 1
            parent_id, channel_id, ch_name = normalized
            try:
                if _upsert_gb_device(
                    parent_id, channel_id, ch_name, default_dir.id,
                    location=_extract_channel_location(ch),
                    attributes=_extract_channel_attributes(ch),
                ):
                    created += 1
            except Exception as e:
                db.session.rollback()
                logger.warning(f'同步国标通道失败 {parent_id}/{channel_id}: {e}')

    sync_unassigned_devices_to_default_directory()
    stats['created'] = created
    stats['channels_seen'] = channels_seen
    if created:
        logger.info(
            f'国标通道同步完成，新增 {created} 个，WVP 设备 {len(gb_devices)} 个，通道 {channels_seen} 条'
        )
    return stats


def ensure_directory_layout() -> None:
    """目录/分屏树加载前：仅整理未分组设备，不阻塞请求去拉 WVP。"""
    try:
        sync_unassigned_devices_to_default_directory()
    except Exception as e:
        logger.warning(f'未分组设备归入默认目录失败: {e}')


def ensure_directory_devices_synced() -> None:
    """兼容旧调用：完整国标同步 + 目录整理（仅手动同步或后台任务应使用）。"""
    try:
        sync_gb28181_channels_to_devices()
    except Exception as e:
        logger.warning(f'国标设备同步异常: {e}')
        ensure_directory_layout()
    try:
        backfill_gb28181_ai_stream_urls()
    except Exception as e:
        logger.warning(f'国标设备 AI 推流地址回填异常: {e}')
