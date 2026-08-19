"""Sentinel 自愈合：不满足调度的组件先打标，再限次修复，耗尽后经网关汇报结果与日志。"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional

import requests

from sentinel.registry_loader import load_components_registry

logger = logging.getLogger('easyaiot-sentinel.remediator')

_UNHEALTHY = {'unavailable', 'unknown', 'degraded'}
_lock = threading.RLock()
_heal_thread: Optional[threading.Thread] = None
_state: Dict[str, Dict[str, Any]] = {}
_state_loaded = False


def _node_id() -> int:
    try:
        return int(os.environ.get('NODE_ID', '0'))
    except ValueError:
        return 0


def _state_path() -> str:
    explicit = os.environ.get('SENTINEL_REMEDIATE_STATE', '').strip()
    if explicit:
        return explicit
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), 'remediation-state.json')


def _max_attempts_default() -> int:
    try:
        return max(1, int(os.environ.get('SENTINEL_HEAL_MAX_ATTEMPTS', '3')))
    except ValueError:
        return 3


def _control_plane_base() -> str:
    """CONTROL_PLANE_URL 指向网关 /admin-api/node/agent，修复接口在同前缀 /sentinel/*。"""
    url = os.environ.get('CONTROL_PLANE_URL', 'http://localhost:48080/admin-api/node/agent')
    base = url.rstrip('/')
    if base.endswith('/agent'):
        base = base[:-len('/agent')]
    return base


def _load_state() -> None:
    global _state, _state_loaded
    if _state_loaded:
        return
    path = _state_path()
    if os.path.isfile(path):
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f) or {}
            if isinstance(data, dict):
                _state = {k: v for k, v in data.items() if isinstance(v, dict)}
        except Exception as exc:
            logger.warning('读取自愈状态失败: %s', exc)
    _state_loaded = True


def _save_state() -> None:
    path = _state_path()
    tmp = path + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(_state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception as exc:
        logger.debug('写入自愈状态失败: %s', exc)


def get_marks() -> Dict[str, Dict[str, Any]]:
    with _lock:
        _load_state()
        return {cid: dict(item) for cid, item in _state.items()}


def snapshot() -> Dict[str, Any]:
    marks = get_marks()
    healing = sum(1 for v in marks.values() if v.get('mark') == 'healing')
    exhausted = sum(1 for v in marks.values() if v.get('mark') == 'exhausted')
    unhealable = sum(1 for v in marks.values() if v.get('mark') == 'unhealable')
    marked = sum(1 for v in marks.values() if v.get('mark') in ('marked', 'healing', 'exhausted', 'unhealable'))
    return {
        'components': marks,
        'summary': {
            'marked': marked,
            'healing': healing,
            'exhausted': exhausted,
            'unhealable': unhealable,
        },
    }


def annotate_components(components: List[Dict[str, Any]]) -> None:
    marks = get_marks()
    for item in components:
        cid = str(item.get('componentId') or '')
        mark = marks.get(cid)
        if not mark:
            continue
        item['healMark'] = mark.get('mark')
        item['healAttempts'] = mark.get('attemptCount') or 0
        item['healMaxAttempts'] = mark.get('maxAttempts') or _max_attempts_default()
        item['healMessage'] = mark.get('lastMessage') or ''


def observe_scan(sentinel: Dict[str, Any]) -> Dict[str, Any]:
    """扫描后打标：不满足调度的期望组件进入自愈队列。"""
    components = sentinel.get('components') or []
    expected_missing = set(sentinel.get('missingExpectedComponents') or [])
    with _lock:
        _load_state()
        now = int(time.time() * 1000)
        reports: List[tuple] = []
        for item in components:
            if not isinstance(item, dict):
                continue
            cid = str(item.get('componentId') or '')
            if not cid:
                continue
            expected = bool(item.get('expected')) or cid in expected_missing
            state = str(item.get('state') or '')
            reason = str(item.get('reason') or '')
            if expected and state in _UNHEALTHY:
                pending = _mark_unhealthy(cid, state, reason, now)
                if pending:
                    reports.append(pending)
            elif state == 'ready':
                _clear_if_healed(cid, now)
        annotate_components(components)
        _save_state()
    for cid, rec, exhausted in reports:
        _report_to_control_plane(cid, rec, exhausted=exhausted)
    return snapshot()


def maybe_start_heal(component_ids: Optional[List[str]] = None) -> None:
    global _heal_thread
    if os.environ.get('SENTINEL_AUTO_REMEDIATE', 'true').strip().lower() not in ('1', 'true', 'yes'):
        return
    with _lock:
        if _heal_thread is not None and _heal_thread.is_alive():
            return
        ids = list(component_ids or [])
        _heal_thread = threading.Thread(
            target=_heal_worker, args=(ids,), name='sentinel-heal', daemon=True)
        _heal_thread.start()


def request_remediation(component_ids: List[str]) -> Dict[str, Any]:
    """兼容旧入口：打标后后台自愈。"""
    observe_scan({'components': [
        {'componentId': cid, 'expected': True, 'state': 'unavailable', 'reason': ''}
        for cid in component_ids
    ], 'missingExpectedComponents': component_ids})
    maybe_start_heal(component_ids)
    return {'requested': True, 'components': list(component_ids)}


def _mark_unhealthy(component_id: str, probe_state: str, reason: str, now_ms: int) -> Optional[tuple]:
    spec = _remediation_spec(component_id)
    current = _state.get(component_id) or {}
    mark = current.get('mark')
    if mark == 'exhausted':
        current['probeState'] = probe_state
        current['reason'] = reason
        current['updatedAt'] = now_ms
        _state[component_id] = current
        return None
    if mark == 'healing' and current.get('inProgress'):
        current['probeState'] = probe_state
        current['reason'] = reason
        _state[component_id] = current
        return None
    max_attempts = int(spec.get('max_attempts') or _max_attempts_default()) if spec else _max_attempts_default()
    if not spec or not spec.get('enabled', True):
        already = mark == 'unhealable' and current.get('exhaustedReported')
        current.update({
            'mark': 'unhealable',
            'probeState': probe_state,
            'reason': reason,
            'attemptCount': int(current.get('attemptCount') or 0),
            'maxAttempts': 0,
            'updatedAt': now_ms,
            'lastMessage': reason or '无可用自愈动作',
        })
        _state[component_id] = current
        if not already:
            current['exhaustedReported'] = True
            return (component_id, dict(current), True)
        return None
    current.update({
        'mark': 'marked' if mark not in ('healing', 'marked') else mark,
        'probeState': probe_state,
        'reason': reason,
        'attemptCount': int(current.get('attemptCount') or 0),
        'maxAttempts': max_attempts,
        'updatedAt': now_ms,
        'action': spec.get('action'),
        'params': spec.get('params') or {},
        'cooldownSec': int(spec.get('cooldown_sec') or 180),
        'logs': list(current.get('logs') or []),
        'exhaustedReported': bool(current.get('exhaustedReported')),
        'inProgress': bool(current.get('inProgress')),
        'lastAttemptAt': current.get('lastAttemptAt') or 0,
    })
    _state[component_id] = current
    return None


def _clear_if_healed(component_id: str, now_ms: int) -> None:
    current = _state.get(component_id)
    if not current:
        return
    if current.get('mark') in ('marked', 'healing', 'exhausted', 'unhealable'):
        logger.info('组件 %s 已恢复可调度，清除自愈标记', component_id)
        current.update({
            'mark': 'healed',
            'probeState': 'ready',
            'updatedAt': now_ms,
            'inProgress': False,
            'lastSuccess': True,
            'lastMessage': '扫描确认已就绪',
        })
        _state[component_id] = current


def _remediation_spec(component_id: str) -> Dict[str, Any]:
    registry = load_components_registry()
    remediation_map = registry.get('remediation') or {}
    spec = remediation_map.get(component_id) if isinstance(remediation_map, dict) else None
    return spec if isinstance(spec, dict) else {}


def _heal_worker(preferred_ids: List[str]) -> None:
    try:
        with _lock:
            _load_state()
            candidates = preferred_ids or list(_state.keys())
        for cid in candidates:
            try:
                _heal_one(cid)
            except Exception as exc:
                logger.warning('自愈异常 component=%s: %s', cid, exc)
    except Exception as exc:
        logger.warning('自愈线程异常: %s', exc)


def _heal_one(component_id: str) -> None:
    spec: Dict[str, Any] = {}
    attempt_no = 0
    with _lock:
        _load_state()
        current = _state.get(component_id) or {}
        mark = current.get('mark')
        if mark in ('exhausted', 'unhealable', 'healed', None):
            return
        if current.get('inProgress'):
            return
        attempt = int(current.get('attemptCount') or 0)
        max_attempts = int(current.get('maxAttempts') or _max_attempts_default())
        if attempt >= max_attempts:
            _exhaust(component_id, current, '已达最大自愈次数')
            snapshot_state = dict(current)
            _save_state()
        else:
            snapshot_state = None
        if snapshot_state is not None:
            pass
        else:
            last_at = float(current.get('lastAttemptAt') or 0)
            cooldown = int(current.get('cooldownSec') or 180)
            if last_at and (time.time() - last_at) < cooldown:
                return
            spec = _remediation_spec(component_id)
            if not spec:
                _exhaust(component_id, current, '无可用自愈动作')
                snapshot_state = dict(current)
                _save_state()
            else:
                current['mark'] = 'healing'
                current['inProgress'] = True
                current['lastAttemptAt'] = time.time()
                _state[component_id] = current
                _save_state()
                attempt_no = attempt + 1
    if snapshot_state is not None:
        _report_to_control_plane(component_id, snapshot_state, exhausted=True)
        return
    if not spec:
        return

    result = _call_control_plane_remediate(component_id, spec)
    success = bool(result.get('success'))
    message = str(result.get('message') or result.get('reason') or ('成功' if success else '失败'))
    logs = result.get('logs') if isinstance(result.get('logs'), list) else []
    now_ms = int(time.time() * 1000)
    log_item = {
        'at': now_ms,
        'attempt': attempt_no,
        'success': success,
        'message': message,
        'output': _trim(result.get('output') or ''),
        'action': spec.get('action'),
    }
    if logs:
        log_item['steps'] = logs[:20]

    exhausted = False
    with _lock:
        current = _state.get(component_id) or {}
        history = list(current.get('logs') or [])
        history.append(log_item)
        current.update({
            'attemptCount': attempt_no,
            'inProgress': False,
            'lastSuccess': success,
            'lastMessage': message,
            'updatedAt': now_ms,
            'logs': history[-10:],
        })
        if success:
            current['mark'] = 'healing'
            current['lastMessage'] = '自愈指令已成功，等待下次扫描确认'
            logger.info('自愈指令成功 component=%s attempt=%s/%s',
                        component_id, attempt_no, current.get('maxAttempts'))
        elif attempt_no >= int(current.get('maxAttempts') or _max_attempts_default()):
            _exhaust(component_id, current, message)
            exhausted = True
        else:
            current['mark'] = 'marked'
            logger.warning('自愈失败 component=%s attempt=%s/%s: %s',
                           component_id, attempt_no, current.get('maxAttempts'), message)
        _state[component_id] = current
        report = dict(current)
        _save_state()
    _report_to_control_plane(component_id, report, exhausted=exhausted)


def _exhaust(component_id: str, current: Dict[str, Any], message: str) -> None:
    current['mark'] = 'exhausted'
    current['inProgress'] = False
    current['lastSuccess'] = False
    current['lastMessage'] = message
    current['updatedAt'] = int(time.time() * 1000)
    current['exhaustedReported'] = True
    _state[component_id] = current
    logger.error('组件 %s 自愈耗尽（%s/%s）: %s',
                 component_id, current.get('attemptCount'), current.get('maxAttempts'), message)


def _call_control_plane_remediate(component_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    node_id = _node_id()
    token = os.environ.get('AGENT_TOKEN', '')
    if not node_id or not token:
        return {'success': False, 'message': 'missing NODE_ID or AGENT_TOKEN'}
    url = f'{_control_plane_base()}/sentinel/remediate'
    payload = {
        'nodeId': node_id,
        'componentId': component_id,
        'action': spec.get('action'),
        'params': spec.get('params') or {},
        'attempt': (_state.get(component_id) or {}).get('attemptCount', 0) + 1,
        'maxAttempts': spec.get('max_attempts') or _max_attempts_default(),
    }
    timeout = int(os.environ.get('SENTINEL_HEAL_TIMEOUT', '600'))
    try:
        resp = requests.post(
            url,
            json=payload,
            headers={'X-Agent-Token': token, 'Content-Type': 'application/json'},
            timeout=timeout,
        )
        body = {}
        try:
            body = resp.json() or {}
        except Exception:
            body = {'msg': resp.text}
        if resp.status_code != 200 or body.get('code', 0) not in (0, '0', None):
            return {
                'success': False,
                'message': str(body.get('msg') or f'HTTP {resp.status_code}'),
                'output': _trim(resp.text),
            }
        data = body.get('data') if isinstance(body.get('data'), dict) else body
        return {
            'success': bool(data.get('success')),
            'message': str(data.get('message') or data.get('reason') or ''),
            'logs': data.get('logs') or data.get('steps') or [],
            'output': _trim(data.get('output') or ''),
        }
    except Exception as exc:
        return {'success': False, 'message': str(exc)}


def _report_to_control_plane(component_id: str, current: Dict[str, Any], *, exhausted: bool) -> None:
    node_id = _node_id()
    token = os.environ.get('AGENT_TOKEN', '')
    if not node_id or not token:
        return
    url = f'{_control_plane_base()}/sentinel/remediate-report'
    payload = {
        'nodeId': node_id,
        'componentId': component_id,
        'mark': current.get('mark'),
        'exhausted': exhausted,
        'success': bool(current.get('lastSuccess')),
        'attemptCount': current.get('attemptCount') or 0,
        'maxAttempts': current.get('maxAttempts') or _max_attempts_default(),
        'probeState': current.get('probeState'),
        'message': current.get('lastMessage') or current.get('reason') or '',
        'action': current.get('action'),
        'logs': current.get('logs') or [],
        'agentToken': token,
    }
    try:
        resp = requests.post(
            url,
            json=payload,
            headers={'X-Agent-Token': token, 'Content-Type': 'application/json'},
            timeout=15,
        )
        if resp.status_code != 200:
            logger.warning('自愈汇报 HTTP %s component=%s', resp.status_code, component_id)
    except Exception as exc:
        logger.warning('自愈汇报失败 component=%s: %s', component_id, exc)


def _trim(text: Any, limit: int = 4000) -> str:
    raw = str(text or '')
    return raw if len(raw) <= limit else raw[:limit] + '...(truncated)'
