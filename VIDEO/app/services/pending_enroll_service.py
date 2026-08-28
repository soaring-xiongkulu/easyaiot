"""待入库工作台：未匹配人脸/车牌目标的暂存、标注修正与确认入库。

数据源是匹配记录表中 matched=False 的记录（逻辑内置暂存库，与正式人脸库/
车牌库隔离）：
- 人脸线：基于修正后的标注框从整帧重新裁剪 → 提取特征向量 → 写入人脸库；
- 车牌线：基于修正后的标注框重新裁剪 → 人工确认/修正 OCR 车牌号 → 写入车牌库。
两条业务线相互独立，可分别批量处理。
"""
import io
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import cv2
import numpy as np

from models import FaceLibrary, FaceMatchRecord, FacePerson, PlateLibrary, PlateMatchRecord, db

logger = logging.getLogger(__name__)

KIND_FACE = 'face'
KIND_PLATE = 'plate'

ENROLL_STATUS_PENDING = 'pending'
ENROLL_STATUS_ENROLLED = 'enrolled'
ENROLL_STATUS_DISCARDED = 'discarded'
ENROLL_STATUSES = (ENROLL_STATUS_PENDING, ENROLL_STATUS_ENROLLED, ENROLL_STATUS_DISCARDED)

# 待处理记录的整帧保留时长：过期后仅保留裁剪图（仍可入库，但无法再修正标注框）
FRAME_TTL_DAYS = int(os.getenv('PENDING_FRAME_TTL_DAYS', '7'))
_FRAME_CLEANUP_INTERVAL_SECONDS = 3600
_cleanup_state: Dict[str, datetime] = {}


class PendingEnrollError(ValueError):
    """工作台业务错误（直接透传给前端展示）"""


def _record_model(kind: str):
    if kind == KIND_FACE:
        return FaceMatchRecord
    if kind == KIND_PLATE:
        return PlateMatchRecord
    raise PendingEnrollError(f'未知的工作台类型: {kind}')


def _crop_field(kind: str) -> str:
    return 'face_image_path' if kind == KIND_FACE else 'plate_image_path'


def _normalize_bbox(bbox) -> Optional[List[int]]:
    if not bbox:
        return None
    try:
        values = [int(round(float(v))) for v in list(bbox)[:4]]
    except (TypeError, ValueError):
        return None
    if len(values) < 4 or values[2] <= values[0] or values[3] <= values[1]:
        return None
    return values


def _clamp_bbox(bbox: List[int], width: int, height: int) -> Optional[List[int]]:
    x1, y1, x2, y2 = bbox
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(width, x2), min(height, y2)
    if x2 <= x1 or y2 <= y1:
        return None
    return [x1, y1, x2, y2]


def _local_media_url(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    return f'/video/alert/image?path={quote(path, safe="")}'


def _read_image(path: Optional[str]):
    if not path or not os.path.isfile(path):
        return None
    image = cv2.imread(path)
    return image


def _crop_bytes_from_record(
    kind: str,
    record,
    bbox: Optional[List[int]] = None,
) -> Tuple[Optional[bytes], str]:
    """获取入库用的目标区域 JPEG。

    优先级：整帧 + 标注框重裁 > 修正框落在裁剪图内重裁 > 原始裁剪图。
    返回 (jpeg_bytes, 来源说明)。
    """
    crop_path = getattr(record, _crop_field(kind), None)

    frame_image = _read_image(record.frame_image_path)
    if frame_image is not None:
        fh, fw = frame_image.shape[:2]
        frame_crop = None
        if bbox is not None:
            clamped = _clamp_bbox(bbox, fw, fh)
            if clamped:
                x1, y1, x2, y2 = clamped
                frame_crop = frame_image[y1:y2, x1:x2]
        if frame_crop is not None and frame_crop.size > 0:
            ok, buf = cv2.imencode('.jpg', frame_crop)
            if ok:
                return buf.tobytes(), 'frame'

    # 无整帧时前端会直接在裁剪图上标注（坐标即裁剪图像素空间），
    # 此处按 1:1 应用修正框；有整帧时坐标为帧空间，需要换算到裁剪图。
    crop_image = _read_image(crop_path)
    if crop_image is not None:
        ch, cw = crop_image.shape[:2]
        if bbox is not None:
            if frame_image is not None:
                scale_x, scale_y = cw / max(fw, 1), ch / max(fh, 1)
            else:
                scale_x = scale_y = 1.0
            scaled = [
                int(bbox[0] * scale_x),
                int(bbox[1] * scale_y),
                int(bbox[2] * scale_x),
                int(bbox[3] * scale_y),
            ]
            clamped = _clamp_bbox(scaled, cw, ch)
            if clamped:
                x1, y1, x2, y2 = clamped
                region = crop_image[y1:y2, x1:x2]
                if region.size > 0:
                    ok, buf = cv2.imencode('.jpg', region)
                    if ok:
                        return buf.tobytes(), 'crop-region'
        ok, buf = cv2.imencode('.jpg', crop_image)
        if ok:
            return buf.tobytes(), 'crop'

    return None, 'missing'


def _record_payload(kind: str, record, *, include_frame_size: bool = False) -> Dict[str, Any]:
    data = record.to_dict()
    crop_path = getattr(record, _crop_field(kind), None)
    data['crop_image_url'] = _local_media_url(crop_path)
    frame_path = record.frame_image_path
    frame_available = bool(frame_path) and os.path.isfile(frame_path)
    data['frame_available'] = frame_available
    data['frame_image_url'] = _local_media_url(frame_path) if frame_available else None
    if include_frame_size and frame_available:
        image = _read_image(frame_path)
        if image is not None:
            fh, fw = image.shape[:2]
            data['frame_width'] = fw
            data['frame_height'] = fh
    return data


def get_stats(kind: str) -> Dict[str, int]:
    model = _record_model(kind)
    base = model.query.filter(model.matched.is_(False))
    return {
        'pending': base.filter(model.enroll_status == ENROLL_STATUS_PENDING).count(),
        'enrolled': base.filter(model.enroll_status == ENROLL_STATUS_ENROLLED).count(),
        'discarded': base.filter(model.enroll_status == ENROLL_STATUS_DISCARDED).count(),
    }


def list_records(
    kind: str,
    *,
    status: str = ENROLL_STATUS_PENDING,
    page: int = 1,
    page_size: int = 24,
    search: Optional[str] = None,
    device_id: Optional[str] = None,
    task_id: Optional[int] = None,
) -> Dict[str, Any]:
    _maybe_cleanup_expired_frames(kind)
    model = _record_model(kind)
    query = model.query.filter(model.matched.is_(False))
    if status and status != 'all':
        if status not in ENROLL_STATUSES:
            raise PendingEnrollError(f'无效的入库状态: {status}')
        query = query.filter(model.enroll_status == status)
    if device_id:
        query = query.filter(model.device_id == str(device_id))
    if task_id:
        query = query.filter(model.task_id == int(task_id))
    if search:
        kw = f'%{search.strip()}%'
        conditions = [model.device_name.ilike(kw), model.task_name.ilike(kw)]
        if kind == KIND_PLATE:
            conditions.append(model.plate_no.ilike(kw))
        query = query.filter(db.or_(*conditions))
    total = query.count()
    rows = (
        query.order_by(model.id.desc())
        .offset(max(0, (page - 1) * page_size))
        .limit(max(1, min(page_size, 200)))
        .all()
    )
    return {
        'list': [_record_payload(kind, r) for r in rows],
        'total': total,
        'page': page,
        'page_size': page_size,
        'stats': get_stats(kind),
    }


def get_record_detail(kind: str, record_id: int) -> Dict[str, Any]:
    record = _record_model(kind).query.get_or_404(int(record_id))
    return _record_payload(kind, record, include_frame_size=True)


def discard_records(kind: str, record_ids: List[int]) -> int:
    """批量忽略：不希望入库的目标移出待处理列表（保留记录历史，可恢复）"""
    if not record_ids:
        return 0
    rows = (
        _record_model(kind).query.filter(
            _record_model(kind).id.in_([int(x) for x in record_ids]),
        ).all()
    )
    changed = 0
    for record in rows:
        if record.enroll_status == ENROLL_STATUS_ENROLLED:
            continue  # 已入库记录不可忽略
        record.enroll_status = ENROLL_STATUS_DISCARDED
        _delete_frame(record)
        changed += 1
    db.session.commit()
    return changed


def restore_records(kind: str, record_ids: List[int]) -> int:
    """批量恢复：将已忽略记录重新放回待处理"""
    if not record_ids:
        return 0
    rows = (
        _record_model(kind).query.filter(
            _record_model(kind).id.in_([int(x) for x in record_ids]),
            _record_model(kind).enroll_status == ENROLL_STATUS_DISCARDED,
        ).all()
    )
    for record in rows:
        record.enroll_status = ENROLL_STATUS_PENDING
    db.session.commit()
    return len(rows)


def delete_records(kind: str, record_ids: List[int]) -> int:
    """批量删除：物理删除未匹配记录及其整帧（裁剪图保留供匹配历史追溯）"""
    if not record_ids:
        return 0
    rows = (
        _record_model(kind).query.filter(
            _record_model(kind).id.in_([int(x) for x in record_ids]),
        ).all()
    )
    for record in rows:
        _delete_frame(record, clear_path=False)
        db.session.delete(record)
    db.session.commit()
    return len(rows)


def _delete_frame(record, *, clear_path: bool = True) -> None:
    frame_path = record.frame_image_path
    if frame_path and os.path.isfile(frame_path):
        try:
            os.remove(frame_path)
        except OSError as exc:
            logger.warning('删除整帧失败: %s (%s)', frame_path, exc)
    if clear_path:
        record.frame_image_path = None


def extract_preview_bytes(
    kind: str,
    record_id: int,
    bbox: Optional[List[int]] = None,
) -> Tuple[bytes, Dict[str, Any]]:
    """按（修正后的）标注框从整帧裁剪提取区域，返回 JPEG 预览及说明。"""
    record = _record_model(kind).query.get_or_404(int(record_id))
    use_bbox = _normalize_bbox(bbox) or _normalize_bbox(record.bbox)
    crop_bytes, source = _crop_bytes_from_record(kind, record, bbox=use_bbox)
    if not crop_bytes:
        raise PendingEnrollError('整帧与裁剪图均已过期，无法预览提取区域')
    info = {
        'record_id': record.id,
        'source': source,
        'bbox': use_bbox,
    }
    return crop_bytes, info


def enroll_record(kind: str, record_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """确认入库：人脸提取特征向量入库 / 车牌写入车牌条目。"""
    model = _record_model(kind)
    record = model.query.get_or_404(int(record_id))
    if record.enroll_status == ENROLL_STATUS_ENROLLED:
        raise PendingEnrollError('该记录已入库，请勿重复操作')
    if record.enroll_status == ENROLL_STATUS_DISCARDED:
        raise PendingEnrollError('该记录已被忽略，请先恢复再入库')

    if kind == KIND_FACE:
        result = _enroll_face(record, payload)
    else:
        result = _enroll_plate(record, payload)

    record.enroll_status = ENROLL_STATUS_ENROLLED
    record.enroll_target_library_id = result['library_id']
    record.enroll_entry_id = result['entry_id']
    record.enroll_time = datetime.utcnow()
    if kind == KIND_FACE:
        record.enroll_person_id = result.get('person_id')
    _delete_frame(record)
    db.session.commit()
    return {
        'record': _record_payload(kind, record),
        'entry': result,
    }


def _enroll_face(record: FaceMatchRecord, payload: Dict[str, Any]) -> Dict[str, Any]:
    from app.services import face_library_service

    library_id = payload.get('library_id') or payload.get('libraryId')
    if not library_id:
        raise PendingEnrollError('请选择目标人脸库')
    if not FaceLibrary.query.get(int(library_id)):
        raise PendingEnrollError('目标人脸库不存在或已删除')
    person_id = payload.get('person_id') or payload.get('personId')
    person_name = (payload.get('person_name') or payload.get('personName') or '').strip()
    if not person_id and not person_name:
        raise PendingEnrollError('请填写人员姓名或选择已有人员')
    if person_id and not person_name:
        # 追加到已有人员时允许省略姓名，取人员当前姓名
        person = FacePerson.query.get(int(person_id))
        if not person:
            raise PendingEnrollError('所选人员不存在')
        person_name = person.person_name

    bbox = _normalize_bbox(payload.get('bbox'))
    image_bytes, source = _crop_bytes_from_record(KIND_FACE, record, bbox=bbox)
    if not image_bytes:
        raise PendingEnrollError('整帧与裁剪图均已过期，无法提取人脸特征')

    entry = face_library_service.add_entry(
        library_id=int(library_id),
        person_name=person_name or '',
        image_bytes=image_bytes,
        person_code=(payload.get('person_code') or payload.get('personCode') or '').strip() or None,
        remark=(payload.get('remark') or '').strip() or None,
        person_id=int(person_id) if person_id else None,
        is_enabled=bool(payload.get('is_enabled', True)),
    )
    logger.info(
        '待入库工作台人脸入库: record=%s entry=%s person=%s source=%s',
        record.id, entry.id, entry.person_id, source,
    )
    return {
        'library_id': int(library_id),
        'entry_id': entry.id,
        'person_id': entry.person_id,
        'person_name': entry.person_name,
        'crop_source': source,
    }


def _enroll_plate(record: PlateMatchRecord, payload: Dict[str, Any]) -> Dict[str, Any]:
    from app.services import plate_library_service

    library_id = payload.get('library_id') or payload.get('libraryId')
    if not library_id:
        raise PendingEnrollError('请选择目标车牌库')
    if not PlateLibrary.query.get(int(library_id)):
        raise PendingEnrollError('目标车牌库不存在或已删除')
    plate_no = plate_library_service._normalize_plate_no(
        payload.get('plate_no') or payload.get('plateNo') or record.plate_no or ''
    )
    if not plate_no:
        raise PendingEnrollError('车牌号不能为空')

    bbox = _normalize_bbox(payload.get('bbox') or payload.get('rect'))
    image_bytes, source = _crop_bytes_from_record(KIND_PLATE, record, bbox=bbox)

    entry = plate_library_service.add_entry(
        library_id=int(library_id),
        plate_no=plate_no,
        plate_color=(payload.get('plate_color') or payload.get('plateColor') or record.plate_color or '').strip() or None,
        owner_name=(payload.get('owner_name') or payload.get('ownerName') or '').strip() or None,
        owner_phone=(payload.get('owner_phone') or payload.get('ownerPhone') or '').strip() or None,
        remark=(payload.get('remark') or '').strip() or None,
        image_bytes=image_bytes,
        is_enabled=bool(payload.get('is_enabled', True)),
    )
    logger.info(
        '待入库工作台车牌入库: record=%s entry=%s plate=%s source=%s',
        record.id, entry.id, entry.plate_no, source,
    )
    return {
        'library_id': int(library_id),
        'entry_id': entry.id,
        'plate_no': entry.plate_no,
        'crop_source': source,
    }


def batch_enroll_records(kind: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """批量确认入库：逐条处理并汇总成功/失败，单条失败不影响其余。"""
    if not items:
        raise PendingEnrollError('batch items 不能为空')
    success: List[Dict[str, Any]] = []
    failed: List[Dict[str, Any]] = []
    for index, item in enumerate(items):
        record_id = item.get('record_id') or item.get('recordId')
        try:
            if not record_id:
                raise PendingEnrollError('record_id 不能为空')
            result = enroll_record(kind, int(record_id), item)
            success.append({'record_id': int(record_id), **result})
        except Exception as exc:
            logger.warning('批量入库第 %s 条失败: %s', index, exc)
            failed.append({'record_id': record_id, 'msg': str(exc)})
    return {
        'success_count': len(success),
        'failed_count': len(failed),
        'success': success,
        'failed': failed,
    }


def _maybe_cleanup_expired_frames(kind: str) -> None:
    """低频清理：超过 TTL 的待处理记录整帧落盘删除（保留裁剪图可继续入库）。"""
    now = datetime.utcnow()
    last = _cleanup_state.get(kind)
    if last is not None and (now - last).total_seconds() < _FRAME_CLEANUP_INTERVAL_SECONDS:
        return
    _cleanup_state[kind] = now
    try:
        model = _record_model(kind)
        threshold = now - timedelta(days=max(1, FRAME_TTL_DAYS))
        rows = (
            model.query.filter(
                model.matched.is_(False),
                model.enroll_status == ENROLL_STATUS_PENDING,
                model.frame_image_path.isnot(None),
                model.created_at < threshold,
            ).all()
        )
        for record in rows:
            _delete_frame(record)
        if rows:
            db.session.commit()
            logger.info('待入库工作台清理过期整帧 %s 条 (%s)', len(rows), kind)
    except Exception as exc:
        logger.warning('待入库工作台整帧清理失败 (%s): %s', kind, exc)
        db.session.rollback()
