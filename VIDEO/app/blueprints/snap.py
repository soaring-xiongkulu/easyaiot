"""
抓拍空间和任务管理路由
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
from flask import Blueprint, request, jsonify

from models import db, DetectionRegion
from app.services.snap_space_service import (
    create_snap_space, update_snap_space, delete_snap_space,
    get_snap_space, list_snap_spaces
)
from app.services.snap_task_service import (
    create_snap_task, update_snap_task, delete_snap_task,
    get_snap_task, list_snap_tasks, start_task, stop_task, restart_task, get_task_logs
)
from app.services.algorithm_service import (
    create_task_algorithm_service, update_task_algorithm_service, delete_task_algorithm_service,
    get_task_algorithm_services, create_region_algorithm_service, update_region_algorithm_service,
    delete_region_algorithm_service, get_region_algorithm_services
)
from app.services.storage_service import (
    get_or_create_device_storage_config, update_device_storage_config,
    get_device_storage_info, check_and_cleanup_storage
)
from app.services.snap_image_service import (
    list_snap_images, delete_snap_images, get_snap_image, cleanup_old_images_by_days
)

snap_bp = Blueprint('snap', __name__)
logger = logging.getLogger(__name__)


# ====================== 抓拍空间管理接口 ======================
@snap_bp.route('/space/list', methods=['GET'])
def list_spaces():
    """查询抓拍空间列表"""
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '').strip() or None
        
        result = list_snap_spaces(page_no, page_size, search)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result['items'],
            'total': result['total']
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'查询抓拍空间列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/space/<int:space_id>', methods=['GET'])
def get_space(space_id):
    """获取抓拍空间详情"""
    try:
        space = get_snap_space(space_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': space.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'获取抓拍空间失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/space', methods=['POST'])
def create_space():
    """创建抓拍空间"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        space_name = data.get('space_name', '').strip()
        if not space_name:
            return jsonify({'code': 400, 'msg': '空间名称不能为空'}), 400
        
        save_mode = data.get('save_mode', 0)
        save_time = data.get('save_time', 0)
        description = data.get('description', '').strip() or None
        device_id = data.get('device_id', '').strip() or None
        
        space = create_snap_space(space_name, save_mode, save_time, description, device_id)
        return jsonify({
            'code': 0,
            'msg': '抓拍空间创建成功',
            'data': space.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'创建抓拍空间失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/space/<int:space_id>', methods=['PUT'])
def update_space(space_id):
    """更新抓拍空间"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        space_name = data.get('space_name', '').strip() if 'space_name' in data else None
        save_mode = data.get('save_mode') if 'save_mode' in data else None
        save_time = data.get('save_time') if 'save_time' in data else None
        description = data.get('description', '').strip() if 'description' in data else None
        
        space = update_snap_space(space_id, space_name, save_mode, save_time, description)
        return jsonify({
            'code': 0,
            'msg': '抓拍空间更新成功',
            'data': space.to_dict()
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'更新抓拍空间失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/space/<int:space_id>', methods=['DELETE'])
def delete_space(space_id):
    """删除抓拍空间"""
    try:
        delete_snap_space(space_id)
        return jsonify({
            'code': 0,
            'msg': '抓拍空间删除成功'
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'删除抓拍空间失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 抓拍任务管理接口 ======================
@snap_bp.route('/task/list', methods=['GET'])
def list_tasks():
    """查询抓拍任务列表"""
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        space_id = request.args.get('space_id')
        device_id = request.args.get('device_id')
        search = request.args.get('search', '').strip() or None
        status = request.args.get('status')
        
        space_id_int = int(space_id) if space_id else None
        status_int = int(status) if status else None
        
        result = list_snap_tasks(page_no, page_size, space_id_int, device_id, search, status_int)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result['items'],
            'total': result['total']
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'查询抓拍任务列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/task/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """获取抓拍任务详情"""
    try:
        task = get_snap_task(task_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': task
        })
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'获取抓拍任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/task', methods=['POST'])
def create_task():
    """创建抓拍任务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        task_name = data.get('task_name', '').strip()
        if not task_name:
            return jsonify({'code': 400, 'msg': '任务名称不能为空'}), 400
        
        space_id = data.get('space_id')
        if not space_id:
            return jsonify({'code': 400, 'msg': '抓拍空间ID不能为空'}), 400
        
        device_id = data.get('device_id', '').strip()
        if not device_id:
            return jsonify({'code': 400, 'msg': '设备ID不能为空'}), 400
        
        task = create_snap_task(
            task_name=task_name,
            space_id=int(space_id),
            device_id=device_id,
            capture_type=data.get('capture_type', 0),
            cron_expression=data.get('cron_expression', '0 */5 * * * *'),
            frame_skip=data.get('frame_skip', 1),
            algorithm_enabled=data.get('algorithm_enabled', False),
            algorithm_type=data.get('algorithm_type'),
            algorithm_model_id=data.get('algorithm_model_id'),
            algorithm_threshold=data.get('algorithm_threshold'),
            algorithm_night_mode=data.get('algorithm_night_mode', False),
            alarm_enabled=data.get('alarm_enabled', False),
            alarm_type=data.get('alarm_type', 0),
            phone_number=data.get('phone_number'),
            email=data.get('email'),
            notify_users=data.get('notify_users'),
            notify_methods=data.get('notify_methods'),
            alarm_suppress_time=data.get('alarm_suppress_time', 300),
            auto_filename=data.get('auto_filename', True),
            custom_filename_prefix=data.get('custom_filename_prefix')
        )
        
        task_dict = task.to_dict()
        from models import Device
        device = Device.query.get(device_id)
        if device:
            task_dict['device_name'] = device.name
        
        return jsonify({
            'code': 0,
            'msg': '抓拍任务创建成功',
            'data': task_dict
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'创建抓拍任务失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新抓拍任务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        update_data = {}
        if 'task_name' in data:
            update_data['task_name'] = data.get('task_name', '').strip()
        if 'space_id' in data:
            update_data['space_id'] = data.get('space_id')
        if 'device_id' in data:
            update_data['device_id'] = data.get('device_id', '').strip()
        if 'capture_type' in data:
            update_data['capture_type'] = data.get('capture_type')
        if 'cron_expression' in data:
            update_data['cron_expression'] = data.get('cron_expression')
        if 'frame_skip' in data:
            update_data['frame_skip'] = data.get('frame_skip')
        if 'algorithm_enabled' in data:
            update_data['algorithm_enabled'] = data.get('algorithm_enabled')
        if 'algorithm_type' in data:
            update_data['algorithm_type'] = data.get('algorithm_type')
        if 'algorithm_model_id' in data:
            update_data['algorithm_model_id'] = data.get('algorithm_model_id')
        if 'algorithm_threshold' in data:
            update_data['algorithm_threshold'] = data.get('algorithm_threshold')
        if 'algorithm_night_mode' in data:
            update_data['algorithm_night_mode'] = data.get('algorithm_night_mode')
        if 'alarm_enabled' in data:
            update_data['alarm_enabled'] = data.get('alarm_enabled')
        if 'alarm_type' in data:
            update_data['alarm_type'] = data.get('alarm_type')
        if 'phone_number' in data:
            update_data['phone_number'] = data.get('phone_number')
        if 'email' in data:
            update_data['email'] = data.get('email')
        if 'notify_users' in data:
            update_data['notify_users'] = data.get('notify_users')
        if 'notify_methods' in data:
            update_data['notify_methods'] = data.get('notify_methods')
        if 'alarm_suppress_time' in data:
            update_data['alarm_suppress_time'] = data.get('alarm_suppress_time')
        if 'auto_filename' in data:
            update_data['auto_filename'] = data.get('auto_filename')
        if 'custom_filename_prefix' in data:
            update_data['custom_filename_prefix'] = data.get('custom_filename_prefix')
        if 'is_enabled' in data:
            update_data['is_enabled'] = data.get('is_enabled')
        
        task = update_snap_task(task_id, **update_data)
        task_dict = task.to_dict()
        from models import Device
        device = Device.query.get(task.device_id)
        if device:
            task_dict['device_name'] = device.name
        
        return jsonify({
            'code': 0,
            'msg': '抓拍任务更新成功',
            'data': task_dict
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'更新抓拍任务失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除抓拍任务"""
    try:
        delete_snap_task(task_id)
        return jsonify({
            'code': 0,
            'msg': '抓拍任务删除成功'
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'删除抓拍任务失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/task/<int:task_id>/start', methods=['POST'])
def start_task_route(task_id):
    """启动抓拍任务"""
    try:
        task = start_task(task_id)
        return jsonify({
            'code': 0,
            'msg': '任务已启动',
            'data': task.to_dict()
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'启动任务失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/task/<int:task_id>/stop', methods=['POST'])
def stop_task_route(task_id):
    """停止抓拍任务"""
    try:
        task = stop_task(task_id)
        return jsonify({
            'code': 0,
            'msg': '任务已停止',
            'data': task.to_dict()
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'停止任务失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/task/<int:task_id>/restart', methods=['POST'])
def restart_task_route(task_id):
    """重启抓拍任务"""
    try:
        task = restart_task(task_id)
        return jsonify({
            'code': 0,
            'msg': '任务已重启',
            'data': task.to_dict()
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'重启任务失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/task/<int:task_id>/logs', methods=['GET'])
def get_task_logs_route(task_id):
    """获取任务日志"""
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 50))
        level = request.args.get('level', '').strip() or None
        
        result = get_task_logs(task_id, page_no, page_size, level)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result['logs'],
            'total': result['total']
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'获取任务日志失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 检测区域管理接口 ======================
@snap_bp.route('/task/<int:task_id>/regions', methods=['GET'])
def list_regions(task_id):
    """查询任务的检测区域列表"""
    try:
        regions = DetectionRegion.query.filter_by(task_id=task_id).order_by(DetectionRegion.sort_order, DetectionRegion.id).all()
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': [region.to_dict() for region in regions]
        })
    except Exception as e:
        logger.error(f'查询检测区域列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/region/<int:region_id>', methods=['GET'])
def get_region(region_id):
    """获取检测区域详情"""
    try:
        region = DetectionRegion.query.get_or_404(region_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': region.to_dict()
        })
    except Exception as e:
        logger.error(f'获取检测区域失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/region', methods=['POST'])
def create_region():
    """创建检测区域"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        task_id = data.get('task_id')
        if not task_id:
            return jsonify({'code': 400, 'msg': '任务ID不能为空'}), 400
        
        region_name = data.get('region_name', '').strip()
        if not region_name:
            return jsonify({'code': 400, 'msg': '区域名称不能为空'}), 400
        
        points = data.get('points')
        if not points or not isinstance(points, list) or len(points) < 3:
            return jsonify({'code': 400, 'msg': '区域坐标点不能为空，且至少需要3个点'}), 400
        
        import json
        region = DetectionRegion(
            task_id=task_id,
            region_name=region_name,
            region_type=data.get('region_type', 'polygon'),
            points=json.dumps(points),
            image_id=data.get('image_id'),
            algorithm_type=data.get('algorithm_type'),
            algorithm_model_id=data.get('algorithm_model_id'),
            algorithm_threshold=data.get('algorithm_threshold'),
            algorithm_enabled=data.get('algorithm_enabled', True),
            color=data.get('color', '#FF5252'),
            opacity=data.get('opacity', 0.3),
            is_enabled=data.get('is_enabled', True),
            sort_order=data.get('sort_order', 0)
        )
        
        db.session.add(region)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '检测区域创建成功',
            'data': region.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'创建检测区域失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/region/<int:region_id>', methods=['PUT'])
def update_region(region_id):
    """更新检测区域"""
    try:
        region = DetectionRegion.query.get_or_404(region_id)
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        if 'region_name' in data:
            region.region_name = data.get('region_name', '').strip()
        if 'region_type' in data:
            region.region_type = data.get('region_type', 'polygon')
        if 'points' in data:
            import json
            points = data.get('points')
            if not points or not isinstance(points, list) or len(points) < 3:
                return jsonify({'code': 400, 'msg': '区域坐标点不能为空，且至少需要3个点'}), 400
            region.points = json.dumps(points)
        if 'image_id' in data:
            region.image_id = data.get('image_id')
        if 'algorithm_type' in data:
            region.algorithm_type = data.get('algorithm_type')
        if 'algorithm_model_id' in data:
            region.algorithm_model_id = data.get('algorithm_model_id')
        if 'algorithm_threshold' in data:
            region.algorithm_threshold = data.get('algorithm_threshold')
        if 'algorithm_enabled' in data:
            region.algorithm_enabled = data.get('algorithm_enabled', True)
        if 'color' in data:
            region.color = data.get('color', '#FF5252')
        if 'opacity' in data:
            region.opacity = data.get('opacity', 0.3)
        if 'is_enabled' in data:
            region.is_enabled = data.get('is_enabled', True)
        if 'sort_order' in data:
            region.sort_order = data.get('sort_order', 0)
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '检测区域更新成功',
            'data': region.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新检测区域失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/region/<int:region_id>', methods=['DELETE'])
def delete_region(region_id):
    """删除检测区域"""
    try:
        region = DetectionRegion.query.get_or_404(region_id)
        db.session.delete(region)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '检测区域删除成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除检测区域失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 算法模型服务配置接口 ======================
@snap_bp.route('/task/<int:task_id>/services', methods=['GET'])
def list_task_services(task_id):
    """获取任务的算法模型服务配置列表"""
    try:
        services = get_task_algorithm_services(task_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': [s.to_dict() for s in services]
        })
    except Exception as e:
        logger.error(f'获取任务算法服务配置失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/task/<int:task_id>/service', methods=['POST'])
def create_task_service(task_id):
    """创建任务的算法模型服务配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        service_name = data.get('service_name', '').strip()
        if not service_name:
            return jsonify({'code': 400, 'msg': '服务名称不能为空'}), 400
        
        service_url = data.get('service_url', '').strip()
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
            'msg': '算法服务配置创建成功',
            'data': service.to_dict()
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'创建算法服务配置失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/service/<int:service_id>', methods=['PUT'])
def update_task_service(service_id):
    """更新任务的算法模型服务配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        service = update_task_algorithm_service(service_id, **data)
        return jsonify({
            'code': 0,
            'msg': '算法服务配置更新成功',
            'data': service.to_dict()
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'更新算法服务配置失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/service/<int:service_id>', methods=['DELETE'])
def delete_task_service(service_id):
    """删除任务的算法模型服务配置"""
    try:
        delete_task_algorithm_service(service_id)
        return jsonify({
            'code': 0,
            'msg': '算法服务配置删除成功'
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'删除算法服务配置失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/region/<int:region_id>/services', methods=['GET'])
def list_region_services(region_id):
    """获取区域的算法模型服务配置列表"""
    try:
        services = get_region_algorithm_services(region_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': [s.to_dict() for s in services]
        })
    except Exception as e:
        logger.error(f'获取区域算法服务配置失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/region/<int:region_id>/service', methods=['POST'])
def create_region_service(region_id):
    """创建区域的算法模型服务配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        service_name = data.get('service_name', '').strip()
        if not service_name:
            return jsonify({'code': 400, 'msg': '服务名称不能为空'}), 400
        
        service_url = data.get('service_url', '').strip()
        if not service_url:
            return jsonify({'code': 400, 'msg': '服务URL不能为空'}), 400
        
        service = create_region_algorithm_service(
            region_id=region_id,
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
            'msg': '区域算法服务配置创建成功',
            'data': service.to_dict()
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'创建区域算法服务配置失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/region-service/<int:service_id>', methods=['PUT'])
def update_region_service(service_id):
    """更新区域的算法模型服务配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        service = update_region_algorithm_service(service_id, **data)
        return jsonify({
            'code': 0,
            'msg': '区域算法服务配置更新成功',
            'data': service.to_dict()
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'更新区域算法服务配置失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/region-service/<int:service_id>', methods=['DELETE'])
def delete_region_service(service_id):
    """删除区域的算法模型服务配置"""
    try:
        delete_region_algorithm_service(service_id)
        return jsonify({
            'code': 0,
            'msg': '区域算法服务配置删除成功'
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'删除区域算法服务配置失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 设备存储配置接口 ======================
@snap_bp.route('/device/<device_id>/storage', methods=['GET'])
def get_device_storage(device_id):
    """获取设备存储配置和信息"""
    try:
        config = get_or_create_device_storage_config(device_id)
        storage_info = get_device_storage_info(device_id)
        
        result = config.to_dict()
        result.update(storage_info)
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result
        })
    except Exception as e:
        logger.error(f'获取设备存储配置失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/device/<device_id>/storage', methods=['PUT'])
def update_device_storage(device_id):
    """更新设备存储配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        config = update_device_storage_config(device_id, **data)
        return jsonify({
            'code': 0,
            'msg': '设备存储配置更新成功',
            'data': config.to_dict()
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'更新设备存储配置失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/device/<device_id>/storage/cleanup', methods=['POST'])
def cleanup_device_storage(device_id):
    """手动触发设备存储清理"""
    try:
        result = check_and_cleanup_storage(device_id)
        return jsonify({
            'code': 0,
            'msg': '存储清理完成',
            'data': result
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'清理设备存储失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 抓拍图片管理接口 ======================
@snap_bp.route('/space/<int:space_id>/images', methods=['GET'])
def list_space_images(space_id):
    """获取抓拍空间图片列表"""
    try:
        device_id = request.args.get('device_id', '').strip() or None
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 20))
        
        result = list_snap_images(space_id, device_id, page_no, page_size)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result['items'],
            'total': result['total']
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'获取抓拍图片列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/space/<int:space_id>/image/<path:object_name>', methods=['GET'])
def get_space_image(space_id, object_name):
    """获取抓拍图片内容"""
    try:
        from flask import Response
        content, content_type, filename = get_snap_image(space_id, object_name)
        return Response(
            content,
            mimetype=content_type,
            headers={'Content-Disposition': f'inline; filename="{filename}"'}
        )
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'获取抓拍图片失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/space/<int:space_id>/images', methods=['DELETE'])
def delete_space_images(space_id):
    """批量删除抓拍图片"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        object_names = data.get('object_names', [])
        if not object_names or not isinstance(object_names, list):
            return jsonify({'code': 400, 'msg': 'object_names必须是非空数组'}), 400
        
        result = delete_snap_images(space_id, object_names)
        return jsonify({
            'code': 0,
            'msg': '删除完成',
            'data': result
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'批量删除抓拍图片失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@snap_bp.route('/space/<int:space_id>/images/cleanup', methods=['POST'])
def cleanup_space_images(space_id):
    """清理过期的抓拍图片"""
    try:
        data = request.get_json() or {}
        days = int(data.get('days', 0))
        
        if days <= 0:
            return jsonify({'code': 400, 'msg': 'days必须大于0'}), 400
        
        result = cleanup_old_images_by_days(space_id, days)
        return jsonify({
            'code': 0,
            'msg': '清理完成',
            'data': result
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'清理过期图片失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500

