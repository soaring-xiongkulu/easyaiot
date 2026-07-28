"""
工作负载管理：在节点上启动/停止 run_deploy 等子进程。
"""
import logging
import os
import socket
import subprocess
import sys
import threading
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import psutil

_repo_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
_lib_root = os.path.join(_repo_root, '.scripts', 'lib')
for _p in (_lib_root,):
    if _p not in sys.path:
        sys.path.insert(0, _p)

logger = logging.getLogger('easyaiot-node-agent.workload')


@dataclass
class WorkloadRecord:
    workload_type: str
    workload_id: str
    process: Optional[subprocess.Popen]
    pid: int
    log_dir: Optional[str] = None
    command: List[str] = field(default_factory=list)
    runtime: str = 'process'  # process | docker
    container_name: Optional[str] = None


class WorkloadManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._workloads: Dict[str, WorkloadRecord] = {}

    def _key(self, workload_type: str, workload_id: str) -> str:
        return f'{workload_type}:{workload_id}'

    def list_workloads(self) -> List[Dict[str, Any]]:
        with self._lock:
            result = []
            for rec in self._workloads.values():
                if rec.runtime == 'docker' and rec.container_name:
                    running = _docker_running(rec.container_name)
                else:
                    running = rec.process is not None and rec.process.poll() is None
                result.append({
                    'workloadType': rec.workload_type,
                    'workloadId': rec.workload_id,
                    'pid': rec.pid,
                    'running': running,
                    'runtime': rec.runtime,
                    'containerName': rec.container_name,
                })
            return result

    def active_count(self) -> int:
        with self._lock:
            n = 0
            for rec in self._workloads.values():
                if rec.runtime == 'docker' and rec.container_name:
                    if _docker_running(rec.container_name):
                        n += 1
                elif rec.process is not None and rec.process.poll() is None:
                    n += 1
            return n

    def deploy(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        workload_type = spec['workloadType']
        workload_id = spec['workloadId']
        command = spec.get('command') or []
        work_dir = spec.get('workDir') or os.getcwd()
        log_dir = spec.get('logDir')
        gpu_ids = spec.get('gpuIds')
        env_extra = spec.get('env') or {}
        runtime = (spec.get('runtime') or env_extra.get('RUNTIME') or 'process').lower()

        key = self._key(workload_type, workload_id)
        with self._lock:
            existing = self._workloads.get(key)
            if existing:
                if existing.runtime == 'docker' and existing.container_name and _docker_running(existing.container_name):
                    raise ValueError(f'工作负载已运行: {key}')
                if existing.process is not None and existing.process.poll() is None:
                    raise ValueError(f'工作负载已运行: {key}')

        env = os.environ.copy()
        env.update({k: str(v) for k, v in env_extra.items() if v is not None})
        env['PYTHONUNBUFFERED'] = '1'
        if gpu_ids:
            env['CUDA_VISIBLE_DEVICES'] = str(gpu_ids)
            env['GPU_IDS'] = str(gpu_ids)
        if log_dir:
            env['LOG_PATH'] = log_dir
            os.makedirs(log_dir, exist_ok=True)

        if runtime == 'docker':
            return self._deploy_docker(spec, key, env)

        if not command:
            raise ValueError('command 不能为空')

        model_path = env.get('MODEL_PATH', '')
        if model_path:
            local_path = _ensure_model_local(model_path, env.get('MODEL_ID', '0'))
            if local_path:
                env['MODEL_PATH'] = local_path

        os.makedirs(work_dir, exist_ok=True)
        log_file = None
        if log_dir:
            log_file = open(os.path.join(log_dir, 'workload.log'), 'a', encoding='utf-8')

        proc = subprocess.Popen(
            command,
            cwd=work_dir,
            env=env,
            stdout=log_file or subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        record = WorkloadRecord(
            workload_type=workload_type,
            workload_id=workload_id,
            process=proc,
            pid=proc.pid,
            log_dir=log_dir,
            command=command,
            runtime='process',
        )
        with self._lock:
            self._workloads[key] = record
        logger.info('工作负载已启动 %s pid=%s', key, proc.pid)
        return {'pid': proc.pid, 'workloadType': workload_type, 'workloadId': workload_id, 'runtime': 'process'}

    def _deploy_docker(self, spec: Dict[str, Any], key: str, env: Dict[str, str]) -> Dict[str, Any]:
        workload_type = spec['workloadType']
        workload_id = spec['workloadId']
        image = spec.get('image') or env.get('IMAGE') or env.get('TRANSFORM_IMAGE')
        if not image:
            raise ValueError('docker 部署需要 image / env.IMAGE')

        # 容器名必须唯一：同节点可跑多副本
        safe_id = ''.join(c if c.isalnum() or c in '-_' else '-' for c in str(workload_id))[:40]
        container_name = (spec.get('containerName') or env.get('CONTAINER_NAME')
                          or f'{workload_type}-{safe_id}')[:63].strip('-')

        host_port = env.get('PORT') or env.get('SERVER_PORT') or '48096'
        container_port = env.get('CONTAINER_PORT') or '48096'
        network = env.get('DOCKER_NETWORK') or ''
        extra_args = []
        if network:
            extra_args.extend(['--network', network])

        # 先清理同名残留
        subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True, text=True)

        cmd = [
            'docker', 'run', '-d',
            '--name', container_name,
            '--restart', 'unless-stopped',
            '-p', f'{host_port}:{container_port}',
            '-e', f'SERVER_PORT={container_port}',
            '-e', f'PORT={container_port}',
        ]
        # 透传常见环境变量
        passthrough = [
            'TRANSFORM_INSTANCE_ID', 'TRANSFORM_NODE_ID', 'TRANSFORM_ROLE',
            'KAFKA_BOOTSTRAP', 'POSTGRES_URL', 'POSTGRES_USERNAME', 'POSTGRES_PASSWORD',
            'SPRING_PROFILES_ACTIVE', 'TRANSFORM_BACKUP_DIR', 'JAVA_OPTS', 'NACOS_ADDR',
        ]
        # 默认 instance id = workloadId，保证多副本身份不同
        if not env.get('TRANSFORM_INSTANCE_ID'):
            env['TRANSFORM_INSTANCE_ID'] = str(workload_id)
        for k in passthrough:
            if env.get(k):
                cmd.extend(['-e', f'{k}={env[k]}'])
        cmd.extend(extra_args)
        cmd.append(image)

        logger.info('docker run: %s', ' '.join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f'docker run 失败: {result.stderr or result.stdout}')
        container_id = (result.stdout or '').strip()
        record = WorkloadRecord(
            workload_type=workload_type,
            workload_id=workload_id,
            process=None,
            pid=0,
            command=cmd,
            runtime='docker',
            container_name=container_name,
        )
        with self._lock:
            self._workloads[key] = record
        logger.info('Docker 工作负载已启动 %s container=%s id=%s port=%s',
                    key, container_name, container_id[:12], host_port)
        return {
            'workloadType': workload_type,
            'workloadId': workload_id,
            'runtime': 'docker',
            'containerName': container_name,
            'containerId': container_id,
            'port': int(host_port),
        }

    def stop(self, workload_type: str, workload_id: str) -> bool:
        key = self._key(workload_type, workload_id)
        with self._lock:
            record = self._workloads.get(key)
        if not record:
            return False
        if record.runtime == 'docker' and record.container_name:
            subprocess.run(['docker', 'rm', '-f', record.container_name], capture_output=True, text=True)
        elif record.process is not None:
            _terminate_process_tree(record.process.pid)
        with self._lock:
            self._workloads.pop(key, None)
        logger.info('工作负载已停止 %s', key)
        return True


def _docker_running(container_name: str) -> bool:
    try:
        r = subprocess.run(
            ['docker', 'inspect', '-f', '{{.State.Running}}', container_name],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0 and (r.stdout or '').strip().lower() == 'true'
    except Exception:
        return False


def _terminate_process_tree(pid: int):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                child.terminate()
            except psutil.Error:
                pass
        parent.terminate()
        gone, alive = psutil.wait_procs(children + [parent], timeout=5)
        for p in alive:
            try:
                p.kill()
            except psutil.Error:
                pass
    except psutil.NoSuchProcess:
        pass


def _ensure_model_local(model_path: str, model_id: str) -> Optional[str]:
    """若 MODEL_PATH 为 MinIO URL 则下载到本地；集群模式优先读 CephFS 共享缓存。"""
    try:
        mid = int(model_id)
        if mid > 0:
            from model_resolver import try_resolve_cluster_model_path
            cluster_path = try_resolve_cluster_model_path(mid)
            if cluster_path:
                logger.info('使用集群共享模型 model_id=%s path=%s', model_id, cluster_path)
                return cluster_path
    except (ImportError, ValueError, TypeError):
        pass

    if not model_path.startswith('/api/v1/buckets/') and not model_path.startswith('http'):
        if os.path.isabs(model_path) and os.path.exists(model_path):
            return model_path
        ai_root = os.environ.get('AI_ROOT', '/opt/easyaiot/AI')
        local = os.path.join(ai_root, model_path) if not os.path.isabs(model_path) else model_path
        return local if os.path.exists(local) else model_path

    try:
        parsed = urllib.parse.urlparse(model_path)
        path_parts = parsed.path.split('/')
        if len(path_parts) < 5 or path_parts[3] != 'buckets':
            return model_path
        bucket_name = path_parts[4]
        query_params = urllib.parse.parse_qs(parsed.query)
        object_key = query_params.get('prefix', [None])[0]
        if not object_key:
            return model_path

        ai_root = os.environ.get('AI_ROOT', '/opt/easyaiot/AI')
        models_base = os.environ.get('AI_MODELS_DIR', '').strip()
        if not models_base:
            try:
                from cluster_storage import get_ai_models_dir
                models_base = get_ai_models_dir()
            except ImportError:
                models_base = os.path.join(ai_root, 'data', 'models')
        storage_dir = os.path.join(models_base, str(model_id))
        os.makedirs(storage_dir, exist_ok=True)
        filename = os.path.basename(object_key) or f'model_{model_id}'
        local_path = os.path.join(storage_dir, filename)
        if os.path.exists(local_path):
            return local_path

        endpoint = os.environ.get('MINIO_ENDPOINT', 'http://localhost:9000').rstrip('/')
        access_key = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
        secret_key = os.environ.get('MINIO_SECRET_KEY', '')
        from minio import Minio
        secure = endpoint.startswith('https')
        host = endpoint.replace('https://', '').replace('http://', '')
        client = Minio(host, access_key=access_key, secret_key=secret_key, secure=secure)
        client.fget_object(bucket_name, object_key, local_path)
        logger.info('模型已下载到 %s', local_path)
        return local_path
    except Exception as e:
        logger.warning('模型下载失败，使用原始路径: %s', e)
        return model_path


def find_available_port(start_port: int = 8000, max_attempts: int = 100) -> Optional[int]:
    for i in range(max_attempts):
        port = start_port + i
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', port))
            return port
        except OSError:
            continue
        finally:
            sock.close()
    return None
