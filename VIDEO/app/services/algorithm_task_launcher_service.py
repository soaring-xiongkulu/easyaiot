"""
算法任务服务启动器
用于自动启动算法任务相关的服务（抽帧器、推送器、排序器）

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import subprocess
import logging
import threading
from typing import Dict, Optional
from datetime import datetime

from models import db, AlgorithmTask, FrameExtractor, Sorter, Pusher

logger = logging.getLogger(__name__)

# 存储已启动的进程
_running_processes: Dict[int, Dict[str, subprocess.Popen]] = {}
_processes_lock = threading.Lock()


def get_service_script_path(service_type: str) -> str:
    """获取服务脚本路径
    
    Args:
        service_type: 服务类型 ('extractor', 'pusher', 'sorter')
    
    Returns:
        str: 服务脚本的绝对路径
    """
    video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    service_paths = {
        'extractor': os.path.join(video_root, 'services', 'frame_extractor_service', 'run_deploy.py'),
        'pusher': os.path.join(video_root, 'services', 'pusher_service', 'run_deploy.py'),
        'sorter': os.path.join(video_root, 'services', 'sorter_service', 'run_deploy.py')
    }
    
    return service_paths.get(service_type)


def start_service_process(task_id: int, service_type: str, service_id: int, 
                         python_executable: Optional[str] = None) -> Optional[subprocess.Popen]:
    """启动服务进程
    
    Args:
        task_id: 算法任务ID
        service_type: 服务类型 ('extractor', 'pusher', 'sorter')
        service_id: 服务ID（extractor_id, pusher_id, sorter_id）
        python_executable: Python可执行文件路径，默认使用sys.executable
    
    Returns:
        subprocess.Popen: 启动的进程对象，失败返回None
    """
    try:
        script_path = get_service_script_path(service_type)
        if not script_path or not os.path.exists(script_path):
            logger.error(f"服务脚本不存在: {script_path}")
            return None
        
        # 使用当前Python解释器
        python_cmd = python_executable or sys.executable
        
        # 构建环境变量
        env = os.environ.copy()
        env['TASK_ID'] = str(task_id)
        
        # 根据服务类型设置不同的环境变量
        if service_type == 'extractor':
            env['EXTRACTOR_ID'] = str(service_id)
            # 为每个任务分配不同的端口，避免冲突
            base_port = 8001
            env['PORT'] = str(base_port + task_id * 10)
        elif service_type == 'pusher':
            env['PUSHER_ID'] = str(service_id)
            base_port = 8003
            env['PORT'] = str(base_port + task_id * 10)
        elif service_type == 'sorter':
            env['SORTER_ID'] = str(service_id)
            base_port = 8002
            env['PORT'] = str(base_port + task_id * 10)
        
        # 确保关键环境变量被传递
        # DATABASE_URL 应该从主程序环境变量继承
        if 'DATABASE_URL' not in env:
            logger.warning("DATABASE_URL环境变量未设置，服务可能无法连接数据库")
        
        # 设置VIDEO服务API地址（用于心跳上报）
        video_service_port = os.getenv('FLASK_RUN_PORT', '6000')
        env['VIDEO_SERVICE_PORT'] = video_service_port
        
        # 启动进程
        process = subprocess.Popen(
            [python_cmd, script_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(script_path)
        )
        
        logger.info(f"✅ 启动{service_type}服务成功: task_id={task_id}, service_id={service_id}, pid={process.pid}")
        return process
        
    except Exception as e:
        logger.error(f"❌ 启动{service_type}服务失败: task_id={task_id}, service_id={service_id}, error={str(e)}", exc_info=True)
        return None


def stop_service_process(task_id: int, service_type: str):
    """停止服务进程
    
    Args:
        task_id: 算法任务ID
        service_type: 服务类型 ('extractor', 'pusher', 'sorter')
    """
    with _processes_lock:
        if task_id in _running_processes:
            if service_type in _running_processes[task_id]:
                process = _running_processes[task_id][service_type]
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    logger.info(f"✅ 停止{service_type}服务成功: task_id={task_id}, pid={process.pid}")
                except subprocess.TimeoutExpired:
                    process.kill()
                    logger.warning(f"⚠️  强制停止{service_type}服务: task_id={task_id}, pid={process.pid}")
                except Exception as e:
                    logger.error(f"❌ 停止{service_type}服务失败: task_id={task_id}, error={str(e)}")
                finally:
                    del _running_processes[task_id][service_type]
                    if not _running_processes[task_id]:
                        del _running_processes[task_id]


def stop_all_task_services(task_id: int):
    """停止任务的所有服务
    
    Args:
        task_id: 算法任务ID
    """
    stop_service_process(task_id, 'extractor')
    stop_service_process(task_id, 'pusher')
    stop_service_process(task_id, 'sorter')


def start_task_services(task_id: int, task: AlgorithmTask) -> bool:
    """启动算法任务的所有服务
    
    Args:
        task_id: 算法任务ID
        task: AlgorithmTask对象
    
    Returns:
        bool: 是否成功启动所有必需的服务
    """
    try:
        success_count = 0
        required_services = []
        
        # 实时算法任务需要：抽帧器、推送器、排序器
        # 抓拍算法任务需要：推送器（不需要抽帧器和排序器）
        if task.task_type == 'realtime':
            if task.extractor_id:
                required_services.append(('extractor', task.extractor_id))
            if task.pusher_id:
                required_services.append(('pusher', task.pusher_id))
            if task.sorter_id:
                required_services.append(('sorter', task.sorter_id))
        else:  # snap
            if task.pusher_id:
                required_services.append(('pusher', task.pusher_id))
        
        # 检查是否已经有运行的服务
        with _processes_lock:
            if task_id in _running_processes:
                logger.warning(f"任务 {task_id} 的服务已在运行，跳过启动")
                return True
        
        # 启动所有必需的服务
        started_processes = {}
        for service_type, service_id in required_services:
            process = start_service_process(task_id, service_type, service_id)
            if process:
                started_processes[service_type] = process
                success_count += 1
            else:
                logger.error(f"启动{service_type}服务失败: task_id={task_id}, service_id={service_id}")
        
        # 保存进程引用
        if started_processes:
            with _processes_lock:
                _running_processes[task_id] = started_processes
        
        # 检查是否所有必需的服务都启动成功
        if success_count == len(required_services):
            logger.info(f"✅ 任务 {task_id} 的所有服务启动成功: {success_count}/{len(required_services)}")
            return True
        else:
            logger.warning(f"⚠️  任务 {task_id} 部分服务启动失败: {success_count}/{len(required_services)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 启动任务 {task_id} 的服务失败: {str(e)}", exc_info=True)
        return False


def auto_start_all_tasks(app=None):
    """自动启动所有启用的算法任务的服务
    
    Args:
        app: Flask应用实例（用于应用上下文）
    """
    try:
        if app:
            with app.app_context():
                _auto_start_all_tasks_internal()
        else:
            _auto_start_all_tasks_internal()
    except Exception as e:
        logger.error(f"❌ 自动启动算法任务服务失败: {str(e)}", exc_info=True)


def _auto_start_all_tasks_internal():
    """内部函数：自动启动所有启用的算法任务的服务"""
    try:
        # 查询所有启用的算法任务
        tasks = AlgorithmTask.query.filter_by(is_enabled=True).all()
        
        if not tasks:
            logger.info("没有启用的算法任务，跳过服务启动")
            return
        
        logger.info(f"发现 {len(tasks)} 个启用的算法任务，开始启动服务...")
        
        success_count = 0
        for task in tasks:
            try:
                # 检查任务是否有必需的服务配置
                if task.task_type == 'realtime':
                    # 实时算法任务需要抽帧器和推送器
                    if not task.extractor_id:
                        logger.warning(f"任务 {task.id} ({task.task_name}) 缺少抽帧器配置，跳过")
                        continue
                    if not task.pusher_id:
                        logger.warning(f"任务 {task.id} ({task.task_name}) 缺少推送器配置，跳过")
                        continue
                else:  # snap
                    # 抓拍算法任务只需要推送器
                    if not task.pusher_id:
                        logger.warning(f"任务 {task.id} ({task.task_name}) 缺少推送器配置，跳过")
                        continue
                
                # 启动任务的服务
                if start_task_services(task.id, task):
                    success_count += 1
                    logger.info(f"✅ 任务 {task.id} ({task.task_name}) 的服务启动成功")
                else:
                    logger.error(f"❌ 任务 {task.id} ({task.task_name}) 的服务启动失败")
                    
            except Exception as e:
                logger.error(f"❌ 启动任务 {task.id} 的服务时出错: {str(e)}", exc_info=True)
        
        logger.info(f"✅ 自动启动完成: {success_count}/{len(tasks)} 个任务的服务启动成功")
        
    except Exception as e:
        logger.error(f"❌ 自动启动算法任务服务失败: {str(e)}", exc_info=True)


def cleanup_stopped_processes():
    """清理已停止的进程"""
    with _processes_lock:
        tasks_to_remove = []
        for task_id, processes in _running_processes.items():
            services_to_remove = []
            for service_type, process in processes.items():
                if process.poll() is not None:
                    # 进程已停止
                    logger.info(f"检测到{service_type}服务已停止: task_id={task_id}, pid={process.pid}")
                    services_to_remove.append(service_type)
            
            for service_type in services_to_remove:
                del processes[service_type]
            
            if not processes:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del _running_processes[task_id]

