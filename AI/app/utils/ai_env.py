"""AI 根目录环境变量加载：优先 .env.{AI_ENV}，供 run.py 与 ai_service 子进程共用。"""
from __future__ import annotations

import ipaddress
import os
from urllib.parse import urlparse

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


def _database_host(url: str | None) -> str:
    if not url:
        return ''
    try:
        return (urlparse(normalize_database_url(url)).hostname or '').strip().lower()
    except (TypeError, ValueError):
        return ''


def _is_loopback_database_url(url: str | None) -> bool:
    host = _database_host(url)
    if not host:
        return False
    if host == 'localhost' or host.endswith('.localhost'):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _running_in_container() -> bool:
    return os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv')


def _restore_container_database_url(previous_url: str | None) -> None:
    """避免 spawn 子进程用源码挂载的 localhost 配置覆盖 Compose 注入值。"""
    loaded_url = os.environ.get('DATABASE_URL')
    if (
        _running_in_container()
        and previous_url
        and not _is_loopback_database_url(previous_url)
        and _is_loopback_database_url(loaded_url)
    ):
        os.environ['DATABASE_URL'] = previous_url


def ai_root_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_ai_env(*, override: bool = True) -> str | None:
    """加载 AI/.env.{AI_ENV} 或 AI/.env；返回实际加载的文件路径。"""
    previous_database_url = os.environ.get('DATABASE_URL')
    root = ai_root_dir()
    candidates: list[str] = []
    env_name = os.getenv('AI_ENV', '').strip()
    if env_name:
        candidates.append(os.path.join(root, f'.env.{env_name}'))
    candidates.append(os.path.join(root, '.env'))
    for path in candidates:
        if os.path.isfile(path):
            load_dotenv(path, override=override)
            _restore_container_database_url(previous_database_url)
            _normalize_database_url_env()
            return path
    load_dotenv(override=override)
    _restore_container_database_url(previous_database_url)
    _normalize_database_url_env()
    return None
