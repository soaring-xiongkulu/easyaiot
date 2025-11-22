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

        # 构建查询
        query = db.session.query(AIService, Model.name.label('model_name')).join(
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
            service_dict['model_name'] = model_name
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

        env = os.environ.copy()
        env['MODEL_ID'] = str(service.model_id)
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
        service_id = data.get('service_id')
        server_ip = data.get('server_ip')
        port = data.get('port')
        inference_endpoint = data.get('inference_endpoint')
        mac_address = data.get('mac_address')

        if not service_id:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：service_id'
            }), 400

        service = AIService.query.get(service_id)
        if not service:
            return jsonify({
                'code': 404,
                'msg': '服务不存在'
            }), 404

        # 更新心跳信息
        service.last_heartbeat = beijing_now()
        if server_ip:
            service.server_ip = server_ip
        if port:
            service.port = port
        if inference_endpoint:
            service.inference_endpoint = inference_endpoint
        if mac_address:
            service.mac_address = mac_address
        if service.status != 'running':
            service.status = 'running'

        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '心跳接收成功'
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

