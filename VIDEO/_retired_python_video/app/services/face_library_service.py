"""人脸库业务服务"""
import io
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import quote

import cv2
import numpy as np

from app.services.face_recognition_service import decode_image_bytes, get_face_recognition_service
from app.services.face_vector_store import get_face_vector_store
from app.services.minio_service import ModelService
from models import FaceAutoEnrollTask, FaceEntry, FaceLibrary, FaceMatchRecord, FacePerson, db

logger = logging.getLogger(__name__)

FACE_BUCKET = os.getenv('FACE_IMAGE_BUCKET', 'face-library')


LIBRARY_CODE_LENGTH = 12


def _gen_library_code() -> str:
    """生成 12 位人脸库编码（大写十六进制）"""
    for _ in range(20):
        code = uuid.uuid4().hex[:LIBRARY_CODE_LENGTH].upper()
        if not FaceLibrary.query.filter_by(code=code).first():
            return code
    raise RuntimeError('无法生成唯一的人脸库编码')


def _normalize_business_tags(tags) -> List[str]:
    """业务标签仅按英文逗号拆分"""
    if tags is None:
        return []
    if isinstance(tags, str):
        items = [tags]
    elif isinstance(tags, list):
        items = tags
    else:
        return []
    result: List[str] = []
    for item in items:
        text = str(item).strip()
        if not text:
            continue
        for part in text.split(','):
            tag = part.strip()
            if tag:
                result.append(tag)
    return list(dict.fromkeys(result))


def _public_image_url(object_name: str) -> str:
    return f'/api/v1/buckets/{FACE_BUCKET}/objects/download?prefix={quote(object_name, safe="")}'


def _upload_face_image(library_id: int, image_bytes: bytes, suffix: str = 'jpg') -> Tuple[str, str]:
    minio = ModelService.get_minio_client()
    if not minio.bucket_exists(FACE_BUCKET):
        minio.make_bucket(FACE_BUCKET)
    object_name = f'{library_id}/{uuid.uuid4().hex}.{suffix}'
    minio.put_object(FACE_BUCKET, object_name, io.BytesIO(image_bytes), len(image_bytes), content_type=f'image/{suffix}')
    return object_name, _public_image_url(object_name)


def _delete_minio_object(object_name: Optional[str]) -> None:
    if not object_name:
        return
    try:
        minio = ModelService.get_minio_client()
        if minio.bucket_exists(FACE_BUCKET):
            minio.remove_object(FACE_BUCKET, object_name)
    except Exception as exc:
        logger.warning('删除 MinIO 对象失败: %s', exc)


def _refresh_library_face_count(library_id: int) -> None:
    library = FaceLibrary.query.get(library_id)
    if not library:
        return
    library.face_count = FaceEntry.query.filter_by(library_id=library_id).count()
    db.session.commit()


def _library_stats(library_id: int) -> Dict[str, int]:
    ensure_person_records(library_id)
    return {
        'face_count': FaceEntry.query.filter_by(library_id=library_id).count(),
        'person_count': FacePerson.query.filter_by(library_id=library_id).count(),
    }


def _enrich_library_dict(data: Dict[str, Any], library_id: int) -> Dict[str, Any]:
    stats = _library_stats(library_id)
    data['face_count'] = stats['face_count']
    data['person_count'] = stats['person_count']
    return data


def _sync_person_entry_labels(person: FacePerson) -> None:
    """合并后统一人员下各条目的姓名/编号展示字段"""
    entries = FaceEntry.query.filter_by(person_id=person.id).all()
    for entry in entries:
        entry.person_name = person.person_name
        entry.person_code = person.person_code
        entry.updated_at = datetime.utcnow()


def _refresh_person_face_count(person_id: int, *, commit: bool = True) -> None:
    person = FacePerson.query.get(person_id)
    if not person:
        return
    entries = FaceEntry.query.filter_by(person_id=person_id).order_by(FaceEntry.created_at.asc()).all()
    person.face_count = len(entries)
    if entries:
        if not person.cover_entry_id or not any(e.id == person.cover_entry_id for e in entries):
            person.cover_entry_id = entries[0].id
        if not person.person_name:
            cover = next((e for e in entries if e.id == person.cover_entry_id), entries[0])
            person.person_name = cover.person_name
    if commit:
        db.session.commit()


def ensure_person_records(library_id: int) -> None:
    """为缺少 person_id 的历史条目补建人员记录"""
    orphan_entries = FaceEntry.query.filter_by(library_id=library_id, person_id=None).all()
    for entry in orphan_entries:
        person = FacePerson(
            library_id=library_id,
            person_name=entry.person_name,
            person_code=entry.person_code,
            is_enabled=entry.is_enabled,
            face_count=1,
        )
        db.session.add(person)
        db.session.flush()
        entry.person_id = person.id
        person.cover_entry_id = entry.id
    if orphan_entries:
        db.session.commit()


def _entry_cover_url(person: FacePerson) -> Optional[str]:
    if not person.cover_entry_id:
        return None
    entry = FaceEntry.query.get(person.cover_entry_id)
    return entry.image_url if entry else None


def _person_to_dict(person: FacePerson, include_entries: bool = False) -> Dict[str, Any]:
    cover_url = _entry_cover_url(person)
    return person.to_dict(include_entries=include_entries, cover_image_url=cover_url)


def list_libraries(search: Optional[str] = None, is_enabled: Optional[bool] = None) -> List[Dict[str, Any]]:
    query = FaceLibrary.query
    if search:
        kw = f'%{search.strip()}%'
        query = query.filter(db.or_(FaceLibrary.name.ilike(kw), FaceLibrary.code.ilike(kw)))
    if is_enabled is not None:
        query = query.filter_by(is_enabled=is_enabled)
    libs = query.order_by(FaceLibrary.id.desc()).all()
    if not libs:
        return []
    lib_ids = [lib.id for lib in libs]
    tasks = FaceAutoEnrollTask.query.filter(FaceAutoEnrollTask.library_id.in_(lib_ids)).all()
    running_map = {t.library_id: bool(t.is_running) for t in tasks}
    result = []
    for lib in libs:
        data = lib.to_dict()
        data['auto_enroll_running'] = running_map.get(lib.id, False)
        _enrich_library_dict(data, lib.id)
        result.append(data)
    return result


def get_library(library_id: int, include_entries: bool = False) -> Dict[str, Any]:
    library = FaceLibrary.query.get_or_404(library_id)
    data = library.to_dict(include_entries=include_entries)
    return _enrich_library_dict(data, library_id)


def create_library(
    name: str,
    business_tags=None,
    description: Optional[str] = None,
    similarity_threshold: float = 0.55,
    is_enabled: bool = True,
) -> FaceLibrary:
    name = (name or '').strip()
    if not name:
        raise ValueError('库名称不能为空')
    library = FaceLibrary(
        name=name,
        code=_gen_library_code(),
        business_tags=json.dumps(_normalize_business_tags(business_tags), ensure_ascii=False),
        description=(description or '').strip() or None,
        similarity_threshold=float(similarity_threshold),
        is_enabled=bool(is_enabled),
        face_count=0,
    )
    db.session.add(library)
    db.session.commit()
    return library


def update_library(library_id: int, **kwargs) -> FaceLibrary:
    library = FaceLibrary.query.get_or_404(library_id)
    if 'name' in kwargs and kwargs['name'] is not None:
        library.name = str(kwargs['name']).strip()
    if 'business_tags' in kwargs and kwargs['business_tags'] is not None:
        library.business_tags = json.dumps(_normalize_business_tags(kwargs['business_tags']), ensure_ascii=False)
    if 'description' in kwargs and kwargs['description'] is not None:
        library.description = str(kwargs['description']).strip() or None
    if 'similarity_threshold' in kwargs and kwargs['similarity_threshold'] is not None:
        library.similarity_threshold = float(kwargs['similarity_threshold'])
    if 'is_enabled' in kwargs and kwargs['is_enabled'] is not None:
        library.is_enabled = bool(kwargs['is_enabled'])
    library.updated_at = datetime.utcnow()
    db.session.commit()
    return library


def delete_library(library_id: int) -> None:
    library = FaceLibrary.query.get_or_404(library_id)
    entries = FaceEntry.query.filter_by(library_id=library_id).all()
    store = get_face_vector_store()
    for entry in entries:
        if entry.milvus_id:
            try:
                store.delete_by_milvus_id(entry.milvus_id)
            except Exception:
                pass
        _delete_minio_object(entry.image_path)
    FaceAutoEnrollTask.query.filter_by(library_id=library_id).delete()
    db.session.delete(library)
    db.session.commit()


def list_entries(library_id: int, search: Optional[str] = None) -> List[Dict[str, Any]]:
    FaceLibrary.query.get_or_404(library_id)
    ensure_person_records(library_id)
    query = FaceEntry.query.filter_by(library_id=library_id)
    if search:
        kw = f'%{search.strip()}%'
        query = query.filter(db.or_(FaceEntry.person_name.ilike(kw), FaceEntry.person_code.ilike(kw)))
    return [e.to_dict() for e in query.order_by(FaceEntry.id.desc()).all()]


def list_persons(
    library_id: int,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 18,
) -> Dict[str, Any]:
    FaceLibrary.query.get_or_404(library_id)
    ensure_person_records(library_id)
    query = FacePerson.query.filter_by(library_id=library_id)
    if search:
        kw = f'%{search.strip()}%'
        query = query.filter(db.or_(FacePerson.person_name.ilike(kw), FacePerson.person_code.ilike(kw)))
    total = query.count()
    persons = (
        query.order_by(FacePerson.updated_at.desc(), FacePerson.id.desc())
        .offset(max(0, (page - 1) * page_size))
        .limit(page_size)
        .all()
    )
    return {
        'data': [_person_to_dict(p) for p in persons],
        'total': total,
        'page': page,
        'page_size': page_size,
    }


def get_person(person_id: int, include_entries: bool = True) -> Dict[str, Any]:
    person = FacePerson.query.get_or_404(person_id)
    data = _person_to_dict(person, include_entries=include_entries)
    if include_entries:
        entries = FaceEntry.query.filter_by(person_id=person_id).order_by(FaceEntry.created_at.asc()).all()
        data['entries'] = [e.to_dict() for e in entries]
    return data


def set_person_cover(person_id: int, entry_id: int) -> Dict[str, Any]:
    person = FacePerson.query.get_or_404(person_id)
    entry = FaceEntry.query.get_or_404(entry_id)
    if entry.person_id != person.id:
        raise ValueError('封面人脸不属于该人员')
    person.cover_entry_id = entry.id
    person.updated_at = datetime.utcnow()
    db.session.commit()
    return _person_to_dict(person)


def add_entry(
    library_id: int,
    person_name: str,
    image_bytes: bytes,
    person_code: Optional[str] = None,
    remark: Optional[str] = None,
    person_id: Optional[int] = None,
    is_enabled: bool = True,
) -> FaceEntry:
    library = FaceLibrary.query.get_or_404(library_id)
    person_name = (person_name or '').strip()
    if not person_name:
        raise ValueError('姓名不能为空')
    if not image_bytes:
        raise ValueError('请上传人脸照片')

    image = decode_image_bytes(image_bytes)
    service = get_face_recognition_service()
    try:
        crop_info = service.extract_and_crop_largest_face(image)
    except FileNotFoundError as exc:
        raise ValueError(
            '人脸特征模型 face_rec.onnx 未安装，请在人脸库页面下载安装后再录入'
        ) from exc
    if not crop_info:
        raise ValueError('图片中未检测到人脸，请上传正面清晰的人脸照片')

    _, crop = cv2.imencode('.jpg', crop_info['crop'])
    crop_bytes = crop.tobytes()
    object_name, image_url = _upload_face_image(library_id, crop_bytes)

    if person_id:
        person = FacePerson.query.filter_by(id=person_id, library_id=library_id).first()
        if not person:
            raise ValueError('指定人员不存在')
    else:
        person = FacePerson(
            library_id=library_id,
            person_name=person_name,
            person_code=person_code,
            is_enabled=is_enabled,
            face_count=0,
        )
        db.session.add(person)
        db.session.flush()

    entry = FaceEntry(
        library_id=library_id,
        person_id=person.id,
        person_name=person_name,
        person_code=person_code,
        image_path=object_name,
        image_url=image_url,
        remark=remark,
        is_enabled=is_enabled,
    )
    db.session.add(entry)
    db.session.flush()

    inserted = service.add_face_to_library(
        library_id=library_id,
        face_entry_id=entry.id,
        person_name=person_name,
        image=crop_info['crop'],
        person_code=person_code,
        embedding=crop_info.get('embedding'),
    )
    entry.milvus_id = inserted.get('milvus_id')

    if not person.cover_entry_id:
        person.cover_entry_id = entry.id
    person.person_name = person.person_name or person_name
    person.person_code = person.person_code or person_code
    person.updated_at = datetime.utcnow()
    _refresh_person_face_count(person.id)
    _refresh_library_face_count(library_id)
    db.session.commit()
    return entry


def add_entries_batch(
    library_id: int,
    person_name: str,
    image_files: List[bytes],
    person_code: Optional[str] = None,
    remark: Optional[str] = None,
    person_id: Optional[int] = None,
    is_enabled: bool = True,
) -> Dict[str, Any]:
    """批量录入：同一人多张人脸照片（创建或追加到已有人员）"""
    if not image_files:
        raise ValueError('请至少上传一张人脸照片')
    entries: List[FaceEntry] = []
    errors: List[Dict[str, Any]] = []
    resolved_person_id = person_id
    for idx, image_bytes in enumerate(image_files):
        if not image_bytes:
            errors.append({'index': idx, 'msg': '图片数据为空'})
            continue
        try:
            entry = add_entry(
                library_id=library_id,
                person_name=person_name,
                image_bytes=image_bytes,
                person_code=person_code,
                remark=remark,
                person_id=resolved_person_id,
                is_enabled=is_enabled,
            )
            if resolved_person_id is None and entry.person_id:
                resolved_person_id = entry.person_id
            entries.append(entry)
        except Exception as exc:
            errors.append({'index': idx, 'msg': str(exc)})
    if not entries:
        raise ValueError(errors[0]['msg'] if errors else '批量录入失败')
    return {
        'person_id': resolved_person_id,
        'entries': [e.to_dict() for e in entries],
        'success_count': len(entries),
        'failed_count': len(errors),
        'errors': errors,
    }


def update_entry(entry_id: int, image_bytes: Optional[bytes] = None, **kwargs) -> FaceEntry:
    entry = FaceEntry.query.get_or_404(entry_id)
    person = FacePerson.query.get(entry.person_id) if entry.person_id else None

    if kwargs.get('person_name') is not None:
        entry.person_name = str(kwargs['person_name']).strip()
        if person and person.cover_entry_id == entry.id:
            person.person_name = entry.person_name
    if kwargs.get('person_code') is not None:
        entry.person_code = str(kwargs['person_code']).strip() or None
        if person and person.cover_entry_id == entry.id:
            person.person_code = entry.person_code
    if kwargs.get('remark') is not None:
        entry.remark = str(kwargs['remark']).strip() or None
    if kwargs.get('is_enabled') is not None:
        entry.is_enabled = bool(kwargs['is_enabled'])

    if image_bytes:
        service = get_face_recognition_service()
        image = decode_image_bytes(image_bytes)
        try:
            crop_info = service.extract_and_crop_largest_face(image)
        except FileNotFoundError as exc:
            raise ValueError(
                '人脸特征模型 face_rec.onnx 未安装，请在人脸库页面下载安装后再录入'
            ) from exc
        if not crop_info:
            raise ValueError('图片中未检测到人脸，请上传正面清晰的人脸照片')
        _, crop = cv2.imencode('.jpg', crop_info['crop'])
        crop_bytes = crop.tobytes()
        _delete_minio_object(entry.image_path)
        object_name, image_url = _upload_face_image(entry.library_id, crop_bytes)
        entry.image_path = object_name
        entry.image_url = image_url
        store = get_face_vector_store()
        if entry.milvus_id:
            try:
                store.delete_by_milvus_id(entry.milvus_id)
            except Exception:
                pass
        inserted = service.add_face_to_library(
            library_id=entry.library_id,
            face_entry_id=entry.id,
            person_name=entry.person_name,
            image=crop_info['crop'],
            person_code=entry.person_code,
            embedding=crop_info.get('embedding'),
        )
        entry.milvus_id = inserted.get('milvus_id')

    entry.updated_at = datetime.utcnow()
    if person:
        person.updated_at = datetime.utcnow()
    db.session.commit()
    return entry


def delete_person(person_id: int) -> None:
    """删除人员及其全部人脸照片"""
    person = FacePerson.query.get_or_404(person_id)
    library_id = person.library_id
    entries = FaceEntry.query.filter_by(person_id=person_id).all()
    store = get_face_vector_store()
    for entry in entries:
        if entry.milvus_id:
            try:
                store.delete_by_milvus_id(entry.milvus_id)
            except Exception:
                pass
        _delete_minio_object(entry.image_path)
        db.session.delete(entry)
    db.session.delete(person)
    db.session.flush()
    _refresh_library_face_count(library_id)
    db.session.commit()


def batch_delete_persons(person_ids: List[int]) -> int:
    """批量删除人员，返回成功删除数量"""
    if not person_ids:
        return 0
    library_ids: Set[int] = set()
    store = get_face_vector_store()
    deleted = 0
    for person_id in person_ids:
        person = FacePerson.query.get(int(person_id))
        if not person:
            continue
        library_ids.add(person.library_id)
        entries = FaceEntry.query.filter_by(person_id=person.id).all()
        for entry in entries:
            if entry.milvus_id:
                try:
                    store.delete_by_milvus_id(entry.milvus_id)
                except Exception:
                    pass
            _delete_minio_object(entry.image_path)
            db.session.delete(entry)
        db.session.delete(person)
        deleted += 1
    db.session.flush()
    for library_id in library_ids:
        _refresh_library_face_count(library_id)
    db.session.commit()
    return deleted


def delete_entry(entry_id: int) -> None:
    entry = FaceEntry.query.get_or_404(entry_id)
    library_id = entry.library_id
    person_id = entry.person_id
    store = get_face_vector_store()
    if entry.milvus_id:
        try:
            store.delete_by_milvus_id(entry.milvus_id)
        except Exception:
            pass
    _delete_minio_object(entry.image_path)

    person = FacePerson.query.get(person_id) if person_id else None
    was_cover = person and person.cover_entry_id == entry.id
    db.session.delete(entry)
    db.session.flush()

    if person:
        remaining = FaceEntry.query.filter_by(person_id=person.id).count()
        if remaining == 0:
            db.session.delete(person)
        else:
            if was_cover:
                first_entry = FaceEntry.query.filter_by(person_id=person.id).order_by(FaceEntry.created_at.asc()).first()
                person.cover_entry_id = first_entry.id if first_entry else None
            _refresh_person_face_count(person.id)
    _refresh_library_face_count(library_id)
    db.session.commit()


def _union_find_groups(entry_ids: List[int], pairs: List[tuple[int, int]]) -> Dict[int, Set[int]]:
    parent = {eid: eid for eid in entry_ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b in pairs:
        if a in parent and b in parent:
            union(a, b)

    groups: Dict[int, Set[int]] = {}
    for eid in entry_ids:
        root = find(eid)
        groups.setdefault(root, set()).add(eid)
    return groups


def preview_normalize_groups(library_id: int, threshold: float = 0.75) -> List[Dict[str, Any]]:
    FaceLibrary.query.get_or_404(library_id)
    ensure_person_records(library_id)
    entries = FaceEntry.query.filter_by(library_id=library_id).order_by(FaceEntry.id.asc()).all()
    if len(entries) < 2:
        return []

    entry_map = {e.id: e for e in entries}
    store = get_face_vector_store()
    try:
        vectors = store.list_library_embeddings(library_id)
    except Exception as exc:
        logger.warning('读取 Milvus 向量失败，跳过归一化预览: %s', exc)
        return []

    vec_map: Dict[int, np.ndarray] = {}
    for row in vectors:
        eid = int(row.get('face_entry_id') or 0)
        emb = row.get('embedding')
        if eid and emb is not None:
            vec_map[eid] = np.array(emb, dtype=np.float32)

    valid_ids = [eid for eid in entry_map if eid in vec_map]
    pairs: List[tuple[int, int]] = []
    for i, a in enumerate(valid_ids):
        va = vec_map[a]
        for b in valid_ids[i + 1:]:
            sim = float(np.dot(va, vec_map[b]))
            if sim >= threshold:
                pairs.append((a, b))

    grouped = _union_find_groups(valid_ids, pairs)
    result: List[Dict[str, Any]] = []
    group_idx = 1
    for members in grouped.values():
        if len(members) < 2:
            continue
        member_entries = [entry_map[mid] for mid in sorted(members)]
        person_ids = {e.person_id for e in member_entries if e.person_id}
        if len(person_ids) <= 1:
            continue

        persons_map: Dict[int, List[FaceEntry]] = {}
        for entry in member_entries:
            if entry.person_id:
                persons_map.setdefault(entry.person_id, []).append(entry)

        def _entry_payload(e: FaceEntry) -> Dict[str, Any]:
            return {
                'entry_id': e.id,
                'person_id': e.person_id,
                'person_name': e.person_name,
                'person_code': e.person_code,
                'image_url': e.image_url,
                'image_path': e.image_path,
                'created_at': e.created_at.isoformat() if e.created_at else None,
            }

        persons_data: List[Dict[str, Any]] = []
        for pid in sorted(persons_map.keys(), key=lambda x: (-len(persons_map[x]), x)):
            person = FacePerson.query.get(pid)
            entries = persons_map[pid]
            persons_data.append({
                'person_id': pid,
                'person_name': (person.person_name if person else None) or entries[0].person_name,
                'person_code': (person.person_code if person else None) or entries[0].person_code,
                'face_count': len(entries),
                'entries': [_entry_payload(e) for e in entries],
            })

        suggested_person_id = persons_data[0]['person_id']
        cover_entries = persons_map.get(suggested_person_id) or member_entries
        suggested_entry_id = min(e.id for e in cover_entries)

        flat_entries = [_entry_payload(e) for e in member_entries]
        result.append({
            'group_id': group_idx,
            'count': len(member_entries),
            'entry_count': len(member_entries),
            'person_count': len(persons_data),
            'suggested_target_person_id': suggested_person_id,
            'suggested_target_entry_id': suggested_entry_id,
            'persons': persons_data,
            'entries': flat_entries,
        })
        group_idx += 1
    return result


def merge_persons(
    target_person_id: int,
    source_person_ids: List[int],
    *,
    commit: bool = True,
) -> Dict[str, Any]:
    """归一化合并：将其他人员的全部人脸照片归入目标人员，保留所有照片"""
    target_person = FacePerson.query.get_or_404(target_person_id)
    sources = [int(x) for x in (source_person_ids or []) if int(x) != target_person_id]
    if not sources:
        raise ValueError('没有可合并的人员')

    for sid in sources:
        source_person = FacePerson.query.get(sid)
        if not source_person or source_person.library_id != target_person.library_id:
            continue
        if not target_person.person_code and source_person.person_code:
            target_person.person_code = source_person.person_code
        entries = FaceEntry.query.filter_by(person_id=source_person.id).all()
        for entry in entries:
            entry.person_id = target_person.id
            entry.updated_at = datetime.utcnow()
        db.session.flush()
        db.session.delete(source_person)

    _sync_person_entry_labels(target_person)
    target_person.updated_at = datetime.utcnow()
    _refresh_person_face_count(target_person.id, commit=commit)
    if commit:
        db.session.commit()
    return get_person(target_person.id, include_entries=True)


def merge_face_entries(target_entry_id: int, source_entry_ids: List[int]) -> Dict[str, Any]:
    """归一化合并（按条目）：将源条目归入目标条目所属人员，保留全部照片"""
    target = FaceEntry.query.get_or_404(target_entry_id)
    target_person = FacePerson.query.get_or_404(target.person_id)
    source_ids = [int(x) for x in (source_entry_ids or []) if int(x) != target_entry_id]
    if not source_ids:
        raise ValueError('没有可合并的条目')

    source_person_ids: Set[int] = set()
    for sid in source_ids:
        source = FaceEntry.query.get(sid)
        if not source or source.library_id != target.library_id:
            continue
        if source.person_id and source.person_id != target_person.id:
            source_person_ids.add(source.person_id)
        source.person_id = target_person.id
        source.updated_at = datetime.utcnow()

    for pid in source_person_ids:
        old_person = FacePerson.query.get(pid)
        if not old_person:
            continue
        remaining = FaceEntry.query.filter_by(person_id=old_person.id).count()
        if remaining == 0:
            db.session.delete(old_person)

    _sync_person_entry_labels(target_person)
    target_person.updated_at = datetime.utcnow()
    _refresh_person_face_count(target_person.id)
    db.session.commit()
    return get_person(target_person.id, include_entries=True)


def merge_all_normalize_groups(library_id: int, threshold: float = 0.75) -> Dict[str, Any]:
    """按预览建议批量合并全部相似分组"""
    groups = preview_normalize_groups(library_id, threshold=threshold)
    merged_groups = 0
    merged_persons = 0
    for group in groups:
        target_pid = group.get('suggested_target_person_id')
        if not target_pid:
            continue
        source_pids = [
            int(p['person_id'])
            for p in (group.get('persons') or [])
            if int(p['person_id']) != int(target_pid)
        ]
        if not source_pids:
            continue
        merge_persons(int(target_pid), source_pids, commit=False)
        merged_groups += 1
        merged_persons += len(source_pids)
    if merged_groups:
        db.session.commit()
    stats = _library_stats(library_id)
    return {
        'merged_groups': merged_groups,
        'merged_persons': merged_persons,
        **stats,
    }


def match_face_in_library(
    library_id: int,
    image_bytes: bytes,
    threshold: Optional[float] = None,
    top_k: int = 5,
) -> Dict[str, Any]:
    library = FaceLibrary.query.get_or_404(library_id)
    use_threshold = float(threshold if threshold is not None else library.similarity_threshold)
    service = get_face_recognition_service()
    image = decode_image_bytes(image_bytes)
    return service.match_in_library(library_id, image, use_threshold, top_k=top_k)


def list_match_records(
    page: int = 1,
    page_size: int = 20,
    library_id: Optional[int] = None,
    device_id: Optional[str] = None,
    matched: Optional[bool] = None,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    query = FaceMatchRecord.query
    if library_id:
        query = query.filter_by(library_id=library_id)
    if device_id:
        query = query.filter_by(device_id=device_id)
    if matched is not None:
        query = query.filter_by(matched=matched)
    if correlation_id:
        cid = str(correlation_id).strip()
        if cid:
            query = query.filter_by(correlation_id=cid)
    total = query.count()
    rows = (
        query.order_by(FaceMatchRecord.id.desc())
        .offset(max(0, (page - 1) * page_size))
        .limit(page_size)
        .all()
    )
    return {'list': [r.to_dict() for r in rows], 'total': total}


def process_face_matching_message(payload: Dict[str, Any]) -> FaceMatchRecord:
    from app.services.library_matching_service import process_face_matching_message as _process
    return _process(payload)
