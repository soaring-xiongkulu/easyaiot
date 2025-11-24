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

from db_models import db, Model, AIService, FrameExtractor, FrameSorter, beijing_now
from app.services.deploy_service import (
    deploy_model,
    start_service,
    stop_service,
    restart_service,
    delete_service,
    get_service_logs
)
from app.services.frame_extractor_service import (
    start_extractor,
    stop_extractor,
    get_extractor
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
        
        # 支持状态过滤：只保留running和stopped
        if status_filter in ['stopped', 'running']:
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
            
            # 计算各状态的实例数（只保留running和stopped）
            statuses = [s[0].status for s in services_list]
            # 将offline和error状态转换为stopped
            normalized_statuses = ['stopped' if s in ['offline', 'error'] else s for s in statuses]
            running_count = sum(1 for status in normalized_statuses if status == 'running')
            stopped_count = sum(1 for status in normalized_statuses if status == 'stopped')
            
            # 计算聚合状态：如果有任何一个running，则显示running；否则显示stopped
            if 'running' in normalized_statuses:
                aggregated_status = 'running'
            else:
                aggregated_status = 'stopped'
            
            # 构建合并后的记录
            service_dict = main_service.to_dict()
            service_dict['model_name'] = model_name if model_name else None
            service_dict['replica_count'] = replica_count
            service_dict['status'] = aggregated_status
            service_dict['running_count'] = running_count
            service_dict['stopped_count'] = stopped_count
            
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
        sorter_push_url = data.get('sorter_push_url')  # 排序器推送地址（可选）

        if not model_id:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：model_id'
            }), 400

        result = deploy_model(model_id, start_port, sorter_push_url)
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

        # 强制要求必须提供 service_id，只根据 service_id 查找和更新
        if not service_id:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：service_id。心跳上报必须提供 service_id 才能准确更新服务记录'
            }), 400
        
        # 根据 service_id 查找服务
        service = AIService.query.get(service_id)
        if not service:
            logger.error(f"通过 service_id={service_id} 未找到服务记录")
            return jsonify({
                'code': 404,
                'msg': f'服务不存在：service_id={service_id}。请确保服务已正确部署'
            }), 404
        
        logger.info(f"通过 service_id={service_id} 找到服务: {service.service_name}")

        # 更新心跳信息
        service.last_heartbeat = beijing_now()
        
        # 更新 service_name（如果提供了新的 service_name 且与数据库中的不同）
        # 允许 service_name 重复，支持同一服务名称的多个实例
        if service_name and service.service_name != service_name:
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
        # 获取分页参数，默认为不分页（兼容旧版本）
        page_no = request.args.get('pageNo')
        page_size = request.args.get('pageSize')
        
        if not service_name:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：service_name'
            }), 400
        
        # 构建基础查询
        base_query = db.session.query(AIService, Model.name.label('model_name')).outerjoin(
            Model, AIService.model_id == Model.id
        ).filter(AIService.service_name == service_name).order_by(desc(AIService.created_at))
        
        # 如果提供了分页参数，使用分页查询
        if page_no and page_size:
            try:
                page_no = int(page_no)
                page_size = int(page_size)
                
                if page_no < 1 or page_size < 1:
                    return jsonify({
                        'code': 400,
                        'msg': '参数错误：pageNo和pageSize必须为正整数'
                    }), 400
                
                # 执行分页查询
                pagination = base_query.paginate(
                    page=page_no,
                    per_page=page_size,
                    error_out=False
                )
                services = pagination.items
                total = pagination.total
            except ValueError:
                return jsonify({
                    'code': 400,
                    'msg': '参数类型错误：pageNo和pageSize需为整数'
                }), 400
        else:
            # 不分页，返回所有数据（兼容旧版本）
            services = base_query.all()
            total = len(services) if services else 0
        
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
            'total': total
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
    """定时检查心跳超时，超过1分钟没上报则更新状态为stopped"""
    try:
        with app.app_context():
            timeout_threshold = beijing_now() - timedelta(minutes=1)
            
            timeout_services = AIService.query.filter(
                AIService.status.in_(['running', 'online']),
                (AIService.last_heartbeat < timeout_threshold) | (AIService.last_heartbeat.is_(None))
            ).all()
            
            for service in timeout_services:
                old_status = service.status
                service.status = 'stopped'
                logger.info(f"服务心跳超时，状态从 {old_status} 更新为 stopped: {service.service_name}")
            
            if timeout_services:
                db.session.commit()
                logger.info(f"已更新 {len(timeout_services)} 个服务状态为stopped")
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


# ========== 抽帧器管理接口 ==========
@deploy_service_bp.route('/extractor/start', methods=['POST'])
def start_extractor_route():
    """启动抽帧器"""
    try:
        data = request.get_json()
        camera_name = data.get('camera_name')
        input_source = data.get('input_source')
        input_type = data.get('input_type', 'rtsp')  # video/rtsp
        model_id = data.get('model_id')
        service_name = data.get('service_name')
        frame_skip = int(data.get('frame_skip', 1))
        
        if not camera_name or not input_source or not model_id or not service_name:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：camera_name, input_source, model_id, service_name'
            }), 400
        
        result = start_extractor(camera_name, input_source, input_type, model_id, service_name, frame_skip)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"启动抽帧器失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@deploy_service_bp.route('/extractor/stop', methods=['POST'])
def stop_extractor_route():
    """停止抽帧器"""
    try:
        data = request.get_json()
        camera_name = data.get('camera_name')
        
        if not camera_name:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：camera_name'
            }), 400
        
        result = stop_extractor(camera_name)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"停止抽帧器失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@deploy_service_bp.route('/extractor/list', methods=['GET'])
def list_extractors():
    """获取抽帧器列表"""
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        camera_name_filter = request.args.get('camera_name', '').strip()
        status_filter = request.args.get('status', '').strip()
        
        # 构建查询
        query = FrameExtractor.query
        
        if camera_name_filter:
            query = query.filter(FrameExtractor.camera_name.ilike(f'%{camera_name_filter}%'))
        
        if status_filter:
            query = query.filter(FrameExtractor.status == status_filter)
        
        # 分页
        pagination = query.order_by(FrameExtractor.created_at.desc()).paginate(
            page=page_no,
            per_page=page_size,
            error_out=False
        )
        
        records = [extractor.to_dict() for extractor in pagination.items]
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': records,
            'total': pagination.total
        })
        
    except Exception as e:
        logger.error(f'获取抽帧器列表失败: {str(e)}')
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@deploy_service_bp.route('/extractor/<camera_name>', methods=['GET'])
def get_extractor_route(camera_name):
    """获取抽帧器详情"""
    try:
        extractor = get_extractor(camera_name)
        if not extractor:
            return jsonify({
                'code': 404,
                'msg': '抽帧器不存在'
            }), 404
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': extractor.to_dict()
        })
        
    except Exception as e:
        logger.error(f'获取抽帧器详情失败: {str(e)}')
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@deploy_service_bp.route('/extractor/heartbeat', methods=['POST'])
def receive_extractor_heartbeat():
    """接收抽帧器心跳"""
    try:
        data = request.get_json()
        extractor_id = data.get('extractor_id')
        camera_name = data.get('camera_name')
        current_frame_index = data.get('current_frame_index', 0)
        
        if not extractor_id:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：extractor_id'
            }), 400
        
        extractor = FrameExtractor.query.get(extractor_id)
        if not extractor:
            return jsonify({
                'code': 404,
                'msg': '抽帧器不存在'
            }), 404
        
        # 更新心跳信息
        extractor.last_heartbeat = beijing_now()
        extractor.current_frame_index = current_frame_index
        
        if extractor.status != 'stopped':
            extractor.status = 'running'
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '心跳接收成功',
            'data': {
                'extractor_id': extractor.id,
                'camera_name': extractor.camera_name
            }
        })
        
    except Exception as e:
        logger.error(f"接收抽帧器心跳失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@deploy_service_bp.route('/extractor/<camera_name>/enable', methods=['POST'])
def enable_extractor_route(camera_name):
    """开启抽帧器"""
    try:
        extractor = get_extractor(camera_name)
        if not extractor:
            return jsonify({
                'code': 404,
                'msg': '抽帧器不存在'
            }), 404
        
        # 如果当前输入源是视频则从头抽帧，如果是rtsp流也是取当前流去抽帧
        if extractor.input_type == 'video':
            extractor.current_frame_index = 0  # 视频从头抽帧
            logger.info(f'抽帧器 {camera_name} 开启，视频输入，帧索引重置为0')
        # RTSP不需要重置索引，从当前流开始抽帧
        
        extractor.is_enabled = True
        db.session.commit()
        
        # 如果抽帧器未运行，启动它
        from app.services.frame_extractor_service import start_extractor
        if extractor.status != 'running':
            result = start_extractor(
                camera_name=extractor.camera_name,
                input_source=extractor.input_source,
                input_type=extractor.input_type,
                model_id=extractor.model_id,
                service_name=extractor.service_name,
                frame_skip=extractor.frame_skip
            )
            if result.get('code') != 0:
                return jsonify(result), 500
        
        return jsonify({
            'code': 0,
            'msg': '抽帧器已开启',
            'data': extractor.to_dict()
        })
        
    except Exception as e:
        logger.error(f'开启抽帧器失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@deploy_service_bp.route('/extractor/<camera_name>/disable', methods=['POST'])
def disable_extractor_route(camera_name):
    """关闭抽帧器"""
    try:
        extractor = get_extractor(camera_name)
        if not extractor:
            return jsonify({
                'code': 404,
                'msg': '抽帧器不存在'
            }), 404
        
        extractor.is_enabled = False
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '抽帧器已关闭',
            'data': extractor.to_dict()
        })
        
    except Exception as e:
        logger.error(f'关闭抽帧器失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@deploy_service_bp.route('/sorter', methods=['GET'])
def get_sorter_route():
    """获取排序器信息"""
    try:
        service_name = request.args.get('service_name', '').strip()
        
        if not service_name:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：service_name'
            }), 400
        
        from app.services.frame_sorter_service import get_sorter
        sorter = get_sorter(service_name)
        
        if not sorter:
            return jsonify({
                'code': 404,
                'msg': '排序器不存在'
            }), 404
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': sorter.to_dict()
        })
        
    except Exception as e:
        logger.error(f'获取排序器信息失败: {str(e)}')
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500
