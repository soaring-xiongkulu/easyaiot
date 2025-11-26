"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
from datetime import datetime
from operator import or_

from flask import Blueprint, request, jsonify
from sqlalchemy import func

from models import Playback, db

playback_bp = Blueprint('playback', __name__)
logger = logging.getLogger(__name__)


@playback_bp.route('/list', methods=['GET'])
def list_playbacks():
    """查询录像回放列表（支持分页和搜索）"""
    try:
        # 获取请求参数
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '').strip()
        device_id = request.args.get('device_id', '').strip()
        start_time = request.args.get('start_time', '').strip()
        end_time = request.args.get('end_time', '').strip()

        # 参数验证
        if page_no < 1 or page_size < 1:
            return jsonify({'code': 400, 'msg': '参数错误：pageNo和pageSize必须为正整数'}), 400

        # 构建基础查询
        query = Playback.query

        # 添加搜索条件
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                or_(
                    Playback.device_name.ilike(search_pattern),
                    Playback.device_id.ilike(search_pattern),
                    Playback.file_path.ilike(search_pattern)
                )
            )

        # 设备ID筛选
        if device_id:
            query = query.filter(Playback.device_id == device_id)

        # 时间范围筛选
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                query = query.filter(Playback.event_time >= start_dt)
            except ValueError:
                return jsonify({'code': 400, 'msg': '开始时间格式错误'}), 400

        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                query = query.filter(Playback.event_time <= end_dt)
            except ValueError:
                return jsonify({'code': 400, 'msg': '结束时间格式错误'}), 400

        # 按录制时间降序排序（最新的在前）
        query = query.order_by(Playback.event_time.desc())

        # 执行分页查询
        pagination = query.paginate(
            page=page_no,
            per_page=page_size,
            error_out=False
        )

        playback_list = [playback.to_dict() for playback in pagination.items]

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': playback_list,
            'total': pagination.total
        })

    except ValueError:
        return jsonify({'code': 400, 'msg': '参数类型错误：pageNo和pageSize需为整数'}), 400
    except Exception as e:
        logger.error(f'录像回放列表查询失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@playback_bp.route('/<int:playback_id>', methods=['GET'])
def get_playback_info(playback_id):
    """获取单个录像回放详情"""
    try:
        playback = Playback.query.get_or_404(playback_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': playback.to_dict()
        })
    except Exception as e:
        logger.error(f'获取录像回放详情失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@playback_bp.route('/', methods=['POST'])
def create_playback():
    """创建录像回放记录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400

        # 验证必填字段
        required_fields = ['file_path', 'event_time', 'device_id', 'device_name', 'duration']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'code': 400, 'msg': f'{field}不能为空'}), 400

        # 解析时间
        try:
            event_time = datetime.fromisoformat(data['event_time'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return jsonify({'code': 400, 'msg': 'event_time格式错误，应为ISO格式'}), 400

        # 创建录像回放记录
        playback = Playback(
            file_path=data['file_path'],
            event_time=event_time,
            device_id=data['device_id'],
            device_name=data['device_name'],
            duration=int(data['duration']),
            thumbnail_path=data.get('thumbnail_path'),
            file_size=data.get('file_size')
        )

        db.session.add(playback)
        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '录像回放记录创建成功',
            'data': playback.to_dict()
        })
    except ValueError as e:
        db.session.rollback()
        logger.error(f'创建录像回放记录失败: {str(e)}')
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'创建录像回放记录失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@playback_bp.route('/<int:playback_id>', methods=['PUT'])
def update_playback(playback_id):
    """更新录像回放记录"""
    try:
        playback = Playback.query.get_or_404(playback_id)
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400

        # 更新字段
        if 'file_path' in data:
            playback.file_path = data['file_path']
        if 'event_time' in data:
            try:
                playback.event_time = datetime.fromisoformat(data['event_time'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return jsonify({'code': 400, 'msg': 'event_time格式错误'}), 400
        if 'device_id' in data:
            playback.device_id = data['device_id']
        if 'device_name' in data:
            playback.device_name = data['device_name']
        if 'duration' in data:
            playback.duration = int(data['duration'])
        if 'thumbnail_path' in data:
            playback.thumbnail_path = data['thumbnail_path']
        if 'file_size' in data:
            playback.file_size = data['file_size']

        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '录像回放记录更新成功',
            'data': playback.to_dict()
        })
    except ValueError as e:
        db.session.rollback()
        logger.error(f'更新录像回放记录失败: {str(e)}')
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新录像回放记录失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@playback_bp.route('/<int:playback_id>', methods=['DELETE'])
def delete_playback(playback_id):
    """删除录像回放记录"""
    try:
        playback = Playback.query.get_or_404(playback_id)
        db.session.delete(playback)
        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': '录像回放记录删除成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除录像回放记录失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@playback_bp.route('/thumbnail/<int:playback_id>', methods=['GET'])
def get_playback_thumbnail(playback_id):
    """获取录像回放封面图"""
    try:
        playback = Playback.query.get_or_404(playback_id)
        if not playback.thumbnail_path:
            return jsonify({'code': 404, 'msg': '该录像没有封面图'}), 404

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'thumbnail_path': playback.thumbnail_path
            }
        })
    except Exception as e:
        logger.error(f'获取录像回放封面图失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500


@playback_bp.route('/statistics', methods=['GET'])
def get_playback_statistics():
    """获取录像回放统计信息"""
    try:
        device_id = request.args.get('device_id', '').strip()
        start_time = request.args.get('start_time', '').strip()
        end_time = request.args.get('end_time', '').strip()

        query = Playback.query

        if device_id:
            query = query.filter(Playback.device_id == device_id)

        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                query = query.filter(Playback.event_time >= start_dt)
            except ValueError:
                return jsonify({'code': 400, 'msg': '开始时间格式错误'}), 400

        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                query = query.filter(Playback.event_time <= end_dt)
            except ValueError:
                return jsonify({'code': 400, 'msg': '结束时间格式错误'}), 400

        total_count = query.count()
        
        # 使用子查询优化统计
        stats_query = query.with_entities(
            func.sum(Playback.duration).label('total_duration'),
            func.sum(Playback.file_size).label('total_size')
        ).first()
        
        total_duration = int(stats_query.total_duration) if stats_query.total_duration else 0
        total_size = int(stats_query.total_size) if stats_query.total_size else 0

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'total_count': total_count,
                'total_duration': int(total_duration),
                'total_size': int(total_size) if total_size else 0
            }
        })
    except Exception as e:
        logger.error(f'获取录像回放统计信息失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500

