"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import concurrent.futures
import logging
import os
import re
import time
from functools import partial
from sched import scheduler

import tzlocal
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
from onvif import ONVIFCamera
from wsdiscovery import WSDiscovery, Scope

from app.services.onvif_service import OnvifCamera
from app.utils.ip_utils import IpReachabilityMonitor
from models import Device, db

# 全局变量定义
_onvif_cameras = {}
# 确保环境变量转换为整数
_monitor = IpReachabilityMonitor(int(os.getenv('CAMERA_ONLINE_INTERVAL', 20)))
logger = logging.getLogger(__name__)
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
scheduler = BackgroundScheduler(timezone=tzlocal.get_localzone_name())

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
    # 如果摄像头地址是 rtmp，则不需要 ONVIF 连接
    if camera.source and camera.source.strip().lower().startswith('rtmp://'):
        raise ValueError(f'设备 {camera.id} 的源地址是 RTMP，不需要 ONVIF 连接')
    
    # 验证IP地址是否有效
    if not camera.ip or not camera.ip.strip():
        raise ValueError(f'设备 {camera.id} 的IP地址为空，无法创建ONVIF连接')
    
    # 验证端口是否有效
    if not camera.port or camera.port <= 0:
        raise ValueError(f'设备 {camera.id} 的端口无效，无法创建ONVIF连接')
    
    return _create_onvif_camera(
        camera.id, camera.ip, camera.port,
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


def _get_camera(id: str) -> Device:
    """获取单个设备ORM对象"""
    return Device.query.get(id)


def _get_cameras() -> list[Device]:
    """获取所有设备"""
    return Device.query.all()


def _to_dict(camera: Device) -> dict:
    """设备对象转字典"""
    # 如果是RTMP设备，默认在线状态为True，不需要通过IP监控判断
    if camera.source and camera.source.strip().lower().startswith('rtmp://'):
        online_status = True
    else:
        online_status = _monitor.is_online(camera.id)
    
    return {
        'id': camera.id,
        'name': camera.name,
        'source': camera.source,
        'rtmp_stream': camera.rtmp_stream,
        'http_stream': camera.http_stream,
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
        'nvr_id': camera.nvr_id if camera.nvr_id else None,
        'nvr_channel': camera.nvr_channel,
        'online': online_status
    }


def _add_online_monitor():
    """初始化设备在线监控"""
    for camera in _get_cameras():
        _monitor.update(camera.id, camera.ip)
    logger.debug('设备在线状态监控服务已初始化')


def _discovery_cameras() -> list:
    """发现网络中的ONVIF设备"""
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


def _update_camera_ip(camera: Device, ip: str):
    """更新设备IP并刷新信息"""
    camera.ip = ip
    
    # 如果摄像头地址是 rtmp，不需要 ONVIF 连接，只更新 IP 和监控
    if camera.source and camera.source.strip().lower().startswith('rtmp://'):
        _monitor.update(camera.id, camera.ip)
        db.session.commit()
        logger.info(f'设备 {camera.id} IP地址已更新为 {ip}（RTMP设备，跳过ONVIF连接）')
        return
    
    try:
        onvif_camera = _create_onvif_camera_from_orm(camera)
        camera_info = onvif_camera.get_info()

        for key, value in camera_info.items():
            if hasattr(camera, key):
                setattr(camera, key, value)

        if camera.stream is not None:
            try:
                camera.source = _get_stream(camera.source, camera.stream)
            except Exception:
                camera.stream = None
                logger.warning(f'设备 {camera.id} 码流调整失败，已重置为默认码流')

        _monitor.update(camera.id, camera.ip)
        db.session.commit()
        logger.info(f'设备 {camera.id} IP地址已更新为 {ip}')
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新设备 {camera.id} IP失败: {str(e)}')
        raise


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
    """启动设备发现服务"""
    ws_daemonlogger = logging.getLogger('daemon')
    ws_daemonlogger.setLevel(logging.ERROR)

    # 确保环境变量转换为整数
    discover_interval = int(os.getenv('CAMERA_DISCOVER_INTERVAL', 120))
    
    # 创建包装函数，将app对象传入refresh_camera
    if app is not None:
        def refresh_camera_with_app():
            refresh_camera(app)
        scheduler.add_job(refresh_camera_with_app, 'interval', seconds=discover_interval)
    else:
        # 如果没有app对象，尝试在运行时获取（可能失败）
        scheduler.add_job(refresh_camera, 'interval', seconds=discover_interval)
    
    # 启动调度器（如果尚未启动）
    if not scheduler.running:
        scheduler.start()
        logger.debug('调度器已启动')
    
    logger.debug('设备发现服务已启动，间隔: %d秒', discover_interval)
    _init_all_cameras()
    _add_online_monitor()


def _init_all_cameras():
    """初始化所有摄像头连接"""
    for camera in _get_cameras():
        executor.submit(
            partial(_safe_create_camera, camera)
        )
    logger.debug('所有设备连接已通过线程池初始化')

    # 在初始化所有摄像头连接后，启动在线监控
    _add_online_monitor()


def _safe_create_camera(camera: Device):
    """安全创建相机连接（带异常处理）"""
    # 如果摄像头地址是 rtmp，跳过ONVIF连接初始化
    if camera.source and camera.source.strip().lower().startswith('rtmp://'):
        logger.debug(f'设备 {camera.id} 的源地址是 RTMP，跳过ONVIF连接初始化')
        return
    
    # 如果IP地址为空，跳过ONVIF连接初始化（可能是直接注册的RTSP设备）
    if not camera.ip or not camera.ip.strip():
        logger.debug(f'设备 {camera.id} 的IP地址为空，跳过ONVIF连接初始化（可能是RTSP直连设备）')
        return
    
    # 如果端口无效，跳过ONVIF连接初始化
    if not camera.port or camera.port <= 0:
        logger.debug(f'设备 {camera.id} 的端口无效，跳过ONVIF连接初始化')
        return
    
    try:
        _create_onvif_camera_from_orm(camera)
    except ValueError as e:
        # 参数验证错误，记录为调试信息
        logger.debug(f'初始化设备 {camera.id} 连接失败: {str(e)}')
    except Exception as e:
        logger.error(f'初始化设备 {camera.id} 连接失败: {str(e)}')


def _get_stream(rtsp_url: str, stream: int) -> str:
    """根据设备类型生成指定码流URL"""
    if stream is None:
        return rtsp_url

    # 海康威视设备
    if re.match(r'rtsp://[^/]*/Streaming/Channels/10\d.*', rtsp_url):
        if stream == 0:
            stream = 1
        elif not (1 <= stream <= 3):
            raise ValueError('海康设备仅支持码流类型: 0[默认], 1[主码流], 2[子码流], 3[第三码流]')
        return re.sub(r'Channels/10\d', f'Channels/10{stream}', rtsp_url)

    # 大华设备
    elif re.match(r'rtsp://[^/]*/cam/realmonitor\?channel=\d+&subtype=\d+.*', rtsp_url):
        if stream == 0:
            stream = 1
        elif not (1 <= stream <= 2):
            raise ValueError('大华设备仅支持码流类型: 0[默认], 1[主码流], 2[辅码流]')
        return re.sub(r'subtype=\d', f'subtype={stream - 1}', rtsp_url)

    raise ValueError('仅支持海康和大华设备的码流调整功能')


def register_camera_by_onvif(ip: str, port: int, password: str) -> str:
    """通过ONVIF搜索并自动注册摄像头
    
    Args:
        ip: 摄像头IP地址
        port: 摄像头端口
        password: 摄像头密码
        
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
    
    # 尝试常见的用户名列表
    common_usernames = ['admin', 'Administrator', 'root', '']
    
    onvif_cam = None
    used_username = None
    temp_id = 'temp_' + str(time.time_ns())  # 临时ID用于连接测试
    
    # 尝试使用不同的用户名连接
    for username in common_usernames:
        try:
            onvif_cam = _create_onvif_camera(
                temp_id,
                ip,
                port,
                username,
                password
            )
            used_username = username
            logger.info(f'使用用户名 "{username}" 成功连接到设备 {ip}:{port}')
            break
        except Exception as e:
            logger.debug(f'使用用户名 "{username}" 连接设备 {ip}:{port} 失败: {str(e)}')
            continue
    
    if onvif_cam is None:
        raise RuntimeError(f'无法连接到设备 {ip}:{port}，请检查IP、端口和密码是否正确，或尝试其他用户名')
    
    # 检查设备是否已存在（通过MAC地址）
    camera_info = onvif_cam.get_info()
    mac = camera_info.get('mac')
    
    if mac:
        existing_camera = Device.query.filter_by(mac=mac).first()
        if existing_camera:
            raise ValueError(f'设备已存在，设备ID: {existing_camera.id}')
    
    # 生成设备ID
    device_id = str(time.time_ns())
    if _get_camera(device_id):
        device_id = str(time.time_ns())  # 如果冲突，重新生成
    
    # 创建设备记录
    camera = Device(
        id=device_id,
        name=f'Camera-{device_id[:6]}',
        source=camera_info.get('source'),
        rtmp_stream=f"rtmp://localhost:1935/live/{device_id}",
        http_stream=f"http://localhost:8989/live/{device_id}.flv",
        stream=None,
        ip=camera_info.get('ip'),
        port=camera_info.get('port', port),
        username=used_username,
        password=password,
        mac=camera_info.get('mac'),
        manufacturer=camera_info.get('manufacturer'),
        model=camera_info.get('model'),
        firmware_version=camera_info.get('firmware_version'),
        serial_number=camera_info.get('serial_number'),
        hardware_id=camera_info.get('hardware_id'),
        support_move=camera_info.get('support_move', False),
        support_zoom=camera_info.get('support_zoom', False),
        nvr_id=None,
        nvr_channel=0
    )
    
    db.session.add(camera)
    try:
        db.session.commit()
        _monitor.update(camera.id, camera.ip)
        logger.info(f'设备 {device_id} 通过ONVIF注册成功，IP: {camera.ip}, 用户名: {used_username}')
        return device_id
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f'数据库提交失败: {str(e)}')


def register_camera(register_info: dict) -> str:
    """注册设备到数据库
    
    如果传入了source字段，直接使用该字段作为RTSP地址，不再通过ONVIF搜索。
    如果没有传入source字段，则通过ONVIF搜索设备信息。
    """
    id = register_info.get('id') or str(time.time_ns())
    if _get_camera(id):
        raise ValueError('设备ID已存在，请使用唯一标识符')

    # 如果传入了source字段，直接使用，不再通过ONVIF搜索
    if register_info.get('source'):
        # 直接注册模式：使用用户提供的source字段
        source = register_info.get('source')
        name = register_info.get('name', f'Camera-{id[:6]}')
        
        # 从source中提取IP和端口（如果可能）
        ip = register_info.get('ip', '')
        port = register_info.get('port', 554)
        username = register_info.get('username', '')
        password = register_info.get('password', '')
        
        # 尝试从RTSP地址中提取IP和端口
        rtsp_pattern = r'rtsp://(?:[^:]+:[^@]+@)?([^:/]+)(?::(\d+))?'
        match = re.match(rtsp_pattern, source)
        if match:
            if not ip:
                ip = match.group(1)
            if not port and match.group(2):
                port = int(match.group(2))
        
        # 创建设备记录（直接使用用户提供的source和所有字段）
        camera = Device(
            id=id,
            name=name,
            source=source,
            rtmp_stream=f"rtmp://localhost:1935/live/{id}",
            http_stream=f"http://localhost:8989/live/{id}.flv",
            stream=register_info.get('stream', 0),
            ip=ip or '',
            port=port,
            username=username,
            password=password,
            mac=register_info.get('mac', ''),
            manufacturer=register_info.get('manufacturer', ''),
            model=register_info.get('model', ''),
            firmware_version=register_info.get('firmware_version', ''),
            serial_number=register_info.get('serial_number', ''),
            hardware_id=register_info.get('hardware_id', ''),
            support_move=register_info.get('support_move', False),
            support_zoom=register_info.get('support_zoom', False),
            nvr_id=register_info.get('nvr_id'),
            nvr_channel=register_info.get('nvr_channel', 0),
            enable_forward=register_info.get('enable_forward')
        )
        
        db.session.add(camera)
        try:
            db.session.commit()
            if ip:
                _monitor.update(camera.id, ip)
            logger.info(f'设备 {id} 注册成功（直接模式），RTSP地址: {source}')
            return id
        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f'数据库提交失败: {str(e)}')
    
    # 如果没有传入source字段，则通过ONVIF搜索（保持原有逻辑）
    try:
        onvif_cam = _create_onvif_camera(
            id,
            register_info['ip'],
            register_info.get('port', 80),
            register_info['username'],
            register_info['password']
        )
    except KeyError as e:
        raise ValueError(f'设备注册信息不完整，缺少必要字段: {str(e)}')
    except Exception as e:
        raise RuntimeError(f'设备注册失败: {str(e)}')

    # 创建设备记录
    camera_info = onvif_cam.get_info()
    camera = Device(
        id=id,  # 显式设置ID，确保使用传入的ID或生成的唯一ID
        name=register_info.get('name', f'Camera-{id[:6]}'),
        source=camera_info.get('source'),
        rtmp_stream=f"rtmp://localhost:1935/live/{id}",
        http_stream=f"http://localhost:8989/live/{id}.flv",
        stream=register_info.get('stream'),
        ip=camera_info.get('ip'),
        port=camera_info.get('port', 80),
        username=camera_info.get('username'),
        password=register_info['password'],
        mac=camera_info.get('mac'),
        manufacturer=camera_info.get('manufacturer'),
        model=camera_info.get('model'),
        firmware_version=camera_info.get('firmware_version'),
        serial_number=camera_info.get('serial_number'),
        hardware_id=camera_info.get('hardware_id'),
        support_move=camera_info.get('support_move', False),
        support_zoom=camera_info.get('support_zoom', False),
        nvr_id=None,
        nvr_channel=0
    )

    # 处理码流设置
    if register_info.get('stream') is not None:
        try:
            camera.source = _get_stream(camera.source, register_info['stream'])
        except Exception as e:
            logger.warning(f'设备 {id} 码流设置失败: {str(e)}，使用默认码流')

    db.session.add(camera)
    try:
        db.session.commit()
        _monitor.update(camera.id, camera.ip)
        logger.info(f'设备 {id} 注册成功，IP: {camera.ip}')
        return id
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f'数据库提交失败: {str(e)}')


def get_camera_info(id: str) -> dict:
    """获取设备基本信息"""
    camera = _get_camera(id)
    if not camera:
        raise ValueError(f'设备 {id} 不存在，请先注册')
    return _to_dict(camera)


def get_camera_list() -> list:
    """获取所有设备信息列表"""
    return [_to_dict(camera) for camera in _get_cameras()]


def get_device_list() -> dict:
    """从数据库获取所有设备"""
    devices = Device.query.all()
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

    # 过滤空值并更新字段
    for k, v in (item for item in update_info.items() if item[1] is not None):
        if hasattr(camera, k):
            setattr(camera, k, v)

    # 处理码流变更
    if 'stream' in update_info:
        try:
            camera.source = _get_stream(camera.source, update_info['stream'])
        except Exception as e:
            raise RuntimeError(f'码流调整失败: {str(e)}')

    # 处理IP地址变更
    if 'ip' in update_info:
        try:
            _update_camera_ip(camera, update_info['ip'])
        except Exception as e:
            raise RuntimeError(f'IP地址更新失败: {str(e)}')

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
        _monitor.delete(camera.id)
        _onvif_cameras.pop(id, None)
        db.session.delete(camera)
        db.session.commit()
        logger.info(f'设备 {id} 已从系统中移除')
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f'删除设备失败: {str(e)}')

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