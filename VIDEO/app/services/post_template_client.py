"""VIDEO → POST 任务模板推送客户端（启动 PUT / 停止 DELETE / 运行中改区域再 PUT）。"""
from __future__ import annotations

import json
import logging
import os
import random
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)


def post_base_url() -> str:
    return (os.getenv('POST_BASE_URL') or '').strip().rstrip('/')


def post_admin_token() -> str:
    return (os.getenv('POST_ADMIN_TOKEN') or '').strip()


def post_push_enabled() -> bool:
    """有 Nacos healthy 实例或静态 POST_BASE_URL 时启用推送。"""
    return bool(_resolve_bases())


def _headers() -> Dict[str, str]:
    h = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    tok = post_admin_token()
    if tok:
        h['Authorization'] = f'Bearer {tok}'
        h['X-Admin-Token'] = tok
    return h


def _resolve_bases() -> List[str]:
    try:
        from app.utils.nacos_service_discovery import pick_post_base_urls
        urls = list(pick_post_base_urls() or [])
        if urls:
            random.shuffle(urls)
            return urls
    except Exception as e:
        logger.debug('nacos pick post urls: %s', e)
    base = post_base_url()
    return [base] if base else []


def _request(method: str, path: str, body: Optional[dict] = None, retries: int = 3) -> bool:
    """path like /v1/tasks/1/template；对 Nacos 多实例轮询/换实例重试。"""
    bases = _resolve_bases()
    if not bases:
        logger.warning('POST 无可用实例（Nacos/POST_BASE_URL），跳过 %s %s', method, path)
        return False
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode('utf-8')
    last_err: Optional[Exception] = None
    attempt = 0
    while attempt < retries:
        for base in bases:
            attempt += 1
            url = f'{base.rstrip("/")}{path}'
            req = urllib.request.Request(url, data=data, headers=_headers(), method=method)
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if 200 <= resp.status < 300:
                        return True
                    last_err = RuntimeError(f'HTTP {resp.status}')
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code == 404 and method == 'DELETE':
                    return True
            except Exception as e:
                last_err = e
            time.sleep(min(0.5 * attempt, 2.0))
            if attempt >= retries:
                break
    logger.error('POST template %s %s failed after %s tries: %s', method, path, retries, last_err)
    return False


def normalize_points(points: Any) -> List[Dict[str, float]]:
    """Normalize {x,y} / [x,y] list to [{x,y}, ...]."""
    out: List[Dict[str, float]] = []
    if not points:
        return out
    if isinstance(points, str):
        try:
            points = json.loads(points)
        except Exception:
            return out
    if not isinstance(points, list):
        return out
    for p in points:
        if isinstance(p, dict) and 'x' in p and 'y' in p:
            out.append({'x': float(p['x']), 'y': float(p['y'])})
        elif isinstance(p, (list, tuple)) and len(p) >= 2:
            out.append({'x': float(p[0]), 'y': float(p[1])})
    return out


def parse_pipeline(raw: Any) -> List[dict]:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


def build_post_task_template(task) -> Dict[str, Any]:
    """Assemble post_task_template.v1 snapshot from AlgorithmTask."""
    from models import DeviceDetectionRegion

    model_ids: List[int] = []
    if getattr(task, 'model_ids', None):
        try:
            raw = task.model_ids
            model_ids = json.loads(raw) if isinstance(raw, str) else list(raw or [])
        except Exception:
            model_ids = []

    pipeline = parse_pipeline(getattr(task, 'post_pipeline', None))
    try:
        from app.services.post_plugin_service import inject_pipeline_endpoints
        pipeline = inject_pipeline_endpoints(pipeline)
    except Exception as e:
        logger.warning('inject_pipeline_endpoints: %s', e)

    devices = list(getattr(task, 'devices', None) or [])
    device_ids = [d.id for d in devices]
    regions_out: List[dict] = []
    if device_ids:
        rows = DeviceDetectionRegion.query.filter(
            DeviceDetectionRegion.device_id.in_(device_ids),
            DeviceDetectionRegion.is_enabled.is_(True),
        ).all()
        for r in rows:
            pts = []
            try:
                pts = json.loads(r.points) if isinstance(r.points, str) else (r.points or [])
            except Exception:
                pts = []
            r_model_ids = []
            if r.model_ids:
                try:
                    r_model_ids = json.loads(r.model_ids) if isinstance(r.model_ids, str) else list(r.model_ids)
                except Exception:
                    r_model_ids = []
            regions_out.append({
                'id': r.id,
                'device_id': r.device_id,
                'region_name': r.region_name,
                'region_type': r.region_type or 'polygon',
                'points': normalize_points(pts),
                'is_enabled': bool(r.is_enabled),
                'sort_order': int(r.sort_order or 0),
                'model_ids': r_model_ids,
            })

    task_body: Dict[str, Any] = {
        'id': task.id,
        'task_name': task.task_name,
        'task_type': task.task_type or 'realtime',
        'alert_event': '检测告警',
        'model_ids': model_ids,
        'post_process_script': getattr(task, 'post_process_script', None) or 'post_process.py',
    }
    if pipeline:
        task_body['pipeline'] = pipeline

    return {
        'schema': 'post_task_template.v1',
        'task': task_body,
        'regions': regions_out,
    }


def put_template(task_id: int, body: Optional[dict] = None, task=None) -> bool:
    if not post_push_enabled():
        return True
    if body is None:
        if task is None:
            from models import AlgorithmTask
            task = AlgorithmTask.query.get(task_id)
        if task is None:
            logger.warning('put_template: task %s not found', task_id)
            return False
        body = build_post_task_template(task)
    ok = _request('PUT', f'/v1/tasks/{task_id}/template', body)
    if ok:
        logger.info('POST template upserted task_id=%s regions=%s', task_id, len(body.get('regions') or []))
    return ok


def delete_template(task_id: int) -> bool:
    if not post_push_enabled():
        return True
    ok = _request('DELETE', f'/v1/tasks/{task_id}/template')
    if ok:
        logger.info('POST template deleted task_id=%s', task_id)
    return ok


def refresh_running_tasks_for_device(device_id: str) -> None:
    """§5.5.1: after region change, re-PUT templates for running tasks referencing the device."""
    if not post_push_enabled():
        return
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
                task.id, device_id,
            )


def push_template_on_start(task) -> bool:
    if not post_push_enabled():
        return True
    return put_template(task.id, task=task)


def push_template_on_stop(task_id: int) -> bool:
    if not post_push_enabled():
        return True
    return delete_template(task_id)


def _http_json(method: str, path: str, body: Optional[dict] = None, timeout: float = 15.0) -> Dict[str, Any]:
    """对 POST 发一次请求并解析 JSON；失败抛 RuntimeError（含状态与正文）。"""
    bases = _resolve_bases()
    if not bases:
        raise RuntimeError('POST 无可用实例（Nacos/POST_BASE_URL）')
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode('utf-8')
    last_err: Optional[Exception] = None
    for base in bases:
        url = f'{base.rstrip("/")}{path}'
        req = urllib.request.Request(url, data=data, headers=_headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode('utf-8') if resp else ''
                try:
                    payload = json.loads(raw) if raw else {}
                except Exception:
                    payload = {'raw': raw}
                return {'ok': True, 'status': int(resp.status), 'data': payload, 'base': base}
        except urllib.error.HTTPError as e:
            raw = ''
            try:
                raw = e.read().decode('utf-8')
            except Exception:
                pass
            try:
                payload = json.loads(raw) if raw else {}
            except Exception:
                payload = {'raw': raw or str(e)}
            # 404/503 等换实例；400 业务错误直接返回
            if e.code in (400, 422):
                return {'ok': False, 'status': e.code, 'data': payload, 'base': base, 'error': payload.get('error') or raw or str(e)}
            last_err = e
            if e.code == 404:
                # debug 未开时常 404
                return {
                    'ok': False,
                    'status': e.code,
                    'data': payload,
                    'base': base,
                    'error': 'POST 调试接口不可用（需 POST_DEBUG_HTTP=true）',
                }
        except Exception as e:
            last_err = e
    raise RuntimeError(f'POST 请求失败 {method} {path}: {last_err}')


def debug_pipeline(body: dict) -> Dict[str, Any]:
    """代理 POST /debug/pipeline（需目标实例 POST_DEBUG_HTTP=true）。"""
    if not isinstance(body, dict):
        raise ValueError('body 必须是对象')
    return _http_json('POST', '/debug/pipeline', body)
