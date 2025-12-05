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
from typing import Dict, Optional, Tuple
from datetime import datetime

from models import db, AlgorithmTask
from .algorithm_task_daemon import AlgorithmTaskDaemon

logger = logging.getLogger(__name__)

# 存储已启动的守护进程对象（参考 AI 模块的 deploy_service.py）
_running_daemons: Dict[int, AlgorithmTaskDaemon] = {}
_daemons_lock = threading.Lock()


def get_service_script_path(service_type: str) -> str:
    """获取服务脚本路径
    
    Args:
        service_type: 服务类型 ('realtime' 统一服务)
    
    Returns:
        str: 服务脚本的绝对路径
    """
    # 当前文件: VIDEO/app/services/algorithm_task_launcher_service.py
    # 需要得到: VIDEO/ 目录
    # 使用3个os.path.dirname: services -> app -> VIDEO
    video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    service_paths = {
        'realtime': os.path.join(video_root, 'services', 'realtime_algorithm_service', 'run_deploy.py')
    }
    
    return service_paths.get(service_type)


def _get_log_path(task_id: int) -> str:
    """获取日志文件路径（按任务ID）
    
    Args:
        task_id: 任务ID
    
    Returns:
        str: 日志目录路径
    """
    video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_base_dir = os.path.join(video_root, 'logs')
    log_dir = os.path.join(log_base_dir, f'task_{task_id}')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def stop_service_process(task_id: int, service_type: str):
    """停止服务进程
    
    Args:
        task_id: 算法任务ID
        service_type: 服务类型 ('realtime' 统一服务)
    """
    with _daemons_lock:
        if task_id in _running_daemons:
            daemon = _running_daemons[task_id]
            try:
                daemon.stop()
                logger.info(f"✅ 停止{service_type}服务成功: task_id={task_id}")
            except Exception as e:
                logger.error(f"❌ 停止{service_type}服务失败: task_id={task_id}, error={str(e)}")
            finally:
                del _running_daemons[task_id]


def stop_all_task_services(task_id: int):
    """停止任务的所有服务
    
    Args:
        task_id: 算法任务ID
    """
    stop_service_process(task_id, 'realtime')


def restart_task_services(task_id: int) -> bool:
    """重启任务的所有服务（使用守护进程的 restart 方法）
    
    Args:
        task_id: 算法任务ID
    
    Returns:
        bool: 是否成功重启服务
    """
    with _daemons_lock:
        if task_id in _running_daemons:
            daemon = _running_daemons[task_id]
            try:
                daemon.restart()
                logger.info(f"✅ 重启任务 {task_id} 的服务成功")
                return True
            except Exception as e:
                logger.error(f"❌ 重启任务 {task_id} 的服务失败: {str(e)}")
                return False
        else:
            logger.warning(f"任务 {task_id} 的服务未运行，无法重启")
            return False


def start_task_services(task_id: int, task: AlgorithmTask) -> Tuple[bool, str, bool]:
    """启动算法任务的所有服务（使用守护进程管理）
    
    Args:
        task_id: 算法任务ID
        task: AlgorithmTask对象
    
    Returns:
        tuple[bool, str, bool]: (是否成功, 消息, 是否已运行)
            - 是否成功: True表示成功或已运行，False表示失败
            - 消息: 描述性消息
            - 是否已运行: True表示服务已在运行，False表示新启动
    """
    try:
        # 实时算法任务：启动统一的实时算法任务服务
        # 抓拍算法任务：不需要启动服务（使用定时任务）
        if task.task_type == 'realtime':
            # 检查是否已经有运行的守护进程
            with _daemons_lock:
                if task_id in _running_daemons:
                    daemon = _running_daemons[task_id]
                    # 检查守护进程是否还在运行（通过检查进程状态）
                    if daemon._running and daemon._process and daemon._process.poll() is None:
                        logger.warning(f"任务 {task_id} 的服务已在运行，跳过启动")
                        return (True, "任务运行中", True)
                    else:
                        logger.info('守护进程已停止，重新启动...')
                        # 清理旧的守护进程
                        try:
                            daemon.stop()
                        except:
                            pass
                        del _running_daemons[task_id]
            
            # 获取日志路径（与 AI 模块保持一致）
            log_path = _get_log_path(task_id)
            
            # 启动守护进程（传入所有必要参数，不需要数据库连接）
            logger.info(f'启动守护进程，任务ID: {task_id}')
            with _daemons_lock:
                _running_daemons[task_id] = AlgorithmTaskDaemon(
                    task_id=task_id,
                    log_path=log_path
                )
            
            logger.info(f"✅ 任务 {task_id} 的实时算法服务启动成功（守护进程已启动）")
            return (True, "启动成功", False)
        else:  # snap
            # 抓拍算法任务不需要启动服务进程
            logger.info(f"抓拍算法任务 {task_id} 不需要启动服务进程")
            return (True, "启动成功", False)
            
    except Exception as e:
        logger.error(f"❌ 启动任务 {task_id} 的服务失败: {str(e)}", exc_info=True)
        return (False, f"启动失败: {str(e)}", False)


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
                # 检查任务是否有必需的配置
                if task.task_type == 'realtime':
                    # 实时算法任务需要模型ID列表
                    if not task.model_ids:
                        logger.warning(f"任务 {task.id} ({task.task_name}) 缺少模型ID配置，跳过")
                        continue
                else:  # snap
                    # 抓拍算法任务不需要启动服务进程
                    logger.info(f"抓拍算法任务 {task.id} ({task.task_name}) 不需要启动服务进程")
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
    """清理已停止的守护进程（守护进程会自动管理，此函数主要用于检查）"""
    with _daemons_lock:
        tasks_to_remove = []
        for task_id, daemon in _running_daemons.items():
            # 检查守护进程是否还在运行
            if not daemon._running or (daemon._process and daemon._process.poll() is not None):
                # 守护进程已停止
                logger.info(f"检测到守护进程已停止: task_id={task_id}")
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            try:
                _running_daemons[task_id].stop()
            except:
                pass
            del _running_daemons[task_id]


def stop_all_daemons():
    """停止所有守护进程（用于VIDEO服务关闭时清理）"""
    with _daemons_lock:
        if not _running_daemons:
            logger.info("没有运行的守护进程，无需停止")
            return
        
        logger.info(f"正在停止 {len(_running_daemons)} 个守护进程...")
        task_ids = list(_running_daemons.keys())
        
        for task_id in task_ids:
            try:
                daemon = _running_daemons[task_id]
                daemon.stop()
                logger.info(f"✅ 停止守护进程成功: task_id={task_id}")
            except Exception as e:
                logger.error(f"❌ 停止守护进程失败: task_id={task_id}, error={str(e)}")
            finally:
                if task_id in _running_daemons:
                    del _running_daemons[task_id]
        
        logger.info(f"✅ 所有守护进程已停止")

