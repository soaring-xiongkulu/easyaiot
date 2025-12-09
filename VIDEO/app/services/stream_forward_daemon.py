"""
推流转发任务守护进程
用于管理推流转发任务服务进程，支持自动重启

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import subprocess as sp
import os
import sys
import threading
import time
import signal
from datetime import datetime


class StreamForwardDaemon:
    """推流转发任务守护进程，管理推流转发任务服务进程，支持自动重启"""

    def __init__(self, task_id: int, log_path: str):
        """
        初始化守护进程
        
        Args:
            task_id: 任务ID
            log_path: 日志文件路径（目录）
        """
        self._process = None
        self._task_id = task_id
        self._log_path = log_path
        self._running = True  # 守护线程是否继续运行
        self._restart = False  # 手动重启标志
        threading.Thread(target=self._daemon, daemon=True).start()

    def _log(self, message: str, level: str = 'INFO', to_file: bool = True, to_app: bool = True):
        """统一的日志记录方法"""
        timestamp = datetime.now().isoformat()
        log_message = f'[{timestamp}] [{level}] {message}'
        
        if to_file:
            try:
                log_file_path = self._get_log_file_path()
                os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
                with open(log_file_path, mode='a', encoding='utf-8') as f:
                    f.write(log_message + '\n')
            except Exception as e:
                pass
        
        if to_app:
            import logging
            logger = logging.getLogger(__name__)
            if level == 'ERROR':
                logger.error(message)
            elif level == 'WARNING':
                logger.warning(message)
            elif level == 'DEBUG':
                logger.debug(message)
            else:
                logger.info(message)

    def _daemon(self):
        """守护线程主循环，管理子进程并处理日志"""
        current_date = datetime.now().date()
        log_file_path = self._get_log_file_path()
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        self._log(f'守护进程启动，任务ID: {self._task_id}', 'INFO')
        
        f_log = open(log_file_path, mode='a', encoding='utf-8')
        try:
            f_log.write(f'# ========== 推流转发任务守护进程启动 ==========\n')
            f_log.write(f'# 任务ID: {self._task_id}\n')
            f_log.write(f'# 启动时间: {datetime.now().isoformat()}\n')
            f_log.write(f'# ===========================================\n\n')
            f_log.flush()
            
            while self._running:
                try:
                    self._log('开始获取部署参数...', 'DEBUG')
                    cmds, cwd, env = self._get_deploy_args()
                    
                    if cmds is None:
                        self._log('获取部署参数失败，无法启动服务', 'ERROR')
                        f_log.write(f'# [{datetime.now().isoformat()}] [ERROR] 获取部署参数失败，无法启动服务\n')
                        f_log.flush()
                        time.sleep(10)  # 等待10秒后重试
                        continue
                    
                    self._log(f'启动服务进程: {" ".join(cmds)}', 'INFO')
                    f_log.write(f'# [{datetime.now().isoformat()}] [INFO] 启动服务进程: {" ".join(cmds)}\n')
                    f_log.flush()
                    
                    # 启动子进程
                    self._process = sp.Popen(
                        cmds,
                        cwd=cwd,
                        env=env,
                        stdout=f_log,
                        stderr=sp.STDOUT,
                        preexec_fn=os.setsid if os.name != 'nt' else None
                    )
                    
                    self._log(f'服务进程已启动，PID: {self._process.pid}', 'INFO')
                    f_log.write(f'# [{datetime.now().isoformat()}] [INFO] 服务进程已启动，PID: {self._process.pid}\n')
                    f_log.flush()
                    
                    # 等待进程结束
                    return_code = self._process.wait()
                    
                    # 检查日期是否变化，如果变化则切换日志文件
                    new_date = datetime.now().date()
                    if new_date != current_date:
                        current_date = new_date
                        f_log.close()
                        log_file_path = self._get_log_file_path()
                        f_log = open(log_file_path, mode='a', encoding='utf-8')
                    
                    if not self._running:
                        self._log('守护进程停止，不再重启服务', 'INFO')
                        f_log.write(f'# [{datetime.now().isoformat()}] [INFO] 守护进程停止，不再重启服务\n')
                        f_log.flush()
                        break
                    
                    if self._restart:
                        self._log('手动重启标志已设置，立即重启服务', 'INFO')
                        f_log.write(f'# [{datetime.now().isoformat()}] [INFO] 手动重启标志已设置，立即重启服务\n')
                        f_log.flush()
                        self._restart = False
                        time.sleep(1)  # 短暂等待后重启
                        continue
                    
                    self._log(f'服务进程异常退出，返回码: {return_code}，5秒后自动重启', 'WARNING')
                    f_log.write(f'# [{datetime.now().isoformat()}] [WARNING] 服务进程异常退出，返回码: {return_code}，5秒后自动重启\n')
                    f_log.flush()
                    time.sleep(5)  # 等待5秒后重启
                    
                except Exception as e:
                    self._log(f'守护进程异常: {str(e)}', 'ERROR')
                    f_log.write(f'# [{datetime.now().isoformat()}] [ERROR] 守护进程异常: {str(e)}\n')
                    f_log.flush()
                    time.sleep(10)  # 异常时等待10秒后重试
        finally:
            f_log.close()

    def _get_log_file_path(self) -> str:
        """获取日志文件路径（按日期）"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        return os.path.join(self._log_path, f'{date_str}.log')

    def _get_deploy_args(self):
        """获取部署参数"""
        try:
            # 获取服务脚本路径
            video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            service_script = os.path.join(video_root, 'services', 'stream_forward_service', 'run_deploy.py')
            
            if not os.path.exists(service_script):
                self._log(f'服务脚本不存在: {service_script}', 'ERROR')
                return None, None, None
            
            # 构建命令
            python_cmd = sys.executable
            cmds = [python_cmd, service_script]
            
            # 工作目录
            cwd = video_root
            
            # 环境变量
            env = os.environ.copy()
            env['TASK_ID'] = str(self._task_id)
            
            return cmds, cwd, env
            
        except Exception as e:
            self._log(f'获取部署参数失败: {str(e)}', 'ERROR')
            return None, None, None

    def stop(self):
        """停止守护进程和服务进程"""
        self._log('停止守护进程...', 'INFO')
        self._running = False
        
        if self._process:
            try:
                # 终止进程组（包括所有子进程）
                if os.name != 'nt':
                    os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                else:
                    self._process.terminate()
                
                # 等待进程结束
                try:
                    self._process.wait(timeout=5)
                except sp.TimeoutExpired:
                    # 如果5秒内未结束，强制终止
                    if os.name != 'nt':
                        os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
                    else:
                        self._process.kill()
                    self._process.wait()
                
                self._log(f'服务进程已停止，PID: {self._process.pid}', 'INFO')
            except Exception as e:
                self._log(f'停止服务进程失败: {str(e)}', 'WARNING')
            finally:
                self._process = None

    def restart(self):
        """手动重启服务进程"""
        self._log('设置手动重启标志...', 'INFO')
        self._restart = True
        if self._process:
            try:
                if os.name != 'nt':
                    os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                else:
                    self._process.terminate()
            except Exception as e:
                self._log(f'终止服务进程失败: {str(e)}', 'WARNING')

