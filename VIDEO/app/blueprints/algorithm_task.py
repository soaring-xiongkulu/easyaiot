"""
算法任务、抽帧器、排序器管理路由
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
from flask import Blueprint, request, jsonify

from models import db
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
            description=data.get('description'),
            is_enabled=data.get('is_enabled', False)
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

