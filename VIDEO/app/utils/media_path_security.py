"""本地媒体文件访问边界校验。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional


def _normalized_root(value: str | os.PathLike) -> Optional[Path]:
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        return Path(os.path.expandvars(os.path.expanduser(raw))).resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return None


def configured_media_roots(extra_roots: Iterable[str] = ()) -> list[Path]:
    """返回允许通过媒体接口读取的根目录。"""
    candidates: list[str] = list(extra_roots)
    for key in (
        'ALERT_IMAGES_DIR',
        'FACE_IMAGES_DIR',
        'PLATE_IMAGES_DIR',
        'EDGE_RECORDING_ROOT',
        'LOCAL_STORAGE_ROOT',
        'AI_LOCAL_STORAGE_ROOT',
        'EASYAIOT_MEDIA_ROOT',
        'MEDIA_HOST_DATA_ROOT',
        'SRS_HOST_DATA_ROOT',
    ):
        value = (os.getenv(key) or '').strip()
        if value:
            candidates.append(value)

    # 容器内固定媒体挂载；仅允许这些明确的媒体根，不允许任意系统目录。
    candidates.extend(('/mnt/easyaiot-media', '/data/playbacks', '/data/local-storage'))

    roots: list[Path] = []
    for candidate in candidates:
        root = _normalized_root(candidate)
        if root is not None and root not in roots:
            roots.append(root)
    return roots


def resolve_allowed_media_file(
    path: str,
    *,
    extra_roots: Iterable[str] = (),
    require_exists: bool = True,
) -> Optional[Path]:
    """解析并校验媒体文件，拒绝目录穿越和软链接逃逸。"""
    raw = str(path or '').strip()
    if not raw or not os.path.isabs(raw):
        return None
    try:
        candidate = Path(raw).resolve(strict=require_exists)
    except (OSError, RuntimeError, ValueError):
        return None

    for root in configured_media_roots(extra_roots):
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        if require_exists and not candidate.is_file():
            return None
        return candidate
    return None
