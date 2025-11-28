"""
监控录像空间管理路由
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
from flask import Blueprint, request, jsonify, send_file
from io import BytesIO

from models import db
from app.services.record_space_service import (
    create_record_space, update_record_space, delete_record_space,
    get_record_space, list_record_spaces, get_record_space_by_device_id
)
from app.services.record_video_service import (
    list_record_videos, delete_record_videos, get_record_video, cleanup_old_videos_by_days
)

record_bp = Blueprint('record', __name__)
logger = logging.getLogger(__name__)


# ====================== 监控录像空间管理接口 ======================
@record_bp.route('/space/list', methods=['GET'])
def list_spaces():
    """查询监控录像空间列表"""
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '').strip() or None
        
        result = list_record_spaces(page_no, page_size, search)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result['items'],
            'total': result['total']
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'查询监控录像空间列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@record_bp.route('/space/<int:space_id>', methods=['GET'])
def get_space(space_id):
    """获取监控录像空间详情"""
    try:
        space = get_record_space(space_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': space.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'获取监控录像空间失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@record_bp.route('/space/device/<device_id>', methods=['GET'])
def get_space_by_device(device_id):
    """根据设备ID获取监控录像空间"""
    try:
        space = get_record_space_by_device_id(device_id)
        if not space:
            return jsonify({
                'code': 404,
                'msg': f'设备 {device_id} 没有关联的监控录像空间'
            }), 404
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': space.to_dict()
        })
    except Exception as e:
        logger.error(f'根据设备ID获取监控录像空间失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@record_bp.route('/space', methods=['POST'])
def create_space():
    """创建监控录像空间（已禁用：监控录像空间现在跟随设备自动创建）"""
    return jsonify({
        'code': 403,
        'msg': '监控录像空间不能手动创建，系统会在创建设备时自动创建监控录像空间'
    }), 403


@record_bp.route('/space/<int:space_id>', methods=['PUT'])
def update_space(space_id):
    """更新监控录像空间"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        space_name = data.get('space_name', '').strip() if 'space_name' in data else None
        save_mode = data.get('save_mode') if 'save_mode' in data else None
        save_time = data.get('save_time') if 'save_time' in data else None
        description = data.get('description', '').strip() if 'description' in data else None
        
        space = update_record_space(space_id, space_name, save_mode, save_time, description)
        return jsonify({
            'code': 0,
            'msg': '监控录像空间更新成功',
            'data': space.to_dict()
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'更新监控录像空间失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@record_bp.route('/space/<int:space_id>', methods=['DELETE'])
def delete_space(space_id):
    """删除监控录像空间（已禁用：监控录像空间跟随设备，删除设备时会自动删除）"""
    try:
        # 检查监控录像空间是否有关联的设备
        space = get_record_space(space_id)
        if space.device_id:
            return jsonify({
                'code': 403,
                'msg': '监控录像空间跟随设备，不能单独删除。请删除关联的设备，监控录像空间会自动删除。'
            }), 403
        
        # 如果没有关联设备，允许删除（兼容旧数据）
        delete_record_space(space_id)
        return jsonify({
            'code': 0,
            'msg': '监控录像空间删除成功'
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'删除监控录像空间失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 监控录像管理接口 ======================
@record_bp.route('/space/<int:space_id>/videos', methods=['GET'])
def list_videos(space_id):
    """获取监控录像列表"""
    try:
        device_id = request.args.get('device_id')
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 20))
        
        result = list_record_videos(space_id, device_id, page_no, page_size)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result['items'],
            'total': result['total']
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'获取监控录像列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@record_bp.route('/space/<int:space_id>/video/<path:object_name>', methods=['GET'])
def get_video(space_id, object_name):
    """获取监控录像内容"""
    try:
        content, content_type, filename = get_record_video(space_id, object_name)
        return send_file(
            BytesIO(content),
            mimetype=content_type,
            as_attachment=False,
            download_name=filename
        )
    except ValueError as e:
        return jsonify({'code': 404, 'msg': str(e)}), 404
    except Exception as e:
        logger.error(f'获取监控录像失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@record_bp.route('/space/<int:space_id>/videos', methods=['DELETE'])
def delete_videos(space_id):
    """批量删除监控录像"""
    try:
        data = request.get_json()
        if not data or 'object_names' not in data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空，需要提供 object_names 数组'}), 400
        
        object_names = data.get('object_names', [])
        if not isinstance(object_names, list) or len(object_names) == 0:
            return jsonify({'code': 400, 'msg': 'object_names 必须是非空数组'}), 400
        
        result = delete_record_videos(space_id, object_names)
        return jsonify({
            'code': 0,
            'msg': '删除成功',
            'data': result
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'批量删除监控录像失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@record_bp.route('/space/<int:space_id>/videos/cleanup', methods=['POST'])
def cleanup_videos(space_id):
    """清理过期的监控录像"""
    try:
        data = request.get_json()
        if not data or 'days' not in data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空，需要提供 days 参数'}), 400
        
        days = int(data.get('days', 0))
        if days < 0:
            return jsonify({'code': 400, 'msg': 'days 必须大于等于0'}), 400
        
        result = cleanup_old_videos_by_days(space_id, days)
        return jsonify({
            'code': 0,
            'msg': '清理完成',
            'data': result
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'清理过期监控录像失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500

