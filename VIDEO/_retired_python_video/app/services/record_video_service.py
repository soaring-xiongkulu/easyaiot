"""
监控录像管理服务
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import io
import logging
import os
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from flask import current_app
from minio.error import S3Error
from sqlalchemy import func

from models import db, RecordSpace, RecordFile, Alert
from app.services.alert_service import _alert_to_dict
from app.services.record_space_service import get_minio_client
from app.utils.service_urls import minio_storage_enabled
from app.services.space_file_metadata_service import (
    delete_record_files_metadata,
    sync_record_files_from_minio,
    extract_prefix_from_url,
)

logger = logging.getLogger(__name__)


def list_record_videos(
    space_id: int,
    device_id: Optional[str] = None,
    page_no: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> Dict:
    """获取监控录像列表（数据库分页）"""
    try:
        record_space = RecordSpace.query.get_or_404(space_id)
        query = RecordFile.query.filter_by(space_id=space_id)

        effective_device_id = device_id or record_space.device_id
        if effective_device_id:
            query = query.filter(RecordFile.device_id == effective_device_id)

        if search:
            query = query.filter(RecordFile.filename.ilike(f'%{search}%'))
        if start_time:
            query = query.filter(RecordFile.event_time >= start_time)
        if end_time:
            query = query.filter(RecordFile.event_time <= end_time)

        query = query.order_by(RecordFile.event_time.desc())
        pagination = query.paginate(page=page_no, per_page=page_size, error_out=False)

        return {
            'items': [item.to_list_item() for item in pagination.items],
            'total': pagination.total,
            'page_no': page_no,
            'page_size': page_size,
        }
    except Exception as e:
        logger.error(f"获取监控录像列表失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取监控录像列表失败: {str(e)}")


def delete_record_videos(space_id: int, object_names: List[str]) -> Dict:
    """批量删除监控录像（MinIO/本地 + 数据库）"""
    try:
        record_space = RecordSpace.query.get_or_404(space_id)
        bucket_name = record_space.bucket_name

        deleted_count = 0
        failed_count = 0
        failed_objects = []

        if not minio_storage_enabled():
            for object_name in object_names:
                record = RecordFile.query.filter_by(
                    space_id=space_id,
                    object_name=object_name,
                ).first()
                local_path = (record.url if record and record.url else '').strip()
                if local_path.startswith('/video/'):
                    local_path = ''
                if not local_path:
                    from app.services.media_dvr_utils import resolve_playback_absolute_path
                    from app.services.playback_disk_guard_service import get_srs_record_dir
                    local_path = resolve_playback_absolute_path(
                        os.path.join(get_srs_record_dir(), object_name.replace('/', os.sep)),
                    )
                try:
                    if local_path and os.path.isfile(local_path):
                        os.remove(local_path)
                    deleted_count += 1
                    logger.info('mini 形态删除监控录像: %s', local_path)
                except OSError as e:
                    failed_count += 1
                    failed_objects.append(object_name)
                    logger.warning('mini 形态删除监控录像失败: %s error=%s', local_path, e)
        else:
            minio_client = get_minio_client()
            if not minio_client.bucket_exists(bucket_name):
                raise ValueError(f"监控录像空间的MinIO bucket不存在: {bucket_name}")

            for object_name in object_names:
                try:
                    minio_client.remove_object(bucket_name, object_name)
                    thumb_name = object_name.rsplit('.', 1)[0] + '.jpg'
                    try:
                        minio_client.remove_object(bucket_name, thumb_name)
                    except Exception:
                        pass
                    deleted_count += 1
                    logger.info(f"删除监控录像成功: {bucket_name}/{object_name}")
                except Exception as e:
                    failed_count += 1
                    failed_objects.append(object_name)
                    logger.warning(f"删除监控录像失败: {bucket_name}/{object_name}, error={str(e)}")

        success_objects = [n for n in object_names if n not in failed_objects]
        delete_record_files_metadata(bucket_name, success_objects)

        return {
            'deleted_count': deleted_count,
            'failed_count': failed_count,
            'failed_objects': failed_objects,
        }
    except Exception as e:
        logger.error(f"批量删除监控录像失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"批量删除监控录像失败: {str(e)}")


def get_record_video(space_id: int, object_name: str):
    """获取监控录像内容"""
    import mimetypes
    import os

    try:
        record_space = RecordSpace.query.get_or_404(space_id)
        bucket_name = record_space.bucket_name

        if not minio_storage_enabled():
            record = RecordFile.query.filter_by(
                space_id=space_id,
                object_name=object_name,
            ).first()
            local_path = (record.url if record and record.url else '').strip()
            if local_path.startswith('/video/'):
                local_path = ''
            if not local_path or not os.path.isfile(local_path):
                from app.services.media_dvr_utils import resolve_playback_absolute_path
                from app.services.playback_disk_guard_service import get_srs_record_dir
                local_path = resolve_playback_absolute_path(
                    os.path.join(get_srs_record_dir(), object_name.replace('/', os.sep)),
                )
            if not os.path.isfile(local_path):
                raise ValueError(f"录像不存在: {object_name}")
            with open(local_path, 'rb') as handle:
                content = handle.read()
            filename = object_name.split('/')[-1]
            ext = os.path.splitext(filename)[1].lower()
            content_type_map = {
                '.mp4': 'video/mp4', '.flv': 'video/x-flv', '.avi': 'video/x-msvideo',
                '.mov': 'video/quicktime', '.mkv': 'video/x-matroska', '.ts': 'video/mp2t',
            }
            guessed, _ = mimetypes.guess_type(filename)
            return content, content_type_map.get(ext) or guessed or 'video/mp4', filename

        minio_client = get_minio_client()
        if not minio_client.bucket_exists(bucket_name):
            raise ValueError(f"监控录像空间的MinIO bucket不存在: {bucket_name}")

        try:
            stat = minio_client.stat_object(bucket_name, object_name)
            data = minio_client.get_object(bucket_name, object_name)
            content = data.read()
            data.close()
            data.release_conn()
            return content, stat.content_type or 'video/mp4', object_name.split('/')[-1]
        except S3Error as e:
            if e.code == 'NoSuchKey':
                raise ValueError(f"录像不存在: {object_name}")
            raise
    except Exception as e:
        logger.error(f"获取监控录像失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取监控录像失败: {str(e)}")


def cleanup_orphan_minio_record_objects(space_id: int, save_time_hours: int) -> Dict:
    """清理 MinIO 中无 record_file 元数据且已过期的录像/缩略图（孤儿对象）。"""
    from app.services.media_dvr_utils import parse_record_minio_object_event_time
    from app.services.space_save_time_service import save_time_cutoff_naive

    if not minio_storage_enabled():
        return {'scanned_count': 0, 'deleted_count': 0, 'error_count': 0, 'skipped': 1}

    cutoff_time = save_time_cutoff_naive(save_time_hours)
    if cutoff_time is None:
        return {'scanned_count': 0, 'deleted_count': 0, 'error_count': 0, 'skipped': 1}

    record_space = RecordSpace.query.get_or_404(space_id)
    bucket_name = record_space.bucket_name
    device_id = record_space.device_id

    minio_client = get_minio_client()
    if not minio_client.bucket_exists(bucket_name):
        return {'scanned_count': 0, 'deleted_count': 0, 'error_count': 0}

    prefix = f'{device_id}/' if device_id else ''

    db_query = RecordFile.query.filter_by(space_id=space_id, bucket_name=bucket_name)
    if device_id:
        db_query = db_query.filter_by(device_id=device_id)
    known_objects = set()
    for record in db_query.all():
        known_objects.add(record.object_name)
        if record.thumbnail_url:
            thumb = extract_prefix_from_url(record.thumbnail_url)
            if thumb:
                known_objects.add(thumb)

    scanned_count = deleted_count = error_count = 0
    for obj in minio_client.list_objects(bucket_name, prefix=prefix, recursive=True):
        object_name = obj.object_name
        if not object_name or object_name.endswith('/'):
            continue
        scanned_count += 1
        if object_name in known_objects:
            continue

        event_time = parse_record_minio_object_event_time(object_name, obj.last_modified)
        if event_time is None or event_time >= cutoff_time:
            continue

        try:
            minio_client.remove_object(bucket_name, object_name)
            deleted_count += 1
            logger.info(
                '删除 MinIO 孤儿录像对象: bucket=%s object=%s event_time=%s cutoff=%s',
                bucket_name, object_name, event_time, cutoff_time,
            )
        except Exception as e:
            error_count += 1
            logger.warning(
                '删除 MinIO 孤儿录像对象失败: bucket=%s object=%s error=%s',
                bucket_name, object_name, e,
            )

    if deleted_count > 0:
        logger.info(
            '录像空间 %s 孤儿对象清理: 扫描=%s, 删除=%s, 错误=%s',
            record_space.space_name, scanned_count, deleted_count, error_count,
        )

    return {
        'scanned_count': scanned_count,
        'deleted_count': deleted_count,
        'error_count': error_count,
    }


def cleanup_old_videos_by_save_time(space_id: int, save_time_hours: int) -> Dict:
    """根据保存时长（小时）清理旧的监控录像"""
    try:
        from app.services.space_save_time_service import save_time_cutoff_naive

        record_space = RecordSpace.query.get_or_404(space_id)
        bucket_name = record_space.bucket_name
        save_mode = record_space.save_mode

        cutoff_time = save_time_cutoff_naive(save_time_hours)
        if cutoff_time is None:
            return {
                'processed_count': 0, 'deleted_count': 0, 'archived_count': 0,
                'error_count': 0, 'orphan_deleted_count': 0, 'orphan_scanned_count': 0,
                'orphan_error_count': 0,
            }
        query = RecordFile.query.filter(
            RecordFile.space_id == space_id,
            RecordFile.event_time < cutoff_time,
        )
        if record_space.device_id:
            query = query.filter(RecordFile.device_id == record_space.device_id)

        records = query.all()

        def _merge_orphan(result: Dict) -> Dict:
            orphan_result = cleanup_orphan_minio_record_objects(space_id, save_time_hours)
            result['orphan_deleted_count'] = orphan_result.get('deleted_count', 0)
            result['orphan_scanned_count'] = orphan_result.get('scanned_count', 0)
            result['orphan_error_count'] = orphan_result.get('error_count', 0)
            return result

        minio_client = get_minio_client()
        if not minio_storage_enabled() or not minio_client.bucket_exists(bucket_name):
            return _merge_orphan({
                'processed_count': 0, 'deleted_count': 0, 'archived_count': 0, 'error_count': 0,
            })

        if not records:
            return _merge_orphan({
                'processed_count': 0, 'deleted_count': 0, 'archived_count': 0, 'error_count': 0,
            })

        archive_bucket_name = current_app.config.get('MINIO_ARCHIVE_BUCKET', 'record-archive')
        if save_mode == 1 and not minio_client.bucket_exists(archive_bucket_name):
            minio_client.make_bucket(archive_bucket_name)

        processed_count = deleted_count = archived_count = error_count = 0

        if save_mode == 0:
            object_names = []
            for record in records:
                try:
                    minio_client.remove_object(bucket_name, record.object_name)
                    if record.thumbnail_url:
                        thumb = extract_prefix_from_url(record.thumbnail_url)
                        if thumb:
                            try:
                                minio_client.remove_object(bucket_name, thumb)
                            except Exception:
                                pass
                    object_names.append(record.object_name)
                    deleted_count += 1
                    processed_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"删除录像失败: {record.object_name}, error={e}")
            delete_record_files_metadata(bucket_name, object_names)
        else:
            device_groups: Dict[str, list] = {}
            for record in records:
                device_groups.setdefault(record.device_id, []).append(record)

            for device_id, record_list in device_groups.items():
                try:
                    zip_buffer = io.BytesIO()
                    removed_names = []
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for record in record_list:
                            try:
                                data = minio_client.get_object(bucket_name, record.object_name)
                                file_content = data.read()
                                data.close()
                                data.release_conn()
                                zip_file.writestr(record.filename, file_content)
                                minio_client.remove_object(bucket_name, record.object_name)
                                removed_names.append(record.object_name)
                                deleted_count += 1
                            except Exception as e:
                                error_count += 1
                                logger.error(f"处理录像失败: {record.object_name}, error={e}")

                    if zip_buffer.tell() > 0:
                        zip_buffer.seek(0)
                        archive_object_name = f"{device_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
                        minio_client.put_object(
                            archive_bucket_name,
                            archive_object_name,
                            zip_buffer,
                            length=zip_buffer.tell(),
                            content_type='application/zip',
                        )
                        archived_count += 1
                        processed_count += len(removed_names)
                        delete_record_files_metadata(bucket_name, removed_names)
                except Exception as e:
                    error_count += len(record_list)
                    logger.error(f"归档设备录像失败: device_id={device_id}, error={e}", exc_info=True)

        return _merge_orphan({
            'processed_count': processed_count,
            'deleted_count': deleted_count,
            'archived_count': archived_count,
            'error_count': error_count,
        })
    except Exception as e:
        logger.error(f"清理过期录像失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"清理过期录像失败: {str(e)}")


def sync_record_videos_metadata(space_id: int) -> Dict:
    """从 MinIO 同步录像元数据到数据库"""
    return sync_record_files_from_minio(space_id)


def _parse_day_range(date_str: str):
    """解析 YYYY-MM-DD 为当日起止时间（与 event_time 一致的 naive 本地时间）。"""
    day_start = datetime.strptime(date_str.strip(), '%Y-%m-%d')
    day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)
    return day_start, day_end


def _alert_time_naive(alert_time: datetime) -> datetime:
    from app.utils.service_urls import normalize_to_shanghai_naive

    return normalize_to_shanghai_naive(alert_time)


def _match_alerts_to_segment(
    alerts: List[Alert],
    seg_start: datetime,
    seg_end: datetime,
    record_url: str,
) -> List[dict]:
    """将告警匹配到录像片段（时间窗重叠或 record_path 一致）。"""
    matched = []
    record_url = (record_url or '').strip()
    for alert in alerts:
        alert_naive = _alert_time_naive(alert.time)
        in_window = alert_naive is not None and seg_start <= alert_naive <= seg_end
        same_record = record_url and (alert.record_path or '').strip() == record_url
        if in_window or same_record:
            matched.append(_alert_to_dict(alert))
    return matched


# 相邻片段间隔 <= 该值（秒）则视为同一段连续录像
SESSION_MERGE_GAP_SEC = 2


def _merge_timeline_ranges(timeline: List[dict], gap_sec: int = SESSION_MERGE_GAP_SEC) -> List[dict]:
    """合并时间轴上相邻的录像覆盖区间。"""
    if not timeline:
        return []
    merged: List[dict] = []
    current = {
        'start_offset_sec': timeline[0]['start_offset_sec'],
        'end_offset_sec': timeline[0]['end_offset_sec'],
        'has_recording': True,
        'has_alert': timeline[0].get('has_alert', False),
        'alert_count': timeline[0].get('alert_count', 0),
        'segment_ids': [timeline[0].get('segment_id')],
    }
    for item in timeline[1:]:
        gap = item['start_offset_sec'] - current['end_offset_sec']
        if gap <= gap_sec:
            current['end_offset_sec'] = item['end_offset_sec']
            current['has_alert'] = current['has_alert'] or item.get('has_alert', False)
            current['alert_count'] = current.get('alert_count', 0) + item.get('alert_count', 0)
            current['segment_ids'].append(item.get('segment_id'))
        else:
            merged.append(current)
            current = {
                'start_offset_sec': item['start_offset_sec'],
                'end_offset_sec': item['end_offset_sec'],
                'has_recording': True,
                'has_alert': item.get('has_alert', False),
                'alert_count': item.get('alert_count', 0),
                'segment_ids': [item.get('segment_id')],
            }
    merged.append(current)
    return merged


def _build_session_groups(segments: List[dict], gap_sec: int = SESSION_MERGE_GAP_SEC) -> List[dict]:
    """将相邻片段合并为连续录像会话（供左侧树与会话播放使用）。"""
    if not segments:
        return []
    groups: List[dict] = []
    current: Optional[dict] = None
    for seg in segments:
        if current is None:
            current = {
                'group_id': len(groups),
                'start_time': seg.get('start_time'),
                'end_time': seg.get('end_time'),
                'start_offset_sec': seg.get('start_offset_sec', 0),
                'end_offset_sec': seg.get('end_offset_sec', 0),
                'segment_count': 1,
                'has_alert': seg.get('has_alert', False),
                'alert_count': seg.get('alert_count', 0),
                'segments': [seg],
            }
        else:
            gap = seg.get('start_offset_sec', 0) - current['end_offset_sec']
            if gap <= gap_sec:
                current['end_offset_sec'] = seg.get('end_offset_sec', 0)
                current['end_time'] = seg.get('end_time')
                current['segment_count'] += 1
                current['has_alert'] = current['has_alert'] or seg.get('has_alert', False)
                current['alert_count'] += seg.get('alert_count', 0)
                current['segments'].append(seg)
            else:
                groups.append(current)
                current = {
                    'group_id': len(groups),
                    'start_time': seg.get('start_time'),
                    'end_time': seg.get('end_time'),
                    'start_offset_sec': seg.get('start_offset_sec', 0),
                    'end_offset_sec': seg.get('end_offset_sec', 0),
                    'segment_count': 1,
                    'has_alert': seg.get('has_alert', False),
                    'alert_count': seg.get('alert_count', 0),
                    'segments': [seg],
                }
    if current is not None:
        groups.append(current)
    return groups


def find_segment_for_alert(device_id: str, alert_id: int) -> Optional[dict]:
    """根据告警 ID 定位所属录像片段及空间。"""
    alert = Alert.query.get(alert_id)
    if not alert or alert.device_id != device_id:
        return None

    space = RecordSpace.query.filter_by(device_id=device_id).first()
    if not space:
        return None

    alert_naive = _alert_time_naive(alert.time)
    if not alert_naive:
        return None

    date_str = alert_naive.strftime('%Y-%m-%d')
    day_start, day_end = _parse_day_range(date_str)

    records = (
        RecordFile.query.filter(
            RecordFile.space_id == space.id,
            RecordFile.device_id == device_id,
            RecordFile.event_time >= day_start,
            RecordFile.event_time <= day_end,
        )
        .order_by(RecordFile.event_time.asc())
        .all()
    )

    record_url = (alert.record_path or '').strip()
    matched_seg = None
    for record in records:
        duration = int(record.duration or 30)
        seg_start = record.event_time
        seg_end = seg_start + timedelta(seconds=duration)
        same_record = record_url and (record.url or '').strip() == record_url
        in_window = seg_start <= alert_naive <= seg_end
        if same_record or in_window:
            matched_seg = record
            break

    if not matched_seg:
        return {
            'space_id': space.id,
            'device_id': device_id,
            'date': date_str,
            'alert_id': alert_id,
            'segment': None,
        }

    duration = int(matched_seg.duration or 30)
    seg_start = matched_seg.event_time
    seg_end = seg_start + timedelta(seconds=duration)
    start_offset = max(0, int((seg_start - day_start).total_seconds()))

    return {
        'space_id': space.id,
        'device_id': device_id,
        'date': date_str,
        'alert_id': alert_id,
        'segment': {
            **matched_seg.to_list_item(),
            'start_time': seg_start.isoformat() if seg_start else None,
            'end_time': seg_end.isoformat() if seg_end else None,
            'start_offset_sec': start_offset,
            'end_offset_sec': min(86400, start_offset + duration),
        },
    }


def list_record_video_dates(space_id: int, device_id: Optional[str] = None) -> List[dict]:
    """列出有录像的日期及片段数量。"""
    record_space = RecordSpace.query.get_or_404(space_id)
    effective_device_id = device_id or record_space.device_id

    query = db.session.query(
        func.date(RecordFile.event_time).label('record_date'),
        func.count(RecordFile.id).label('segment_count'),
    ).filter(RecordFile.space_id == space_id)

    if effective_device_id:
        query = query.filter(RecordFile.device_id == effective_device_id)

    rows = (
        query.group_by(func.date(RecordFile.event_time))
        .order_by(func.date(RecordFile.event_time).desc())
        .all()
    )
    return [
        {
            'date': row.record_date.strftime('%Y-%m-%d') if hasattr(row.record_date, 'strftime') else str(row.record_date),
            'segment_count': int(row.segment_count or 0),
        }
        for row in rows
    ]


def list_record_videos_day_detail(
    space_id: int,
    date_str: str,
    device_id: Optional[str] = None,
) -> Dict[str, Any]:
    """获取指定日期的全部录像片段、时间轴覆盖及告警关联。"""
    record_space = RecordSpace.query.get_or_404(space_id)
    effective_device_id = device_id or record_space.device_id
    day_start, day_end = _parse_day_range(date_str)

    query = RecordFile.query.filter(
        RecordFile.space_id == space_id,
        RecordFile.event_time >= day_start,
        RecordFile.event_time <= day_end,
    )
    if effective_device_id:
        query = query.filter(RecordFile.device_id == effective_device_id)

    records = query.order_by(RecordFile.event_time.asc()).all()

    alert_query = Alert.query.filter(
        Alert.time >= day_start,
        Alert.time <= day_end,
    )
    if effective_device_id:
        alert_query = alert_query.filter(Alert.device_id == effective_device_id)
    day_alerts = alert_query.order_by(Alert.time.asc()).all()

    segments: List[dict] = []
    timeline: List[dict] = []
    total_duration = 0
    alert_segment_count = 0

    for record in records:
        duration = int(record.duration or 30)
        seg_start = record.event_time
        seg_end = seg_start + timedelta(seconds=duration)
        matched_alerts = _match_alerts_to_segment(day_alerts, seg_start, seg_end, record.url)
        has_alert = len(matched_alerts) > 0
        if has_alert:
            alert_segment_count += 1
        total_duration += duration

        start_offset = max(0, int((seg_start - day_start).total_seconds()))
        end_offset = min(86400, start_offset + duration)

        segments.append({
            **record.to_list_item(),
            'start_time': seg_start.isoformat() if seg_start else None,
            'end_time': seg_end.isoformat() if seg_end else None,
            'has_alert': has_alert,
            'alert_count': len(matched_alerts),
            'alerts': matched_alerts,
            'start_offset_sec': start_offset,
            'end_offset_sec': end_offset,
        })
        timeline.append({
            'start_offset_sec': start_offset,
            'end_offset_sec': end_offset,
            'has_recording': True,
            'has_alert': has_alert,
            'segment_id': record.id,
            'alert_count': len(matched_alerts),
        })

    timeline_merged = _merge_timeline_ranges(timeline)
    session_groups = _build_session_groups(segments)

    return {
        'date': date_str,
        'device_id': effective_device_id,
        'space_id': space_id,
        'segments': segments,
        'timeline': timeline,
        'timeline_merged': timeline_merged,
        'session_groups': session_groups,
        'total_segments': len(segments),
        'total_sessions': len(session_groups),
        'total_duration_sec': total_duration,
        'alert_segment_count': alert_segment_count,
        'total_alert_count': len(day_alerts),
        'alerts': [_alert_to_dict(a) for a in day_alerts],
    }
