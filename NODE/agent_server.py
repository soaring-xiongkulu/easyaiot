"""
Agent HTTP 服务：接收控制面下发的部署/停止指令。
"""
import logging
import os
from flask import Flask, jsonify, request

from workload_manager import WorkloadManager, find_available_port
from media_manager import MediaStackManager
from mqtt_manager import MqttStackManager

logger = logging.getLogger('easyaiot-node-agent.server')

AGENT_TOKEN = os.environ.get('AGENT_TOKEN', '')
AGENT_LISTEN_HOST = os.environ.get('AGENT_LISTEN_HOST', '0.0.0.0')
AGENT_LISTEN_PORT = int(os.environ.get('AGENT_LISTEN_PORT', '9100'))

app = Flask(__name__)
manager = WorkloadManager()
media_manager = MediaStackManager()
mqtt_manager = MqttStackManager()


def _ok(data=None):
    return jsonify({'code': 0, 'msg': 'success', 'data': data or {}})


def _err(msg: str, code: int = 1):
    return jsonify({'code': code, 'msg': msg, 'data': None}), 400


def _check_token():
    token = request.headers.get('X-Agent-Token', '')
    if not AGENT_TOKEN or token != AGENT_TOKEN:
        return False
    return True


@app.before_request
def auth_middleware():
    if request.path in ('/health',):
        return None
    if not _check_token():
        return _err('Agent 认证失败', 401)


@app.get('/health')
def health():
    return _ok({'status': 'ok'})


@app.post('/workload/deploy')
def deploy_workload():
    try:
        spec = request.get_json(force=True) or {}
        if not spec.get('workloadType') or not spec.get('workloadId'):
            return _err('workloadType 和 workloadId 必填')
        env = spec.get('env') or {}
        runtime = (spec.get('runtime') or env.get('RUNTIME') or 'process').lower()
        # TRANSFORM 镜像默认从 48096 起找空闲口，同节点可多容器
        if not env.get('PORT'):
            start = int(env.get('START_PORT') or (48096 if runtime == 'docker' or spec.get('workloadType') == 'transform_runtime' else 8000))
            port = find_available_port(start)
            if port:
                env['PORT'] = str(port)
                spec['env'] = env
        # docker 模式允许 command 为空（由 Agent 组装 docker run）
        if runtime != 'docker' and not (spec.get('command') or []):
            return _err('command 不能为空')
        data = manager.deploy(spec)
        return _ok(data)
    except Exception as e:
        logger.exception('部署失败')
        return _err(str(e))


@app.post('/workload/stop')
def stop_workload():
    try:
        body = request.get_json(force=True) or {}
        workload_type = body.get('workloadType')
        workload_id = body.get('workloadId')
        if not workload_type or not workload_id:
            return _err('workloadType 和 workloadId 必填')
        manager.stop(workload_type, workload_id)
        return _ok({'stopped': True})
    except Exception as e:
        logger.exception('停止失败')
        return _err(str(e))


@app.get('/workload/list')
def list_workloads():
    return _ok({'workloads': manager.list_workloads(), 'activeTasks': manager.active_count()})


@app.post('/media/deploy')
def deploy_media_stack():
    try:
        spec = request.get_json(force=True) or {}
        if not spec.get('stackType') and not spec.get('mediaType'):
            return _err('stackType 必填')
        data = media_manager.deploy(spec)
        return _ok(data)
    except Exception as e:
        logger.exception('媒体栈部署失败')
        return _err(str(e))


@app.post('/media/stop')
def stop_media_stack():
    try:
        body = request.get_json(force=True) or {}
        stack_type = body.get('stackType') or body.get('mediaType')
        if not stack_type:
            return _err('stackType 必填')
        media_manager.stop(stack_type)
        return _ok({'stopped': True})
    except Exception as e:
        logger.exception('媒体栈停止失败')
        return _err(str(e))


@app.post('/mqtt/deploy')
def deploy_mqtt_stack():
    try:
        spec = request.get_json(force=True) or {}
        data = mqtt_manager.deploy(spec)
        return _ok(data)
    except Exception as e:
        logger.exception('MQTT 网关部署失败')
        return _err(str(e))


@app.post('/mqtt/stop')
def stop_mqtt_stack():
    try:
        body = request.get_json(force=True) or {}
        stack_type = body.get('stackType') or 'emqx'
        mqtt_manager.stop(stack_type)
        return _ok({'stopped': True})
    except Exception as e:
        logger.exception('MQTT 网关停止失败')
        return _err(str(e))


def create_app():
    return app


def run_server():
    logger.info('Agent HTTP 服务启动 %s:%s', AGENT_LISTEN_HOST, AGENT_LISTEN_PORT)
    app.run(host=AGENT_LISTEN_HOST, port=AGENT_LISTEN_PORT, threaded=True, use_reloader=False)
