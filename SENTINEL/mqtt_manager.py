"""
MQTT 网关管理：在节点上通过 docker compose 启动/停止 EMQX。
"""
import logging
import os
import shutil
import subprocess
from typing import Any, Dict, List

logger = logging.getLogger('easyaiot-node-agent.mqtt')

MQTT_CLUSTER_ROOT = os.environ.get('MQTT_CLUSTER_ROOT', '/opt/easyaiot/mqtt-cluster')
COMPOSE_FILE = os.path.join(MQTT_CLUSTER_ROOT, 'docker-compose.mqtt-node.yml')

STACK_PROFILES = {
    'emqx': {'service': 'emqx'},
    'mqtt_gateway': {'service': 'emqx'},
}


def resolve_compose_cmd() -> List[str]:
    proc = subprocess.run(
        ['docker', 'compose', 'version'],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return ['docker', 'compose']
    if shutil.which('docker-compose'):
        return ['docker-compose']
    raise RuntimeError('未找到 docker compose / docker-compose，请先安装 Docker Compose')


class MqttStackManager:
    def __init__(self):
        self._running: Dict[str, str] = {}

    def deploy(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        stack_type = spec.get('stackType') or 'emqx'
        if stack_type not in STACK_PROFILES:
            raise ValueError(f'不支持的 MQTT 栈类型: {stack_type}')

        node_id = str(spec.get('nodeId') or os.environ.get('NODE_ID', 'mqtt-node'))
        env = os.environ.copy()
        env.update({k: str(v) for k, v in (spec.get('env') or {}).items() if v is not None})
        env.setdefault('MQTT_CLUSTER_ROOT', MQTT_CLUSTER_ROOT)
        env.setdefault('MQTT_NODE_NAME', f'node-{node_id}')
        env['MQTT_NODE_ID'] = f"{env.get('MQTT_NODE_NAME')}-emqx"

        install_script = os.path.join(MQTT_CLUSTER_ROOT, 'install_mqtt_stack.sh')
        if os.path.isfile(install_script):
            logger.info('执行 MQTT 栈部署: bash %s', install_script)
            proc = subprocess.run(
                ['bash', install_script],
                cwd=MQTT_CLUSTER_ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr or proc.stdout or 'install_mqtt_stack.sh 失败')
        else:
            if not os.path.isfile(COMPOSE_FILE):
                raise FileNotFoundError(f'未找到 compose 文件: {COMPOSE_FILE}')
            cmd = resolve_compose_cmd() + ['-f', COMPOSE_FILE, 'up', '-d', 'emqx']
            logger.info('启动 EMQX: %s', ' '.join(cmd))
            proc = subprocess.run(cmd, cwd=MQTT_CLUSTER_ROOT, env=env, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr or proc.stdout or f'docker compose 失败: {proc.returncode}')

        self._running[stack_type] = node_id
        return {'stackType': stack_type, 'nodeId': node_id, 'status': 'running'}

    def stop(self, stack_type: str) -> bool:
        if stack_type not in STACK_PROFILES:
            return False
        if not os.path.isfile(COMPOSE_FILE):
            return False
        cmd = resolve_compose_cmd() + ['-f', COMPOSE_FILE, 'stop', 'emqx']
        proc = subprocess.run(cmd, cwd=MQTT_CLUSTER_ROOT, capture_output=True, text=True)
        self._running.pop(stack_type, None)
        return proc.returncode == 0
