"""
VIDEO → POST 模板推送与调试代理。
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def parse_pipeline(raw) -> Optional[List[Dict[str, Any]]]:
    if raw is None:
        return None
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError('post_pipeline 必须是 JSON 数组')
        return data
    raise ValueError('post_pipeline 类型不支持')


def _admin_headers() -> Dict[str, str]:
    headers = {'Content-Type': 'application/json'}
    token = (os.getenv('POST_ADMIN_TOKEN') or '').strip()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    return headers


def resolve_post_base_url() -> Optional[str]:
    from app.utils.nacos_service_discovery import pick_post_base_url
    return pick_post_base_url()


def _request_post(path: str, *, method: str = 'GET', body: Optional[dict] = None, timeout: float = 15) -> Tuple[int, Any]:
    base = resolve_post_base_url()
    if not base:
        return 503, {'error': 'POST 服务不可用，请检查 POST_BASE_URL 或 Nacos 注册'}
    url = f'{base.rstrip("/")}{path}'
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=_admin_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode('utf-8', errors='replace')
            try:
                return resp.status, json.loads(text) if text else {}
            except json.JSONDecodeError:
                return resp.status, {'raw': text}
    except urllib.error.HTTPError as exc:
        text = exc.read().decode('utf-8', errors='replace')
        try:
            payload = json.loads(text) if text else {'error': exc.reason}
        except json.JSONDecodeError:
            payload = {'error': text or exc.reason}
        return exc.code, payload
    except Exception as exc:
        logger.warning('POST 请求失败 %s %s: %s', method, url, exc)
        return 502, {'error': str(exc)}


def debug_pipeline(body: dict) -> Tuple[int, Any]:
    return _request_post('/debug/pipeline', method='POST', body=body)


def debug_plugin(body: dict) -> Tuple[int, Any]:
    return _request_post('/debug/plugin', method='POST', body=body)


def _task_regions(task) -> List[Dict[str, Any]]:
    from models import DeviceDetectionRegion

    device_ids = []
    for dev in getattr(task, 'devices', None) or []:
        did = getattr(dev, 'id', None)
        if did:
            device_ids.append(str(did))
    if not device_ids:
        return []
    rows = DeviceDetectionRegion.query.filter(
        DeviceDetectionRegion.device_id.in_(device_ids),
        DeviceDetectionRegion.is_enabled.is_(True),
    ).all()
    out = []
    for r in rows:
        points = []
        try:
            raw_pts = json.loads(r.points) if isinstance(r.points, str) else (r.points or [])
            for p in raw_pts or []:
                if isinstance(p, dict):
                    points.append({'x': float(p.get('x', 0)), 'y': float(p.get('y', 0))})
                elif isinstance(p, (list, tuple)) and len(p) >= 2:
                    points.append({'x': float(p[0]), 'y': float(p[1])})
        except Exception:
            points = []
        model_ids = []
        if r.model_ids:
            try:
                model_ids = json.loads(r.model_ids) if isinstance(r.model_ids, str) else list(r.model_ids or [])
            except Exception:
                model_ids = []
        out.append({
            'id': r.id,
            'device_id': r.device_id,
            'region_name': r.region_name,
            'region_type': r.region_type or 'polygon',
            'points': points,
            'is_enabled': bool(r.is_enabled),
            'sort_order': int(r.sort_order or 0),
            'model_ids': model_ids,
        })
    return out


def build_template_from_task(task) -> Dict[str, Any]:
    from app.services.post_plugin_service import inject_pipeline_endpoints

    model_ids = []
    raw_models = getattr(task, 'model_ids', None)
    if raw_models:
        try:
            model_ids = json.loads(raw_models) if isinstance(raw_models, str) else list(raw_models)
        except Exception:
            model_ids = []
    if getattr(task, 'alert_event_enabled', False):
        pipeline = inject_pipeline_endpoints(parse_pipeline(getattr(task, 'post_pipeline', None)))
    else:
        pipeline = None
    return {
        'schema': 'post_task_template.v1',
        'task': {
            'id': int(task.id),
            'task_name': task.task_name,
            'task_type': task.task_type,
            'alert_event': '检测告警',
            'model_ids': model_ids,
            'pipeline': pipeline,
            'post_process_script': getattr(task, 'post_process_script', None) or '',
        },
        'regions': _task_regions(task),
    }


def put_template(task_id: int, *, task=None) -> bool:
    from models import AlgorithmTask

    if task is None:
        task = AlgorithmTask.query.get(task_id)
    if not task:
        return False
    tpl = build_template_from_task(task)
    status, payload = _request_post(f'/v1/tasks/{int(task_id)}/template', method='PUT', body=tpl)
    if status >= 400:
        logger.error('PUT POST 模板失败 task=%s status=%s payload=%s', task_id, status, payload)
        return False
    return True


def push_template_on_start(task) -> bool:
    return put_template(int(task.id), task=task)


def push_template_on_stop(task_id: int) -> bool:
    status, payload = _request_post(f'/v1/tasks/{int(task_id)}/template', method='DELETE')
    if status >= 400:
        logger.warning('DELETE POST 模板失败 task=%s status=%s payload=%s', task_id, status, payload)
        return False
    return True


def refresh_running_tasks_for_device(device_id: str) -> None:
    """区域变更后，为引用该设备的运行中任务重新推送 POST 模板。"""
    from models import AlgorithmTask, Device

    device = Device.query.get(device_id)
    if not device:
        return
    tasks = AlgorithmTask.query.filter(
        AlgorithmTask.devices.contains(device),
        AlgorithmTask.run_status.in_(('running', 'restarting')),
    ).all()
    for task in tasks:
        ok = put_template(task.id, task=task)
        if not ok:
            logger.error(
                '运行中改区域后 PUT POST 模板失败: task_id=%s device_id=%s',
                task.id,
                device_id,
            )


def build_sample_event(task, *, device_id: str = '', frame_width: int = 1920, frame_height: int = 1080) -> Dict[str, Any]:
    dev_id = device_id
    if not dev_id:
        for dev in getattr(task, 'devices', None) or []:
            dev_id = str(getattr(dev, 'id', '') or '')
            if dev_id:
                break
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return {
        'schema': 'infer_event.v1',
        'event_kind': 'infer',
        'correlation_id': f'debug-{task.id}-{int(datetime.now().timestamp())}',
        'task_id': int(task.id),
        'task_name': getattr(task, 'task_name', '') or '',
        'task_type': getattr(task, 'task_type', 'realtime') or 'realtime',
        'device_id': dev_id or 'demo-device',
        'timestamp': now,
        'frame_width': int(frame_width),
        'frame_height': int(frame_height),
        'detections': [
            {
                'bbox': [0.42, 0.38, 0.58, 0.72],
                'class_id': 0,
                'class_name': 'person',
                'confidence': 0.86,
                'track_id': 1,
            },
        ],
    }
