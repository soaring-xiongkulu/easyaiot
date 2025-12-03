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

from models import db, AlgorithmTask, Device, SnapSpace, algorithm_task_device
import json

logger = logging.getLogger(__name__)


def create_algorithm_task(task_name: str,
                         task_type: str = 'realtime',
                         device_ids: Optional[List[str]] = None,
                         model_ids: Optional[List[int]] = None,
                         extract_interval: int = 25,
                         tracking_enabled: bool = False,
                         tracking_similarity_threshold: float = 0.2,
                         tracking_max_age: int = 25,
                         tracking_smooth_alpha: float = 0.25,
                         alert_hook_url: Optional[str] = None,
                         alert_hook_enabled: bool = False,
                         space_id: Optional[int] = None,
                         cron_expression: Optional[str] = None,
                         frame_skip: int = 1,
                         is_enabled: bool = False,
                         defense_mode: Optional[str] = None,
                         defense_schedule: Optional[str] = None) -> AlgorithmTask:
    """创建算法任务"""
    try:
        # 验证任务类型
        if task_type not in ['realtime', 'snap']:
            raise ValueError(f"无效的任务类型: {task_type}，必须是 'realtime' 或 'snap'")
        
        device_id_list = device_ids or []
        
        # 验证所有设备是否存在
        for dev_id in device_id_list:
            Device.query.get_or_404(dev_id)
        
        # 实时算法任务：验证模型ID列表
        if task_type == 'realtime':
            if not model_ids:
                raise ValueError("实时算法任务必须指定模型ID列表")
            # 验证模型是否存在并获取模型名称（支持默认模型和数据库模型）
            model_names_list = []
            # 默认模型映射：负数ID -> 模型文件路径
            default_model_map = {
                -1: 'yolo11n.pt',
                -2: 'yolov8n.pt',
            }
            try:
                # 调用AI模块API获取模型信息（仅对正数ID，即数据库中的模型）
                import requests
                import os
                ai_service_url = os.getenv('AI_SERVICE_URL', 'http://localhost:5000')
                for model_id in model_ids:
                    # 如果是负数ID，表示默认模型
                    if model_id < 0:
                        model_file = default_model_map.get(model_id)
                        if model_file:
                            model_names_list.append(f"{model_file} (默认模型)")
                        else:
                            logger.warning(f"未知的默认模型ID: {model_id}")
                            model_names_list.append(f"默认模型_{model_id}")
                    else:
                        # 正数ID，从数据库获取模型信息
                        try:
                            response = requests.get(
                                f"{ai_service_url}/model/{model_id}",
                                headers={'X-Authorization': f'Bearer {os.getenv("JWT_TOKEN", "")}'},
                                timeout=5
                            )
                            if response.status_code == 200:
                                model_data = response.json()
                                if model_data.get('code') == 0:
                                    model_info = model_data.get('data', {})
                                    model_name = model_info.get('name', f'Model_{model_id}')
                                    model_version = model_info.get('version', '')
                                    if model_version:
                                        model_names_list.append(f"{model_name} (v{model_version})")
                                    else:
                                        model_names_list.append(model_name)
                                else:
                                    logger.warning(f"获取模型 {model_id} 信息失败: {model_data.get('msg')}")
                                    model_names_list.append(f"Model_{model_id}")
                            else:
                                logger.warning(f"获取模型 {model_id} 信息失败: HTTP {response.status_code}")
                                model_names_list.append(f"Model_{model_id}")
                        except Exception as e:
                            logger.warning(f"获取模型 {model_id} 信息异常: {str(e)}")
                            model_names_list.append(f"Model_{model_id}")
            except Exception as e:
                logger.warning(f"调用AI模块API获取模型信息失败: {str(e)}，使用默认名称")
                # 对于默认模型，使用模型文件名；对于数据库模型，使用Model_ID格式
                model_names_list = []
                for mid in model_ids:
                    if mid < 0:
                        model_file = default_model_map.get(mid)
                        if model_file:
                            model_names_list.append(f"{model_file} (默认模型)")
                        else:
                            model_names_list.append(f"默认模型_{mid}")
                    else:
                        model_names_list.append(f"Model_{mid}")
            
            model_ids_json = json.dumps(model_ids)
            model_names = ','.join(model_names_list) if model_names_list else None
        else:
            # 抓拍算法任务：不需要模型列表
            model_ids_json = None
            model_names = None
        
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
                schedule = [[1] * 24 for _ in range(7)]
                defense_schedule = json.dumps(schedule)
            elif defense_mode == 'day':
                # 白天模式：6:00-18:00填充
                schedule = [[1 if 6 <= h < 18 else 0 for h in range(24)] for _ in range(7)]
                defense_schedule = json.dumps(schedule)
            elif defense_mode == 'night':
                # 夜间模式：18:00-6:00填充
                schedule = [[1 if h >= 18 or h < 6 else 0 for h in range(24)] for _ in range(7)]
                defense_schedule = json.dumps(schedule)
            else:
                # 半防模式：全部清空
                schedule = [[0] * 24 for _ in range(7)]
                defense_schedule = json.dumps(schedule)
        
        # 如果启用了告警Hook但没有提供URL，自动设置为固定的网关路径
        if alert_hook_enabled and not alert_hook_url:
            alert_hook_url = '/admin-api/video/alert/hook'
        
        task = AlgorithmTask(
            task_name=task_name,
            task_code=task_code,
            task_type=task_type,
            model_ids=model_ids_json,
            model_names=model_names,
            extract_interval=extract_interval if task_type == 'realtime' else 25,
            rtmp_input_url=None,  # 不再使用，从摄像头列表获取RTSP流地址
            rtmp_output_url=None,  # 不再使用，从摄像头列表获取RTMP流地址
            tracking_enabled=tracking_enabled if task_type == 'realtime' else False,
            tracking_similarity_threshold=tracking_similarity_threshold if task_type == 'realtime' else 0.2,
            tracking_max_age=tracking_max_age if task_type == 'realtime' else 25,
            tracking_smooth_alpha=tracking_smooth_alpha if task_type == 'realtime' else 0.25,
            alert_hook_url=alert_hook_url,
            alert_hook_enabled=alert_hook_enabled,
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
        
        # 提交所有更改（包括任务和算法服务）
        db.session.commit()
        
        logger.info(f"创建算法任务成功: task_id={task.id}, task_name={task_name}, task_type={task_type}, device_ids={device_id_list}, model_ids={model_ids}")
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
        
        # 处理模型ID列表
        model_ids = kwargs.pop('model_ids', None)
        
        # 验证所有设备是否存在（如果提供）
        if device_id_list is not None:
            for dev_id in device_id_list:
                Device.query.get_or_404(dev_id)
        
        # 根据任务类型验证字段
        if task_type == 'realtime':
            # 实时算法任务：验证模型ID列表
            if model_ids is not None:
                if not model_ids:
                    raise ValueError("实时算法任务必须指定模型ID列表")
                # 验证模型是否存在并获取模型名称（支持默认模型和数据库模型）
                model_names_list = []
                # 默认模型映射：负数ID -> 模型文件路径
                default_model_map = {
                    -1: 'yolo11n.pt',
                    -2: 'yolov8n.pt',
                }
                try:
                    # 调用AI模块API获取模型信息（仅对正数ID，即数据库中的模型）
                    import requests
                    import os
                    ai_service_url = os.getenv('AI_SERVICE_URL', 'http://localhost:5000')
                    for model_id in model_ids:
                        # 如果是负数ID，表示默认模型
                        if model_id < 0:
                            model_file = default_model_map.get(model_id)
                            if model_file:
                                model_names_list.append(f"{model_file} (默认模型)")
                            else:
                                logger.warning(f"未知的默认模型ID: {model_id}")
                                model_names_list.append(f"默认模型_{model_id}")
                        else:
                            # 正数ID，从数据库获取模型信息
                            try:
                                response = requests.get(
                                    f"{ai_service_url}/model/{model_id}",
                                    headers={'X-Authorization': f'Bearer {os.getenv("JWT_TOKEN", "")}'},
                                    timeout=5
                                )
                                if response.status_code == 200:
                                    model_data = response.json()
                                    if model_data.get('code') == 0:
                                        model_info = model_data.get('data', {})
                                        model_name = model_info.get('name', f'Model_{model_id}')
                                        model_version = model_info.get('version', '')
                                        if model_version:
                                            model_names_list.append(f"{model_name} (v{model_version})")
                                        else:
                                            model_names_list.append(model_name)
                                    else:
                                        logger.warning(f"获取模型 {model_id} 信息失败: {model_data.get('msg')}")
                                        model_names_list.append(f"Model_{model_id}")
                                else:
                                    logger.warning(f"获取模型 {model_id} 信息失败: HTTP {response.status_code}")
                                    model_names_list.append(f"Model_{model_id}")
                            except Exception as e:
                                logger.warning(f"获取模型 {model_id} 信息异常: {str(e)}")
                                model_names_list.append(f"Model_{model_id}")
                except Exception as e:
                    logger.warning(f"调用AI模块API获取模型信息失败: {str(e)}，使用默认名称")
                    # 对于默认模型，使用模型文件名；对于数据库模型，使用Model_ID格式
                    model_names_list = []
                    for mid in model_ids:
                        if mid < 0:
                            model_file = default_model_map.get(mid)
                            if model_file:
                                model_names_list.append(f"{model_file} (默认模型)")
                            else:
                                model_names_list.append(f"默认模型_{mid}")
                        else:
                            model_names_list.append(f"Model_{mid}")
                
                kwargs['model_ids'] = json.dumps(model_ids)
                kwargs['model_names'] = ','.join(model_names_list) if model_names_list else None
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
            if 'model_ids' in kwargs:
                kwargs['model_ids'] = None
            if 'model_names' in kwargs:
                kwargs['model_names'] = None
        
        # 验证推送器是否存在（如果提供）
        if 'pusher_id' in kwargs and kwargs['pusher_id']:
            Pusher.query.get_or_404(kwargs['pusher_id'])
        
        updatable_fields = [
            'task_name', 'task_type', 'pusher_id',
            'model_ids', 'model_names',  # 模型配置
            'extract_interval',  # 实时算法任务配置（rtmp_input_url和rtmp_output_url不再使用，从摄像头列表获取）
            'tracking_enabled', 'tracking_similarity_threshold', 'tracking_max_age', 'tracking_smooth_alpha',  # 追踪配置
            'alert_hook_url', 'alert_hook_enabled',  # 告警配置
            'space_id', 'cron_expression', 'frame_skip',  # 抓拍算法任务配置
            'is_enabled', 'status', 'exception_reason',
            'defense_mode', 'defense_schedule'
        ]
        
        # 验证布防模式
        if 'defense_mode' in kwargs:
            defense_mode = kwargs['defense_mode']
            if defense_mode and defense_mode not in ['full', 'half', 'day', 'night']:
                raise ValueError(f"无效的布防模式: {defense_mode}，必须是 'full', 'half', 'day' 或 'night'")
        
        # 如果启用了告警Hook但没有提供URL，自动设置为固定的网关路径
        if 'alert_hook_enabled' in kwargs and kwargs['alert_hook_enabled']:
            if 'alert_hook_url' not in kwargs or not kwargs.get('alert_hook_url'):
                kwargs['alert_hook_url'] = '/admin-api/video/alert/hook'
        
        for field in updatable_fields:
            if field in kwargs:
                setattr(task, field, kwargs[field])
        
        # 更新多对多关系
        if device_id_list is not None:
            devices = Device.query.filter(Device.id.in_(device_id_list)).all() if device_id_list else []
            task.devices = devices
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"更新算法任务成功: task_id={task_id}, task_type={task_type}, device_ids={device_id_list}, model_ids={model_ids}")
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
            joinedload(AlgorithmTask.devices),
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
            joinedload(AlgorithmTask.devices),
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
    """启动算法任务
    
    Returns:
        tuple[AlgorithmTask, str, bool]: (任务对象, 消息, 是否已运行)
    """
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        task.is_enabled = True
        task.status = 0
        task.exception_reason = None
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 启动任务相关的服务（抽帧器、推送器、排序器）
        service_message = "启动成功"
        already_running = False
        try:
            from app.services.algorithm_task_launcher_service import start_task_services
            success, msg, is_running = start_task_services(task_id, task)
            if success:
                service_message = msg
                already_running = is_running
            else:
                service_message = msg
                logger.warning(f"启动任务 {task_id} 的服务失败: {msg}")
        except Exception as e:
            logger.warning(f"启动任务 {task_id} 的服务时出错: {str(e)}", exc_info=True)
            service_message = f"服务启动异常: {str(e)}"
        
        logger.info(f"启动算法任务成功: task_id={task_id}, message={service_message}, already_running={already_running}")
        return task, service_message, already_running
    except Exception as e:
        db.session.rollback()
        logger.error(f"启动算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"启动算法任务失败: {str(e)}")


def stop_algorithm_task(task_id: int):
    """停止算法任务"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        task.is_enabled = False
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 停止任务相关的服务（抽帧器、推送器、排序器）
        try:
            from app.services.algorithm_task_launcher_service import stop_all_task_services
            stop_all_task_services(task_id)
        except Exception as e:
            logger.warning(f"停止任务 {task_id} 的服务时出错: {str(e)}", exc_info=True)
            # 不抛出异常，允许任务停止但服务可能未停止
        
        logger.info(f"停止算法任务成功: task_id={task_id}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"停止算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"停止算法任务失败: {str(e)}")


def restart_algorithm_task(task_id: int):
    """重启算法任务（使用守护进程的 restart 方法，更高效）"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        task.is_enabled = True
        task.status = 0
        task.exception_reason = None
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 尝试使用守护进程的 restart 方法（如果守护进程在运行）
        try:
            from app.services.algorithm_task_launcher_service import restart_task_services, start_task_services
            # 先尝试重启（如果守护进程在运行）
            if not restart_task_services(task_id):
                # 如果重启失败（守护进程未运行），则启动服务
                logger.info(f"守护进程未运行，启动服务: task_id={task_id}")
                start_task_services(task_id, task)
        except Exception as e:
            logger.warning(f"重启任务 {task_id} 的服务时出错: {str(e)}", exc_info=True)
            # 如果出错，尝试启动服务
            try:
                start_task_services(task_id, task)
            except Exception as e2:
                logger.error(f"启动任务 {task_id} 的服务也失败: {str(e2)}", exc_info=True)
        
        logger.info(f"重启算法任务成功: task_id={task_id}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"重启算法任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"重启算法任务失败: {str(e)}")

