"""姿态意图匹配编排：场景姿态库匹配 → 意图告警。"""
import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from app.services.library_matching_service import parse_business_tags, tags_overlap
from app.utils.pose_intent import (
    extract_angle_features,
    features_from_json,
    match_person_to_entry,
    match_sequence_to_entry,
    visible_keypoint_count,
)
from models import AlgorithmTask, PoseIntentMatchRecord, ScenarioPoseEntry, ScenarioPoseLibrary, db

logger = logging.getLogger(__name__)

EVENT_POSE_INTENT_MATCH = 'pose_intent_match'

# device_id -> event -> last_ts
_SUPPRESS_CACHE: Dict[str, Dict[str, float]] = {}
_SUPPRESS_LOCK = threading.Lock()

# device+task+person -> 最近 N 帧特征序列（DTW 时序匹配）
_TEMPORAL_BUFFER: Dict[str, List[List[float]]] = {}
_TEMPORAL_LOCK = threading.Lock()


def _default_pose_intent_config() -> Dict[str, Any]:
    return {
        'require_person_detection': True,
        'min_keypoint_visible_ratio': 0.35,
        'match_top_k': 1,
        'suppress_same_intent_sec': 10,
        'region_constraint_enabled': False,
        'region_ids': [],
        'draw_skeleton_on_alert': False,
        'temporal_dtw_enabled': False,
        'temporal_window_frames': 6,
        'temporal_dtw_threshold': 0.65,
    }


def load_pose_intent_config(task) -> Dict[str, Any]:
    cfg = _default_pose_intent_config()
    raw = getattr(task, 'pose_intent_config', None)
    if raw:
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else (raw or {})
            if isinstance(parsed, dict):
                cfg.update(parsed)
        except Exception:
            pass
    return cfg


def resolve_pose_libraries(task: AlgorithmTask) -> List[ScenarioPoseLibrary]:
    lib_ids = AlgorithmTask._parse_library_ids(getattr(task, 'pose_library_ids', None))
    if not lib_ids:
        return []
    filter_tags = parse_business_tags(getattr(task, 'matching_business_tags', None))
    libraries = []
    for lib_id in lib_ids:
        lib = ScenarioPoseLibrary.query.get(lib_id)
        if not lib or not lib.is_enabled:
            continue
        lib_tags = []
        if lib.business_tags:
            try:
                lib_tags = json.loads(lib.business_tags) if isinstance(lib.business_tags, str) else lib.business_tags
            except Exception:
                lib_tags = []
        if tags_overlap(lib_tags, filter_tags):
            libraries.append(lib)
    return libraries


def _resolve_threshold(task: AlgorithmTask, library: ScenarioPoseLibrary) -> float:
    task_threshold = getattr(task, 'pose_intent_threshold', None)
    if task_threshold is not None:
        return float(task_threshold)
    return float(library.similarity_threshold or 0.72)


def _should_suppress(device_id: str, event: str, suppress_sec: float) -> bool:
    if suppress_sec <= 0:
        return False
    now = time.time()
    with _SUPPRESS_LOCK:
        bucket = _SUPPRESS_CACHE.setdefault(device_id, {})
        last = bucket.get(event, 0)
        if now - last < suppress_sec:
            return True
        bucket[event] = now
    return False


def _temporal_buffer_key(task_id: Any, device_id: str, person_index: int) -> str:
    return f'{task_id}:{device_id}:{person_index}'


def _push_temporal_feature(
    task_id: Any,
    device_id: str,
    person_index: int,
    feature: List[float],
    max_frames: int,
) -> List[List[float]]:
    key = _temporal_buffer_key(task_id, device_id, person_index)
    with _TEMPORAL_LOCK:
        buf = _TEMPORAL_BUFFER.setdefault(key, [])
        buf.append(feature)
        if len(buf) > max_frames:
            buf[:] = buf[-max_frames:]
        return list(buf)


def _match_with_temporal_dtw(
    task: AlgorithmTask,
    cfg: Dict[str, Any],
    *,
    device_id: str,
    person_index: int,
    keypoints: List[List[float]],
    library: ScenarioPoseLibrary,
    threshold: float,
) -> List[Dict[str, Any]]:
    """多帧 DTW 时序匹配（条目 extra_rules 含 sequence_features）。"""
    feat = extract_angle_features(keypoints)
    if feat is None:
        return []
    window = max(3, int(cfg.get('temporal_window_frames') or 6))
    dtw_threshold = float(cfg.get('temporal_dtw_threshold') or 0.65)
    seq = _push_temporal_feature(getattr(task, 'id', None), device_id, person_index, feat, window)
    if len(seq) < 3:
        return []

    matches: List[Dict[str, Any]] = []
    entries = ScenarioPoseEntry.query.filter_by(library_id=library.id, is_enabled=True).all()
    for entry in entries:
        rules = None
        if entry.extra_rules:
            try:
                rules = json.loads(entry.extra_rules) if isinstance(entry.extra_rules, str) else entry.extra_rules
            except Exception:
                rules = None
        if not rules or not (rules.get('sequence_features') or rules.get('reference_sequence')):
            continue
        sim, ok = match_sequence_to_entry(seq, rules, threshold=dtw_threshold)
        eff_threshold = max(threshold, dtw_threshold)
        if ok and sim >= eff_threshold:
            matches.append({
                'library_id': library.id,
                'library_name': library.name,
                'library_code': library.code,
                'scene_category': library.scene_category,
                'entry_id': entry.id,
                'entry_name': entry.name,
                'similarity': round(sim, 4),
                'threshold': eff_threshold,
                'intent_event': library.intent_event or EVENT_POSE_INTENT_MATCH,
                'intent_object': library.intent_object or '姿态意图',
                'alert_level': library.alert_level or 'warning',
                'person_index': person_index,
                'keypoints': keypoints,
                'match_method': 'dtw',
                'temporal_frames': len(seq),
            })
    return matches


def _person_in_regions(keypoints: List[List[float]], regions: List[Dict[str, Any]]) -> bool:
    if not regions or not keypoints:
        return True
    visible = [kp for kp in keypoints if len(kp) >= 3 and float(kp[2]) >= 0.25]
    if not visible:
        return False
    cx = sum(kp[0] for kp in visible) / len(visible)
    cy = sum(kp[1] for kp in visible) / len(visible)
    for region in regions:
        points = region.get('points') or region.get('polygon') or []
        if not points:
            continue
        try:
            import cv2
            import numpy as np
            poly = np.array(points, dtype=np.float32).reshape(-1, 2)
            if cv2.pointPolygonTest(poly, (float(cx), float(cy)), False) >= 0:
                return True
        except Exception:
            continue
    return False


def match_pose_intent(
    task: AlgorithmTask,
    pose_persons: List[Dict[str, Any]],
    *,
    regions: Optional[List[Dict[str, Any]]] = None,
    device_id: str = '',
) -> List[Dict[str, Any]]:
    if not task or not bool(getattr(task, 'pose_intent_enabled', False)):
        return []
    if not pose_persons:
        return []

    cfg = load_pose_intent_config(task)
    libraries = resolve_pose_libraries(task)
    if not libraries:
        return []

    min_visible = max(4, int(17 * float(cfg.get('min_keypoint_visible_ratio') or 0.35)))
    region_enabled = bool(cfg.get('region_constraint_enabled'))
    top_k = max(1, int(cfg.get('match_top_k') or 1))
    temporal_dtw = bool(cfg.get('temporal_dtw_enabled'))

    all_matches: List[Dict[str, Any]] = []

    for person_index, person in enumerate(pose_persons):
        keypoints = person.get('keypoints') or []
        if visible_keypoint_count(keypoints) < min_visible:
            continue
        if region_enabled and regions and not _person_in_regions(keypoints, regions):
            continue

        person_matches: List[Dict[str, Any]] = []
        for library in libraries:
            threshold = _resolve_threshold(task, library)

            if temporal_dtw:
                person_matches.extend(_match_with_temporal_dtw(
                    task, cfg,
                    device_id=device_id,
                    person_index=person_index,
                    keypoints=keypoints,
                    library=library,
                    threshold=threshold,
                ))

            entries = ScenarioPoseEntry.query.filter_by(
                library_id=library.id, is_enabled=True,
            ).all()
            for entry in entries:
                rules = None
                if entry.extra_rules:
                    try:
                        rules = json.loads(entry.extra_rules) if isinstance(entry.extra_rules, str) else entry.extra_rules
                    except Exception:
                        rules = None
                if rules and (rules.get('sequence_features') or rules.get('reference_sequence')):
                    continue
                sim, _ = match_person_to_entry(
                    keypoints,
                    features_from_json(entry.feature_vector),
                    match_mode=library.match_mode or 'angle',
                    extra_rules=rules,
                    source_type=entry.source_type or 'image',
                )
                if sim >= threshold:
                    person_matches.append({
                        'library_id': library.id,
                        'library_name': library.name,
                        'library_code': library.code,
                        'scene_category': library.scene_category,
                        'entry_id': entry.id,
                        'entry_name': entry.name,
                        'similarity': round(sim, 4),
                        'threshold': threshold,
                        'intent_event': library.intent_event or EVENT_POSE_INTENT_MATCH,
                        'intent_object': library.intent_object or '姿态意图',
                        'alert_level': library.alert_level or 'warning',
                        'person_index': person_index,
                        'keypoints': keypoints,
                        'match_method': 'single',
                    })

        person_matches.sort(key=lambda x: x['similarity'], reverse=True)
        all_matches.extend(person_matches[:top_k])

    return all_matches


def build_intent_alerts(
    task: AlgorithmTask,
    ctx: Dict[str, Any],
    matches: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if not matches:
        return []

    cfg = load_pose_intent_config(task)
    suppress_sec = float(cfg.get('suppress_same_intent_sec') or 10)
    device_id = str(ctx.get('device_id') or '')
    business_tags = parse_business_tags(getattr(task, 'matching_business_tags', None))

    alerts = []
    for match in matches:
        event = match.get('intent_event') or EVENT_POSE_INTENT_MATCH
        if _should_suppress(device_id, event, suppress_sec):
            continue
        information = {
            'match_type': 'pose_intent',
            'library_id': match.get('library_id'),
            'library_name': match.get('library_name'),
            'library_code': match.get('library_code'),
            'scene_category': match.get('scene_category'),
            'entry_id': match.get('entry_id'),
            'entry_name': match.get('entry_name'),
            'similarity': match.get('similarity'),
            'threshold': match.get('threshold'),
            'person_index': match.get('person_index'),
            'alert_level': match.get('alert_level'),
            'match_method': match.get('match_method'),
            'temporal_frames': match.get('temporal_frames'),
            'business_tags': business_tags,
            'pose_result': ctx.get('pose_result'),
            'pose_intent_matches': matches,
            'correlation_id': ctx.get('correlation_id'),
            'frame_number': ctx.get('frame_number'),
            'skeleton_image_path': ctx.get('skeleton_image_path'),
        }
        alerts.append({
            'object': match.get('intent_object') or '姿态意图',
            'event': event,
            'information': information,
            'business_tags': business_tags,
        })
    return alerts


def save_match_records(
    task: AlgorithmTask,
    ctx: Dict[str, Any],
    matches: List[Dict[str, Any]],
) -> None:
    try:
        for match in matches:
            record = PoseIntentMatchRecord(
                task_id=getattr(task, 'id', None),
                task_name=getattr(task, 'task_name', None),
                device_id=str(ctx.get('device_id') or ''),
                device_name=ctx.get('device_name'),
                library_id=match.get('library_id'),
                library_name=match.get('library_name'),
                entry_id=match.get('entry_id'),
                entry_name=match.get('entry_name'),
                similarity=match.get('similarity'),
                intent_event=match.get('intent_event'),
                matched=True,
                pose_snapshot=json.dumps(match.get('keypoints') or [], ensure_ascii=False),
                correlation_id=ctx.get('correlation_id'),
                task_type=getattr(task, 'task_type', None),
            )
            db.session.add(record)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.warning('保存姿态意图匹配记录失败: %s', exc)


def run_intent_matching(task: AlgorithmTask, ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    pose_persons = ctx.get('pose_persons') or []
    regions = ctx.get('regions') or []
    device_id = str(ctx.get('device_id') or '')
    matches = match_pose_intent(task, pose_persons, regions=regions, device_id=device_id)
    if matches:
        save_match_records(task, ctx, matches)
    return matches
