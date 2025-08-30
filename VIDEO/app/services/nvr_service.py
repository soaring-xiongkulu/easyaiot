import concurrent.futures
import logging
import os
import time
from contextlib import contextmanager
from functools import lru_cache

from app.utils.ip_utils import IpReachabilityMonitor
from models import Nvr, Device, db

logger = logging.getLogger(__name__)
_monitor = IpReachabilityMonitor(os.getenv('CAMERA_ONLINE_INTERVAL', 20))
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

# ------------------- 核心工具函数 -------------------
@contextmanager
def db_session():
    """数据库事务上下文管理器，确保原子性操作"""
    try:
        yield
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"数据库操作失败: {str(e)}", exc_info=True)
        raise


# ------------------- NVR管理功能 -------------------
def register_nvr(register_info: dict) -> int:
    """注册NVR设备"""
    required_fields = {'ip', 'username', 'password'}
    if missing := required_fields - set(register_info.keys()):
        raise ValueError(f'缺少必要字段: {", ".join(missing)}')

    # 创建NVR对象
    nvr = Nvr(
        ip=register_info['ip'],
        username=register_info['username'],
        password=register_info['password'],
        name=register_info.get('name', f"NVR-{register_info['ip']}"),
        model=register_info.get('model')
    )

    try:
        with db_session():
            db.session.add(nvr)
            _monitor.update(nvr.id, nvr.ip)  # 添加到在线监控
        logger.info(f"NVR[{nvr.id}]注册成功")
        return nvr.id
    except Exception as e:
        logger.error(f"NVR注册失败: {str(e)}")
        raise


def get_nvr_info(id: int) -> dict:
    """获取NVR详细信息"""
    if not (nvr := Nvr.query.get(id)):
        raise LookupError(f'NVR[{id}]不存在')

    # 构造返回信息（包含子摄像头）
    return {
        "id": nvr.id,
        "ip": nvr.ip,
        "name": nvr.name,
        "model": nvr.model,
        "online": _monitor.is_online(nvr.id),
        "cameras": [
            {"id": cam.id, "channel": cam.nvr_channel}
            for cam in Device.query.filter_by(nvr_id=nvr.id).all()
        ]
    }


def delete_nvr(id: int):
    """删除NVR及其关联资源"""
    if not (nvr := Nvr.query.get(id)):
        raise LookupError(f'NVR[{id}]不存在')

    # 删除关联摄像头
    cameras = Device.query.filter_by(nvr_id=id).all()
    try:
        with db_session():
            for camera in cameras:
                db.session.delete(camera)
            db.session.delete(nvr)
            _monitor.delete(nvr.id)  # 从监控器移除
        logger.info(f"NVR[{id}]删除成功")
    except Exception as e:
        logger.error(f"删除NVR[{id}]失败: {str(e)}")
        raise


# ------------------- 码流生成函数 -------------------
@lru_cache(maxsize=128)
def _get_stream(nvr: Nvr, channel: int, stream: int) -> str:
    """生成RTSP流地址（带缓存）"""
    if not stream or stream == 1:
        stream = 1
    elif stream > 2 or stream < 0:
        raise ValueError('码流类型只支持0/1/2')

    # 格式化通道和码流（海康威视格式）
    return f"rtsp://{nvr.username}:{nvr.password}@{nvr.ip}:554/Streaming/Channels/{channel}{stream:02d}"


# ------------------- 子摄像头管理 -------------------
def add_nvr_camera(nvr_id: int, args: dict):
    """添加NVR子摄像头"""
    if not (nvr := Nvr.query.get(nvr_id)):
        raise LookupError(f'NVR[{nvr_id}]不存在')

    # 参数校验
    if not (nvr_channel := args.get('nvr_channel')):
        raise ValueError('缺少通道编号参数')
    if Device.query.filter_by(nvr_id=nvr_id, nvr_channel=nvr_channel).first():
        raise RuntimeError(f"通道{nvr_channel}已被占用")

    # 创建摄像头
    camera = Device(
        id=args.get('id', f"cam-{nvr_id}-{nvr_channel}-{int(time.time())}"),
        nvr_id=nvr_id,
        nvr_channel=nvr_channel,
        name=args.get('name', f"Camera-{nvr_channel}"),
        source=_get_stream(nvr, nvr_channel, args.get('stream', 1)),
        stream=args.get('stream', 1),
        manufacturer=args.get('manufacturer'),
        model=args.get('model')
    )

    try:
        with db_session():
            db.session.add(camera)
        logger.info(f"NVR[{nvr_id}]通道[{nvr_channel}]添加成功")
    except Exception as e:
        logger.error(f"添加摄像头失败: {str(e)}")
        raise
