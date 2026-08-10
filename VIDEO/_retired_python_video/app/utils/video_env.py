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
    for path in candidates:
        if os.path.isfile(path):
            load_dotenv(path, override=override)
            return path
    load_dotenv(override=override)
    return None
