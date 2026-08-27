"""VIDEO 根目录环境变量加载：优先 .env.{VIDEO_ENV}，供 run.py 与各 algorithm 子进程共用。"""
from __future__ import annotations

import os

from dotenv import load_dotenv


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
    return loaded_path
