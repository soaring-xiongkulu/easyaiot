"""
SRS 本地回放录像磁盘守护服务（全部署形态通用）。

防止 playbacks（live + ai 等）撑满宿主机磁盘：
1. 按设备/全局文件年龄与数量上限清理（同时覆盖 live/ai）
2. 按全局容量上限（PLAYBACK_GLOBAL_MAX_GB）清理
3. 清理历史误配目录（如 ~/easyaiot/data/playbacks）
4. 同步删除 Playback 孤儿库记录
5. 磁盘使用率超阈值时紧急删除最旧文件
"""
from __future__ import annotations

import errno
import logging
import os
import shutil
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

FlvEntry = Tuple[str, float, int]  # path, mtime, size_bytes


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ('1', 'true', 'yes', 'on')


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return int(str(raw).strip())
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return float(str(raw).strip())
    except ValueError:
        return default


def _normalize_config_path(path: str) -> str:
    if not path:
        return path
    return os.path.normpath(os.path.expanduser(os.path.expandvars(path.strip())))


def get_srs_record_dir() -> str:
    """录像根目录（容器内优先 /data/playbacks 或 /mnt/easyaiot-media/playbacks）。"""
    candidates: List[str] = []
    try:
        from cluster_storage import get_playbacks_dir, is_cluster_mode
        if is_cluster_mode() or (os.getenv('MEDIA_HOST_DATA_ROOT') or '').strip():
            candidates.append(get_playbacks_dir())
    except ImportError:
        pass

    for key in ('MEDIA_RECORD_DIR', 'SRS_RECORD_DIR'):
        raw = (os.getenv(key) or '').strip()
        if raw:
            candidates.append(_normalize_config_path(raw))

    host_root = (os.getenv('MEDIA_HOST_DATA_ROOT') or os.getenv('SRS_HOST_DATA_ROOT') or '').strip()
    if host_root:
        candidates.append(os.path.join(_normalize_config_path(host_root), 'playbacks'))

    # Docker 固定挂载点（宿主机路径写进 env 时，容器内该路径往往不存在）
    candidates.extend([
        '/data/playbacks',
        '/mnt/easyaiot-media/playbacks',
    ])

    seen = set()
    for path in candidates:
        if not path or path in seen:
            continue
        seen.add(path)
        if os.path.isdir(path):
            return path

    try:
        from app.services.media_dvr_utils import discover_srs_host_data_root
        return os.path.join(discover_srs_host_data_root(), 'playbacks')
    except Exception:
        return '/data/playbacks'


def get_snap_staging_dir() -> str:
    try:
        from cluster_storage import get_snaps_dir
        return get_snaps_dir()
    except ImportError:
        snap_dir = (os.getenv('MEDIA_SNAP_DIR') or '').strip()
        if snap_dir:
            return snap_dir.rstrip('/\\')
        host_root = (os.getenv('MEDIA_HOST_DATA_ROOT') or '/mnt/easyaiot-media').strip()
        return os.path.join(host_root.rstrip('/\\'), 'snaps')


def get_camera_screenshot_dir() -> str:
    """区域检测/设备封面等截图的本地落盘目录（mini 形态，不部署 MinIO）。"""
    explicit = (os.getenv('MEDIA_CAMERA_SCREENSHOT_DIR') or '').strip()
    if explicit:
        return explicit.rstrip('/\\')
    record_dir = (os.getenv('MEDIA_RECORD_DIR') or get_srs_record_dir()).strip()
    if record_dir.startswith('/data'):
        return os.path.join('/data', 'camera-screenshots')
    snap_root = get_snap_staging_dir()
    parent = os.path.dirname(snap_root.rstrip('/\\'))
    return os.path.join(parent, 'camera-screenshots')


def _playback_dir_mode() -> int:
    raw = os.getenv('PLAYBACK_DIR_MODE', '777')
    try:
        return int(str(raw).strip(), 8)
    except ValueError:
        return 0o777


def _playback_file_mode() -> int:
    raw = os.getenv('PLAYBACK_FILE_MODE', '666')
    try:
        return int(str(raw).strip(), 8)
    except ValueError:
        return 0o666


def _use_sudo_for_playback_fix() -> bool:
    return _env_bool('PLAYBACK_FIX_USE_SUDO', False)


def _sudo_run(args: List[str], timeout: int = 15) -> bool:
    cmd = ['sudo', '-n', *args]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            logger.debug('sudo 命令失败: %s, stderr=%s', cmd, (result.stderr or '').strip())
            return False
        return True
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError) as exc:
        logger.debug('sudo 命令异常: %s, %s', cmd, exc)
        return False


def ensure_playback_path_deletable(file_path: str) -> None:
    """修复 SRS root 属主录像路径权限，使当前进程可删除。

    删除文件需要父目录写权限；SRS 以 root 创建 755 目录时普通用户无法 unlink。
    从文件向上至 SRS_RECORD_DIR，对目录 chmod（默认 777）、对文件 chmod（默认 666）。
    当前用户无权限时可通过 PLAYBACK_FIX_USE_SUDO=true 调用 sudo chmod。
    """
    if not file_path:
        return

    record_dir = os.path.normpath(get_srs_record_dir())
    normalized = os.path.normpath(file_path)
    if not (normalized == record_dir or normalized.startswith(record_dir + os.sep)):
        return

    dir_mode = _playback_dir_mode()
    file_mode = _playback_file_mode()
    targets: List[Tuple[str, str]] = []
    if os.path.isfile(normalized):
        targets.append(('file', normalized))

    current = os.path.dirname(normalized)
    while current.startswith(record_dir):
        targets.append(('dir', current))
        if current == record_dir:
            break
        current = os.path.dirname(current)

    failed: List[Tuple[str, str]] = []
    for kind, path in targets:
        mode = file_mode if kind == 'file' else dir_mode
        try:
            os.chmod(path, mode)
        except OSError:
            failed.append((kind, path))

    if not failed or not _use_sudo_for_playback_fix():
        return

    for kind, path in failed:
        mode_str = oct(file_mode if kind == 'file' else dir_mode)[2:]
        if not _sudo_run(['chmod', mode_str, path]):
            logger.warning('sudo 修复回放路径权限失败: %s', path)


def is_cleanup_enabled() -> bool:
    return _env_bool('PLAYBACK_CLEANUP_ENABLED', True)


def get_disk_usage_percent(path: Optional[str] = None) -> float:
    """返回 path 所在文件系统的已用空间百分比。"""
    check_path = path or get_srs_record_dir()
    try:
        if not os.path.exists(check_path):
            parent = os.path.dirname(check_path) or '/'
            check_path = parent
        usage = shutil.disk_usage(check_path)
        if usage.total <= 0:
            return 0.0
        return (usage.used / usage.total) * 100.0
    except OSError as exc:
        logger.warning('无法获取磁盘使用率 path=%s: %s', check_path, exc)
        return 0.0


def iter_flv_files(root: str, relative_subdir: Optional[str] = None) -> List[FlvEntry]:
    """递归收集 root 下所有 .flv 文件，按 mtime 升序。"""
    base = root
    if relative_subdir:
        base = os.path.join(root, relative_subdir)
    if not os.path.isdir(base):
        return []

    entries: List[FlvEntry] = []
    for dirpath, _, filenames in os.walk(base):
        for name in filenames:
            if not name.lower().endswith('.flv'):
                continue
            file_path = os.path.join(dirpath, name)
            if not os.path.isfile(file_path):
                continue
            try:
                stat = os.stat(file_path)
                entries.append((file_path, stat.st_mtime, stat.st_size))
            except OSError as exc:
                logger.warning('读取录像文件信息失败: %s, %s', file_path, exc)
    entries.sort(key=lambda item: item[1])
    return entries


def remove_playback_file(file_path: str, reason: str = '') -> bool:
    if not file_path:
        return False
    existed = os.path.isfile(file_path)
    if existed:
        ensure_playback_path_deletable(file_path)
    suffix = f' ({reason})' if reason else ''
    removed = False
    if existed:
        try:
            os.remove(file_path)
            logger.info('已删除本地回放录像: %s%s', file_path, suffix)
            _prune_empty_parents(file_path, stop_at=get_srs_record_dir())
            removed = True
        except OSError as exc:
            if (
                _use_sudo_for_playback_fix()
                and getattr(exc, 'errno', None) in (errno.EACCES, errno.EPERM)
                and _sudo_run(['rm', '-f', file_path])
            ):
                logger.info('已删除本地回放录像(sudo): %s%s', file_path, suffix)
                _prune_empty_parents(file_path, stop_at=get_srs_record_dir())
                removed = True
            elif getattr(exc, 'errno', None) == errno.ENOENT:
                removed = False
            else:
                logger.debug('删除本地回放录像失败: %s, %s', file_path, exc)
                return False

    # 文件已删或本来就不存在：同步清理 Playback 孤儿行
    _delete_playback_db_for_file(file_path)
    return removed or (not existed)


def _playback_path_aliases(file_path: str) -> List[str]:
    """同一录像在宿主机/容器不同挂载前缀下的路径别名。"""
    if not file_path:
        return []
    norm = os.path.normpath(file_path).replace('\\', '/')
    aliases = {file_path, norm}
    marker = '/playbacks/'
    idx = norm.find(marker)
    if idx >= 0:
        rel = norm[idx + len(marker):]
        aliases.add(f'/data/playbacks/{rel}')
        aliases.add(f'/mnt/easyaiot-media/playbacks/{rel}')
        host_root = (os.getenv('EASYAIOT_MEDIA_ROOT') or '').strip().rstrip('/')
        if host_root and not host_root.startswith('/mnt/easyaiot-media'):
            aliases.add(f'{host_root}/playbacks/{rel}')
    return [p for p in aliases if p]


def _delete_playback_db_for_file(file_path: str) -> int:
    """按文件路径删除 Playback 行（含路径别名）。"""
    aliases = _playback_path_aliases(file_path)
    if not aliases:
        return 0
    try:
        from models import Playback, db
        deleted = (
            Playback.query.filter(Playback.file_path.in_(aliases))
            .delete(synchronize_session=False)
        )
        if deleted:
            db.session.commit()
            logger.info('已同步删除 Playback 记录 %s 条: %s', deleted, file_path)
        return int(deleted or 0)
    except Exception as exc:
        logger.debug('同步删除 Playback 记录失败: %s, %s', file_path, exc)
        try:
            from models import db
            db.session.rollback()
        except Exception:
            pass
        return 0


def cleanup_orphan_playback_records(batch_size: int = 500, max_rows: int = 20000) -> Dict[str, int]:
    """清理指向已不存在文件的 Playback 孤儿记录。"""
    from models import Playback, db
    from app.services.media_dvr_utils import resolve_playback_absolute_path

    scanned = 0
    removed = 0
    last_id = 0
    while scanned < max_rows:
        rows = (
            Playback.query.filter(Playback.id > last_id)
            .order_by(Playback.id.asc())
            .limit(batch_size)
            .all()
        )
        if not rows:
            break
        orphan_ids: List[int] = []
        for row in rows:
            scanned += 1
            last_id = row.id
            path = (row.file_path or '').strip()
            if not path:
                orphan_ids.append(row.id)
                continue
            # MinIO / HTTP URL 不按本地文件校验
            if path.startswith('http://') or path.startswith('https://') or '/api/v1/buckets/' in path:
                continue
            abs_path = resolve_playback_absolute_path(path)
            if abs_path and os.path.isfile(abs_path):
                continue
            if os.path.isfile(path):
                continue
            orphan_ids.append(row.id)
        if orphan_ids:
            Playback.query.filter(Playback.id.in_(orphan_ids)).delete(synchronize_session=False)
            db.session.commit()
            removed += len(orphan_ids)
    if removed:
        logger.info('Playback 孤儿清理完成: scanned=%s removed=%s', scanned, removed)
    return {'scanned': scanned, 'removed': removed}


def _prune_empty_parents(file_path: str, stop_at: str) -> None:
    """删除文件后向上清理空目录（不超过 stop_at）。"""
    stop_at = os.path.normpath(stop_at)
    current = os.path.normpath(os.path.dirname(file_path))
    while current.startswith(stop_at) and current != stop_at:
        try:
            if not os.path.isdir(current):
                break
            if os.listdir(current):
                break
            os.rmdir(current)
            current = os.path.dirname(current)
        except OSError:
            if _use_sudo_for_playback_fix() and _sudo_run(['rmdir', current]):
                current = os.path.dirname(current)
                continue
            break


def remove_local_after_minio_upload(file_path: str) -> bool:
    """MinIO 上传成功后删除本地副本。"""
    if not _env_bool('PLAYBACK_DELETE_AFTER_UPLOAD', True):
        return False
    if not is_cleanup_enabled():
        return False
    return remove_playback_file(file_path, reason='已上传MinIO')


def _delete_oldest_entries(
    entries: List[FlvEntry],
    delete_count: int,
    reason: str,
) -> Dict[str, int]:
    deleted = 0
    freed_bytes = 0
    for i in range(min(delete_count, len(entries))):
        path, _, size = entries[i]
        if remove_playback_file(path, reason=reason):
            deleted += 1
            freed_bytes += size
    return {'deleted': deleted, 'freed_bytes': freed_bytes}


def _playback_app_names(record_dir: Optional[str] = None) -> List[str]:
    """SRS dvr_path 下的 app 名（live/ai/gb28181/...）。"""
    root = record_dir or get_srs_record_dir()
    if not os.path.isdir(root):
        return []
    names: List[str] = []
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if os.path.isdir(path) and not name.startswith('.'):
            names.append(name)
    # 常见 app 优先，确保即便空目录也被纳入策略
    preferred = ['live', 'ai', 'gb28181']
    ordered = [n for n in preferred if n in names]
    ordered.extend(n for n in names if n not in ordered)
    return ordered


def _device_dirs_for_id(device_id: str, record_dir: Optional[str] = None) -> List[str]:
    """同一 device_id 在 live/ai 等 app 下的目录列表。"""
    root = record_dir or get_srs_record_dir()
    dirs: List[str] = []
    for app in _playback_app_names(root):
        path = os.path.join(root, app, str(device_id))
        if os.path.isdir(path):
            dirs.append(path)
    return dirs


def cleanup_device_expired_recordings(
    device_id: str,
    max_age_hours: Optional[int] = None,
) -> Dict[str, int]:
    """按文件年龄清理单设备在 live/ai 等目录下的过期本地录像。"""
    if not is_cleanup_enabled():
        return {'skipped': 1}

    max_age_hours = max_age_hours if max_age_hours is not None else _env_int('PLAYBACK_MAX_AGE_HOURS', 24)
    if max_age_hours <= 0:
        return {'skipped': 1, 'reason': 'max_age_disabled', 'device_id': device_id}

    device_dirs = _device_dirs_for_id(device_id)
    entries: List[FlvEntry] = []
    for device_dir in device_dirs:
        entries.extend(iter_flv_files(device_dir))
    if not entries:
        return {'device_id': device_id, 'total': 0, 'deleted': 0}

    entries.sort(key=lambda item: item[1])
    cutoff = datetime.now().timestamp() - max_age_hours * 3600
    expired = [e for e in entries if e[1] < cutoff]
    if not expired:
        return {'device_id': device_id, 'total': len(entries), 'deleted': 0}

    result = _delete_oldest_entries(expired, len(expired), reason=f'设备{device_id}超过{max_age_hours}小时')
    result['device_id'] = device_id
    result['total'] = len(entries)
    if result['deleted'] > 0:
        logger.info(
            '设备回放录像过期清理: device_id=%s, apps=%s, 超过%s小时, 删除=%s',
            device_id, len(device_dirs), max_age_hours, result['deleted'],
        )
    return result


def _list_recorded_device_ids() -> List[str]:
    """扫描 live/ai/... 下所有设备目录 ID。"""
    root = get_srs_record_dir()
    device_ids: set = set()
    for app in _playback_app_names(root):
        app_dir = os.path.join(root, app)
        try:
            for name in os.listdir(app_dir):
                if os.path.isdir(os.path.join(app_dir, name)) and not name.startswith('.'):
                    device_ids.add(name)
        except OSError:
            continue
    return sorted(device_ids)


def _list_live_device_ids() -> List[str]:
    """兼容旧调用：现返回所有 app 下的设备 ID。"""
    return _list_recorded_device_ids()


def _resolve_device_playback_max_age_map() -> Dict[str, int]:
    """返回 device_id -> 保留小时数；0 表示永久（跳过年龄清理）。"""
    try:
        from models import RecordSpace
        from app.services.space_save_time_service import enrich_record_space_dict, DEFAULT_SAVE_TIME

        result: Dict[str, int] = {}
        for space in RecordSpace.query.filter(RecordSpace.device_id.isnot(None)).all():
            info = enrich_record_space_dict({'save_time': space.save_time}, space)
            hours = info.get('effective_save_time')
            if hours is None:
                hours = DEFAULT_SAVE_TIME
            result[str(space.device_id)] = int(hours)
        return result
    except Exception as exc:
        logger.debug('无法解析设备录像保留策略，将使用 PLAYBACK_MAX_AGE_HOURS: %s', exc)
        return {}


def _effective_max_age_hours(device_hours: Optional[int], default_hours: int) -> int:
    """设备策略与全局上限取更严者；0=永久仅当全局也未限制时生效。"""
    global_cap = _env_int('PLAYBACK_MAX_AGE_HOURS', default_hours)
    if device_hours is None:
        return global_cap
    if device_hours <= 0:
        # 业务配置「永久」时，仍受全局硬顶约束（防磁盘撑爆）；全局 0 才真永久
        return global_cap if global_cap > 0 else 0
    if global_cap <= 0:
        return device_hours
    return min(device_hours, global_cap)


def cleanup_all_devices_expired_recordings() -> Dict[str, object]:
    """按各设备录像空间 effective save_time 清理本地 SRS 录像（含 live/ai）。"""
    if not is_cleanup_enabled():
        return {'skipped': 1}

    default_hours = _env_int('PLAYBACK_MAX_AGE_HOURS', 24)
    device_hours = _resolve_device_playback_max_age_map()
    device_ids = _list_recorded_device_ids()

    total_deleted = 0
    total_freed = 0
    device_stats: Dict[str, Dict[str, int]] = {}
    for device_id in device_ids:
        max_age = _effective_max_age_hours(device_hours.get(device_id), default_hours)
        if max_age <= 0:
            device_stats[device_id] = {'skipped': 1, 'reason': 'permanent'}
            continue
        result = cleanup_device_expired_recordings(device_id, max_age_hours=max_age)
        device_stats[device_id] = result
        total_deleted += result.get('deleted', 0)
        total_freed += result.get('freed_bytes', 0)

    return {
        'devices_checked': len(device_ids),
        'deleted': total_deleted,
        'freed_bytes': total_freed,
        'by_device': device_stats,
    }


def cleanup_device_recordings(
    device_id: str,
    max_recordings: Optional[int] = None,
    keep_ratio: Optional[float] = None,
) -> Dict[str, int]:
    """清理单设备 live/ai 目录下超出数量上限的最旧录像。"""
    if not is_cleanup_enabled():
        return {'skipped': 1}

    max_recordings = max_recordings if max_recordings is not None else _env_int('PLAYBACK_DEVICE_MAX_FILES', 30)
    keep_ratio = keep_ratio if keep_ratio is not None else _env_float('PLAYBACK_KEEP_RATIO', 0.2)
    keep_ratio = min(1.0, max(0.05, keep_ratio))

    entries: List[FlvEntry] = []
    for device_dir in _device_dirs_for_id(device_id):
        entries.extend(iter_flv_files(device_dir))
    entries.sort(key=lambda item: item[1])
    total = len(entries)
    if total <= max_recordings:
        return {'total': total, 'deleted': 0}

    keep_count = max(1, int(total * keep_ratio))
    # 数量超限时至少删到 max_recordings
    delete_count = max(total - max_recordings, total - keep_count)
    result = _delete_oldest_entries(entries, delete_count, reason=f'设备{device_id}数量超限')
    result['total'] = total
    if result['deleted'] > 0:
        logger.info(
            '设备回放录像数量清理: device_id=%s, 总数=%s, 删除=%s, 上限=%s',
            device_id, total, result['deleted'], max_recordings,
        )
    return result


def cleanup_global_recordings(
    max_recordings: Optional[int] = None,
    keep_ratio: Optional[float] = None,
) -> Dict[str, int]:
    """清理整个 playbacks 目录下超出全局数量/容量上限的最旧录像。"""
    if not is_cleanup_enabled():
        return {'skipped': 1}

    max_recordings = max_recordings if max_recordings is not None else _env_int('PLAYBACK_GLOBAL_MAX_FILES', 2000)
    keep_ratio = keep_ratio if keep_ratio is not None else _env_float('PLAYBACK_KEEP_RATIO', 0.2)
    keep_ratio = min(1.0, max(0.05, keep_ratio))
    max_gb = _env_float('PLAYBACK_GLOBAL_MAX_GB', 50)

    entries = iter_flv_files(get_srs_record_dir())
    total = len(entries)
    total_bytes = sum(e[2] for e in entries)
    deleted = 0
    freed = 0

    # 数量超限
    if total > max_recordings:
        keep_count = max(1, min(max_recordings, int(total * keep_ratio)))
        delete_count = total - keep_count
        result = _delete_oldest_entries(entries, delete_count, reason='全局数量超限')
        deleted += result.get('deleted', 0)
        freed += result.get('freed_bytes', 0)
        entries = iter_flv_files(get_srs_record_dir())
        total = len(entries)
        total_bytes = sum(e[2] for e in entries)

    # 容量超限（所有形态通用硬顶，防 live+ai 双写把盘撑爆）
    max_bytes = int(max(0.0, max_gb) * 1024 * 1024 * 1024)
    if max_bytes > 0 and total_bytes > max_bytes:
        over = total_bytes - max_bytes
        remove_n = 0
        acc = 0
        for _, _, size in entries:
            remove_n += 1
            acc += size
            if acc >= over:
                break
        result = _delete_oldest_entries(entries, remove_n, reason=f'全局容量超限>{max_gb}GB')
        deleted += result.get('deleted', 0)
        freed += result.get('freed_bytes', 0)
        entries = iter_flv_files(get_srs_record_dir())
        total = len(entries)
        total_bytes = sum(e[2] for e in entries)

    out = {
        'total': total,
        'deleted': deleted,
        'freed_bytes': freed,
        'total_bytes': total_bytes,
        'max_gb': max_gb,
    }
    if deleted:
        logger.info(
            '全局回放录像清理: 文件=%s, 容量=%.1fGB, 删除=%s, 释放=%.1fMB',
            total, total_bytes / (1024 ** 3), deleted, freed / (1024 * 1024),
        )
    return out


def cleanup_expired_files(max_age_hours: Optional[int] = None) -> Dict[str, int]:
    """按文件年龄删除过期本地录像（含 live/ai 与上传失败孤儿）。"""
    if not is_cleanup_enabled():
        return {'skipped': 1}

    max_age_hours = max_age_hours if max_age_hours is not None else _env_int('PLAYBACK_MAX_AGE_HOURS', 24)
    if max_age_hours <= 0:
        return {'skipped': 1, 'reason': 'max_age_disabled'}

    cutoff = datetime.now().timestamp() - max_age_hours * 3600
    entries = iter_flv_files(get_srs_record_dir())
    expired = [e for e in entries if e[1] < cutoff]
    if not expired:
        return {'total': len(entries), 'deleted': 0}

    result = _delete_oldest_entries(expired, len(expired), reason=f'超过{max_age_hours}小时')
    result['total'] = len(entries)
    if result['deleted'] > 0:
        logger.info(
            '回放录像过期清理: 超过%s小时, 删除=%s, 释放约=%.1fMB',
            max_age_hours, result['deleted'], result.get('freed_bytes', 0) / (1024 * 1024),
        )
    return result


def cleanup_all_devices_count_recordings() -> Dict[str, object]:
    """按设备文件数量上限清理（live+ai 合计）。"""
    if not is_cleanup_enabled():
        return {'skipped': 1}
    total_deleted = 0
    total_freed = 0
    checked = 0
    for device_id in _list_recorded_device_ids():
        checked += 1
        result = cleanup_device_recordings(device_id)
        total_deleted += result.get('deleted', 0)
        total_freed += result.get('freed_bytes', 0)
    return {
        'devices_checked': checked,
        'deleted': total_deleted,
        'freed_bytes': total_freed,
    }


def _legacy_playback_roots() -> List[str]:
    """历史/误配录像根（与当前 get_srs_record_dir 不同时一并清理）。"""
    roots: List[str] = []
    explicit = (os.getenv('PLAYBACK_LEGACY_DIRS') or '').strip()
    if explicit:
        for part in explicit.split(':'):
            part = part.strip()
            if part:
                roots.append(part)
    home = os.path.expanduser('~')
    roots.extend([
        os.path.join(home, 'easyaiot', 'data', 'playbacks'),
        '/home/ubuntu/easyaiot/data/playbacks',
        '/data/playbacks',
    ])
    current = os.path.normpath(get_srs_record_dir())
    uniq: List[str] = []
    seen = {current}
    for root in roots:
        path = os.path.normpath(os.path.expanduser(root))
        if path in seen or not os.path.isdir(path):
            continue
        # 避免把当前挂载的同一物理目录再清一遍（通过 realpath）
        try:
            if os.path.samefile(path, current):
                continue
        except OSError:
            pass
        seen.add(path)
        uniq.append(path)
    return uniq


def cleanup_legacy_playback_roots(max_age_hours: Optional[int] = None) -> Dict[str, object]:
    """清理历史路径残留录像（如 ~/easyaiot/data/playbacks），防止双写撑盘。"""
    if not is_cleanup_enabled():
        return {'skipped': 1}
    max_age_hours = max_age_hours if max_age_hours is not None else _env_int('PLAYBACK_MAX_AGE_HOURS', 24)
    if max_age_hours <= 0:
        max_age_hours = 24
    cutoff = datetime.now().timestamp() - max_age_hours * 3600
    total_deleted = 0
    total_freed = 0
    by_root: Dict[str, Dict[str, int]] = {}
    for root in _legacy_playback_roots():
        entries = iter_flv_files(root)
        expired = [e for e in entries if e[1] < cutoff]
        # 历史目录：过期全删；若仍很大则再按全局容量砍一刀
        result = _delete_oldest_entries(expired, len(expired), reason=f'历史目录过期:{root}')
        deleted = result.get('deleted', 0)
        freed = result.get('freed_bytes', 0)
        remain = iter_flv_files(root)
        remain_bytes = sum(e[2] for e in remain)
        max_legacy_gb = _env_float('PLAYBACK_LEGACY_MAX_GB', 5)
        max_bytes = int(max(0.0, max_legacy_gb) * 1024 ** 3)
        if max_bytes > 0 and remain_bytes > max_bytes:
            over = remain_bytes - max_bytes
            remove_n = 0
            acc = 0
            for _, _, size in remain:
                remove_n += 1
                acc += size
                if acc >= over:
                    break
            extra = _delete_oldest_entries(remain, remove_n, reason=f'历史目录容量超限:{root}')
            deleted += extra.get('deleted', 0)
            freed += extra.get('freed_bytes', 0)
        by_root[root] = {'deleted': deleted, 'freed_bytes': freed}
        total_deleted += deleted
        total_freed += freed
    if total_deleted:
        logger.warning(
            '历史录像目录清理: deleted=%s freed=%.1fMB roots=%s',
            total_deleted, total_freed / (1024 * 1024), list(by_root.keys()),
        )
    return {'deleted': total_deleted, 'freed_bytes': total_freed, 'by_root': by_root}


def emergency_free_disk(target_percent: Optional[float] = None) -> Dict[str, int]:
    """磁盘使用率超过紧急阈值时，持续删除最旧录像直至降至目标水位。"""
    if not is_cleanup_enabled():
        return {'skipped': 1}

    record_dir = get_srs_record_dir()
    critical = _env_float('PLAYBACK_DISK_CRITICAL_PERCENT', 90)
    target = target_percent if target_percent is not None else _env_float('PLAYBACK_DISK_TARGET_PERCENT', 75)
    disk_pct_before = get_disk_usage_percent(record_dir)

    if disk_pct_before < critical:
        return {'disk_percent': round(disk_pct_before, 2), 'deleted': 0, 'skipped': 1}

    logger.warning(
        '磁盘使用率紧急: %.1f%% >= %.1f%%, 开始删除最旧回放录像, 目标=%.1f%%',
        disk_pct_before, critical, target,
    )

    total_deleted = 0
    total_freed = 0
    batch_size = _env_int('PLAYBACK_EMERGENCY_BATCH_SIZE', 50)
    max_rounds = _env_int('PLAYBACK_EMERGENCY_MAX_ROUNDS', 200)

    for _ in range(max_rounds):
        disk_pct = get_disk_usage_percent(record_dir)
        if disk_pct < target:
            break
        entries = iter_flv_files(record_dir)
        if not entries:
            break
        batch = entries[:batch_size]
        result = _delete_oldest_entries(batch, len(batch), reason='磁盘紧急清理')
        total_deleted += result['deleted']
        total_freed += result.get('freed_bytes', 0)
        if result['deleted'] == 0:
            break

    final_pct = get_disk_usage_percent(record_dir)
    if total_deleted > 0:
        logger.warning(
            '磁盘紧急清理完成: 删除=%s, 释放约=%.1fMB, 磁盘 %.1f%% -> %.1f%%',
            total_deleted, total_freed / (1024 * 1024), disk_pct_before, final_pct,
        )
    return {
        'deleted': total_deleted,
        'freed_bytes': total_freed,
        'disk_percent_before': disk_pct_before,
        'disk_percent_after': final_pct,
    }


def run_playback_disk_guard() -> Dict[str, object]:
    """定时任务入口：综合执行各项清理策略（全形态通用）。"""
    if not is_cleanup_enabled():
        logger.debug('回放磁盘守护已关闭 (PLAYBACK_CLEANUP_ENABLED=false)')
        return {'enabled': False}

    record_dir = get_srs_record_dir()
    disk_pct = get_disk_usage_percent(record_dir)
    warn_pct = _env_float('PLAYBACK_DISK_WARN_PERCENT', 80)

    stats: Dict[str, object] = {
        'enabled': True,
        'record_dir': record_dir,
        'disk_percent': round(disk_pct, 2),
    }

    stats['devices_age'] = cleanup_all_devices_expired_recordings()
    stats['devices_count'] = cleanup_all_devices_count_recordings()
    stats['expired'] = cleanup_expired_files()
    stats['global'] = cleanup_global_recordings()
    try:
        stats['legacy'] = cleanup_legacy_playback_roots()
    except Exception as exc:
        logger.warning('历史录像目录清理失败: %s', exc)
        stats['legacy'] = {'error': str(exc)}
    try:
        stats['orphans'] = cleanup_orphan_playback_records()
    except Exception as exc:
        logger.warning('Playback 孤儿清理失败: %s', exc)
        stats['orphans'] = {'error': str(exc)}

    if disk_pct >= warn_pct:
        stats['emergency'] = emergency_free_disk()
    else:
        stats['emergency'] = {'skipped': 1, 'disk_percent': disk_pct}

    logger.info(
        '回放磁盘守护完成: dir=%s, 磁盘=%.1f%%, devices_age=%s, devices_count=%s, '
        'expired=%s, global=%s, legacy=%s, orphans=%s, emergency=%s',
        record_dir, disk_pct,
        stats.get('devices_age'), stats.get('devices_count'),
        stats.get('expired'), stats.get('global'),
        stats.get('legacy'), stats.get('orphans'), stats.get('emergency'),
    )
    return stats
