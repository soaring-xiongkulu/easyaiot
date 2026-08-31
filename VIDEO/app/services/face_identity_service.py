"""电子身份解析：不知道现实姓名，也能跨摄像头形成稳定身份与轨迹。"""
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import cv2
import numpy as np

from models import Device, FaceIdentity, FaceIdentitySample, FaceMatchRecord, FacePerson, db


def _normalized(value) -> np.ndarray:
    vector = np.asarray(value, dtype=np.float32).flatten()
    norm = float(np.linalg.norm(vector))
    if norm <= 0:
        raise ValueError('人脸特征向量无效')
    return vector / norm


def _new_code(now: datetime) -> str:
    return f'EID-{now:%Y%m%d}-{uuid.uuid4().hex[:8].upper()}'


def _load_embedding(image_path: str) -> np.ndarray:
    image = cv2.imread(str(image_path or ''))
    if image is None:
        raise ValueError('电子身份解析无法读取人脸图片')
    from app.services.face_recognition_service import get_face_recognition_service
    service = get_face_recognition_service()
    info = service.extract_and_crop_largest_face(
        image, allow_full_frame_fallback=False, enforce_quality=False,
    )
    if info:
        return _normalized(info['embedding'])
    height, width = image.shape[:2]
    # 算法链路的人脸图通常已经按关键点对齐为小尺寸正方形；这种输入无需再次检测。
    # 仅允许小图，杜绝把历史整帧/桌面误检当作人脸直接提特征。
    ratio = width / max(height, 1)
    if max(width, height) <= 256 and 0.75 <= ratio <= 1.33:
        return _normalized(service._resolve_embedding(image))
    raise ValueError('SCRFD 未在图片中检测到有效人脸')


def _best_identity(vector: np.ndarray):
    best_identity = None
    best_similarity = -1.0
    rows = (
        db.session.query(FaceIdentitySample, FaceIdentity)
        .join(FaceIdentity, FaceIdentity.id == FaceIdentitySample.identity_id)
        .filter(FaceIdentity.status.in_(['anonymous', 'confirmed']))
        .order_by(FaceIdentitySample.id.desc())
        .limit(max(100, int(os.getenv('FACE_IDENTITY_SEARCH_SAMPLE_LIMIT', '10000'))))
        .all()
    )
    for sample, identity in rows:
        try:
            candidate = _normalized(json.loads(sample.embedding))
        except Exception:
            continue
        if candidate.shape != vector.shape:
            continue
        similarity = float(np.dot(vector, candidate))
        if similarity > best_similarity:
            best_identity, best_similarity = identity, similarity
    return best_identity, best_similarity


def _append_sample(identity: FaceIdentity, vector: np.ndarray, image_path: Optional[str],
                   device_id: Optional[str], quality_score: Optional[float]) -> None:
    max_samples = max(1, int(os.getenv('FACE_IDENTITY_MAX_SAMPLES', '8')))
    if FaceIdentitySample.query.filter_by(identity_id=identity.id).count() >= max_samples:
        return
    db.session.add(FaceIdentitySample(
        identity_id=identity.id,
        embedding=json.dumps(vector.tolist(), separators=(',', ':')),
        image_path=image_path,
        device_id=str(device_id) if device_id else None,
        quality_score=quality_score,
    ))


def resolve_identity(*, embedding=None, image_path: Optional[str] = None,
                     device_id: Optional[str] = None, seen_at: Optional[datetime] = None,
                     quality_score: Optional[float] = None,
                     formal_person_id: Optional[int] = None) -> Dict[str, Any]:
    """解析或创建电子身份。调用方负责最终 commit，以便与轨迹记录原子落库。"""
    now = seen_at or datetime.utcnow()
    vector = _normalized(embedding) if embedding is not None else _load_embedding(image_path or '')

    identity = None
    similarity = None
    resolution = 'new'
    if formal_person_id:
        identity = FaceIdentity.query.filter_by(person_id=int(formal_person_id)).filter(
            FaceIdentity.status != 'merged',
        ).first()
        resolution = 'confirmed'
    if identity is None:
        candidate, best_similarity = _best_identity(vector)
        threshold = float(os.getenv('FACE_IDENTITY_SIMILARITY_THRESHOLD', '0.45'))
        if candidate is not None and str(device_id or '') in {
            str(candidate.first_device_id or ''), str(candidate.last_device_id or ''),
        }:
            threshold = float(os.getenv('FACE_IDENTITY_SAME_CAMERA_THRESHOLD', '0.35'))
        if candidate is not None and best_similarity >= threshold:
            identity, similarity, resolution = candidate, best_similarity, 'matched'

    created = identity is None
    suppressed = False
    if not created and device_id:
        dedup_start = now - timedelta(seconds=max(
            1, int(os.getenv('FACE_IDENTITY_TRAJECTORY_DEDUP_SECONDS', '10')),
        ))
        suppressed = FaceMatchRecord.query.filter(
            FaceMatchRecord.identity_id == identity.id,
            FaceMatchRecord.device_id == str(device_id),
            FaceMatchRecord.created_at >= dedup_start,
        ).first() is not None
    if created:
        person = FacePerson.query.get(int(formal_person_id)) if formal_person_id else None
        code = _new_code(now)
        identity = FaceIdentity(
            identity_code=code,
            display_name=(person.person_name if person else f'未知人员-{code[-8:]}'),
            real_name=person.person_name if person else None,
            status='confirmed' if person else 'anonymous',
            person_id=person.id if person else None,
            cover_image_path=image_path,
            first_seen_at=now, last_seen_at=now,
            first_device_id=str(device_id) if device_id else None,
            last_device_id=str(device_id) if device_id else None,
            occurrence_count=1,
        )
        db.session.add(identity)
        db.session.flush()
        _append_sample(identity, vector, image_path, device_id, quality_score)
    elif not suppressed:
        identity.last_seen_at = now
        identity.last_device_id = str(device_id) if device_id else identity.last_device_id
        identity.occurrence_count = int(identity.occurrence_count or 0) + 1
        # 差异足够大的清晰样本可增强侧脸/光照覆盖，过近重复不保存。
        if similarity is not None and similarity < float(os.getenv('FACE_IDENTITY_SAMPLE_ADD_THRESHOLD', '0.72')):
            _append_sample(identity, vector, image_path, device_id, quality_score)
        if image_path and not identity.cover_image_path:
            identity.cover_image_path = image_path
    return {
        'identity': identity, 'created': created,
        'similarity': similarity, 'resolution': resolution,
        'trajectory_suppressed': suppressed,
    }


def apply_to_record(record: FaceMatchRecord, result: Dict[str, Any]) -> None:
    identity = result['identity']
    record.identity_id = identity.id
    record.identity_code = identity.identity_code
    record.identity_name = identity.display_name
    record.identity_similarity = result.get('similarity')
    record.identity_resolution = result.get('resolution')


def list_identities(*, page=1, page_size=20, status=None, search=None) -> Dict[str, Any]:
    query = FaceIdentity.query.filter(FaceIdentity.status != 'merged')
    if status:
        query = query.filter(FaceIdentity.status == status)
    if search:
        keyword = f'%{str(search).strip()}%'
        query = query.filter(db.or_(
            FaceIdentity.identity_code.ilike(keyword), FaceIdentity.display_name.ilike(keyword),
            FaceIdentity.real_name.ilike(keyword), FaceIdentity.remark.ilike(keyword),
        ))
    total = query.count()
    rows = query.order_by(FaceIdentity.last_seen_at.desc()).offset(
        max(0, (int(page) - 1) * int(page_size)),
    ).limit(max(1, min(int(page_size), 200))).all()
    return {'list': [row.to_dict() for row in rows], 'total': total}


def update_identity(identity_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    identity = FaceIdentity.query.get_or_404(identity_id)
    for field in ('display_name', 'real_name', 'remark'):
        if field in payload:
            setattr(identity, field, str(payload[field]).strip() or None)
    if payload.get('person_id') is not None:
        person = FacePerson.query.get_or_404(int(payload['person_id']))
        identity.person_id = person.id
        identity.real_name = identity.real_name or person.person_name
        identity.display_name = identity.real_name or person.person_name
        identity.status = 'confirmed'
    if payload.get('status') in ('anonymous', 'confirmed', 'disabled'):
        identity.status = payload['status']
    identity.updated_at = datetime.utcnow()
    db.session.commit()
    return identity.to_dict()


def merge_identities(target_id: int, source_ids) -> Dict[str, Any]:
    target = FaceIdentity.query.get_or_404(int(target_id))
    sources = FaceIdentity.query.filter(FaceIdentity.id.in_([int(x) for x in source_ids])).all()
    merged = 0
    for source in sources:
        if source.id == target.id or source.status == 'merged':
            continue
        FaceIdentitySample.query.filter_by(identity_id=source.id).update({'identity_id': target.id})
        FaceMatchRecord.query.filter_by(identity_id=source.id).update({
            'identity_id': target.id,
            'identity_code': target.identity_code,
            'identity_name': target.display_name,
        })
        target.occurrence_count = int(target.occurrence_count or 0) + int(source.occurrence_count or 0)
        if source.first_seen_at and (not target.first_seen_at or source.first_seen_at < target.first_seen_at):
            target.first_seen_at = source.first_seen_at
            target.first_device_id = source.first_device_id
        if source.last_seen_at and (not target.last_seen_at or source.last_seen_at > target.last_seen_at):
            target.last_seen_at = source.last_seen_at
            target.last_device_id = source.last_device_id
        source.status = 'merged'
        source.merged_into_id = target.id
        merged += 1
    db.session.commit()
    return {'target': target.to_dict(), 'merged_count': merged}


def identity_trajectory(identity_id: int, *, date: Optional[str] = None, limit=500) -> Dict[str, Any]:
    identity = FaceIdentity.query.get_or_404(int(identity_id))
    query = FaceMatchRecord.query.filter(FaceMatchRecord.identity_id == identity.id)
    if date:
        local_start = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=timezone(timedelta(hours=8)))
        start = (local_start - timedelta(hours=8)).replace(tzinfo=None)
        query = query.filter(FaceMatchRecord.created_at >= start,
                             FaceMatchRecord.created_at < start + timedelta(days=1))
    records = query.order_by(FaceMatchRecord.created_at.asc()).limit(max(1, min(int(limit), 2000))).all()
    device_ids = {r.device_id for r in records}
    devices = {d.id: d for d in Device.query.filter(Device.id.in_(device_ids)).all()} if device_ids else {}
    points = []
    for record in records:
        device = devices.get(record.device_id)
        points.append({
            'record_id': record.id, 'time': record.to_dict()['created_at'],
            'device_id': record.device_id, 'device_name': record.device_name,
            'longitude': getattr(device, 'longitude', None),
            'latitude': getattr(device, 'latitude', None),
            'face_image_path': record.face_image_path,
            'similarity': record.identity_similarity,
            'task_id': record.task_id, 'task_name': record.task_name,
        })
    return {'identity': identity.to_dict(), 'points': points, 'total': len(points)}


def backfill_unresolved_records(limit: int = 5000) -> Dict[str, int]:
    """为历史真人抓拍补建电子身份；SCRFD 无法确认的旧误检保持未解析。"""
    rows = FaceMatchRecord.query.filter(
        FaceMatchRecord.identity_id.is_(None),
        FaceMatchRecord.face_image_path.isnot(None),
        FaceMatchRecord.status == 'success',
    ).order_by(FaceMatchRecord.id.asc()).limit(max(1, min(int(limit), 20000))).all()
    resolved = skipped = failed = 0
    for record in rows:
        try:
            result = resolve_identity(
                image_path=record.face_image_path, device_id=record.device_id,
                seen_at=record.created_at,
            )
            if result.get('trajectory_suppressed'):
                record.enroll_status = 'tracked'
            elif not result.get('created') and record.enroll_status == 'pending':
                record.enroll_status = 'tracked'
            apply_to_record(record, result)
            db.session.commit()
            resolved += 1
        except ValueError:
            db.session.rollback()
            skipped += 1
        except Exception:
            db.session.rollback()
            failed += 1
    return {'resolved': resolved, 'skipped': skipped, 'failed': failed}
