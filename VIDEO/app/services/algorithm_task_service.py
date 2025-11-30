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

from models import db, AlgorithmTask, Device, FrameExtractor, Sorter

logger = logging.getLogger(__name__)


def create_algorithm_task(task_name: str, device_id: str,
                         extractor_id: Optional[int] = None,
                         sorter_id: Optional[int] = None,
                         description: Optional[str] = None,
                         is_enabled: bool = True) -> AlgorithmTask:
    """创建算法任务"""
    try:
        # 验证设备是否存在
        device = Device.query.get_or_404(device_id)
        
        # 验证抽帧器是否存在（如果提供）
        if extractor_id:
            FrameExtractor.query.get_or_404(extractor_id)
        
        # 验证排序器是否存在（如果提供）
        if sorter_id:
            Sorter.query.get_or_404(sorter_id)
        
        # 生成唯一编号
        task_code = f"ALG_TASK_{uuid.uuid4().hex[:8].upper()}"
        
        task = AlgorithmTask(
            task_name=task_name,
            task_code=task_code,
            device_id=device_id,
            extractor_id=extractor_id,
            sorter_id=sorter_id,
            description=description,
            is_enabled=is_enabled
        )
        
        db.session.add(task)
        db.session.commit()
        
        logger.info(f"创建算法任务成功: task_id={task.id}, task_name={task_name}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建算法任务失败: {str(e)}")


def update_algorithm_task(task_id: int, **kwargs) -> AlgorithmTask:
    """更新算法任务"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        
        # 验证设备是否存在（如果提供）
        if 'device_id' in kwargs:
            Device.query.get_or_404(kwargs['device_id'])
        
        # 验证抽帧器是否存在（如果提供）
        if 'extractor_id' in kwargs and kwargs['extractor_id']:
            FrameExtractor.query.get_or_404(kwargs['extractor_id'])
        
        # 验证排序器是否存在（如果提供）
        if 'sorter_id' in kwargs and kwargs['sorter_id']:
            Sorter.query.get_or_404(kwargs['sorter_id'])
        
        updatable_fields = [
            'task_name', 'device_id', 'extractor_id', 'sorter_id',
            'description', 'is_enabled', 'status', 'exception_reason'
        ]
        
        for field in updatable_fields:
            if field in kwargs:
                setattr(task, field, kwargs[field])
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"更新算法任务成功: task_id={task_id}")
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
            query = query.filter_by(device_id=device_id)
        
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

