"""
模型部署服务路由
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy import desc

from db_models import db, Model, AIService, beijing_now
from app.services.deploy_service import (
    deploy_model,
    start_service,
    stop_service,
    restart_service,
    delete_service,
    get_service_logs
)

deploy_service_bp = Blueprint('deploy_service', __name__)
logger = logging.getLogger(__name__)


# 部署服务列表查询（按service_name分组）
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

        # 构建基础查询（使用 LEFT JOIN 支持 model_id 为空的情况）
        base_query = db.session.query(AIService, Model.name.label('model_name')).outerjoin(
            Model, AIService.model_id == Model.id
        )

        # 应用过滤条件
        if model_id:
            try:
                model_id_int = int(model_id)
                base_query = base_query.filter(AIService.model_id == model_id_int)
            except ValueError:
                pass
        
        if server_ip:
            base_query = base_query.filter(AIService.server_ip.ilike(f'%{server_ip}%'))
        
        # 支持状态过滤：running/offline/stopped/error
        if status_filter in ['offline', 'stopped', 'running', 'error']:
            if status_filter == 'running':
                base_query = base_query.filter(AIService.status.in_(['running', 'online']))
            elif status_filter == 'error':
                base_query = base_query.filter(AIService.status.in_(['offline', 'error']))
            else:
                base_query = base_query.filter(AIService.status == status_filter)

        # 获取所有符合条件的服务
        all_services = base_query.all()
        
        # 按service_name分组
        grouped_services = {}
        for service, model_name in all_services:
            service_name = service.service_name
            if service_name not in grouped_services:
                grouped_services[service_name] = {
                    'services': [],
                    'model_name': model_name
                }
            grouped_services[service_name]['services'].append((service, model_name))
        
        # 为每个service_name生成一条合并记录
        merged_records = []
        for service_name, group_data in grouped_services.items():
            services_list = group_data['services']
            model_name = group_data['model_name']
            
            # 使用第一个服务作为主记录（按创建时间倒序，取最新的）
            services_list.sort(key=lambda x: x[0].created_at if x[0].created_at else datetime.min, reverse=True)
            main_service, _ = services_list[0]
            
            # 计算副本数
            replica_count = len(services_list)
            
            # 计算聚合状态：如果有任何一个running，则显示running；否则显示stopped
            statuses = [s[0].status for s in services_list]
            if 'running' in statuses:
                aggregated_status = 'running'
            elif 'offline' in statuses:
                aggregated_status = 'offline'
            elif 'error' in statuses:
                aggregated_status = 'error'
            else:
                aggregated_status = 'stopped'
            
            # 构建合并后的记录
            service_dict = main_service.to_dict()
            service_dict['model_name'] = model_name if model_name else None
            service_dict['replica_count'] = replica_count
            service_dict['status'] = aggregated_status
            
            # 如果服务记录中没有版本和格式，从Model表获取
            if not service_dict.get('model_version'):
                model = Model.query.get(main_service.model_id)
                if model:
                    service_dict['model_version'] = model.version
            if not service_dict.get('format'):
                model = Model.query.get(main_service.model_id)
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
            
            merged_records.append(service_dict)
        
        # 按创建时间倒序排序
        merged_records.sort(key=lambda x: x.get('created_at') or '', reverse=True)
        
        # 手动分页
        total = len(merged_records)
        start_idx = (page_no - 1) * page_size
        end_idx = start_idx + page_size
        paginated_records = merged_records[start_idx:end_idx]

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': paginated_records,
            'total': total
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
def deploy_model_route():
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        start_port = int(data.get('start_port', 8000))

        if not model_id:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：model_id'
            }), 400

        result = deploy_model(model_id, start_port)
        return jsonify(result)

    except ValueError as e:
        return jsonify({
            'code': 400,
            'msg': str(e)
        }), 400
    except Exception as e:
        logger.error(f"部署模型失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 启动服务
@deploy_service_bp.route('/<int:service_id>/start', methods=['POST'])
def start_service_route(service_id):
    try:
        result = start_service(service_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({
            'code': 400,
            'msg': str(e)
        }), 400
    except Exception as e:
        logger.error(f"启动服务失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 停止服务
@deploy_service_bp.route('/<int:service_id>/stop', methods=['POST'])
def stop_service_route(service_id):
    try:
        result = stop_service(service_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({
            'code': 400,
            'msg': str(e)
        }), 400
    except Exception as e:
        logger.error(f"停止服务失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 重启服务
@deploy_service_bp.route('/<int:service_id>/restart', methods=['POST'])
def restart_service_route(service_id):
    try:
        result = restart_service(service_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({
            'code': 400,
            'msg': str(e)
        }), 400
    except Exception as e:
        logger.error(f"重启服务失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 查看日志
@deploy_service_bp.route('/<int:service_id>/logs', methods=['GET'])
def get_service_logs_route(service_id):
    try:
        lines = int(request.args.get('lines', 100))
        date = request.args.get('date', '').strip()
        
        result = get_service_logs(service_id, lines, date if date else None)
        return jsonify(result)
    except ValueError as e:
        return jsonify({
            'code': 400,
            'msg': str(e)
        }), 400
    except Exception as e:
        logger.error(f"获取日志失败: {str(e)}", exc_info=True)
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
        service_id = data.get('service_id')
        model_id = data.get('model_id')
        server_ip = data.get('server_ip')
        port = data.get('port')
        inference_endpoint = data.get('inference_endpoint')
        mac_address = data.get('mac_address')
        model_version = data.get('model_version')
        format_type = data.get('format')
        process_id = data.get('process_id')

        # 优先使用 service_id 查找服务（最准确）
        service = None
        if service_id:
            service = AIService.query.get(service_id)
            if service:
                logger.info(f"通过 service_id={service_id} 找到已有服务: {service.service_name}")
        
        # 如果没有 service_id，尝试通过 service_name + server_ip + port 组合查找（更精确）
        if not service and service_name and server_ip and port:
            service = AIService.query.filter_by(
                service_name=service_name,
                server_ip=server_ip,
                port=port
            ).first()
            if service:
                logger.info(f"通过 service_name={service_name}, server_ip={server_ip}, port={port} 找到已有服务")
        
        # 如果仍然找不到，尝试仅通过 service_name 查找（兼容旧逻辑）
        if not service and service_name:
            service = AIService.query.filter_by(service_name=service_name).first()
            if service:
                logger.warning(f"通过 service_name={service_name} 找到服务，但可能存在多个同名服务，建议使用 service_id 或 server_ip+port 组合")
        
        # 如果仍然找不到服务，创建新记录（这种情况应该很少见，因为服务应该先创建记录再启动）
        if not service:
            if not service_name:
                # 如果没有 service_name 也没有 service_id，无法创建新记录
                return jsonify({
                    'code': 400,
                    'msg': '缺少必要参数：service_name 或 service_id'
                }), 400
            
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

        # 更新心跳信息
        service.last_heartbeat = beijing_now()
        
        # 更新 service_name（如果提供了新的 service_name 且与数据库中的不同）
        if service_name and service.service_name != service_name:
            # 检查新的 service_name 是否已被其他服务使用
            existing_service = AIService.query.filter_by(service_name=service_name).first()
            if existing_service and existing_service.id != service.id:
                logger.warning(f"service_name {service_name} 已被服务 ID {existing_service.id} 使用，无法更新服务 ID {service.id} 的 service_name")
            else:
                logger.info(f"更新服务 ID {service.id} 的 service_name: {service.service_name} -> {service_name}")
                service.service_name = service_name
        
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
            service.model_id = model_id
        if model_version:
            service.model_version = model_version
        if format_type:
            service.format = format_type
        if process_id:
            service.process_id = process_id
        
        # 更新日志路径（如果提供了LOG_PATH环境变量，或者根据服务ID生成）
        log_path = data.get('log_path')
        if log_path:
            service.log_path = log_path
        elif not service.log_path:
            # 如果没有log_path，根据服务ID生成
            import os
            ai_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            log_base_dir = os.path.join(ai_root, 'logs')
            service.log_path = os.path.join(log_base_dir, str(service.id))
        
        # 如果服务状态是stopped，保持stopped状态；否则更新为running
        if service.status != 'stopped':
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
        logger.error(f"接收心跳失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 删除服务
@deploy_service_bp.route('/<int:service_id>/delete', methods=['POST'])
def delete_service_route(service_id):
    try:
        result = delete_service(service_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({
            'code': 400,
            'msg': str(e)
        }), 400
    except Exception as e:
        logger.error(f"删除服务失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 批量启动服务（按service_name）
@deploy_service_bp.route('/batch/start', methods=['POST'])
def batch_start_service_route():
    try:
        data = request.get_json()
        service_name = data.get('service_name')
        
        if not service_name:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：service_name'
            }), 400
        
        # 查找所有相同service_name的服务
        services = AIService.query.filter_by(service_name=service_name).all()
        if not services:
            return jsonify({
                'code': 404,
                'msg': f'未找到服务: {service_name}'
            }), 404
        
        # 批量启动
        success_count = 0
        fail_count = 0
        errors = []
        
        for service in services:
            try:
                result = start_service(service.id)
                if result.get('code') == 0:
                    success_count += 1
                else:
                    fail_count += 1
                    errors.append(f"服务ID {service.id}: {result.get('msg', '启动失败')}")
            except Exception as e:
                fail_count += 1
                errors.append(f"服务ID {service.id}: {str(e)}")
        
        return jsonify({
            'code': 0,
            'msg': f'批量启动完成：成功 {success_count} 个，失败 {fail_count} 个',
            'data': {
                'success_count': success_count,
                'fail_count': fail_count,
                'errors': errors
            }
        })
        
    except Exception as e:
        logger.error(f"批量启动服务失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 批量停止服务（按service_name）
@deploy_service_bp.route('/batch/stop', methods=['POST'])
def batch_stop_service_route():
    try:
        data = request.get_json()
        service_name = data.get('service_name')
        
        if not service_name:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：service_name'
            }), 400
        
        # 查找所有相同service_name的服务
        services = AIService.query.filter_by(service_name=service_name).all()
        if not services:
            return jsonify({
                'code': 404,
                'msg': f'未找到服务: {service_name}'
            }), 404
        
        # 批量停止
        success_count = 0
        fail_count = 0
        errors = []
        
        for service in services:
            try:
                result = stop_service(service.id)
                if result.get('code') == 0:
                    success_count += 1
                else:
                    fail_count += 1
                    errors.append(f"服务ID {service.id}: {result.get('msg', '停止失败')}")
            except Exception as e:
                fail_count += 1
                errors.append(f"服务ID {service.id}: {str(e)}")
        
        return jsonify({
            'code': 0,
            'msg': f'批量停止完成：成功 {success_count} 个，失败 {fail_count} 个',
            'data': {
                'success_count': success_count,
                'fail_count': fail_count,
                'errors': errors
            }
        })
        
    except Exception as e:
        logger.error(f"批量停止服务失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 批量重启服务（按service_name）
@deploy_service_bp.route('/batch/restart', methods=['POST'])
def batch_restart_service_route():
    try:
        data = request.get_json()
        service_name = data.get('service_name')
        
        if not service_name:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：service_name'
            }), 400
        
        # 查找所有相同service_name的服务
        services = AIService.query.filter_by(service_name=service_name).all()
        if not services:
            return jsonify({
                'code': 404,
                'msg': f'未找到服务: {service_name}'
            }), 404
        
        # 批量重启
        success_count = 0
        fail_count = 0
        errors = []
        
        for service in services:
            try:
                result = restart_service(service.id)
                if result.get('code') == 0:
                    success_count += 1
                else:
                    fail_count += 1
                    errors.append(f"服务ID {service.id}: {result.get('msg', '重启失败')}")
            except Exception as e:
                fail_count += 1
                errors.append(f"服务ID {service.id}: {str(e)}")
        
        return jsonify({
            'code': 0,
            'msg': f'批量重启完成：成功 {success_count} 个，失败 {fail_count} 个',
            'data': {
                'success_count': success_count,
                'fail_count': fail_count,
                'errors': errors
            }
        })
        
    except Exception as e:
        logger.error(f"批量重启服务失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# 获取service_name的所有副本详情
@deploy_service_bp.route('/replicas', methods=['GET'])
def get_service_replicas():
    try:
        service_name = request.args.get('service_name', '').strip()
        
        if not service_name:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：service_name'
            }), 400
        
        # 查找所有相同service_name的服务
        services = db.session.query(AIService, Model.name.label('model_name')).outerjoin(
            Model, AIService.model_id == Model.id
        ).filter(AIService.service_name == service_name).order_by(desc(AIService.created_at)).all()
        
        if not services:
            return jsonify({
                'code': 404,
                'msg': f'未找到服务: {service_name}'
            }), 404
        
        # 构建响应数据
        records = []
        for service, model_name in services:
            service_dict = service.to_dict()
            service_dict['model_name'] = model_name if model_name else None
            # 如果服务记录中没有版本和格式，从Model表获取
            if not service_dict.get('model_version'):
                model = Model.query.get(service.model_id)
                if model:
                    service_dict['model_version'] = model.version
            if not service_dict.get('format'):
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
            'total': len(records)
        })
        
    except Exception as e:
        logger.error(f'获取服务副本详情失败: {str(e)}')
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
        
        # 查找服务记录以获取服务ID
        service = AIService.query.filter_by(service_name=service_name).first()
        if not service:
            return jsonify({
                'code': 404,
                'msg': f'服务不存在: {service_name}'
            }), 404
        
        # 按服务ID创建日志目录
        ai_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        log_base_dir = os.path.join(ai_root, 'logs')
        service_log_dir = os.path.join(log_base_dir, str(service.id))
        os.makedirs(service_log_dir, exist_ok=True)
        
        # 按日期创建日志文件，格式：YYYY-MM-DD.log
        log_date = datetime.now().strftime('%Y-%m-%d')
        log_filename = f"{log_date}.log"
        log_file_path = os.path.join(service_log_dir, log_filename)
        
        # 构建日志行
        log_line = f"[{timestamp or datetime.now().isoformat()}] [{log_level}] {log_content}\n"
        
        # 将日志写入日期文件
        try:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
                f.flush()
        except Exception as e:
            logger.error(f"写入日志文件失败: {str(e)}")
            return jsonify({
                'code': 500,
                'msg': f'写入日志文件失败: {str(e)}'
            }), 500
        
        # 更新服务的log_path（如果不同）
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
                'log_file': log_file_path
            }
        })
        
    except Exception as e:
        logger.error(f"接收日志失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


def check_heartbeat_timeout(app):
    """定时检查心跳超时，超过1分钟没上报则更新状态为离线"""
    try:
        with app.app_context():
            timeout_threshold = beijing_now() - timedelta(minutes=1)
            
            timeout_services = AIService.query.filter(
                AIService.status.in_(['running', 'online']),
                (AIService.last_heartbeat < timeout_threshold) | (AIService.last_heartbeat.is_(None))
            ).all()
            
            for service in timeout_services:
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
    import threading
    import time
    
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
