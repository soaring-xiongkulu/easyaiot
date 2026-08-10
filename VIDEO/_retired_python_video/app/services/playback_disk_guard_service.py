"""
SRS 本地回放录像磁盘守护服务。

防止 ~/easyaiot/data/playbacks（尤其 live 目录）撑满宿主机磁盘：
1. MinIO 上传成功后删除本地 .flv（默认开启）
2. 按设备/全局文件数量上限清理
3. 按文件年龄清理孤儿录像
4. 磁盘使用率超阈值时紧急删除最旧文件
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
    try:
        from cluster_storage import get_playbacks_dir, is_cluster_mode
        if is_cluster_mode() or (os.getenv('MEDIA_HOST_DATA_ROOT') or '').strip():
            return get_playbacks_dir()
    except ImportError:
        pass
    media_record = (os.getenv('MEDIA_RECORD_DIR') or '').strip()
    if media_record:
        return _normalize_config_path(media_record)
    srs_record = (os.getenv('SRS_RECORD_DIR') or '').strip()
    if srs_record:
        return _normalize_config_path(srs_record)
    host_root = (os.getenv('MEDIA_HOST_DATA_ROOT') or '').strip()
    if host_root:
        return os.path.join(_normalize_config_path(host_root), 'playbacks')
    from app.services.media_dvr_utils import discover_srs_host_data_root
    return os.path.join(discover_srs_host_data_root(), 'playbacks')


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
    if not file_path or not os.path.isfile(file_path):
        return False
    ensure_playback_path_deletable(file_path)
    suffix = f' ({reason})' if reason else ''
    try:
        os.remove(file_path)
        logger.info('已删除本地回放录像: %s%s', file_path, suffix)
        _prune_empty_parents(file_path, stop_at=get_srs_record_dir())
        return True
    except OSError as exc:
        if (
            _use_sudo_for_playback_fix()
            and getattr(exc, 'errno', None) in (errno.EACCES, errno.EPERM)
            and _sudo_run(['rm', '-f', file_path])
        ):
            logger.info('已删除本地回放录像(sudo): %s%s', file_path, suffix)
            _prune_empty_parents(file_path, stop_at=get_srs_record_dir())
            return True
        if getattr(exc, 'errno', None) == errno.ENOENT:
            return False
        logger.debug('删除本地回放录像失败: %s, %s', file_path, exc)
        return False


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


def cleanup_device_expired_recordings(
    device_id: str,
    max_age_hours: Optional[int] = None,
) -> Dict[str, int]:
    """按文件年龄清理单设备 live 目录下过期本地录像。"""
    if not is_cleanup_enabled():
        return {'skipped': 1}

    max_age_hours = max_age_hours if max_age_hours is not None else _env_int('PLAYBACK_MAX_AGE_HOURS', 1)
    if max_age_hours <= 0:
        return {'skipped': 1, 'reason': 'max_age_disabled', 'device_id': device_id}

    record_dir = get_srs_record_dir()
    device_dir = os.path.join(record_dir, 'live', str(device_id))
    entries = iter_flv_files(device_dir)
    if not entries:
        return {'device_id': device_id, 'total': 0, 'deleted': 0}

    cutoff = datetime.now().timestamp() - max_age_hours * 3600
    expired = [e for e in entries if e[1] < cutoff]
    if not expired:
        return {'device_id': device_id, 'total': len(entries), 'deleted': 0}

    result = _delete_oldest_entries(expired, len(expired), reason=f'设备{device_id}超过{max_age_hours}小时')
    result['device_id'] = device_id
    result['total'] = len(entries)
    if result['deleted'] > 0:
        logger.info(
            '设备回放录像过期清理: device_id=%s, 超过%s小时, 删除=%s',
            device_id, max_age_hours, result['deleted'],
        )
    return result


def _list_live_device_ids() -> List[str]:
    live_dir = os.path.join(get_srs_record_dir(), 'live')
    if not os.path.isdir(live_dir):
        return []
    return [
        name for name in os.listdir(live_dir)
        if os.path.isdir(os.path.join(live_dir, name))
    ]


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


def cleanup_all_devices_expired_recordings() -> Dict[str, object]:
    """按各设备录像空间 effective save_time 清理本地 SRS 录像。"""
    if not is_cleanup_enabled():
        return {'skipped': 1}

    default_hours = _env_int('PLAYBACK_MAX_AGE_HOURS', 1)
    device_hours = _resolve_device_playback_max_age_map()
    device_ids = _list_live_device_ids()

    total_deleted = 0
    total_freed = 0
    device_stats: Dict[str, Dict[str, int]] = {}
    for device_id in device_ids:
        max_age = device_hours.get(device_id, default_hours)
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
    """清理单设备 live 目录下超出数量上限的最旧录像。"""
    if not is_cleanup_enabled():
        return {'skipped': 1}

    max_recordings = max_recordings if max_recordings is not None else _env_int('PLAYBACK_DEVICE_MAX_FILES', 30)
    keep_ratio = keep_ratio if keep_ratio is not None else _env_float('PLAYBACK_KEEP_RATIO', 0.2)
    keep_ratio = min(1.0, max(0.05, keep_ratio))

    record_dir = get_srs_record_dir()
    device_dir = os.path.join(record_dir, 'live', str(device_id))
    entries = iter_flv_files(device_dir)
    total = len(entries)
    if total <= max_recordings:
        return {'total': total, 'deleted': 0}

    keep_count = max(1, int(total * keep_ratio))
    delete_count = total - keep_count
    result = _delete_oldest_entries(entries, delete_count, reason=f'设备{device_id}数量超限')
    result['total'] = total
    if result['deleted'] > 0:
        logger.info(
            '设备回放录像数量清理: device_id=%s, 总数=%s, 删除=%s, 保留约=%s',
            device_id, total, result['deleted'], keep_count,
        )
    return result


def cleanup_global_recordings(
    max_recordings: Optional[int] = None,
    keep_ratio: Optional[float] = None,
) -> Dict[str, int]:
    """清理整个 playbacks 目录下超出全局数量上限的最旧录像。"""
    if not is_cleanup_enabled():
        return {'skipped': 1}

    max_recordings = max_recordings if max_recordings is not None else _env_int('PLAYBACK_GLOBAL_MAX_FILES', 2000)
    keep_ratio = keep_ratio if keep_ratio is not None else _env_float('PLAYBACK_KEEP_RATIO', 0.2)
    keep_ratio = min(1.0, max(0.05, keep_ratio))

    entries = iter_flv_files(get_srs_record_dir())
    total = len(entries)
    if total <= max_recordings:
        return {'total': total, 'deleted': 0}

    keep_count = max(1, int(total * keep_ratio))
    delete_count = total - keep_count
    result = _delete_oldest_entries(entries, delete_count, reason='全局数量超限')
    result['total'] = total
    if result['deleted'] > 0:
        logger.info(
            '全局回放录像数量清理: 总数=%s, 删除=%s, 保留约=%s',
            total, result['deleted'], keep_count,
        )
    return result


def cleanup_expired_files(max_age_hours: Optional[int] = None) -> Dict[str, int]:
    """按文件年龄删除过期本地录像（含上传失败产生的孤儿文件）。"""
    if not is_cleanup_enabled():
        return {'skipped': 1}

    max_age_hours = max_age_hours if max_age_hours is not None else _env_int('PLAYBACK_MAX_AGE_HOURS', 1)
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
    """定时任务入口：综合执行各项清理策略。"""
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

    stats['devices'] = cleanup_all_devices_expired_recordings()
    stats['expired'] = cleanup_expired_files()
    stats['global'] = cleanup_global_recordings()

    if disk_pct >= warn_pct:
        stats['emergency'] = emergency_free_disk()
    else:
        stats['emergency'] = {'skipped': 1, 'disk_percent': disk_pct}

    logger.info(
        '回放磁盘守护完成: dir=%s, 磁盘=%.1f%%, devices=%s, expired=%s, global=%s, emergency=%s',
        record_dir, disk_pct, stats.get('devices'), stats.get('expired'), stats.get('global'), stats.get('emergency'),
    )
    return stats
