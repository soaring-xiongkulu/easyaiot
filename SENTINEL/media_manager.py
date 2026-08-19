"""
媒体栈管理：在节点上通过 docker compose 启动/停止 SRS / ZLM。
"""
import logging
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger('easyaiot-node-agent.media')

MEDIA_CLUSTER_ROOT = os.environ.get('MEDIA_CLUSTER_ROOT', '/opt/easyaiot/media-cluster')
COMPOSE_FILE = os.path.join(MEDIA_CLUSTER_ROOT, 'docker-compose.media-node.yml')

STACK_PROFILES = {
    'srs_live': {'MEDIA_NODE_TYPE': 'srs_live', 'service': 'srs'},
    'srs_ai': {'MEDIA_NODE_TYPE': 'srs_ai', 'service': 'srs'},
    'zlm': {'MEDIA_NODE_TYPE': 'zlm', 'service': 'zlm'},
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


class MediaStackManager:
    def __init__(self):
        self._running: Dict[str, str] = {}

    def _ensure_rendered_configs(self, env: Dict[str, str]) -> None:
        install_script = os.path.join(MEDIA_CLUSTER_ROOT, 'install_media_stack.sh')
        if not os.path.isfile(install_script):
            srs_conf = os.path.join(MEDIA_CLUSTER_ROOT, 'srs', 'docker.conf')
            zlm_conf = os.path.join(MEDIA_CLUSTER_ROOT, 'zlm', 'config.ini')
            raise FileNotFoundError(
                f'未找到 install_media_stack.sh，且缺少渲染配置 {srs_conf} / {zlm_conf}'
            )
        render_env = dict(env)
        render_env.setdefault('MEDIA_NODE_NAME', f"node-{render_env.get('NODE_ID', 'media')}")
        render_env.setdefault('MEDIA_NODE_HOST', os.environ.get('POD_IP', '127.0.0.1'))
        render_env['MEDIA_RENDER_CONFIGS_ONLY'] = '1'
        logger.info('渲染媒体栈配置（节点 tags 端口）: bash %s', install_script)
        proc = subprocess.run(
            ['bash', install_script],
            cwd=MEDIA_CLUSTER_ROOT,
            env=render_env,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr or proc.stdout or 'install_media_stack.sh 渲染配置失败')

    def deploy(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        stack_type = spec.get('stackType') or spec.get('mediaType')
        if stack_type not in STACK_PROFILES:
            raise ValueError(f'不支持的媒体栈类型: {stack_type}')

        node_id = str(spec.get('nodeId') or os.environ.get('NODE_ID', 'media-node'))
        env = os.environ.copy()
        env.update({k: str(v) for k, v in (spec.get('env') or {}).items() if v is not None})
        env['MEDIA_NODE_ID'] = f'{node_id}-{"srs" if STACK_PROFILES[stack_type]["service"] == "srs" else "zlm"}'
        env.setdefault('MEDIA_NODE_NAME', f'node-{node_id}')
        env['MEDIA_NODE_TYPE'] = STACK_PROFILES[stack_type]['MEDIA_NODE_TYPE']
        env.setdefault('MEDIA_SCHEDULER_HOST', os.environ.get('CONTROL_PLANE_HOST', '127.0.0.1'))
        env.setdefault('SRS_CANDIDATE_IP', os.environ.get('POD_IP', ''))
        env.setdefault('ZLM_HTTP_PORT', '6080')

        if not os.path.isfile(COMPOSE_FILE):
            raise FileNotFoundError(f'未找到 compose 文件: {COMPOSE_FILE}')

        self._ensure_rendered_configs(env)

        cmd = resolve_compose_cmd() + ['-f', COMPOSE_FILE, 'up', '-d']
        service = STACK_PROFILES[stack_type].get('service')
        if service:
            cmd.append(service)

        logger.info('启动媒体栈 %s: %s', stack_type, ' '.join(cmd))
        proc = subprocess.run(cmd, cwd=MEDIA_CLUSTER_ROOT, env=env, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr or proc.stdout or f'docker compose 失败: {proc.returncode}')

        self._running[stack_type] = node_id
        return {'stackType': stack_type, 'nodeId': node_id, 'status': 'running'}

    def stop(self, stack_type: str) -> bool:
        if stack_type not in STACK_PROFILES:
            return False
        if not os.path.isfile(COMPOSE_FILE):
            return False
        service = STACK_PROFILES[stack_type].get('service')
        cmd = resolve_compose_cmd() + ['-f', COMPOSE_FILE, 'stop']
        if service:
            cmd.append(service)
        subprocess.run(cmd, cwd=MEDIA_CLUSTER_ROOT, capture_output=True, text=True)
        self._running.pop(stack_type, None)
        return True
