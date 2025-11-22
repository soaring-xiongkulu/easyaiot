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


def create_systemd_service(ai_service, model_path, model_version, model_format):
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
            with open(systemd_service_path, 'w') as f:
                f.write(service_content)
            
            # 重新加载systemd
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            
            logger.info(f"Systemd服务文件已创建: {systemd_service_path}")
            return systemd_service_name
            
        except PermissionError:
            logger.error(f"没有权限创建systemd服务文件，需要root权限")
            return None
        except Exception as e:
            logger.error(f"创建systemd服务文件失败: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"创建systemd服务失败: {str(e)}")
        return None


def start_systemd_service(service_name):
    """启动systemd服务"""
    try:
        result = subprocess.run(
            ['systemctl', 'start', service_name],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Systemd服务已启动: {service_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"启动systemd服务失败: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"启动systemd服务异常: {str(e)}")
        return False


def stop_systemd_service(service_name):
    """停止systemd服务"""
    try:
        result = subprocess.run(
            ['systemctl', 'stop', service_name],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Systemd服务已停止: {service_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(f"停止systemd服务失败（可能服务未运行）: {e.stderr}")
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


def delete_systemd_service(service_name):
    """删除systemd服务"""
    try:
        # 先停止服务
        stop_systemd_service(service_name)
        
        # 禁用服务
        subprocess.run(['systemctl', 'disable', service_name], capture_output=True)
        
        # 删除服务文件
        service_path = os.path.join(SYSTEMD_SERVICE_DIR, service_name)
        if os.path.exists(service_path):
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
        
        # 创建日志目录（按servicename创建文件夹）
        log_base_dir = os.path.join('data', 'deploy_logs')
        log_dir = os.path.join(log_base_dir, service_name)
        os.makedirs(log_dir, exist_ok=True)
        # 日志路径指向目录，实际日志文件按日期创建
        log_path = log_dir

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
        deploy_service_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'services')
        deploy_script = os.path.join(deploy_service_dir, 'run_deploy.py')
        
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
            # 添加MODEL_VERSION和MODEL_FORMAT到环境变量
            env['MODEL_VERSION'] = model.version
            env['MODEL_FORMAT'] = model_format
            
            # 创建systemd service文件
            systemd_service_name = create_systemd_service(ai_service, model_path, model.version, model_format)
            
            if not systemd_service_name:
                ai_service.status = 'error'
                db.session.commit()
                return jsonify({
                    'code': 500,
                    'msg': '创建systemd服务失败，请检查是否有root权限'
                }), 500
            
            # 启动systemd服务
            if start_systemd_service(systemd_service_name):
                # 更新服务记录
                ai_service.status = 'running'
                # 不再存储process_id，因为由systemd管理
                ai_service.process_id = None
                db.session.commit()
                
                logger.info(f"部署服务已启动（systemd）: {service_name} on {server_ip}:{port}")
                
                return jsonify({
                    'code': 0,
                    'msg': '部署成功',
                    'data': ai_service.to_dict()
                })
            else:
                ai_service.status = 'error'
                db.session.commit()
                return jsonify({
                    'code': 500,
                    'msg': '启动systemd服务失败'
                }), 500

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

        # 获取模型版本和格式
        model_version = service.model_version or model.version
        model_format = service.format
        if not model_format:
            # 从模型路径推断格式
            model_path_lower = model_path.lower()
            if model_path_lower.endswith('.onnx') or 'onnx' in model_path_lower:
                model_format = 'onnx'
            elif model_path_lower.endswith(('.pt', '.pth')):
                model_format = 'pytorch'
            elif 'openvino' in model_path_lower:
                model_format = 'openvino'
            elif 'tensorrt' in model_path_lower:
                model_format = 'tensorrt'
            else:
                model_format = 'pytorch'
        
        # 日志路径
        if service.log_path:
            log_path = service.log_path
        else:
            log_base_dir = os.path.join('data', 'deploy_logs')
            log_path = os.path.join(log_base_dir, service.service_name)
            os.makedirs(log_path, exist_ok=True)
            service.log_path = log_path

        try:
            # 创建或更新systemd service文件
            systemd_service_name = create_systemd_service(service, model_path, model_version, model_format)
            
            if not systemd_service_name:
                service.status = 'error'
                db.session.commit()
                return jsonify({
                    'code': 500,
                    'msg': '创建systemd服务失败，请检查是否有root权限'
                }), 500
            
            # 启动systemd服务
            if start_systemd_service(systemd_service_name):
                service.status = 'running'
                service.process_id = None
                db.session.commit()
                
                logger.info(f"服务已启动（systemd）: {service.service_name} on {service.server_ip}:{service.port}")
                
                return jsonify({
                    'code': 0,
                    'msg': '服务启动成功',
                    'data': service.to_dict()
                })
            else:
                service.status = 'error'
                db.session.commit()
                return jsonify({
                    'code': 500,
                    'msg': '启动systemd服务失败'
                }), 500

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

        # 停止systemd服务
        systemd_service_name = f"{SYSTEMD_SERVICE_PREFIX}-{service.id}.service"
        stop_systemd_service(systemd_service_name)

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
        
        # 检查日志文件是否存在
        if not os.path.exists(log_file_path):
            return jsonify({
                'code': 404,
                'msg': f'日志文件不存在: {log_filename}'
            }), 404

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
                    format=format_type
                )
                db.session.add(service)
            else:
                # 如果服务存在，更新信息
                logger.debug(f"更新服务 {service_name} 的心跳信息")

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
        if service.status != 'running':
            service.status = 'running'

        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '心跳接收成功',
            'data': {
                'service_id': service.id,
                'service_name': service.service_name
            }
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
        
        # 如果服务正在运行，先停止
        if service.status == 'running':
            stop_service(service_id)

        # 删除systemd服务文件
        systemd_service_name = f"{SYSTEMD_SERVICE_PREFIX}-{service.id}.service"
        delete_systemd_service(systemd_service_name)

        # 删除服务记录
        db.session.delete(service)
        db.session.commit()

        logger.info(f"服务已删除: {service.service_name}")

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

