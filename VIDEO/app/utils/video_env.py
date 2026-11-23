"""VIDEO 根目录环境变量加载：优先 .env.{VIDEO_ENV}，供 run.py 与各 algorithm 子进程共用。"""
from __future__ import annotations

import os

from dotenv import load_dotenv


# 算法任务由 VIDEO 守护进程启动时注入的关键变量。它们描述容器网络、任务身份
# 与控制面位置，不能被宿主机开发用 .env（常指向 localhost）覆盖。
_LAUNCHER_ENV_KEYS = (
    'DATABASE_URL',
    'GATEWAY_URL',
    'JAVA_BACKEND_URL',
    'AUTH_CHECK_URL',
    'KAFKA_BOOTSTRAP_SERVERS',
    'MQTT_BROKER_URLS',
    'REDIS_HOST',
    'REDIS_PORT',
    'REDIS_PASSWORD',
    'SRS_HOST',
    'SRS_RTMP_PORT',
    'SRS_HTTP_PORT',
    'SRS_API_PORT',
    'MINIO_ENDPOINT',
    'MINIO_ACCESS_KEY',
    'MINIO_SECRET_KEY',
    'MINIO_SECURE',
    'NACOS_SERVER',
    'NACOS_NAMESPACE',
    'NACOS_USERNAME',
    'NACOS_PASSWORD',
    'POD_IP',
    'HOST_IP',
    'TASK_ID',
    'DEVICE_IDS',
    'WORKLOAD_ID',
    'LOG_PATH',
    'VIDEO_CONTROL_URL',
    'VIDEO_HEARTBEAT_URL',
    'VIDEO_SERVICE_HOST',
    'VIDEO_SERVICE_URL',
    'VIDEO_SERVICE_PORT',
    'CAMERA_SOURCE_REMOTE_WORKER',
    'CAMERA_SOURCE_MODE',
    'CAMERA_SOURCE_MANAGER_URL',
    'CAMERA_SOURCE_MANAGER_PORT',
    'CAMERA_SOURCE_MANAGER_TOKEN',
    'PATROL_SESSION_ID',
    'POST_PROCESS_TASK_ID',
    'POST_PROCESS_REPLICA',
    'POST_PROCESS_WORKER_HTTP_HOST',
    'POST_PROCESS_WORKER_HTTP_PORT',
)


def normalize_database_url(url: str) -> str:
    """让未指定驱动的 PostgreSQL URL 显式使用镜像中已有的 psycopg2。"""
    if url.startswith('postgres://'):
        return f"postgresql+psycopg2://{url[len('postgres://') :]}"
    if url.startswith('postgresql://'):
        return f"postgresql+psycopg2://{url[len('postgresql://') :]}"
    return url


def _normalize_database_url_env() -> None:
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        os.environ['DATABASE_URL'] = normalize_database_url(database_url)


def video_root_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_video_env(*, override: bool = True) -> str | None:
    """加载 VIDEO/.env.{VIDEO_ENV} 或 VIDEO/.env；返回实际加载的文件路径。"""
    root = video_root_dir()
    candidates: list[str] = []
    env_name = os.getenv('VIDEO_ENV', '').strip()
    if env_name:
        candidates.append(os.path.join(root, f'.env.{env_name}'))
    candidates.append(os.path.join(root, '.env'))
    loaded_path = None
    for path in candidates:
        if os.path.isfile(path):
            load_dotenv(path, override=override)
            loaded_path = path
            break
    if loaded_path is None:
        load_dotenv(override=override)

    # 节点存储模式由 iot-node 部署流程生成，必须覆盖通用 .env，避免控制面与运行时漂移。
    runtime_candidates = []
    configured_runtime_env = os.getenv('MEDIA_RECORDING_STORAGE_ENV', '').strip()
    if configured_runtime_env:
        runtime_candidates.append(configured_runtime_env)
    runtime_candidates.extend([
        os.path.join(root, '.recording-storage.env'),
        '/opt/easyaiot/media-cluster/recording-storage.env',
    ])
    for runtime_env in runtime_candidates:
        if os.path.isfile(runtime_env):
            load_dotenv(runtime_env, override=True)
            break
    _normalize_database_url_env()
    return loaded_path


def load_video_env_preserving_launcher(*, extra_keys: tuple[str, ...] = ()) -> str | None:
    """加载 VIDEO 配置，同时保留 launcher/compose 已注入的关键环境变量。

    基础 .env 使用 ``override=False``；保存并恢复仍用于防御
    ``.recording-storage.env`` 等运行时配置的强制覆盖。
    """
    keys = dict.fromkeys((*_LAUNCHER_ENV_KEYS, *extra_keys))
    preserved = {key: os.environ[key] for key in keys if key in os.environ}
    loaded_path = load_video_env(override=False)
    os.environ.update(preserved)
    # 恢复后的 launcher DATABASE_URL 也需补齐 psycopg2 driver。
    _normalize_database_url_env()
    return loaded_path
