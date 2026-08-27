"""
mini 形态本地对象存储：目录结构与 MinIO bucket/key 一致，便于复用 /api/v1/buckets/... URL。

历史对象优先从安装包自带的 flat 种子目录（.scripts/minio）同步；也可在 MinIO 服务
短暂可用时通过 S3 API 拉取（migrate_minio_s3_to_local_storage）。
"""
from __future__ import annotations

import logging
import mimetypes
import os
import shutil
from typing import Iterable, List, Optional, Tuple
from urllib.parse import quote

from app.utils.service_urls import minio_storage_enabled

logger = logging.getLogger(__name__)


def get_local_storage_root() -> str:
    explicit = (os.getenv('LOCAL_STORAGE_ROOT') or os.getenv('AI_LOCAL_STORAGE_ROOT') or '').strip()
    if explicit:
        return os.path.normpath(os.path.expanduser(explicit))
    for key in ('MEDIA_HOST_DATA_ROOT', 'SRS_HOST_DATA_ROOT'):
        root = (os.getenv(key) or '').strip()
        if root:
            return os.path.join(os.path.normpath(root), 'local-storage')
    return '/data/local-storage'


def _ai_root() -> str:
    ai_root = (os.getenv('AI_ROOT') or '').strip()
    if ai_root:
        return os.path.normpath(ai_root)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def get_minio_seed_data_root() -> Optional[str]:
    """安装包 flat 种子数据根目录（.scripts/minio，结构与 bucket/key 一致）。"""
    explicit = (os.getenv('MINIO_SEED_DATA_ROOT') or os.getenv('MINIO_FS_DATA_ROOT') or '').strip()
    if explicit and os.path.isdir(explicit):
        return os.path.normpath(explicit)

    repo_root = os.path.dirname(_ai_root())
    candidates = [
        '/minio-seed-data',
        os.path.join(repo_root, '.scripts', 'minio'),
        '/opt/easyaiot/.scripts/minio',
    ]
    for candidate in candidates:
        if candidate and os.path.isdir(candidate):
            return os.path.normpath(candidate)
    return None


def _safe_object_parts(bucket_name: str, object_key: str) -> tuple[str, list[str]]:
    safe_bucket = (bucket_name or 'default').strip().strip('/').replace('\\', '/')
    safe_key = (object_key or '').strip().replace('\\', '/')
    if (
        not safe_bucket
        or '/' in safe_bucket
        or safe_bucket in ('.', '..')
        or not safe_key
        or safe_key.startswith('/')
    ):
        raise ValueError('非法本地对象路径')
    normalized_key = os.path.normpath(safe_key).replace('\\', '/')
    if normalized_key in ('.', '..') or normalized_key.startswith('../'):
        raise ValueError('本地对象路径越界')
    return safe_bucket, normalized_key.split('/')


def local_object_path(bucket_name: str, object_key: str) -> str:
    safe_bucket, safe_key_parts = _safe_object_parts(bucket_name, object_key)
    root = os.path.realpath(get_local_storage_root())
    path = os.path.realpath(os.path.join(root, safe_bucket, *safe_key_parts))
    try:
        if os.path.commonpath((root, path)) != root:
            raise ValueError('本地对象路径越界')
    except ValueError as exc:
        raise ValueError('本地对象路径越界') from exc
    return path


def seed_object_path(bucket_name: str, object_key: str) -> Optional[str]:
    seed_root = get_minio_seed_data_root()
    if not seed_root:
        return None
    safe_bucket, safe_key_parts = _safe_object_parts(bucket_name, object_key)
    real_seed_root = os.path.realpath(seed_root)
    path = os.path.realpath(os.path.join(real_seed_root, safe_bucket, *safe_key_parts))
    if os.path.commonpath((real_seed_root, path)) != real_seed_root:
        raise ValueError('种子对象路径越界')
    return path if os.path.isfile(path) else None


def build_minio_download_url(bucket_name: str, object_key: str) -> str:
    return f'/api/v1/buckets/{bucket_name}/objects/download?prefix={quote(object_key, safe="")}'


def materialize_seed_object(bucket_name: str, object_key: str, dest_path: str) -> bool:
    src = seed_object_path(bucket_name, object_key)
    if not src:
        return False
    try:
        dest_dir = os.path.dirname(dest_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(src, dest_path)
        return os.path.isfile(dest_path) and os.path.getsize(dest_path) > 0
    except OSError as exc:
        logger.warning('种子对象复制失败 %s/%s: %s', bucket_name, object_key, exc)
        return False


def ensure_local_object(bucket_name: str, object_key: str) -> Optional[str]:
    """确保对象存在于 flat 本地存储；缺失时尝试从种子目录懒加载。"""
    path = local_object_path(bucket_name, object_key)
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        return path
    if materialize_seed_object(bucket_name, object_key, path):
        logger.info('已从种子目录懒加载对象: %s/%s -> %s', bucket_name, object_key, path)
        return path
    return None


def migrate_seed_data_to_local_storage(
    buckets: Optional[Iterable[str]] = None,
    skip_existing: bool = True,
) -> Tuple[int, int]:
    """将 .scripts/minio 种子数据批量同步到 flat 本地存储。返回 (copied, skipped)。"""
    seed_root = get_minio_seed_data_root()
    if not seed_root:
        return 0, 0

    bucket_filter = set(buckets) if buckets is not None else None
    copied = 0
    skipped = 0

    for bucket_name in sorted(os.listdir(seed_root)):
        bucket_path = os.path.join(seed_root, bucket_name)
        if not os.path.isdir(bucket_path):
            continue
        if bucket_filter is not None and bucket_name not in bucket_filter:
            continue

        for dirpath, _, filenames in os.walk(bucket_path):
            for filename in filenames:
                src = os.path.join(dirpath, filename)
                if not os.path.isfile(src):
                    continue
                rel = os.path.relpath(src, bucket_path).replace('\\', '/')
                dest = local_object_path(bucket_name, rel)
                if skip_existing and os.path.isfile(dest) and os.path.getsize(dest) > 0:
                    skipped += 1
                    continue
                try:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(src, dest)
                    copied += 1
                except OSError as exc:
                    logger.warning('种子同步失败 %s/%s: %s', bucket_name, rel, exc)

    if copied:
        logger.info('种子 -> local-storage 同步完成: copied=%s skipped=%s', copied, skipped)
    return copied, skipped


def migrate_minio_s3_to_local_storage(
    buckets: Optional[Iterable[str]] = None,
    skip_existing: bool = True,
) -> Tuple[int, int]:
    """MinIO 服务可用时，通过 S3 API 将对象同步到 flat 本地存储。"""
    if not minio_storage_enabled():
        return 0, 0
    try:
        from app.services.minio_service import ModelService
    except Exception:
        return 0, 0

    bucket_filter = list(buckets) if buckets is not None else None
    if bucket_filter is None:
        bucket_filter = ['models']

    copied = 0
    skipped = 0
    try:
        client = ModelService.get_minio_client()
    except Exception as exc:
        logger.debug('MinIO 客户端不可用，跳过 S3 同步: %s', exc)
        return 0, 0

    for bucket_name in bucket_filter:
        try:
            if not client.bucket_exists(bucket_name):
                continue
        except Exception:
            continue
        try:
            objects = client.list_objects(bucket_name, recursive=True)
        except Exception as exc:
            logger.warning('列举 MinIO 桶失败 %s: %s', bucket_name, exc)
            continue
        for obj in objects:
            object_key = obj.object_name
            if not object_key or object_key.endswith('/'):
                continue
            dest = local_object_path(bucket_name, object_key)
            if skip_existing and os.path.isfile(dest) and os.path.getsize(dest) > 0:
                skipped += 1
                continue
            try:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                client.fget_object(bucket_name, object_key, dest)
                copied += 1
            except Exception as exc:
                logger.warning('S3 同步失败 %s/%s: %s', bucket_name, object_key, exc)

    if copied:
        logger.info('MinIO S3 -> local-storage 同步完成: copied=%s skipped=%s', copied, skipped)
    return copied, skipped


def migrate_minio_fs_to_local_storage(
    buckets: Optional[Iterable[str]] = None,
    skip_existing: bool = True,
) -> Tuple[int, int]:
    """兼容旧调用：优先种子目录，MinIO 在线时补充 S3 同步。"""
    copied, skipped = migrate_seed_data_to_local_storage(buckets=buckets, skip_existing=skip_existing)
    s3_copied, s3_skipped = migrate_minio_s3_to_local_storage(buckets=buckets, skip_existing=skip_existing)
    return copied + s3_copied, skipped + s3_skipped


def save_local_object(bucket_name: str, object_key: str, source_path: str) -> Tuple[bool, Optional[str]]:
    if minio_storage_enabled():
        return False, 'MinIO 已启用，不应写入本地存储'
    dest = local_object_path(bucket_name, object_key)
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(source_path, dest)
        return True, None
    except OSError as exc:
        return False, str(exc)


def read_local_object(bucket_name: str, object_key: str) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    path = ensure_local_object(bucket_name, object_key)
    if not path:
        return None, None, f'本地对象不存在: {bucket_name}/{object_key}'
    try:
        with open(path, 'rb') as handle:
            content = handle.read()
        filename = os.path.basename(object_key) or 'download'
        guessed, _ = mimetypes.guess_type(filename)
        return content, guessed or 'application/octet-stream', None
    except OSError as exc:
        return None, None, str(exc)


def local_object_exists(bucket_name: str, object_key: str) -> bool:
    if os.path.isfile(local_object_path(bucket_name, object_key)):
        return True
    return seed_object_path(bucket_name, object_key) is not None


def delete_local_object(bucket_name: str, object_key: str) -> bool:
    path = local_object_path(bucket_name, object_key)
    try:
        if os.path.isfile(path):
            os.remove(path)
            return True
    except OSError:
        return False
    return False
