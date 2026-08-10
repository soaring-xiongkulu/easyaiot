"""
算法任务 AI 后处理脚本加载与执行。
用户在工作区编写 post_process.py，实现 process(ctx) 函数。
人体姿态分析在 iot-sink Worker 内异步执行，不占用算法任务进程算力。
"""
from __future__ import annotations

import importlib.util
import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_MODULE_CACHE: Dict[str, Any] = {}
_MODULE_MTIME: Dict[str, float] = {}
_CACHE_LOCK = threading.Lock()
_STATE: Dict[str, Dict[str, Any]] = {}


def get_workspace_root() -> Path:
    env_root = (os.getenv('POST_PROCESS_WORKSPACE_ROOT') or '').strip()
    if env_root:
        return Path(env_root).resolve()
    video_root = Path(__file__).resolve().parents[2]
    return (video_root.parent / '.scripts' / 'docker' / 'vscode_data' / 'workspaces').resolve()


def get_task_workspace_dir(task_id: int) -> Path:
    return get_workspace_root() / f'task_{task_id}'


def get_task_script_path(task_id: int, script_name: str = 'post_process.py') -> Path:
    return get_task_workspace_dir(task_id) / script_name


def task_needs_sink_processing(task_config: Any) -> bool:
    """任务是否需要投递 iot-sink（AI 后处理脚本和/或人体姿态分析/姿态意图分析）。"""
    if not task_config:
        return False
    return bool(getattr(task_config, 'post_process_enabled', False)) or bool(
        getattr(task_config, 'pose_analysis_enabled', False)
    ) or bool(getattr(task_config, 'pose_intent_enabled', False))


def _serialize_detection(det: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'class_id': det.get('class_id'),
        'class_name': det.get('class_name'),
        'confidence': float(det.get('confidence', 0)),
        'bbox': list(det.get('bbox') or []),
        'track_id': det.get('track_id', 0),
        'is_cached': bool(det.get('is_cached', False)),
        'first_seen_time': det.get('first_seen_time'),
        'duration': float(det.get('duration', 0) or 0),
    }


def build_task_context(
    task_config: Any,
    *,
    device_id: str,
    device_name: str,
    frame_number: int,
    timestamp: float,
    detections: List[Dict[str, Any]],
    tracked_detections: Optional[List[Dict[str, Any]]] = None,
    regions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """构建算法任务通用入参，供 iot-sink Worker 后处理使用。"""
    task_id = getattr(task_config, 'id', None)
    state_key = f'task_{task_id}' if task_id is not None else 'unknown'
    state = _STATE.setdefault(state_key, {})

    tracked = tracked_detections if tracked_detections is not None else detections
    from app.utils.alert_class_filter import parse_alert_class_names
    pose_enabled = bool(getattr(task_config, 'pose_analysis_enabled', False)) or bool(
        getattr(task_config, 'pose_intent_enabled', False)
    )
    return {
        'task_id': task_id,
        'task_name': getattr(task_config, 'task_name', ''),
        'task_code': getattr(task_config, 'task_code', ''),
        'task_type': getattr(task_config, 'task_type', 'realtime'),
        'device_id': device_id,
        'device_name': device_name,
        'frame_number': frame_number,
        'timestamp': timestamp,
        'detections': [_serialize_detection(d) for d in detections],
        'tracked_detections': [_serialize_detection(d) for d in tracked],
        'tracking_enabled': bool(getattr(task_config, 'tracking_enabled', False)),
        'regions': regions or [],
        'state': state,
        'model_ids': _parse_model_ids(getattr(task_config, 'model_ids', None)),
        'alert_class_names': parse_alert_class_names(getattr(task_config, 'alert_class_names', None)),
        'pose_analysis_enabled': pose_enabled,
        'pose_intent_enabled': bool(getattr(task_config, 'pose_intent_enabled', False)),
        'pose_persons': [],
        'pose_result': None,
        'pose_intent_matches': [],
    }


def _parse_model_ids(raw) -> List[int]:
    if not raw:
        return []
    try:
        import json
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(parsed, list):
            return [int(x) for x in parsed if x is not None and str(x).strip() != '']
    except Exception:
        pass
    return []


def load_regions_for_device(device_id: str) -> List[Dict[str, Any]]:
    try:
        from models import DeviceDetectionRegion
        regions = DeviceDetectionRegion.query.filter_by(
            device_id=device_id,
            is_enabled=True,
        ).order_by(DeviceDetectionRegion.sort_order).all()
        return [r.to_dict() for r in regions]
    except Exception as exc:
        logger.debug('加载设备检测区域失败 device=%s: %s', device_id, exc)
        return []


def _load_process_module(task_id: int, script_name: str):
    script_path = get_task_script_path(task_id, script_name)
    if not script_path.is_file():
        return None

    cache_key = str(script_path)
    mtime = script_path.stat().st_mtime
    with _CACHE_LOCK:
        cached = _MODULE_CACHE.get(cache_key)
        if cached is not None and _MODULE_MTIME.get(cache_key) == mtime:
            return cached

    spec = importlib.util.spec_from_file_location(f'post_process_task_{task_id}', script_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    with _CACHE_LOCK:
        _MODULE_CACHE[cache_key] = module
        _MODULE_MTIME[cache_key] = mtime
    return module


def apply_pose_analysis_in_worker(
    task_config: Any,
    ctx: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """在 iot-sink Worker 内对告警图执行人体姿态分析，结果写入 ctx。"""
    if not task_config or not (
        bool(getattr(task_config, 'pose_analysis_enabled', False))
        or bool(getattr(task_config, 'pose_intent_enabled', False))
    ):
        return None

    from app.utils.pose_analysis import (
        build_pose_result_payload,
        load_pose_config_from_task,
        run_pose_analysis_from_image_path,
        serialize_pose_persons,
        should_run_pose_analysis,
    )

    cfg = load_pose_config_from_task(task_config)
    frame_number = int(ctx.get('frame_number') or 0)
    detections = ctx.get('detections') or []
    if not should_run_pose_analysis(cfg, frame_number=frame_number, detections=detections):
        return None

    image_path = ctx.get('alert_image_path')
    if not image_path:
        logger.warning('任务 %s 姿态分析跳过：无 alert_image_path', getattr(task_config, 'id', None))
        return None

    started = time.time()
    persons = run_pose_analysis_from_image_path(image_path, cfg)
    elapsed_ms = (time.time() - started) * 1000
    if elapsed_ms > 200:
        logger.info('任务 %s 姿态分析耗时 %.1fms', getattr(task_config, 'id', None), elapsed_ms)

    ctx['pose_persons'] = serialize_pose_persons(persons)
    ctx['pose_result'] = build_pose_result_payload(persons)
    return {
        'pose_count': len(persons),
        'pose_result': ctx['pose_result'],
    }


def _run_user_post_process_script(task_config: Any, ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not bool(getattr(task_config, 'post_process_enabled', False)):
        return None

    task_id = getattr(task_config, 'id', None)
    if task_id is None:
        return None

    script_name = (getattr(task_config, 'post_process_script', None) or 'post_process.py').strip()
    module = _load_process_module(task_id, script_name)
    if module is None:
        return None

    process_fn = getattr(module, 'process', None)
    if not callable(process_fn):
        logger.warning('任务 %s 后处理脚本缺少 process(ctx) 函数', task_id)
        return None

    started = time.time()
    try:
        result = process_fn(ctx)
    except Exception as exc:
        logger.error('任务 %s 后处理执行失败: %s', task_id, exc, exc_info=True)
        return None
    finally:
        elapsed_ms = (time.time() - started) * 1000
        if elapsed_ms > 200:
            logger.info('任务 %s 后处理耗时 %.1fms', task_id, elapsed_ms)

    if result is None:
        return None
    if not isinstance(result, dict):
        logger.warning('任务 %s 后处理返回值必须是 dict，实际: %s', task_id, type(result).__name__)
        return None
    return result


def apply_pose_intent_matching(
    task_config: Any,
    ctx: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """场景姿态库意图匹配，命中后构造 alerts。"""
    if not task_config or not bool(getattr(task_config, 'pose_intent_enabled', False)):
        return None

    from app.services.pose_intent_matching_service import (
        build_intent_alerts,
        run_intent_matching,
    )
    from app.utils.pose_intent_visual import maybe_draw_skeleton_on_alert_image

    matches = run_intent_matching(task_config, ctx)
    if not matches:
        return None

    ctx['pose_intent_matches'] = matches
    maybe_draw_skeleton_on_alert_image(task_config, ctx)
    alerts = build_intent_alerts(task_config, ctx, matches)
    result: Dict[str, Any] = {
        'pose_intent_matches': matches,
        'publish_sink': True,
    }
    if alerts:
        result['alerts'] = alerts
        result['suppress_default_alert'] = True
    return result


def run_post_process(
    task_config: Any,
    ctx: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """iot-sink Worker 入口：先异步姿态分析，再意图匹配，再执行用户后处理脚本。"""
    if not task_config:
        return None

    pose_enabled = bool(getattr(task_config, 'pose_analysis_enabled', False)) or bool(
        getattr(task_config, 'pose_intent_enabled', False)
    )
    intent_enabled = bool(getattr(task_config, 'pose_intent_enabled', False))
    pp_enabled = bool(getattr(task_config, 'post_process_enabled', False))
    if not pose_enabled and not pp_enabled and not intent_enabled:
        return None

    merged: Dict[str, Any] = {}

    if pose_enabled:
        pose_part = apply_pose_analysis_in_worker(task_config, ctx)
        if pose_part:
            merged.update(pose_part)

    if intent_enabled:
        intent_part = apply_pose_intent_matching(task_config, ctx)
        if intent_part:
            for key, value in intent_part.items():
                if key == 'alerts' and 'alerts' in merged:
                    existing = merged.get('alerts') or []
                    if isinstance(existing, list) and isinstance(value, list):
                        merged['alerts'] = existing + value
                    else:
                        merged['alerts'] = value
                else:
                    merged[key] = value

    if pp_enabled:
        user_result = _run_user_post_process_script(task_config, ctx)
        if user_result:
            for key, value in user_result.items():
                if key == 'alerts' and 'alerts' in merged:
                    existing = merged.get('alerts') or []
                    if isinstance(existing, list) and isinstance(value, list):
                        merged['alerts'] = existing + value
                    else:
                        merged['alerts'] = value
                else:
                    merged[key] = value

    if not merged:
        return None

    if (pose_enabled or intent_enabled) and not pp_enabled:
        merged.setdefault('publish_sink', True)
    return merged


def enqueue_post_process_request(
    task_config: Any,
    *,
    device_id: str,
    device_name: str,
    frame_number: int,
    timestamp: float,
    detections: List[Dict[str, Any]],
    tracked_detections: Optional[List[Dict[str, Any]]] = None,
    alert_image_path: Optional[str] = None,
) -> None:
    """将检测结果 HTTP 投递至 iot-sink 入队，姿态分析在 Worker 内异步执行。"""
    if not task_needs_sink_processing(task_config):
        return
    regions = load_regions_for_device(device_id)
    ctx = build_task_context(
        task_config,
        device_id=device_id,
        device_name=device_name,
        frame_number=frame_number,
        timestamp=timestamp,
        detections=detections,
        tracked_detections=tracked_detections,
        regions=regions,
    )
    if alert_image_path:
        ctx['alert_image_path'] = alert_image_path
    try:
        from app.services.post_process_sink_client import publish_post_process_request_async
        publish_post_process_request_async(ctx, alert_image_path=alert_image_path)
    except Exception as exc:
        logger.warning('后处理请求投递 iot-sink 失败: %s', exc)


def apply_post_process(
    task_config: Any,
    *,
    device_id: str,
    device_name: str,
    frame_number: int,
    timestamp: float,
    detections: List[Dict[str, Any]],
    tracked_detections: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """兼容旧调用：仅投递 iot-sink 请求，不在算法进程内执行后处理。"""
    enqueue_post_process_request(
        task_config,
        device_id=device_id,
        device_name=device_name,
        frame_number=frame_number,
        timestamp=timestamp,
        detections=detections,
        tracked_detections=tracked_detections,
    )
    return None


def resolve_post_process_outcome(
    pp_result: Optional[Dict[str, Any]],
    detections: List[Dict[str, Any]],
    *,
    alert_class_names: Any = None,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """解析后处理返回值，得到用于默认告警的检测列表与自定义告警。"""
    from app.utils.alert_class_filter import filter_detections_for_alert

    if not pp_result:
        return filter_detections_for_alert(detections, alert_class_names), []

    detections_for_alert = detections
    if pp_result.get('suppress_default_alert'):
        detections_for_alert = []
    elif pp_result.get('detections') is not None:
        detections_for_alert = pp_result.get('detections') or []

    detections_for_alert = filter_detections_for_alert(
        detections_for_alert,
        alert_class_names,
    )

    custom_alerts = pp_result.get('alerts') or []
    if custom_alerts and not isinstance(custom_alerts, list):
        custom_alerts = []
    return detections_for_alert, custom_alerts
