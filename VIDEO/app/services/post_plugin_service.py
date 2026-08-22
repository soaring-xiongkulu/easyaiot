"""
POST 外置插件登记与 pipeline endpoint 注入。
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

BUILTIN_PLUGIN_IDS = frozenset({
    'region_gate',
    'default_pass',
    'user_script',
    'line_cross',
    'region_enter_exit',
    'dwell_timer',
    'headcount_gate',
})

BUILTIN_PLUGIN_CATALOG: List[Dict[str, Any]] = [
    {
        'id': 'region_gate',
        'name': '区域闸门',
        'kinds': ['filter'],
        'builtin': True,
        'description': '按设备检测区域过滤检测框，区域外目标丢弃。',
        'params_schema': {
            'type': 'object',
            'properties': {
                'hit_mode': {
                    'type': 'string',
                    'enum': ['center', 'any', 'all'],
                    'default': 'center',
                    'title': '命中模式',
                },
            },
        },
    },
    {
        'id': 'line_cross',
        'name': '越线检测',
        'kinds': ['filter', 'decide'],
        'builtin': True,
        'description': '检测目标越过 line 类型检测线时触发（需开启目标追踪）。',
        'params_schema': {
            'type': 'object',
            'properties': {
                'direction': {
                    'type': 'string',
                    'enum': ['both', 'forward', 'backward'],
                    'default': 'both',
                    'title': '方向',
                },
                'sample_point': {
                    'type': 'string',
                    'enum': ['center', 'bottom'],
                    'default': 'center',
                    'title': '采样点',
                },
                'target_classes': {'type': 'array', 'items': {'type': 'string'}, 'title': '目标类别'},
            },
        },
    },
    {
        'id': 'region_enter_exit',
        'name': '区域进出',
        'kinds': ['filter', 'decide'],
        'builtin': True,
        'description': '检测目标进入或离开多边形区域（需开启目标追踪）。',
        'params_schema': {
            'type': 'object',
            'properties': {
                'event_type': {
                    'type': 'string',
                    'enum': ['enter', 'exit', 'both'],
                    'default': 'both',
                    'title': '事件类型',
                },
                'hit_mode': {
                    'type': 'string',
                    'enum': ['center', 'any'],
                    'default': 'center',
                    'title': '命中模式',
                },
                'target_classes': {'type': 'array', 'items': {'type': 'string'}, 'title': '目标类别'},
            },
        },
    },
    {
        'id': 'dwell_timer',
        'name': '停留超时',
        'kinds': ['filter', 'decide'],
        'builtin': True,
        'description': '目标在区域内停留超过阈值时触发（需开启目标追踪）。',
        'params_schema': {
            'type': 'object',
            'properties': {
                'min_dwell_sec': {'type': 'number', 'default': 5, 'title': '最短停留(秒)'},
                'hit_mode': {
                    'type': 'string',
                    'enum': ['center', 'any'],
                    'default': 'center',
                    'title': '命中模式',
                },
                'target_classes': {'type': 'array', 'items': {'type': 'string'}, 'title': '目标类别'},
            },
        },
    },
    {
        'id': 'headcount_gate',
        'name': '人数阈值',
        'kinds': ['filter', 'decide'],
        'builtin': True,
        'description': '区域内目标数量满足阈值时放行。',
        'params_schema': {
            'type': 'object',
            'properties': {
                'threshold': {'type': 'integer', 'default': 1, 'title': '阈值'},
                'operator': {
                    'type': 'string',
                    'enum': ['gte', 'lte', 'eq'],
                    'default': 'gte',
                    'title': '比较符',
                },
                'count_mode': {
                    'type': 'string',
                    'enum': ['in_regions', 'all'],
                    'default': 'in_regions',
                    'title': '计数范围',
                },
                'hit_mode': {
                    'type': 'string',
                    'enum': ['center', 'any'],
                    'default': 'center',
                    'title': '命中模式',
                },
                'target_classes': {'type': 'array', 'items': {'type': 'string'}, 'title': '目标类别'},
            },
        },
    },
    {
        'id': 'user_script',
        'name': '业务脚本',
        'kinds': ['enrich'],
        'builtin': True,
        'description': '调用 USER_SCRIPT_URL 做业务富化（与 Python 业务脚本 Worker 独立）。',
        'params_schema': {'type': 'object', 'properties': {}},
    },
    {
        'id': 'default_pass',
        'name': '标准放行',
        'kinds': ['decide'],
        'builtin': True,
        'description': '最终放行步骤，组装标准告警载荷。',
        'params_schema': {'type': 'object', 'properties': {}},
    },
]


def _ensure_tables() -> None:
    try:
        from models import db, ensure_post_plugin_tables
        ensure_post_plugin_tables(db.engine)
    except Exception as exc:
        logger.debug('ensure_post_plugin_tables: %s', exc)


def list_plugin_catalog() -> Dict[str, Any]:
    _ensure_tables()
    from models import PostPlugin

    builtins = list(BUILTIN_PLUGIN_CATALOG)
    externals: List[Dict[str, Any]] = []
    try:
        for row in PostPlugin.query.filter_by(enabled=True).order_by(PostPlugin.id).all():
            data = row.to_dict(include_service=True)
            manifest = data.get('manifest') or {}
            externals.append({
                'id': data['id'],
                'name': data.get('name') or data['id'],
                'kinds': manifest.get('kinds') or ['enrich'],
                'builtin': False,
                'description': manifest.get('description') or '',
                'params_schema': manifest.get('params_schema') or {'type': 'object', 'properties': {}},
                'version': data.get('latest_version'),
                'service': data.get('service'),
            })
    except Exception as exc:
        logger.warning('读取 post_plugin 表失败: %s', exc)
    return {'builtins': builtins, 'externals': externals}


def _lookup_endpoint(plugin_id: str, version: str = '') -> Optional[str]:
    if plugin_id in BUILTIN_PLUGIN_IDS:
        return None
    _ensure_tables()
    from models import PostPlugin, PostPluginService

    row = PostPlugin.query.get(plugin_id)
    if not row or not row.enabled:
        return None
    ver = (version or row.latest_version or '').strip()
    svc = PostPluginService.query.filter_by(plugin_id=plugin_id, version=ver).first()
    if svc is None:
        svc = PostPluginService.query.filter_by(plugin_id=plugin_id).first()
    if not svc or (svc.status or '').lower() != 'running':
        return None
    ep = (svc.endpoint or '').strip()
    return ep or None


def inject_pipeline_endpoints(pipeline: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if not pipeline:
        return []
    out = []
    for step in pipeline:
        if not isinstance(step, dict):
            continue
        item = dict(step)
        plugin = str(item.get('plugin') or '').strip()
        if plugin and plugin not in BUILTIN_PLUGIN_IDS and not (item.get('endpoint') or '').strip():
            ep = _lookup_endpoint(plugin, str(item.get('version') or ''))
            if ep:
                item['endpoint'] = ep
        out.append(item)
    return out


def ensure_external_services_ready(pipeline: Optional[List[Dict[str, Any]]]) -> Tuple[bool, str]:
    if not pipeline:
        return True, 'ok'
    missing = []
    for step in pipeline:
        if not isinstance(step, dict):
            continue
        if step.get('enabled') is False:
            continue
        plugin = str(step.get('plugin') or '').strip()
        if not plugin or plugin in BUILTIN_PLUGIN_IDS:
            continue
        ep = (step.get('endpoint') or '').strip() or (_lookup_endpoint(plugin, str(step.get('version') or '')) or '')
        if not ep:
            missing.append(plugin)
    if missing:
        return False, f'外置插件未就绪: {", ".join(sorted(set(missing)))}'
    return True, 'ok'
