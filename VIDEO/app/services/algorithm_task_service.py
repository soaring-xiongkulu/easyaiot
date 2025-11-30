"""
算法任务管理服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import uuid
from datetime import datetime
from typing import List, Optional

from models import db, AlgorithmTask, Device, FrameExtractor, Sorter, Pusher, SnapSpace, algorithm_task_device

logger = logging.getLogger(__name__)


def create_algorithm_task(task_name: str,
                         task_type: str = 'realtime',
                         extractor_id: Optional[int] = None,
                         sorter_id: Optional[int] = None,
                         pusher_id: Optional[int] = None,
                         device_ids: Optional[List[str]] = None,
                         space_id: Optional[int] = None,
                         cron_expression: Optional[str] = None,
                         frame_skip: int = 1,
                         description: Optional[str] = None,
                         is_enabled: bool = False) -> AlgorithmTask:
    """创建算法任务"""
    try:
        # 验证任务类型
        if task_type not in ['realtime', 'snap']:
            raise ValueError(f"无效的任务类型: {task_type}，必须是 'realtime' 或 'snap'")
        
        device_id_list = device_ids or []
        
        # 验证所有设备是否存在
        for dev_id in device_id_list:
            Device.query.get_or_404(dev_id)
        
        # 实时算法任务：验证抽帧器和排序器（可选）
        if task_type == 'realtime':
            if extractor_id:
                FrameExtractor.query.get_or_404(extractor_id)
            if sorter_id:
                Sorter.query.get_or_404(sorter_id)
        else:
            # 抓拍算法任务：不需要抽帧器和排序器
            extractor_id = None
            sorter_id = None
        
        # 抓拍算法任务：验证抓拍空间
        if task_type == 'snap':
            if not space_id:
                raise ValueError("抓拍算法任务必须指定抓拍空间")
            SnapSpace.query.get_or_404(space_id)
            if not cron_expression:
                raise ValueError("抓拍算法任务必须指定Cron表达式")
        else:
            # 实时算法任务：不需要抓拍空间和Cron表达式
            space_id = None
            cron_expression = None
            frame_skip = 1
        
        # 验证推送器是否存在（如果提供）
        if pusher_id:
            Pusher.query.get_or_404(pusher_id)
        
        # 生成唯一编号
        prefix = "REALTIME_TASK" if task_type == 'realtime' else "SNAP_TASK"
        task_code = f"{prefix}_{uuid.uuid4().hex[:8].upper()}"
        
        task = AlgorithmTask(
            task_name=task_name,
            task_code=task_code,
            task_type=task_type,
            extractor_id=extractor_id,
            sorter_id=sorter_id,
            pusher_id=pusher_id,
            space_id=space_id,
            cron_expression=cron_expression,
            frame_skip=frame_skip,
            description=description,
            is_enabled=is_enabled
        )
        
        db.session.add(task)
        db.session.flush()  # 先flush以获取task.id
        
        # 关联多个摄像头
        if device_id_list:
            devices = Device.query.filter(Device.id.in_(device_id_list)).all()
            task.devices = devices
        
        db.session.commit()
        
        logger.info(f"创建算法任务成功: task_id={task.id}, task_name={task_name}, task_type={task_type}, device_ids={device_id_list}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建算法任务失败: {str(e)}")


def update_algorithm_task(task_id: int, **kwargs) -> AlgorithmTask:
    """更新算法任务"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        task_type = kwargs.get('task_type', task.task_type)
        
        # 处理设备ID列表
        device_id_list = kwargs.pop('device_ids', None)
        
        # 验证所有设备是否存在（如果提供）
        if device_id_list is not None:
            for dev_id in device_id_list:
                Device.query.get_or_404(dev_id)
        
        # 根据任务类型验证字段
        if task_type == 'realtime':
            # 实时算法任务：验证抽帧器和排序器（可选）
            if 'extractor_id' in kwargs and kwargs['extractor_id']:
                FrameExtractor.query.get_or_404(kwargs['extractor_id'])
            if 'sorter_id' in kwargs and kwargs['sorter_id']:
                Sorter.query.get_or_404(kwargs['sorter_id'])
            # 清除抓拍相关字段
            if 'space_id' in kwargs:
                kwargs['space_id'] = None
            if 'cron_expression' in kwargs:
                kwargs['cron_expression'] = None
            if 'frame_skip' in kwargs:
                kwargs['frame_skip'] = 1
        else:
            # 抓拍算法任务：验证抓拍空间
            if 'space_id' in kwargs and kwargs['space_id']:
                SnapSpace.query.get_or_404(kwargs['space_id'])
            # 清除实时算法任务相关字段
            if 'extractor_id' in kwargs:
                kwargs['extractor_id'] = None
            if 'sorter_id' in kwargs:
                kwargs['sorter_id'] = None
        
        # 验证推送器是否存在（如果提供）
        if 'pusher_id' in kwargs and kwargs['pusher_id']:
            Pusher.query.get_or_404(kwargs['pusher_id'])
        
        updatable_fields = [
            'task_name', 'task_type', 'extractor_id', 'sorter_id', 'pusher_id',
            'space_id', 'cron_expression', 'frame_skip',
            'description', 'is_enabled', 'status', 'exception_reason'
        ]
        
        for field in updatable_fields:
            if field in kwargs:
                setattr(task, field, kwargs[field])
        
        # 更新多对多关系
        if device_id_list is not None:
            devices = Device.query.filter(Device.id.in_(device_id_list)).all() if device_id_list else []
            task.devices = devices
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"更新算法任务成功: task_id={task_id}, task_type={task_type}, device_ids={device_id_list}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"更新算法任务失败: {str(e)}")


def delete_algorithm_task(task_id: int):
    """删除算法任务"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        
        logger.info(f"删除算法任务成功: task_id={task_id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"删除算法任务失败: {str(e)}")


def get_algorithm_task(task_id: int) -> AlgorithmTask:
    """获取算法任务详情"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        return task
    except Exception as e:
        logger.error(f"获取算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取算法任务失败: {str(e)}")


def list_algorithm_tasks(page_no: int = 1, page_size: int = 10,
                        search: Optional[str] = None,
                        device_id: Optional[str] = None,
                        task_type: Optional[str] = None,
                        is_enabled: Optional[bool] = None) -> dict:
    """查询算法任务列表"""
    try:
        query = AlgorithmTask.query
        
        if search:
            query = query.filter(
                db.or_(
                    AlgorithmTask.task_name.like(f'%{search}%'),
                    AlgorithmTask.task_code.like(f'%{search}%')
                )
            )
        
        if device_id:
            # 通过多对多关系查询
            query = query.filter(AlgorithmTask.devices.any(Device.id == device_id))
        
        if task_type:
            query = query.filter_by(task_type=task_type)
        
        if is_enabled is not None:
            query = query.filter_by(is_enabled=is_enabled)
        
        total = query.count()
        
        # 分页
        offset = (page_no - 1) * page_size
        tasks = query.order_by(
            AlgorithmTask.created_at.desc()
        ).offset(offset).limit(page_size).all()
        
        return {
            'items': [task.to_dict() for task in tasks],
            'total': total
        }
    except Exception as e:
        logger.error(f"查询算法任务列表失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"查询算法任务列表失败: {str(e)}")


def start_algorithm_task(task_id: int):
    """启动算法任务"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        task.run_status = 'running'
        task.status = 0
        task.exception_reason = None
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"启动算法任务成功: task_id={task_id}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"启动算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"启动算法任务失败: {str(e)}")


def stop_algorithm_task(task_id: int):
    """停止算法任务"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        task.run_status = 'stopped'
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"停止算法任务成功: task_id={task_id}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"停止算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"停止算法任务失败: {str(e)}")


def restart_algorithm_task(task_id: int):
    """重启算法任务"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        task.run_status = 'restarting'
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 这里可以添加实际的重启逻辑
        # 暂时先设置为running
        task.run_status = 'running'
        task.status = 0
        task.exception_reason = None
        db.session.commit()
        
        logger.info(f"重启算法任务成功: task_id={task_id}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"重启算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"重启算法任务失败: {str(e)}")

