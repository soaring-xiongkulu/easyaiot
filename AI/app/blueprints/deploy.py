"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import os
import shlex
import socket
import subprocess
import threading
import time
import uuid
from datetime import datetime, timedelta

import psutil
import requests
from flask import Blueprint, request, jsonify
from sqlalchemy import desc

from db_models import db, Model, AIService, beijing_now

deploy_service_bp = Blueprint('deploy_service', __name__)
logger = logging.getLogger(__name__)

# 存储部署服务的进程信息（已废弃，改用systemd管理）
deploy_processes = {}

# Systemd服务文件目录
SYSTEMD_SERVICE_DIR = '/etc/systemd/system'
SYSTEMD_SERVICE_PREFIX = 'ai-deploy-service'


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


def kill_process(process_id):
    """杀死指定进程ID的进程"""
    try:
        if process_id:
            # 使用psutil检查进程是否存在
            if psutil.pid_exists(process_id):
                process = psutil.Process(process_id)
                process.kill()
                logger.info(f"已杀死进程: {process_id}")
                return True
            else:
                logger.warning(f"进程不存在: {process_id}")
                return False
        return False
    except psutil.NoSuchProcess:
        logger.warning(f"进程不存在: {process_id}")
        return False
    except psutil.AccessDenied:
        logger.error(f"没有权限杀死进程: {process_id}")
        return False
    except Exception as e:
        logger.error(f"杀死进程失败: {process_id}, 错误: {str(e)}")
        return False


def run_with_sudo(command, root_password=None):
    """使用sudo或su执行命令（如果需要）"""
    if root_password:
        # 使用su执行命令，通过stdin传递root密码
        # 使用shlex.quote安全地转义命令参数
        cmd_str = ' '.join(shlex.quote(arg) for arg in command)
        process = subprocess.Popen(
            ['su', '-c', cmd_str, 'root'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=root_password + '\n')
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command, stdout, stderr)
        return stdout
    else:
        # 直接执行命令
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout


def verify_sudo_permission(root_password=None):
    """
    验证sudo权限或root密码是否正确
    返回: (success: bool, error_msg: str)
    """
    try:
        # 先检查是否有sudo权限（不需要密码）
        try:
            result = subprocess.run(
                ['sudo', '-n', 'echo', 'test'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # 有sudo权限且不需要密码
                return True, None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # sudo命令不存在或超时，继续检查
            pass
        
        # 检查是否有权限直接写入systemd目录（可能是root用户）
        test_path = os.path.join(SYSTEMD_SERVICE_DIR, '.test_write_permission')
        try:
            with open(test_path, 'w') as f:
                f.write('test')
            os.remove(test_path)
            # 如果能直接写入，说明有权限（可能是root用户）
            return True, None
        except PermissionError:
            # 如果没有直接权限，需要验证root密码
            if root_password:
                try:
                    # 使用su尝试一个简单的命令来验证密码
                    process = subprocess.Popen(
                        ['su', '-c', 'echo test', 'root'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate(input=root_password + '\n', timeout=5)
                    if process.returncode == 0:
                        return True, None
                    else:
                        # 检查是否是密码错误
                        error_lower = stderr.lower()
                        if 'authentication failure' in error_lower or '认证失败' in error_lower or '密码不正确' in error_lower or 'incorrect password' in error_lower:
                            return False, 'root密码错误'
                        else:
                            return False, f'权限验证失败: {stderr.strip()}'
                except subprocess.TimeoutExpired:
                    process.kill()
                    return False, '权限验证超时'
                except Exception as e:
                    return False, f'权限验证异常: {str(e)}'
            else:
                return False, '没有sudo权限且未提供root密码'
    except Exception as e:
        logger.error(f"验证sudo权限失败: {str(e)}")
        return False, f'验证sudo权限失败: {str(e)}'


def create_systemd_service(ai_service, model_path, model_version, model_format, root_password=None):
    """创建systemd service文件"""
    try:
        # 获取当前用户和组
        import pwd
        import grp
        current_user = os.getenv('USER', 'root')
        try:
            user_info = pwd.getpwnam(current_user)
            user = current_user
            group = grp.getgrgid(user_info.pw_gid).gr_name
        except:
            user = 'root'
            group = 'root'
        
        # 获取Python路径
        python_path = subprocess.check_output(['which', 'python3']).decode().strip()
        if not python_path:
            python_path = subprocess.check_output(['which', 'python']).decode().strip()
        
        # 获取服务脚本路径
        deploy_service_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'services')
        script_path = os.path.join(deploy_service_dir, 'run_deploy.py')
        
        # 服务名（用于systemd service文件名）
        systemd_service_name = f"{SYSTEMD_SERVICE_PREFIX}-{ai_service.id}.service"
        systemd_service_path = os.path.join(SYSTEMD_SERVICE_DIR, systemd_service_name)
        
        # 读取模板文件
        template_path = os.path.join(deploy_service_dir, 'deploy_service_template.service')
        if not os.path.exists(template_path):
            logger.error(f"Systemd服务模板文件不存在: {template_path}")
            return None
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # 替换模板变量
        log_file = os.path.join(ai_service.log_path, f"{ai_service.service_name}_all.log")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        service_content = template_content.format(
            SERVICE_NAME=ai_service.service_name,
            USER=user,
            GROUP=group,
            WORKING_DIR=deploy_service_dir,
            MODEL_ID=str(ai_service.model_id),
            MODEL_PATH=model_path,
            SERVICE_ID=str(ai_service.id),
            SERVICE_NAME_VAR=ai_service.service_name,
            PORT=str(ai_service.port),
            SERVER_IP=ai_service.server_ip,
            LOG_PATH=ai_service.log_path,
            MODEL_VERSION=model_version,
            MODEL_FORMAT=model_format,
            NACOS_SERVER=os.getenv('NACOS_SERVER', 'localhost:8848'),
            NACOS_NAMESPACE=os.getenv('NACOS_NAMESPACE', ''),
            NACOS_USERNAME=os.getenv('NACOS_USERNAME', 'nacos'),
            NACOS_PASSWORD=os.getenv('NACOS_PASSWORD', 'basiclab@iot78475418754'),
            AI_SERVICE_NAME=os.getenv('SERVICE_NAME', 'model-server'),
            PYTHON_PATH=python_path,
            SCRIPT_PATH=script_path,
            LOG_FILE=log_file
        )
        
        # 写入systemd service文件（需要root权限）
        try:
            # 先尝试直接写入
            with open(systemd_service_path, 'w') as f:
                f.write(service_content)
            
            # 重新加载systemd
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            
            logger.info(f"Systemd服务文件已创建: {systemd_service_path}")
            return systemd_service_name
            
        except PermissionError:
            # 如果没有权限且提供了root密码，使用su
            if root_password:
                try:
                    # 使用su写入文件，先通过echo写入临时文件，然后移动
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.service') as tmp_file:
                        tmp_file.write(service_content)
                        tmp_path = tmp_file.name
                    
                    try:
                        # 使用su执行命令移动文件
                        cmd = f"mv {shlex.quote(tmp_path)} {shlex.quote(systemd_service_path)}"
                        process = subprocess.Popen(
                            ['su', '-c', cmd, 'root'],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        stdout, stderr = process.communicate(input=root_password + '\n')
                        if process.returncode != 0:
                            logger.error(f"使用su创建systemd服务文件失败: {stderr}")
                            os.unlink(tmp_path)
                            return None
                        
                        # 设置文件权限
                        run_with_sudo(['chmod', '644', systemd_service_path], root_password)
                        
                        # 使用su重新加载systemd
                        run_with_sudo(['systemctl', 'daemon-reload'], root_password)
                        
                        logger.info(f"Systemd服务文件已创建（使用su）: {systemd_service_path}")
                        return systemd_service_name
                    except Exception as e:
                        # 清理临时文件
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass
                        raise e
                except Exception as e:
                    logger.error(f"使用su创建systemd服务文件失败: {str(e)}")
                    return None
            else:
                logger.error(f"没有权限创建systemd服务文件，需要root权限")
                return None
        except Exception as e:
            logger.error(f"创建systemd服务文件失败: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"创建systemd服务失败: {str(e)}")
        return None


def start_systemd_service(service_name, root_password=None):
    """启动systemd服务"""
    try:
        if root_password:
            run_with_sudo(['systemctl', 'start', service_name], root_password)
        else:
            subprocess.run(
                ['systemctl', 'start', service_name],
                capture_output=True,
                text=True,
                check=True
            )
        logger.info(f"Systemd服务已启动: {service_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"启动systemd服务失败: {e.stderr if hasattr(e, 'stderr') else str(e)}")
        return False
    except Exception as e:
        logger.error(f"启动systemd服务异常: {str(e)}")
        return False


def stop_systemd_service(service_name, root_password=None):
    """停止systemd服务"""
    try:
        if root_password:
            run_with_sudo(['systemctl', 'stop', service_name], root_password)
        else:
            subprocess.run(
                ['systemctl', 'stop', service_name],
                capture_output=True,
                text=True,
                check=True
            )
        logger.info(f"Systemd服务已停止: {service_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(f"停止systemd服务失败（可能服务未运行）: {e.stderr if hasattr(e, 'stderr') else str(e)}")
        return False
    except Exception as e:
        logger.error(f"停止systemd服务异常: {str(e)}")
        return False


def get_systemd_service_status(service_name):
    """获取systemd服务状态"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == 'active'
    except Exception as e:
        logger.error(f"获取systemd服务状态失败: {str(e)}")
        return False


def delete_systemd_service(service_name, root_password=None):
    """删除systemd服务"""
    try:
        # 先停止服务
        stop_systemd_service(service_name, root_password)
        
        # 禁用服务
        if root_password:
            run_with_sudo(['systemctl', 'disable', service_name], root_password)
        else:
            subprocess.run(['systemctl', 'disable', service_name], capture_output=True)
        
        # 删除服务文件
        service_path = os.path.join(SYSTEMD_SERVICE_DIR, service_name)
        if os.path.exists(service_path):
            if root_password:
                # 使用sudo删除文件
                run_with_sudo(['rm', '-f', service_path], root_password)
                run_with_sudo(['systemctl', 'daemon-reload'], root_password)
            else:
                os.remove(service_path)
                subprocess.run(['systemctl', 'daemon-reload'], check=True)
            logger.info(f"Systemd服务文件已删除: {service_path}")
        
        return True
    except Exception as e:
        logger.error(f"删除systemd服务失败: {str(e)}")
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
        
        # 支持状态过滤：running/offline/stopped/error
        if status_filter in ['offline', 'stopped', 'running', 'error']:
            # 兼容旧的状态值：online -> running, error -> offline
            if status_filter == 'running':
                query = query.filter(AIService.status.in_(['running', 'online']))
            elif status_filter == 'error':
                query = query.filter(AIService.status.in_(['offline', 'error']))
            else:
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
        start_port = int(data.get('start_port', 8000))
        root_password = data.get('root_password')  # 必填的root密码

        if not model_id:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：model_id'
            }), 400

        # 检查root密码是否提供
        if not root_password or not root_password.strip():
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：root_password（Root密码为必填项）'
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

        # 生成唯一的服务名称（确保不重复）
        max_attempts = 10
        for attempt in range(max_attempts):
            if attempt == 0:
                service_name = f"{model.name}_{model.version}_{int(time.time())}"
            else:
                # 如果已存在，添加随机后缀
                service_name = f"{model.name}_{model.version}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # 检查服务名称是否已存在
            existing_service = AIService.query.filter_by(service_name=service_name).first()
            if not existing_service:
                break
        else:
            # 如果尝试多次后仍然冲突，使用UUID
            service_name = uuid.uuid4().hex

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
        
        # 创建日志目录（按servicename创建文件夹）
        log_base_dir = os.path.join('data', 'deploy_logs')
        log_dir = os.path.join(log_base_dir, service_name)
        os.makedirs(log_dir, exist_ok=True)
        # 日志路径指向目录，实际日志文件按日期创建
        log_path = log_dir

        # 在创建服务记录之前，先验证sudo权限或root密码
        # 这样可以避免在权限验证失败时创建无用的服务记录
        deploy_service_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'services')
        deploy_script = os.path.join(deploy_service_dir, 'run_deploy.py')
        
        if os.path.exists(deploy_script):
            # 只有部署脚本存在时才需要验证权限（因为需要创建systemd服务）
            verify_success, verify_error = verify_sudo_permission(root_password)
            if not verify_success:
                # 权限验证失败，不创建服务记录，直接返回错误
                # verify_error 已经包含了具体的错误信息（如"root密码错误"）
                return jsonify({
                    'code': 403,
                    'msg': verify_error or '创建systemd服务失败，需要root权限。请提供正确的root密码后重试。'
                }), 403

        # 创建部署服务记录（只有在权限验证通过后才创建）
        ai_service = AIService(
            model_id=model_id,
            service_name=service_name,
            server_ip=server_ip,
            port=port,
            inference_endpoint=f"http://{server_ip}:{port}/inference",
            status='offline',
            mac_address=mac_address,
            deploy_time=beijing_now(),
            log_path=log_path,
            model_version=model.version,
            format=model_format
        )
        db.session.add(ai_service)
        db.session.commit()
        
        if not os.path.exists(deploy_script):
            # 如果部署脚本不存在，先创建服务记录，稍后可以手动启动
            logger.warning(f"部署脚本不存在: {deploy_script}，服务记录已创建但未启动")
            return jsonify({
                'code': 0,
                'msg': '服务记录已创建，但部署脚本不存在，请检查部署服务目录',
                'data': ai_service.to_dict()
            })

        # 创建systemd服务并启动
        try:
            # 创建systemd service文件（MODEL_VERSION和MODEL_FORMAT已在create_systemd_service中通过模板设置）
            systemd_service_name = create_systemd_service(ai_service, model_path, model.version, model_format, root_password)
            
            if not systemd_service_name:
                ai_service.status = 'offline'
                db.session.commit()
                # 如果是因为权限问题失败，返回特定错误码
                return jsonify({
                    'code': 403,
                    'msg': '创建systemd服务失败，需要root权限。请提供root密码后重试。'
                }), 403
            
            # 启动systemd服务
            if start_systemd_service(systemd_service_name, root_password):
                # 更新服务记录，状态会在心跳上报时更新为running
                ai_service.status = 'offline'  # 初始状态，等待心跳上报后变为running
                # process_id会在心跳上报时更新
                db.session.commit()
                
                logger.info(f"部署服务已启动（systemd）: {service_name} on {server_ip}:{port}")
                
                return jsonify({
                    'code': 0,
                    'msg': '部署成功',
                    'data': ai_service.to_dict()
                })
            else:
                ai_service.status = 'offline'
                db.session.commit()
                return jsonify({
                    'code': 500,
                    'msg': '启动systemd服务失败'
                }), 500

        except Exception as e:
            logger.error(f"启动部署服务失败: {str(e)}")
            ai_service.status = 'offline'
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
        
        # 检查模型id是否存在
        if not service.model_id:
            return jsonify({
                'code': 400,
                'msg': '服务未关联模型，无法启动。请先为服务关联模型或通过心跳上报 model_id'
            }), 400

        model = Model.query.get(service.model_id)
        if not model:
            return jsonify({
                'code': 404,
                'msg': '模型不存在'
            }), 404

        # 使用相同的模型和servicename重新拉起来进程，再走一遍部署流程
        # 检查模型路径并推断格式
        model_path = model.model_path or model.onnx_model_path or model.torchscript_model_path or model.tensorrt_model_path or model.openvino_model_path
        if not model_path:
            return jsonify({
                'code': 400,
                'msg': '模型没有可用的模型文件路径'
            }), 400

        # 推断模型格式
        model_format = service.format
        if not model_format:
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

        # 获取模型版本
        model_version = service.model_version or model.version

        # 检查端口是否可用，如果被占用则找新端口
        if service.port and not check_port_available('0.0.0.0', service.port):
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
        elif not service.port:
            # 如果没有端口，分配一个新端口
            port = find_available_port(8000)
            if not port:
                return jsonify({
                    'code': 500,
                    'msg': '无法找到可用端口'
                }), 500
            service.port = port
            service.inference_endpoint = f"http://{service.server_ip}:{port}/inference"

        # 确保日志目录存在
        if service.log_path:
            log_path = service.log_path
        else:
            log_base_dir = os.path.join('data', 'deploy_logs')
            log_path = os.path.join(log_base_dir, service.service_name)
            os.makedirs(log_path, exist_ok=True)
            service.log_path = log_path

        # 获取root密码（如果提供）
        data = request.get_json() or {}
        root_password = data.get('root_password')
        
        # 在创建systemd服务之前，先验证sudo权限或root密码
        deploy_service_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'services')
        deploy_script = os.path.join(deploy_service_dir, 'run_deploy.py')
        
        if os.path.exists(deploy_script):
            verify_success, verify_error = verify_sudo_permission(root_password)
            if not verify_success:
                return jsonify({
                    'code': 403,
                    'msg': verify_error or '创建systemd服务失败，需要root权限。请提供正确的root密码后重试。'
                }), 403

        # 创建或更新systemd service文件
        systemd_service_name = create_systemd_service(service, model_path, model_version, model_format, root_password)
        
        if not systemd_service_name:
            service.status = 'offline'
            db.session.commit()
            return jsonify({
                'code': 403,
                'msg': '创建systemd服务失败，需要root权限。请提供root密码后重试。'
            }), 403
        
        # 启动systemd服务
        if start_systemd_service(systemd_service_name, root_password):
            service.status = 'running'
            # process_id会在心跳上报时更新
            db.session.commit()
            
            logger.info(f"服务已启动（systemd）: {service.service_name} on {service.server_ip}:{service.port}")
            
            return jsonify({
                'code': 0,
                'msg': '服务启动成功',
                'data': service.to_dict()
            })
        else:
            service.status = 'offline'
            db.session.commit()
            return jsonify({
                'code': 500,
                'msg': '启动systemd服务失败'
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
        
        # 如果服务不在线，不需要停止
        if service.status != 'running':
            return jsonify({
                'code': 400,
                'msg': '服务未在线，无需停止'
            }), 400

        # 如果有process_id，尝试杀死进程
        if service.process_id:
            kill_process(service.process_id)

        # 更新状态为停止，下次心跳回复停止标识，让服务自己杀掉process_id进程
        service.status = 'stopped'
        db.session.commit()

        logger.info(f"服务已停止: {service.service_name}, process_id: {service.process_id}")

        return jsonify({
            'code': 0,
            'msg': '服务停止成功',
            'data': {
                'should_stop': True,  # 停止标识，让服务自己杀掉process_id进程
                'service': service.to_dict()
            }
        })

    except Exception as e:
        logger.error(f"停止服务失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500




# 查看日志
@deploy_service_bp.route('/<int:service_id>/logs', methods=['GET'])
def get_service_logs(service_id):
    """
    查看服务日志
    支持参数：
    - lines: 返回的行数（默认100）
    - date: 指定日期查看（格式：YYYY-MM-DD），不指定则查看 all 文件
    """
    try:
        service = AIService.query.get_or_404(service_id)
        
        lines = int(request.args.get('lines', 100))  # 默认返回最后100行
        date = request.args.get('date', '').strip()  # 可选：指定日期
        
        # 确定日志文件路径
        if not service.log_path:
            # 如果服务记录中没有日志路径，使用默认路径
            log_base_dir = os.path.join('data', 'deploy_logs')
            service_log_dir = os.path.join(log_base_dir, service.service_name)
        else:
            service_log_dir = service.log_path
        
        # 根据参数选择日志文件
        if date:
            # 查看指定日期的日志文件
            log_filename = f"{service.service_name}_{date}.log"
            log_file_path = os.path.join(service_log_dir, log_filename)
        else:
            # 默认查看 all 文件
            log_filename = f"{service.service_name}_all.log"
            log_file_path = os.path.join(service_log_dir, log_filename)
        
        # 检查日志文件是否存在，如果不存在则返回空日志
        if not os.path.exists(log_file_path):
            # 如果日志文件不存在，返回空日志而不是404错误
            logger.warning(f"日志文件不存在: {log_file_path}，返回空日志")
            return jsonify({
                'code': 0,
                'msg': 'success',
                'data': {
                    'logs': f'日志文件不存在: {log_filename}\n请等待服务运行后生成日志。',
                    'total_lines': 0,
                    'log_file': log_filename,
                    'is_all_file': not bool(date)
                }
            })

        # 读取日志文件最后N行
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                log_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

            return jsonify({
                'code': 0,
                'msg': 'success',
                'data': {
                    'logs': ''.join(log_lines),
                    'total_lines': len(all_lines),
                    'log_file': log_filename,
                    'is_all_file': not bool(date)
                }
            })
        except Exception as e:
            logger.error(f"读取日志文件失败: {str(e)}")
            return jsonify({
                'code': 500,
                'msg': f'读取日志文件失败: {str(e)}'
            }), 500

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


# 接收日志上报
@deploy_service_bp.route('/logs', methods=['POST'])
def receive_logs():
    """接收来自部署服务的日志上报，按servicename创建文件夹存储日志"""
    try:
        data = request.get_json()
        service_name = data.get('service_name')
        log_content = data.get('log')
        log_level = data.get('level', 'INFO')
        timestamp = data.get('timestamp')
        
        if not service_name or not log_content:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：service_name 或 log'
            }), 400
        
        # 按servicename创建日志目录
        # 日志目录结构：data/deploy_logs/{service_name}/
        log_base_dir = os.path.join('data', 'deploy_logs')
        service_log_dir = os.path.join(log_base_dir, service_name)
        os.makedirs(service_log_dir, exist_ok=True)
        
        # 按日期创建日志文件，格式：{service_name}_YYYY-MM-DD.log
        log_date = datetime.now().strftime('%Y-%m-%d')
        log_filename = f"{service_name}_{log_date}.log"
        log_file_path = os.path.join(service_log_dir, log_filename)
        
        # all 日志文件路径
        all_log_filename = f"{service_name}_all.log"
        all_log_file_path = os.path.join(service_log_dir, all_log_filename)
        
        # 构建日志行
        log_line = f"[{timestamp or datetime.now().isoformat()}] [{log_level}] {log_content}\n"
        
        # 将日志同时写入日期文件和 all 文件
        try:
            # 写入日期文件
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
                f.flush()  # 确保立即写入
            
            # 写入 all 文件
            with open(all_log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
                f.flush()  # 确保立即写入
        except Exception as e:
            logger.error(f"写入日志文件失败: {str(e)}")
            return jsonify({
                'code': 500,
                'msg': f'写入日志文件失败: {str(e)}'
            }), 500
        
        # 查找服务记录（如果存在），更新log_path
        service = AIService.query.filter_by(service_name=service_name).first()
        if service:
            # 更新服务的日志路径（指向目录，而不是单个文件）
            if not service.log_path or service.log_path != service_log_dir:
                service.log_path = service_log_dir
                db.session.commit()
        
        # 同时记录到主程序日志
        if log_level == 'ERROR':
            logger.error(f"[{service_name}] {log_content}")
        elif log_level == 'WARNING':
            logger.warning(f"[{service_name}] {log_content}")
        else:
            logger.info(f"[{service_name}] {log_content}")
        
        return jsonify({
            'code': 0,
            'msg': '日志接收成功',
            'data': {
                'date_log_file': log_file_path,
                'all_log_file': all_log_file_path
            }
        })
        
    except Exception as e:
        logger.error(f"接收日志失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


def check_heartbeat_timeout(app):
    """定时检查心跳超时，超过1分钟没上报则更新状态为离线"""
    try:
        with app.app_context():
            # 计算1分钟前的时间
            timeout_threshold = beijing_now() - timedelta(minutes=1)
            
            # 查找所有运行中状态但心跳超时的服务
            timeout_services = AIService.query.filter(
                AIService.status.in_(['running', 'online']),  # 兼容旧的online状态
                (AIService.last_heartbeat < timeout_threshold) | (AIService.last_heartbeat.is_(None))
            ).all()
            
            for service in timeout_services:
                # 更新状态为离线
                old_status = service.status
                service.status = 'offline'
                logger.info(f"服务心跳超时，状态从 {old_status} 更新为 offline: {service.service_name}")
            
            if timeout_services:
                db.session.commit()
                logger.info(f"已更新 {len(timeout_services)} 个服务状态为离线")
    except Exception as e:
        logger.error(f"检查心跳超时失败: {str(e)}")
        try:
            db.session.rollback()
        except:
            pass


def start_heartbeat_checker(app):
    """启动心跳检查定时任务"""
    def checker_loop():
        while True:
            try:
                check_heartbeat_timeout(app)
            except Exception as e:
                logger.error(f"心跳检查任务异常: {str(e)}")
            time.sleep(30)  # 每30秒检查一次
    
    checker_thread = threading.Thread(target=checker_loop, daemon=True)
    checker_thread.start()
    logger.info("心跳超时检查任务已启动（每30秒检查一次）")

