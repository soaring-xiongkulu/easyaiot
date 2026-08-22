"""
POST 定制后处理：插件目录与调试代理。
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

post_plugin_bp = Blueprint('post_plugin', __name__)


@post_plugin_bp.route('/plugins/catalog', methods=['GET'])
def plugin_catalog():
    try:
        from app.services.post_plugin_service import list_plugin_catalog
        data = list_plugin_catalog()
        return jsonify({'code': 0, 'msg': 'success', 'data': data})
    except Exception as exc:
        logger.error('获取 POST 插件目录失败: %s', exc, exc_info=True)
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@post_plugin_bp.route('/debug/pipeline', methods=['POST'])
def debug_pipeline_route():
    try:
        from app.services.post_template_client import debug_pipeline
        from app.services.post_plugin_service import inject_pipeline_endpoints

        body = request.get_json(silent=True) or {}
        if body.get('pipeline_override'):
            body['pipeline_override'] = inject_pipeline_endpoints(body['pipeline_override'])
        status, payload = debug_pipeline(body)
        if status >= 400:
            return jsonify({'code': status, 'msg': payload.get('error') if isinstance(payload, dict) else str(payload), 'data': payload}), status
        return jsonify({'code': 0, 'msg': 'success', 'data': payload})
    except Exception as exc:
        logger.error('POST pipeline 调试失败: %s', exc, exc_info=True)
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@post_plugin_bp.route('/debug/plugin', methods=['POST'])
def debug_plugin_route():
    try:
        from app.services.post_template_client import debug_plugin

        body = request.get_json(silent=True) or {}
        status, payload = debug_plugin(body)
        if status >= 400:
            return jsonify({'code': status, 'msg': payload.get('error') if isinstance(payload, dict) else str(payload), 'data': payload}), status
        return jsonify({'code': 0, 'msg': 'success', 'data': payload})
    except Exception as exc:
        logger.error('POST plugin 调试失败: %s', exc, exc_info=True)
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@post_plugin_bp.route('/debug/sample-event/<int:task_id>', methods=['GET'])
def sample_event(task_id: int):
    try:
        from models import AlgorithmTask
        from app.services.post_template_client import build_sample_event, _task_regions

        task = AlgorithmTask.query.get_or_404(task_id)
        device_id = (request.args.get('device_id') or '').strip()
        fw = int(request.args.get('frame_width') or 1920)
        fh = int(request.args.get('frame_height') or 1080)
        event = build_sample_event(task, device_id=device_id, frame_width=fw, frame_height=fh)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'event': event,
                'regions': _task_regions(task),
            },
        })
    except Exception as exc:
        logger.error('生成样例事件失败 task=%s: %s', task_id, exc, exc_info=True)
        return jsonify({'code': 500, 'msg': str(exc)}), 500
