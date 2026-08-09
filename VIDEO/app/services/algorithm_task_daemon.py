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

import app.utils.nvidia_lib_path  # noqa: F401  子进程 run_deploy 继承 LD_LIBRARY_PATH

# 不再需要导入数据库模型，所有信息都通过参数传入


class AlgorithmTaskDaemon:
    """算法任务守护进程，管理算法任务服务进程，支持自动重启
    
    注意：这个守护进程是独立的，不需要数据库连接。
    所有必要的信息都通过参数传入。
    """

    def __init__(
        self,
        task_id: int,
        log_path: str,
        task_type: str = 'realtime',
        llm_enabled: bool = False,
        extra_env: dict = None,
        executor: str = 'cpp',
        runtime_bin: str = None,
        runtime_ini: str = None,
    ):
        """
        初始化守护进程
        
        Args:
            task_id: 任务ID
            log_path: 日志文件路径（目录）
            task_type: 任务类型 ('realtime' 实时算法任务, 'snap' 抓拍算法任务)
            llm_enabled: 是否启用LLM
            extra_env: 启动时注入子进程的额外环境变量（如 SAM 配置，避免守护进程查库）
            executor: python | cpp（G-5.4 起仅 cpp；python 拒绝启动）
            runtime_bin: RUNTIME 二进制路径（executor=cpp）
            runtime_ini: RUNTIME 配置 ini 路径（executor=cpp）
        """
        self._process = None
        self._task_id = task_id
        self._log_path = log_path
        self._task_type = task_type
        self._extra_env = extra_env or {}
        self._executor = (executor or 'cpp').strip().lower()
        self._runtime_bin = runtime_bin
        self._runtime_ini = runtime_ini
        self._running = True  # 守护线程是否继续运行
        self._restart = False  # 手动重启标志
        self._daemon_thread = threading.Thread(target=self._daemon, daemon=True)
        self._daemon_thread.start()

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

                    if not self._running:
                        self._log('守护进程收到停止信号，取消启动子进程', 'INFO')
                        break
                    
                    # 记录启动信息
                    self._log(f'准备启动算法任务服务，任务ID: {self._task_id}, executor={self._executor}', 'INFO')
                    f_log.write(f'\n# ========== 启动算法任务服务 ==========\n')
                    f_log.write(f'# 时间: {datetime.now().isoformat()}\n')
                    f_log.write(f'# 任务ID: {self._task_id}\n')
                    f_log.write(f'# executor: {self._executor}\n')
                    f_log.write(f'# 命令: {" ".join(cmds)}\n')
                    f_log.write(f'# 工作目录: {cwd}\n')
                    f_log.write(f'# 环境变量:\n')
                    for key in ['TASK_ID', 'DATABASE_URL', 'VIDEO_SERVICE_PORT', 'RUNTIME_BIN']:
                        if key in env:
                            f_log.write(f'#   {key}={env[key]}\n')
                    f_log.write(f'# ===================================\n\n')
                    f_log.flush()
                    
                    self._log(f'执行命令: {" ".join(cmds)}', 'DEBUG')
                    self._log(f'工作目录: {cwd}', 'DEBUG')
                    self._log(f'任务ID: {env.get("TASK_ID", "N/A")}', 'INFO')

                    # 如果在windows平台出现跨平台就会报错
                    creationflags = 0
                    preexec_fn = None
                    if os.name == 'posix':
                        # Linux / macOS
                        preexec_fn = os.setsid
                    else:
                        # Windows
                        creationflags = sp.CREATE_NEW_PROCESS_GROUP

                    # 使用进程组启动，以便能够一次性终止整个进程树
                    self._process = sp.Popen(
                        cmds,
                        stdout=sp.PIPE,
                        stderr=sp.STDOUT,
                        cwd=cwd,
                        env=env,
                        text=True,
                        encoding='utf-8',  # 关键
                        errors='replace',  # 防止极端情况直接崩
                        bufsize=1,
                        preexec_fn=preexec_fn,  # 创建新的进程组
                        creationflags=creationflags
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
                    # SIGTERM(-15) 来自 stop()/restart() 时为预期行为，勿当作异常崩溃
                    graceful_stop = (
                        return_code in (-15, 15)
                        and (not self._running or self._restart)
                    )
                    log_level = 'INFO' if return_code == 0 or graceful_stop else 'WARNING'
                    self._log(f'进程已退出，返回码: {return_code}', log_level)
                    f_log.write(f'\n# 进程退出，返回码: {return_code}\n')
                    
                    # 如果进程异常退出，记录所有输出用于诊断，并输出到控制台
                    if return_code != 0 and not graceful_stop:
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
                        # run_deploy 收到 SIGTERM 后 signal_handler 以 0 退出，属预期停机，勿自动重启
                        if return_code == 0:
                            self._log('算法任务服务已正常退出，守护进程结束', 'INFO')
                            f_log.write(
                                f'\n# [{datetime.now().isoformat()}] 算法任务服务已正常退出，守护进程结束\n'
                            )
                            f_log.flush()
                            f_log.close()
                            return
                        restart_msg = f'算法任务服务异常退出（返回码: {return_code}），将在5秒后重启'
                        self._log(restart_msg, 'WARNING')
                        f_log.write(
                            f'\n# [{datetime.now().isoformat()}] {restart_msg}......\n'
                        )
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

    def join_daemon_thread(self, timeout: float = 15.0) -> bool:
        """等待守护线程结束（替换守护进程时避免遗留线程继续拉起子进程）"""
        thread = getattr(self, '_daemon_thread', None)
        if not thread or not thread.is_alive():
            return True
        thread.join(timeout=timeout)
        return not thread.is_alive()

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
        self._log(
            f'任务信息: 任务ID: {self._task_id}, 任务类型: {self._task_type}, executor={self._executor}',
            'DEBUG',
        )

        executor = (getattr(self, '_executor', None) or 'cpp').strip().lower()
        if executor in ('cpp', 'c++', 'runtime', 'cxx'):
            return self._get_cpp_deploy_args()

        # G-5.4: python executor path retired — refuse and log (no silent fallback).
        self._log(
            f'拒绝启动：executor={self._executor!r} 已停用，仅支持 executor=cpp'
            f'（task_id={self._task_id}, task_type={self._task_type}）',
            'ERROR',
        )
        return None, None, None

    def _get_cpp_deploy_args(self) -> tuple:
        """拉起 RUNTIME 二进制（executor=cpp）。"""
        runtime_bin = (self._runtime_bin or os.getenv('RUNTIME_BIN') or '').strip()
        runtime_ini = (self._runtime_ini or '').strip()
        if not runtime_bin or not os.path.isfile(runtime_bin):
            self._log(f'RUNTIME 二进制不存在: {runtime_bin}', 'ERROR')
            return None, None, None
        if not os.access(runtime_bin, os.X_OK) and not runtime_bin.lower().endswith('.exe'):
            self._log(f'RUNTIME 二进制不可执行: {runtime_bin}', 'ERROR')
            return None, None, None
        if not runtime_ini or not os.path.isfile(runtime_ini):
            self._log(f'RUNTIME 配置不存在: {runtime_ini}', 'ERROR')
            return None, None, None

        cmds = [runtime_bin, runtime_ini]
        cwd = os.path.dirname(runtime_bin) or os.getcwd()
        env = os.environ.copy()
        env['TASK_ID'] = str(self._task_id)
        env['LOG_PATH'] = self._log_path
        env['RUNTIME_BIN'] = runtime_bin
        for key in (
            'ALERT_HOOK_URL', 'VIDEO_SERVICE_HOST', 'VIDEO_SERVICE_URL', 'VIDEO_SERVICE_PORT',
            'POD_IP', 'HOST_IP', 'RUNTIME_MODEL_PATH', 'RUNTIME_CLASSES_PATH',
            'LD_LIBRARY_PATH', 'PATH',
            'USE_GPU', 'RUNTIME_PREFER_GPU', 'RUNTIME_FORCE_CPU', 'RUNTIME_GPU_DEVICE_ID',
            'CUDA_VISIBLE_DEVICES', 'NVIDIA_VISIBLE_DEVICES',
        ):
            val = os.getenv(key)
            if val is not None and val != '':
                env[key] = val
        if self._extra_env:
            env.update(self._extra_env)
        # Default prefer GPU unless explicitly disabled
        if 'USE_GPU' not in env:
            env['USE_GPU'] = 'true'
        if 'RUNTIME_PREFER_GPU' not in env:
            env['RUNTIME_PREFER_GPU'] = 'true'
        # Ensure ORT/conda/CUDA libs are visible (Linux LD_LIBRARY_PATH / Windows PATH)
        try:
            from app.services.runtime_config_service import runtime_library_path_env
            lib_path = runtime_library_path_env()
            if lib_path:
                if os.name == 'nt':
                    env['PATH'] = lib_path
                else:
                    existing = (env.get('LD_LIBRARY_PATH') or '').strip()
                    if existing:
                        env['LD_LIBRARY_PATH'] = (
                            lib_path if lib_path == existing else f'{lib_path}:{existing}'
                        )
                    else:
                        env['LD_LIBRARY_PATH'] = lib_path
        except Exception as e:
            self._log(f'构建 runtime library PATH 失败: {e}', 'WARNING')
        self._log(
            f'CPP 启动: {" ".join(cmds)} (USE_GPU={env.get("USE_GPU")}, '
            f'RUNTIME_PREFER_GPU={env.get("RUNTIME_PREFER_GPU")})',
            'INFO',
        )
        return cmds, cwd, env

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

