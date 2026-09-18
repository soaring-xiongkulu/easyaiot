"""
模型权重路径解析 — 本机与集群（CephFS）统一入口。

集群模式下控制面将 MinIO 对象同步至 AI_MODELS_DIR/{model_id}/，
各 VIDEO / NODE Worker 优先读取共享路径，避免每节点重复下载。
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

logger = logging.getLogger(__name__)

SYNC_MARKER = '.synced'
METADATA_FILE = 'metadata.json'

_WEIGHT_FIELDS: Tuple[Tuple[str, str], ...] = (
    ('onnx_model_path', 'onnx'),
    ('model_path', 'pt'),
    ('torchscript_model_path', 'torchscript'),
    ('tensorrt_model_path', 'tensorrt'),
    ('openvino_model_path', 'openvino'),
)


def parse_minio_download_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """解析 MinIO 下载 URL：/api/v1/buckets/{bucket}/objects/download?prefix={key}"""
    try:
        parsed = urlparse((url or '').strip())
        path_parts = parsed.path.split('/')
        if len(path_parts) < 5 or path_parts[3] != 'buckets':
            return None, None
        bucket_name = path_parts[4]
        query_params = parse_qs(parsed.query)
        object_key = query_params.get('prefix', [None])[0]
        if object_key:
            object_key = unquote(object_key)
        return bucket_name, object_key
    except Exception:
        return None, None


def model_record_from_orm(model: Any) -> Dict[str, Any]:
    """将 SQLAlchemy Model 转为 resolver 使用的 dict。"""
    class_names = None
    raw_cn = getattr(model, 'class_names', None)
    if raw_cn:
        try:
            class_names = json.loads(raw_cn) if isinstance(raw_cn, str) else raw_cn
        except Exception:
            class_names = None
    return {
        'id': getattr(model, 'id', None),
        'name': getattr(model, 'name', None),
        'version': getattr(model, 'version', None),
        'description': getattr(model, 'description', None),
        'model_origin': getattr(model, 'model_origin', None) or 'upload',
        'origin_ref': getattr(model, 'origin_ref', None),
        'model_path': getattr(model, 'model_path', None),
        'onnx_model_path': getattr(model, 'onnx_model_path', None),
        'torchscript_model_path': getattr(model, 'torchscript_model_path', None),
        'tensorrt_model_path': getattr(model, 'tensorrt_model_path', None),
        'openvino_model_path': getattr(model, 'openvino_model_path', None),
        'class_names': class_names,
    }


def pick_weights_ref(model_record: Dict[str, Any]) -> Tuple[Optional[str], str]:
    """选择最优权重引用，返回 (path_or_url, format_hint)。"""
    for field, fmt in _WEIGHT_FIELDS:
        val = (model_record.get(field) or '').strip()
        if val:
            return val, fmt
    return None, ''


def model_has_weights(model_record: Dict[str, Any]) -> bool:
    return pick_weights_ref(model_record)[0] is not None


def get_model_cluster_dir(model_id: int) -> str:
    try:
        from cluster_storage import get_ai_models_dir
        base = get_ai_models_dir()
    except ImportError:
        explicit = (os.getenv('AI_MODELS_DIR') or '').strip()
        if explicit:
            base = explicit
        else:
            base = os.path.join(os.getenv('AI_ROOT', '/opt/easyaiot/AI'), 'data', 'models')
    return os.path.join(base, str(model_id))


def _canonical_filename(weights_ref: str, fmt: str) -> str:
    ref_lower = (weights_ref or '').lower()
    if fmt == 'onnx' or ref_lower.endswith('.onnx'):
        return 'model.onnx'
    if ref_lower.endswith('.pt'):
        return 'model.pt'
    return f'model.{fmt}' if fmt else 'model.bin'


def _find_weights_in_dir(model_dir: str) -> Optional[str]:
    if not os.path.isdir(model_dir):
        return None
    for name in ('model.onnx', 'model.pt', 'weights.onnx', 'weights.pt'):
        path = os.path.join(model_dir, name)
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            return path
    for fn in sorted(os.listdir(model_dir)):
        if fn.startswith('.') or fn == METADATA_FILE:
            continue
        if fn.endswith(('.onnx', '.pt', '.engine', '.xml')):
            path = os.path.join(model_dir, fn)
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                return path
    return None


def is_cluster_synced(model_id: int) -> bool:
    model_dir = get_model_cluster_dir(model_id)
    marker = os.path.join(model_dir, SYNC_MARKER)
    if not os.path.isfile(marker):
        return False
    return _find_weights_in_dir(model_dir) is not None


def resolve_cluster_model_path(model_id: int) -> Optional[str]:
    """若集群目录已同步，返回本地权重绝对路径。"""
    if model_id < 0:
        return None
    if not is_cluster_synced(model_id):
        return None
    return _find_weights_in_dir(get_model_cluster_dir(model_id))


def try_resolve_cluster_model_path(model_id: int) -> Optional[str]:
    """Worker 侧：有 .synced 标记则读 Ceph；否则若目录内已有权重也允许使用。"""
    if model_id < 0:
        return None
    model_dir = get_model_cluster_dir(model_id)
    marker = os.path.join(model_dir, SYNC_MARKER)
    found = _find_weights_in_dir(model_dir)
    if found and (os.path.isfile(marker) or os.path.isfile(found)):
        return found
    return None


def _write_metadata(model_dir: str, model_record: Dict[str, Any], weights_file: str) -> None:
    meta = {
        'model_id': model_record.get('id'),
        'name': model_record.get('name'),
        'version': model_record.get('version'),
        'model_origin': model_record.get('model_origin'),
        'origin_ref': model_record.get('origin_ref'),
        'weights_file': os.path.basename(weights_file),
        'class_names': model_record.get('class_names'),
    }
    with open(os.path.join(model_dir, METADATA_FILE), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def _mark_synced(model_dir: str) -> None:
    marker = os.path.join(model_dir, SYNC_MARKER)
    with open(marker, 'w', encoding='utf-8') as f:
        f.write('ok\n')


def download_from_minio(bucket_name: str, object_key: str, destination_path: str) -> Tuple[bool, str]:
    """不依赖 Flask 上下文的 MinIO 下载。"""
    try:
        from minio import Minio
    except ImportError as e:
        return False, f'minio 库不可用: {e}'

    endpoint = os.getenv('MINIO_ENDPOINT', 'RustFS:9000')
    access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'

    os.makedirs(os.path.dirname(destination_path) or '.', exist_ok=True)
    tmp_path = destination_path + '.tmp'
    try:
        client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        client.fget_object(bucket_name, object_key, tmp_path)
        os.replace(tmp_path, destination_path)
        return True, ''
    except Exception as e:
        logger.error('MinIO 下载失败 bucket=%s key=%s: %s', bucket_name, object_key, e)
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return False, str(e)


def sync_model_weights_to_cluster(
    model_id: int,
    model_record: Dict[str, Any],
    download_fn: Optional[Callable[[str, str, str], Tuple[bool, str]]] = None,
) -> Tuple[bool, str, Optional[str]]:
    """
    将模型权重同步到集群共享目录。
    返回 (success, message, local_weights_path)。
    """
    if model_id < 0:
        return False, '默认模型不支持集群同步', None

    existing = resolve_cluster_model_path(model_id)
    if existing:
        return True, '已存在于集群缓存', existing

    weights_ref, fmt = pick_weights_ref(model_record)
    if not weights_ref:
        return False, '模型无可用权重路径', None

    model_dir = get_model_cluster_dir(model_id)
    os.makedirs(model_dir, exist_ok=True)
    dest_name = _canonical_filename(weights_ref, fmt)
    dest_path = os.path.join(model_dir, dest_name)

    dl = download_fn or download_from_minio

    if weights_ref.startswith('/api/v1/buckets/') or '/buckets/' in weights_ref:
        bucket, key = parse_minio_download_url(weights_ref)
        if not bucket or not key:
            return False, f'无法解析 MinIO URL: {weights_ref}', None
        ok, err = dl(bucket, key, dest_path)
        if not ok:
            return False, err or 'MinIO 下载失败', None
    elif weights_ref.startswith('http://') or weights_ref.startswith('https://'):
        import urllib.request
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=os.path.splitext(dest_name)[1])
            os.close(tmp_fd)
            urllib.request.urlretrieve(weights_ref, tmp_path)
            shutil.move(tmp_path, dest_path)
        except Exception as e:
            return False, f'HTTP 下载失败: {e}', None
    elif os.path.isfile(weights_ref):
        shutil.copy2(weights_ref, dest_path)
    elif not os.path.isabs(weights_ref):
        for root in (
            os.getenv('AI_ROOT', '/opt/easyaiot/AI'),
            os.getenv('NODE_REMOTE_AI_ROOT', ''),
        ):
            if not root:
                continue
            candidate = os.path.join(root, weights_ref)
            if os.path.isfile(candidate):
                shutil.copy2(candidate, dest_path)
                break
        else:
            return False, f'本地权重不存在: {weights_ref}', None
    else:
        return False, f'不支持的权重路径: {weights_ref}', None

    if not os.path.isfile(dest_path) or os.path.getsize(dest_path) <= 0:
        return False, '同步后权重文件无效', None

    _write_metadata(model_dir, model_record, dest_path)
    _mark_synced(model_dir)
    logger.info('模型已同步至集群目录 model_id=%s path=%s', model_id, dest_path)
    return True, '同步成功', dest_path


def ensure_models_on_cluster(
    model_ids: List[int],
    fetch_model_fn: Callable[[int], Optional[Dict[str, Any]]],
    download_fn: Optional[Callable[[str, str, str], Tuple[bool, str]]] = None,
) -> Tuple[bool, List[str]]:
    """批量预同步；返回 (all_ok, error_messages)。"""
    errors: List[str] = []
    for mid in model_ids:
        try:
            mid_int = int(mid)
        except (TypeError, ValueError):
            errors.append(f'无效 model_id: {mid}')
            continue
        if mid_int < 0:
            continue
        if is_cluster_synced(mid_int):
            continue
        record = fetch_model_fn(mid_int)
        if not record:
            errors.append(f'model {mid_int}: 记录不存在')
            continue
        ok, msg, _ = sync_model_weights_to_cluster(mid_int, record, download_fn=download_fn)
        if not ok:
            errors.append(f'model {mid_int}: {msg}')
    return len(errors) == 0, errors
