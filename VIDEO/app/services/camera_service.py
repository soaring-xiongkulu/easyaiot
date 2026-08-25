"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import concurrent.futures
import logging
import os
import re
import signal
import socket
import threading
import time
import tzlocal
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
from onvif import ONVIFCamera
from sqlalchemy import or_
from wsdiscovery import WSDiscovery, Scope

from app.services.nvr_service import (
    infer_nvr_link_from_source,
    is_nvr_channel_device,
    nvr_fields_for_device,
    repair_nvr_channel_links,
    resolve_nvr_link,
)
from app.services.onvif_service import OnvifCamera
from app.utils.gb28181_source import GB28181_SOURCE_PREFIX
from app.utils.rtsp_url import parse_rtsp_auth
from app.utils.ip_utils import IpReachabilityMonitor, resolve_ipv4_for_stream_urls
from app.utils.rtc_source import cleanup_rtc_stream_for_device
from models import Device, db, DeviceDetectionRegion, DeviceDirectory, DeviceTrackSession, DeviceTrackPoint

DEFAULT_DIRECTORY_NAME = '默认分组'

_LOCATION_FIELD_KEYS = frozenset({
    'longitude', 'latitude', 'altitude', 'address', 'location_source', 'heading',
})


def _parse_optional_float(value):
    """解析可选浮点；空字符串/None 表示清除。"""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f'坐标数值无效: {value}') from e


def _validate_location_pair(longitude, latitude):
    """经纬度需成对出现；有值时校验 WGS84 范围。"""
    if longitude is None and latitude is None:
        return
    if longitude is None or latitude is None:
        raise ValueError('经纬度需同时填写或同时留空')
    if not (-180.0 <= longitude <= 180.0):
        raise ValueError('经度范围应在 -180 至 180 之间')
    if not (-90.0 <= latitude <= 90.0):
        raise ValueError('纬度范围应在 -90 至 90 之间')


def _validate_heading(heading):
    """朝向角：0=正北，顺时针 0-360。"""
    if heading is None:
        return
    if not (0.0 <= heading <= 360.0):
        raise ValueError('朝向应在 0 至 360 度之间')


def _location_fields_for_device(camera: Device) -> dict:
    has_location = camera.longitude is not None and camera.latitude is not None
    updated_at = camera.location_updated_at
    return {
        'longitude': camera.longitude,
        'latitude': camera.latitude,
        'altitude': camera.altitude,
        'address': camera.address,
        'heading': camera.heading,
        'location_source': camera.location_source,
        'location_updated_at': updated_at.isoformat() if updated_at else None,
        'has_location': has_location,
    }


def _gb_attribute_fields_for_device(camera: Device) -> dict:
    """GB28181 通道目录属性（PTZ 能力 / 结构 / 方位 / 业务分类），供地图区分与筛选。"""
    return {
        'support_move': camera.support_move,
        'support_zoom': camera.support_zoom,
        'ptz_type': camera.ptz_type,
        'direction_type': camera.direction_type,
        'position_type': camera.position_type,
        'room_type': camera.room_type,
        'use_type': camera.use_type,
        'supply_light_type': camera.supply_light_type,
        'resolution': camera.resolution,
    }


def _apply_location_updates(camera: Device, update_info: dict) -> None:
    """处理位置字段更新；允许显式传 null/空字符串清除。"""
    if not any(k in update_info for k in _LOCATION_FIELD_KEYS):
        return

    longitude = camera.longitude
    latitude = camera.latitude
    altitude = camera.altitude
    address = camera.address
    heading = camera.heading

    if 'longitude' in update_info:
        longitude = _parse_optional_float(update_info['longitude'])
    if 'latitude' in update_info:
        latitude = _parse_optional_float(update_info['latitude'])
    if 'altitude' in update_info:
        altitude = _parse_optional_float(update_info['altitude'])
    if 'heading' in update_info:
        heading = _parse_optional_float(update_info['heading'])
    if 'address' in update_info:
        raw_addr = update_info['address']
        if raw_addr is None or raw_addr == '':
            address = None
        else:
            address = str(raw_addr).strip() or None

    _validate_location_pair(longitude, latitude)
    _validate_heading(heading)
    if altitude is not None and not (-500.0 <= altitude <= 9000.0):
        raise ValueError('海拔高度应在 -500 至 9000 米之间')

    camera.longitude = longitude
    camera.latitude = latitude
    camera.altitude = altitude
    camera.address = address
    camera.heading = heading

    has_coords = longitude is not None and latitude is not None
    has_any = has_coords or altitude is not None or bool(address) or heading is not None
    if has_any:
        src = update_info.get('location_source')
        if src:
            camera.location_source = str(src).strip()[:20] or 'manual'
        elif not camera.location_source or camera.location_source == 'gb28181':
            camera.location_source = 'manual'
        camera.location_updated_at = datetime.utcnow()
    else:
        camera.location_source = None
        camera.location_updated_at = None
        camera.heading = None

# 全局变量定义
_onvif_cameras = {}
_ingress_node_summary_cache: dict[int, tuple[float, dict]] = {}
# 确保环境变量转换为整数
_monitor = IpReachabilityMonitor(int(os.getenv('CAMERA_ONLINE_INTERVAL', 20)))
logger = logging.getLogger(__name__)
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
scheduler = BackgroundScheduler(timezone=tzlocal.get_localzone_name())

_scheduler_lock = threading.Lock()
_scheduler_shutdown_registered = False
_scheduler_stopped = False
_background_stopped = False


def ensure_scheduler_running() -> bool:
    """启动全局 APScheduler（幂等）。"""
    global _scheduler_stopped
    with _scheduler_lock:
        if _scheduler_stopped:
            logger.warning('APScheduler 已关闭，跳过启动')
            return False
        if not scheduler.running:
            scheduler.start()
        return True


def shutdown_scheduler(wait: bool = True) -> None:
    """安全关闭全局 APScheduler（幂等）。"""
    global _scheduler_stopped
    with _scheduler_lock:
        if _scheduler_stopped:
            return
        if scheduler.running:
            try:
                scheduler.shutdown(wait=wait)
            except Exception as exc:
                logger.debug('关闭 APScheduler 失败: %s', exc)
        _scheduler_stopped = True


def shutdown_background_services(wait: bool = True) -> None:
    """停止 IP 监控、线程池与调度器，避免进程退出时后台线程继续提交任务。"""
    global _background_stopped
    with _scheduler_lock:
        if _background_stopped:
            return
        _background_stopped = True

    try:
        _monitor.stop()
    except Exception as exc:
        logger.debug('停止 IP 可达性监控失败: %s', exc)

    shutdown_scheduler(wait=wait)

    try:
        from app.services.snap_task_service import shutdown_snap_scheduler
        shutdown_snap_scheduler(wait=wait)
    except Exception as exc:
        logger.debug('关闭抓拍任务调度器失败: %s', exc)

    try:
        executor.shutdown(wait=wait, cancel_futures=True)
    except TypeError:
        try:
            executor.shutdown(wait=wait)
        except Exception as exc:
            logger.debug('关闭 camera executor 失败: %s', exc)
    except Exception as exc:
        logger.debug('关闭 camera executor 失败: %s', exc)


def register_scheduler_shutdown() -> None:
    """注册进程退出与信号处理，确保后台服务先于解释器关闭线程池。"""
    global _scheduler_shutdown_registered
    with _scheduler_lock:
        if _scheduler_shutdown_registered:
            return
        _scheduler_shutdown_registered = True

    import atexit

    def _on_exit():
        shutdown_background_services(wait=True)

    atexit.register(_on_exit)

    def _signal_handler(signum, frame):
        shutdown_background_services(wait=True)

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _signal_handler)
        except Exception:
            pass


def is_default_directory(directory) -> bool:
    """根级「默认分组」为系统保留目录。"""
    return bool(
        directory
        and directory.name == DEFAULT_DIRECTORY_NAME
        and directory.parent_id is None
    )


def get_or_create_default_directory() -> DeviceDirectory:
    directory = DeviceDirectory.query.filter_by(
        name=DEFAULT_DIRECTORY_NAME,
        parent_id=None,
    ).first()
    if directory:
        return directory
    directory = DeviceDirectory(
        name=DEFAULT_DIRECTORY_NAME,
        parent_id=None,
        description='未手动分组的摄像头（含直连与国标）',
        sort_order=-1000,
    )
    db.session.add(directory)
    db.session.commit()
    return directory


def sync_unassigned_devices_to_default_directory() -> int:
    """将 directory_id 为空的设备归入默认分组（含直连、国标）。"""
    default_dir = get_or_create_default_directory()
    updated = Device.query.filter(Device.directory_id.is_(None)).update(
        {Device.directory_id: default_dir.id},
        synchronize_session=False,
    )
    if updated:
        db.session.commit()
    return updated


def directory_id_for_new_device(register_info: dict | None = None) -> int:
    register_info = register_info or {}
    raw = register_info.get('directory_id')
    if raw is not None and raw != '' and raw != 0:
        return int(raw)
    return get_or_create_default_directory().id

# 全局PTZ指令队列与锁
ptz_queues = {}
ptz_queue_locks = {}

def _get_onvif_camera(id: str) -> OnvifCamera:
    """获取缓存的ONVIF相机对象或创建新连接"""
    if id in _onvif_cameras:
        return _onvif_cameras[id]
    return _update_onvif_camera(id)


def _update_onvif_camera(id: str) -> OnvifCamera:
    """更新或创建ONVIF相机连接"""
    camera = _get_camera(id)
    if not camera:
        raise ValueError(f'设备ID {id} 不存在于系统中')

    if is_nvr_channel_device(camera):
        raise ValueError(f'设备 {id} 为 NVR 挂载通道，不需要 ONVIF 连接')

    # 如果摄像头地址是 rtmp，不需要 ONVIF 连接
    if camera.source and camera.source.strip().lower().startswith('rtmp://'):
        raise ValueError(f'设备 {id} 的源地址是 RTMP，不需要 ONVIF 连接')

    _onvif_cameras.pop(id, None)

    try:
        onvif_cam = _create_onvif_camera_from_orm(camera)
        _onvif_cameras[id] = onvif_cam
        return onvif_cam
    except ValueError as e:
        # IP地址或端口无效，抛出更明确的错误
        raise RuntimeError(f'设备 {id} 连接失败：{str(e)}')
    except Exception as e:
        raise RuntimeError(f'设备 {id} 连接失败：{str(e)}')


def _create_onvif_camera_from_orm(camera: Device) -> OnvifCamera:
    """从ORM对象创建ONVIF连接"""
    if is_nvr_channel_device(camera):
        raise ValueError(f'设备 {camera.id} 为 NVR 挂载通道，不需要 ONVIF 连接')

    # 如果摄像头地址是 rtmp，则不需要 ONVIF 连接
    if camera.source and camera.source.strip().lower().startswith('rtmp://'):
        raise ValueError(f'设备 {camera.id} 的源地址是 RTMP，不需要 ONVIF 连接')
    
    # 验证IP地址是否有效
    if not camera.ip or not camera.ip.strip():
        raise ValueError(f'设备 {camera.id} 的IP地址为空，无法创建ONVIF连接')
    
    # 验证端口是否有效，确保端口是整数类型
    try:
        port = int(camera.port) if camera.port else 0
    except (ValueError, TypeError):
        port = 0
    
    if not port or port <= 0:
        raise ValueError(f'设备 {camera.id} 的端口无效，无法创建ONVIF连接')
    
    return _create_onvif_camera(
        camera.id, camera.ip, port,
        camera.username, camera.password
    )


def _create_onvif_camera(camera_id, *args, **kwargs) -> OnvifCamera:
    """带超时的ONVIF连接创建"""

    def connect():
        return OnvifCamera(*args, **kwargs)

    # 使用 ThreadPoolExecutor 实现超时控制
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(connect)
        from onvif import ONVIFError
        try:
            return future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            raise RuntimeError('设备连接超时，请检查网络连接')
        except ONVIFError as e:
            error_msg = str(e).removeprefix('Unknown error: ')
            raise RuntimeError(f'ONVIF协议错误: {error_msg}')
        except Exception as e:
            raise RuntimeError(f'连接异常: {str(e)}')


def list_onvif_presets(device_id: str) -> list[dict]:
    """查询 ONVIF 设备预置点列表"""
    cam = _get_onvif_camera(device_id)
    if not cam._ptz_controller:
        raise RuntimeError('该设备不支持云台/预置点')
    return cam.list_positions()


def set_onvif_preset(device_id: str, name: str, preset_token: str | None = None) -> str | None:
    """保存当前云台位置为预置点"""
    cam = _get_onvif_camera(device_id)
    if not cam._ptz_controller:
        raise RuntimeError('该设备不支持云台/预置点')
    token = cam.save_position(name, preset_token)
    if not token:
        raise RuntimeError('保存预置点失败，设备可能不支持该操作')
    return token


def call_onvif_preset(device_id: str, preset_token: str) -> None:
    """调用 ONVIF 预置点"""
    cam = _get_onvif_camera(device_id)
    if not cam._ptz_controller:
        raise RuntimeError('该设备不支持云台/预置点')
    cam.goto_position(preset_token)


def delete_onvif_preset(device_id: str, preset_token: str) -> None:
    """删除 ONVIF 预置点"""
    cam = _get_onvif_camera(device_id)
    if not cam._ptz_controller:
        raise RuntimeError('该设备不支持云台/预置点')
    if not cam.remove_position(preset_token):
        raise RuntimeError('删除预置点失败')


def _get_camera(id: str) -> Device:
    """获取单个设备ORM对象"""
    return Device.query.get(id)


def _get_camera_for_location(id: str, *, name: str | None = None) -> Device:
    """获取设备；国标虚拟通道在不存在时按需入库，供坐标设置/详情查询。"""
    camera = Device.query.get(id)
    if camera:
        return camera
    if (id or '').startswith('gb28181_'):
        from app.services.gb28181_sync_service import ensure_gb28181_virtual_device
        return ensure_gb28181_virtual_device(id, name=name)
    raise ValueError(f'设备 {id} 不存在，请先注册')


def _get_cameras() -> list[Device]:
    """获取所有设备"""
    return Device.query.all()


def _normalize_stream_source(source: str | None) -> str:
    """取流地址规范化，用于重复检测。"""
    return (source or '').strip()


def find_existing_device_for_register(
    *,
    ip: str = '',
    mac: str = '',
    serial_number: str = '',
    nvr_id: int | None = None,
    nvr_channel: int | None = None,
    source: str = '',
) -> Device | None:
    """网段登记或 NVR 通道挂载时查找已注册设备，避免重复创建。"""
    ip = (ip or '').strip()
    mac = (mac or '').strip()
    serial = (serial_number or '').strip()
    normalized_source = _normalize_stream_source(source)

    if nvr_id and nvr_channel and int(nvr_channel) > 0:
        existing = Device.query.filter_by(nvr_id=nvr_id, nvr_channel=int(nvr_channel)).first()
        if existing:
            return existing

    if nvr_id and ip:
        existing = Device.query.filter(Device.nvr_id == nvr_id, Device.ip == ip).first()
        if existing:
            return existing

    nvr_scope = bool(nvr_id)

    if mac:
        q = Device.query.filter(Device.mac == mac)
        if nvr_scope:
            q = q.filter(or_(Device.nvr_id.is_(None), Device.nvr_id == nvr_id))
        existing = q.first()
        if existing:
            return existing

    if serial:
        q = Device.query.filter(Device.serial_number == serial)
        if nvr_scope:
            q = q.filter(or_(Device.nvr_id.is_(None), Device.nvr_id == nvr_id))
        existing = q.first()
        if existing:
            return existing

    if normalized_source:
        q = Device.query.filter(Device.source == normalized_source)
        if nvr_scope:
            q = q.filter(or_(Device.nvr_id.is_(None), Device.nvr_id == nvr_id))
        existing = q.first()
        if existing:
            return existing
        # 已提供完整取流地址时，同一 IP 不同路径视为不同设备，不再按 IP 兜底
        return None

    if ip:
        existing = Device.query.filter(
            Device.ip == ip,
            or_(Device.nvr_id.is_(None), Device.nvr_channel == 0),
        ).first()
        if existing and (not nvr_scope or existing.nvr_id in (None, nvr_id)):
            return existing
        if not nvr_scope:
            existing = Device.query.filter_by(ip=ip).first()
            if existing:
                return existing

    return None


def _uses_direct_stream(camera: Device) -> bool:
    """设备已配置直连取流地址（RTSP/RTMP/国标），无需 ONVIF。"""
    src = (camera.source or '').strip().lower()
    return src.startswith(('rtsp://', 'rtmp://', 'gb28181://'))


def _is_custom_camera(camera: Device) -> bool:
    """直连/网段扫描登记设备：有取流地址即按表单信息入库，不走 ONVIF。"""
    if is_nvr_channel_device(camera):
        return True
    if _uses_direct_stream(camera):
        return True
    if not camera.source:
        return False
    if not camera.ip or not camera.ip.strip():
        return True
    return False


def is_device_available_for_stream(device: Device) -> bool:
    """设备是否允许启动推流。摄像头/NVR 通道常屏蔽 ICMP，不能仅用 ping 判定离线。"""
    if not device:
        return False

    source_lower = (device.source or '').strip().lower()
    if source_lower.startswith('rtmp://'):
        return False

    if _is_custom_camera(device):
        return True

    if device.channel_online is True:
        return True

    conn = (device.connection_status or '').strip().lower()
    if conn == 'online':
        return True

    if device.enable_forward and (device.http_stream or device.rtmp_stream):
        return True

    if device.ip and _monitor.is_watching(device.id) and _monitor.is_online(device.id):
        return True

    stream_source = (device.source or device.rtsp_direct or '').strip()
    if stream_source.startswith(('rtsp://', 'http://', 'https://', 'gb28181://')):
        return True

    return False


def _to_dict(camera: Device) -> dict:
    """设备对象转字典"""
    # 如果是RTMP设备或自定义摄像头，默认在线状态为True，不需要通过IP监控判断
    if camera.source and camera.source.strip().lower().startswith('rtmp://'):
        online_status = True
    elif _is_custom_camera(camera):
        # 自定义摄像头（通过视频源添加的）默认在线
        online_status = True
    else:
        online_status = is_device_available_for_stream(camera)
    
    source = (camera.source or '').strip()
    ingress_node_id = getattr(camera, 'ingress_node_id', None)
    ingress_summary = {
        'ingress_node_name': '本机（主节点）',
        'ingress_node_host': None,
        'ingress_node_status': 'online',
    }
    if ingress_node_id:
        try:
            node_id = int(ingress_node_id)
            cached = _ingress_node_summary_cache.get(node_id)
            if cached and time.monotonic() - cached[0] < 10:
                node = cached[1]
            else:
                from app.utils.node_client import get_node
                node = get_node(node_id)
                _ingress_node_summary_cache[node_id] = (time.monotonic(), node)
            ingress_summary = {
                'ingress_node_name': node.get('name') or f'边缘节点 #{ingress_node_id}',
                'ingress_node_host': node.get('host'),
                'ingress_node_status': node.get('status') or 'unknown',
            }
        except Exception:
            ingress_summary = {
                'ingress_node_name': f'边缘节点 #{ingress_node_id}',
                'ingress_node_host': None,
                'ingress_node_status': 'offline',
            }
    payload = {
        'id': camera.id,
        'name': camera.name,
        'source': camera.source,
        'rtmp_stream': camera.rtmp_stream,
        'http_stream': camera.http_stream,
        'ai_rtmp_stream': camera.ai_rtmp_stream,
        'ai_http_stream': camera.ai_http_stream,
        'enable_forward': camera.enable_forward,
        'stream': camera.stream,
        'ip': camera.ip,
        'port': camera.port,
        'username': camera.username,
        'mac': camera.mac,
        'manufacturer': camera.manufacturer,
        'model': camera.model,
        'firmware_version': camera.firmware_version,
        'serial_number': camera.serial_number,
        'hardware_id': camera.hardware_id,
        'support_move': camera.support_move,
        'support_zoom': camera.support_zoom,
        'ingress_node_id': ingress_node_id,
        **ingress_summary,
        'directory_id': camera.directory_id if camera.directory_id else None,
        'rtsp_direct': camera.rtsp_direct,
        'channel_online': camera.channel_online,
        'connection_status': camera.connection_status,
        'online': online_status,
        **_location_fields_for_device(camera),
        **nvr_fields_for_device(camera),
    }
    # nvr_fields_for_device 对无 NVR 的设备默认 device_kind=direct，需保留国标通道类型
    if source.lower().startswith('gb28181://'):
        payload['device_kind'] = 'gb28181'
    # 大疆机场 / 无人机：协议共用司空 OpenAPI，用 dji_device_type 区分展示
    try:
        from app.utils.flighthub_source import (
            is_dji_device,
            resolve_camera_index,
            resolve_device_type_from_record,
        )
        if is_dji_device(
            manufacturer=camera.manufacturer or '',
            model=camera.model or '',
            hardware_id=camera.hardware_id or '',
            source=source,
        ):
            dji_type = resolve_device_type_from_record(
                model=camera.model or '',
                name=camera.name or '',
                connection_status=camera.connection_status or '',
            )
            payload['device_kind'] = 'dji'
            payload['dji_device_type'] = dji_type
            payload['camera_index'] = resolve_camera_index(
                source=source,
                connection_status=camera.connection_status or '',
            )
            payload['has_skylink_token'] = bool(getattr(camera, 'skylink_token', None))
    except Exception:
        pass
    return payload


def _add_online_monitor():
    """初始化设备在线监控"""
    for camera in _get_cameras():
        # 判断是否是自定义摄像头
        is_custom = _is_custom_camera(camera)
        # 初始化已有设备时：自定义摄像头默认在线，其他设备检查实际在线状态
        if camera.ip:
            _monitor.update(camera.id, camera.ip, default_online=is_custom)
    logger.debug('设备在线状态监控服务已初始化')


def _discovery_cameras() -> list:
    """发现网络中的 ONVIF 设备（同网段 WS-Discovery，不含跨网段扫描）。"""
    wsd = WSDiscovery()
    wsd.start()
    onvif_cameras = []

    try:
        services = wsd.searchServices(
            scopes=[Scope("onvif://www.onvif.org/Profile")],
            timeout=2
        )

        for svc in services:
            try:
                ip_match = next(
                    (m[1] for m in
                     (re.search(r'(\d+\.\d+\.\d+\.\d+)', addr) for addr in svc.getXAddrs())
                     if m), None
                )
                if not ip_match:
                    continue

                mac_scope = next(
                    (str(scope).removeprefix('onvif://www.onvif.org/MAC/')
                     for scope in svc.getScopes()
                     if str(scope).startswith('onvif://www.onvif.org/MAC/')),
                    None
                )

                name_scope = next(
                    (str(scope).removeprefix('onvif://www.onvif.org/name/')
                     for scope in svc.getScopes()
                     if str(scope).startswith('onvif://www.onvif.org/name/')),
                    None
                )

                onvif_cameras.append({
                    'mac': mac_scope,
                    'ip': ip_match,
                    'hardware_name': name_scope
                })
            except Exception:
                continue
    finally:
        wsd.stop()
        if hasattr(wsd, '_stopThreads'):
            wsd._stopThreads()

    return onvif_cameras


def _get_local_ipv4_addresses() -> list[str]:
    """获取本机有效IPv4地址（过滤回环地址）。"""
    candidates: list[str] = []

    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = item[4][0]
            if ip and ip != '127.0.0.1':
                candidates.append(ip)
    except Exception:
        pass

    # 通过默认出口再补充一个IP（不真正发包）
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(('8.8.8.8', 80))
        ip = sock.getsockname()[0]
        sock.close()
        if ip and ip != '127.0.0.1':
            candidates.append(ip)
    except Exception:
        pass

    result = []
    seen = set()
    for ip in candidates:
        if ip in seen:
            continue
        seen.add(ip)
        result.append(ip)
    return result


def _get_host_ip_for_stream_urls() -> str:
    """解析用于 RTMP/HTTP 播放与 AI 流地址中的宿主机 IP。

    Docker ``network_mode: host`` 下与宿主机同网卡；优先 ``netifaces`` + Linux 默认路由，
    避免 hostname/Docker 桥接地址误判。

    优先级：环境变量 POD_IP > netifaces（默认路由网卡 / 私网优先）> getaddrinfo+UDP 补充 >
    UDP 出口探测 > 127.0.0.1。
    """
    explicit = (os.getenv('POD_IP') or '').strip()
    if explicit:
        return explicit

    ip_nf = resolve_ipv4_for_stream_urls()
    if ip_nf:
        return ip_nf

    for ip in _get_local_ipv4_addresses():
        if ip.startswith('169.254.'):
            continue
        return ip

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(('8.8.8.8', 80))
        ip = sock.getsockname()[0]
        sock.close()
        if ip and ip != '127.0.0.1' and not ip.startswith('169.254.'):
            return ip
    except Exception:
        pass

    logger.warning('无法探测宿主机 IP，流地址中的主机名将回退为 127.0.0.1')
    return '127.0.0.1'


def _legacy_local_stream_urls(device_id: str) -> tuple[str, str, str, str]:
    """本机 SRS 默认流地址（不经过媒体节点池）。"""
    host = _get_host_ip_for_stream_urls()
    return (
        f'rtmp://{host}:1935/live/{device_id}',
        f'http://{host}:8080/live/{device_id}.flv',
        f'rtmp://{host}:1935/ai/{device_id}',
        f'http://{host}:8080/ai/{device_id}.flv',
    )


def _default_stream_urls(device_id: str) -> tuple[str, str, str, str]:
    """生成 live 与 ai 的 RTMP、HTTP-FLV 地址；启用媒体节点池时经 iot-node 调度。"""
    try:
        from app.utils.media_client import (
            allocate_device_media,
            is_media_pool_enabled,
            stream_urls_from_binding,
        )
        if is_media_pool_enabled():
            binding = allocate_device_media(device_id)
            return stream_urls_from_binding(binding)
    except Exception as e:
        logger.warning('媒体节点池分配失败 device_id=%s，回退本机地址: %s', device_id, e)

    return _legacy_local_stream_urls(device_id)


def gb28181_device_stream_urls(device_id: str) -> tuple[str, str, str, str]:
    """国标虚拟设备：播放走 WVP 点播，仅生成算法任务用的 AI 推流地址。"""
    try:
        from app.utils.media_client import (
            allocate_device_media,
            is_media_pool_enabled,
            stream_urls_from_binding,
        )
        if is_media_pool_enabled():
            binding = allocate_device_media(
                device_id,
                need_srs_live=False,
                need_srs_ai=True,
                need_zlm=True,
            )
            _, _, ai_rtmp_stream, ai_http_stream = stream_urls_from_binding(binding)
            return '', '', ai_rtmp_stream, ai_http_stream
    except Exception as e:
        logger.warning('国标设备媒体节点池分配失败 device_id=%s，回退本机地址: %s', device_id, e)

    _, _, ai_rtmp_stream, ai_http_stream = _legacy_local_stream_urls(device_id)
    return '', '', ai_rtmp_stream, ai_http_stream


def resolve_device_ai_rtmp_stream(device) -> str | None:
    """算法任务输出流：优先 ai_rtmp_stream，否则 rtmp_stream；国标设备缺失时按 device_id 生成。"""
    ai_rtmp = (device.ai_rtmp_stream or '').strip()
    if ai_rtmp:
        return ai_rtmp
    rtmp = (device.rtmp_stream or '').strip()
    if rtmp:
        return rtmp
    source = (device.source or '').strip()
    if source.lower().startswith('gb28181://'):
        return _default_stream_urls(device.id)[2]
    return None


def _update_camera_ip(camera: Device, ip: str):
    """更新设备 IP（不自动 ONVIF，仅更新监控目标）。"""
    camera.ip = ip
    if camera.ip:
        _monitor.update(camera.id, camera.ip, default_online=True)
    db.session.commit()
    logger.info(f'设备 {camera.id} IP已更新为 {ip}')


def refresh_camera(app=None):
    """刷新设备IP信息"""
    dis_cameras = _discovery_cameras()
    
    # 如果没有传入app，尝试使用current_app（在请求上下文中）
    if app is None:
        try:
            from flask import current_app
            app = current_app._get_current_object()
        except RuntimeError:
            logger.error('refresh_camera: 无法获取应用上下文，请传入app参数')
            return
    
    with app.app_context():
        for dis_cam in dis_cameras:
            if not dis_cam['mac']:
                continue

            camera = Device.query.filter(Device.mac == dis_cam["mac"]).one_or_none()
            if camera and camera.ip != dis_cam['ip']:
                try:
                    old_ip = camera.ip
                    _update_camera_ip(camera, dis_cam['ip'])
                    logger.info(f'设备 {camera.id} IP地址已从 {old_ip} 更新为 {dis_cam["ip"]}')
                except Exception as e:
                    logger.error(f'刷新设备 {camera.id} IP失败: {str(e)}')


def search_camera() -> list:
    """搜索网络中的ONVIF设备"""
    return _discovery_cameras()


def _start_search(app=None):
    """启动在线监控；不再自动连接 ONVIF（仅保留按需接口 register_camera_by_onvif / PTZ）。"""
    ws_daemonlogger = logging.getLogger('daemon')
    ws_daemonlogger.setLevel(logging.ERROR)

    _init_all_cameras()
    _add_online_monitor()


def _init_all_cameras():
    """启动时修复 NVR 关联并注册 IP 可达性监控，不预连 ONVIF。"""
    try:
        repair_nvr_channel_links()
    except Exception as e:
        logger.warning(f'修复 NVR 通道关联失败: {e}')
    logger.debug('设备启动初始化完成（已跳过自动 ONVIF 连接）')


def _get_stream(rtsp_url: str, stream: int) -> str:
    """根据设备类型生成指定码流URL"""
    if stream is None:
        return rtsp_url

    # 如果stream为0，表示使用默认码流，返回原始URL
    if stream == 0:
        return rtsp_url

    # 海康威视设备
    if re.match(r'rtsp://[^/]*/Streaming/Channels/10\d.*', rtsp_url):
        if not (1 <= stream <= 3):
            raise ValueError('海康设备仅支持码流类型: 0[默认], 1[主码流], 2[子码流], 3[第三码流]')
        return re.sub(r'Channels/10\d', f'Channels/10{stream}', rtsp_url)

    # 大华设备
    elif re.match(r'rtsp://[^/]*/cam/realmonitor\?channel=\d+&subtype=\d+.*', rtsp_url):
        if not (1 <= stream <= 2):
            raise ValueError('大华设备仅支持码流类型: 0[默认], 1[主码流], 2[辅码流]')
        return re.sub(r'subtype=\d', f'subtype={stream - 1}', rtsp_url)

    # 宇视设备
    elif re.match(r'rtsp://[^/]*/unicast/c\d+/s\d+/live.*', rtsp_url):
        if not (1 <= stream <= 2):
            raise ValueError('宇视设备仅支持码流类型: 0[默认], 1[主码流], 2[辅码流]')
        # 宇视设备：0=主码流, 1=辅码流，所以stream=1时用0，stream=2时用1
        stream_type = stream - 1
        return re.sub(r'/s\d+/', f'/s{stream_type}/', rtsp_url)

    # 对于不支持的设备类型，记录警告并返回原始URL
    logger.warning(f'设备RTSP地址 {rtsp_url[:50]}... 不支持码流调整功能，将使用原始URL')
    return rtsp_url


def _generate_stream_urls(source: str, device_id: str) -> tuple[str, str, str, str]:
    """根据源地址生成RTMP和HTTP播放地址，以及AI推流地址和AI HTTP地址
    
    Args:
        source: 源地址（RTSP、RTMP或HTTP）
        device_id: 设备ID
        
    Returns:
        tuple: (rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream)
    """
    source_lower = source.strip().lower()
    
    # 判断是否是RTMP流
    is_rtmp = source_lower.startswith('rtmp://')
    
    # 判断是否是HTTP流
    is_http = source_lower.startswith('http://') or source_lower.startswith('https://')
    
    if is_rtmp:
        # RTMP地址格式：rtmp://ip:port/path 或 rtmp://domain/path 或 rtmp://ip/path 或 rtmp://ip:port
        rtmp_pattern = r'rtmp://([^:/]+)(?::(\d+))?(?:/(.*))?'
        match = re.match(rtmp_pattern, source)
        if match:
            server = match.group(1)
            port = match.group(2) or '1935'
            path = match.group(3) or f'live/{device_id}'
            
            # 生成RTMP播放地址（使用源路径）
            rtmp_stream = f"rtmp://{server}:{port}/{path}"
            
            # 生成HTTP播放地址（使用8080端口，添加.flv后缀）
            # 如果路径已经包含.flv，则不重复添加
            if path.endswith('.flv'):
                http_path = path
            else:
                http_path = f"{path}.flv"
            # HTTP流地址默认使用8080端口
            http_stream = f"http://{server}:8080/{http_path}"
            
            # AI流地址使用不同的路径前缀
            ai_path = f"ai/{device_id}" if not path.startswith('ai/') else path
            ai_rtmp_stream = f"rtmp://{server}:{port}/{ai_path}"
            if ai_path.endswith('.flv'):
                ai_http_path = ai_path
            else:
                ai_http_path = f"{ai_path}.flv"
            ai_http_stream = f"http://{server}:8080/{ai_http_path}"
            
            return rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream
        else:
            # 如果解析失败，使用默认格式（宿主机 IP）
            return _default_stream_urls(device_id)
    elif is_http:
        # HTTP地址格式：http://ip:port/path 或 https://ip:port/path
        http_pattern = r'(https?)://([^:/]+)(?::(\d+))?(?:/(.*))?'
        match = re.match(http_pattern, source)
        if match:
            protocol = match.group(1)  # http 或 https
            server = match.group(2)
            port = match.group(3) or ('443' if protocol == 'https' else '8080')
            path = match.group(4) or f'live/{device_id}'
            
            # HTTP设备不需要RTMP流，使用空字符串或默认值
            rtmp_stream = f"rtmp://{server}:1935/live/{device_id}"
            # HTTP播放地址直接使用源地址的端口和路径
            http_stream = f"{protocol}://{server}:{port}/{path}"
            
            # AI流地址
            ai_rtmp_stream = f"rtmp://{server}:1935/ai/{device_id}"
            ai_http_stream = f"{protocol}://{server}:{port}/ai/{device_id}.flv"
            
            return rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream
        else:
            # 如果解析失败，使用默认格式（宿主机 IP）
            return _default_stream_urls(device_id)
    else:
        # RTSP流，使用设备ID与宿主机 IP 生成默认地址
        return _default_stream_urls(device_id)


def _onvif_username_candidates(username: str | None) -> list[str]:
    """生成 ONVIF 登录用户名候选列表。已提供用户名时仅尝试该用户名，避免多用户名试探导致设备锁定。"""
    if username is not None and str(username).strip() != '':
        return [str(username).strip()]
    return ['admin', 'Administrator', 'root', '']


def _format_onvif_register_error(ip: str, port: int, last_error: str | None) -> str:
    """将 ONVIF 连接失败整理为可读的注册错误信息。"""
    detail = (last_error or '').strip()
    if 'locked' in detail.lower() or '锁定' in detail:
        return (
            f'设备 {ip}:{port} 因多次错误登录已被锁定，请等待约 30 分钟后重试，'
            f'或到摄像机 Web 管理页解锁后再注册'
        )
    if detail:
        return f'无法连接到设备 {ip}:{port}：{detail}'
    return f'无法连接到设备 {ip}:{port}，请检查 IP、端口、用户名和密码是否正确'


def register_camera_by_onvif(
    ip: str,
    port: int,
    password: str,
    username: str | None = None,
    ingress_node_id: int | None = None,
) -> str:
    """通过ONVIF搜索并自动注册摄像头
    
    Args:
        ip: 摄像头IP地址
        port: 摄像头端口
        password: 摄像头密码
        username: 摄像头用户名（可选；未提供时依次尝试常见默认用户名）
        
    Returns:
        设备ID
        
    Raises:
        ValueError: 参数验证失败
        RuntimeError: 设备连接或注册失败
    """
    if not ip or not ip.strip():
        raise ValueError('摄像头IP地址不能为空')
    if not port or port <= 0:
        raise ValueError('摄像头端口必须大于0')
    if not password or not password.strip():
        raise ValueError('摄像头密码不能为空')
    
    used_username = (username or '').strip()
    if ingress_node_id:
        from app.utils.node_client import camera_access
        camera_info = camera_access(int(ingress_node_id), 'probe-onvif', {
            'ip': ip,
            'port': port,
            'username': used_username,
            'password': password,
        })
        if not isinstance(camera_info, dict):
            raise RuntimeError('边缘节点未返回有效的 ONVIF 设备信息')
    else:
        onvif_cam = None
        used_username = None
        last_error: str | None = None
        temp_id = 'temp_' + str(time.time_ns())  # 临时ID用于连接测试

        for candidate in _onvif_username_candidates(username):
            try:
                onvif_cam = _create_onvif_camera(
                    temp_id, ip, port, candidate, password
                )
                used_username = candidate
                logger.info(f'使用用户名 "{candidate}" 成功连接到设备 {ip}:{port}')
                break
            except Exception as e:
                last_error = str(e)
                logger.debug(f'使用用户名 "{candidate}" 连接设备 {ip}:{port} 失败: {last_error}')

        if onvif_cam is None:
            raise RuntimeError(_format_onvif_register_error(ip, port, last_error))
        camera_info = onvif_cam.get_info()

    used_username = str(camera_info.get('username') or used_username or '').strip()
    # 检查设备是否已存在（通过MAC地址）
    mac = camera_info.get('mac')
    
    existing_camera = find_existing_device_for_register(
        ip=ip,
        mac=mac or '',
        serial_number=(camera_info.get('serial_number') or '').strip(),
    )
    if existing_camera:
        update_camera(
            existing_camera.id,
            {
                'ip': ip,
                'port': port,
                'username': used_username,
                'password': password,
                'source': camera_info.get('source'),
                'mac': mac,
                'manufacturer': camera_info.get('manufacturer'),
                'model': camera_info.get('model'),
                'firmware_version': camera_info.get('firmware_version'),
                'serial_number': camera_info.get('serial_number'),
                'ingress_node_id': ingress_node_id,
            },
        )
        try:
            from app.services.stream_forward_service import ensure_device_stream_forward_task
            ensure_device_stream_forward_task(existing_camera.id)
        except Exception as e:
            logger.warning(f'同步设备 {existing_camera.id} 接入节点失败: {e}')
        logger.info(f'设备 {existing_camera.id} 已存在，已更新（ONVIF 登记）')
        return existing_camera.id
    
    # 生成设备ID
    device_id = str(time.time_ns())
    if _get_camera(device_id):
        device_id = str(time.time_ns())  # 如果冲突，重新生成
    
    # 创建设备记录
    # 获取制造商和型号，确保不为空
    manufacturer = camera_info.get('manufacturer', '').strip() if camera_info.get('manufacturer') else ''
    model = camera_info.get('model', '').strip() if camera_info.get('model') else ''
    
    # 如果ONVIF获取的信息中manufacturer或model为空，使用专业的默认值
    if not manufacturer:
        manufacturer = 'EasyAIoT'
    if not model:
        model = 'Camera-EasyAIoT'
    
    # 生成RTMP和HTTP播放地址，以及AI流地址
    source = camera_info.get('source', '')
    if source:
        rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream = _generate_stream_urls(source, device_id)
    else:
        rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream = _default_stream_urls(device_id)
    
    camera = Device(
        id=device_id,
        name=f'Camera-{device_id[:6]}',
        source=camera_info.get('source'),
        rtmp_stream=rtmp_stream,
        http_stream=http_stream,
        ai_rtmp_stream=ai_rtmp_stream,
        ai_http_stream=ai_http_stream,
        stream=None,
        ip=camera_info.get('ip'),
        port=camera_info.get('port', port),
        username=used_username,
        password=password,
        mac=camera_info.get('mac'),
        manufacturer=manufacturer,
        model=model,
        firmware_version=camera_info.get('firmware_version'),
        serial_number=camera_info.get('serial_number'),
        hardware_id=camera_info.get('hardware_id'),
        support_move=camera_info.get('support_move', False),
        support_zoom=camera_info.get('support_zoom', False),
        nvr_id=None,
        nvr_channel=0,
        ingress_node_id=ingress_node_id,
        directory_id=directory_id_for_new_device(),
    )
    
    db.session.add(camera)
    try:
        db.session.commit()
        _monitor.update(camera.id, camera.ip)
        logger.info(f'设备 {device_id} 通过ONVIF注册成功，IP: {camera.ip}, 用户名: {used_username}')
        
        # 自动为设备创建抓拍空间
        try:
            from app.services.snap_space_service import create_snap_space_for_device
            create_snap_space_for_device(device_id, camera.name)
            logger.info(f'设备 {device_id} 的抓拍空间已自动创建')
        except Exception as e:
            logger.warning(f'为设备 {device_id} 创建抓拍空间失败: {str(e)}，但不影响设备注册')
        
        # 自动为设备创建监控录像空间
        try:
            from app.services.record_space_service import create_record_space_for_device
            create_record_space_for_device(device_id, camera.name)
            logger.info(f'设备 {device_id} 的监控录像空间已自动创建')
        except Exception as e:
            logger.warning(f'为设备 {device_id} 创建监控录像空间失败: {str(e)}，但不影响设备注册')

        try:
            from app.services.stream_forward_service import ensure_device_stream_forward_task
            ensure_device_stream_forward_task(device_id)
        except Exception as e:
            logger.warning(f'为设备 {device_id} 自动创建推流任务失败: {e}')
        
        return device_id
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f'数据库提交失败: {str(e)}')


def register_camera(register_info: dict) -> str:
    """注册设备到数据库（直连取流）。

    须传入 ``source``（RTSP/RTMP 等）；不再自动 ONVIF。
    ONVIF 发现请使用 ``register_camera_by_onvif`` 或 ``/register/device/onvif``。
    """
    id = register_info.get('id') or str(time.time_ns())
    if _get_camera(id):
        raise ValueError('设备ID已存在，请使用唯一标识符')

    # 如果传入了source字段，直接使用，不再通过ONVIF搜索
    if register_info.get('source'):
        # 直接注册模式：使用用户提供的source字段
        source = register_info.get('source')
        name = register_info.get('name', f'Camera-{id[:6]}')
        camera_type = register_info.get('cameraType', '')
        ingress_node_id = register_info.get('ingress_node_id')
        if ingress_node_id not in (None, '', 0, '0'):
            try:
                ingress_node_id = int(ingress_node_id)
            except (TypeError, ValueError) as exc:
                raise ValueError('接入节点 ID 无效') from exc
            from app.utils.node_client import camera_access
            camera_access(ingress_node_id, 'probe-stream', {'source': source, 'timeout': 10})
        else:
            ingress_node_id = None
        
        # 判断是否是RTMP流
        is_rtmp = source.strip().lower().startswith('rtmp://')
        is_custom = camera_type == 'custom'
        
        # 从source中提取IP和端口（如果可能）
        ip = register_info.get('ip', '')
        port = register_info.get('port', 554)
        username = register_info.get('username', '')
        password = register_info.get('password', '')
        
        # 尝试从RTSP/RTMP地址中提取IP和端口
        if is_rtmp:
            # RTMP地址格式：rtmp://ip:port/path 或 rtmp://domain/path 或 rtmp://ip/path
            # RTMP通常不需要认证，所以不提取用户名密码
            rtmp_pattern = r'rtmp://([^:/]+)(?::(\d+))?(?:/.*)?'
            match = re.match(rtmp_pattern, source)
            if match:
                extracted_ip = match.group(1)
                extracted_port = match.group(2)
                if not ip:
                    ip = extracted_ip
                if not port:
                    if extracted_port:
                        port = int(extracted_port)
                    else:
                        port = 1935  # RTMP默认端口
            logger.info(f'设备 {id} 是RTMP流，从地址中提取IP: {ip}, 端口: {port}')
        else:
            auth = parse_rtsp_auth(source)
            extracted_ip = auth.get("hostname")
            extracted_port = auth.get("port")
            extracted_username = auth.get("username")
            extracted_password = auth.get("password")
            if not ip and extracted_ip:
                ip = extracted_ip
            if not port and extracted_port:
                port = int(extracted_port)
            if not username and extracted_username:
                username = extracted_username
            if not password and extracted_password:
                password = extracted_password
        
        # NVR 挂载通道或显式 skip_onvif：仅用枚举/表单字段，不逐台 ONVIF
        camera_info = {}
        is_nvr_channel = (
            bool(register_info.get('nvr_id'))
            or register_info.get('skip_onvif')
            or int(register_info.get('nvr_channel') or 0) > 0
            or (register_info.get('model') or '').strip() == 'NVR-Channel'
        )
        if is_nvr_channel:
            logger.info(f'设备 {id} 为 NVR 挂载通道，跳过 ONVIF 信息获取')
        else:
            logger.info(f'设备 {id} 使用取流地址直连登记，跳过 ONVIF 信息获取')
        
        # 获取制造商和型号，确保不为空
        manufacturer = register_info.get('manufacturer') or camera_info.get('manufacturer', '')
        model = register_info.get('model') or camera_info.get('model', '')
        
        # 如果manufacturer或model为空，使用默认值
        if not manufacturer or not manufacturer.strip():
            manufacturer = 'EasyAIoT'
        if not model or not model.strip():
            model = 'Camera-EasyAIoT'
        
        # 生成RTMP和HTTP播放地址，以及AI流地址
        if source.strip().lower().startswith('gb28181://'):
            rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream = gb28181_device_stream_urls(id)
        else:
            rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream = _generate_stream_urls(source, id)
        
        nvr_id, nvr_channel = resolve_nvr_link(register_info)
        if not nvr_id:
            inferred_id, inferred_ch = infer_nvr_link_from_source(source)
            if inferred_id:
                nvr_id = inferred_id
                if inferred_ch and not nvr_channel:
                    nvr_channel = inferred_ch
                is_nvr_channel = True
        reg_mac = (register_info.get('mac') or camera_info.get('mac') or '').strip()
        reg_serial = (register_info.get('serial_number') or camera_info.get('serial_number') or '').strip()
        existing = find_existing_device_for_register(
            ip=ip or '',
            mac=reg_mac,
            serial_number=reg_serial,
            nvr_id=nvr_id,
            nvr_channel=nvr_channel if nvr_channel else None,
            source=source,
        )
        if existing:
            id = existing.id
            if source.strip().lower().startswith('gb28181://'):
                rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream = gb28181_device_stream_urls(id)
            else:
                rtmp_stream, http_stream, ai_rtmp_stream, ai_http_stream = _generate_stream_urls(source, id)
            existing.name = name
            existing.source = source
            existing.rtmp_stream = rtmp_stream
            existing.http_stream = http_stream
            existing.ai_rtmp_stream = ai_rtmp_stream
            existing.ai_http_stream = ai_http_stream
            existing.stream = register_info.get('stream', existing.stream or 0)
            existing.ip = ip or ''
            existing.port = port
            existing.username = username
            existing.password = password
            if 'skylink_token' in register_info:
                existing.skylink_token = register_info.get('skylink_token') or None
            existing.mac = reg_mac or existing.mac
            existing.manufacturer = manufacturer.strip()
            existing.model = model.strip()
            existing.firmware_version = register_info.get('firmware_version') or camera_info.get('firmware_version', '') or existing.firmware_version
            existing.serial_number = reg_serial or existing.serial_number
            existing.hardware_id = register_info.get('hardware_id') or camera_info.get('hardware_id', '') or existing.hardware_id
            existing.support_move = register_info.get('support_move') if register_info.get('support_move') is not None else camera_info.get('support_move', existing.support_move)
            existing.support_zoom = register_info.get('support_zoom') if register_info.get('support_zoom') is not None else camera_info.get('support_zoom', existing.support_zoom)
            existing.nvr_id = int(nvr_id) if nvr_id else None
            existing.nvr_channel = nvr_channel or 0
            existing.ingress_node_id = ingress_node_id
            existing.rtsp_direct = register_info.get('rtsp_direct')
            existing.channel_online = register_info.get('channel_online')
            if register_info.get('connection_status') is not None:
                existing.connection_status = register_info.get('connection_status')
            if register_info.get('enable_forward') is not None:
                existing.enable_forward = register_info.get('enable_forward')
            camera = existing
            logger.info(f'设备 {id} 已存在，已更新（网段/直连登记）')
        else:
            # 创建设备记录，优先使用用户提供的字段，缺失的字段从ONVIF获取的信息中填充
            camera = Device(
                id=id,
                name=name,
                source=source,
                rtmp_stream=rtmp_stream,
                http_stream=http_stream,
                ai_rtmp_stream=ai_rtmp_stream,
                ai_http_stream=ai_http_stream,
                stream=register_info.get('stream', 0),
                ip=ip or '',
                port=port,
                username=username,
                password=password,
                skylink_token=register_info.get('skylink_token') or None,
                mac=reg_mac,
                manufacturer=manufacturer.strip(),
                model=model.strip(),
                firmware_version=register_info.get('firmware_version') or camera_info.get('firmware_version', ''),
                serial_number=reg_serial,
                hardware_id=register_info.get('hardware_id') or camera_info.get('hardware_id', ''),
                support_move=register_info.get('support_move') if register_info.get('support_move') is not None else camera_info.get('support_move', False),
                support_zoom=register_info.get('support_zoom') if register_info.get('support_zoom') is not None else camera_info.get('support_zoom', False),
                nvr_id=int(nvr_id) if nvr_id else None,
                nvr_channel=nvr_channel,
                ingress_node_id=ingress_node_id,
                rtsp_direct=register_info.get('rtsp_direct'),
                channel_online=register_info.get('channel_online'),
                connection_status=register_info.get('connection_status'),
                enable_forward=register_info.get('enable_forward'),
                directory_id=directory_id_for_new_device(register_info),
            )
            db.session.add(camera)
        try:
            if any(k in register_info for k in ('longitude', 'latitude', 'altitude', 'address', 'heading', 'location_source')):
                try:
                    _apply_location_updates(camera, register_info)
                except Exception as loc_err:
                    logger.warning(f'设备 {id} 位置信息写入失败: {loc_err}')
            db.session.commit()
            if ip and not is_nvr_channel:
                # 自定义摄像头默认在线；NVR 通道不启动 IPC 在线探测
                is_custom = is_custom or is_rtmp
                _monitor.update(camera.id, ip, default_online=is_custom)
            elif is_custom or is_rtmp:
                # 自定义摄像头或RTMP流即使没有IP也默认在线（在_to_dict中处理）
                logger.debug(f'设备 {id} 是自定义摄像头或RTMP流，无需IP监控')
            logger.info(f'设备 {id} 注册成功（直接模式），RTSP地址: {source}')
            
            # 自动为设备创建抓拍空间
            try:
                from app.services.snap_space_service import create_snap_space_for_device
                create_snap_space_for_device(id, name)
                # 自动为设备创建监控录像空间
                try:
                    from app.services.record_space_service import create_record_space_for_device
                    create_record_space_for_device(id, name)
                    logger.info(f'设备 {id} 的监控录像空间已自动创建')
                except Exception as e:
                    logger.warning(f'为设备 {id} 创建监控录像空间失败: {str(e)}，但不影响设备注册')
                logger.info(f'设备 {id} 的抓拍空间已自动创建')
            except Exception as e:
                logger.warning(f'为设备 {id} 创建抓拍空间失败: {str(e)}，但不影响设备注册')
            
            # 自动检查并创建推流转发任务
            # GB28181 虚拟摄像头由算法任务在运行时动态向 WVP 拉流，不需要创建独立推流转发任务
            # NVR 挂载通道批量登记时不自动建推流任务，避免逐路拉流阻塞
            if not is_nvr_channel and not source.strip().lower().startswith('gb28181://'):
                try:
                    from app.services.stream_forward_service import ensure_device_stream_forward_task
                    ensure_device_stream_forward_task(id)
                except Exception as e:
                    logger.warning(f'为设备 {id} 自动创建推流转发任务失败: {str(e)}，但不影响设备注册')
            
            return id
        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'数据库提交失败: {str(e)}')
    
    # 无 source 时不再自动 ONVIF，请使用专用接口或填写 RTSP 地址
    raise ValueError(
        '请提供 source（RTSP/RTMP 取流地址）；若需 ONVIF 发现请调用 /register/device/onvif'
    )


def ensure_device_spaces(device_id: str):
    """确保设备有对应的抓拍空间和录像空间，如果没有则自动创建
    
    Args:
        device_id: 设备ID
    """
    try:
        from app.services.snap_space_service import get_snap_space_by_device_id, create_snap_space_for_device
        from app.services.record_space_service import get_record_space_by_device_id, create_record_space_for_device
        
        camera = _get_camera(device_id)
        if not camera:
            return  # 设备不存在，直接返回
        
        # 检查并创建抓拍空间
        snap_space = get_snap_space_by_device_id(device_id)
        if not snap_space:
            try:
                create_snap_space_for_device(device_id, camera.name)
                logger.info(f'设备 {device_id} 的抓拍空间已自动创建')
            except Exception as e:
                logger.warning(f'为设备 {device_id} 自动创建抓拍空间失败: {str(e)}')
        
        # 检查并创建录像空间
        record_space = get_record_space_by_device_id(device_id)
        if not record_space:
            try:
                create_record_space_for_device(device_id, camera.name)
                logger.info(f'设备 {device_id} 的监控录像空间已自动创建')
            except Exception as e:
                logger.warning(f'为设备 {device_id} 自动创建监控录像空间失败: {str(e)}')
    except Exception as e:
        logger.warning(f'检查设备 {device_id} 空间失败: {str(e)}')


def get_device_location_info(device_id: str, *, ensure_name: str | None = None) -> dict:
    """获取设备坐标信息；国标虚拟通道不存在时按需入库。"""
    camera = _get_camera_for_location(device_id, name=ensure_name)
    payload = _to_dict(camera)
    return {
        'id': camera.id,
        'name': camera.name,
        'device_kind': payload.get('device_kind'),
        **_location_fields_for_device(camera),
    }


def resolve_device_inference_input(device_id: str) -> dict:
    """为模型推理解析设备可取流的输入地址（含国标 WVP 点播解析）。"""
    from app.services.stream_url_sync_service import resolve_device_stream_urls
    from app.utils.gb28181_source import is_gb28181_source, resolve_gb28181_source

    camera = _get_camera(device_id)
    if not camera:
        raise ValueError(f'设备 {device_id} 不存在')

    source = (camera.source or '').strip()
    rtsp_direct = (camera.rtsp_direct or '').strip()
    rtmp_stream, http_stream, _, _ = resolve_device_stream_urls(camera)
    rtmp_stream = (rtmp_stream or camera.rtmp_stream or '').strip()
    http_stream = (http_stream or camera.http_stream or '').strip()

    resolved_source = None
    is_gb28181 = is_gb28181_source(source)
    if is_gb28181:
        resolved_source = resolve_gb28181_source(source, logger=logger)
    elif source.lower().startswith(('rtsp://', 'rtmp://')):
        resolved_source = source
    elif rtsp_direct.lower().startswith(('rtsp://', 'rtmp://')):
        resolved_source = rtsp_direct

    return {
        'device_id': device_id,
        'source': source or None,
        'rtsp_direct': rtsp_direct or None,
        'rtmp_stream': rtmp_stream or None,
        'http_stream': http_stream or None,
        'resolved_source': (resolved_source or '').strip() or None,
        'is_gb28181': is_gb28181,
    }


def get_camera_info(id: str, *, ensure_name: str | None = None) -> dict:
    """获取设备基本信息"""
    camera = _get_camera_for_location(id, name=ensure_name)

    # 确保设备有对应的抓拍空间和录像空间
    ensure_device_spaces(id)

    return _to_dict(camera)


def get_camera_list() -> list:
    """获取所有设备信息列表"""
    cameras = _get_cameras()
    
    # 确保所有设备都有对应的抓拍空间和录像空间
    for camera in cameras:
        try:
            ensure_device_spaces(camera.id)
        except Exception as e:
            logger.warning(f'检查设备 {camera.id} 空间时出错: {str(e)}')
    
    return [_to_dict(camera) for camera in cameras]


def get_device_list() -> dict:
    """从数据库获取所有设备"""
    devices = Device.query.all()
    
    # 确保所有设备都有对应的抓拍空间和录像空间
    for device in devices:
        try:
            ensure_device_spaces(device.id)
        except Exception as e:
            logger.warning(f'检查设备 {device.id} 空间时出错: {str(e)}')
    
    device_list = [_to_dict(device) for device in devices]

    # 计算统计信息
    total = len(device_list)
    online = sum(1 for dev in device_list if dev['online'])

    return {
        'list': device_list,
        'total': total,
        'online': online,
    }


def update_camera(id: str, update_info: dict):
    """更新设备信息"""
    camera = _get_camera(id)
    if not camera:
        raise ValueError(f'设备 {id} 不存在，无法修改')
    
    # 确保设备有对应的抓拍空间和录像空间
    ensure_device_spaces(id)

    _apply_location_updates(camera, update_info)
    update_info = {k: v for k, v in update_info.items() if k not in _LOCATION_FIELD_KEYS}

    # 保存旧的设备名称，用于后续同步更新空间名称
    old_device_name = camera.name
    device_name_changed = False
    
    # 检查是否是自定义摄像头（通过cameraType字段或设备特征判断）
    # cameraType字段只在前端传递，不保存到数据库，用于判断设备类型
    is_custom_from_request = update_info.get('cameraType') == 'custom'

    _NVR_PAYLOAD_KEYS = frozenset({
        'nvr', 'nvr_ip', 'nvr_port', 'nvr_name', 'nvr_username', 'nvr_password',
        'nvr_vendor', 'nvr_model', 'nvr_serial', 'nvr_firmware', 'nvr_device_type', 'nvr_mac',
        'nvr_scheme', 'nvr_rtsp_url', 'nvr_source',
    })
    if any(k in update_info for k in ('nvr_id', 'nvr_channel', *_NVR_PAYLOAD_KEYS)):
        nvr_id, nvr_channel = resolve_nvr_link(update_info)
        camera.nvr_id = nvr_id
        camera.nvr_channel = nvr_channel

    # 过滤空值并更新字段
    for k, v in (item for item in update_info.items() if item[1] is not None):
        if k in _NVR_PAYLOAD_KEYS or k in ('nvr_id', 'nvr_channel'):
            continue
        if k in ('rtsp_direct', 'channel_online', 'connection_status') and hasattr(camera, k):
            setattr(camera, k, v)
            continue
        if hasattr(camera, k):
            # 对于布尔值字段，处理空字符串和字符串类型的布尔值
            if k in ['enable_forward', 'support_move', 'support_zoom']:
                # 如果是空字符串，跳过该字段的更新
                if v == '':
                    continue
                # 如果是字符串类型的布尔值，转换为布尔值
                if isinstance(v, str):
                    v = v.lower() in ('true', '1', 'yes', 'on')
                # 确保是布尔类型
                v = bool(v) if v is not None else None
            # 对于manufacturer和model字段，确保去除首尾空格，如果为空则使用默认值
            elif k in ['manufacturer', 'model'] and isinstance(v, str):
                v = v.strip()
                if not v:
                    if k == 'manufacturer':
                        v = 'EasyAIoT'
                    else:
                        v = 'Camera-EasyAIoT'
            # 对于port字段，确保转换为整数类型
            elif k == 'port':
                try:
                    v = int(v) if v else None
                except (ValueError, TypeError):
                    raise ValueError(f'端口值无效: {v}，必须是数字')
            # 检查设备名称是否发生变化
            elif k == 'name':
                # 处理字符串类型的名称，去除首尾空格
                if isinstance(v, str):
                    v = v.strip()
                # 检查名称是否真的发生了变化
                if v != old_device_name:
                    device_name_changed = True
            setattr(camera, k, v)

    # 处理码流变更
    if 'stream' in update_info:
        try:
            camera.source = _get_stream(camera.source, update_info['stream'])
        except Exception as e:
            raise RuntimeError(f'码流调整失败: {str(e)}')

    # NVR 挂载通道：仅更新库表字段，不触发 IPC ONVIF
    if is_nvr_channel_device(camera):
        for k, v in (item for item in update_info.items() if item[1] is not None):
            if k in _NVR_PAYLOAD_KEYS or k in ('nvr_id', 'nvr_channel', 'cameraType', 'skip_onvif'):
                continue
            if k in ('rtsp_direct', 'channel_online', 'connection_status') and hasattr(camera, k):
                setattr(camera, k, v)
                continue
            if hasattr(camera, k):
                setattr(camera, k, v)
        if not camera.manufacturer or not camera.manufacturer.strip():
            camera.manufacturer = 'EasyAIoT'
        if not camera.model or not camera.model.strip():
            camera.model = 'NVR-Channel'
        try:
            db.session.commit()
            logger.info(f'设备 {id} 信息已更新（NVR 通道）')
        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'数据库更新失败: {str(e)}') from e
        return

    # 处理IP地址变更
    # 注意：IP地址变更时，如果ONVIF连接失败，不应该阻止其他字段的更新
    # 只有在IP地址确实变更时才尝试通过ONVIF更新设备信息
    if 'ip' in update_info:
        old_ip = camera.ip
        new_ip = update_info['ip']
        # 只有当IP地址确实发生变化时才尝试通过ONVIF更新
        if old_ip != new_ip:
            try:
                # 保存更新前的设备名称，用于检查是否通过ONVIF更新了名称
                name_before_ip_update = camera.name
                _update_camera_ip(camera, new_ip)
                # 如果IP更新成功，_update_camera_ip已经提交了数据库
                # 检查设备名称是否发生变化（可能是通过ONVIF更新的）
                if device_name_changed or (camera.name and camera.name != name_before_ip_update):
                    # 同步更新空间名称
                    try:
                        from app.services.snap_space_service import get_snap_space_by_device_id, update_snap_space
                        from app.services.record_space_service import get_record_space_by_device_id, update_record_space
                        
                        # 更新抓拍空间名称
                        snap_space = get_snap_space_by_device_id(id)
                        if snap_space and camera.name:
                            update_snap_space(snap_space.id, space_name=camera.name)
                            logger.info(f'设备 {id} 的抓拍空间名称已同步更新为: {camera.name}')
                        
                        # 更新录像空间名称
                        record_space = get_record_space_by_device_id(id)
                        if record_space and camera.name:
                            update_record_space(record_space.id, space_name=camera.name)
                            logger.info(f'设备 {id} 的录像空间名称已同步更新为: {camera.name}')
                    except Exception as e:
                        # 空间名称更新失败不应该阻止设备信息更新，只记录警告
                        logger.warning(f'同步更新设备 {id} 的空间名称失败: {str(e)}，但不影响设备信息更新')
                
                logger.info(f'设备 {id} IP地址已从 {old_ip} 更新为 {new_ip}')
                return
            except Exception as e:
                # IP地址更新失败时，记录警告但不阻止其他字段的更新
                # 只更新IP地址，不通过ONVIF获取其他信息
                logger.warning(f'设备 {id} IP地址更新失败（ONVIF连接失败）: {str(e)}，将仅更新IP地址')
                # 只更新IP地址，不通过ONVIF获取其他信息
                camera.ip = new_ip
                
                # 判断是否是自定义摄像头（通过视频源添加的）
                # 优先使用请求中的cameraType字段，如果没有则通过设备特征判断
                is_custom = is_custom_from_request or _is_custom_camera(camera)
                
                # 更新监控：编辑后强制设置为在线状态
                if new_ip:
                    _monitor.update(camera.id, new_ip, default_online=True)
                    logger.debug(f'设备 {id} IP地址变更后强制设置为在线状态（新IP: {new_ip}）')
                
                # 如果是RTMP设备或自定义摄像头，直接提交
                if camera.source and (camera.source.strip().lower().startswith('rtmp://') or is_custom):
                    # 如果设备名称也变化了，同步更新空间名称
                    if device_name_changed and camera.name:
                        try:
                            from app.services.snap_space_service import get_snap_space_by_device_id, update_snap_space
                            from app.services.record_space_service import get_record_space_by_device_id, update_record_space
                            
                            # 更新抓拍空间名称
                            snap_space = get_snap_space_by_device_id(id)
                            if snap_space:
                                update_snap_space(snap_space.id, space_name=camera.name)
                                logger.info(f'设备 {id} 的抓拍空间名称已同步更新为: {camera.name}')
                            
                            # 更新录像空间名称
                            record_space = get_record_space_by_device_id(id)
                            if record_space:
                                update_record_space(record_space.id, space_name=camera.name)
                                logger.info(f'设备 {id} 的录像空间名称已同步更新为: {camera.name}')
                        except Exception as e:
                            logger.warning(f'同步更新设备 {id} 的空间名称失败: {str(e)}，但不影响设备信息更新')
                    
                    db.session.commit()
                    device_type = 'RTMP设备' if camera.source.strip().lower().startswith('rtmp://') else '自定义摄像头'
                    logger.info(f'设备 {id} IP地址已更新为 {new_ip}（{device_type}，跳过ONVIF连接）')
                    return
    
    # 确保manufacturer和model不为空（更新后最终验证，如果为空则使用默认值）
    if not camera.manufacturer or not camera.manufacturer.strip():
        camera.manufacturer = 'EasyAIoT'
    if not camera.model or not camera.model.strip():
        camera.model = 'Camera-EasyAIoT'
    
    # 强制更新监控状态为在线（编辑后确保设备显示为在线）
    # 判断是否是自定义摄像头或RTMP设备
    is_custom = is_custom_from_request or _is_custom_camera(camera)
    is_rtmp = camera.source and camera.source.strip().lower().startswith('rtmp://')
    
    # 如果有IP地址，强制更新监控状态为在线
    if camera.ip:
        # 自定义摄像头、RTMP设备或编辑后的设备都强制设置为在线
        _monitor.update(camera.id, camera.ip, default_online=True)
        logger.debug(f'设备 {id} 编辑后强制设置为在线状态（IP: {camera.ip}）')
    elif is_rtmp or is_custom:
        # RTMP设备或自定义摄像头即使没有IP也默认在线（在_to_dict中处理）
        logger.debug(f'设备 {id} 是{"RTMP设备" if is_rtmp else "自定义摄像头"}，无需IP监控，默认在线')

    # 如果设备名称发生变化，同步更新关联的抓拍空间和录像空间的名称
    if device_name_changed and camera.name:
        try:
            from app.services.snap_space_service import get_snap_space_by_device_id, update_snap_space
            from app.services.record_space_service import get_record_space_by_device_id, update_record_space
            
            # 更新抓拍空间名称
            snap_space = get_snap_space_by_device_id(id)
            if snap_space:
                update_snap_space(snap_space.id, space_name=camera.name)
                logger.info(f'设备 {id} 的抓拍空间名称已同步更新为: {camera.name}')
            
            # 更新录像空间名称
            record_space = get_record_space_by_device_id(id)
            if record_space:
                update_record_space(record_space.id, space_name=camera.name)
                logger.info(f'设备 {id} 的录像空间名称已同步更新为: {camera.name}')
        except Exception as e:
            # 空间名称更新失败不应该阻止设备信息更新，只记录警告
            logger.warning(f'同步更新设备 {id} 的空间名称失败: {str(e)}，但不影响设备信息更新')

    try:
        db.session.commit()
        logger.info(f'设备 {id} 信息已更新')
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f'数据库更新失败: {str(e)}')


def delete_camera(id: str):
    """删除设备"""
    camera = _get_camera(id)
    if not camera:
        raise ValueError(f'设备 {id} 不存在，无法删除')

    try:
        # 先删除设备相关的检测区域，避免外键约束错误
        regions = DeviceDetectionRegion.query.filter_by(device_id=id).all()
        for region in regions:
            db.session.delete(region)
        logger.info(f'已删除设备 {id} 的 {len(regions)} 个检测区域')

        # RTC 设备：同步清理 go2rtc 流
        try:
            cleanup_rtc_stream_for_device(camera)
        except Exception as rtc_exc:
            logger.warning(f'清理 RTC 流失败（设备 {id}）: {rtc_exc}')

        _monitor.delete(camera.id)
        _onvif_cameras.pop(id, None)
        db.session.delete(camera)
        db.session.commit()
        logger.info(f'设备 {id} 已从系统中移除')
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f'删除设备失败: {str(e)}')


def batch_delete_cameras(device_ids: list) -> dict:
    """批量删除摄像头设备，返回 deleted / failed / errors。"""
    if not device_ids:
        return {'deleted': 0, 'failed': 0, 'errors': []}

    deleted = 0
    errors: list[dict] = []
    seen = set()
    for raw_id in device_ids:
        device_id = str(raw_id or '').strip()
        if not device_id or device_id in seen:
            continue
        seen.add(device_id)
        try:
            delete_camera(device_id)
            deleted += 1
        except ValueError as e:
            errors.append({'device_id': device_id, 'msg': str(e)})
        except Exception as e:
            logger.error(f'批量删除设备 {device_id} 失败: {e}', exc_info=True)
            errors.append({'device_id': device_id, 'msg': str(e)})

    return {
        'deleted': deleted,
        'failed': len(errors),
        'errors': errors,
    }

def get_snapshot_uri(ip: str, port: int, username: str, password: str) -> str:
    """
    获取ONVIF设备的快照URI
    :param ip: 设备IP地址
    :param port: ONVIF服务端口（默认80）
    :param username: 认证用户名
    :param password: 认证密码
    :return: 快照URI字符串（包含认证信息）
    """
    try:
        # 1. 创建ONVIFCamera实例
        cam = ONVIFCamera(
            ip, port, username, password,
            wsdl_dir=current_app.config.get('ONVIF_WSDL_DIR', '/etc/onvif/wsdl')
        )

        # 2. 创建媒体服务
        media_service = cam.create_media_service()

        # 3. 获取配置文件（默认使用第一个Profile）
        profiles = media_service.GetProfiles()
        if not profiles:
            raise ValueError("未找到有效的媒体配置文件")
        profile_token = profiles[0].token

        # 4. 获取快照URI
        snapshot_uri_response = media_service.GetSnapshotUri({'ProfileToken': profile_token})
        snapshot_uri = snapshot_uri_response.Uri

        # 5. 注入认证信息（关键步骤）
        if username and password:
            if "http://" in snapshot_uri:
                snapshot_uri = snapshot_uri.replace(
                    "http://",
                    f"http://{username}:{password}@",
                    1
                )
            elif "https://" in snapshot_uri:
                snapshot_uri = snapshot_uri.replace(
                    "https://",
                    f"https://{username}:{password}@",
                    1
                )

        logger.info(f"设备 {ip} 快照URI获取成功: {snapshot_uri[:50]}...")
        return snapshot_uri

    except Exception as e:
        logger.error(f"获取设备 {ip} 快照URI失败: {str(e)}")
        raise RuntimeError(f"ONVIF快照URI获取失败: {str(e)}")


def list_devices_for_map(*, directory_id=None, has_location_only=True) -> list:
    """返回用于地图展示的摄像头位置列表（轻量字段）。"""
    query = Device.query
    if directory_id is not None:
        # 国标虚拟设备恒挂默认分组，但通道可出现在任意目录视图下；放行以免按目录筛选时漏掉其坐标
        query = query.filter(
            or_(
                Device.directory_id == directory_id,
                Device.source.ilike(f'{GB28181_SOURCE_PREFIX}%'),
            )
        )
    if has_location_only:
        query = query.filter(
            Device.longitude.isnot(None),
            Device.latitude.isnot(None),
        )
    devices = query.order_by(Device.updated_at.desc()).all()
    result = []
    for device in devices:
        loc = _location_fields_for_device(device)
        result.append({
            'id': device.id,
            'name': device.name,
            'source': device.source,
            'directory_id': device.directory_id,
            'online': _to_dict(device).get('online'),
            **_gb_attribute_fields_for_device(device),
            **loc,
            **nvr_fields_for_device(device),
        })
    return result


def update_device_location(device_id: str, update_info: dict, *, ensure_name: str | None = None) -> dict:
    """更新单个摄像头的位置信息（地图选点等场景）。"""
    camera = _get_camera_for_location(device_id, name=ensure_name)
    _apply_location_updates(camera, update_info)
    db.session.commit()
    return _location_fields_for_device(camera)


def batch_update_device_locations(items: list) -> dict:
    """批量更新摄像头 WGS84 坐标（CSV/Excel 导入场景）。"""
    if not items:
        return {'updated': 0, 'errors': []}

    updated = 0
    errors = []
    for item in items:
        if not isinstance(item, dict):
            errors.append({'index': None, 'msg': '条目格式无效'})
            continue
        device_id = str(item.get('device_id') or item.get('id') or '').strip()
        if not device_id:
            errors.append({'device_id': None, 'msg': '缺少 device_id'})
            continue
        try:
            camera = _get_camera_for_location(
                device_id,
                name=str(item.get('name') or '').strip() or None,
            )
        except ValueError:
            errors.append({'device_id': device_id, 'msg': '设备不存在'})
            continue
        try:
            _apply_location_updates(camera, {
                'longitude': item.get('longitude'),
                'latitude': item.get('latitude'),
                'altitude': item.get('altitude'),
                'address': item.get('address'),
                'heading': item.get('heading'),
                'location_source': item.get('location_source') or 'import',
            })
            updated += 1
        except ValueError as exc:
            errors.append({'device_id': device_id, 'msg': str(exc)})

    if updated:
        db.session.commit()
    else:
        db.session.rollback()
    return {'updated': updated, 'errors': errors, 'total': len(items)}


def _parse_optional_datetime(value):
    if value is None or value == '':
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f'无法解析时间: {text}')


def list_track_sessions(*, device_id=None, begin=None, end=None, limit=50) -> list:
    """查询轨迹段列表，供地图轨迹回放选择。"""
    query = DeviceTrackSession.query
    if device_id:
        query = query.filter(DeviceTrackSession.device_id == str(device_id).strip())
    begin_dt = _parse_optional_datetime(begin) if begin else None
    end_dt = _parse_optional_datetime(end) if end else None
    if begin_dt:
        query = query.filter(DeviceTrackSession.started_at >= begin_dt)
    if end_dt:
        query = query.filter(DeviceTrackSession.started_at <= end_dt)
    sessions = query.order_by(DeviceTrackSession.started_at.desc()).limit(max(1, min(int(limit or 50), 200))).all()
    return [session.to_dict() for session in sessions]


def list_track_points(*, session_id=None, device_id=None, begin=None, end=None, limit=5000) -> list:
    """查询轨迹点；优先 session_id，否则按 device_id + 时间范围。"""
    query = DeviceTrackPoint.query
    if session_id not in (None, ''):
        query = query.filter(DeviceTrackPoint.session_id == int(session_id))
    elif device_id:
        query = query.filter(DeviceTrackPoint.device_id == str(device_id).strip())
    else:
        raise ValueError('需提供 session_id 或 device_id')
    begin_dt = _parse_optional_datetime(begin) if begin else None
    end_dt = _parse_optional_datetime(end) if end else None
    if begin_dt:
        query = query.filter(DeviceTrackPoint.recorded_at >= begin_dt)
    if end_dt:
        query = query.filter(DeviceTrackPoint.recorded_at <= end_dt)
    points = query.order_by(DeviceTrackPoint.recorded_at.asc()).limit(max(1, min(int(limit or 5000), 10000))).all()
    return [point.to_dict() for point in points]
