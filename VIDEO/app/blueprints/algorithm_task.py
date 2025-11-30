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

from models import db, FrameExtractor, Sorter, Pusher
from app.services.algorithm_task_service import (
    create_algorithm_task, update_algorithm_task, delete_algorithm_task,
    get_algorithm_task, list_algorithm_tasks, start_algorithm_task,
    stop_algorithm_task, restart_algorithm_task
)
from app.services.frame_extractor_service import (
    create_frame_extractor, update_frame_extractor, delete_frame_extractor,
    get_frame_extractor, list_frame_extractors
)
from app.services.sorter_service import (
    create_sorter, update_sorter, delete_sorter,
    get_sorter, list_sorters
)
from app.services.pusher_service import (
    create_pusher, update_pusher, delete_pusher,
    get_pusher, list_pushers
)
from app.services.algorithm_service import (
    create_task_algorithm_service, update_task_algorithm_service,
    delete_task_algorithm_service, get_task_algorithm_services
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
        return jsonify({'code': 404, 'msg': str(e)}), 404
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
            extractor_id=data.get('extractor_id'),
            sorter_id=data.get('sorter_id'),
            pusher_id=data.get('pusher_id'),
            device_ids=data.get('device_ids'),
            space_id=data.get('space_id'),
            cron_expression=data.get('cron_expression'),
            frame_skip=data.get('frame_skip', 1),
            is_enabled=data.get('is_enabled', False),
            defense_mode=data.get('defense_mode'),
            defense_schedule=data.get('defense_schedule'),
            algorithm_services=data.get('algorithm_services')
        )
        
        return jsonify({
            'code': 0,
            'msg': '创建成功',
            'data': task.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
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
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
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
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'删除算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """启动算法任务"""
    try:
        task = start_algorithm_task(task_id)
        return jsonify({
            'code': 0,
            'msg': '启动成功',
            'data': task.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
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
        return jsonify({'code': 404, 'msg': str(e)}), 404
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
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'重启算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 抽帧器管理接口 ======================
@algorithm_task_bp.route('/extractor/list', methods=['GET'])
def list_extractors():
    """查询抽帧器列表"""
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '').strip() or None
        
        result = list_frame_extractors(page_no, page_size, search)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result['items'],
            'total': result['total']
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'查询抽帧器列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/extractor/<int:extractor_id>', methods=['GET'])
def get_extractor(extractor_id):
    """获取抽帧器详情"""
    try:
        extractor = get_frame_extractor(extractor_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': extractor.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'获取抽帧器失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/extractor', methods=['POST'])
def create_extractor():
    """创建抽帧器"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        extractor_name = data.get('extractor_name')
        if not extractor_name:
            return jsonify({'code': 400, 'msg': '抽帧器名称不能为空'}), 400
        
        extractor = create_frame_extractor(
            extractor_name=extractor_name,
            extractor_type=data.get('extractor_type', 'interval'),
            interval=data.get('interval', 1),
            description=data.get('description'),
            is_enabled=data.get('is_enabled', True)
        )
        
        return jsonify({
            'code': 0,
            'msg': '创建成功',
            'data': extractor.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'创建抽帧器失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/extractor/<int:extractor_id>', methods=['PUT'])
def update_extractor(extractor_id):
    """更新抽帧器"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        extractor = update_frame_extractor(extractor_id, **data)
        
        return jsonify({
            'code': 0,
            'msg': '更新成功',
            'data': extractor.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'更新抽帧器失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/extractor/<int:extractor_id>', methods=['DELETE'])
def delete_extractor(extractor_id):
    """删除抽帧器"""
    try:
        delete_frame_extractor(extractor_id)
        return jsonify({
            'code': 0,
            'msg': '删除成功'
        })
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'删除抽帧器失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 排序器管理接口 ======================
@algorithm_task_bp.route('/sorter/list', methods=['GET'])
def list_sorters_route():
    """查询排序器列表"""
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '').strip() or None
        
        result = list_sorters(page_no, page_size, search)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result['items'],
            'total': result['total']
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'查询排序器列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/sorter/<int:sorter_id>', methods=['GET'])
def get_sorter_route(sorter_id):
    """获取排序器详情"""
    try:
        sorter = get_sorter(sorter_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': sorter.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'获取排序器失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/sorter', methods=['POST'])
def create_sorter_route():
    """创建排序器"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        sorter_name = data.get('sorter_name')
        if not sorter_name:
            return jsonify({'code': 400, 'msg': '排序器名称不能为空'}), 400
        
        sorter = create_sorter(
            sorter_name=sorter_name,
            sorter_type=data.get('sorter_type', 'confidence'),
            sort_order=data.get('sort_order', 'desc'),
            description=data.get('description'),
            is_enabled=data.get('is_enabled', True)
        )
        
        return jsonify({
            'code': 0,
            'msg': '创建成功',
            'data': sorter.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'创建排序器失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/sorter/<int:sorter_id>', methods=['PUT'])
def update_sorter_route(sorter_id):
    """更新排序器"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        sorter = update_sorter(sorter_id, **data)
        
        return jsonify({
            'code': 0,
            'msg': '更新成功',
            'data': sorter.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'更新排序器失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/sorter/<int:sorter_id>', methods=['DELETE'])
def delete_sorter_route(sorter_id):
    """删除排序器"""
    try:
        delete_sorter(sorter_id)
        return jsonify({
            'code': 0,
            'msg': '删除成功'
        })
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'删除排序器失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 算法任务的服务管理接口 ======================
@algorithm_task_bp.route('/task/<int:task_id>/services', methods=['GET'])
def list_task_services(task_id):
    """获取算法任务的所有算法服务"""
    try:
        services = get_task_algorithm_services(task_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': [s.to_dict() for s in services]
        })
    except Exception as e:
        logger.error(f'获取算法任务服务列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/service', methods=['POST'])
def create_task_service(task_id):
    """为算法任务创建算法服务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        service_name = data.get('service_name')
        if not service_name:
            return jsonify({'code': 400, 'msg': '服务名称不能为空'}), 400
        
        service_url = data.get('service_url')
        if not service_url:
            return jsonify({'code': 400, 'msg': '服务URL不能为空'}), 400
        
        service = create_task_algorithm_service(
            task_id=task_id,
            service_name=service_name,
            service_url=service_url,
            service_type=data.get('service_type'),
            model_id=data.get('model_id'),
            threshold=data.get('threshold'),
            request_method=data.get('request_method', 'POST'),
            request_headers=data.get('request_headers'),
            request_body_template=data.get('request_body_template'),
            timeout=data.get('timeout', 30),
            is_enabled=data.get('is_enabled', True),
            sort_order=data.get('sort_order', 0)
        )
        
        return jsonify({
            'code': 0,
            'msg': '创建成功',
            'data': service.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'创建算法服务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/service/<int:service_id>', methods=['PUT'])
def update_task_service(service_id):
    """更新算法任务的算法服务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        service = update_task_algorithm_service(service_id, **data)
        
        return jsonify({
            'code': 0,
            'msg': '更新成功',
            'data': service.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'更新算法服务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/service/<int:service_id>', methods=['DELETE'])
def delete_task_service(service_id):
    """删除算法任务的算法服务"""
    try:
        delete_task_algorithm_service(service_id)
        return jsonify({
            'code': 0,
            'msg': '删除成功'
        })
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'删除算法服务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 推送器管理接口 ======================
@algorithm_task_bp.route('/pusher/list', methods=['GET'])
def list_pushers_route():
    """查询推送器列表"""
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '').strip() or None
        is_enabled = request.args.get('is_enabled')
        is_enabled = bool(int(is_enabled)) if is_enabled else None
        
        result = list_pushers(page_no, page_size, search, is_enabled)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result['items'],
            'total': result['total']
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'查询推送器列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/pusher/<int:pusher_id>', methods=['GET'])
def get_pusher_route(pusher_id):
    """获取推送器详情"""
    try:
        pusher = get_pusher(pusher_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': pusher.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'获取推送器失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/pusher', methods=['POST'])
def create_pusher_route():
    """创建推送器"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        pusher_name = data.get('pusher_name')
        if not pusher_name:
            return jsonify({'code': 400, 'msg': '推送器名称不能为空'}), 400
        
        pusher = create_pusher(
            pusher_name=pusher_name,
            video_stream_enabled=data.get('video_stream_enabled', False),
            video_stream_url=data.get('video_stream_url'),
            video_stream_format=data.get('video_stream_format', 'rtmp'),
            video_stream_quality=data.get('video_stream_quality', 'high'),
            event_alert_enabled=data.get('event_alert_enabled', False),
            event_alert_url=data.get('event_alert_url'),
            event_alert_method=data.get('event_alert_method', 'http'),
            event_alert_format=data.get('event_alert_format', 'json'),
            event_alert_headers=data.get('event_alert_headers'),
            event_alert_template=data.get('event_alert_template'),
            description=data.get('description'),
            is_enabled=data.get('is_enabled', True)
        )
        
        return jsonify({
            'code': 0,
            'msg': '创建成功',
            'data': pusher.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'创建推送器失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/pusher/<int:pusher_id>', methods=['PUT'])
def update_pusher_route(pusher_id):
    """更新推送器"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        pusher = update_pusher(pusher_id, **data)
        
        return jsonify({
            'code': 0,
            'msg': '更新成功',
            'data': pusher.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'更新推送器失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/pusher/<int:pusher_id>', methods=['DELETE'])
def delete_pusher_route(pusher_id):
    """删除推送器"""
    try:
        delete_pusher(pusher_id)
        return jsonify({
            'code': 0,
            'msg': '删除成功'
        })
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'删除推送器失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 心跳接收接口 ======================
@algorithm_task_bp.route('/heartbeat/extractor', methods=['POST'])
def receive_extractor_heartbeat():
    """接收抽帧器心跳"""
    try:
        data = request.get_json()
        extractor_id = data.get('extractor_id')
        server_ip = data.get('server_ip')
        port = data.get('port')
        process_id = data.get('process_id')
        log_path = data.get('log_path')
        task_id = data.get('task_id')
        
        if not extractor_id:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：extractor_id'
            }), 400
        
        extractor = FrameExtractor.query.get(extractor_id)
        if not extractor:
            return jsonify({
                'code': 404,
                'msg': f'抽帧器不存在：extractor_id={extractor_id}'
            }), 404
        
        # 更新心跳信息
        extractor.last_heartbeat = datetime.utcnow()
        if server_ip:
            extractor.server_ip = server_ip
        if port:
            extractor.port = port
        if process_id:
            extractor.process_id = process_id
        if log_path:
            extractor.log_path = log_path
        elif not extractor.log_path:
            # 如果没有log_path，根据extractor_id生成
            video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            log_base_dir = os.path.join(video_root, 'logs')
            extractor.log_path = os.path.join(log_base_dir, f'frame_extractor_{extractor_id}')
        if task_id:
            extractor.task_id = task_id
        
        # 更新状态为running
        if extractor.status != 'stopped':
            extractor.status = 'running'
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '心跳接收成功',
            'data': {
                'extractor_id': extractor.id,
                'extractor_name': extractor.extractor_name
            }
        })
    except Exception as e:
        logger.error(f"接收抽帧器心跳失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@algorithm_task_bp.route('/heartbeat/sorter', methods=['POST'])
def receive_sorter_heartbeat():
    """接收排序器心跳"""
    try:
        data = request.get_json()
        sorter_id = data.get('sorter_id')
        server_ip = data.get('server_ip')
        port = data.get('port')
        process_id = data.get('process_id')
        log_path = data.get('log_path')
        task_id = data.get('task_id')
        
        if not sorter_id:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：sorter_id'
            }), 400
        
        sorter = Sorter.query.get(sorter_id)
        if not sorter:
            return jsonify({
                'code': 404,
                'msg': f'排序器不存在：sorter_id={sorter_id}'
            }), 404
        
        # 更新心跳信息
        sorter.last_heartbeat = datetime.utcnow()
        if server_ip:
            sorter.server_ip = server_ip
        if port:
            sorter.port = port
        if process_id:
            sorter.process_id = process_id
        if log_path:
            sorter.log_path = log_path
        elif not sorter.log_path:
            # 如果没有log_path，根据sorter_id生成
            video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            log_base_dir = os.path.join(video_root, 'logs')
            sorter.log_path = os.path.join(log_base_dir, f'sorter_{sorter_id}')
        if task_id:
            sorter.task_id = task_id
        
        # 更新状态为running
        if sorter.status != 'stopped':
            sorter.status = 'running'
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '心跳接收成功',
            'data': {
                'sorter_id': sorter.id,
                'sorter_name': sorter.sorter_name
            }
        })
    except Exception as e:
        logger.error(f"接收排序器心跳失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@algorithm_task_bp.route('/heartbeat/pusher', methods=['POST'])
def receive_pusher_heartbeat():
    """接收推送器心跳"""
    try:
        data = request.get_json()
        pusher_id = data.get('pusher_id')
        server_ip = data.get('server_ip')
        port = data.get('port')
        process_id = data.get('process_id')
        log_path = data.get('log_path')
        task_id = data.get('task_id')
        
        if not pusher_id:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：pusher_id'
            }), 400
        
        pusher = Pusher.query.get(pusher_id)
        if not pusher:
            return jsonify({
                'code': 404,
                'msg': f'推送器不存在：pusher_id={pusher_id}'
            }), 404
        
        # 更新心跳信息
        pusher.last_heartbeat = datetime.utcnow()
        if server_ip:
            pusher.server_ip = server_ip
        if port:
            pusher.port = port
        if process_id:
            pusher.process_id = process_id
        if log_path:
            pusher.log_path = log_path
        elif not pusher.log_path:
            # 如果没有log_path，根据pusher_id生成
            video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            log_base_dir = os.path.join(video_root, 'logs')
            pusher.log_path = os.path.join(log_base_dir, f'pusher_{pusher_id}')
        if task_id:
            pusher.task_id = task_id
        
        # 更新状态为running
        if pusher.status != 'stopped':
            pusher.status = 'running'
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '心跳接收成功',
            'data': {
                'pusher_id': pusher.id,
                'pusher_name': pusher.pusher_name
            }
        })
    except Exception as e:
        logger.error(f"接收推送器心跳失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


# ====================== 日志查看接口 ======================
@algorithm_task_bp.route('/task/<int:task_id>/extractor/logs', methods=['GET'])
def get_task_extractor_logs(task_id):
    """获取算法任务的抽帧器日志"""
    try:
        from models import AlgorithmTask
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 404, 'msg': '算法任务不存在'}), 404
        
        if not task.extractor_id:
            return jsonify({'code': 400, 'msg': '该算法任务未配置抽帧器'}), 400
        
        extractor = FrameExtractor.query.get(task.extractor_id)
        if not extractor:
            return jsonify({'code': 404, 'msg': '抽帧器不存在'}), 404
        
        lines = int(request.args.get('lines', 100))
        date = request.args.get('date', '').strip()
        
        return get_service_logs(extractor, lines, date if date else None)
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f"获取抽帧器日志失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/sorter/logs', methods=['GET'])
def get_task_sorter_logs(task_id):
    """获取算法任务的排序器日志"""
    try:
        from models import AlgorithmTask
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 404, 'msg': '算法任务不存在'}), 404
        
        if not task.sorter_id:
            return jsonify({'code': 400, 'msg': '该算法任务未配置排序器'}), 400
        
        sorter = Sorter.query.get(task.sorter_id)
        if not sorter:
            return jsonify({'code': 404, 'msg': '排序器不存在'}), 404
        
        lines = int(request.args.get('lines', 100))
        date = request.args.get('date', '').strip()
        
        return get_service_logs(sorter, lines, date if date else None)
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f"获取排序器日志失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/pusher/logs', methods=['GET'])
def get_task_pusher_logs(task_id):
    """获取算法任务的推送器日志"""
    try:
        from models import AlgorithmTask
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 404, 'msg': '算法任务不存在'}), 404
        
        if not task.pusher_id:
            return jsonify({'code': 400, 'msg': '该算法任务未配置推送器'}), 400
        
        pusher = Pusher.query.get(task.pusher_id)
        if not pusher:
            return jsonify({'code': 404, 'msg': '推送器不存在'}), 404
        
        lines = int(request.args.get('lines', 100))
        date = request.args.get('date', '').strip()
        
        return get_service_logs(pusher, lines, date if date else None)
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f"获取推送器日志失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


def get_service_logs(service_obj, lines: int = 100, date: str = None):
    """获取服务日志的通用函数"""
    try:
        # 确定日志文件路径
        video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        log_base_dir = os.path.join(video_root, 'logs')
        
        if not service_obj.log_path:
            # 根据服务类型生成日志目录
            if isinstance(service_obj, FrameExtractor):
                service_log_dir = os.path.join(log_base_dir, f'frame_extractor_{service_obj.id}')
            elif isinstance(service_obj, Sorter):
                service_log_dir = os.path.join(log_base_dir, f'sorter_{service_obj.id}')
            elif isinstance(service_obj, Pusher):
                service_log_dir = os.path.join(log_base_dir, f'pusher_{service_obj.id}')
            else:
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

