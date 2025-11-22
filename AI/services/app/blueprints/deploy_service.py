"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import os
import socket
import subprocess
import threading
import time
import uuid
from datetime import datetime

import psutil
import requests
from flask import Blueprint, request, jsonify
from sqlalchemy import desc

from db_models import db, Model, AIService, beijing_now

deploy_service_bp = Blueprint('deploy_service', __name__)
logger = logging.getLogger(__name__)

# 存储部署服务的进程信息
deploy_processes = {}


def check_port_available(host, port):
    """检查端口是否可用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        sock.close()
        return True
    except OSError:
        return False
    finally:
        try:
            sock.close()
        except:
            pass


def find_available_port(start_port=8000, max_attempts=100):
    """查找可用端口，从start_port开始自增"""
    for i in range(max_attempts):
        port = start_port + i
        if check_port_available('0.0.0.0', port):
            return port
    return None


def get_mac_address():
    """获取MAC地址"""
    try:
        import uuid
        mac = uuid.getnode()
        return ':'.join(['{:02x}'.format((mac >> elements) & 0xff) for elements in range(0, 2 * 6, 2)][::-1])
    except:
        return 'unknown'


def get_local_ip():
    """获取本地IP地址"""
    try:
        import netifaces
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface).get(netifaces.AF_INET, [])
            for addr in addrs:
                ip = addr['addr']
                if ip != '127.0.0.1' and not ip.startswith('169.254.'):
                    return ip
    except:
        pass
    
    # 备用方案
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def install_conda():
    """安装conda（Miniconda）"""
    try:
        import platform
        import urllib.request
        
        logger.info("开始安装conda（Miniconda）...")
        
        # 检测系统架构
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # 确定下载URL
        if system == 'linux':
            if machine in ['x86_64', 'amd64']:
                arch = 'x86_64'
            elif machine in ['aarch64', 'arm64']:
                arch = 'aarch64'
            else:
                logger.error(f"不支持的系统架构: {machine}")
                return False
            installer_name = f"Miniconda3-latest-Linux-{arch}.sh"
        elif system == 'darwin':  # macOS
            if machine in ['x86_64', 'amd64']:
                arch = 'x86_64'
            elif machine in ['arm64', 'aarch64']:
                arch = 'arm64'
            else:
                logger.error(f"不支持的系统架构: {machine}")
                return False
            installer_name = f"Miniconda3-latest-MacOSX-{arch}.sh"
        else:
            logger.error(f"不支持的操作系统: {system}")
            return False
        
        installer_url = f"https://repo.anaconda.com/miniconda/{installer_name}"
        installer_path = os.path.join('/tmp', installer_name)
        
        logger.info(f"下载Miniconda安装程序: {installer_url}")
        
        # 下载安装程序
        try:
            urllib.request.urlretrieve(installer_url, installer_path)
            logger.info("下载完成")
        except Exception as e:
            logger.error(f"下载Miniconda安装程序失败: {str(e)}")
            return False
        
        # 检查下载的文件
        if not os.path.exists(installer_path) or os.path.getsize(installer_path) == 0:
            logger.error("下载的安装程序文件无效")
            return False
        
        # 设置安装路径（默认安装到用户目录）
        home_dir = os.path.expanduser('~')
        install_dir = os.path.join(home_dir, 'miniconda3')
        
        logger.info(f"安装Miniconda到: {install_dir}")
        
        # 执行安装（静默模式）
        install_result = subprocess.run(
            ['bash', installer_path, '-b', '-p', install_dir, '-f'],
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )
        
        # 清理安装程序
        try:
            os.remove(installer_path)
        except:
            pass
        
        if install_result.returncode == 0:
            logger.info("Miniconda安装成功")
            
            # 将conda添加到PATH
            conda_bin = os.path.join(install_dir, 'bin')
            if conda_bin not in os.environ.get('PATH', ''):
                os.environ['PATH'] = f"{conda_bin}:{os.environ.get('PATH', '')}"
            
            return True
        else:
            logger.error(f"Miniconda安装失败: {install_result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"安装conda时发生异常: {str(e)}")
        return False


def check_and_init_conda():
    """检查conda是否已安装和初始化，如果没有则安装并初始化"""
    try:
        # 首先尝试直接执行conda命令检查是否可用
        conda_version_check = subprocess.run(
            ['conda', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if conda_version_check.returncode == 0:
            # conda可用，检查是否已初始化
            # 检查常见的shell配置文件
            home_dir = os.path.expanduser('~')
            shell_configs = [
                os.path.join(home_dir, '.bashrc'),
                os.path.join(home_dir, '.zshrc'),
                os.path.join(home_dir, '.bash_profile'),
                os.path.join(home_dir, '.profile')
            ]
            
            conda_initialized = False
            for config_file in shell_configs:
                if os.path.exists(config_file):
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 检查是否包含conda初始化代码
                            if 'conda initialize' in content or '>>> conda initialize >>>' in content:
                                conda_initialized = True
                                break
                    except Exception:
                        continue
            
            # 如果未初始化，执行conda init
            if not conda_initialized:
                logger.info("检测到conda未初始化，正在执行conda init...")
                
                # 检测当前shell类型
                shell = os.environ.get('SHELL', '/bin/bash')
                if 'zsh' in shell:
                    shell_type = 'zsh'
                elif 'fish' in shell:
                    shell_type = 'fish'
                elif 'powershell' in shell.lower():
                    shell_type = 'powershell'
                else:
                    shell_type = 'bash'  # 默认使用bash
                
                logger.info(f"检测到shell类型: {shell_type}，执行conda init {shell_type}")
                
                # 执行conda init
                init_result = subprocess.run(
                    ['conda', 'init', shell_type],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if init_result.returncode == 0:
                    logger.info(f"conda init {shell_type} 执行成功")
                    # 尝试重新加载环境（通过source配置文件）
                    # 注意：在Python中直接source可能不会立即生效，但conda命令应该已经可用
                    return True
                else:
                    logger.warning(f"conda init {shell_type} 执行失败: {init_result.stderr}")
                    # 即使init失败，也继续尝试使用conda
                    return True
            else:
                logger.info("conda已初始化")
                return True
        else:
            # conda命令执行失败，可能是未初始化
            logger.info("conda命令执行失败，尝试查找conda安装路径...")
            
            # 尝试查找conda的常见安装路径
            possible_conda_paths = [
                os.path.expanduser('~/anaconda3/bin/conda'),
                os.path.expanduser('~/miniconda3/bin/conda'),
                '/opt/conda/bin/conda',
                '/usr/local/anaconda3/bin/conda',
                '/usr/local/miniconda3/bin/conda',
            ]
            
            conda_path = None
            for path in possible_conda_paths:
                if os.path.exists(path):
                    logger.info(f"找到conda安装路径: {path}")
                    conda_path = path
                    break
            
            if not conda_path:
                # conda未找到，尝试安装
                logger.info("未找到conda安装，开始安装conda...")
                if install_conda():
                    # 安装成功后，更新conda路径
                    home_dir = os.path.expanduser('~')
                    conda_path = os.path.join(home_dir, 'miniconda3', 'bin', 'conda')
                    if not os.path.exists(conda_path):
                        logger.warning("conda安装成功但无法找到conda可执行文件")
                        return False
                    logger.info(f"conda安装成功，路径: {conda_path}")
                else:
                    logger.error("conda安装失败，跳过conda初始化")
                    return False
            
            # 使用找到的conda路径执行conda init来初始化
            logger.info("尝试执行conda init以初始化conda...")
            
            # 检测当前shell类型
            shell = os.environ.get('SHELL', '/bin/bash')
            if 'zsh' in shell:
                shell_type = 'zsh'
            elif 'fish' in shell:
                shell_type = 'fish'
            elif 'powershell' in shell.lower():
                shell_type = 'powershell'
            else:
                shell_type = 'bash'  # 默认使用bash
            
            logger.info(f"检测到shell类型: {shell_type}，执行conda init {shell_type}")
            
            # 执行conda init（使用找到的conda路径）
            init_result = subprocess.run(
                [conda_path, 'init', shell_type],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if init_result.returncode == 0:
                logger.info(f"conda init {shell_type} 执行成功")
                # 更新PATH以便后续使用
                conda_bin_dir = os.path.dirname(conda_path)
                if conda_bin_dir not in os.environ.get('PATH', ''):
                    os.environ['PATH'] = f"{conda_bin_dir}:{os.environ.get('PATH', '')}"
                return True
            else:
                logger.warning(f"conda init {shell_type} 执行失败: {init_result.stderr}")
                return False
            
    except FileNotFoundError:
        logger.info("conda命令未找到，尝试安装conda...")
        if install_conda():
            # 安装成功后，再次尝试初始化
            logger.info("conda安装成功，继续初始化...")
            # 重新尝试检查conda版本
            try:
                conda_version_check = subprocess.run(
                    ['conda', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if conda_version_check.returncode == 0:
                    # conda可用，继续初始化流程
                    shell = os.environ.get('SHELL', '/bin/bash')
                    if 'zsh' in shell:
                        shell_type = 'zsh'
                    elif 'fish' in shell:
                        shell_type = 'fish'
                    elif 'powershell' in shell.lower():
                        shell_type = 'powershell'
                    else:
                        shell_type = 'bash'
                    
                    init_result = subprocess.run(
                        ['conda', 'init', shell_type],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if init_result.returncode == 0:
                        logger.info(f"conda init {shell_type} 执行成功")
                        return True
                    else:
                        logger.warning(f"conda init {shell_type} 执行失败: {init_result.stderr}")
                        return True  # 即使init失败，conda已安装，继续使用
                else:
                    logger.warning("conda安装成功但无法执行，跳过初始化")
                    return False
            except Exception as e:
                logger.warning(f"conda安装后检查失败: {str(e)}")
                return False
        else:
            logger.error("conda安装失败，跳过conda初始化")
            return False
    except Exception as e:
        logger.warning(f"检查conda初始化时发生异常: {str(e)}")
        return False


def install_deploy_dependencies():
    """在模型部署之前安装依赖"""
    conda_env_name = 'AI-SVC'
    
    # 获取services目录路径（requirements.txt所在目录）
    services_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    requirements_file = os.path.join(services_dir, 'requirements.txt')
    
    if not os.path.exists(requirements_file):
        logger.warning(f"requirements.txt文件不存在: {requirements_file}，跳过依赖安装")
        return True
    
    try:
        logger.info(f"开始安装部署服务依赖: {requirements_file}")
        
        # 检查并初始化conda
        check_and_init_conda()
        
        # 检查conda是否可用
        conda_check = subprocess.run(
            ['conda', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if conda_check.returncode != 0:
            logger.warning("conda不可用，使用系统pip安装依赖")
            # 如果conda不可用，直接使用pip
            result = subprocess.run(
                ['pip', 'install', '-r', requirements_file],
                cwd=services_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("部署服务依赖安装成功")
                return True
            else:
                logger.error(f"部署服务依赖安装失败: {result.stderr}")
                return False
        
        # 检查conda环境是否存在
        logger.info(f"检查conda环境: {conda_env_name}")
        env_list_result = subprocess.run(
            ['conda', 'env', 'list'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        env_exists = False
        if env_list_result.returncode == 0:
            # 检查环境列表中是否包含目标环境（精确匹配环境名）
            import re
            # 使用正则表达式匹配环境名（作为独立单词，可能在行首或空格后）
            pattern = r'(?:^|\s)' + re.escape(conda_env_name) + r'(?:\s|$)'
            env_exists = bool(re.search(pattern, env_list_result.stdout, re.MULTILINE))
        
        # 如果环境不存在，创建环境
        if not env_exists:
            logger.info(f"conda环境 {conda_env_name} 不存在，正在创建...")
            create_result = subprocess.run(
                ['conda', 'create', '-n', conda_env_name, 'python=3.10', '-y'],
                capture_output=True,
                text=True,
                timeout=600  # 创建环境可能需要较长时间，设置10分钟超时
            )
            
            if create_result.returncode != 0:
                logger.error(f"创建conda环境失败: {create_result.stderr}")
                return False
            
            logger.info(f"conda环境 {conda_env_name} 创建成功")
        else:
            logger.info(f"conda环境 {conda_env_name} 已存在")
        
        # 在conda环境中执行pip install
        logger.info(f"在conda环境 {conda_env_name} 中安装依赖...")
        result = subprocess.run(
            ['conda', 'run', '-n', conda_env_name, 'pip', 'install', '-r', requirements_file],
            cwd=services_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            logger.info(f"在conda环境 {conda_env_name} 中部署服务依赖安装成功")
            return True
        else:
            logger.error(f"在conda环境 {conda_env_name} 中部署服务依赖安装失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("依赖安装超时")
        return False
    except FileNotFoundError:
        logger.warning("conda命令未找到，使用系统pip安装依赖")
        # 如果conda命令不存在，尝试直接使用pip
        try:
            result = subprocess.run(
                ['pip', 'install', '-r', requirements_file],
                cwd=services_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("部署服务依赖安装成功（使用系统pip）")
                return True
            else:
                logger.error(f"部署服务依赖安装失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"使用系统pip安装依赖时发生异常: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"安装部署服务依赖时发生异常: {str(e)}")
        return False


# 部署服务列表查询
@deploy_service_bp.route('/list', methods=['GET'])
def get_deploy_services():
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        model_id = request.args.get('model_id', '').strip()
        server_ip = request.args.get('server_ip', '').strip()
        status_filter = request.args.get('status', '').strip()

        if page_no < 1 or page_size < 1:
            return jsonify({
                'code': 400,
                'msg': '参数错误：pageNo和pageSize必须为正整数'
            }), 400

        # 构建查询（使用 LEFT JOIN 支持 model_id 为空的情况）
        query = db.session.query(AIService, Model.name.label('model_name')).outerjoin(
            Model, AIService.model_id == Model.id
        )

        # 应用过滤条件
        if model_id:
            try:
                model_id_int = int(model_id)
                query = query.filter(AIService.model_id == model_id_int)
            except ValueError:
                # 如果model_id不是数字，忽略该过滤条件
                pass
        
        if server_ip:
            query = query.filter(AIService.server_ip.ilike(f'%{server_ip}%'))
        
        if status_filter in ['running', 'stopped', 'error']:
            query = query.filter(AIService.status == status_filter)

        # 按创建时间倒序
        query = query.order_by(desc(AIService.created_at))

        # 分页
        pagination = query.paginate(
            page=page_no,
            per_page=page_size,
            error_out=False
        )

        # 构建响应数据
        records = []
        for service, model_name in pagination.items:
            service_dict = service.to_dict()
            service_dict['model_name'] = model_name if model_name else None  # 处理 model_id 为空的情况
            # 如果服务记录中没有版本和格式，从Model表获取
            if not service_dict.get('model_version'):
                model = Model.query.get(service.model_id)
                if model:
                    service_dict['model_version'] = model.version
            if not service_dict.get('format'):
                # 尝试从模型路径推断格式
                model = Model.query.get(service.model_id)
                if model:
                    model_path = model.model_path or model.onnx_model_path or model.torchscript_model_path or model.tensorrt_model_path or model.openvino_model_path
                    if model_path:
                        model_path_lower = model_path.lower()
                        if model_path_lower.endswith('.onnx') or 'onnx' in model_path_lower:
                            service_dict['format'] = 'onnx'
                        elif model_path_lower.endswith(('.pt', '.pth')):
                            service_dict['format'] = 'pytorch'
                        elif 'openvino' in model_path_lower:
                            service_dict['format'] = 'openvino'
                        elif 'tensorrt' in model_path_lower:
                            service_dict['format'] = 'tensorrt'
                        elif model.onnx_model_path:
                            service_dict['format'] = 'onnx'
                        elif model.torchscript_model_path:
                            service_dict['format'] = 'torchscript'
                        elif model.tensorrt_model_path:
                            service_dict['format'] = 'tensorrt'
                        elif model.openvino_model_path:
                            service_dict['format'] = 'openvino'
            records.append(service_dict)

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': records,
            'total': pagination.total
        })

    except ValueError:
        return jsonify({
            'code': 400,
            'msg': '参数类型错误：pageNo和pageSize需为整数'
        }), 400
    except Exception as e:
        logger.error(f'查询部署服务失败: {str(e)}')
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 部署模型服务
@deploy_service_bp.route('/deploy', methods=['POST'])
def deploy_model():
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        service_name = data.get('service_name', '').strip()
        start_port = int(data.get('start_port', 8000))

        if not model_id:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：model_id'
            }), 400

        # 检查模型是否存在
        model = Model.query.get(model_id)
        if not model:
            return jsonify({
                'code': 404,
                'msg': '模型不存在'
            }), 404

        # 检查模型路径并推断格式
        model_path = model.model_path or model.onnx_model_path or model.torchscript_model_path or model.tensorrt_model_path or model.openvino_model_path
        if not model_path:
            return jsonify({
                'code': 400,
                'msg': '模型没有可用的模型文件路径'
            }), 400

        # 推断模型格式
        model_format = None
        model_path_lower = model_path.lower()
        if model_path_lower.endswith('.onnx') or 'onnx' in model_path_lower:
            model_format = 'onnx'
        elif model_path_lower.endswith(('.pt', '.pth')) or 'pytorch' in model_path_lower or 'torch' in model_path_lower:
            model_format = 'pytorch'
        elif 'openvino' in model_path_lower:
            model_format = 'openvino'
        elif 'tensorrt' in model_path_lower or model_path_lower.endswith('.trt'):
            model_format = 'tensorrt'
        elif model_path_lower.endswith('.tflite'):
            model_format = 'tflite'
        elif 'coreml' in model_path_lower or model_path_lower.endswith('.mlmodel'):
            model_format = 'coreml'
        else:
            # 默认根据路径字段判断
            if model.onnx_model_path:
                model_format = 'onnx'
            elif model.torchscript_model_path:
                model_format = 'torchscript'
            elif model.tensorrt_model_path:
                model_format = 'tensorrt'
            elif model.openvino_model_path:
                model_format = 'openvino'
            else:
                model_format = 'pytorch'  # 默认

        # 生成服务名称
        if not service_name:
            service_name = f"{model.name}_{model.version}_{int(time.time())}"

        # 查找可用端口
        port = find_available_port(start_port)
        if not port:
            return jsonify({
                'code': 500,
                'msg': f'无法找到可用端口（从{start_port}开始尝试了100个端口）'
            }), 500

        # 获取服务器信息
        server_ip = get_local_ip()
        mac_address = get_mac_address()
        
        # 创建日志目录
        log_dir = os.path.join('data', 'deploy_logs')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"{service_name}_{port}.log")

        # 创建部署服务记录
        ai_service = AIService(
            model_id=model_id,
            service_name=service_name,
            server_ip=server_ip,
            port=port,
            inference_endpoint=f"http://{server_ip}:{port}/inference",
            status='stopped',
            mac_address=mac_address,
            deploy_time=beijing_now(),
            log_path=log_path,
            model_version=model.version,
            format=model_format
        )
        db.session.add(ai_service)
        db.session.commit()

        # 启动部署服务进程
        deploy_service_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'deploy_service')
        deploy_script = os.path.join(deploy_service_dir, 'run_deploy.py')
        
        if not os.path.exists(deploy_script):
            # 如果部署脚本不存在，先创建服务记录，稍后可以手动启动
            logger.warning(f"部署脚本不存在: {deploy_script}，服务记录已创建但未启动")
            return jsonify({
                'code': 0,
                'msg': '服务记录已创建，但部署脚本不存在，请检查部署服务目录',
                'data': ai_service.to_dict()
            })

        # 在部署之前安装依赖
        if not install_deploy_dependencies():
            logger.warning("依赖安装失败，但继续尝试启动部署服务")

        # 启动部署服务
        env = os.environ.copy()
        env['MODEL_ID'] = str(model_id)
        env['MODEL_PATH'] = model_path
        env['SERVICE_ID'] = str(ai_service.id)
        env['SERVICE_NAME'] = service_name
        env['PORT'] = str(port)
        env['SERVER_IP'] = server_ip
        env['LOG_PATH'] = log_path
        env['AI_SERVICE_API'] = os.getenv('AI_SERVICE_API', 'http://localhost:5000/model/deploy_service')

        try:
            with open(log_path, 'a') as log_file:
                process = subprocess.Popen(
                    ['python', deploy_script],
                    cwd=deploy_service_dir,
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
            
            # 更新服务记录
            ai_service.process_id = process.pid
            ai_service.status = 'running'
            db.session.commit()

            # 存储进程信息
            deploy_processes[ai_service.id] = {
                'process': process,
                'service_id': ai_service.id
            }

            logger.info(f"部署服务已启动: {service_name} on {server_ip}:{port} (PID: {process.pid})")

            return jsonify({
                'code': 0,
                'msg': '部署成功',
                'data': ai_service.to_dict()
            })

        except Exception as e:
            logger.error(f"启动部署服务失败: {str(e)}")
            ai_service.status = 'error'
            db.session.commit()
            return jsonify({
                'code': 500,
                'msg': f'启动部署服务失败: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f"部署模型失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 启动服务
@deploy_service_bp.route('/<int:service_id>/start', methods=['POST'])
def start_service(service_id):
    try:
        service = AIService.query.get_or_404(service_id)
        
        if service.status == 'running':
            return jsonify({
                'code': 400,
                'msg': '服务已在运行中'
            }), 400

        # 检查端口是否可用
        if not check_port_available('0.0.0.0', service.port):
            # 如果端口被占用，尝试找新端口
            new_port = find_available_port(service.port)
            if new_port:
                service.port = new_port
                service.inference_endpoint = f"http://{service.server_ip}:{new_port}/inference"
                logger.info(f"端口{service.port}被占用，已切换到端口{new_port}")
            else:
                return jsonify({
                    'code': 500,
                    'msg': '无法找到可用端口'
                }), 500

        # 获取模型信息
        if not service.model_id:
            return jsonify({
                'code': 400,
                'msg': '服务未关联模型，无法启动。请先为服务关联模型或通过心跳上报 model_id'
            }), 400

        model = Model.query.get(service.model_id)
        if not model:
            return jsonify({
                'code': 404,
                'msg': '关联的模型不存在'
            }), 404

        model_path = model.model_path or model.onnx_model_path
        if not model_path:
            return jsonify({
                'code': 400,
                'msg': '模型没有可用的模型文件路径'
            }), 400

        # 启动部署服务
        deploy_service_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'deploy_service')
        deploy_script = os.path.join(deploy_service_dir, 'run_deploy.py')
        
        if not os.path.exists(deploy_script):
            return jsonify({
                'code': 500,
                'msg': '部署脚本不存在'
            }), 500

        # 在部署之前安装依赖
        if not install_deploy_dependencies():
            logger.warning("依赖安装失败，但继续尝试启动部署服务")

        env = os.environ.copy()
        env['MODEL_ID'] = str(service.model_id) if service.model_id else ''
        env['MODEL_PATH'] = model_path
        env['SERVICE_ID'] = str(service.id)
        env['SERVICE_NAME'] = service.service_name
        env['PORT'] = str(service.port)
        env['SERVER_IP'] = service.server_ip
        env['LOG_PATH'] = service.log_path or os.path.join('data', 'deploy_logs', f"{service.service_name}_{service.port}.log")
        env['AI_SERVICE_API'] = os.getenv('AI_SERVICE_API', 'http://localhost:5000/model/deploy_service')

        try:
            log_path = env['LOG_PATH']
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            
            with open(log_path, 'a') as log_file:
                process = subprocess.Popen(
                    ['python', deploy_script],
                    cwd=deploy_service_dir,
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
            
            service.process_id = process.pid
            service.status = 'running'
            db.session.commit()

            deploy_processes[service.id] = {
                'process': process,
                'service_id': service.id
            }

            logger.info(f"服务已启动: {service.service_name} on {service.server_ip}:{service.port} (PID: {process.pid})")

            return jsonify({
                'code': 0,
                'msg': '服务启动成功',
                'data': service.to_dict()
            })

        except Exception as e:
            logger.error(f"启动服务失败: {str(e)}")
            service.status = 'error'
            db.session.commit()
            return jsonify({
                'code': 500,
                'msg': f'启动服务失败: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f"启动服务失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 停止服务
@deploy_service_bp.route('/<int:service_id>/stop', methods=['POST'])
def stop_service(service_id):
    try:
        service = AIService.query.get_or_404(service_id)
        
        if service.status != 'running':
            return jsonify({
                'code': 400,
                'msg': '服务未在运行中'
            }), 400

        # 停止进程
        if service.process_id:
            try:
                # 尝试从进程字典中获取
                if service.id in deploy_processes:
                    process = deploy_processes[service.id]['process']
                    process.terminate()
                    process.wait(timeout=5)
                    del deploy_processes[service.id]
                else:
                    # 如果不在字典中，尝试通过PID停止
                    try:
                        proc = psutil.Process(service.process_id)
                        proc.terminate()
                        proc.wait(timeout=5)
                    except psutil.NoSuchProcess:
                        pass
                    except psutil.TimeoutExpired:
                        proc.kill()
                    except Exception as e:
                        logger.warning(f"停止进程失败: {str(e)}")
            except Exception as e:
                logger.warning(f"停止进程失败: {str(e)}")

        service.status = 'stopped'
        service.process_id = None
        db.session.commit()

        logger.info(f"服务已停止: {service.service_name}")

        return jsonify({
            'code': 0,
            'msg': '服务停止成功',
            'data': service.to_dict()
        })

    except Exception as e:
        logger.error(f"停止服务失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 重启服务
@deploy_service_bp.route('/<int:service_id>/restart', methods=['POST'])
def restart_service(service_id):
    try:
        # 先停止
        stop_result = stop_service(service_id)
        if stop_result[0].get_json()['code'] != 0:
            return stop_result

        # 等待一下
        time.sleep(1)

        # 再启动
        return start_service(service_id)

    except Exception as e:
        logger.error(f"重启服务失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 查看日志
@deploy_service_bp.route('/<int:service_id>/logs', methods=['GET'])
def get_service_logs(service_id):
    try:
        service = AIService.query.get_or_404(service_id)
        
        lines = int(request.args.get('lines', 100))  # 默认返回最后100行
        
        if not service.log_path or not os.path.exists(service.log_path):
            return jsonify({
                'code': 404,
                'msg': '日志文件不存在'
            }), 404

        # 读取日志文件最后N行
        with open(service.log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            log_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'logs': ''.join(log_lines),
                'total_lines': len(all_lines)
            }
        })

    except Exception as e:
        logger.error(f"获取日志失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 接收心跳
@deploy_service_bp.route('/heartbeat', methods=['POST'])
def receive_heartbeat():
    try:
        data = request.get_json()
        service_name = data.get('service_name')
        service_id = data.get('service_id')  # 保留兼容性，优先使用 service_name
        model_id = data.get('model_id')  # 模型ID（可选）
        server_ip = data.get('server_ip')
        port = data.get('port')
        inference_endpoint = data.get('inference_endpoint')
        mac_address = data.get('mac_address')
        model_version = data.get('model_version')  # 模型版本（可选）
        format_type = data.get('format')  # 模型格式（可选）
        process_id = data.get('process_id')  # 进程ID（重要，需要上传）

        # 优先使用 service_name，如果没有则使用 service_id（向后兼容）
        if not service_name:
            if service_id:
                # 向后兼容：如果只有 service_id，尝试查找
                service = AIService.query.get(service_id)
                if not service:
                    return jsonify({
                        'code': 404,
                        'msg': '服务不存在，请提供 service_name'
                    }), 404
            else:
                return jsonify({
                    'code': 400,
                    'msg': '缺少必要参数：service_name 或 service_id'
                }), 400
        else:
            # 根据 service_name 查找或创建服务记录
            service = AIService.query.filter_by(service_name=service_name).first()
            
            if not service:
                # 如果服务不存在，自动创建新记录
                logger.info(f"服务 {service_name} 不存在，自动创建新记录")
                service = AIService(
                    service_name=service_name,
                    model_id=model_id if model_id else None,
                    server_ip=server_ip,
                    port=port,
                    inference_endpoint=inference_endpoint or (f"http://{server_ip}:{port}/inference" if server_ip and port else None),
                    mac_address=mac_address,
                    status='running',
                    deploy_time=beijing_now(),
                    model_version=model_version,
                    format=format_type,
                    process_id=process_id
                )
                db.session.add(service)
            else:
                # 如果服务存在，更新信息
                logger.debug(f"更新服务 {service_name} 的心跳信息")
                
                # 检查服务状态，如果状态是stopped，返回停止标识
                should_stop = (service.status == 'stopped')

        # 更新心跳信息
        service.last_heartbeat = beijing_now()
        if server_ip:
            service.server_ip = server_ip
        if port:
            service.port = port
        if inference_endpoint:
            service.inference_endpoint = inference_endpoint
        elif server_ip and port and not service.inference_endpoint:
            service.inference_endpoint = f"http://{server_ip}:{port}/inference"
        if mac_address:
            service.mac_address = mac_address
        if model_id and not service.model_id:
            # 如果原来没有 model_id，现在有，则更新
            service.model_id = model_id
        if model_version:
            service.model_version = model_version
        if format_type:
            service.format = format_type
        if process_id:
            service.process_id = process_id
        
        # 如果服务状态是stopped，保持stopped状态；否则更新为running
        if service.status == 'stopped':
            # 保持stopped状态，不更新
            pass
        else:
            # 统一改为running（兼容旧的online状态）
            service.status = 'running'

        db.session.commit()

        # 构建返回数据
        response_data = {
            'service_id': service.id,
            'service_name': service.service_name
        }
        
        # 如果服务状态是stopped，返回停止标识
        if service.status == 'stopped':
            response_data['should_stop'] = True

        return jsonify({
            'code': 0,
            'msg': '心跳接收成功',
            'data': response_data
        })

    except Exception as e:
        logger.error(f"接收心跳失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 删除服务
@deploy_service_bp.route('/<int:service_id>/delete', methods=['POST'])
def delete_service(service_id):
    try:
        service = AIService.query.get_or_404(service_id)
        service_name = service.service_name

        # 直接删除服务记录（不需要管理员权限）
        # 如果服务还活着，会通过heartbeat机制重新注册上来
        db.session.delete(service)
        db.session.commit()

        logger.info(f"服务已删除: {service_name}")

        return jsonify({
            'code': 0,
            'msg': '服务删除成功'
        })

    except Exception as e:
        logger.error(f"删除服务失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500

