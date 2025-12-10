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
import signal
import time
from typing import Dict, Optional, Tuple
from datetime import datetime

from models import db, AlgorithmTask
from .algorithm_task_daemon import AlgorithmTaskDaemon
from .snap_space_service import get_snap_space_by_device_id, create_snap_space_for_device

logger = logging.getLogger(__name__)

# 存储已启动的守护进程对象（参考 AI 模块的 deploy_service.py）
_running_daemons: Dict[int, AlgorithmTaskDaemon] = {}
_daemons_lock = threading.Lock()
# 启动锁：防止并发启动同一个任务
_starting_tasks: Dict[int, threading.Lock] = {}
_starting_lock = threading.Lock()


def get_service_script_path(service_type: str) -> str:
    """获取服务脚本路径
    
    Args:
        service_type: 服务类型 ('realtime' 实时算法服务, 'snap' 抓拍算法服务)
    
    Returns:
        str: 服务脚本的绝对路径
    """
    # 当前文件: VIDEO/app/services/algorithm_task_launcher_service.py
    # 需要得到: VIDEO/ 目录
    # 使用3个os.path.dirname: services -> app -> VIDEO
    video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    service_paths = {
        'realtime': os.path.join(video_root, 'services', 'realtime_algorithm_service', 'run_deploy.py'),
        'snap': os.path.join(video_root, 'services', 'snapshot_algorithm_service', 'run_deploy.py')
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


def cleanup_orphaned_processes(task_id: int):
    """清理遗留的进程（包括run_deploy.py和FFmpeg进程）
    
    Args:
        task_id: 算法任务ID
    """
    try:
        import psutil
        import os
        
        # 获取当前守护进程管理的进程PID（如果存在）
        protected_pids = set()
        with _daemons_lock:
            if task_id in _running_daemons:
                daemon = _running_daemons[task_id]
                # 保护正在运行的守护进程管理的进程（即使_process为None，也可能正在启动中）
                if daemon._running:
                    if daemon._process:
                        try:
                            # 检查进程是否真的在运行
                            if daemon._process.poll() is None:
                                # 守护进程管理的进程还在运行，保护它及其子进程
                                protected_pids.add(daemon._process.pid)
                                try:
                                    # 获取所有子进程的PID
                                    parent_proc = psutil.Process(daemon._process.pid)
                                    for child in parent_proc.children(recursive=True):
                                        protected_pids.add(child.pid)
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass
                        except:
                            # poll失败，进程可能已经不存在，但不影响保护逻辑
                            pass
                    else:
                        # 进程为None但守护进程还在运行，说明可能正在启动中
                        # 为了安全起见，不清理任何进程（避免误杀正在启动的进程）
                        logger.debug(f"守护进程正在启动中（task_id={task_id}），跳过清理遗留进程")
                        return
        
        # 查找所有相关的进程
        target_script = 'run_deploy.py'
        target_env = f'TASK_ID={task_id}'
        
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'environ']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue
                
                # 检查是否是run_deploy.py进程且环境变量匹配
                # 更精确的检查：脚本路径必须以run_deploy.py结尾
                is_target = False
                cmdline_str = ' '.join(cmdline)
                
                # 检查脚本路径是否真的以run_deploy.py结尾（更精确的匹配）
                script_path_match = False
                for arg in cmdline:
                    arg_str = str(arg)
                    # 检查是否是脚本路径（以run_deploy.py结尾）
                    if arg_str.endswith(target_script) or arg_str.endswith(target_script.replace('.py', '')):
                        script_path_match = True
                        break
                
                if script_path_match:
                    # 优先检查环境变量（最可靠）
                    try:
                        environ = proc.info.get('environ', {})
                        if environ:
                            proc_task_id = environ.get('TASK_ID')
                            if proc_task_id == str(task_id):
                                is_target = True
                            else:
                                # 环境变量不匹配，跳过
                                continue
                        else:
                            # 无法获取环境变量，尝试从命令行参数中提取（作为备选方案）
                            # 但只检查明确的环境变量格式，避免误判
                            found_task_id = None
                            for arg in cmdline:
                                arg_str = str(arg)
                                # 检查是否是环境变量格式：TASK_ID=xxx
                                if 'TASK_ID=' in arg_str:
                                    try:
                                        found_task_id = arg_str.split('TASK_ID=')[1].split()[0].strip()
                                        break
                                    except:
                                        pass
                            
                            if found_task_id == str(task_id):
                                is_target = True
                            else:
                                # 任务ID不匹配，跳过
                                continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # 如果无法获取环境变量，且无法从命令行提取，跳过（避免误杀）
                        logger.debug(f"无法获取进程 {proc.info['pid']} 的环境变量，跳过检查")
                        continue
                
                # 检查是否是FFmpeg进程（可能是run_deploy.py的子进程）
                # 重要：只清理算法任务相关的FFmpeg进程，不影响RTSP推流的FFmpeg进程
                is_ffmpeg = False
                if 'ffmpeg' in cmdline_str.lower():
                    try:
                        # 检查父进程是否是我们的run_deploy.py进程
                        parent = proc.parent()
                        if parent:
                            try:
                                parent_cmdline = parent.cmdline()
                                if not parent_cmdline:
                                    # 无法获取父进程命令行，跳过（避免误杀）
                                    continue
                                
                                # 检查父进程脚本路径
                                parent_script_match = False
                                for arg in parent_cmdline:
                                    if str(arg).endswith(target_script):
                                        parent_script_match = True
                                        break
                                
                                # 只有父进程是run_deploy.py时才继续检查
                                if parent_script_match:
                                    try:
                                        parent_environ = parent.environ()
                                        # 必须同时满足：父进程是run_deploy.py 且 TASK_ID匹配
                                        if parent_environ and parent_environ.get('TASK_ID') == str(task_id):
                                            is_ffmpeg = True
                                        else:
                                            # 父进程是run_deploy.py但TASK_ID不匹配，跳过（避免误杀）
                                            continue
                                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                                        # 无法获取父进程环境变量，跳过（避免误杀）
                                        continue
                                else:
                                    # 父进程不是run_deploy.py，这是RTSP推流的FFmpeg进程，跳过
                                    continue
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                # 无法获取父进程信息，跳过（避免误杀）
                                continue
                        else:
                            # 没有父进程，跳过（避免误杀）
                            continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # 无法获取父进程，跳过（避免误杀）
                        continue
                
                if is_target or is_ffmpeg:
                    # 检查是否是受保护的进程（当前守护进程管理的进程）
                    proc_pid = proc.info['pid']
                    if proc_pid in protected_pids:
                        logger.debug(f"跳过受保护的进程: PID={proc_pid} (task_id={task_id})")
                        continue
                    
                    try:
                        logger.warning(f"🔍 发现遗留进程: PID={proc_pid}, CMD={' '.join(cmdline[:3])}...")
                        # 先尝试优雅终止
                        proc.terminate()
                        try:
                            proc.wait(timeout=3)
                            logger.info(f"✅ 遗留进程 {proc_pid} 已优雅终止")
                        except psutil.TimeoutExpired:
                            # 强制终止
                            proc.kill()
                            proc.wait(timeout=1)
                            logger.warning(f"⚠️ 遗留进程 {proc_pid} 已强制终止")
                        killed_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        # 进程已经不存在或无权访问
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # 进程已经不存在或无权访问，继续下一个
                continue
        
        if killed_count > 0:
            logger.info(f"🧹 清理了 {killed_count} 个遗留进程 (task_id={task_id})")
        else:
            logger.debug(f"未发现遗留进程 (task_id={task_id})")
            
    except ImportError:
        # psutil未安装，使用ps命令（Linux）
        try:
            # 获取当前守护进程管理的进程PID（如果存在）
            protected_pids = set()
            with _daemons_lock:
                if task_id in _running_daemons:
                    daemon = _running_daemons[task_id]
                    # 保护正在运行的守护进程管理的进程
                    if daemon._running:
                        if daemon._process:
                            try:
                                if daemon._process.poll() is None:
                                    protected_pids.add(daemon._process.pid)
                            except:
                                pass
                        else:
                            # 进程为None但守护进程还在运行，说明可能正在启动中
                            # 为了安全起见，不清理任何进程
                            logger.debug(f"守护进程正在启动中（task_id={task_id}），跳过清理遗留进程")
                            return
            
            # 查找run_deploy.py进程
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                pids_to_kill = []
                for line in lines:
                    if 'run_deploy.py' in line and f'TASK_ID={task_id}' in line:
                        parts = line.split()
                        if len(parts) > 1:
                            try:
                                pid = int(parts[1])
                                # 检查是否是受保护的进程
                                if pid not in protected_pids:
                                    pids_to_kill.append(pid)
                            except ValueError:
                                pass
                
                # 终止找到的进程及其子进程
                for pid in pids_to_kill:
                    try:
                        # 终止进程组
                        os.killpg(os.getpgid(pid), signal.SIGTERM)
                        time.sleep(1)
                        # 如果还在运行，强制终止
                        try:
                            os.killpg(os.getpgid(pid), signal.SIGKILL)
                        except:
                            pass
                        logger.info(f"🧹 清理遗留进程: PID={pid} (task_id={task_id})")
                    except (ProcessLookupError, OSError):
                        pass
        except Exception as e:
            logger.warning(f"清理遗留进程失败: {str(e)}")
    except Exception as e:
        logger.warning(f"清理遗留进程时出错: {str(e)}")


def stop_service_process(task_id: int, service_type: str):
    """停止服务进程
    
    Args:
        task_id: 算法任务ID
        service_type: 服务类型 ('realtime' 统一服务)
    """
    # 等待启动完成（如果正在启动）
    with _starting_lock:
        if task_id in _starting_tasks:
            task_start_lock = _starting_tasks[task_id]
            # 尝试获取锁（如果正在启动，会等待）
            if task_start_lock.acquire(blocking=True, timeout=5):
                task_start_lock.release()
    
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
    
    # 清理可能遗留的进程（包括FFmpeg子进程）
    cleanup_orphaned_processes(task_id)
    
    # 清理启动锁
    with _starting_lock:
        if task_id in _starting_tasks:
            del _starting_tasks[task_id]


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
    # 获取或创建任务专用的启动锁（防止并发启动）
    with _starting_lock:
        if task_id not in _starting_tasks:
            _starting_tasks[task_id] = threading.Lock()
        task_start_lock = _starting_tasks[task_id]
    
    # 使用任务专用的启动锁，防止并发启动
    if not task_start_lock.acquire(blocking=False):
        logger.warning(f"任务 {task_id} 正在启动中，跳过重复启动")
        return (True, "任务正在启动中", True)
    
    try:
        # 实时算法任务和抓拍算法任务都需要启动服务进程
        if task.task_type in ['realtime', 'snap']:
            # 检查是否已经有运行的守护进程（在清理之前检查，避免误杀正在运行的进程）
            should_cleanup = True
            with _daemons_lock:
                if task_id in _running_daemons:
                    daemon = _running_daemons[task_id]
                    if daemon._running and daemon._process and daemon._process.poll() is None:
                        # 守护进程正在运行，不清理遗留进程（避免误杀）
                        should_cleanup = False
                        logger.debug(f'守护进程正在运行，跳过清理遗留进程 (task_id={task_id})')
            
            # 检查是否已经有运行的守护进程（在清理之前检查，避免误杀正在运行的进程）
            existing_daemon = None
            with _daemons_lock:
                if task_id in _running_daemons:
                    existing_daemon = _running_daemons[task_id]
                    if existing_daemon._running and existing_daemon._process and existing_daemon._process.poll() is None:
                        # 守护进程正在运行，检查是否真的是我们的进程
                        try:
                            import psutil
                            proc = psutil.Process(existing_daemon._process.pid)
                            cmdline = proc.cmdline()
                            
                            # 更精确的检查：脚本路径必须以run_deploy.py结尾
                            script_path_match = False
                            for arg in cmdline:
                                if str(arg).endswith('run_deploy.py'):
                                    script_path_match = True
                                    break
                            
                            if script_path_match:
                                # 检查环境变量
                                try:
                                    environ = proc.environ()
                                    if environ.get('TASK_ID') == str(task_id):
                                        logger.warning(f"任务 {task_id} 的服务已在运行，跳过启动")
                                        return (True, "任务运行中", True)
                                except:
                                    # 如果无法获取环境变量，假设是同一个进程（因为脚本路径匹配）
                                    logger.warning(f"任务 {task_id} 的服务已在运行（无法验证环境变量），跳过启动")
                                    return (True, "任务运行中", True)
                        except (ImportError, psutil.NoSuchProcess, psutil.AccessDenied):
                            # psutil未安装或进程不存在，使用poll结果
                            logger.warning(f"任务 {task_id} 的服务已在运行，跳过启动")
                            return (True, "任务运行中", True)
            
            # 只有在没有运行的守护进程时才清理遗留进程
            if should_cleanup:
                logger.debug(f'清理任务 {task_id} 的遗留进程...')
                cleanup_orphaned_processes(task_id)
                logger.debug(f'清理任务 {task_id} 的遗留进程完成')
            
            # 如果存在旧的守护进程但进程已停止，清理它
            if existing_daemon:
                with _daemons_lock:
                    if task_id in _running_daemons:
                        daemon = _running_daemons[task_id]
                        if not daemon._running or (daemon._process and daemon._process.poll() is not None):
                            logger.info('守护进程已停止或进程不存在，清理旧守护进程...')
                            try:
                                daemon.stop()
                            except:
                                pass
                            del _running_daemons[task_id]
                        elif daemon._process is None:
                            # 进程为None且守护进程已停止，清理
                            logger.info('守护进程启动失败，清理并重新启动...')
                            try:
                                daemon.stop()
                            except:
                                pass
                            del _running_daemons[task_id]
            
            # 获取日志路径（与 AI 模块保持一致）
            log_path = _get_log_path(task_id)
            
            # 启动守护进程（传入所有必要参数，不需要数据库连接）
            logger.info(f'启动守护进程，任务ID: {task_id}, 任务类型: {task.task_type}')
            daemon = None
            with _daemons_lock:
                daemon = AlgorithmTaskDaemon(
                    task_id=task_id,
                    log_path=log_path,
                    task_type=task.task_type
                )
                _running_daemons[task_id] = daemon
            
            # 等待守护进程启动并获取进程PID（最多等待2秒）
            import time
            process_pid = None
            for _ in range(20):  # 等待最多2秒（20 * 0.1秒）
                time.sleep(0.1)
                if daemon._process is not None:
                    try:
                        if daemon._process.poll() is None:
                            process_pid = daemon._process.pid
                            break
                    except:
                        pass
                if not daemon._running:
                    # 守护进程已停止，退出等待
                    break
            
            # 如果进程已启动，立即清理一次遗留进程（这次会保护新进程）
            if process_pid:
                logger.debug(f'新进程已启动 (PID: {process_pid})，再次清理遗留进程（会保护新进程）...')
                cleanup_orphaned_processes(task_id)
            
            task_type_name = "实时算法" if task.task_type == 'realtime' else "抓拍算法"
            logger.info(f"✅ 任务 {task_id} 的{task_type_name}服务启动成功（守护进程已启动）")
            return (True, "启动成功", False)
        else:
            # 未知的任务类型
            logger.warning(f"未知的任务类型: {task.task_type}，跳过启动")
            return (False, f"未知的任务类型: {task.task_type}", False)
            
    except Exception as e:
        logger.error(f"❌ 启动任务 {task_id} 的服务失败: {str(e)}", exc_info=True)
        return (False, f"启动失败: {str(e)}", False)
    finally:
        # 释放启动锁
        task_start_lock.release()
        # 如果任务已停止，清理启动锁
        with _starting_lock:
            if task_id in _starting_tasks:
                # 检查任务是否还在运行
                with _daemons_lock:
                    if task_id not in _running_daemons:
                        # 任务已停止，清理启动锁
                        del _starting_tasks[task_id]


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
                elif task.task_type == 'snap':
                    # 抓拍算法任务需要模型ID列表
                    if not task.model_ids:
                        logger.warning(f"任务 {task.id} ({task.task_name}) 缺少模型ID配置，跳过")
                        continue
                    
                    # 确保任务关联的所有设备都有抓拍空间（如果没有则自动创建）
                    if not task.devices or len(task.devices) == 0:
                        logger.warning(f"任务 {task.id} ({task.task_name}) 没有关联的设备，跳过")
                        continue
                    
                    # 为每个关联的设备确保有抓拍空间
                    for device in task.devices:
                        try:
                            # 检查设备是否已有抓拍空间
                            snap_space = get_snap_space_by_device_id(device.id)
                            if not snap_space:
                                # 如果没有，自动创建
                                logger.info(f"为设备 {device.id} ({device.name or device.id}) 自动创建抓拍空间")
                                create_snap_space_for_device(device.id, device.name)
                            else:
                                logger.debug(f"设备 {device.id} 已有抓拍空间: {snap_space.space_name}")
                        except Exception as e:
                            logger.error(f"为设备 {device.id} 创建/获取抓拍空间失败: {str(e)}", exc_info=True)
                            # 继续处理其他设备，不中断整个任务
                else:
                    logger.warning(f"任务 {task.id} ({task.task_name}) 未知的任务类型: {task.task_type}，跳过")
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
            # 如果_process为None，说明守护进程可能正在启动中，不清理
            if not daemon._running:
                # 守护进程已停止
                logger.info(f"检测到守护进程已停止: task_id={task_id}")
                tasks_to_remove.append(task_id)
            elif daemon._process and daemon._process.poll() is not None:
                # 进程已退出
                logger.info(f"检测到守护进程的子进程已退出: task_id={task_id}")
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

