"""人脸/车牌库匹配编排：按业务标签确定库范围、执行匹配、命中后落告警。"""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Type

import cv2
import numpy as np

from app.services.alert_consumer_service import upload_image_to_minio
from app.services.alert_service import create_alert
from models import (
    AlgorithmTask,
    Alert,
    FaceLibrary,
    FaceMatchRecord,
    PlateEntry,
    PlateLibrary,
    PlateMatchRecord,
    db,
)

logger = logging.getLogger(__name__)

EVENT_FACE_LIBRARY_MATCH = 'face_library_match'
EVENT_PLATE_LIBRARY_MATCH = 'plate_library_match'


def parse_business_tags(raw) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return _dedupe_tags([str(x).strip() for x in parsed if str(x).strip()])
        except json.JSONDecodeError:
            pass
        return _dedupe_tags([p.strip() for p in text.split(',') if p.strip()])
    if isinstance(raw, list):
        return _dedupe_tags([str(x).strip() for x in raw if str(x).strip()])
    return []


def _dedupe_tags(tags: List[str]) -> List[str]:
    return list(dict.fromkeys(tags))


def tags_overlap(lib_tags: List[str], filter_tags: List[str]) -> bool:
    if not filter_tags:
        return True
    if not lib_tags:
        return False
    lib_set = {t.lower() for t in lib_tags}
    return any(t.lower() in lib_set for t in filter_tags)


def _task_library_ids(task: AlgorithmTask, library_model: Type) -> List[int]:
    if library_model is FaceLibrary:
        raw = getattr(task, 'face_library_ids', None)
    else:
        raw = getattr(task, 'plate_library_ids', None)
    return AlgorithmTask._parse_library_ids(raw)


def resolve_matching_libraries(
    library_model: Type,
    *,
    task: Optional[AlgorithmTask],
) -> List[Any]:
    """根据任务配置的库 ID 列表确定待检索库（多库依次匹配，命中即停）。"""
    if task is None:
        return []

    task_library_ids = _task_library_ids(task, library_model)
    if not task_library_ids:
        return []

    libs = []
    for lib_id in task_library_ids:
        lib = library_model.query.get(lib_id)
        if lib and lib.is_enabled:
            libs.append(lib)
    return libs


def _load_task(task_id: Optional[int]) -> Optional[AlgorithmTask]:
    if not task_id:
        return None
    try:
        return AlgorithmTask.query.get(int(task_id))
    except (TypeError, ValueError):
        return None


def _library_tags(library) -> List[str]:
    return parse_business_tags(getattr(library, 'business_tags', None))


def _resolve_correlation_id(payload: Dict[str, Any]) -> Optional[str]:
    cid = payload.get('correlationId') or payload.get('correlation_id')
    if cid is None:
        return None
    cid = str(cid).strip()
    return cid or None


def _create_match_alert(
    *,
    event: str,
    object_label: str,
    device_id: str,
    device_name: str,
    image_path: Optional[str],
    task_id: Optional[int],
    task_name: Optional[str],
    task_type: Optional[str],
    business_tags: List[str],
    information: Dict[str, Any],
    correlation_id: Optional[str] = None,
) -> Optional[int]:
    """匹配成功后写入告警库，并上传 MinIO 供列表展示。"""
    try:
        if correlation_id:
            information = {**information, 'correlation_id': correlation_id}
        alert_dict = create_alert({
            'object': object_label,
            'event': event,
            'device_id': device_id,
            'device_name': device_name or device_id,
            'image_path': image_path,
            'task_id': task_id,
            'task_name': task_name,
            'task_type': task_type or 'realtime',
            'business_tags': business_tags,
            'information': information,
            'correlation_id': correlation_id,
        })
        alert_id = alert_dict.get('id')
        if alert_id and image_path:
            minio_path = upload_image_to_minio(image_path, alert_id, device_id)
            if minio_path:
                alert = Alert.query.get(alert_id)
                if alert:
                    alert.image_url = minio_path
                    db.session.commit()
        return alert_id
    except Exception as exc:
        logger.error('创建库匹配告警失败: %s', exc, exc_info=True)
        return None


def match_face_across_libraries(
    libraries: List[FaceLibrary],
    image_path: str,
    threshold: Optional[float],
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[FaceLibrary]]:
    from app.services.face_recognition_service import get_face_recognition_service

    if not libraries or not image_path:
        return False, None, None

    image = cv2.imread(image_path)
    if image is None:
        logger.warning('人脸匹配图片无法读取: %s', image_path)
        return False, None, None

    service = get_face_recognition_service()
    best_result: Optional[Dict[str, Any]] = None
    best_library: Optional[FaceLibrary] = None
    best_similarity = -1.0

    for library in libraries:
        use_threshold = float(
            threshold if threshold is not None else (library.similarity_threshold or 0.55)
        )
        try:
            result = service.match_image_file_in_library(library.id, image, use_threshold)
        except Exception as exc:
            logger.warning('人脸库 %s 匹配失败: %s', library.id, exc)
            continue
        if not result.get('matched'):
            continue
        best_match = result.get('best_match') or {}
        sim = float(best_match.get('similarity') or 0)
        if sim > best_similarity:
            best_similarity = sim
            best_result = result
            best_library = library

    if best_result and best_library:
        return True, best_result, best_library
    return False, None, None


def match_plate_across_libraries(
    libraries: List[PlateLibrary],
    plate_no: str,
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[PlateLibrary]]:
    from app.services.plate_library_service import match_plate_in_library, _normalize_plate_no

    plate_no = _normalize_plate_no(plate_no)
    if not libraries or not plate_no:
        return False, None, None

    for library in libraries:
        result = match_plate_in_library(library.id, plate_no)
        if result.get('matched'):
            return True, result, library
    return False, None, None


def process_face_matching_message(payload: Dict[str, Any]) -> FaceMatchRecord:
    task_id = payload.get('taskId') or payload.get('task_id')
    task = _load_task(task_id)
    if not task:
        raise ValueError('任务不存在或未配置人脸库')
    threshold = payload.get('threshold') or payload.get('faceMatchingThreshold')

    libraries = resolve_matching_libraries(FaceLibrary, task=task)
    if not libraries:
        raise ValueError('任务未配置有效的人脸库')

    face_image_path = payload.get('faceImagePath') or payload.get('face_image_path')
    device_id = str(payload.get('deviceId') or payload.get('device_id') or '')
    device_name = payload.get('deviceName') or payload.get('device_name')
    task_name = payload.get('taskName') or payload.get('task_name')
    task_type = payload.get('taskType') or payload.get('task_type')
    correlation_id = _resolve_correlation_id(payload)
    source_event = payload.get('sourceEvent') or payload.get('source_event')

    matched = False
    best_match = None
    matched_library = None
    business_tags: List[str] = []
    candidates_json = None
    alert_id = None

    if libraries and face_image_path:
        matched, match_result, matched_library = match_face_across_libraries(
            libraries, face_image_path, threshold,
        )
        if match_result:
            best_match = match_result.get('best_match')
            candidates_json = json.dumps(match_result.get('candidates') or [], ensure_ascii=False)
        if matched and matched_library:
            business_tags = _library_tags(matched_library)
            person_name = (best_match or {}).get('person_name') or (best_match or {}).get('label') or '未知人员'
            alert_id = _create_match_alert(
                event=EVENT_FACE_LIBRARY_MATCH,
                object_label=person_name,
                device_id=device_id,
                device_name=device_name or device_id,
                image_path=face_image_path,
                task_id=task_id,
                task_name=task_name,
                task_type=task_type,
                business_tags=business_tags,
                correlation_id=correlation_id,
                information={
                    'match_type': 'face',
                    'source_event': source_event,
                    'library_id': matched_library.id,
                    'library_name': matched_library.name,
                    'library_code': matched_library.code,
                    'business_tags': business_tags,
                    'matched_person_name': person_name,
                    'matched_person_code': (best_match or {}).get('person_code'),
                    'matched_face_entry_id': (best_match or {}).get('face_entry_id'),
                    'similarity': (best_match or {}).get('similarity'),
                    'threshold': match_result.get('threshold') if match_result else threshold,
                    'face_image_path': face_image_path,
                },
            )

    record = FaceMatchRecord(
        task_id=task_id,
        task_name=task_name,
        device_id=device_id,
        device_name=device_name,
        library_id=matched_library.id if matched_library else None,
        library_name=matched_library.name if matched_library else payload.get('libraryName'),
        face_image_path=face_image_path,
        matched=matched,
        matched_person_name=(best_match or {}).get('person_name') or (best_match or {}).get('label'),
        matched_person_code=(best_match or {}).get('person_code'),
        matched_face_entry_id=(best_match or {}).get('face_entry_id'),
        similarity=(best_match or {}).get('similarity'),
        threshold=threshold,
        candidates=candidates_json,
        alert_id=alert_id,
        correlation_id=correlation_id,
        task_type=task_type,
        status='success',
    )
    db.session.add(record)
    db.session.commit()
    return record


def process_plate_matching_message(payload: Dict[str, Any]) -> PlateMatchRecord:
    task_id = payload.get('taskId') or payload.get('task_id')
    task = _load_task(task_id)
    if not task:
        raise ValueError('任务不存在或未配置车牌库')
    plate_no = payload.get('plateNo') or payload.get('plate_no') or ''

    libraries = resolve_matching_libraries(PlateLibrary, task=task)
    if not libraries:
        raise ValueError('任务未配置有效的车牌库')

    device_id = str(payload.get('deviceId') or payload.get('device_id') or '')
    device_name = payload.get('deviceName') or payload.get('device_name')
    task_name = payload.get('taskName') or payload.get('task_name')
    task_type = payload.get('taskType') or payload.get('task_type')
    plate_image_path = payload.get('plateImagePath') or payload.get('plate_image_path')
    plate_color = payload.get('plateColor') or payload.get('plate_color')
    correlation_id = _resolve_correlation_id(payload)

    matched = False
    match_result = None
    matched_library = None
    entry = None
    business_tags: List[str] = []
    alert_id = None

    if libraries and plate_no:
        matched, match_result, matched_library = match_plate_across_libraries(libraries, plate_no)
        entry = (match_result or {}).get('entry')
        if matched and matched_library:
            business_tags = _library_tags(matched_library)
            owner_name = (entry or {}).get('owner_name') or plate_no
            alert_id = _create_match_alert(
                event=EVENT_PLATE_LIBRARY_MATCH,
                object_label=plate_no,
                device_id=device_id,
                device_name=device_name or device_id,
                image_path=plate_image_path,
                task_id=task_id,
                task_name=task_name,
                task_type=task_type,
                business_tags=business_tags,
                correlation_id=correlation_id,
                information={
                    'match_type': 'plate',
                    'library_id': matched_library.id,
                    'library_name': matched_library.name,
                    'library_code': matched_library.code,
                    'business_tags': business_tags,
                    'plate_no': plate_no,
                    'plate_color': plate_color,
                    'matched_owner_name': owner_name,
                    'matched_plate_entry_id': (entry or {}).get('id'),
                    'detect_conf': payload.get('detectConf') or payload.get('detect_conf'),
                    'plate_image_path': plate_image_path,
                },
            )

    record = PlateMatchRecord(
        task_id=task_id,
        task_name=task_name,
        device_id=device_id,
        device_name=device_name,
        library_id=matched_library.id if matched_library else None,
        library_name=matched_library.name if matched_library else payload.get('libraryName'),
        plate_no=plate_no or None,
        plate_color=plate_color,
        plate_image_path=plate_image_path,
        matched=matched,
        matched_plate_entry_id=(entry or {}).get('id') if entry else None,
        matched_owner_name=(entry or {}).get('owner_name') if entry else None,
        detect_conf=payload.get('detectConf') or payload.get('detect_conf'),
        alert_id=alert_id,
        correlation_id=correlation_id,
        task_type=task_type,
        status='success',
    )
    db.session.add(record)
    db.session.commit()
    return record
