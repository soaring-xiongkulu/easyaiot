"""
模型部署守护线程
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import subprocess as sp
import os
import threading
import io
import time
import urllib.parse
from pathlib import Path
from datetime import datetime

from db_models import db, AIService, beijing_now


class DeployServiceDaemon:
    """模型部署服务守护线程，管理模型服务进程，支持自动重启"""

    def __init__(self, service_id: int):
        self._process = None
        self._service_id = service_id
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
        # 获取Flask应用上下文
        from flask import current_app
        from run import create_app
        app = create_app()
        
        log_file_path = self._get_log_file_path()
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        self._log(f'守护进程启动，服务ID: {self._service_id}', 'INFO')
        
        with open(log_file_path, mode='w', encoding='utf-8') as f_log:
            f_log.write(f'# ========== 模型部署服务守护进程启动 ==========\n')
            f_log.write(f'# 服务ID: {self._service_id}\n')
            f_log.write(f'# 启动时间: {datetime.now().isoformat()}\n')
            f_log.write(f'# ===========================================\n\n')
            f_log.flush()
            
            while self._running:
                try:
                    with app.app_context():
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
                    for line in iter(self._process.stdout.readline, ''):
                        if not line:
                            break
                        f_log.write(line)
                        f_log.flush()
                    
                    # 等待进程结束
                    return_code = self._process.wait()
                    self._log(f'进程已退出，返回码: {return_code}', 'INFO' if return_code == 0 else 'WARNING')
                    f_log.write(f'\n# 进程退出，返回码: {return_code}\n')
                    f_log.flush()
                    
                    if not self._running:
                        self._log('守护进程收到停止信号，退出', 'INFO')
                        f_log.write(f'# [{datetime.now().isoformat()}] 模型服务已停止\n')
                        f_log.flush()
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
        """获取日志文件路径"""
        try:
            from run import create_app
            app = create_app()
            with app.app_context():
                service = AIService.query.get(self._service_id)
                if service and service.log_path:
                    log_dir = service.log_path
                else:
                    log_dir = os.path.join('data', 'deploy_logs')
                
                os.makedirs(log_dir, exist_ok=True)
                service_name = service.service_name if service else f'service_{self._service_id}'
                return os.path.join(log_dir, f'{service_name}.log')
        except:
            # 如果无法获取应用上下文，使用默认路径
            log_dir = os.path.join('data', 'deploy_logs')
            os.makedirs(log_dir, exist_ok=True)
            return os.path.join(log_dir, f'service_{self._service_id}.log')

    def _parse_minio_url(self, url: str) -> tuple:
        """解析MinIO URL，返回(bucket_name, object_key)"""
        try:
            self._log(f'解析MinIO URL: {url}', 'DEBUG')
            parsed = urllib.parse.urlparse(url)
            path_parts = parsed.path.split('/')
            
            # 提取bucket名称: /api/v1/buckets/{bucket_name}/objects/...
            if len(path_parts) >= 5 and path_parts[3] == 'buckets':
                bucket_name = path_parts[4]
            else:
                self._log(f'URL格式不正确，无法提取bucket名称: {url}', 'ERROR')
                return None, None
            
            # 提取object_key
            query_params = urllib.parse.parse_qs(parsed.query)
            object_key = query_params.get('prefix', [None])[0]
            
            if not object_key:
                self._log(f'URL中缺少prefix参数: {url}', 'ERROR')
                return None, None
            
            self._log(f'解析成功 - Bucket: {bucket_name}, Object: {object_key}', 'DEBUG')
            return bucket_name, object_key
        except Exception as e:
            self._log(f'解析MinIO URL失败: {url}, 错误: {str(e)}', 'ERROR')
            return None, None
    
    def _download_model_from_minio(self, model_path: str) -> str:
        """从MinIO下载模型文件到本地，返回本地文件路径"""
        try:
            self._log(f'开始处理模型路径: {model_path}', 'INFO')
            
            # 检查是否是MinIO URL
            if not model_path.startswith('/api/v1/buckets/'):
                # 如果不是URL，检查是否是本地文件路径
                self._log(f'检测到本地文件路径，检查文件是否存在...', 'DEBUG')
                if os.path.exists(model_path):
                    file_size = os.path.getsize(model_path)
                    self._log(f'模型文件已存在（本地路径）: {model_path}, 大小: {file_size} 字节', 'INFO')
                    return model_path
                else:
                    self._log(f'模型文件不存在: {model_path}', 'ERROR')
                    return None
            
            # 解析URL
            self._log(f'检测到MinIO URL，开始解析...', 'INFO')
            bucket_name, object_key = self._parse_minio_url(model_path)
            if not bucket_name or not object_key:
                self._log(f'无法解析MinIO URL: {model_path}', 'ERROR')
                return None
            
            # 创建模型存储目录
            model_storage_dir = os.path.join('data', 'models', str(self._service_id))
            os.makedirs(model_storage_dir, exist_ok=True)
            self._log(f'模型存储目录: {model_storage_dir}', 'DEBUG')
            
            # 从object_key中提取文件名
            filename = os.path.basename(object_key) or f"model_{self._service_id}"
            local_path = os.path.join(model_storage_dir, filename)
            self._log(f'本地模型文件路径: {local_path}', 'DEBUG')
            
            # 如果文件已存在，直接返回（避免重复下载）
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
                self._log(f'模型文件已存在，跳过下载: {local_path}, 大小: {file_size} 字节', 'INFO')
                return local_path
            
            # 下载文件
            self._log(f'开始从MinIO下载模型文件...', 'INFO')
            self._log(f'  Bucket: {bucket_name}', 'DEBUG')
            self._log(f'  Object: {object_key}', 'DEBUG')
            self._log(f'  目标路径: {local_path}', 'DEBUG')
            
            from app.services.minio_service import ModelService
            from flask import current_app
            
            # 需要在应用上下文中调用
            import time
            start_time = time.time()
            success, error_msg = ModelService.download_from_minio(
                bucket_name, object_key, local_path
            )
            download_time = time.time() - start_time
            
            if success:
                file_size = os.path.getsize(local_path)
                self._log(f'模型文件下载成功: {local_path}, 大小: {file_size} 字节, 耗时: {download_time:.2f}秒', 'INFO')
                return local_path
            else:
                self._log(f'模型文件下载失败: {error_msg}', 'ERROR')
                return None
                
        except Exception as e:
            import traceback
            error_msg = f'下载模型文件异常: {str(e)}\n{traceback.format_exc()}'
            self._log(error_msg, 'ERROR')
            return None

    def _get_deploy_args(self) -> tuple:
        """获取部署服务的启动参数"""
        try:
            self._log(f'获取服务信息，服务ID: {self._service_id}', 'DEBUG')
            service = AIService.query.get(self._service_id)
            if not service:
                self._log(f'服务不存在，服务ID: {self._service_id}', 'ERROR')
                return None, None, None
            
            self._log(f'服务信息: {service.service_name}, 模型ID: {service.model_id}, 端口: {service.port}', 'DEBUG')
            
            model = None
            if service.model_id:
                from db_models import Model
                model = Model.query.get(service.model_id)
            
            if not model:
                self._log(f'模型不存在，模型ID: {service.model_id}', 'ERROR')
                return None, None, None
            
            self._log(f'模型信息: {model.name}, 版本: {model.version}', 'DEBUG')
        except Exception as e:
            import traceback
            error_msg = f'获取部署参数失败: {str(e)}\n{traceback.format_exc()}'
            self._log(error_msg, 'ERROR')
            return None, None, None
        
        # 获取模型路径
        model_path = (model.model_path or model.onnx_model_path or 
                     model.torchscript_model_path or model.tensorrt_model_path or 
                     model.openvino_model_path)
        if not model_path:
            self._log('模型没有可用的模型文件路径', 'ERROR')
            return None, None, None
        
        self._log(f'原始模型路径: {model_path}', 'INFO')
        
        # 如果模型路径是URL，先下载到本地
        local_model_path = self._download_model_from_minio(model_path)
        if not local_model_path:
            self._log(f'无法获取本地模型文件路径，原始路径: {model_path}', 'ERROR')
            return None, None, None
        
        # 获取部署脚本路径
        deploy_service_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'services')
        deploy_script = os.path.join(deploy_service_dir, 'run_deploy.py')
        
        self._log(f'部署脚本路径: {deploy_script}', 'DEBUG')
        
        if not os.path.exists(deploy_script):
            self._log(f'部署脚本不存在: {deploy_script}', 'ERROR')
            return None, None, None
        
        # 构建启动命令
        python_exec = 'python3'
        # 尝试使用conda环境
        conda_python = self._get_conda_python()
        if conda_python:
            python_exec = conda_python
            self._log(f'使用Conda Python: {python_exec}', 'INFO')
        else:
            self._log(f'使用系统Python: {python_exec}', 'INFO')
        
        cmds = [python_exec, deploy_script]
        
        # 准备环境变量
        env = os.environ.copy()
        env['MODEL_ID'] = str(service.model_id) if service.model_id else ''
        env['MODEL_PATH'] = local_model_path  # 使用本地路径
        env['SERVICE_ID'] = str(service.id)
        env['SERVICE_NAME'] = service.service_name
        env['PORT'] = str(service.port)
        env['SERVER_IP'] = service.server_ip
        env['MODEL_VERSION'] = service.model_version or model.version or 'V1.0.0'
        env['MODEL_FORMAT'] = service.format or 'pytorch'
        
        # 日志路径
        if service.log_path:
            env['LOG_PATH'] = service.log_path
        else:
            log_dir = os.path.join('data', 'deploy_logs', service.service_name)
            os.makedirs(log_dir, exist_ok=True)
            env['LOG_PATH'] = log_dir
        
        self._log(f'环境变量已设置: MODEL_PATH={local_model_path}, PORT={env["PORT"]}, SERVICE_NAME={env["SERVICE_NAME"]}', 'DEBUG')
        
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

