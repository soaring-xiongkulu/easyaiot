"""车牌库业务服务"""
import io
import json
import logging
import os
import re
import uuid
from difflib import SequenceMatcher
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs, quote, urlparse

import cv2
import numpy as np

from app.services.minio_service import ModelService
from app.utils.plate_capture_service import detect_and_recognize_plates
from models import PlateAutoEnrollTask, PlateEntry, PlateLibrary, PlateMatchRecord, db

logger = logging.getLogger(__name__)

PLATE_BUCKET = os.getenv('PLATE_IMAGE_BUCKET', 'plate-library')
LIBRARY_CODE_LENGTH = 12
PLATE_NO_PATTERN = re.compile(
    r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领'
    r'学警港澳挂民航危0123456789ABCDEFGHJKLMNPQRSTUVWXYZ险品]{5,10}$'
)


def _gen_library_code() -> str:
    for _ in range(20):
        code = uuid.uuid4().hex[:LIBRARY_CODE_LENGTH].upper()
        if not PlateLibrary.query.filter_by(code=code).first():
            return code
    raise RuntimeError('无法生成唯一的车牌库编码')


def _normalize_business_tags(tags) -> List[str]:
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


def _normalize_plate_no(plate_no: str) -> str:
    return (plate_no or '').strip().upper().replace(' ', '')


def _plate_no_similarity(plate_a: str, plate_b: str) -> float:
    """规范化后车牌字符串相似度，1.0 表示完全一致"""
    a = _normalize_plate_no(plate_a)
    b = _normalize_plate_no(plate_b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def _union_find_groups(entry_ids: List[int], pairs: List[tuple]) -> Dict[int, Set[int]]:
    parent = {eid: eid for eid in entry_ids}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[parent[x]] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
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


def _public_image_url(object_name: str) -> str:
    return f'/api/v1/buckets/{PLATE_BUCKET}/objects/download?prefix={quote(object_name, safe="")}'


def _upload_plate_image(library_id: int, image_bytes: bytes, suffix: str = 'jpg') -> Tuple[str, str]:
    minio = ModelService.get_minio_client()
    if not minio.bucket_exists(PLATE_BUCKET):
        minio.make_bucket(PLATE_BUCKET)
    object_name = f'{library_id}/{uuid.uuid4().hex}.{suffix}'
    minio.put_object(PLATE_BUCKET, object_name, io.BytesIO(image_bytes), len(image_bytes), content_type=f'image/{suffix}')
    return object_name, _public_image_url(object_name)


def _delete_minio_object(object_name: Optional[str]) -> None:
    if not object_name:
        return
    try:
        minio = ModelService.get_minio_client()
        if minio.bucket_exists(PLATE_BUCKET):
            minio.remove_object(PLATE_BUCKET, object_name)
    except Exception as exc:
        logger.warning('删除 MinIO 对象失败: %s', exc)


def _object_name_from_url(image_url: Optional[str]) -> Optional[str]:
    if not image_url:
        return None
    if image_url.startswith('/api/v1/buckets/'):
        try:
            parsed = urlparse(image_url)
            prefix = parse_qs(parsed.query).get('prefix', [None])[0]
            if prefix:
                return prefix
        except Exception:
            pass
    marker = f'/{PLATE_BUCKET}/'
    idx = image_url.find(marker)
    if idx >= 0:
        return image_url[idx + len(marker):]
    return None


def _refresh_library_plate_count(library_id: int) -> None:
    library = PlateLibrary.query.get(library_id)
    if not library:
        return
    library.plate_count = PlateEntry.query.filter_by(library_id=library_id).count()
    db.session.commit()


def list_libraries(search: Optional[str] = None, is_enabled: Optional[bool] = None) -> List[Dict[str, Any]]:
    query = PlateLibrary.query
    if search:
        kw = f'%{search.strip()}%'
        query = query.filter(db.or_(PlateLibrary.name.ilike(kw), PlateLibrary.code.ilike(kw)))
    if is_enabled is not None:
        query = query.filter_by(is_enabled=is_enabled)
    libs = query.order_by(PlateLibrary.id.desc()).all()
    if not libs:
        return []
    lib_ids = [lib.id for lib in libs]
    tasks = PlateAutoEnrollTask.query.filter(PlateAutoEnrollTask.library_id.in_(lib_ids)).all()
    running_map = {t.library_id: bool(t.is_running) for t in tasks}
    result = []
    for lib in libs:
        data = lib.to_dict()
        data['auto_enroll_running'] = running_map.get(lib.id, False)
        data['plate_count'] = PlateEntry.query.filter_by(library_id=lib.id).count()
        result.append(data)
    return result


def get_library(library_id: int, include_entries: bool = False) -> Dict[str, Any]:
    library = PlateLibrary.query.get_or_404(library_id)
    data = library.to_dict(include_entries=include_entries)
    data['plate_count'] = PlateEntry.query.filter_by(library_id=library_id).count()
    return data


def create_library(
    name: str,
    business_tags=None,
    description: Optional[str] = None,
    is_enabled: bool = True,
) -> PlateLibrary:
    name = (name or '').strip()
    if not name:
        raise ValueError('库名称不能为空')
    library = PlateLibrary(
        name=name,
        code=_gen_library_code(),
        business_tags=json.dumps(_normalize_business_tags(business_tags), ensure_ascii=False),
        description=(description or '').strip() or None,
        is_enabled=is_enabled,
    )
    db.session.add(library)
    db.session.commit()
    return library


def update_library(library_id: int, **kwargs) -> PlateLibrary:
    library = PlateLibrary.query.get_or_404(library_id)
    if 'name' in kwargs and kwargs['name'] is not None:
        name = str(kwargs['name']).strip()
        if not name:
            raise ValueError('库名称不能为空')
        library.name = name
    if 'business_tags' in kwargs:
        library.business_tags = json.dumps(_normalize_business_tags(kwargs['business_tags']), ensure_ascii=False)
    if 'description' in kwargs:
        library.description = (kwargs['description'] or '').strip() or None
    if 'is_enabled' in kwargs and kwargs['is_enabled'] is not None:
        library.is_enabled = bool(kwargs['is_enabled'])
    library.updated_at = datetime.utcnow()
    db.session.commit()
    return library


def delete_library(library_id: int) -> None:
    library = PlateLibrary.query.get_or_404(library_id)
    entries = PlateEntry.query.filter_by(library_id=library_id).all()
    for entry in entries:
        _delete_minio_object(_object_name_from_url(entry.image_url))
    db.session.delete(library)
    db.session.commit()


def list_entries(
    library_id: int,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    PlateLibrary.query.get_or_404(library_id)
    query = PlateEntry.query.filter_by(library_id=library_id)
    if search:
        kw = f'%{search.strip()}%'
        query = query.filter(
            db.or_(
                PlateEntry.plate_no.ilike(kw),
                PlateEntry.owner_name.ilike(kw),
                PlateEntry.owner_phone.ilike(kw),
            )
        )
    total = query.count()
    rows = (
        query.order_by(PlateEntry.id.desc())
        .offset(max(0, (page - 1) * page_size))
        .limit(page_size)
        .all()
    )
    return {'list': [r.to_dict() for r in rows], 'total': total}


def add_entry(
    library_id: int,
    plate_no: str,
    plate_color: Optional[str] = None,
    owner_name: Optional[str] = None,
    owner_phone: Optional[str] = None,
    remark: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    is_enabled: bool = True,
) -> PlateEntry:
    PlateLibrary.query.get_or_404(library_id)
    plate_no = _normalize_plate_no(plate_no)
    if not plate_no:
        raise ValueError('车牌号不能为空')
    existing = PlateEntry.query.filter_by(library_id=library_id, plate_no=plate_no).first()
    if existing:
        raise ValueError(f'车牌号 {plate_no} 已存在于该库中')

    image_url = None
    if image_bytes:
        _, image_url = _upload_plate_image(library_id, image_bytes)

    entry = PlateEntry(
        library_id=library_id,
        plate_no=plate_no,
        plate_color=(plate_color or '').strip() or None,
        owner_name=(owner_name or '').strip() or None,
        owner_phone=(owner_phone or '').strip() or None,
        image_url=image_url,
        remark=(remark or '').strip() or None,
        is_enabled=is_enabled,
    )
    db.session.add(entry)
    db.session.commit()
    _refresh_library_plate_count(library_id)
    return entry


def update_entry(entry_id: int, **kwargs) -> PlateEntry:
    entry = PlateEntry.query.get_or_404(entry_id)
    if 'plate_no' in kwargs and kwargs['plate_no'] is not None:
        plate_no = _normalize_plate_no(kwargs['plate_no'])
        if not plate_no:
            raise ValueError('车牌号不能为空')
        dup = PlateEntry.query.filter(
            PlateEntry.library_id == entry.library_id,
            PlateEntry.plate_no == plate_no,
            PlateEntry.id != entry_id,
        ).first()
        if dup:
            raise ValueError(f'车牌号 {plate_no} 已存在于该库中')
        entry.plate_no = plate_no
    for field in ('plate_color', 'owner_name', 'owner_phone', 'remark'):
        if field in kwargs:
            val = kwargs[field]
            setattr(entry, field, (val or '').strip() or None if val is not None else getattr(entry, field))
    if 'is_enabled' in kwargs and kwargs['is_enabled'] is not None:
        entry.is_enabled = bool(kwargs['is_enabled'])
    if kwargs.get('image_bytes'):
        _delete_minio_object(_object_name_from_url(entry.image_url))
        _, entry.image_url = _upload_plate_image(entry.library_id, kwargs['image_bytes'])
    entry.updated_at = datetime.utcnow()
    db.session.commit()
    return entry


def delete_entry(entry_id: int) -> None:
    entry = PlateEntry.query.get_or_404(entry_id)
    library_id = entry.library_id
    _delete_minio_object(_object_name_from_url(entry.image_url))
    db.session.delete(entry)
    db.session.commit()
    _refresh_library_plate_count(library_id)


def batch_delete_entries(entry_ids: List[int]) -> int:
    if not entry_ids:
        return 0
    entries = PlateEntry.query.filter(PlateEntry.id.in_(entry_ids)).all()
    library_ids = set()
    for entry in entries:
        library_ids.add(entry.library_id)
        _delete_minio_object(_object_name_from_url(entry.image_url))
        db.session.delete(entry)
    db.session.commit()
    for lib_id in library_ids:
        _refresh_library_plate_count(lib_id)
    return len(entries)


def _entry_normalize_payload(entry: PlateEntry) -> Dict[str, Any]:
    return {
        'entry_id': entry.id,
        'plate_no': entry.plate_no,
        'plate_color': entry.plate_color,
        'owner_name': entry.owner_name,
        'owner_phone': entry.owner_phone,
        'image_url': entry.image_url,
        'image_path': entry.image_path,
        'remark': entry.remark,
        'is_enabled': entry.is_enabled,
        'created_at': entry.created_at.isoformat() if entry.created_at else None,
    }


def _suggest_target_plate_entry(entries: List[PlateEntry]) -> int:
    """优先保留有图片、车主信息较全、最早录入的条目作为合并目标"""

    def _score(entry: PlateEntry) -> tuple:
        rank = 0
        if entry.image_url:
            rank -= 100
        if entry.owner_name:
            rank -= 10
        if entry.owner_phone:
            rank -= 5
        if entry.plate_color:
            rank -= 2
        return (rank, entry.id)

    return min(entries, key=_score).id


def preview_normalize_groups(library_id: int, threshold: float = 1.0) -> List[Dict[str, Any]]:
    """预览库内可合并的重复车牌组；threshold=1 为规范化后完全一致，降低则允许 OCR 近似"""
    PlateLibrary.query.get_or_404(library_id)
    threshold = max(0.75, min(1.0, float(threshold)))
    entries = (
        PlateEntry.query.filter_by(library_id=library_id)
        .order_by(PlateEntry.id.asc())
        .all()
    )
    if len(entries) < 2:
        return []

    entry_map = {e.id: e for e in entries}
    member_groups: List[List[PlateEntry]] = []

    if threshold >= 0.999:
        grouped: Dict[str, List[PlateEntry]] = {}
        for entry in entries:
            key = _normalize_plate_no(entry.plate_no)
            if not key:
                continue
            grouped.setdefault(key, []).append(entry)
        member_groups = [members for members in grouped.values() if len(members) >= 2]
    else:
        valid_entries = [e for e in entries if _normalize_plate_no(e.plate_no)]
        valid_ids = [e.id for e in valid_entries]
        pairs: List[tuple] = []
        for i, entry_a in enumerate(valid_entries):
            for entry_b in valid_entries[i + 1:]:
                if _plate_no_similarity(entry_a.plate_no, entry_b.plate_no) >= threshold:
                    pairs.append((entry_a.id, entry_b.id))
        clustered = _union_find_groups(valid_ids, pairs)
        for members_ids in clustered.values():
            if len(members_ids) < 2:
                continue
            member_groups.append([entry_map[mid] for mid in sorted(members_ids)])

    result: List[Dict[str, Any]] = []
    for group_idx, members in enumerate(member_groups, start=1):
        suggested_id = _suggest_target_plate_entry(members)
        canonical = _normalize_plate_no(entry_map[suggested_id].plate_no)
        result.append({
            'group_id': group_idx,
            'plate_no': canonical,
            'count': len(members),
            'entry_count': len(members),
            'suggested_target_entry_id': suggested_id,
            'entries': [_entry_normalize_payload(e) for e in members],
        })
    return result


def merge_plate_entries(
    target_entry_id: int,
    source_entry_ids: List[int],
    *,
    commit: bool = True,
) -> Dict[str, Any]:
    """将同车牌号的重复条目合并到目标条目，补全车主/图片等字段后删除冗余记录"""
    target = PlateEntry.query.get_or_404(target_entry_id)
    source_ids = [int(x) for x in (source_entry_ids or []) if int(x) != target_entry_id]
    if not source_ids:
        raise ValueError('没有可合并的条目')

    sources: List[PlateEntry] = []
    for sid in source_ids:
        source = PlateEntry.query.get(sid)
        if not source or source.library_id != target.library_id:
            continue
        sources.append(source)
    if not sources:
        raise ValueError('没有可合并的条目')

    target.plate_no = _normalize_plate_no(target.plate_no)
    for source in sources:
        if not target.plate_color and source.plate_color:
            target.plate_color = source.plate_color
        if not target.owner_name and source.owner_name:
            target.owner_name = source.owner_name
        if not target.owner_phone and source.owner_phone:
            target.owner_phone = source.owner_phone
        if not target.remark and source.remark:
            target.remark = source.remark
        if source.is_enabled:
            target.is_enabled = True
        if not target.image_url and source.image_url:
            target.image_url = source.image_url
            target.image_path = source.image_path
        else:
            _delete_minio_object(_object_name_from_url(source.image_url))
        db.session.delete(source)

    target.updated_at = datetime.utcnow()
    if commit:
        db.session.commit()
        _refresh_library_plate_count(target.library_id)
    return target.to_dict()


def merge_all_normalize_groups(library_id: int, threshold: float = 1.0) -> Dict[str, Any]:
    """按预览建议批量合并全部重复车牌组"""
    groups = preview_normalize_groups(library_id, threshold=threshold)
    merged_groups = 0
    merged_entries = 0
    for group in groups:
        target_id = group.get('suggested_target_entry_id')
        if not target_id:
            continue
        source_ids = [
            int(e['entry_id'])
            for e in (group.get('entries') or [])
            if int(e['entry_id']) != int(target_id)
        ]
        if not source_ids:
            continue
        merge_plate_entries(int(target_id), source_ids, commit=False)
        merged_groups += 1
        merged_entries += len(source_ids)
    if merged_groups:
        db.session.commit()
        _refresh_library_plate_count(library_id)
    stats = get_library(library_id)
    return {
        'merged_groups': merged_groups,
        'merged_entries': merged_entries,
        'plate_count': stats.get('plate_count', 0),
    }


def match_plate_in_library(library_id: int, plate_no: str) -> Dict[str, Any]:
    """在车牌库中精确匹配车牌号"""
    PlateLibrary.query.get_or_404(library_id)
    plate_no = _normalize_plate_no(plate_no)
    if not plate_no:
        return {'matched': False, 'plate_no': plate_no, 'entry': None}
    entry = PlateEntry.query.filter_by(
        library_id=library_id, plate_no=plate_no, is_enabled=True,
    ).first()
    return {
        'matched': entry is not None,
        'plate_no': plate_no,
        'entry': entry.to_dict() if entry else None,
    }


def recognize_plates_in_image(image_bytes: bytes) -> List[Dict[str, Any]]:
    """识别图片中的车牌"""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError('无法解码图片')
    return detect_and_recognize_plates(image)


def list_match_records(
    page: int = 1,
    page_size: int = 20,
    library_id: Optional[int] = None,
    device_id: Optional[str] = None,
    matched: Optional[bool] = None,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    query = PlateMatchRecord.query
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
        query.order_by(PlateMatchRecord.id.desc())
        .offset(max(0, (page - 1) * page_size))
        .limit(page_size)
        .all()
    )
    return {'list': [r.to_dict() for r in rows], 'total': total}


def process_plate_matching_message(payload: Dict[str, Any]) -> PlateMatchRecord:
    from app.services.library_matching_service import process_plate_matching_message as _process
    return _process(payload)
