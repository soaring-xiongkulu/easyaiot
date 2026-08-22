"""POST 外置插件管理 API（登记 / 启停 / 扩缩；无市场）。"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from app.services import post_plugin_service as svc

post_plugin_bp = Blueprint('post_plugin', __name__)
logger = logging.getLogger(__name__)


@post_plugin_bp.route('/plugins', methods=['GET'])
def list_plugins():
    try:
        enabled = request.args.get('enabled')
        en = None
        if enabled is not None and enabled != '':
            en = enabled in ('1', 'true', 'True', 'yes')
        return jsonify({'code': 0, 'msg': 'success', 'data': svc.list_plugins(en)})
    except Exception as e:
        logger.error('list post plugins: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': str(e)}), 500


@post_plugin_bp.route('/plugins', methods=['POST'])
def register_plugin():
    try:
        data = request.get_json(force=True) or {}
        manifest = data.get('manifest') or data
        endpoint = data.get('endpoint')
        row = svc.register_plugin(manifest, endpoint=endpoint)
        return jsonify({'code': 0, 'msg': 'success', 'data': row.to_dict()})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('register post plugin: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': str(e)}), 500


@post_plugin_bp.route('/plugins/<plugin_id>', methods=['GET'])
def get_plugin(plugin_id: str):
    try:
        row = svc.get_plugin(plugin_id)
        return jsonify({'code': 0, 'msg': 'success', 'data': row.to_dict()})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


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
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


@post_plugin_bp.route('/plugins/<plugin_id>', methods=['DELETE'])
def delete_plugin(plugin_id: str):
    try:
        force = request.args.get('force', 'false').lower() in ('1', 'true', 'yes')
        svc.delete_plugin(plugin_id, force=force)
        return jsonify({'code': 0, 'msg': 'success'})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


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
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('start post plugin: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': str(e)}), 500


@post_plugin_bp.route('/plugins/<plugin_id>/stop', methods=['POST'])
def stop_plugin(plugin_id: str):
    try:
        data = request.get_json(silent=True) or {}
        row = svc.stop_service(plugin_id, version=data.get('version'))
        return jsonify({'code': 0, 'msg': 'success', 'data': row.to_dict()})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


@post_plugin_bp.route('/plugins/<plugin_id>/replicas', methods=['PUT', 'POST'])
def scale_plugin(plugin_id: str):
    try:
        data = request.get_json(force=True) or {}
        replicas = data.get('replicas')
        if replicas is None:
            return jsonify({'code': 400, 'msg': 'replicas required'}), 400
        row = svc.scale_service(plugin_id, int(replicas), version=data.get('version'))
        return jsonify({'code': 0, 'msg': 'success', 'data': row.to_dict()})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


@post_plugin_bp.route('/plugins/<plugin_id>/tasks', methods=['GET'])
def plugin_tasks(plugin_id: str):
    """列出 post_pipeline 引用了该插件的算法任务（粗匹配）。"""
    try:
        return jsonify({'code': 0, 'msg': 'success', 'data': svc.list_tasks_using_plugin(plugin_id)})
    except Exception as e:
        logger.error('list plugin tasks: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': str(e)}), 500


@post_plugin_bp.route('/debug/pipeline', methods=['POST'])
def debug_pipeline_proxy():
    """WEB → VIDEO → POST /debug/pipeline，避免浏览器直连 POST 地址。"""
    try:
        from app.services import post_template_client as post_client
        body = request.get_json(force=True) or {}
        result = post_client.debug_pipeline(body)
        if not result.get('ok'):
            return jsonify({
                'code': int(result.get('status') or 502),
                'msg': result.get('error') or 'POST debug 失败',
                'data': result.get('data'),
            }), int(result.get('status') or 502)
        return jsonify({'code': 0, 'msg': 'success', 'data': result.get('data')})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('debug pipeline proxy: %s', e, exc_info=True)
        return jsonify({'code': 502, 'msg': str(e)}), 502
