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
    get_record_space, list_record_spaces, get_record_space_by_device_id, sync_spaces_to_minio
)
from app.services.record_video_service import (
    list_record_videos, delete_record_videos, get_record_video, cleanup_old_videos_by_save_time,
    sync_record_videos_metadata, list_record_video_dates, list_record_videos_day_detail,
    find_segment_for_alert,
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
        parent_key = request.args.get('parentKey', 'root').strip() or 'root'
        scope = request.args.get('scope', '').strip() or None

        result = list_record_spaces(page_no, page_size, search, parent_key, scope)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result['items'],
            'total': result['total'],
            'parent_key': result.get('parent_key', 'root'),
            'breadcrumbs': result.get('breadcrumbs', []),
            'is_search': result.get('is_search', False),
            'scope': result.get('scope'),
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
        return jsonify({'code': 400, 'msg': str(e)}), 400
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
                'code': 400,
                'msg': f'设备 {device_id} 没有关联的监控录像空间'
            }), 400
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
        save_time_custom = data.get('save_time_custom') if 'save_time_custom' in data else None
        description = data.get('description', '').strip() if 'description' in data else None
        
        try:
            space = update_record_space(
                space_id, space_name, save_mode, save_time, description, save_time_custom,
            )
        except ValueError as ve:
            return jsonify({'code': 400, 'msg': str(ve)}), 400
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


@record_bp.route('/space/group-policy', methods=['PUT'])
def update_group_policy():
    """更新 NVR / GB28181 分组默认录像保存时间，联动非自定义子设备。"""
    try:
        data = request.get_json() or {}
        group_type = (data.get('group_type') or '').strip().lower()
        group_key = str(data.get('group_key') or '').strip()
        save_time = data.get('save_time')
        if save_time is None:
            return jsonify({'code': 400, 'msg': 'save_time 不能为空'}), 400

        from app.services.space_group_save_time_service import update_group_save_time
        from app.services.space_save_time_service import SPACE_KIND_RECORD

        policy, updated = update_group_save_time(group_type, group_key, SPACE_KIND_RECORD, save_time)
        return jsonify({
            'code': 0,
            'msg': f'分组存储策略已更新，已同步 {updated} 个非自定义设备空间',
            'data': {
                'group_type': policy.group_type,
                'group_key': policy.group_key,
                'save_time': policy.record_save_time,
                'updated_count': updated,
            },
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'更新分组录像存储策略失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@record_bp.route('/space/<int:space_id>', methods=['DELETE'])
def delete_space(space_id):
    """删除监控录像空间"""
    try:
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


@record_bp.route('/space/sync/minio', methods=['POST'])
def sync_spaces_minio():
    """同步所有监控录像空间到Minio，创建不存在的目录"""
    try:
        result = sync_spaces_to_minio()
        return jsonify({
            'code': 0,
            'msg': '同步完成',
            'data': result
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'同步监控录像空间到Minio失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 监控录像管理接口 ======================
@record_bp.route('/space/<int:space_id>/videos/dates', methods=['GET'])
def list_video_dates(space_id):
    """列出有录像的日期"""
    try:
        device_id = request.args.get('device_id')
        dates = list_record_video_dates(space_id, device_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': dates,
        })
    except Exception as e:
        logger.error(f'获取录像日期列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@record_bp.route('/space/<int:space_id>/videos/day', methods=['GET'])
def list_videos_by_day(space_id):
    """获取指定日期的录像片段详情（含时间轴与告警关联）"""
    try:
        date_str = request.args.get('date', '').strip()
        if not date_str:
            return jsonify({'code': 400, 'msg': 'date 参数不能为空（格式 YYYY-MM-DD）'}), 400
        device_id = request.args.get('device_id')
        result = list_record_videos_day_detail(space_id, date_str, device_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result,
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'获取日录像详情失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@record_bp.route('/space/device/<device_id>/resolve-alert', methods=['GET'])
def resolve_alert_segment(device_id):
    """根据告警 ID 定位录像片段（供告警页跳转回放）"""
    try:
        alert_id = request.args.get('alert_id') or request.args.get('alertId')
        if not alert_id:
            return jsonify({'code': 400, 'msg': 'alert_id 参数不能为空'}), 400
        result = find_segment_for_alert(device_id, int(alert_id))
        if not result:
            return jsonify({'code': 404, 'msg': '未找到告警或关联录像空间'}), 404
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result,
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'定位告警录像片段失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@record_bp.route('/space/<int:space_id>/videos', methods=['GET'])
def list_videos(space_id):
    """获取监控录像列表"""
    try:
        device_id = request.args.get('device_id')
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 20))
        search = request.args.get('search', '').strip() or None
        start_time = request.args.get('startTime')
        end_time = request.args.get('endTime')

        from datetime import datetime
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None

        result = list_record_videos(space_id, device_id, page_no, page_size, search, start_dt, end_dt)
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
        return jsonify({'code': 400, 'msg': str(e)}), 400
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


@record_bp.route('/space/<int:space_id>/videos/sync', methods=['POST'])
def sync_videos_metadata(space_id):
    """从 MinIO 同步录像元数据到数据库（历史数据回填）"""
    try:
        result = sync_record_videos_metadata(space_id)
        return jsonify({
            'code': 0,
            'msg': '同步完成',
            'data': result
        })
    except RuntimeError as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500
    except Exception as e:
        logger.error(f'同步录像元数据失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@record_bp.route('/space/<int:space_id>/videos/cleanup', methods=['POST'])
def cleanup_videos(space_id):
    """清理过期的监控录像"""
    try:
        data = request.get_json()
        if not data or 'save_time_hours' not in data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空，需要提供 save_time_hours 参数'}), 400

        save_time_hours = int(data.get('save_time_hours', 0))
        if save_time_hours <= 0:
            return jsonify({'code': 400, 'msg': 'save_time_hours 必须大于 0'}), 400

        result = cleanup_old_videos_by_save_time(space_id, save_time_hours)
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

