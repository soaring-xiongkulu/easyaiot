"""
推流转发任务管理路由
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import os
from datetime import datetime
from flask import Blueprint, request, jsonify

from models import db, StreamForwardTask, Device
from app.services.stream_forward_service import (
    create_stream_forward_task, update_stream_forward_task, delete_stream_forward_task,
    get_stream_forward_task, list_stream_forward_tasks, start_stream_forward_task,
    stop_stream_forward_task, restart_stream_forward_task
)

stream_forward_bp = Blueprint('stream_forward', __name__)
logger = logging.getLogger(__name__)


# ====================== 推流转发任务管理接口 ======================
@stream_forward_bp.route('/task/list', methods=['GET'])
def list_tasks():
    """查询推流转发任务列表"""
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '').strip() or None
        device_id = request.args.get('device_id', '').strip() or None
        is_enabled = request.args.get('is_enabled')
        is_enabled = bool(int(is_enabled)) if is_enabled else None
        
        result = list_stream_forward_tasks(page_no, page_size, search, device_id, is_enabled)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result['items'],
            'total': result['total']
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'查询推流转发任务列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@stream_forward_bp.route('/task/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """获取推流转发任务详情"""
    try:
        task = get_stream_forward_task(task_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': task.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'获取推流转发任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@stream_forward_bp.route('/task', methods=['POST'])
def create_task():
    """创建推流转发任务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        task_name = data.get('task_name')
        if not task_name:
            return jsonify({'code': 400, 'msg': '任务名称不能为空'}), 400
        
        # 处理 is_enabled 参数，确保正确转换为布尔值
        is_enabled = data.get('is_enabled', False)
        if isinstance(is_enabled, str):
            # 如果是字符串，转换为布尔值
            is_enabled = is_enabled.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(is_enabled, int):
            # 如果是数字，转换为布尔值
            is_enabled = bool(is_enabled)
        elif not isinstance(is_enabled, bool):
            # 如果是其他类型，默认为 False
            is_enabled = False
        
        task = create_stream_forward_task(
            task_name=task_name,
            device_ids=data.get('device_ids'),
            output_format=data.get('output_format', 'rtmp'),
            output_quality=data.get('output_quality', 'high'),
            output_bitrate=data.get('output_bitrate'),
            description=data.get('description'),
            is_enabled=is_enabled
        )
        
        return jsonify({
            'code': 0,
            'msg': '创建成功',
            'data': task.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'创建推流转发任务失败: {str(e)}', exc_info=True)
        # 检查是否是摄像头冲突错误
        error_msg = str(e)
        if '摄像头冲突' in error_msg or '不能同时用于' in error_msg:
            return jsonify({'code': 400, 'msg': error_msg}), 400
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@stream_forward_bp.route('/task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新推流转发任务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        # 处理 is_enabled 参数，确保正确转换为布尔值
        if 'is_enabled' in data:
            is_enabled = data['is_enabled']
            if isinstance(is_enabled, str):
                # 如果是字符串，转换为布尔值
                is_enabled = is_enabled.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(is_enabled, int):
                # 如果是数字，转换为布尔值
                is_enabled = bool(is_enabled)
            elif not isinstance(is_enabled, bool):
                # 如果是其他类型，默认为 False
                is_enabled = False
            data['is_enabled'] = is_enabled
        
        task = update_stream_forward_task(task_id, **data)
        
        return jsonify({
            'code': 0,
            'msg': '更新成功',
            'data': task.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'更新推流转发任务失败: {str(e)}', exc_info=True)
        # 检查是否是摄像头冲突错误
        error_msg = str(e)
        if '摄像头冲突' in error_msg or '不能同时用于' in error_msg:
            return jsonify({'code': 400, 'msg': error_msg}), 400
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@stream_forward_bp.route('/task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除推流转发任务"""
    try:
        delete_stream_forward_task(task_id)
        return jsonify({
            'code': 0,
            'msg': '删除成功'
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'删除推流转发任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@stream_forward_bp.route('/task/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """启动推流转发任务"""
    try:
        task, message, already_running = start_stream_forward_task(task_id)
        # 将任务数据转换为字典，并添加 already_running 字段
        task_dict = task.to_dict()
        task_dict['already_running'] = already_running
        
        return jsonify({
            'code': 0,
            'msg': message,  # "任务运行中" 或 "启动成功"
            'data': task_dict
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'启动推流转发任务失败: {str(e)}', exc_info=True)
        # 检查是否是摄像头冲突错误
        error_msg = str(e)
        if '摄像头冲突' in error_msg or '不能同时用于' in error_msg:
            return jsonify({'code': 400, 'msg': error_msg}), 400
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@stream_forward_bp.route('/task/<int:task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """停止推流转发任务"""
    try:
        task = stop_stream_forward_task(task_id)
        return jsonify({
            'code': 0,
            'msg': '停止成功',
            'data': task.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'停止推流转发任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@stream_forward_bp.route('/task/<int:task_id>/restart', methods=['POST'])
def restart_task(task_id):
    """重启推流转发任务"""
    try:
        task = restart_stream_forward_task(task_id)
        return jsonify({
            'code': 0,
            'msg': '重启成功',
            'data': task.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'重启推流转发任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 心跳接收接口 ======================
@stream_forward_bp.route('/heartbeat', methods=['POST'])
def receive_heartbeat():
    """接收推流转发服务心跳"""
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
        
        task = StreamForwardTask.query.get(task_id)
        if not task:
            return jsonify({
                'code': 400,
                'msg': f'推流转发任务不存在：task_id={task_id}'
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
            task.service_log_path = os.path.join(log_base_dir, f'stream_forward_task_{task_id}')
        
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
        logger.error(f"接收推流转发服务心跳失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# ====================== 服务状态查询接口 ======================
@stream_forward_bp.route('/task/<int:task_id>/status', methods=['GET'])
def get_task_status(task_id):
    """获取推流转发任务的服务状态信息"""
    try:
        task = StreamForwardTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '推流转发任务不存在'}), 400
        
        # 检查守护进程是否在运行（即使心跳未上报）
        daemon_running = False
        try:
            from app.services.stream_forward_launcher_service import _running_daemons, _daemons_lock
            with _daemons_lock:
                if task_id in _running_daemons:
                    daemon = _running_daemons[task_id]
                    if daemon._running and daemon._process and daemon._process.poll() is None:
                        daemon_running = True
        except Exception as e:
            logger.debug(f"检查守护进程状态失败: {str(e)}")
        
        # 根据 is_enabled、心跳和守护进程状态判断服务状态
        # 优先考虑 is_enabled 字段：如果 is_enabled=False，即使有心跳也应该返回 stopped
        if not task.is_enabled:
            service_status = 'stopped'
        else:
            # is_enabled=True 时，再根据心跳和守护进程状态判断
            has_recent_heartbeat = task.service_last_heartbeat and (datetime.utcnow() - task.service_last_heartbeat).total_seconds() < 60
            if has_recent_heartbeat:
                service_status = 'running'
            elif daemon_running:
                # 守护进程在运行但心跳未上报（可能是刚启动，心跳还未上报）
                service_status = 'running'
            else:
                service_status = 'stopped'
        
        # 构建服务状态信息
        service_info = {
            'task_id': task.id,
            'task_name': task.task_name,
            'server_ip': task.service_server_ip,
            'port': task.service_port,
            'process_id': task.service_process_id,
            'last_heartbeat': task.service_last_heartbeat.isoformat() if task.service_last_heartbeat else None,
            'log_path': task.service_log_path,
            'status': service_status,
            'total_streams': task.total_streams
        }
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': service_info
        })
    except Exception as e:
        logger.error(f"获取推流转发任务服务状态失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 日志查看接口 ======================
@stream_forward_bp.route('/task/<int:task_id>/logs', methods=['GET'])
def get_task_logs(task_id):
    """获取推流转发任务的日志"""
    try:
        task = StreamForwardTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '推流转发任务不存在'}), 400
        
        lines = int(request.args.get('lines', 100))
        date = request.args.get('date', '').strip()
        
        # 创建一个模拟的服务对象，用于调用get_service_logs
        class StreamForwardServiceObj:
            def __init__(self, log_path):
                self.log_path = log_path
                self.id = task_id
        
        # 确定日志路径
        if task.service_log_path:
            log_path = task.service_log_path
        else:
            video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            log_base_dir = os.path.join(video_root, 'logs')
            log_path = os.path.join(log_base_dir, f'stream_forward_task_{task_id}')
        
        service_obj = StreamForwardServiceObj(log_path)
        return get_service_logs(service_obj, lines, date if date else None)
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f"获取推流转发任务日志失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 推流地址查询接口 ======================
@stream_forward_bp.route('/task/<int:task_id>/streams', methods=['GET'])
def get_task_streams(task_id):
    """获取推流转发任务关联的摄像头推流地址列表"""
    try:
        task = StreamForwardTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '推流转发任务不存在'}), 400
        
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
                'rtmp_stream': device.rtmp_stream,
                'http_stream': device.http_stream,
                'source': device.source,
                'cover_image_path': device.cover_image_path,
            }
            streams.append(stream_info)
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': streams
        })
    except Exception as e:
        logger.error(f"获取推流转发任务推流地址失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


def get_service_logs(service_obj, lines: int = 100, date: str = None):
    """获取服务日志的通用函数"""
    try:
        # 确定日志文件路径
        video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        log_base_dir = os.path.join(video_root, 'logs')
        
        if not service_obj.log_path:
            # 根据服务类型生成日志目录
            service_log_dir = os.path.join(log_base_dir, f'stream_forward_task_{service_obj.id}')
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

