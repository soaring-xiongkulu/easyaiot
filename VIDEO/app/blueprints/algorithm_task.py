"""
算法任务、抽帧器、排序器管理路由
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from models import db, AlgorithmTask, FrameExtractor, Sorter, Pusher, Device
from app.services.algorithm_task_service import (
    create_algorithm_task, update_algorithm_task, delete_algorithm_task,
    get_algorithm_task, list_algorithm_tasks, start_algorithm_task,
    stop_algorithm_task, restart_algorithm_task
)

algorithm_task_bp = Blueprint('algorithm_task', __name__)
logger = logging.getLogger(__name__)


# ====================== 算法任务管理接口 ======================
@algorithm_task_bp.route('/task/list', methods=['GET'])
def list_tasks():
    """查询算法任务列表"""
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '').strip() or None
        device_id = request.args.get('device_id', '').strip() or None
        task_type = request.args.get('task_type', '').strip() or None
        is_enabled = request.args.get('is_enabled')
        is_enabled = bool(int(is_enabled)) if is_enabled else None
        
        result = list_algorithm_tasks(page_no, page_size, search, device_id, task_type, is_enabled)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result['items'],
            'total': result['total']
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'查询算法任务列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """获取算法任务详情"""
    try:
        task = get_algorithm_task(task_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': task.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'获取算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task', methods=['POST'])
def create_task():
    """创建算法任务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        task_name = data.get('task_name')
        if not task_name:
            return jsonify({'code': 400, 'msg': '任务名称不能为空'}), 400
        
        task_type = data.get('task_type', 'realtime')
        if task_type not in ['realtime', 'snap']:
            return jsonify({'code': 400, 'msg': '任务类型必须是 realtime 或 snap'}), 400
        
        task = create_algorithm_task(
            task_name=task_name,
            task_type=task_type,
            device_ids=data.get('device_ids'),
            model_ids=data.get('model_ids'),  # 模型ID列表
            extract_interval=data.get('extract_interval', 25),
            # rtmp_input_url和rtmp_output_url不再从请求中获取，改为从摄像头列表获取
            tracking_enabled=data.get('tracking_enabled', False),
            tracking_similarity_threshold=data.get('tracking_similarity_threshold', 0.2),
            tracking_max_age=data.get('tracking_max_age', 25),
            tracking_smooth_alpha=data.get('tracking_smooth_alpha', 0.25),
            alert_event_enabled=data.get('alert_event_enabled', False),
            alert_notification_enabled=data.get('alert_notification_enabled', False),
            alert_notification_config=data.get('alert_notification_config'),
            cron_expression=data.get('cron_expression'),
            frame_skip=data.get('frame_skip', 25),
            is_enabled=data.get('is_enabled', False),
            defense_mode=data.get('defense_mode'),
            defense_schedule=data.get('defense_schedule')
        )
        
        return jsonify({
            'code': 0,
            'msg': '创建成功',
            'data': task.to_dict()
        })
    except (ValueError, RuntimeError) as e:
        # 提取错误消息，如果是 RuntimeError 包装的 ValueError，提取原始消息
        error_msg = str(e)
        if isinstance(e, RuntimeError) and '创建算法任务失败:' in error_msg:
            # 提取冒号后的消息
            error_msg = error_msg.split('创建算法任务失败:', 1)[-1].strip()
        return jsonify({'code': 400, 'msg': error_msg}), 400
    except Exception as e:
        logger.error(f'创建算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新算法任务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        task = update_algorithm_task(task_id, **data)
        
        return jsonify({
            'code': 0,
            'msg': '更新成功',
            'data': task.to_dict()
        })
    except (ValueError, RuntimeError) as e:
        # 提取错误消息，如果是 RuntimeError 包装的 ValueError，提取原始消息
        error_msg = str(e)
        if isinstance(e, RuntimeError) and '更新算法任务失败:' in error_msg:
            # 提取冒号后的消息
            error_msg = error_msg.split('更新算法任务失败:', 1)[-1].strip()
        return jsonify({'code': 400, 'msg': error_msg}), 400
    except Exception as e:
        logger.error(f'更新算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除算法任务"""
    try:
        delete_algorithm_task(task_id)
        return jsonify({
            'code': 0,
            'msg': '删除成功'
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'删除算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """启动算法任务"""
    try:
        task, message, already_running = start_algorithm_task(task_id)
        # 将任务数据转换为字典，并添加 already_running 字段
        task_dict = task.to_dict()
        task_dict['already_running'] = already_running
        
        return jsonify({
            'code': 0,
            'msg': message,  # "任务运行中" 或 "启动成功"
            'data': task_dict
        })
    except (ValueError, RuntimeError) as e:
        # 提取错误消息，如果是 RuntimeError 包装的 ValueError，提取原始消息
        error_msg = str(e)
        if isinstance(e, RuntimeError) and '启动算法任务失败:' in error_msg:
            # 提取冒号后的消息
            error_msg = error_msg.split('启动算法任务失败:', 1)[-1].strip()
        return jsonify({'code': 400, 'msg': error_msg}), 400
    except Exception as e:
        logger.error(f'启动算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """停止算法任务"""
    try:
        task = stop_algorithm_task(task_id)
        return jsonify({
            'code': 0,
            'msg': '停止成功',
            'data': task.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'停止算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/restart', methods=['POST'])
def restart_task(task_id):
    """重启算法任务"""
    try:
        task = restart_algorithm_task(task_id)
        return jsonify({
            'code': 0,
            'msg': '重启成功',
            'data': task.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'重启算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 抽帧器、排序器、推送器、算法服务管理接口已移除 ======================
# 新架构统一使用realtime_algorithm_service，不再需要这些独立的服务管理接口


# ====================== 心跳接收接口 ======================
# 新架构统一使用实时算法服务心跳接口，旧的抽帧器、排序器、推送器心跳接口已移除


@algorithm_task_bp.route('/heartbeat/realtime', methods=['POST'])
def receive_realtime_heartbeat():
    """接收实时算法服务心跳"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        server_ip = data.get('server_ip')
        port = data.get('port')
        process_id = data.get('process_id')
        log_path = data.get('log_path')
        
        if not task_id:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：task_id'
            }), 400
        
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({
                'code': 400,
                'msg': f'算法任务不存在：task_id={task_id}'
            }), 400
        
        # 更新心跳信息
        task.service_last_heartbeat = datetime.utcnow()
        if server_ip:
            task.service_server_ip = server_ip
        if port:
            task.service_port = port
        if process_id:
            task.service_process_id = process_id
        if log_path:
            task.service_log_path = log_path
        elif not task.service_log_path:
            # 如果没有log_path，根据task_id生成
            video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            log_base_dir = os.path.join(video_root, 'logs')
            task.service_log_path = os.path.join(log_base_dir, f'task_{task_id}')
        
        # 更新运行状态为running
        if task.run_status != 'stopped':
            task.run_status = 'running'
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '心跳接收成功',
            'data': {
                'task_id': task.id,
                'task_name': task.task_name
            }
        })
    except Exception as e:
        logger.error(f"接收实时算法服务心跳失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# ====================== 服务状态查询接口 ======================
@algorithm_task_bp.route('/task/<int:task_id>/services/status', methods=['GET'])
def get_task_services_status(task_id):
    """获取算法任务的所有服务状态信息"""
    try:
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '算法任务不存在'}), 400
        
        result = {
            'realtime_service': None
        }
        
        # 实时算法任务：返回统一服务的状态
        if task.task_type == 'realtime':
            # 检查守护进程是否在运行（即使心跳未上报）
            daemon_running = False
            try:
                from app.services.algorithm_task_launcher_service import _running_daemons, _daemons_lock
                with _daemons_lock:
                    if task_id in _running_daemons:
                        daemon = _running_daemons[task_id]
                        if daemon._running and daemon._process and daemon._process.poll() is None:
                            daemon_running = True
            except Exception as e:
                logger.debug(f"检查守护进程状态失败: {str(e)}")
            
            # 根据心跳和守护进程状态判断服务状态
            has_recent_heartbeat = task.service_last_heartbeat and (datetime.utcnow() - task.service_last_heartbeat).total_seconds() < 60
            if has_recent_heartbeat:
                service_status = 'running'
            elif daemon_running:
                # 守护进程在运行但心跳未上报（可能是刚启动，心跳还未上报）
                service_status = 'running'
            else:
                service_status = 'stopped'
            
            # 构建实时算法服务状态信息
            realtime_service = {
                'task_id': task.id,
                'task_name': task.task_name,
                'server_ip': task.service_server_ip,
                'port': task.service_port,
                'process_id': task.service_process_id,
                'last_heartbeat': task.service_last_heartbeat.isoformat() if task.service_last_heartbeat else None,
                'log_path': task.service_log_path,
                'status': service_status,
                'run_status': task.run_status
            }
            result['realtime_service'] = realtime_service
        else:
            # 抓拍算法任务：不需要服务状态
            pass
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result
        })
    except Exception as e:
        logger.error(f"获取算法任务服务状态失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 日志查看接口 ======================
@algorithm_task_bp.route('/task/<int:task_id>/extractor/logs', methods=['GET'])
def get_task_extractor_logs(task_id):
    """获取算法任务的抽帧器日志"""
    try:
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '算法任务不存在'}), 400
        
        # 新架构统一使用realtime_algorithm_service，对于实时算法任务，使用统一的日志路径
        if task.task_type == 'realtime':
            # 对于实时算法任务，使用统一的日志路径
            lines = int(request.args.get('lines', 100))
            date = request.args.get('date', '').strip()
            
            # 创建一个模拟的服务对象，用于调用get_service_logs
            class RealtimeServiceObj:
                def __init__(self, log_path):
                    self.log_path = log_path
                    self.id = task_id
            
            # 确定日志路径
            if task.service_log_path:
                log_path = task.service_log_path
            else:
                video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                log_base_dir = os.path.join(video_root, 'logs')
                log_path = os.path.join(log_base_dir, f'task_{task_id}')
            
            service_obj = RealtimeServiceObj(log_path)
            return get_service_logs(service_obj, lines, date if date else None)
        else:
            # 对于抓拍算法任务，检查是否有extractor_id（旧架构）
            # 注意：新架构的AlgorithmTask模型中没有extractor_id字段
            # 这里为了兼容性，直接返回提示信息
            return jsonify({
                'code': 400,
                'msg': '新架构已统一使用实时算法服务，请使用realtime日志接口'
            }), 400
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f"获取抽帧器日志失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/sorter/logs', methods=['GET'])
def get_task_sorter_logs(task_id):
    """获取算法任务的排序器日志"""
    try:
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '算法任务不存在'}), 400
        
        # 新架构统一使用realtime_algorithm_service，对于实时算法任务，使用统一的日志路径
        if task.task_type == 'realtime':
            # 对于实时算法任务，使用统一的日志路径
            lines = int(request.args.get('lines', 100))
            date = request.args.get('date', '').strip()
            
            # 创建一个模拟的服务对象，用于调用get_service_logs
            class RealtimeServiceObj:
                def __init__(self, log_path):
                    self.log_path = log_path
                    self.id = task_id
            
            # 确定日志路径
            if task.service_log_path:
                log_path = task.service_log_path
            else:
                video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                log_base_dir = os.path.join(video_root, 'logs')
                log_path = os.path.join(log_base_dir, f'task_{task_id}')
            
            service_obj = RealtimeServiceObj(log_path)
            return get_service_logs(service_obj, lines, date if date else None)
        else:
            # 对于抓拍算法任务，检查是否有sorter_id（旧架构）
            # 注意：新架构的AlgorithmTask模型中没有sorter_id字段
            # 这里为了兼容性，直接返回提示信息
            return jsonify({
                'code': 400,
                'msg': '新架构已统一使用实时算法服务，请使用realtime日志接口'
            }), 400
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f"获取排序器日志失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/pusher/logs', methods=['GET'])
def get_task_pusher_logs(task_id):
    """获取算法任务的推送器日志"""
    try:
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '算法任务不存在'}), 400
        
        # 新架构统一使用realtime_algorithm_service，对于实时算法任务，使用统一的日志路径
        if task.task_type == 'realtime':
            # 对于实时算法任务，使用统一的日志路径
            lines = int(request.args.get('lines', 100))
            date = request.args.get('date', '').strip()
            
            # 创建一个模拟的服务对象，用于调用get_service_logs
            class RealtimeServiceObj:
                def __init__(self, log_path):
                    self.log_path = log_path
                    self.id = task_id
            
            # 确定日志路径
            if task.service_log_path:
                log_path = task.service_log_path
            else:
                video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                log_base_dir = os.path.join(video_root, 'logs')
                log_path = os.path.join(log_base_dir, f'task_{task_id}')
            
            service_obj = RealtimeServiceObj(log_path)
            return get_service_logs(service_obj, lines, date if date else None)
        else:
            # 对于抓拍算法任务，检查是否有pusher_id（旧架构）
            # 注意：新架构的AlgorithmTask模型中没有pusher_id字段
            # 这里为了兼容性，直接返回提示信息
            return jsonify({
                'code': 400,
                'msg': '新架构已统一使用实时算法服务，请使用realtime日志接口'
            }), 400
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f"获取推送器日志失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/realtime/logs', methods=['GET'])
def get_task_realtime_logs(task_id):
    """获取实时算法任务的日志"""
    try:
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '算法任务不存在'}), 400
        
        if task.task_type != 'realtime':
            return jsonify({'code': 400, 'msg': '该接口仅支持实时算法任务'}), 400
        
        lines = int(request.args.get('lines', 100))
        date = request.args.get('date', '').strip()
        
        # 创建一个模拟的服务对象，用于调用get_service_logs
        class RealtimeServiceObj:
            def __init__(self, log_path):
                self.log_path = log_path
                self.id = task_id
        
        # 确定日志路径
        if task.service_log_path:
            log_path = task.service_log_path
        else:
            video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            log_base_dir = os.path.join(video_root, 'logs')
            log_path = os.path.join(log_base_dir, f'task_{task_id}')
        
        service_obj = RealtimeServiceObj(log_path)
        return get_service_logs(service_obj, lines, date if date else None)
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f"获取实时算法服务日志失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 推流地址查询接口 ======================
@algorithm_task_bp.route('/task/<int:task_id>/streams', methods=['GET'])
def get_task_streams(task_id):
    """获取算法任务关联的摄像头推流地址列表"""
    try:
        import json
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '算法任务不存在'}), 400
        
        # 获取关联的摄像头列表
        device_list = task.devices if task.devices else []
        if not device_list:
            return jsonify({
                'code': 0,
                'msg': 'success',
                'data': []
            })
        
        # 构建摄像头推流地址列表
        streams = []
        for device in device_list:
            stream_info = {
                'device_id': device.id,
                'device_name': device.name or device.id,
                'http_stream': device.http_stream,
                'rtmp_stream': device.rtmp_stream,
                'source': device.source,
                'cover_image_path': device.cover_image_path,  # 添加设备封面图字段
            }
            
            # 对于实时算法任务和抓拍算法任务，都直接使用摄像头的推流地址
            
            streams.append(stream_info)
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': streams
        })
    except Exception as e:
        logger.error(f"获取算法任务推流地址失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


def get_service_logs(service_obj, lines: int = 100, date: str = None):
    """获取服务日志的通用函数"""
    try:
        # 确定日志文件路径
        video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        log_base_dir = os.path.join(video_root, 'logs')
        
        if not service_obj.log_path:
            # 根据服务类型生成日志目录（仅支持实时算法服务）
            service_log_dir = os.path.join(log_base_dir, str(service_obj.id))
        else:
            service_log_dir = service_obj.log_path
        
        # 根据参数选择日志文件（按日期）
        if date:
            log_filename = f"{date}.log"
        else:
            # 如果没有指定日期，返回今天的日志文件
            log_filename = datetime.now().strftime('%Y-%m-%d.log')
        
        log_file_path = os.path.join(service_log_dir, log_filename)
        
        # 检查日志文件是否存在
        if not os.path.exists(log_file_path):
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
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试使用其他编码
            try:
                with open(log_file_path, 'r', encoding='gbk') as f:
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
        logger.error(f"获取服务日志失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500

