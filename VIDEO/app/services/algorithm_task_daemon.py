"""
算法任务守护进程
用于管理算法任务服务进程，支持自动重启

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import subprocess as sp
import os
import sys
import re
import threading
import time
import signal
from datetime import datetime
from typing import Optional

# 不再需要导入数据库模型，所有信息都通过参数传入


class AlgorithmTaskDaemon:
    """算法任务守护进程，管理算法任务服务进程，支持自动重启
    
    注意：这个守护进程是独立的，不需要数据库连接。
    所有必要的信息都通过参数传入。
    """

    def __init__(self, task_id: int, log_path: str, task_type: str = 'realtime'):
        """
        初始化守护进程
        
        Args:
            task_id: 任务ID
            log_path: 日志文件路径（目录）
            task_type: 任务类型 ('realtime' 实时算法任务, 'snap' 抓拍算法任务)
        """
        self._process = None
        self._task_id = task_id
        self._log_path = log_path
        self._task_type = task_type
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
                # 使用追加模式，如果日期变化会自动创建新文件
                with open(log_file_path, mode='a', encoding='utf-8') as f:
                    f.write(log_message + '\n')
            except Exception as e:
                # 如果文件写入失败，至少记录到应用日志
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
        
        # 使用追加模式，因为日志文件按日期分割
        f_log = open(log_file_path, mode='a', encoding='utf-8')
        try:
            f_log.write(f'# ========== 算法任务守护进程启动 ==========\n')
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
                    
                    # 记录启动信息
                    self._log(f'准备启动算法任务服务，任务ID: {self._task_id}', 'INFO')
                    f_log.write(f'\n# ========== 启动算法任务服务 ==========\n')
                    f_log.write(f'# 时间: {datetime.now().isoformat()}\n')
                    f_log.write(f'# 任务ID: {self._task_id}\n')
                    f_log.write(f'# Python解释器: {cmds[0]}\n')
                    f_log.write(f'# 部署脚本: {cmds[1]}\n')
                    f_log.write(f'# 工作目录: {cwd}\n')
                    f_log.write(f'# 环境变量:\n')
                    for key in ['TASK_ID', 'DATABASE_URL', 'VIDEO_SERVICE_PORT']:
                        if key in env:
                            f_log.write(f'#   {key}={env[key]}\n')
                    f_log.write(f'# ===================================\n\n')
                    f_log.flush()
                    
                    self._log(f'执行命令: {" ".join(cmds)}', 'DEBUG')
                    self._log(f'工作目录: {cwd}', 'DEBUG')
                    self._log(f'任务ID: {env.get("TASK_ID", "N/A")}', 'INFO')
                    
                    # 使用进程组启动，以便能够一次性终止整个进程树
                    self._process = sp.Popen(
                        cmds,
                        stdout=sp.PIPE,
                        stderr=sp.STDOUT,
                        cwd=cwd,
                        env=env,
                        text=True,
                        bufsize=1,
                        preexec_fn=os.setsid  # 创建新的进程组
                    )
                    
                    self._log(f'进程已启动，PID: {self._process.pid}', 'INFO')
                    f_log.write(f'# 进程PID: {self._process.pid}\n')
                    f_log.flush()
                    
                    # 实时读取并写入日志
                    # 收集所有输出，用于错误诊断
                    all_output_lines = []
                    error_markers = ['ERROR', 'Error', 'error', '❌', 'Exception', 'Traceback', 'Failed', 'failed']
                    
                    for line in iter(self._process.stdout.readline, ''):
                        if not line:
                            break
                        
                        # 检查日期是否变化，如果变化则切换日志文件
                        today = datetime.now().date()
                        if today != current_date:
                            # 日期变化，关闭旧文件，打开新文件
                            f_log.close()
                            current_date = today
                            log_file_path = self._get_log_file_path()
                            f_log = open(log_file_path, mode='a', encoding='utf-8')
                            f_log.write(f'# ========== 日期切换 ==========\n')
                            f_log.write(f'# 新日期: {current_date}\n')
                            f_log.write(f'# ============================\n\n')
                            f_log.flush()
                        
                        # 保存所有输出用于错误诊断
                        all_output_lines.append(line)
                        
                        # 检查是否包含错误标记
                        is_error = any(marker in line for marker in error_markers)
                        
                        # 过滤掉一些不必要的日志（但保留错误信息）
                        # 可以根据需要添加更多过滤规则
                        if not is_error and any(marker in line for marker in [
                            "✅ multiprocessing启动方法已为",
                            "✅ 已加载默认配置文件",
                            "✅ 已设置 ONNX Runtime 使用 CPU",
                            "✅ Flask URL配置: SERVER_NAME=",
                            "数据库连接: postgresql://",
                            "✅ 数据库连接成功",
                            "✅ 所有蓝图注册成功",
                            "⚠️ 未配置POD_IP",
                            "✅ 服务注册成功: model-server@",
                            "🚀 心跳线程已启动，间隔:",
                        ]):
                            # 这是其他模块的正常日志，不写入算法任务日志文件
                            continue
                        
                        # 过滤掉 Flask HTTP 请求日志（格式：IP - - [日期] "请求" 状态码）
                        if not is_error and re.match(r'^\d+\.\d+\.\d+\.\d+\s+-\s+-\s+\[.*?\]\s+"[A-Z]+', line):
                            # 这是 Flask HTTP 请求日志，不写入
                            continue
                        
                        f_log.write(line)
                        f_log.flush()
                    
                    # 等待进程结束
                    return_code = self._process.wait()
                    self._log(f'进程已退出，返回码: {return_code}', 'INFO' if return_code == 0 else 'WARNING')
                    f_log.write(f'\n# 进程退出，返回码: {return_code}\n')
                    
                    # 如果进程异常退出，记录所有输出用于诊断，并输出到控制台
                    if return_code != 0:
                        error_summary = []
                        error_summary.append(f'\n# ========== 进程异常退出，完整输出 ==========')
                        f_log.write(f'\n# ========== 进程异常退出，完整输出 ==========\n')
                        
                        # 提取关键错误信息
                        key_errors = []
                        for line in all_output_lines:
                            f_log.write(line)
                            # 查找关键错误信息
                            if any(marker in line for marker in ['ERROR', 'Error', 'error', '❌', 'Exception', 'Traceback', 'Failed', 'failed', '无法', '失败']):
                                key_errors.append(line.rstrip())
                        
                        f_log.write(f'# ===========================================\n')
                        error_summary.append(f'# ===========================================')
                        
                        # 输出关键错误到控制台
                        if key_errors:
                            print(f"\n{'='*60}", file=sys.stderr)
                            print(f"[守护进程] 任务 {self._task_id} 异常退出，返回码: {return_code}", file=sys.stderr)
                            print(f"[守护进程] 关键错误信息:", file=sys.stderr)
                            print(f"{'='*60}", file=sys.stderr)
                            for error_line in key_errors[-20:]:  # 只输出最后20行错误
                                print(f"[守护进程] {error_line}", file=sys.stderr)
                            print(f"{'='*60}", file=sys.stderr)
                        else:
                            # 如果没有找到明显的错误标记，输出最后几行
                            print(f"\n{'='*60}", file=sys.stderr)
                            print(f"[守护进程] 任务 {self._task_id} 异常退出，返回码: {return_code}", file=sys.stderr)
                            print(f"[守护进程] 最后输出（可能包含错误信息）:", file=sys.stderr)
                            print(f"{'='*60}", file=sys.stderr)
                            for line in all_output_lines[-10:]:  # 输出最后10行
                                print(f"[守护进程] {line.rstrip()}", file=sys.stderr)
                            print(f"{'='*60}", file=sys.stderr)
                    
                    f_log.flush()
                    
                    # 检查是否应该停止（在重启逻辑之前检查）
                    if not self._running:
                        self._log('守护进程收到停止信号，退出', 'INFO')
                        f_log.write(f'# [{datetime.now().isoformat()}] 算法任务服务已停止\n')
                        f_log.flush()
                        f_log.close()
                        return

                    # 判断是否异常退出
                    if self._restart:
                        self._restart = False
                        # 再次检查是否应该停止（可能在等待过程中收到停止信号）
                        if not self._running:
                            self._log('守护进程收到停止信号，取消重启', 'INFO')
                            f_log.write(f'# [{datetime.now().isoformat()}] 守护进程收到停止信号，取消重启\n')
                            f_log.flush()
                            f_log.close()
                            return
                        self._log('手动重启算法任务服务', 'INFO')
                        f_log.write(f'\n# [{datetime.now().isoformat()}] 手动重启算法任务服务......\n')
                        f_log.flush()
                    else:
                        # 再次检查是否应该停止（可能在等待过程中收到停止信号）
                        if not self._running:
                            self._log('守护进程收到停止信号，取消自动重启', 'INFO')
                            f_log.write(f'# [{datetime.now().isoformat()}] 守护进程收到停止信号，取消自动重启\n')
                            f_log.flush()
                            f_log.close()
                            return
                        self._log(f'算法任务服务异常退出（返回码: {return_code}），将在5秒后重启', 'WARNING')
                        f_log.write(f'\n# [{datetime.now().isoformat()}] 算法任务服务异常退出（返回码: {return_code}），将在5秒后重启......\n')
                        f_log.flush()
                        # 在等待期间，定期检查是否收到停止信号
                        for _ in range(50):  # 5秒 = 50 * 0.1秒
                            if not self._running:
                                self._log('守护进程收到停止信号，取消自动重启', 'INFO')
                                f_log.write(f'# [{datetime.now().isoformat()}] 守护进程收到停止信号，取消自动重启\n')
                                f_log.flush()
                                f_log.close()
                                return
                            time.sleep(0.1)
                        # 等待结束后，再次检查是否应该停止
                        if not self._running:
                            self._log('守护进程收到停止信号，取消自动重启', 'INFO')
                            f_log.write(f'# [{datetime.now().isoformat()}] 守护进程收到停止信号，取消自动重启\n')
                            f_log.flush()
                            f_log.close()
                            return
                        self._log('算法任务服务重启', 'INFO')
                        f_log.write(f'# [{datetime.now().isoformat()}] 算法任务服务重启\n')
                        f_log.flush()
                        
                except Exception as e:
                    import traceback
                    error_msg = f'守护进程异常: {str(e)}\n{traceback.format_exc()}'
                    self._log(error_msg, 'ERROR')
                    f_log.write(f'\n# [{datetime.now().isoformat()}] [ERROR] {error_msg}\n')
                    f_log.flush()
                    # 在等待期间，定期检查是否收到停止信号
                    for _ in range(100):  # 10秒 = 100 * 0.1秒
                        if not self._running:
                            self._log('守护进程收到停止信号，退出异常处理', 'INFO')
                            f_log.write(f'# [{datetime.now().isoformat()}] 守护进程收到停止信号，退出异常处理\n')
                            f_log.flush()
                            f_log.close()
                            return
                        time.sleep(0.1)
        finally:
            if f_log:
                f_log.close()

    def restart(self):
        """手动重启服务"""
        self._restart = True
        if self._process:
            self._process.terminate()

    def stop(self):
        """停止服务"""
        self._log('收到停止信号，正在停止守护进程...', 'INFO')
        self._running = False
        if self._process:
            try:
                # 先尝试优雅终止整个进程组
                try:
                    # 使用进程组ID终止整个进程树（包括所有子进程和孙进程，如FFmpeg）
                    pgid = os.getpgid(self._process.pid)
                    self._log(f'终止进程组 {pgid} (主进程PID: {self._process.pid})', 'INFO')
                    os.killpg(pgid, signal.SIGTERM)
                except (ProcessLookupError, OSError) as e:
                    # 如果进程组不存在，尝试直接终止主进程
                    self._log(f'进程组不存在，直接终止主进程: {str(e)}', 'WARNING')
                    try:
                        self._process.terminate()
                    except ProcessLookupError:
                        # 进程已经不存在
                        self._log('进程已不存在', 'INFO')
                        return
                
                # 等待进程退出
                try:
                    self._process.wait(timeout=10)  # 增加等待时间到10秒
                    self._log('进程已优雅退出', 'INFO')
                except sp.TimeoutExpired:
                    # 如果10秒内没有退出，强制杀死整个进程组
                    self._log('进程未在10秒内退出，强制终止整个进程组', 'WARNING')
                    try:
                        pgid = os.getpgid(self._process.pid)
                        os.killpg(pgid, signal.SIGKILL)
                    except (ProcessLookupError, OSError):
                        # 如果进程组不存在，尝试直接杀死主进程
                        try:
                            self._process.kill()
                        except ProcessLookupError:
                            pass
                    try:
                        self._process.wait(timeout=3)
                    except (sp.TimeoutExpired, ProcessLookupError):
                        pass
            except Exception as e:
                self._log(f'停止进程时出错: {str(e)}', 'WARNING')
                # 如果进程已经不存在，忽略错误
                pass
        self._log('守护进程已停止', 'INFO')

    def _get_log_file_path(self) -> str:
        """获取日志文件路径（按日期）"""
        # 直接使用传入的 log_path（应该是 logs/task_{task_id}），不需要访问数据库
        os.makedirs(self._log_path, exist_ok=True)
        # 按日期创建日志文件
        log_filename = datetime.now().strftime('%Y-%m-%d.log')
        return os.path.join(self._log_path, log_filename)

    def _get_deploy_args(self) -> tuple:
        """获取部署服务的启动参数"""
        self._log(f'任务信息: 任务ID: {self._task_id}, 任务类型: {self._task_type}', 'DEBUG')
        
        # 根据任务类型选择服务路径
        video_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if self._task_type == 'snap':
            deploy_service_dir = os.path.join(video_root, 'services', 'snapshot_algorithm_service')
        else:  # realtime
            deploy_service_dir = os.path.join(video_root, 'services', 'realtime_algorithm_service')
        
        deploy_script = os.path.join(deploy_service_dir, 'run_deploy.py')
        
        self._log(f'部署脚本路径: {deploy_script}', 'DEBUG')
        
        if not os.path.exists(deploy_script):
            self._log(f'部署脚本不存在: {deploy_script}', 'ERROR')
            return None, None, None
        
        # 构建启动命令
        # 优先使用当前运行的 Python 解释器（与 AI 模块保持一致）
        python_exec = sys.executable
        # 尝试使用conda环境（如果存在且与当前解释器不同）
        conda_python = self._get_conda_python()
        if conda_python and conda_python != python_exec:
            # 检查 conda Python 是否存在且可执行
            if os.path.exists(conda_python) and os.access(conda_python, os.X_OK):
                python_exec = conda_python
                self._log(f'使用Conda Python: {python_exec}', 'INFO')
            else:
                self._log(f'Conda Python 路径无效，使用当前解释器: {python_exec}', 'INFO')
        else:
            self._log(f'使用当前Python解释器: {python_exec}', 'INFO')
        
        cmds = [python_exec, deploy_script]
        
        # 准备环境变量（使用传入的参数）
        env = os.environ.copy()
        # 重要：设置 PYTHONUNBUFFERED，确保输出实时（与 AI 模块保持一致）
        env['PYTHONUNBUFFERED'] = '1'
        env['TASK_ID'] = str(self._task_id)
        
        # 确保关键环境变量被传递
        if 'DATABASE_URL' not in env:
            self._log('DATABASE_URL环境变量未设置，服务可能无法连接数据库', 'WARNING')
        
        # 设置VIDEO服务API地址（用于心跳上报和告警hook）
        video_service_port = os.getenv('FLASK_RUN_PORT', '6000')
        env['VIDEO_SERVICE_PORT'] = video_service_port
        
        # 重要：realtime_algorithm_service 使用 host 网络模式，必须使用 localhost 访问 Kafka
        # 如果环境变量中配置了容器名（如 Kafka:9092），需要强制覆盖为 localhost:9092
        # 这样可以避免在 host 网络模式下尝试解析容器名导致的连接失败
        kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        # 如果配置中包含容器名（Kafka 或 kafka-server），强制使用 localhost
        if 'Kafka' in kafka_bootstrap_servers or 'kafka-server' in kafka_bootstrap_servers:
            self._log(f'检测到 Kafka 配置使用容器名，强制覆盖为 localhost:9092（realtime_algorithm_service 使用 host 网络模式）', 'INFO')
            env['KAFKA_BOOTSTRAP_SERVERS'] = 'localhost:9092'
        else:
            # 如果已经是 localhost 或 IP 地址，直接使用
            env['KAFKA_BOOTSTRAP_SERVERS'] = kafka_bootstrap_servers
        
        # 设置日志路径
        env['LOG_PATH'] = self._log_path
        
        self._log(f'环境变量已设置: TASK_ID={env["TASK_ID"]}, VIDEO_SERVICE_PORT={env["VIDEO_SERVICE_PORT"]}, KAFKA_BOOTSTRAP_SERVERS={env["KAFKA_BOOTSTRAP_SERVERS"]}', 'DEBUG')
        
        return cmds, deploy_service_dir, env

    def _get_conda_python(self) -> str:
        """获取conda环境的Python路径"""
        conda_env_name = 'VIDEO-SVC'
        self._log(f'查找Conda环境: {conda_env_name}', 'DEBUG')
        
        possible_paths = [
            os.path.expanduser(f'~/miniconda3/envs/{conda_env_name}/bin/python'),
            os.path.expanduser(f'~/anaconda3/envs/{conda_env_name}/bin/python'),
            f'/opt/conda/envs/{conda_env_name}/bin/python',
            f'/usr/local/miniconda3/envs/{conda_env_name}/bin/python',
            f'/usr/local/anaconda3/envs/{conda_env_name}/bin/python',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self._log(f'找到Conda Python: {path}', 'DEBUG')
                return path
        
        # 尝试使用conda run
        try:
            self._log(f'尝试使用conda run查找Python...', 'DEBUG')
            result = sp.run(
                ['conda', 'run', '-n', conda_env_name, 'which', 'python'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                python_path = result.stdout.strip()
                if python_path and os.path.exists(python_path):
                    self._log(f'通过conda run找到Python: {python_path}', 'DEBUG')
                    return python_path
        except Exception as e:
            self._log(f'conda run查找失败: {str(e)}', 'DEBUG')
        
        self._log(f'未找到Conda环境，将使用系统Python', 'DEBUG')
        return None

