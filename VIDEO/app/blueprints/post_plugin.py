"""
POST 定制后处理：外置插件 CRUD + 插件目录与调试代理。
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from app.services import post_plugin_service as svc

logger = logging.getLogger(__name__)

post_plugin_bp = Blueprint('post_plugin', __name__)


@post_plugin_bp.route('/plugins/catalog', methods=['GET'])
def plugin_catalog():
    """内置/外置插件目录（须在 /plugins/<plugin_id> 之前注册）。"""
    try:
        data = svc.list_plugin_catalog()
        return jsonify({'code': 0, 'msg': 'success', 'data': data})
    except Exception as exc:
        logger.error('获取 POST 插件目录失败: %s', exc, exc_info=True)
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@post_plugin_bp.route('/plugins', methods=['GET'])
def list_plugins():
    try:
        enabled = request.args.get('enabled')
        en = None
        if enabled is not None and enabled != '':
            en = enabled in ('1', 'true', 'True', 'yes')
        return jsonify({'code': 0, 'msg': 'success', 'data': svc.list_plugins(en)})
    except Exception as exc:
        logger.error('list post plugins: %s', exc, exc_info=True)
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@post_plugin_bp.route('/plugins', methods=['POST'])
def register_plugin():
    try:
        data = request.get_json(force=True) or {}
        manifest = data.get('manifest') or data
        endpoint = data.get('endpoint')
        row = svc.register_plugin(manifest, endpoint=endpoint)
        return jsonify({'code': 0, 'msg': 'success', 'data': row.to_dict()})
    except ValueError as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        logger.error('register post plugin: %s', exc, exc_info=True)
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@post_plugin_bp.route('/plugins/<plugin_id>', methods=['GET'])
def get_plugin(plugin_id: str):
    try:
        row = svc.get_plugin(plugin_id)
        return jsonify({'code': 0, 'msg': 'success', 'data': row.to_dict()})
    except ValueError as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@post_plugin_bp.route('/plugins/<plugin_id>', methods=['PATCH', 'PUT'])
def update_plugin(plugin_id: str):
    try:
        data = request.get_json(force=True) or {}
        row = svc.update_plugin(
            plugin_id,
            enabled=data.get('enabled'),
            manifest=data.get('manifest'),
        )
        return jsonify({'code': 0, 'msg': 'success', 'data': row.to_dict()})
    except ValueError as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@post_plugin_bp.route('/plugins/<plugin_id>', methods=['DELETE'])
def delete_plugin(plugin_id: str):
    try:
        force = request.args.get('force', 'false').lower() in ('1', 'true', 'yes')
        svc.delete_plugin(plugin_id, force=force)
        return jsonify({'code': 0, 'msg': 'success'})
    except ValueError as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@post_plugin_bp.route('/plugins/<plugin_id>/start', methods=['POST'])
def start_plugin(plugin_id: str):
    try:
        data = request.get_json(silent=True) or {}
        row = svc.start_service(
            plugin_id,
            version=data.get('version'),
            deploy_mode=data.get('deploy_mode'),
            endpoint=data.get('endpoint'),
            replicas=data.get('replicas'),
            target_node_id=data.get('target_node_id'),
        )
        return jsonify({'code': 0, 'msg': 'success', 'data': row.to_dict()})
    except ValueError as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        logger.error('start post plugin: %s', exc, exc_info=True)
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@post_plugin_bp.route('/plugins/<plugin_id>/stop', methods=['POST'])
def stop_plugin(plugin_id: str):
    try:
        data = request.get_json(silent=True) or {}
        row = svc.stop_service(plugin_id, version=data.get('version'))
        return jsonify({'code': 0, 'msg': 'success', 'data': row.to_dict()})
    except ValueError as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@post_plugin_bp.route('/plugins/<plugin_id>/replicas', methods=['PUT', 'POST'])
def scale_plugin(plugin_id: str):
    try:
        data = request.get_json(force=True) or {}
        replicas = data.get('replicas')
        if replicas is None:
            return jsonify({'code': 400, 'msg': 'replicas required'}), 400
        row = svc.scale_service(plugin_id, int(replicas), version=data.get('version'))
        return jsonify({'code': 0, 'msg': 'success', 'data': row.to_dict()})
    except ValueError as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@post_plugin_bp.route('/plugins/<plugin_id>/tasks', methods=['GET'])
def plugin_tasks(plugin_id: str):
    try:
        return jsonify({'code': 0, 'msg': 'success', 'data': svc.list_tasks_using_plugin(plugin_id)})
    except Exception as exc:
        logger.error('list plugin tasks: %s', exc, exc_info=True)
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
            err = payload.get('error') if isinstance(payload, dict) else str(payload)
            return jsonify({'code': status, 'msg': err, 'data': payload}), status
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
            err = payload.get('error') if isinstance(payload, dict) else str(payload)
            return jsonify({'code': status, 'msg': err, 'data': payload}), status
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
