"""
POST 定制后处理：外置插件 CRUD + 插件目录与调试代理。
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from app.services import post_plugin_service as svc

logger = logging.getLogger(__name__)

post_plugin_bp = Blueprint('post_plugin', __name__)


@post_plugin_bp.route('/tasks/<int:task_id>/bindings', methods=['GET'])
def get_task_bindings(task_id):
    from models import AlgorithmTask
    from app.services.post_region_binding_service import binding_state
    task = AlgorithmTask.query.get(task_id)
    if task is None:
        return jsonify({'code': 404, 'msg': '任务不存在'}), 404
    return jsonify({'code': 0, 'data': binding_state(task), 'msg': 'success'})


@post_plugin_bp.route('/tasks/<int:task_id>/regions/<int:region_id>/binding', methods=['PUT'])
def put_region_binding(task_id, region_id):
    from app.services.post_region_binding_service import save_binding
    from app.services.device_detection_region_service import RegionRevisionConflict
    try:
        result = save_binding(task_id, region_id, request.get_json(silent=True) or {})
        from app.blueprints.device_detection_region import _refresh_task_runtime
        result['runtime_sync_status'] = _refresh_task_runtime(task_id)
        return jsonify({'code': 0, 'data': result, 'msg': 'success'})
    except RegionRevisionConflict as exc:
        return jsonify({'code': 409, 'msg': str(exc)}), 409
    except (ValueError, TypeError) as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception:
        logger.exception('保存区域插件绑定失败')
        return jsonify({'code': 500, 'msg': '保存绑定失败'}), 500


@post_plugin_bp.route('/tasks/<int:task_id>/results', methods=['GET'])
def task_business_results(task_id):
    from models import AlgorithmTask
    from app.services.post_plugin_results import list_business_results
    if AlgorithmTask.query.get(task_id) is None:
        return jsonify({'code': 404, 'msg': '任务不存在'}), 404
    try:
        return jsonify({'code': 0, 'data': list_business_results(task_id, request.args), 'msg': 'success'})
    except (ValueError, TypeError) as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception:
        logger.exception('查询后处理业务结果失败 task_id=%s', task_id)
        return jsonify({'code': 500, 'msg': '查询后处理业务结果失败'}), 500


@post_plugin_bp.route('/tasks/<int:task_id>/trainframe', methods=['POST'])
def post_task_trainframe(task_id):
    """训练场投放一帧：前端模拟人经真实 MQTT InferEvent 驱动 POST 插件引擎。"""
    from models import AlgorithmTask, Device
    from app.services.train_frame_simulator import MAX_ACTORS, TrainFrameError, publish_train_frame
    task = AlgorithmTask.query.get(task_id)
    if task is None:
        return jsonify({'code': 404, 'msg': '任务不存在'}), 404
    body = request.get_json(silent=True) or {}
    device_id = str(body.get('device_id') or '').strip()
    if not device_id:
        return jsonify({'code': 400, 'msg': '缺少 device_id'}), 400
    device = Device.query.get(device_id)
    if device is None:
        return jsonify({'code': 404, 'msg': '摄像头不存在'}), 404
    actors = body.get('actors')
    if not isinstance(actors, list) or len(actors) > MAX_ACTORS:
        return jsonify({'code': 400, 'msg': f'actors 必须是列表且不超过 {MAX_ACTORS} 个'}), 400
    try:
        published = publish_train_frame(task, device, actors)
    except TrainFrameError as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception:
        logger.exception('训练场投放失败 task_id=%s device=%s', task_id, device_id)
        return jsonify({'code': 503, 'msg': '投放失败：消息总线不可用或模板推送失败，请稍后重试'}), 503
    return jsonify({'code': 0, 'data': {'published': published}, 'msg': f'已发布 1 帧（{published} 个模拟目标）'})


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
