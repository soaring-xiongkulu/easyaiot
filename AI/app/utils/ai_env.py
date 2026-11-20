"""AI 根目录环境变量加载：优先 .env.{AI_ENV}，供 run.py 与 ai_service 子进程共用。"""
from __future__ import annotations

import os

from dotenv import load_dotenv


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


def ai_root_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_ai_env(*, override: bool = True) -> str | None:
    """加载 AI/.env.{AI_ENV} 或 AI/.env；返回实际加载的文件路径。"""
    root = ai_root_dir()
    candidates: list[str] = []
    env_name = os.getenv('AI_ENV', '').strip()
    if env_name:
        candidates.append(os.path.join(root, f'.env.{env_name}'))
    candidates.append(os.path.join(root, '.env'))
    for path in candidates:
        if os.path.isfile(path):
            load_dotenv(path, override=override)
            _normalize_database_url_env()
            return path
    load_dotenv(override=override)
    _normalize_database_url_env()
    return None
