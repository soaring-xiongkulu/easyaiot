"""
推流转发任务管理服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_

from models import db, StreamForwardTask, Device
from app.utils.device_conflict_checker import (
    check_device_conflict_with_algorithm_tasks,
    format_conflict_message
)
import json

logger = logging.getLogger(__name__)


def create_stream_forward_task(task_name: str,
                               device_ids: Optional[List[str]] = None,
                               output_format: str = 'rtmp',
                               output_quality: str = 'high',
                               output_bitrate: Optional[str] = None,
                               description: Optional[str] = None,
                               is_enabled: bool = False) -> StreamForwardTask:
    """创建推流转发任务"""
    try:
        device_id_list = device_ids or []
        
        # 验证所有设备是否存在
        for dev_id in device_id_list:
            Device.query.get_or_404(dev_id)
        
        # 检查摄像头是否已经在启用的算法任务中使用
        if device_id_list:
            has_conflict, conflicts = check_device_conflict_with_algorithm_tasks(device_id_list)
            if has_conflict:
                conflict_msg = format_conflict_message(conflicts, 'algorithm')
                raise ValueError(f"摄像头冲突：{conflict_msg}。同一个摄像头不能同时用于推流转发和算法任务。")
        
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
            total_streams=len(device_id_list)
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


def update_stream_forward_task(task_id: int, **kwargs) -> StreamForwardTask:
    """更新推流转发任务"""
    try:
        task = StreamForwardTask.query.get_or_404(task_id)
        
        # 更新字段
        if 'task_name' in kwargs:
            task.task_name = kwargs['task_name']
        if 'device_ids' in kwargs:
            device_id_list = kwargs['device_ids'] or []
            # 验证所有设备是否存在
            for dev_id in device_id_list:
                Device.query.get_or_404(dev_id)
            
            # 检查摄像头是否已经在启用的算法任务中使用（排除当前任务）
            if device_id_list:
                has_conflict, conflicts = check_device_conflict_with_algorithm_tasks(device_id_list, exclude_task_id=task_id)
                if has_conflict:
                    conflict_msg = format_conflict_message(conflicts, 'algorithm')
                    raise ValueError(f"摄像头冲突：{conflict_msg}。同一个摄像头不能同时用于推流转发和算法任务。")
            
            # 更新关联设备（安全地更新，避免重复插入）
            devices = Device.query.filter(Device.id.in_(device_id_list)).all()
            # 获取当前已关联的设备ID集合
            current_device_ids = {d.id for d in task.devices}
            # 获取新的设备ID集合
            new_device_ids = {d.id for d in devices}
            
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
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"更新推流转发任务成功: task_id={task_id}")
        return task
        
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
        
        # 检查摄像头是否已经在启用的算法任务中使用
        device_ids = [d.id for d in task.devices]
        has_conflict, conflicts = check_device_conflict_with_algorithm_tasks(device_ids)
        if has_conflict:
            conflict_msg = format_conflict_message(conflicts, 'algorithm')
            raise ValueError(f"摄像头冲突：{conflict_msg}。同一个摄像头不能同时用于推流转发和算法任务。")
        
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
        # 先停止
        stop_stream_forward_task(task_id)
        
        # 再启动
        start_stream_forward_task(task_id)
        
        task = StreamForwardTask.query.get_or_404(task_id)
        logger.info(f"重启推流转发任务成功: task_id={task_id}")
        return task
        
    except Exception as e:
        logger.error(f"重启推流转发任务失败: {str(e)}", exc_info=True)
        raise

