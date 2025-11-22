"""
模型部署守护线程
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
import io
import time
import urllib.parse
from pathlib import Path
from datetime import datetime

# 不再需要导入数据库模型，所有信息都通过参数传入


class DeployServiceDaemon:
    """模型部署服务守护线程，管理模型服务进程，支持自动重启
    
    注意：这个守护进程是独立的，不需要数据库连接。
    所有必要的信息都通过参数传入。
    """

    def __init__(self, service_id: int, service_name: str, log_path: str,
                 model_id: int, model_path: str, port: int, server_ip: str,
                 model_version: str = 'V1.0.0', model_format: str = 'pytorch'):
        """
        初始化守护进程
        
        Args:
            service_id: 服务ID
            service_name: 服务名称
            log_path: 日志文件路径（目录）
            model_id: 模型ID
            model_path: 模型文件路径（本地路径，已经下载好的）
            port: 服务端口
            server_ip: 服务器IP
            model_version: 模型版本
            model_format: 模型格式
        """
        self._process = None
        self._service_id = service_id
        self._service_name = service_name
        self._log_path = log_path
        self._model_id = model_id
        self._model_path = model_path  # 已经是本地路径
        self._port = port
        self._server_ip = server_ip
        self._model_version = model_version
        self._model_format = model_format
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
        # 不再需要 Flask 应用上下文，所有信息都已通过参数传入
        current_date = datetime.now().date()
        log_file_path = self._get_log_file_path()
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        self._log(f'守护进程启动，服务ID: {self._service_id}', 'INFO')
        
        # 使用追加模式，因为日志文件按日期分割
        f_log = open(log_file_path, mode='a', encoding='utf-8')
        try:
            f_log.write(f'# ========== 模型部署服务守护进程启动 ==========\n')
            f_log.write(f'# 服务ID: {self._service_id}\n')
            f_log.write(f'# 服务名称: {self._service_name}\n')
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
                    self._log(f'准备启动模型服务，服务ID: {self._service_id}', 'INFO')
                    f_log.write(f'\n# ========== 启动模型服务 ==========\n')
                    f_log.write(f'# 时间: {datetime.now().isoformat()}\n')
                    f_log.write(f'# 服务ID: {self._service_id}\n')
                    f_log.write(f'# Python解释器: {cmds[0]}\n')
                    f_log.write(f'# 部署脚本: {cmds[1]}\n')
                    f_log.write(f'# 工作目录: {cwd}\n')
                    f_log.write(f'# 环境变量:\n')
                    for key in ['MODEL_ID', 'MODEL_PATH', 'SERVICE_ID', 'SERVICE_NAME', 'PORT', 'SERVER_IP', 'MODEL_VERSION', 'MODEL_FORMAT']:
                        if key in env:
                            f_log.write(f'#   {key}={env[key]}\n')
                    f_log.write(f'# ===================================\n\n')
                    f_log.flush()
                    
                    self._log(f'执行命令: {" ".join(cmds)}', 'DEBUG')
                    self._log(f'工作目录: {cwd}', 'DEBUG')
                    self._log(f'模型路径: {env.get("MODEL_PATH", "N/A")}', 'INFO')
                    self._log(f'服务端口: {env.get("PORT", "N/A")}', 'INFO')
                    
                    self._process = sp.Popen(
                        cmds,
                        stdout=sp.PIPE,
                        stderr=sp.STDOUT,
                        cwd=cwd,
                        env=env,
                        text=True,
                        bufsize=1
                    )
                    
                    self._log(f'进程已启动，PID: {self._process.pid}', 'INFO')
                    f_log.write(f'# 进程PID: {self._process.pid}\n')
                    f_log.flush()
                    
                    # 实时读取并写入日志
                    # 注意：只写入 services 模块的日志，过滤掉 AI 模块的日志
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
                        
                        # 检查是否是 services 模块的日志（包含 [SERVICES] 前缀）
                        # 或者是 services 模块的其他输出（不包含 AI 模块的特征）
                        # AI 模块的日志特征：
                        # - "✅ multiprocessing启动方法已为'spawn'"
                        # - "✅ 已加载默认配置文件"
                        # - "✅ 已设置 ONNX Runtime 使用 CPU 执行提供者"
                        # - "✅ Flask URL配置"
                        # - "数据库连接:"
                        # - "✅ 数据库连接成功"
                        # - "✅ 所有蓝图注册成功"
                        # - "⚠️ 未配置POD_IP"
                        # - "✅ 服务注册成功: model-server@"
                        # - "🚀 心跳线程已启动"
                        # - Flask HTTP 请求日志格式: "192.168.11.28 - - [23/Nov/2025"
                        
                        # 重要：如果包含错误标记，即使可能是 AI 模块的日志，也要记录
                        is_error = any(marker in line for marker in error_markers)
                        
                        # 过滤掉 AI 模块的正常日志（但保留错误信息）
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
                            # 这是 AI 模块的正常日志，不写入 services 模块的日志文件
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
                            print(f"[守护进程] 服务 {self._service_name} (ID: {self._service_id}) 异常退出，返回码: {return_code}", file=sys.stderr)
                            print(f"[守护进程] 关键错误信息:", file=sys.stderr)
                            print(f"{'='*60}", file=sys.stderr)
                            for error_line in key_errors[-20:]:  # 只输出最后20行错误
                                print(f"[守护进程] {error_line}", file=sys.stderr)
                            print(f"{'='*60}", file=sys.stderr)
                        else:
                            # 如果没有找到明显的错误标记，输出最后几行
                            print(f"\n{'='*60}", file=sys.stderr)
                            print(f"[守护进程] 服务 {self._service_name} (ID: {self._service_id}) 异常退出，返回码: {return_code}", file=sys.stderr)
                            print(f"[守护进程] 最后输出（可能包含错误信息）:", file=sys.stderr)
                            print(f"{'='*60}", file=sys.stderr)
                            for line in all_output_lines[-10:]:  # 输出最后10行
                                print(f"[守护进程] {line.rstrip()}", file=sys.stderr)
                            print(f"{'='*60}", file=sys.stderr)
                    
                    f_log.flush()
                    
                    if not self._running:
                        self._log('守护进程收到停止信号，退出', 'INFO')
                        f_log.write(f'# [{datetime.now().isoformat()}] 模型服务已停止\n')
                        f_log.flush()
                        f_log.close()
                        return

                    # 判断是否异常退出
                    if self._restart:
                        self._restart = False
                        self._log('手动重启模型服务', 'INFO')
                        f_log.write(f'\n# [{datetime.now().isoformat()}] 手动重启模型服务......\n')
                        f_log.flush()
                    else:
                        self._log(f'模型服务异常退出（返回码: {return_code}），将在5秒后重启', 'WARNING')
                        f_log.write(f'\n# [{datetime.now().isoformat()}] 模型服务异常退出（返回码: {return_code}），将在5秒后重启......\n')
                        f_log.flush()
                        time.sleep(5)
                        self._log('模型服务重启', 'INFO')
                        f_log.write(f'# [{datetime.now().isoformat()}] 模型服务重启\n')
                        f_log.flush()
                        
                except Exception as e:
                    import traceback
                    error_msg = f'守护进程异常: {str(e)}\n{traceback.format_exc()}'
                    self._log(error_msg, 'ERROR')
                    f_log.write(f'\n# [{datetime.now().isoformat()}] [ERROR] {error_msg}\n')
                    f_log.flush()
                    time.sleep(10)  # 发生异常时等待10秒后重试
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
        self._running = False
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except sp.TimeoutExpired:
                self._process.kill()

    def _get_log_file_path(self) -> str:
        """获取日志文件路径（按日期）"""
        # 直接使用传入的 log_path（应该是 logs/{service_id}），不需要访问数据库
        os.makedirs(self._log_path, exist_ok=True)
        # 按日期创建日志文件
        log_filename = datetime.now().strftime('%Y-%m-%d.log')
        return os.path.join(self._log_path, log_filename)

    def _get_deploy_args(self) -> tuple:
        """获取部署服务的启动参数"""
        # 所有信息都已通过参数传入，不需要访问数据库
        self._log(f'服务信息: {self._service_name}, 模型ID: {self._model_id}, 端口: {self._port}', 'DEBUG')
        
        # 模型路径已经是本地路径（在 deploy_service.py 中已经处理好了）
        if not self._model_path or not os.path.exists(self._model_path):
            self._log(f'模型文件不存在: {self._model_path}', 'ERROR')
            return None, None, None
        
        self._log(f'模型路径: {self._model_path}', 'INFO')
        
        # 获取部署脚本路径
        deploy_service_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'services')
        deploy_script = os.path.join(deploy_service_dir, 'run_deploy.py')
        
        self._log(f'部署脚本路径: {deploy_script}', 'DEBUG')
        
        if not os.path.exists(deploy_script):
            self._log(f'部署脚本不存在: {deploy_script}', 'ERROR')
            return None, None, None
        
        # 构建启动命令
        # 优先使用当前运行的 Python 解释器（与 test_service.py 保持一致）
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
        # 重要：设置 PYTHONUNBUFFERED，确保输出实时（与 test_service.py 保持一致）
        env['PYTHONUNBUFFERED'] = '1'
        env['MODEL_ID'] = str(self._model_id)
        env['MODEL_PATH'] = self._model_path  # 已经是本地路径
        env['SERVICE_ID'] = str(self._service_id)
        env['SERVICE_NAME'] = self._service_name
        env['PORT'] = str(self._port)
        env['SERVER_IP'] = self._server_ip
        env['MODEL_VERSION'] = self._model_version
        env['MODEL_FORMAT'] = self._model_format
        env['LOG_PATH'] = self._log_path
        
        self._log(f'环境变量已设置: MODEL_PATH={self._model_path}, PORT={env["PORT"]}, SERVICE_NAME={env["SERVICE_NAME"]}', 'DEBUG')
        
        return cmds, deploy_service_dir, env

    def _get_conda_python(self) -> str:
        """获取conda环境的Python路径"""
        conda_env_name = 'AI-SVC'
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

