"""
摄像头巡检会话 API
"""
import json
import logging
import queue

from flask import Blueprint, request, jsonify, Response, stream_with_context

from models import db
from app.services.patrol_session_service import (
    create_patrol_session,
    get_patrol_session,
    start_patrol_session,
    stop_patrol_session,
    receive_patrol_heartbeat,
    build_session_stats_payload,
    resolve_directory_device_ids,
    broadcast_patrol_session,
)
from app.services.patrol_progress_hub import subscribe, unsubscribe

patrol_bp = Blueprint('patrol', __name__)
logger = logging.getLogger(__name__)


@patrol_bp.route('/session', methods=['POST'])
def create_session():
    try:
        data = request.get_json() or {}
        session = create_patrol_session(data)
        return jsonify({'code': 0, 'msg': 'success', 'data': session.to_dict()})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('创建巡检会话失败: %s', e, exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@patrol_bp.route('/session/<int:session_id>', methods=['GET'])
def get_session(session_id):
    session = get_patrol_session(session_id)
    if not session:
        return jsonify({'code': 404, 'msg': '巡检会话不存在'}), 404
    return jsonify({'code': 0, 'msg': 'success', 'data': session.to_dict()})


@patrol_bp.route('/session/<int:session_id>/start', methods=['POST'])
def start_session(session_id):
    try:
        ok, msg = start_patrol_session(session_id)
        session = get_patrol_session(session_id)
        code = 0 if ok else 400
        return jsonify({
            'code': code,
            'msg': msg,
            'data': session.to_dict() if session else None,
        }), (200 if ok else 400)
    except Exception as e:
        logger.error('启动巡检失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': str(e)}), 500


@patrol_bp.route('/session/<int:session_id>/stop', methods=['POST'])
def stop_session(session_id):
    try:
        ok, msg = stop_patrol_session(session_id)
        session = get_patrol_session(session_id)
        return jsonify({'code': 0 if ok else 400, 'msg': msg, 'data': session.to_dict() if session else None})
    except Exception as e:
        logger.error('停止巡检失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': str(e)}), 500


@patrol_bp.route('/session/<int:session_id>/stats', methods=['GET'])
def session_stats(session_id):
    session = get_patrol_session(session_id)
    if not session:
        return jsonify({'code': 404, 'msg': '巡检会话不存在'}), 404
    return jsonify({
        'code': 0,
        'msg': 'success',
        'data': build_session_stats_payload(session),
    })


@patrol_bp.route('/session/<int:session_id>/events', methods=['GET'])
def session_events(session_id):
    session = get_patrol_session(session_id)
    if not session:
        return jsonify({'code': 404, 'msg': '巡检会话不存在'}), 404

    def generate():
        q = subscribe(session_id)
        try:
            initial = build_session_stats_payload(session)
            yield f"event: progress\ndata: {json.dumps(initial, ensure_ascii=False)}\n\n"
            while True:
                try:
                    msg = q.get(timeout=25)
                    event_type = msg.get('type', 'progress')
                    data = json.dumps(msg.get('data', {}), ensure_ascii=False)
                    yield f"event: {event_type}\ndata: {data}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            unsubscribe(session_id, q)

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


@patrol_bp.route('/directory/<int:directory_id>/devices', methods=['GET'])
def directory_patrol_devices(directory_id):
    include_children = request.args.get('include_children', '1') not in ('0', 'false', 'False')
    try:
        device_ids, dir_name = resolve_directory_device_ids(
            directory_id,
            include_children=include_children,
        )
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'directory_id': directory_id,
                'directory_name': dir_name,
                'device_ids': device_ids,
                'total': len(device_ids),
            },
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('查询目录巡检设备失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@patrol_bp.route('/session/<int:session_id>', methods=['PATCH'])
def patch_session(session_id):
    try:
        data = request.get_json() or {}
        session = get_patrol_session(session_id)
        if not session:
            return jsonify({'code': 404, 'msg': '巡检会话不存在'}), 404
        if 'focus_device_id' in data:
            session.focus_device_id = data.get('focus_device_id') or None
        if 'interval_sec' in data and data['interval_sec']:
            session.interval_sec = max(3, int(data['interval_sec']))
        if 'pool_size' in data and data['pool_size']:
            session.pool_size = max(1, min(int(data['pool_size']), 16))
        db.session.commit()
        broadcast_patrol_session(session_id, 'progress')
        return jsonify({'code': 0, 'msg': 'success', 'data': session.to_dict()})
    except Exception as e:
        logger.error('更新巡检会话失败: %s', e, exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500


@patrol_bp.route('/heartbeat', methods=['POST'])
def patrol_heartbeat():
    try:
        data = request.get_json() or {}
        if not receive_patrol_heartbeat(data):
            return jsonify({'code': 400, 'msg': '无效心跳'}), 400
        return jsonify({'code': 0, 'msg': '心跳接收成功'})
    except Exception as e:
        logger.error('接收巡检心跳失败: %s', e, exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500
