"""
算法子进程内部服务 URL 解析（mini 形态 vs 完整网关形态）。
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

SHANGHAI_TZ = timezone(timedelta(hours=8))
# Docker 容器常为 UTC，旧逻辑把 fromtimestamp 的 UTC 墙钟误标为东八区，相差 8 小时
LEGACY_PLAYBACK_TZ_OFFSET_SECONDS = 8 * 3600

_MINI_PROFILES = frozenset({'mini', '1', 'minimal', '4g'})
_NON_MINI_PROFILES = frozenset({'standard', '2', 'std', '16g', 'full', '3', 'complete'})
_LEGACY_GATEWAY_BASES = frozenset({
    'http://localhost:48080',
    'http://127.0.0.1:48080',
})
_MINI_SYSTEM_PORTS = frozenset({'48099'})


def is_mini_deploy_profile() -> bool:
    profile = (os.getenv('EASYAIOT_DEPLOY_PROFILE') or '').strip().lower()
    if profile in _NON_MINI_PROFILES:
        return False
    if profile in _MINI_PROFILES:
        return True
    # 未显式声明形态时，根据 mini 直连端口推断（iot-system:48099）
    for key in ('GATEWAY_URL', 'JAVA_BACKEND_URL'):
        url = (os.getenv(key) or '').strip().rstrip('/')
        if url and any(url.endswith(f':{port}') for port in _MINI_SYSTEM_PORTS):
            return True
    return False


def minio_storage_enabled() -> bool:
    """mini 形态默认不部署 MinIO，空间/抓拍/录像等走本地路径。"""
    explicit = (os.getenv('MINIO_ENABLED') or '').strip().lower()
    if explicit in ('1', 'true', 'yes', 'on'):
        return True
    if explicit in ('0', 'false', 'no', 'off'):
        return False
    return not is_mini_deploy_profile()


def resolve_video_service_base_url() -> str:
    explicit = (os.getenv('VIDEO_SERVICE_URL') or '').strip().rstrip('/')
    if explicit:
        return explicit
    port = (os.getenv('VIDEO_SERVICE_PORT') or os.getenv('FLASK_RUN_PORT') or '6000').strip()
    host = (os.getenv('VIDEO_SERVICE_HOST') or os.getenv('POD_IP') or os.getenv('HOST_IP') or '127.0.0.1').strip()
    return f'http://{host}:{port}'


def should_use_gateway_for_video_api() -> bool:
    override = (os.getenv('VIDEO_API_USE_GATEWAY') or '').strip().lower()
    if override in ('1', 'true', 'yes', 'on'):
        return True
    if override in ('0', 'false', 'no', 'off'):
        return False
    if is_mini_deploy_profile():
        return False
    gateway = (os.getenv('GATEWAY_URL') or '').strip().rstrip('/')
    if not gateway or gateway in _LEGACY_GATEWAY_BASES:
        return False
    return True


def resolve_gateway_base_url() -> str:
    for key in ('JAVA_BACKEND_URL', 'GATEWAY_URL'):
        url = (os.getenv(key) or '').strip().rstrip('/')
        if url:
            return url
    return 'http://localhost:48080'


def resolve_alert_hook_url() -> str:
    explicit = (os.getenv('ALERT_HOOK_URL') or '').strip()
    if explicit:
        return explicit
    if should_use_gateway_for_video_api():
        return f'{resolve_gateway_base_url()}/admin-api/video/alert/hook'
    return f'{resolve_video_service_base_url()}/video/alert/hook'


def resolve_face_matching_publish_url() -> str:
    explicit = (os.getenv('FACE_MATCHING_PUBLISH_URL') or '').strip()
    if explicit:
        return explicit
    if should_use_gateway_for_video_api():
        return f'{resolve_gateway_base_url()}/admin-api/video/face/matching/publish'
    return f'{resolve_video_service_base_url()}/video/face/matching/publish'


def resolve_plate_matching_publish_url() -> str:
    explicit = (os.getenv('PLATE_MATCHING_PUBLISH_URL') or '').strip()
    if explicit:
        return explicit
    if should_use_gateway_for_video_api():
        return f'{resolve_gateway_base_url()}/admin-api/video/plate/matching/publish'
    return f'{resolve_video_service_base_url()}/video/plate/matching/publish'


def parse_alert_time_str(alert_time_str: str):
    """解析告警时间为东八区 aware datetime。"""
    if not alert_time_str or not str(alert_time_str).strip():
        return None, '告警时间不能为空'
    text = str(alert_time_str).strip()
    for fmt in (
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
    ):
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=SHANGHAI_TZ)
            else:
                parsed = parsed.astimezone(SHANGHAI_TZ)
            return parsed, None
        except ValueError:
            continue
    return None, '告警时间格式错误，应为：YYYY-MM-DD HH:MM:SS'


def normalize_to_shanghai_naive(value):
    """统一为东八区 naive 墙钟，便于与 Alert.time / Playback.event_time 比较。"""
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(SHANGHAI_TZ).replace(tzinfo=None)


def ensure_shanghai_aware(value):
    """将 datetime 规范为东八区 aware（naive 按 UTC 绝对时刻再转东八区）。"""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).astimezone(SHANGHAI_TZ)
    return value.astimezone(SHANGHAI_TZ)


def alert_time_to_utc(value):
    return ensure_shanghai_aware(value).astimezone(timezone.utc)


def epoch_to_shanghai_datetime(ts: float) -> datetime:
    """Unix 时间戳（秒）转为东八区 aware datetime。"""
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).astimezone(SHANGHAI_TZ)


def now_shanghai_naive() -> datetime:
    """当前东八区墙钟（naive），与 captured_at / event_time 存储约定一致。"""
    return datetime.now(SHANGHAI_TZ).replace(tzinfo=None)


def shanghai_time_str_from_epoch(ts: float) -> str:
    """Unix 时间戳格式化为东八区墙钟字符串（YYYY-MM-DD HH:MM:SS）。"""
    return epoch_to_shanghai_datetime(float(ts)).strftime('%Y-%m-%d %H:%M:%S')


def now_shanghai_time_str() -> str:
    """当前东八区墙钟字符串（YYYY-MM-DD HH:MM:SS）。"""
    return now_shanghai_naive().strftime('%Y-%m-%d %H:%M:%S')


def shanghai_isoformat(dt) -> str | None:
    """东八区墙钟序列化为 ISO-8601（+08:00），便于前端按本地时间展示。"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        aware = dt.replace(tzinfo=SHANGHAI_TZ)
    else:
        aware = dt.astimezone(SHANGHAI_TZ)
    return aware.isoformat()


def save_time_cutoff_naive(save_time_hours) -> datetime | None:
    """东八区 naive 截止时间，与 event_time/captured_at（东八区墙钟）直接比较。

    save_time_hours <= 0 表示永久保存，返回 None。
    """
    try:
        hours = int(save_time_hours)
    except (TypeError, ValueError):
        return None
    if hours <= 0:
        return None
    return (datetime.now(SHANGHAI_TZ) - timedelta(hours=hours)).replace(tzinfo=None)


def playback_segment_utc_starts(event_time):
    """返回录像片段可能的 UTC 起始时刻（含旧版时区误标数据）。"""
    aware = ensure_shanghai_aware(event_time)
    candidates = [aware.astimezone(timezone.utc)]
    naive_wall = aware.replace(tzinfo=None)
    legacy_utc = naive_wall.replace(tzinfo=timezone.utc)
    if legacy_utc not in candidates:
        candidates.append(legacy_utc)
    return candidates


def score_playback_for_alert(playback, alert_time, time_range: int = 300):
    """匹配告警与录像片段，返回时间差（秒）或 None。"""
    alert_utc = alert_time_to_utc(alert_time)
    duration = int(getattr(playback, 'duration', None) or 0) or 1
    best = None
    for seg_start in playback_segment_utc_starts(playback.event_time):
        seg_end = seg_start + timedelta(seconds=duration)
        legacy_start = seg_start - timedelta(seconds=duration)
        if legacy_start <= alert_utc <= seg_end:
            return 0
        center = seg_start + timedelta(seconds=duration / 2)
        diff = abs((center - alert_utc).total_seconds())
        if diff <= time_range and (best is None or diff < best):
            best = diff
    return best


def is_local_filesystem_path(path: str) -> bool:
    """是否为宿主机/容器内本地绝对路径（非 HTTP、非 MinIO API、非 VIDEO API）。"""
    if not path or not isinstance(path, str):
        return False
    p = path.strip()
    if not p.startswith('/'):
        return False
    if p.startswith('/api/') or p.startswith('/video/'):
        return False
    return (
        p.startswith('/data/')
        or p.startswith('/mnt/')
        or p.startswith('/app/')
        or p.startswith('/tmp/')
    )


def build_alert_image_api_url(local_path: str) -> str:
    from urllib.parse import quote
    return f'/video/alert/image?path={quote(local_path, safe="")}'


def build_alert_record_api_url(local_path: str) -> str:
    from urllib.parse import quote
    return f'/video/alert/record?path={quote(local_path, safe="")}'


def resolve_playback_display_url(file_path: str) -> str:
    """将 DB 中的录像 file_path 转为浏览器可请求的 VIDEO API 相对路径。"""
    if not file_path:
        return file_path
    u = file_path.strip()
    if is_local_filesystem_path(u):
        return build_alert_record_api_url(u)
    return u


def build_snap_image_api_url(space_id: int, object_name: str) -> str:
    from urllib.parse import quote
    safe_name = quote(object_name, safe='/')
    return f'/video/snap/space/{space_id}/image/{safe_name}'


def build_record_video_api_url(space_id: int, object_name: str) -> str:
    from urllib.parse import quote
    safe_name = quote(object_name, safe='/')
    return f'/video/record/space/{space_id}/video/{safe_name}'


def normalize_media_display_url(url: str) -> str:
    """将本地绝对路径转为前端可访问的 VIDEO API 相对路径。"""
    if not url:
        return url
    u = url.strip()
    if is_local_filesystem_path(u):
        return build_alert_image_api_url(u)
    return u
