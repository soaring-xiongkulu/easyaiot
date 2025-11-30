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
from sqlalchemy.orm import joinedload

from models import db, AlgorithmTask, Device, FrameExtractor, Sorter, Pusher, SnapSpace, algorithm_task_device
from app.services.algorithm_service import create_task_algorithm_service

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
                         is_enabled: bool = False,
                         defense_mode: Optional[str] = None,
                         defense_schedule: Optional[str] = None,
                         algorithm_services: Optional[List[dict]] = None) -> AlgorithmTask:
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
        
        # 处理布防时段配置
        if defense_mode:
            if defense_mode not in ['full', 'half', 'day', 'night']:
                raise ValueError(f"无效的布防模式: {defense_mode}，必须是 'full', 'half', 'day' 或 'night'")
        else:
            defense_mode = 'half'  # 默认半防模式
        
        # 如果未提供defense_schedule，根据模式生成默认值
        if not defense_schedule:
            if defense_mode == 'full':
                # 全防模式：全部填充
                import json
                schedule = [[1] * 24 for _ in range(7)]
                defense_schedule = json.dumps(schedule)
            elif defense_mode == 'day':
                # 白天模式：6:00-18:00填充
                import json
                schedule = [[1 if 6 <= h < 18 else 0 for h in range(24)] for _ in range(7)]
                defense_schedule = json.dumps(schedule)
            elif defense_mode == 'night':
                # 夜间模式：18:00-6:00填充
                import json
                schedule = [[1 if h >= 18 or h < 6 else 0 for h in range(24)] for _ in range(7)]
                defense_schedule = json.dumps(schedule)
            else:
                # 半防模式：全部清空
                import json
                schedule = [[0] * 24 for _ in range(7)]
                defense_schedule = json.dumps(schedule)
        
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
            is_enabled=is_enabled,
            defense_mode=defense_mode,
            defense_schedule=defense_schedule
        )
        
        db.session.add(task)
        db.session.flush()  # 先flush以获取task.id
        
        # 关联多个摄像头
        if device_id_list:
            devices = Device.query.filter(Device.id.in_(device_id_list)).all()
            task.devices = devices
        
        # 根据前端传递的算法服务信息创建算法服务（在提交事务之前）
        service_names_list = []
        if algorithm_services:
            # 前端直接传递完整的算法服务信息
            from models import AlgorithmModelService
            import json
            
            for idx, service_data in enumerate(algorithm_services):
                try:
                    # 验证必要字段
                    service_name = service_data.get('service_name')
                    service_url = service_data.get('service_url') or service_data.get('inference_endpoint')
                    
                    if not service_name:
                        logger.warning(f"算法服务缺少 service_name，跳过创建")
                        continue
                    
                    if not service_url:
                        logger.warning(f"算法服务 {service_name} 缺少 service_url 或 inference_endpoint，跳过创建")
                        continue
                    
                    # 处理请求头和请求体模板（可能是字符串或字典）
                    request_headers = service_data.get('request_headers')
                    if isinstance(request_headers, dict):
                        request_headers = json.dumps(request_headers)
                    elif isinstance(request_headers, str):
                        # 已经是字符串，直接使用
                        pass
                    else:
                        request_headers = None
                    
                    request_body_template = service_data.get('request_body_template')
                    if isinstance(request_body_template, dict):
                        request_body_template = json.dumps(request_body_template)
                    elif isinstance(request_body_template, str):
                        # 已经是字符串，直接使用
                        pass
                    else:
                        request_body_template = None
                    
                    # 创建算法服务（在事务内）
                    service = AlgorithmModelService(
                        task_id=task.id,
                        service_name=service_name,
                        service_url=service_url,
                        service_type=service_data.get('service_type'),
                        model_id=service_data.get('model_id'),
                        threshold=service_data.get('threshold'),
                        request_method=service_data.get('request_method', 'POST'),
                        request_headers=request_headers,
                        request_body_template=request_body_template,
                        timeout=service_data.get('timeout', 30),
                        is_enabled=service_data.get('is_enabled', True),
                        sort_order=service_data.get('sort_order', idx)
                    )
                    
                    db.session.add(service)
                    service_names_list.append(service_name)
                    logger.info(f"为任务 {task.id} 创建算法服务成功: service_name={service_name}, service_url={service_url}")
                except Exception as e:
                    logger.error(f"创建算法服务失败: service_data={service_data}, error={str(e)}", exc_info=True)
                    # 继续处理其他服务，不中断整个流程
                    continue
        
        # 保存服务名称列表到冗余字段
        if service_names_list:
            task.service_names = ', '.join(service_names_list)
        
        # 提交所有更改（包括任务和算法服务）
        db.session.commit()
        
        logger.info(f"创建算法任务成功: task_id={task.id}, task_name={task_name}, task_type={task_type}, device_ids={device_id_list}, algorithm_services_count={len(algorithm_services) if algorithm_services else 0}")
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
        
        # 处理算法服务列表
        algorithm_services = kwargs.pop('algorithm_services', None)
        
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
            'is_enabled', 'status', 'exception_reason',
            'defense_mode', 'defense_schedule'
        ]
        
        # 验证布防模式
        if 'defense_mode' in kwargs:
            defense_mode = kwargs['defense_mode']
            if defense_mode and defense_mode not in ['full', 'half', 'day', 'night']:
                raise ValueError(f"无效的布防模式: {defense_mode}，必须是 'full', 'half', 'day' 或 'night'")
        
        for field in updatable_fields:
            if field in kwargs:
                setattr(task, field, kwargs[field])
        
        # 更新多对多关系
        if device_id_list is not None:
            devices = Device.query.filter(Device.id.in_(device_id_list)).all() if device_id_list else []
            task.devices = devices
        
        # 处理算法服务列表（如果提供）
        service_names_list = []
        if algorithm_services is not None:
            # 前端直接传递完整的算法服务信息
            from models import AlgorithmModelService
            import json
            
            # 删除旧的算法服务
            AlgorithmModelService.query.filter_by(task_id=task_id).delete()
            
            # 创建新的算法服务
            if algorithm_services:
                for idx, service_data in enumerate(algorithm_services):
                    try:
                        # 验证必要字段
                        service_name = service_data.get('service_name')
                        service_url = service_data.get('service_url') or service_data.get('inference_endpoint')
                        
                        if not service_name:
                            logger.warning(f"算法服务缺少 service_name，跳过创建")
                            continue
                        
                        if not service_url:
                            logger.warning(f"算法服务 {service_name} 缺少 service_url 或 inference_endpoint，跳过创建")
                            continue
                        
                        # 处理请求头和请求体模板（可能是字符串或字典）
                        request_headers = service_data.get('request_headers')
                        if isinstance(request_headers, dict):
                            request_headers = json.dumps(request_headers)
                        elif isinstance(request_headers, str):
                            # 已经是字符串，直接使用
                            pass
                        else:
                            request_headers = None
                        
                        request_body_template = service_data.get('request_body_template')
                        if isinstance(request_body_template, dict):
                            request_body_template = json.dumps(request_body_template)
                        elif isinstance(request_body_template, str):
                            # 已经是字符串，直接使用
                            pass
                        else:
                            request_body_template = None
                        
                        # 创建算法服务（在事务内）
                        service = AlgorithmModelService(
                            task_id=task.id,
                            service_name=service_name,
                            service_url=service_url,
                            service_type=service_data.get('service_type'),
                            model_id=service_data.get('model_id'),
                            threshold=service_data.get('threshold'),
                            request_method=service_data.get('request_method', 'POST'),
                            request_headers=request_headers,
                            request_body_template=request_body_template,
                            timeout=service_data.get('timeout', 30),
                            is_enabled=service_data.get('is_enabled', True),
                            sort_order=service_data.get('sort_order', idx)
                        )
                        
                        db.session.add(service)
                        service_names_list.append(service_name)
                        logger.info(f"为任务 {task.id} 更新算法服务成功: service_name={service_name}, service_url={service_url}")
                    except Exception as e:
                        logger.error(f"更新算法服务失败: service_data={service_data}, error={str(e)}", exc_info=True)
                        # 继续处理其他服务，不中断整个流程
                        continue
            
            # 更新服务名称列表到冗余字段
            task.service_names = ', '.join(service_names_list) if service_names_list else None
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"更新算法任务成功: task_id={task_id}, task_type={task_type}, device_ids={device_id_list}, algorithm_services_count={len(algorithm_services) if algorithm_services else 0}")
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
        task = AlgorithmTask.query.options(
            joinedload(AlgorithmTask.algorithm_services),
            joinedload(AlgorithmTask.devices),
            joinedload(AlgorithmTask.extractor),
            joinedload(AlgorithmTask.sorter),
            joinedload(AlgorithmTask.pusher),
            joinedload(AlgorithmTask.snap_space)
        ).get_or_404(task_id)
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
        query = AlgorithmTask.query.options(
            joinedload(AlgorithmTask.algorithm_services),
            joinedload(AlgorithmTask.devices),
            joinedload(AlgorithmTask.extractor),
            joinedload(AlgorithmTask.sorter),
            joinedload(AlgorithmTask.pusher),
            joinedload(AlgorithmTask.snap_space)
        )
        
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
            AlgorithmTask.updated_at.desc()
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

