"""
推流转发任务管理服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_

from models import db, StreamForwardTask, Device
# 注意：已移除冲突检查，推流转发任务和算法任务可以共存
# 推流转发任务使用 rtmp_stream/http_stream，算法任务使用 ai_rtmp_stream/ai_http_stream
import json

logger = logging.getLogger(__name__)

_NVR_STREAM_FORWARD_MARKER_PREFIX = 'nvr_stream_forward:nvr_id:'


def _is_nvr_stream_forward_task(task: StreamForwardTask) -> bool:
    description = (task.description or '').strip()
    return _NVR_STREAM_FORWARD_MARKER_PREFIX in description


def _default_schedule_policy(device_count: int, *, is_nvr: bool = False) -> str:
    """根据场景解析默认调度策略（单路始终本机）。"""
    if device_count <= 1:
        return 'local'
    if is_nvr:
        policy = os.getenv('STREAM_FORWARD_NVR_SCHEDULE_POLICY', 'auto').strip().lower()
    else:
        policy = os.getenv('STREAM_FORWARD_MULTI_DEVICE_SCHEDULE_POLICY', 'local').strip().lower()
    return policy if policy in ('local', 'auto', 'node') else 'local'


def _maybe_upgrade_nvr_schedule_policy(task: StreamForwardTask, device_count: int) -> bool:
    """NVR 多路任务可将历史 local 策略升级为集群 auto（可配置关闭）。"""
    if device_count <= 1 or not _is_nvr_stream_forward_task(task):
        return False
    upgrade = os.getenv('STREAM_FORWARD_NVR_UPGRADE_LOCAL', 'true').strip().lower() in ('1', 'true', 'yes', 'on')
    if not upgrade:
        return False
    if (task.schedule_policy or 'local') != 'local':
        return False
    task.schedule_policy = _default_schedule_policy(device_count, is_nvr=True)
    return True


def _trigger_deploy_sync(task_id: int, *, full_restart: bool = False) -> None:
    """任务运行中时同步部署：策略变更全量重启，设备变更增量重平衡。"""
    from .stream_forward_launcher_service import (
        rebalance_stream_forward_task,
        restart_stream_forward_task_services,
    )

    task = StreamForwardTask.query.get(task_id)
    if not task or not task.is_enabled:
        return
    try:
        if full_restart:
            if not restart_stream_forward_task_services(task_id):
                raise RuntimeError('重启推流转发服务失败')
        else:
            if not rebalance_stream_forward_task(task_id):
                raise RuntimeError('重平衡推流转发部署失败')
    except Exception as e:
        logger.warning('推流转发部署同步失败 task_id=%s: %s', task_id, e, exc_info=True)
        raise


def create_stream_forward_task(task_name: str,
                               device_ids: Optional[List[str]] = None,
                               output_format: str = 'rtmp',
                               output_quality: str = 'high',
                               output_bitrate: Optional[str] = None,
                               description: Optional[str] = None,
                               is_enabled: bool = False,
                               schedule_policy: str = 'local',
                               prefer_gpu: bool = True,
                               target_node_id: Optional[int] = None) -> StreamForwardTask:
    """创建推流转发任务"""
    try:
        device_id_list = device_ids or []
        
        # 验证所有设备是否存在
        for dev_id in device_id_list:
            Device.query.get_or_404(dev_id)
        
        # 注意：推流转发任务和算法任务可以共存，因为它们使用不同的流地址
        # 推流转发任务使用 rtmp_stream/http_stream，算法任务使用 ai_rtmp_stream/ai_http_stream
        
        # 生成任务编号
        task_code = f"STREAM_FORWARD_{uuid.uuid4().hex[:8].upper()}"
        
        # 创建任务
        task = StreamForwardTask(
            task_name=task_name,
            task_code=task_code,
            output_format=output_format,
            output_quality=output_quality,
            output_bitrate=output_bitrate,
            description=description,
            is_enabled=is_enabled,
            total_streams=len(device_id_list),
            schedule_policy=schedule_policy or 'local',
            prefer_gpu=prefer_gpu if prefer_gpu is not None else True,
            target_node_id=target_node_id,
        )
        
        db.session.add(task)
        # 先 flush 以确保任务有 ID，然后再关联设备
        db.session.flush()
        
        # 关联设备（在任务有 ID 后再关联，避免重复插入）
        if device_id_list:
            devices = Device.query.filter(Device.id.in_(device_id_list)).all()
            # 对于新创建的任务，直接设置设备列表
            # 但如果任务已存在关联（异常情况），则使用 extend 避免重复
            if task.devices:
                existing_device_ids = {d.id for d in task.devices}
                new_devices = [d for d in devices if d.id not in existing_device_ids]
                if new_devices:
                    task.devices.extend(new_devices)
            else:
                task.devices = devices
        
        db.session.commit()
        
        logger.info(f"创建推流转发任务成功: task_id={task.id}, task_name={task_name}")
        return task
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建推流转发任务失败: {str(e)}", exc_info=True)
        raise


def update_stream_forward_task(task_id: int, auto_rebalance: bool = True, **kwargs) -> Tuple[StreamForwardTask, Optional[str]]:
    """更新推流转发任务，返回 (task, sync_action)。sync_action: rebalance | full_restart | None"""
    try:
        task = StreamForwardTask.query.get_or_404(task_id)
        was_enabled = bool(task.is_enabled)
        device_ids_changed = False
        schedule_changed = False
        previous_schedule = task.schedule_policy or 'local'
        previous_target_node = task.target_node_id
        
        # 更新字段
        if 'task_name' in kwargs:
            task.task_name = kwargs['task_name']
        if 'device_ids' in kwargs:
            device_id_list = kwargs['device_ids'] or []
            # 验证所有设备是否存在
            for dev_id in device_id_list:
                Device.query.get_or_404(dev_id)
            
            # 注意：推流转发任务和算法任务可以共存，因为它们使用不同的流地址
            # 推流转发任务使用 rtmp_stream/http_stream，算法任务使用 ai_rtmp_stream/ai_http_stream
            
            # 更新关联设备（安全地更新，避免重复插入）
            devices = Device.query.filter(Device.id.in_(device_id_list)).all()
            # 获取当前已关联的设备ID集合
            current_device_ids = {d.id for d in task.devices}
            # 获取新的设备ID集合
            new_device_ids = {d.id for d in devices}
            device_ids_changed = current_device_ids != new_device_ids
            
            # 找出需要删除的设备（在当前关联中但不在新列表中的）
            devices_to_remove = [d for d in task.devices if d.id not in new_device_ids]
            # 找出需要添加的设备（在新列表中但不在当前关联中的）
            devices_to_add = [d for d in devices if d.id not in current_device_ids]
            
            # 移除不需要的设备
            for device in devices_to_remove:
                task.devices.remove(device)
            # 添加新的设备
            task.devices.extend(devices_to_add)
            
            task.total_streams = len(device_id_list)
            _maybe_upgrade_nvr_schedule_policy(task, len(device_id_list))
        if 'output_format' in kwargs:
            task.output_format = kwargs['output_format']
        if 'output_quality' in kwargs:
            task.output_quality = kwargs['output_quality']
        if 'output_bitrate' in kwargs:
            task.output_bitrate = kwargs['output_bitrate']
        if 'description' in kwargs:
            task.description = kwargs['description']
        if 'is_enabled' in kwargs:
            task.is_enabled = kwargs['is_enabled']
        if 'schedule_policy' in kwargs:
            new_policy = kwargs['schedule_policy'] or 'local'
            schedule_changed = new_policy != previous_schedule
            task.schedule_policy = new_policy
        if 'target_node_id' in kwargs:
            schedule_changed = schedule_changed or kwargs['target_node_id'] != previous_target_node
            task.target_node_id = kwargs['target_node_id']
        if 'prefer_gpu' in kwargs:
            task.prefer_gpu = bool(kwargs['prefer_gpu'])
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        sync_action = None
        if auto_rebalance and was_enabled and task.is_enabled and (device_ids_changed or schedule_changed):
            sync_action = 'full_restart' if schedule_changed else 'rebalance'
            _trigger_deploy_sync(task_id, full_restart=schedule_changed)
        
        logger.info(f"更新推流转发任务成功: task_id={task_id}")
        return task, sync_action
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新推流转发任务失败: {str(e)}", exc_info=True)
        raise


def delete_stream_forward_task(task_id: int):
    """删除推流转发任务"""
    try:
        task = StreamForwardTask.query.get_or_404(task_id)
        
        # 如果任务正在运行（is_enabled=True），先停止
        if task.is_enabled:
            from .stream_forward_launcher_service import stop_stream_forward_task
            stop_stream_forward_task(task_id)
        
        db.session.delete(task)
        db.session.commit()
        
        logger.info(f"删除推流转发任务成功: task_id={task_id}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除推流转发任务失败: {str(e)}", exc_info=True)
        raise


def get_stream_forward_task(task_id: int) -> StreamForwardTask:
    """获取推流转发任务详情"""
    task = StreamForwardTask.query.options(joinedload(StreamForwardTask.devices)).get_or_404(task_id)
    return task


def list_stream_forward_tasks(page_no: int = 1,
                               page_size: int = 10,
                               search: Optional[str] = None,
                               device_id: Optional[str] = None,
                               is_enabled: Optional[bool] = None) -> dict:
    """查询推流转发任务列表"""
    try:
        query = StreamForwardTask.query.options(joinedload(StreamForwardTask.devices))
        
        # 搜索条件
        if search:
            query = query.filter(
                or_(
                    StreamForwardTask.task_name.like(f'%{search}%'),
                    StreamForwardTask.task_code.like(f'%{search}%')
                )
            )
        
        # 设备筛选
        if device_id:
            query = query.join(StreamForwardTask.devices).filter(Device.id == device_id)
        
        # 启用状态筛选
        if is_enabled is not None:
            query = query.filter(StreamForwardTask.is_enabled == is_enabled)
        
        # 排序
        query = query.order_by(StreamForwardTask.created_at.desc())
        
        # 分页
        total = query.count()
        tasks = query.offset((page_no - 1) * page_size).limit(page_size).all()
        
        # 转换为字典
        items = [task.to_dict() for task in tasks]
        
        return {
            'items': items,
            'total': total,
            'page_no': page_no,
            'page_size': page_size
        }
        
    except Exception as e:
        logger.error(f"查询推流转发任务列表失败: {str(e)}", exc_info=True)
        raise


def start_stream_forward_task(task_id: int) -> tuple[StreamForwardTask, str, bool]:
    """启动推流转发任务
    
    只根据 is_enabled 来判断任务状态：
    - is_enabled=True: 运行中
    - is_enabled=False: 已停止
    """
    try:
        task = StreamForwardTask.query.get_or_404(task_id)
        
        # 检查是否已经启用（运行中）
        if task.is_enabled:
            return task, "任务已在运行中", True
        
        # 检查是否有关联的设备
        if not task.devices or len(task.devices) == 0:
            raise ValueError("推流转发任务必须关联至少一个摄像头")
        
        # 注意：推流转发任务和算法任务可以共存，因为它们使用不同的流地址
        # 推流转发任务使用 rtmp_stream/http_stream，算法任务使用 ai_rtmp_stream/ai_http_stream
        
        # 启动任务
        from .stream_forward_launcher_service import start_stream_forward_task as launcher_start
        launcher_start(task_id)
        
        # 更新状态
        task.is_enabled = True
        task.last_success_time = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"启动推流转发任务成功: task_id={task_id}")
        return task, "启动成功", False
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"启动推流转发任务失败: {str(e)}", exc_info=True)
        raise


def stop_stream_forward_task(task_id: int) -> StreamForwardTask:
    """停止推流转发任务
    
    只根据 is_enabled 来判断任务状态：
    - is_enabled=True: 运行中
    - is_enabled=False: 已停止
    """
    try:
        task = StreamForwardTask.query.get_or_404(task_id)
        
        # 检查是否已经停止
        if not task.is_enabled:
            return task
        
        # 停止任务
        from .stream_forward_launcher_service import stop_stream_forward_task as launcher_stop
        launcher_stop(task_id)
        
        # 更新状态
        task.is_enabled = False
        db.session.commit()
        
        logger.info(f"停止推流转发任务成功: task_id={task_id}")
        return task
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"停止推流转发任务失败: {str(e)}", exc_info=True)
        raise


def restart_stream_forward_task(task_id: int) -> StreamForwardTask:
    """重启推流转发任务"""
    try:
        task = StreamForwardTask.query.get_or_404(task_id)
        if not task.is_enabled:
            start_stream_forward_task(task_id)
            task = StreamForwardTask.query.get_or_404(task_id)
            logger.info(f"重启推流转发任务成功: task_id={task_id}")
            return task

        from .stream_forward_launcher_service import restart_stream_forward_task_services
        if not restart_stream_forward_task_services(task_id):
            raise RuntimeError('重启推流转发服务失败')

        task = StreamForwardTask.query.get_or_404(task_id)
        task.last_success_time = datetime.utcnow()
        db.session.commit()
        logger.info(f"重启推流转发任务成功: task_id={task_id}")
        return task
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"重启推流转发任务失败: {str(e)}", exc_info=True)
        raise


def _nvr_stream_forward_marker(nvr_id: int) -> str:
    return f'{_NVR_STREAM_FORWARD_MARKER_PREFIX}{nvr_id}'


def _find_nvr_stream_forward_task(nvr_id: int) -> Optional[StreamForwardTask]:
    marker = _nvr_stream_forward_marker(nvr_id)
    return StreamForwardTask.query.filter(
        StreamForwardTask.description.contains(marker),
    ).order_by(StreamForwardTask.id.desc()).first()


def ensure_nvr_stream_forward_task(nvr_id: int) -> Optional[StreamForwardTask]:
    """确保 NVR 下属全部 RTSP 挂载通道共用一个推流转发任务，不存在则创建并启动。"""
    from models import Nvr

    try:
        nvr = Nvr.query.get(nvr_id)
        if not nvr:
            logger.warning(f'NVR {nvr_id} 不存在，无法创建推流转发任务')
            return None

        devices = Device.query.filter_by(nvr_id=nvr_id).all()
        device_ids = [
            d.id for d in devices
            if d.source
            and d.source.strip()
            and not d.source.strip().lower().startswith('gb28181://')
        ]
        if not device_ids:
            logger.info(f'NVR {nvr_id} 下无可推流的 RTSP 通道，跳过推流转发任务')
            return None

        nvr_label = (nvr.name or nvr.ip or str(nvr_id)).strip()
        marker = _nvr_stream_forward_marker(nvr_id)
        description = f'NVR {nvr_label} 下属通道自动推流转发 ({marker})'
        task = _find_nvr_stream_forward_task(nvr_id)
        was_running = bool(task and task.is_enabled)

        if task:
            current_ids = {d.id for d in task.devices}
            new_ids = set(device_ids)
            schedule_upgraded = _maybe_upgrade_nvr_schedule_policy(task, len(device_ids))
            devices_changed = current_ids != new_ids or task.total_streams != len(device_ids)
            if devices_changed or schedule_upgraded:
                update_kwargs = {
                    'description': description,
                }
                if devices_changed:
                    update_kwargs['device_ids'] = device_ids
                if schedule_upgraded:
                    update_kwargs['schedule_policy'] = task.schedule_policy
                task, _ = update_stream_forward_task(
                    task.id,
                    auto_rebalance=was_running,
                    **update_kwargs,
                )
                task = StreamForwardTask.query.get(task.id)
                if was_running:
                    logger.info(
                        f'已更新并同步 NVR 推流转发部署: nvr_id={nvr_id}, task_id={task.id}, '
                        f'channels={len(device_ids)}, schedule={task.schedule_policy}',
                    )
            elif was_running:
                logger.info(
                    f'NVR 推流转发任务无设备/策略变化，跳过重平衡: nvr_id={nvr_id}, task_id={task.id}',
                )
            return task

        task_name = f'{nvr_label}-推流转发'
        schedule_policy = _default_schedule_policy(len(device_ids), is_nvr=True)
        task = create_stream_forward_task(
            task_name=task_name,
            device_ids=device_ids,
            output_format='rtmp',
            output_quality='high',
            description=description,
            is_enabled=False,
            schedule_policy=schedule_policy,
        )
        try:
            start_stream_forward_task(task.id)
            logger.info(
                f'为 NVR {nvr_id} 创建并启动推流转发任务: task_id={task.id}, channels={len(device_ids)}',
            )
        except Exception as e:
            logger.warning(f'NVR 推流转发任务创建成功但启动失败: task_id={task.id}, error={e}')
        return task
    except Exception as e:
        logger.error(f'为 NVR {nvr_id} 确保推流转发任务失败: {e}', exc_info=True)
        return None


def ensure_device_stream_forward_task(device_id: str) -> Optional[StreamForwardTask]:
    """确保摄像头存在推流转发任务，如果不存在则自动创建并启动
    
    Args:
        device_id: 摄像头ID
        
    Returns:
        StreamForwardTask: 推流转发任务对象，如果创建失败则返回None
    """
    try:
        # 检查设备是否存在
        device = Device.query.get(device_id)
        if not device:
            logger.warning(f"设备 {device_id} 不存在，无法创建推流转发任务")
            return None
        
        # 查询该摄像头是否已经存在于任何推流转发任务中
        existing_tasks = StreamForwardTask.query.filter(
            StreamForwardTask.devices.any(Device.id == device_id)
        ).all()
        
        # 如果已经存在任务，直接返回第一个任务
        if existing_tasks:
            logger.info(f"设备 {device_id} 已存在于推流转发任务中，任务ID: {existing_tasks[0].id}")
            return existing_tasks[0]
        
        # 注意：不再检查设备冲突，因为推流转发任务使用rtmp_stream，算法任务使用ai_rtmp，它们使用不同的流地址，可以同时使用
        
        # 创建新的推流转发任务
        task_name = f"{device.name or device_id}-推流转发"
        task = create_stream_forward_task(
            task_name=task_name,
            device_ids=[device_id],
            output_format='rtmp',
            output_quality='high',
            description=f"为设备 {device.name or device_id} 自动创建的推流转发任务",
            is_enabled=False  # 先创建，稍后启动
        )
        
        # 启动任务
        try:
            start_stream_forward_task(task.id)
            logger.info(f"为设备 {device_id} 自动创建并启动推流转发任务成功，任务ID: {task.id}")
        except Exception as e:
            logger.warning(f"为设备 {device_id} 自动创建推流转发任务成功，但启动失败: {str(e)}")
            # 即使启动失败，也返回任务对象
        
        return task
        
    except Exception as e:
        logger.error(f"为设备 {device_id} 确保推流转发任务失败: {str(e)}", exc_info=True)
        return None

