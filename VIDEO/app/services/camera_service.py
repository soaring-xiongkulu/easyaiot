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
        'auto_snap_enabled': camera.auto_snap_enabled if hasattr(camera, 'auto_snap_enabled') else False,
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
        'directory_id': camera.directory_id if camera.directory_id else None,
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
                # 对于manufacturer和model字段，如果ONVIF返回的值为空，保留原有值或使用默认值
                if key in ['manufacturer', 'model']:
                    if not value or not str(value).strip():
                        # 如果原有值也为空，使用默认值
                        current_value = getattr(camera, key, '')
                        if not current_value or not str(current_value).strip():
                            if key == 'manufacturer':
                                value = 'EasyAIoT'
                            else:
                                value = 'Camera-EasyAIoT'
                        else:
                            # 保留原有值
                            continue
                setattr(camera, key, value)

        # 确保manufacturer和model不为空
        if not camera.manufacturer or not camera.manufacturer.strip():
            camera.manufacturer = 'EasyAIoT'
        if not camera.model or not camera.model.strip():
            camera.model = 'Camera-EasyAIoT'

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
    try:
        port = int(camera.port) if camera.port else 0
    except (ValueError, TypeError):
        port = 0
    
    if not port or port <= 0:
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


def _generate_stream_urls(source: str, device_id: str) -> tuple[str, str]:
    """根据源地址生成RTMP和HTTP播放地址
    
    Args:
        source: 源地址（RTSP、RTMP或HTTP）
        device_id: 设备ID
        
    Returns:
        tuple: (rtmp_stream, http_stream)
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
            
            return rtmp_stream, http_stream
        else:
            # 如果解析失败，使用默认格式
            server = '127.0.0.1'
            rtmp_stream = f"rtmp://{server}:1935/live/{device_id}"
            http_stream = f"http://{server}:8080/live/{device_id}.flv"
            return rtmp_stream, http_stream
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
            
            return rtmp_stream, http_stream
        else:
            # 如果解析失败，使用默认格式
            server = '127.0.0.1'
            rtmp_stream = f"rtmp://{server}:1935/live/{device_id}"
            http_stream = f"http://{server}:8080/live/{device_id}.flv"
            return rtmp_stream, http_stream
    else:
        # RTSP流，使用设备ID生成默认地址
        server = '127.0.0.1'
        rtmp_stream = f"rtmp://{server}:1935/live/{device_id}"
        http_stream = f"http://{server}:8080/live/{device_id}.flv"
        return rtmp_stream, http_stream


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
    # 获取制造商和型号，确保不为空
    manufacturer = camera_info.get('manufacturer', '').strip() if camera_info.get('manufacturer') else ''
    model = camera_info.get('model', '').strip() if camera_info.get('model') else ''
    
    # 如果ONVIF获取的信息中manufacturer或model为空，使用专业的默认值
    if not manufacturer:
        manufacturer = 'EasyAIoT'
    if not model:
        model = 'Camera-EasyAIoT'
    
    # 生成RTMP和HTTP播放地址
    source = camera_info.get('source', '')
    rtmp_stream, http_stream = _generate_stream_urls(source, device_id) if source else (f"rtmp://127.0.0.1:1935/live/{device_id}", f"http://127.0.0.1:8080/live/{device_id}.flv")
    
    camera = Device(
        id=device_id,
        name=f'Camera-{device_id[:6]}',
        source=camera_info.get('source'),
        rtmp_stream=rtmp_stream,
        http_stream=http_stream,
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
        nvr_channel=0
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
        camera_type = register_info.get('cameraType', '')
        
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
            # RTSP地址格式：rtsp://username:password@ip:port/path 或 rtsp://ip:port/path
            rtsp_pattern = r'rtsp://(?:([^:]+):([^@]+)@)?([^:/]+)(?::(\d+))?(?:/.*)?'
            match = re.match(rtsp_pattern, source)
            if match:
                extracted_username = match.group(1)
                extracted_password = match.group(2)
                extracted_ip = match.group(3)
                extracted_port = match.group(4)
                if not ip:
                    ip = extracted_ip
                if not port:
                    if extracted_port:
                        port = int(extracted_port)
                    else:
                        port = 554  # RTSP默认端口
                # 如果地址中包含用户名密码，且用户未提供，则使用地址中的
                if not username and extracted_username:
                    username = extracted_username
                if not password and extracted_password:
                    password = extracted_password
        
        # 如果不是自定义设备且不是RTMP流，且提供了IP、端口、用户名、密码，且某些字段缺失，尝试通过ONVIF获取设备信息
        camera_info = {}
        if not is_custom and not is_rtmp and ip and port and username and password:
            # 检查是否有缺失的字段需要填充
            missing_fields = [
                'mac', 'manufacturer', 'model', 'firmware_version', 
                'serial_number', 'hardware_id', 'support_move', 'support_zoom'
            ]
            has_missing_fields = any(not register_info.get(field) for field in missing_fields)
            
            if has_missing_fields:
                try:
                    # 尝试通过ONVIF获取设备信息
                    onvif_cam = _create_onvif_camera(
                        id,
                        ip,
                        port,
                        username,
                        password
                    )
                    camera_info = onvif_cam.get_info()
                    logger.info(f'设备 {id} 通过ONVIF获取到设备信息，用于填充缺失字段')
                except Exception as e:
                    # ONVIF连接失败不影响注册，只记录警告
                    logger.warning(f'设备 {id} ONVIF连接失败，无法获取设备信息: {str(e)}')
                    camera_info = {}
        elif is_custom or is_rtmp:
            # 自定义设备或RTMP流，不通过ONVIF获取，只记录日志
            logger.info(f'设备 {id} 是{"RTMP流" if is_rtmp else "自定义设备"}，跳过ONVIF信息获取')
        
        # 获取制造商和型号，确保不为空
        manufacturer = register_info.get('manufacturer') or camera_info.get('manufacturer', '')
        model = register_info.get('model') or camera_info.get('model', '')
        
        # 如果manufacturer或model为空，使用默认值
        if not manufacturer or not manufacturer.strip():
            manufacturer = 'EasyAIoT'
        if not model or not model.strip():
            model = 'Camera-EasyAIoT'
        
        # 生成RTMP和HTTP播放地址
        rtmp_stream, http_stream = _generate_stream_urls(source, id)
        
        # 创建设备记录，优先使用用户提供的字段，缺失的字段从ONVIF获取的信息中填充
        camera = Device(
            id=id,
            name=name,
            source=source,
            rtmp_stream=rtmp_stream,
            http_stream=http_stream,
            stream=register_info.get('stream', 0),
            ip=ip or '',
            port=port,
            username=username,
            password=password,
            mac=register_info.get('mac') or camera_info.get('mac', ''),
            manufacturer=manufacturer.strip(),
            model=model.strip(),
            firmware_version=register_info.get('firmware_version') or camera_info.get('firmware_version', ''),
            serial_number=register_info.get('serial_number') or camera_info.get('serial_number', ''),
            hardware_id=register_info.get('hardware_id') or camera_info.get('hardware_id', ''),
            support_move=register_info.get('support_move') if register_info.get('support_move') is not None else camera_info.get('support_move', False),
            support_zoom=register_info.get('support_zoom') if register_info.get('support_zoom') is not None else camera_info.get('support_zoom', False),
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
    
    # 获取制造商和型号，确保不为空
    manufacturer = camera_info.get('manufacturer', '').strip() if camera_info.get('manufacturer') else ''
    model = camera_info.get('model', '').strip() if camera_info.get('model') else ''
    
    # 如果ONVIF获取的信息中manufacturer或model为空，使用专业的默认值
    if not manufacturer:
        manufacturer = 'EasyAIoT'
    if not model:
        model = 'Camera-EasyAIoT'
    
    # 生成RTMP和HTTP播放地址
    source = camera_info.get('source', '')
    rtmp_stream, http_stream = _generate_stream_urls(source, id) if source else (f"rtmp://127.0.0.1:1935/live/{id}", f"http://127.0.0.1:8080/live/{id}.flv")
    
    camera = Device(
        id=id,  # 显式设置ID，确保使用传入的ID或生成的唯一ID
        name=register_info.get('name', f'Camera-{id[:6]}'),
        source=camera_info.get('source'),
        rtmp_stream=rtmp_stream,
        http_stream=http_stream,
        stream=register_info.get('stream'),
        ip=camera_info.get('ip'),
        port=camera_info.get('port', 80),
        username=camera_info.get('username'),
        password=register_info['password'],
        mac=camera_info.get('mac'),
        manufacturer=manufacturer,
        model=model,
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
        
        # 自动为设备创建抓拍空间
        try:
            from app.services.snap_space_service import create_snap_space_for_device
            create_snap_space_for_device(id, camera.name)
            logger.info(f'设备 {id} 的抓拍空间已自动创建')
        except Exception as e:
            logger.warning(f'为设备 {id} 创建抓拍空间失败: {str(e)}，但不影响设备注册')
        
        # 自动为设备创建监控录像空间
        try:
            from app.services.record_space_service import create_record_space_for_device
            create_record_space_for_device(id, camera.name)
            logger.info(f'设备 {id} 的监控录像空间已自动创建')
        except Exception as e:
            logger.warning(f'为设备 {id} 创建监控录像空间失败: {str(e)}，但不影响设备注册')
        
        return id
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f'数据库提交失败: {str(e)}')


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


def get_camera_info(id: str) -> dict:
    """获取设备基本信息"""
    camera = _get_camera(id)
    if not camera:
        raise ValueError(f'设备 {id} 不存在，请先注册')
    
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

    # 保存旧的设备名称，用于后续同步更新空间名称
    old_device_name = camera.name
    device_name_changed = False

    # 过滤空值并更新字段
    for k, v in (item for item in update_info.items() if item[1] is not None):
        if hasattr(camera, k):
            # 对于布尔值字段，处理空字符串和字符串类型的布尔值
            if k in ['enable_forward', 'support_move', 'support_zoom', 'auto_snap_enabled']:
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
                # 更新监控
                _monitor.update(camera.id, new_ip)
                # 如果是RTMP设备，直接提交
                if camera.source and camera.source.strip().lower().startswith('rtmp://'):
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
                    logger.info(f'设备 {id} IP地址已更新为 {new_ip}（RTMP设备，跳过ONVIF连接）')
                    return
    
    # 确保manufacturer和model不为空（更新后最终验证，如果为空则使用默认值）
    if not camera.manufacturer or not camera.manufacturer.strip():
        camera.manufacturer = 'EasyAIoT'
    if not camera.model or not camera.model.strip():
        camera.model = 'Camera-EasyAIoT'

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

    # 检查设备关联的抓拍空间是否有图片
    try:
        from app.services.snap_space_service import check_device_space_has_images
        has_images, image_count = check_device_space_has_images(id)
        if has_images:
            raise ValueError(f'设备关联的抓拍空间还有 {image_count} 张抓拍图片，无法删除设备。请先删除所有图片后再删除设备。')
    except ValueError:
        raise
    except Exception as e:
        logger.warning(f'检查设备抓拍空间图片失败: {str(e)}，继续删除设备')
    
    # 检查设备关联的监控录像空间是否有录像
    try:
        from app.services.record_space_service import check_device_space_has_videos
        has_videos, video_count = check_device_space_has_videos(id)
        if has_videos:
            raise ValueError(f'设备关联的监控录像空间还有 {video_count} 个监控录像，无法删除设备。请先删除所有录像后再删除设备。')
    except ValueError:
        raise
    except Exception as e:
        logger.warning(f'检查设备监控录像空间录像失败: {str(e)}，继续删除设备')

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