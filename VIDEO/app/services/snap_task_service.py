"""
抓拍任务服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import uuid
from datetime import datetime
from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from models import db, SnapTask, SnapSpace, Device
from app.services.snap_space_service import get_minio_client, create_camera_folder
from app.services.camera_service import get_snapshot_uri

logger = logging.getLogger(__name__)

# 全局任务调度器
_scheduler = None
_running_tasks = {}  # 存储运行中的任务ID


def get_scheduler():
    """获取全局调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
        _scheduler.start()
        logger.info("抓拍任务调度器已启动")
    return _scheduler


def create_snap_task(
    task_name, space_id, device_id,
    capture_type=0, cron_expression="0 */5 * * * *", frame_skip=1,
    algorithm_enabled=False, algorithm_type=None, algorithm_model_id=None,
    algorithm_threshold=None, algorithm_night_mode=False,
    alarm_enabled=False, alarm_type=0, phone_number=None, email=None,
    notify_users=None, notify_methods=None, alarm_suppress_time=300,
    auto_filename=True, custom_filename_prefix=None
):
    """创建抓拍任务"""
    try:
        # 验证空间和设备存在
        space = SnapSpace.query.get_or_404(space_id)
        device = Device.query.get_or_404(device_id)
        
        # 生成唯一编号
        task_code = f"TASK_{uuid.uuid4().hex[:8].upper()}"
        
        # 处理通知人列表（如果是字典则转换为JSON字符串）
        import json
        notify_users_json = None
        if notify_users:
            if isinstance(notify_users, (dict, list)):
                notify_users_json = json.dumps(notify_users, ensure_ascii=False)
            else:
                notify_users_json = notify_users
        
        # 创建任务记录
        snap_task = SnapTask(
            task_name=task_name,
            task_code=task_code,
            space_id=space_id,
            device_id=device_id,
            capture_type=capture_type,
            cron_expression=cron_expression,
            frame_skip=frame_skip,
            algorithm_enabled=algorithm_enabled,
            algorithm_type=algorithm_type,
            algorithm_model_id=algorithm_model_id,
            algorithm_threshold=algorithm_threshold,
            algorithm_night_mode=algorithm_night_mode,
            alarm_enabled=alarm_enabled,
            alarm_type=alarm_type,
            phone_number=phone_number,
            email=email,
            notify_users=notify_users_json,
            notify_methods=notify_methods,
            alarm_suppress_time=alarm_suppress_time,
            auto_filename=auto_filename,
            custom_filename_prefix=custom_filename_prefix,
            is_enabled=True,
            status=0,
            run_status='stopped'
        )
        
        db.session.add(snap_task)
        db.session.commit()
        
        # 确保设备文件夹存在
        create_camera_folder(space_id, device_id)
        
        # 如果任务启用，添加到调度器
        if snap_task.is_enabled:
            add_task_to_scheduler(snap_task.id)
        
        logger.info(f"抓拍任务创建成功: {task_name} ({task_code})")
        return snap_task
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建抓拍任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建抓拍任务失败: {str(e)}")


def update_snap_task(task_id, **kwargs):
    """更新抓拍任务"""
    try:
        task = SnapTask.query.get_or_404(task_id)
        
        # 更新字段
        updatable_fields = [
            'task_name', 'space_id', 'device_id', 'capture_type',
            'cron_expression', 'frame_skip', 'algorithm_enabled',
            'algorithm_type', 'algorithm_model_id', 'algorithm_threshold',
            'algorithm_night_mode', 'alarm_enabled', 'alarm_type',
            'phone_number', 'email', 'auto_filename', 'custom_filename_prefix',
            'is_enabled', 'notify_methods', 'alarm_suppress_time'
        ]
        
        for field in updatable_fields:
            if field in kwargs:
                setattr(task, field, kwargs[field])
        
        # 处理通知人列表
        if 'notify_users' in kwargs:
            import json
            notify_users = kwargs['notify_users']
            if notify_users:
                if isinstance(notify_users, (dict, list)):
                    task.notify_users = json.dumps(notify_users, ensure_ascii=False)
                else:
                    task.notify_users = notify_users
            else:
                task.notify_users = None
        
        db.session.commit()
        
        # 重新调度任务
        remove_task_from_scheduler(task_id)
        if task.is_enabled:
            add_task_to_scheduler(task_id)
        
        logger.info(f"抓拍任务更新成功: ID={task_id}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新抓拍任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"更新抓拍任务失败: {str(e)}")


def delete_snap_task(task_id):
    """删除抓拍任务"""
    try:
        task = SnapTask.query.get_or_404(task_id)
        
        # 从调度器移除
        remove_task_from_scheduler(task_id)
        
        # 删除数据库记录
        db.session.delete(task)
        db.session.commit()
        
        logger.info(f"抓拍任务删除成功: ID={task_id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除抓拍任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"删除抓拍任务失败: {str(e)}")


def get_snap_task(task_id):
    """获取抓拍任务详情"""
    try:
        task = SnapTask.query.get_or_404(task_id)
        task_dict = task.to_dict()
        
        # 获取设备名称
        device = Device.query.get(task.device_id)
        if device:
            task_dict['device_name'] = device.name
        
        return task_dict
    except Exception as e:
        logger.error(f"获取抓拍任务失败: {str(e)}")
        raise ValueError(f"抓拍任务不存在: ID={task_id}")


def list_snap_tasks(page_no=1, page_size=10, space_id=None, device_id=None, search=None, status=None):
    """查询抓拍任务列表"""
    try:
        query = db.session.query(SnapTask, Device.name.label('device_name')).join(
            Device, SnapTask.device_id == Device.id
        )
        
        if space_id:
            query = query.filter(SnapTask.space_id == space_id)
        if device_id:
            query = query.filter(SnapTask.device_id == device_id)
        if search:
            query = query.filter(SnapTask.task_name.ilike(f'%{search}%'))
        if status is not None:
            query = query.filter(SnapTask.status == status)
        
        query = query.order_by(SnapTask.created_at.desc())
        
        # 手动分页
        total = query.count()
        offset = (page_no - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        result = []
        for task, device_name in items:
            task_dict = task.to_dict()
            task_dict['device_name'] = device_name
            result.append(task_dict)
        
        return {
            'items': result,
            'total': total,
            'page_no': page_no,
            'page_size': page_size
        }
    except Exception as e:
        logger.error(f"查询抓拍任务列表失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"查询抓拍任务列表失败: {str(e)}")


def add_task_to_scheduler(task_id):
    """将任务添加到调度器"""
    try:
        task = SnapTask.query.get(task_id)
        if not task or not task.is_enabled:
            return
        
        scheduler = get_scheduler()
        job_id = f"snap_task_{task_id}"
        
        # 如果任务已存在，先移除
        if job_id in _running_tasks:
            remove_task_from_scheduler(task_id)
        
        # 解析cron表达式并添加任务
        try:
            # 简单的cron解析（秒 分 时 日 月 周）
            cron_parts = task.cron_expression.strip().split()
            if len(cron_parts) == 6:
                trigger = CronTrigger(
                    second=cron_parts[0],
                    minute=cron_parts[1],
                    hour=cron_parts[2],
                    day=cron_parts[3],
                    month=cron_parts[4],
                    day_of_week=cron_parts[5]
                )
            elif len(cron_parts) == 5:
                # 标准cron（分 时 日 月 周）
                trigger = CronTrigger(
                    minute=cron_parts[0],
                    hour=cron_parts[1],
                    day=cron_parts[2],
                    month=cron_parts[3],
                    day_of_week=cron_parts[4]
                )
            else:
                logger.error(f"无效的cron表达式: {task.cron_expression}")
                return
            
            scheduler.add_job(
                execute_snap_task,
                trigger=trigger,
                id=job_id,
                args=[task_id],
                replace_existing=True
            )
            
            _running_tasks[task_id] = job_id
            logger.info(f"任务已添加到调度器: {task.task_name} (ID={task_id})")
        except Exception as e:
            logger.error(f"添加任务到调度器失败: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"添加任务到调度器失败: {str(e)}", exc_info=True)


def remove_task_from_scheduler(task_id):
    """从调度器移除任务"""
    try:
        job_id = f"snap_task_{task_id}"
        if job_id in _running_tasks.values():
            scheduler = get_scheduler()
            scheduler.remove_job(job_id)
            _running_tasks.pop(task_id, None)
            logger.info(f"任务已从调度器移除: ID={task_id}")
    except Exception as e:
        logger.error(f"从调度器移除任务失败: {str(e)}", exc_info=True)


def execute_snap_task(task_id):
    """执行抓拍任务"""
    try:
        task = SnapTask.query.get(task_id)
        if not task or not task.is_enabled:
            return
        
        # 检查夜间模式
        if task.algorithm_night_mode:
            from datetime import datetime
            now = datetime.now()
            hour = now.hour
            if not (hour >= 23 or hour < 8):
                logger.debug(f"任务 {task.task_name} 处于夜间模式，当前时间不在23:00-08:00范围内，跳过执行")
                return
        
        # 获取设备和空间信息
        device = Device.query.get(task.device_id)
        space = SnapSpace.query.get(task.space_id)
        
        if not device or not space:
            logger.error(f"任务 {task.task_name} 关联的设备或空间不存在")
            task.status = 1
            task.exception_reason = "关联的设备或空间不存在"
            db.session.commit()
            return
        
        # 执行抓拍
        success = capture_image(task, device, space)
        
        # 更新任务统计
        task.total_captures += 1
        task.last_capture_time = datetime.utcnow()
        if success:
            task.last_success_time = datetime.utcnow()
            task.status = 0
            task.exception_reason = None
        else:
            task.status = 1
            task.exception_reason = "抓拍失败"
        
        db.session.commit()
        
    except Exception as e:
        logger.error(f"执行抓拍任务失败: {str(e)}", exc_info=True)
        task = SnapTask.query.get(task_id)
        if task:
            task.status = 1
            task.exception_reason = str(e)
            db.session.commit()


def crop_region_from_frame(frame, points):
    """从帧中裁剪区域
    
    Args:
        frame: 原始帧（numpy数组）
        points: 区域坐标点列表，格式：[{x: 0.1, y: 0.2}, ...]（归一化坐标0-1）
    
    Returns:
        numpy数组: 裁剪后的图片
    """
    try:
        import cv2
        import numpy as np
        
        height, width = frame.shape[:2]
        
        # 转换归一化坐标为像素坐标
        pixel_points = []
        for point in points:
            x = int(point['x'] * width)
            y = int(point['y'] * height)
            pixel_points.append([x, y])
        
        pixel_points = np.array(pixel_points, dtype=np.int32)
        
        # 创建掩码
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(mask, [pixel_points], 255)
        
        # 裁剪区域
        cropped = cv2.bitwise_and(frame, frame, mask=mask)
        
        # 获取边界框
        x, y, w, h = cv2.boundingRect(pixel_points)
        cropped_roi = cropped[y:y+h, x:x+w]
        
        return cropped_roi
    except Exception as e:
        logger.error(f"裁剪区域失败: {str(e)}", exc_info=True)
        return frame


def should_trigger_alarm(result: dict, threshold: float = None) -> bool:
    """判断检测结果是否应该触发告警
    
    Args:
        result: 算法服务返回的结果
        threshold: 阈值
    
    Returns:
        bool: 是否触发告警
    """
    try:
        # 根据不同的结果格式判断
        if isinstance(result, dict):
            # 检查是否有检测到目标
            if 'detected' in result and result['detected']:
                if threshold is not None:
                    confidence = result.get('confidence', result.get('score', 0))
                    return confidence >= threshold
                return True
            
            # 检查置信度
            if 'confidence' in result or 'score' in result:
                confidence = result.get('confidence', result.get('score', 0))
                if threshold is not None:
                    return confidence >= threshold
                return confidence > 0.5  # 默认阈值
        
        return False
    except Exception as e:
        logger.error(f"判断告警触发失败: {str(e)}", exc_info=True)
        return False


def send_alert_for_detection(task, region, detection_result, frame, device):
    """发送检测告警
    
    Args:
        task: 任务对象
        region: 检测区域对象（可选）
        detection_result: 检测结果
        frame: 检测的图片帧
        device: 设备对象
    """
    try:
        from app.services.notification_service import send_alert_notification
        from app.services.alert_service import create_alert
        from datetime import datetime
        import cv2
        import io
        import base64
        
        # 构建告警数据
        alert_data = {
            'object': detection_result.get('object_type', 'UNKNOWN'),
            'event': detection_result.get('event_type', 'DETECTION'),
            'device_id': device.id,
            'device_name': device.name,
            'region': region.region_name if region else None,
            'information': detection_result,
            'time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 保存图片（可选，如果需要）
        # 这里可以保存到MinIO并获取路径
        
        # 创建告警记录
        try:
            alert_record = create_alert(alert_data)
            alert_data['image_path'] = alert_record.get('image_path')
            alert_data['record_path'] = alert_record.get('record_path')
        except Exception as e:
            logger.warning(f"创建告警记录失败: {str(e)}")
        
        # 发送通知
        send_alert_notification(task, alert_data)
        
    except Exception as e:
        logger.error(f"发送检测告警失败: {str(e)}", exc_info=True)


def capture_image(task, device, space):
    """执行实际的抓拍操作"""
    try:
        import cv2
        import numpy as np
        import io
        import requests
        import subprocess
        from datetime import datetime
        
        minio_client = get_minio_client()
        bucket_name = space.bucket_name
        space_code = space.space_code
        device_folder = f"{device.id}/"
        
        # 根据抓拍类型选择不同的抓拍方式
        if task.capture_type == 0:  # 抽帧
            source = device.source.strip() if device.source else None
            if not source:
                logger.error(f"设备 {device.id} 源地址为空")
                return False
            
            source_lower = source.lower()
            
            # 判断是否是RTMP流
            if source_lower.startswith('rtmp://'):
                # 使用FFmpeg从RTMP流中抽帧
                try:
                    # 使用FFmpeg从RTMP流中抽取一帧并输出为JPEG格式
                    ffmpeg_cmd = [
                        'ffmpeg',
                        '-i', source,  # RTMP流地址
                        '-vframes', '1',  # 只抽取1帧
                        '-f', 'image2',  # 输出格式为图片
                        '-vcodec', 'mjpeg',  # 使用MJPEG编码
                        '-q:v', '2',  # 高质量
                        'pipe:1'  # 输出到标准输出
                    ]
                    
                    # 执行FFmpeg命令并捕获输出
                    process = subprocess.Popen(
                        ffmpeg_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    stdout, stderr = process.communicate(timeout=10)  # 10秒超时
                    
                    if process.returncode != 0:
                        error_msg = stderr.decode('utf-8', errors='ignore') if stderr else '未知错误'
                        logger.error(f"设备 {device.id} RTMP流抽帧失败: {error_msg}")
                        return False
                    
                    if not stdout:
                        logger.error(f"设备 {device.id} RTMP流抽帧失败: 未获取到图像数据")
                        return False
                    
                    # 将FFmpeg输出的JPEG数据解码为OpenCV图像
                    image_array = np.frombuffer(stdout, np.uint8)
                    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                    
                    if frame is None:
                        logger.error(f"设备 {device.id} RTMP流抽帧失败: 图像解码失败")
                        return False
                    
                    logger.info(f"设备 {device.id} 从RTMP流成功抽帧")
                except subprocess.TimeoutExpired:
                    logger.error(f"设备 {device.id} RTMP流抽帧超时")
                    return False
                except Exception as e:
                    logger.error(f"设备 {device.id} RTMP流抽帧异常: {str(e)}", exc_info=True)
                    return False
            else:
                # 从RTSP流中抽帧（使用OpenCV）
                cap = cv2.VideoCapture(source)
                ret, frame = cap.read()
                cap.release()
                
                if not ret:
                    logger.error(f"设备 {device.id} RTSP流读取失败")
                    return False
        else:  # 抓拍（使用ONVIF快照）
            snapshot_uri = get_snapshot_uri(device.ip, device.port, device.username, device.password)
            if not snapshot_uri:
                logger.error(f"设备 {device.id} 无法获取ONVIF快照URI")
                return False
            
            auth = (device.username, device.password) if device.username and device.password else None
            response = requests.get(snapshot_uri, auth=auth, timeout=10)
            if response.status_code != 200:
                logger.error(f"设备 {device.id} ONVIF快照请求失败: {response.status_code}")
                return False
            
            image_bytes = io.BytesIO(response.content)
            image_np = cv2.imdecode(np.frombuffer(image_bytes.read(), np.uint8), cv2.IMREAD_COLOR)
            frame = image_np
        
        # 如果启用算法推理，调用AI服务
        if task.algorithm_enabled:
            # 获取检测区域
            from models import DetectionRegion
            regions = DetectionRegion.query.filter_by(
                task_id=task.id, 
                is_enabled=True
            ).order_by(DetectionRegion.sort_order).all()
            
            # 检查是否配置了检测区域
            has_regions = len(regions) > 0
            
            if has_regions:
                # 根据检测区域进行检测
                for region in regions:
                    if not region.algorithm_enabled:
                        continue
                    
                    # 获取区域的模型服务配置
                    from app.services.algorithm_service import get_region_algorithm_services, call_algorithm_service
                    region_services = get_region_algorithm_services(region.id)
                    
                    if region_services:
                        # 裁剪区域图片
                        import json
                        try:
                            points = json.loads(region.points) if isinstance(region.points, str) else region.points
                            cropped_frame = crop_region_from_frame(frame, points)
                            
                            # 调用区域的每个模型服务
                            for service in region_services:
                                if not service.is_enabled:
                                    continue
                                
                                try:
                                    # 编码裁剪后的图片
                                    success, encoded_image = cv2.imencode('.jpg', cropped_frame)
                                    if success:
                                        image_bytes = encoded_image.tobytes()
                                        
                                        # 调用算法服务
                                        result = call_algorithm_service(
                                            service, 
                                            image_bytes,
                                            additional_params={
                                                'region_id': region.id,
                                                'region_name': region.region_name,
                                                'points': points
                                            }
                                        )
                                        
                                        # 检查检测结果并发送告警
                                        if result and should_trigger_alarm(result, service.threshold):
                                            send_alert_for_detection(task, region, result, frame, device)
                                except Exception as e:
                                    logger.error(f"调用区域算法服务失败: region_id={region.id}, service_id={service.id}, error={str(e)}")
                        except Exception as e:
                            logger.error(f"处理检测区域失败: region_id={region.id}, error={str(e)}")
                    else:
                        # 使用区域的旧配置（兼容）
                        if region.algorithm_model_id:
                            # TODO: 调用旧的算法服务
                            pass
            else:
                # 全屏检测（使用任务级别的模型服务配置）
                from app.services.algorithm_service import get_task_algorithm_services, call_algorithm_service
                task_services = get_task_algorithm_services(task.id)
                
                if task_services:
                    # 调用任务的每个模型服务
                    for service in task_services:
                        if not service.is_enabled:
                            continue
                        
                        try:
                            # 编码图片
                            success, encoded_image = cv2.imencode('.jpg', frame)
                            if success:
                                image_bytes = encoded_image.tobytes()
                                
                                # 调用算法服务
                                result = call_algorithm_service(service, image_bytes)
                                
                                # 检查检测结果并发送告警
                                if result and should_trigger_alarm(result, service.threshold):
                                    send_alert_for_detection(task, None, result, frame, device)
                        except Exception as e:
                            logger.error(f"调用任务算法服务失败: task_id={task.id}, service_id={service.id}, error={str(e)}")
                else:
                    # 使用任务的旧配置（兼容）
                    if task.algorithm_model_id:
                        # TODO: 调用旧的算法服务
                        pass
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if task.auto_filename:
            if task.custom_filename_prefix:
                filename = f"{task.custom_filename_prefix}_{timestamp}.jpg"
            else:
                filename = f"{device.id}_{timestamp}.jpg"
        else:
            filename = f"{task.task_code}_{timestamp}.jpg"
        
        object_name = f"{device_folder}{filename}"
        
        # 编码图像
        success, encoded_image = cv2.imencode('.jpg', frame)
        if not success:
            logger.error(f"图像编码失败: {device.id}")
            return False
        
        image_bytes = encoded_image.tobytes()
        
        # 上传到MinIO
        minio_client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(image_bytes),
            len(image_bytes),
            content_type="image/jpeg"
        )
        
        logger.info(f"抓拍成功: {bucket_name}/{object_name}")
        return True
        
    except Exception as e:
        logger.error(f"抓拍操作失败: {str(e)}", exc_info=True)
        return False


def start_task(task_id):
    """启动任务"""
    try:
        task = SnapTask.query.get_or_404(task_id)
        task.is_enabled = True
        task.run_status = 'running'
        db.session.commit()
        add_task_to_scheduler(task_id)
        logger.info(f"任务已启动: ID={task_id}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"启动任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"启动任务失败: {str(e)}")


def stop_task(task_id):
    """停止任务"""
    try:
        task = SnapTask.query.get_or_404(task_id)
        task.is_enabled = False
        task.run_status = 'stopped'
        db.session.commit()
        remove_task_from_scheduler(task_id)
        logger.info(f"任务已停止: ID={task_id}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"停止任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"停止任务失败: {str(e)}")


def restart_task(task_id):
    """重启任务"""
    try:
        task = SnapTask.query.get_or_404(task_id)
        task.run_status = 'restarting'
        db.session.commit()
        
        # 先停止
        remove_task_from_scheduler(task_id)
        
        # 再启动
        if task.is_enabled:
            add_task_to_scheduler(task_id)
            task.run_status = 'running'
        else:
            task.run_status = 'stopped'
        
        db.session.commit()
        logger.info(f"任务已重启: ID={task_id}")
        return task
    except Exception as e:
        db.session.rollback()
        logger.error(f"重启任务失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"重启任务失败: {str(e)}")


def get_task_logs(task_id, page_no=1, page_size=50, level=None):
    """获取任务日志
    
    Args:
        task_id: 任务ID
        page_no: 页码
        page_size: 每页数量
        level: 日志级别过滤（可选）
    
    Returns:
        dict: 包含logs和total的字典
    """
    try:
        import os
        import glob
        from datetime import datetime
        
        # 日志文件路径（根据任务ID）
        log_dir = os.path.join('logs', str(task_id))
        if not os.path.exists(log_dir):
            return {'logs': [], 'total': 0}
        
        # 查找所有日志文件
        log_files = glob.glob(os.path.join(log_dir, '*.log'))
        log_files.sort(key=os.path.getmtime, reverse=True)  # 按修改时间倒序
        
        # 读取日志
        all_logs = []
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 简单的日志解析（格式：时间戳 - 级别 - 消息）
                        parts = line.split(' - ', 2)
                        if len(parts) >= 3:
                            log_time = parts[0]
                            log_level = parts[1]
                            log_message = parts[2]
                            
                            # 级别过滤
                            if level and log_level.lower() != level.lower():
                                continue
                            
                            all_logs.append({
                                'time': log_time,
                                'level': log_level,
                                'message': log_message,
                                'file': os.path.basename(log_file)
                            })
            except Exception as e:
                logger.warning(f"读取日志文件失败: {log_file}, error={str(e)}")
        
        # 分页
        total = len(all_logs)
        offset = (page_no - 1) * page_size
        logs = all_logs[offset:offset + page_size]
        
        return {
            'logs': logs,
            'total': total,
            'page_no': page_no,
            'page_size': page_size
        }
    except Exception as e:
        logger.error(f"获取任务日志失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取任务日志失败: {str(e)}")


def init_all_tasks():
    """初始化所有启用的任务到调度器（应用启动时调用）"""
    try:
        tasks = SnapTask.query.filter_by(is_enabled=True).all()
        for task in tasks:
            add_task_to_scheduler(task.id)
        logger.info(f"已初始化 {len(tasks)} 个抓拍任务到调度器")
    except Exception as e:
        logger.error(f"初始化任务失败: {str(e)}", exc_info=True)

