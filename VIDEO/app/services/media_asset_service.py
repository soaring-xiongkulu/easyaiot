"""统一媒体资产与设备录像策略服务。"""
import posixpath
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from models import db, Device, DeviceRecordingPolicy, MediaAsset, RecordFile, RecordSpace


RECORDING_MODES = {'continuous', 'event_only', 'off'}
PLAYBACK_ROUTE_MODES = {'auto', 'direct', 'proxy'}
ASSET_TYPES = {'alert_image', 'event_clip', 'recording_segment', 'snapshot', 'thumbnail'}
ASSET_STATUSES = {'pending', 'uploading', 'ready', 'failed', 'deleted'}
STORAGE_SCOPES = {'edge', 'central'}
STORAGE_BACKENDS = {'local', 'minio'}


def _utc_now():
    return datetime.now(timezone.utc)


def parse_timestamp(value):
    if value in (None, ''):
        return None
    if isinstance(value, datetime):
        return (value.replace(tzinfo=timezone.utc) if value.tzinfo is None
                else value.astimezone(timezone.utc))
    normalized = str(value).strip().replace('Z', '+00:00')
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_object_key(value: str) -> str:
    """资产路径只能是 POSIX 相对键，绝不接受宿主机绝对路径。"""
    raw = str(value or '').strip().replace('\\', '/')
    if not raw or raw.startswith('/'):
        raise ValueError('object_key 必须是非空相对路径')
    normalized = posixpath.normpath(raw)
    if normalized in ('.', '..') or normalized.startswith('../'):
        raise ValueError('object_key 不能越出媒体根目录')
    return normalized


def get_or_default_policy(device_id: str, persist: bool = False) -> DeviceRecordingPolicy:
    device = Device.query.get(device_id)
    if not device:
        raise ValueError(f'设备不存在: {device_id}')
    policy = DeviceRecordingPolicy.query.filter_by(device_id=device_id).first()
    if policy:
        return policy
    policy = DeviceRecordingPolicy(
        device_id=device_id,
        recording_mode='continuous',
        retention_hours=168,
        event_pre_seconds=10,
        event_post_seconds=20,
        event_image_sync=True,
        event_clip_sync=True,
        live_transport_mode='always_push',
        playback_route_mode='auto',
    )
    if persist:
        db.session.add(policy)
        db.session.commit()
    return policy


def update_recording_policy(device_id: str, payload: Dict[str, Any]):
    policy = get_or_default_policy(device_id, persist=False)
    recording_mode = str(payload.get('recording_mode', policy.recording_mode or 'continuous')).strip().lower()
    route_mode = str(payload.get('playback_route_mode', policy.playback_route_mode or 'auto')).strip().lower()
    if recording_mode not in RECORDING_MODES:
        raise ValueError('recording_mode 仅支持 continuous/event_only/off')
    if route_mode not in PLAYBACK_ROUTE_MODES:
        raise ValueError('playback_route_mode 仅支持 auto/direct/proxy')
    retention_hours = int(payload.get(
        'retention_hours', 168 if policy.retention_hours is None else policy.retention_hours,
    ))
    event_pre_seconds = int(payload.get(
        'event_pre_seconds', 10 if policy.event_pre_seconds is None else policy.event_pre_seconds,
    ))
    event_post_seconds = int(payload.get(
        'event_post_seconds', 20 if policy.event_post_seconds is None else policy.event_post_seconds,
    ))
    if not 0 <= retention_hours <= 24 * 3650:
        raise ValueError('retention_hours 范围必须为 0～87600 小时，0 表示永久')
    if not 0 <= event_pre_seconds <= 300 or not 0 <= event_post_seconds <= 300:
        raise ValueError('事件前后录像秒数范围必须为 0～300')

    policy.recording_mode = recording_mode
    policy.retention_hours = retention_hours
    policy.event_pre_seconds = event_pre_seconds
    policy.event_post_seconds = event_post_seconds
    policy.event_image_sync = bool(payload.get('event_image_sync', policy.event_image_sync is not False))
    policy.event_clip_sync = bool(payload.get('event_clip_sync', policy.event_clip_sync is not False))
    policy.live_transport_mode = 'always_push'
    policy.playback_route_mode = route_mode
    policy.updated_at = _utc_now()
    db.session.add(policy)

    # 兼容既有录像空间清理策略；该字段本身就是小时单位。
    space = RecordSpace.query.filter_by(device_id=device_id).first()
    if space:
        space.save_time = retention_hours
        space.save_time_custom = True
    db.session.commit()
    return policy


def upsert_media_asset(payload: Dict[str, Any], *, authenticated_node_id: Optional[int] = None,
                       commit: bool = True) -> MediaAsset:
    asset_id = str(payload.get('asset_id') or payload.get('id') or uuid.uuid4())
    try:
        uuid.UUID(asset_id)
    except (TypeError, ValueError):
        raise ValueError('asset_id 必须是 UUID')
    asset_type = str(payload.get('asset_type') or '').strip().lower()
    if asset_type not in ASSET_TYPES:
        raise ValueError(f'不支持的 asset_type: {asset_type}')
    device_id = str(payload.get('device_id') or '').strip()
    if not device_id:
        raise ValueError('device_id 不能为空')
    if not Device.query.get(device_id):
        raise ValueError(f'设备不存在: {device_id}')
    storage_scope = str(payload.get('storage_scope') or '').strip().lower()
    storage_backend = str(payload.get('storage_backend') or '').strip().lower()
    status = str(payload.get('status') or 'pending').strip().lower()
    if storage_scope not in STORAGE_SCOPES or storage_backend not in STORAGE_BACKENDS:
        raise ValueError('storage_scope/storage_backend 不合法')
    if status not in ASSET_STATUSES:
        raise ValueError(f'不支持的资产状态: {status}')
    object_key = normalize_object_key(payload.get('object_key'))

    source_node_id = payload.get('source_node_id')
    storage_node_id = payload.get('storage_node_id')
    if authenticated_node_id is not None:
        source_node_id = int(source_node_id or authenticated_node_id)
        storage_node_id = int(storage_node_id or authenticated_node_id) if storage_scope == 'edge' else storage_node_id
        if source_node_id != authenticated_node_id or (
                storage_scope == 'edge' and int(storage_node_id) != authenticated_node_id):
            raise ValueError('节点只能上报属于自己的边缘资产')
    if storage_scope == 'edge' and storage_node_id is None:
        raise ValueError('边缘资产必须填写 storage_node_id')
    if storage_scope == 'central' and storage_backend == 'minio' and not payload.get('bucket_name'):
        raise ValueError('中心 MinIO 资产必须填写 bucket_name')

    asset = MediaAsset.query.get(asset_id)
    if not asset and storage_scope == 'central' and payload.get('bucket_name'):
        asset = MediaAsset.query.filter_by(
            bucket_name=str(payload.get('bucket_name')),
            object_key=object_key,
        ).first()
    if not asset:
        asset = MediaAsset(id=asset_id, created_at=_utc_now())
    elif authenticated_node_id is not None:
        if asset.source_node_id is not None and int(asset.source_node_id) != authenticated_node_id:
            raise ValueError('节点不能覆盖其他节点上报的资产')
        if (asset.storage_scope == 'edge' and asset.storage_node_id is not None
                and int(asset.storage_node_id) != authenticated_node_id):
            raise ValueError('节点不能覆盖其他边缘节点存储的资产')

    asset.asset_type = asset_type
    asset.device_id = device_id
    asset.alert_id = payload.get('alert_id')
    asset.task_id = payload.get('task_id')
    asset.source_node_id = source_node_id
    asset.storage_node_id = storage_node_id
    asset.storage_generation = max(1, int(payload.get('storage_generation') or 1))
    asset.storage_scope = storage_scope
    asset.storage_backend = storage_backend
    asset.bucket_name = payload.get('bucket_name')
    asset.object_key = object_key
    asset.status = status
    asset.start_time = parse_timestamp(payload.get('start_time'))
    asset.end_time = parse_timestamp(payload.get('end_time'))
    asset.duration_ms = payload.get('duration_ms')
    asset.file_size = payload.get('file_size')
    asset.content_type = payload.get('content_type') or 'application/octet-stream'
    asset.etag = payload.get('etag')
    asset.checksum = payload.get('checksum')
    asset.retry_count = max(0, int(payload.get('retry_count') or 0))
    asset.last_error = payload.get('last_error')
    asset.expires_at = parse_timestamp(payload.get('expires_at'))
    asset.updated_at = _utc_now()
    db.session.add(asset)
    if commit:
        db.session.commit()
    return asset


def upsert_central_recording_asset(record: RecordFile, commit: bool = False) -> MediaAsset:
    duration_seconds = int(record.duration or 0)
    start_time = record.event_time
    if start_time is not None and start_time.tzinfo is None:
        # 既有 record_file.event_time 是上海本地 naive；统一资产时间轴必须转换为 UTC 事实值。
        from models import SHANGHAI_TZ
        start_time = start_time.replace(tzinfo=SHANGHAI_TZ).astimezone(timezone.utc)
    asset = upsert_media_asset({
        'asset_id': record.asset_id or str(uuid.uuid4()),
        'asset_type': 'recording_segment',
        'device_id': record.device_id,
        'task_id': record.task_id,
        'storage_scope': 'central',
        'storage_backend': 'minio',
        'bucket_name': record.bucket_name,
        'object_key': record.object_name,
        'status': 'ready',
        'start_time': start_time,
        'end_time': start_time if not duration_seconds else None,
        'duration_ms': duration_seconds * 1000 if record.duration is not None else None,
        'file_size': record.file_size,
        'content_type': record.content_type or 'video/mp4',
        'etag': record.etag,
    }, commit=False)
    # end_time 上面先支持 datetime；数值时间戳单独转换，避免输入格式歧义。
    if duration_seconds and start_time:
        from datetime import timedelta
        asset.end_time = start_time + timedelta(seconds=duration_seconds)
    record.asset_id = asset.id
    if commit:
        db.session.commit()
    return asset


def report_assets(items: Iterable[Dict[str, Any]], authenticated_node_id: int):
    results = []
    for payload in items:
        asset = upsert_media_asset(payload, authenticated_node_id=authenticated_node_id, commit=False)
        results.append({'asset_id': asset.id, 'status': asset.status})
    db.session.commit()
    return results


def query_assets(*, device_id=None, begin=None, end=None, asset_type=None, status=None,
                 page_no=1, page_size=100):
    query = MediaAsset.query
    if device_id:
        query = query.filter(MediaAsset.device_id == device_id)
    if asset_type:
        query = query.filter(MediaAsset.asset_type == asset_type)
    if status:
        query = query.filter(MediaAsset.status == status)
    if begin:
        query = query.filter(MediaAsset.end_time >= parse_timestamp(begin))
    if end:
        query = query.filter(MediaAsset.start_time <= parse_timestamp(end))
    pagination = query.order_by(MediaAsset.start_time.desc(), MediaAsset.created_at.desc()).paginate(
        page=max(1, int(page_no)), per_page=min(500, max(1, int(page_size))), error_out=False,
    )
    return {'items': [asset.to_dict() for asset in pagination.items], 'total': pagination.total}
