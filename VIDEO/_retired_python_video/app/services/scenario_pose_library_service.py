"""场景姿态库业务服务"""
import io
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import cv2
import numpy as np

from app.services.minio_service import ModelService
from app.utils.pose_intent import (
    SCENE_TEMPLATES,
    extract_angle_features,
    features_from_json,
    features_to_json,
    match_person_to_entry,
)
from models import ScenarioPoseEntry, ScenarioPoseLibrary, db

logger = logging.getLogger(__name__)

POSE_BUCKET = os.getenv('SCENARIO_POSE_IMAGE_BUCKET', 'scenario-pose-library')
LIBRARY_CODE_LENGTH = 12


def _gen_library_code() -> str:
    for _ in range(20):
        code = uuid.uuid4().hex[:LIBRARY_CODE_LENGTH].upper()
        if not ScenarioPoseLibrary.query.filter_by(code=code).first():
            return code
    raise RuntimeError('无法生成唯一的场景姿态库编码')


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


def _public_image_url(object_name: str) -> str:
    return f'/api/v1/buckets/{POSE_BUCKET}/objects/download?prefix={quote(object_name, safe="")}'


def _upload_pose_image(library_id: int, image_bytes: bytes, suffix: str = 'jpg') -> Tuple[str, str]:
    minio = ModelService.get_minio_client()
    if not minio.bucket_exists(POSE_BUCKET):
        minio.make_bucket(POSE_BUCKET)
    object_name = f'{library_id}/{uuid.uuid4().hex}.{suffix}'
    minio.put_object(
        POSE_BUCKET, object_name, io.BytesIO(image_bytes), len(image_bytes),
        content_type=f'image/{suffix}',
    )
    return object_name, _public_image_url(object_name)


def _delete_minio_object(object_name: Optional[str]) -> None:
    if not object_name:
        return
    try:
        minio = ModelService.get_minio_client()
        if minio.bucket_exists(POSE_BUCKET):
            minio.remove_object(POSE_BUCKET, object_name)
    except Exception as exc:
        logger.warning('删除 MinIO 对象失败: %s', exc)


def _refresh_library_entry_count(library_id: int) -> None:
    library = ScenarioPoseLibrary.query.get(library_id)
    if not library:
        return
    library.entry_count = ScenarioPoseEntry.query.filter_by(library_id=library_id).count()
    db.session.commit()


def extract_keypoints_from_image_bytes(image_bytes: bytes, conf: float = 0.25) -> List[Dict[str, Any]]:
    from app.utils.pose_analysis import run_pose_analysis, load_pose_model, DEFAULT_POSE_CONF

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError('无法解码图片')
    model = load_pose_model({'model_file_path': 'yolo26n-pose.pt', 'conf': conf or DEFAULT_POSE_CONF})
    persons = run_pose_analysis(model, frame, conf=conf or DEFAULT_POSE_CONF)
    return persons


def extract_keypoints_from_path(image_path: str, conf: float = 0.25) -> List[Dict[str, Any]]:
    if not image_path or not os.path.isfile(image_path):
        return []
    with open(image_path, 'rb') as f:
        return extract_keypoints_from_image_bytes(f.read(), conf=conf)


def list_libraries(search: Optional[str] = None, is_enabled: Optional[bool] = None) -> List[Dict[str, Any]]:
    query = ScenarioPoseLibrary.query
    if search:
        kw = f'%{search.strip()}%'
        query = query.filter(db.or_(
            ScenarioPoseLibrary.name.ilike(kw),
            ScenarioPoseLibrary.code.ilike(kw),
        ))
    if is_enabled is not None:
        query = query.filter_by(is_enabled=is_enabled)
    libs = query.order_by(ScenarioPoseLibrary.id.desc()).all()
    result = []
    for lib in libs:
        data = lib.to_dict()
        data['entry_count'] = ScenarioPoseEntry.query.filter_by(library_id=lib.id).count()
        result.append(data)
    return result


def get_library(library_id: int, include_entries: bool = False) -> Dict[str, Any]:
    library = ScenarioPoseLibrary.query.get_or_404(library_id)
    data = library.to_dict(include_entries=include_entries)
    data['entry_count'] = ScenarioPoseEntry.query.filter_by(library_id=library_id).count()
    return data


def create_library(
    name: str,
    *,
    scene_category: Optional[str] = None,
    business_tags=None,
    description: Optional[str] = None,
    similarity_threshold: float = 0.72,
    match_mode: str = 'angle',
    intent_event: Optional[str] = None,
    intent_object: Optional[str] = None,
    alert_level: str = 'warning',
    is_enabled: bool = True,
) -> ScenarioPoseLibrary:
    name = (name or '').strip()
    if not name:
        raise ValueError('库名称不能为空')
    library = ScenarioPoseLibrary(
        name=name,
        code=_gen_library_code(),
        scene_category=(scene_category or 'custom').strip() or 'custom',
        business_tags=json.dumps(_normalize_business_tags(business_tags), ensure_ascii=False),
        description=(description or '').strip() or None,
        similarity_threshold=float(similarity_threshold or 0.72),
        match_mode=(match_mode or 'angle').strip() or 'angle',
        intent_event=(intent_event or 'pose_intent_match').strip(),
        intent_object=(intent_object or '姿态意图').strip(),
        alert_level=(alert_level or 'warning').strip(),
        is_enabled=is_enabled,
    )
    db.session.add(library)
    db.session.commit()
    return library


def update_library(library_id: int, **kwargs) -> ScenarioPoseLibrary:
    library = ScenarioPoseLibrary.query.get_or_404(library_id)
    if 'name' in kwargs and kwargs['name'] is not None:
        name = str(kwargs['name']).strip()
        if not name:
            raise ValueError('库名称不能为空')
        library.name = name
    if 'scene_category' in kwargs:
        library.scene_category = (kwargs['scene_category'] or 'custom').strip() or 'custom'
    if 'business_tags' in kwargs:
        library.business_tags = json.dumps(_normalize_business_tags(kwargs['business_tags']), ensure_ascii=False)
    if 'description' in kwargs:
        library.description = (kwargs['description'] or '').strip() or None
    if 'similarity_threshold' in kwargs and kwargs['similarity_threshold'] is not None:
        library.similarity_threshold = float(kwargs['similarity_threshold'])
    if 'match_mode' in kwargs and kwargs['match_mode']:
        library.match_mode = str(kwargs['match_mode']).strip()
    if 'intent_event' in kwargs and kwargs['intent_event']:
        library.intent_event = str(kwargs['intent_event']).strip()
    if 'intent_object' in kwargs and kwargs['intent_object']:
        library.intent_object = str(kwargs['intent_object']).strip()
    if 'alert_level' in kwargs and kwargs['alert_level']:
        library.alert_level = str(kwargs['alert_level']).strip()
    if 'is_enabled' in kwargs:
        library.is_enabled = bool(kwargs['is_enabled'])
    library.updated_at = datetime.utcnow()
    db.session.commit()
    return library


def delete_library(library_id: int) -> None:
    library = ScenarioPoseLibrary.query.get_or_404(library_id)
    for entry in ScenarioPoseEntry.query.filter_by(library_id=library_id).all():
        _delete_minio_object(entry.image_path)
    db.session.delete(library)
    db.session.commit()


def list_entries(library_id: int, search: Optional[str] = None) -> List[Dict[str, Any]]:
    ScenarioPoseLibrary.query.get_or_404(library_id)
    query = ScenarioPoseEntry.query.filter_by(library_id=library_id)
    if search:
        kw = f'%{search.strip()}%'
        query = query.filter(ScenarioPoseEntry.name.ilike(kw))
    return [e.to_dict() for e in query.order_by(ScenarioPoseEntry.id.desc()).all()]


def _build_entry_from_keypoints(
    library: ScenarioPoseLibrary,
    name: str,
    keypoints: List[List[float]],
    *,
    source_type: str = 'image',
    image_path: Optional[str] = None,
    image_url: Optional[str] = None,
    extra_rules=None,
    remark: Optional[str] = None,
) -> ScenarioPoseEntry:
    feat = extract_angle_features(keypoints)
    entry = ScenarioPoseEntry(
        library_id=library.id,
        name=(name or '参考姿态').strip(),
        source_type=source_type,
        image_path=image_path,
        image_url=image_url,
        keypoints=json.dumps(keypoints, ensure_ascii=False),
        feature_vector=features_to_json(feat),
        extra_rules=json.dumps(extra_rules, ensure_ascii=False) if extra_rules else None,
        remark=(remark or '').strip() or None,
    )
    db.session.add(entry)
    db.session.commit()
    _refresh_library_entry_count(library.id)
    return entry


def add_entry_from_image(
    library_id: int,
    name: str,
    image_bytes: bytes,
    *,
    remark: Optional[str] = None,
    conf: float = 0.25,
) -> ScenarioPoseEntry:
    library = ScenarioPoseLibrary.query.get_or_404(library_id)
    persons = extract_keypoints_from_image_bytes(image_bytes, conf=conf)
    if not persons:
        raise ValueError('未检测到人体姿态，请更换图片')
    keypoints = persons[0].get('keypoints') or []
    object_name, image_url = _upload_pose_image(library_id, image_bytes)
    return _build_entry_from_keypoints(
        library, name, keypoints,
        source_type='image', image_path=object_name, image_url=image_url, remark=remark,
    )


def add_rule_entry(
    library_id: int,
    name: str,
    extra_rules: dict,
    *,
    remark: Optional[str] = None,
) -> ScenarioPoseEntry:
    library = ScenarioPoseLibrary.query.get_or_404(library_id)
    entry = ScenarioPoseEntry(
        library_id=library.id,
        name=(name or '规则模板').strip(),
        source_type='rule',
        extra_rules=json.dumps(extra_rules or {}, ensure_ascii=False),
        remark=(remark or '').strip() or None,
    )
    db.session.add(entry)
    db.session.commit()
    _refresh_library_entry_count(library.id)
    return entry


def update_entry(entry_id: int, **kwargs) -> ScenarioPoseEntry:
    entry = ScenarioPoseEntry.query.get_or_404(entry_id)
    if 'name' in kwargs and kwargs['name']:
        entry.name = str(kwargs['name']).strip()
    if 'remark' in kwargs:
        entry.remark = (kwargs['remark'] or '').strip() or None
    if 'is_enabled' in kwargs:
        entry.is_enabled = bool(kwargs['is_enabled'])
    if 'extra_rules' in kwargs and kwargs['extra_rules'] is not None:
        entry.extra_rules = json.dumps(kwargs['extra_rules'], ensure_ascii=False)
    entry.updated_at = datetime.utcnow()
    db.session.commit()
    return entry


def delete_entry(entry_id: int) -> None:
    entry = ScenarioPoseEntry.query.get_or_404(entry_id)
    library_id = entry.library_id
    _delete_minio_object(entry.image_path)
    db.session.delete(entry)
    db.session.commit()
    _refresh_library_entry_count(library_id)


def re_extract_entry(entry_id: int, conf: float = 0.25) -> ScenarioPoseEntry:
    entry = ScenarioPoseEntry.query.get_or_404(entry_id)
    if not entry.image_path:
        raise ValueError('该条目无参考图片')
    minio = ModelService.get_minio_client()
    if not minio.bucket_exists(POSE_BUCKET):
        raise ValueError('图片存储不可用')
    response = minio.get_object(POSE_BUCKET, entry.image_path)
    try:
        image_bytes = response.read()
    finally:
        response.close()
        response.release_conn()
    persons = extract_keypoints_from_image_bytes(image_bytes, conf=conf)
    if not persons:
        raise ValueError('未检测到人体姿态')
    keypoints = persons[0].get('keypoints') or []
    feat = extract_angle_features(keypoints)
    entry.keypoints = json.dumps(keypoints, ensure_ascii=False)
    entry.feature_vector = features_to_json(feat)
    entry.updated_at = datetime.utcnow()
    db.session.commit()
    return entry


def extract_preview(image_bytes: bytes, conf: float = 0.25) -> Dict[str, Any]:
    persons = extract_keypoints_from_image_bytes(image_bytes, conf=conf)
    if not persons:
        return {'count': 0, 'persons': []}
    result_persons = []
    for p in persons:
        kps = p.get('keypoints') or []
        feat = extract_angle_features(kps)
        result_persons.append({
            'keypoints': kps,
            'feature_vector': feat,
            'keypointCount': 17,
            'poseType': 'body17',
        })
    return {'count': len(result_persons), 'persons': result_persons}


def match_test(library_id: int, image_bytes: bytes, conf: float = 0.25) -> List[Dict[str, Any]]:
    library = ScenarioPoseLibrary.query.get_or_404(library_id)
    persons = extract_keypoints_from_image_bytes(image_bytes, conf=conf)
    if not persons:
        return []
    entries = ScenarioPoseEntry.query.filter_by(library_id=library_id, is_enabled=True).all()
    results = []
    threshold = float(library.similarity_threshold or 0.72)
    for pi, person in enumerate(persons):
        kps = person.get('keypoints') or []
        best = None
        for entry in entries:
            rules = None
            if entry.extra_rules:
                try:
                    rules = json.loads(entry.extra_rules) if isinstance(entry.extra_rules, str) else entry.extra_rules
                except Exception:
                    rules = None
            sim, _ = match_person_to_entry(
                kps,
                features_from_json(entry.feature_vector),
                match_mode=library.match_mode or 'angle',
                extra_rules=rules,
                source_type=entry.source_type or 'image',
            )
            if best is None or sim > best['similarity']:
                best = {
                    'entry_id': entry.id,
                    'entry_name': entry.name,
                    'similarity': round(sim, 4),
                    'matched': sim >= threshold,
                }
        if best:
            best['person_index'] = pi
            results.append(best)
    return results


def list_scene_templates() -> List[Dict[str, Any]]:
    return [{'key': k, **v} for k, v in SCENE_TEMPLATES.items()]


def import_scene_template(library_id: int, template_key: str) -> ScenarioPoseEntry:
    tpl = SCENE_TEMPLATES.get(template_key)
    if not tpl:
        raise ValueError(f'未知场景模板: {template_key}')
    library = ScenarioPoseLibrary.query.get_or_404(library_id)
    library.scene_category = tpl.get('scene_category', template_key)
    library.intent_event = tpl.get('intent_event')
    library.intent_object = tpl.get('intent_object')
    library.match_mode = tpl.get('match_mode', 'angle')
    library.similarity_threshold = tpl.get('similarity_threshold', 0.72)
    db.session.commit()
    return add_rule_entry(
        library_id,
        name=tpl.get('name') or template_key,
        extra_rules=tpl.get('extra_rules') or {},
        remark=f'内置模板 {template_key}',
    )
