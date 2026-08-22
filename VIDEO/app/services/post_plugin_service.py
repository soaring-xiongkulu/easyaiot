"""
POST 外置插件登记、启停与 pipeline endpoint 注入。
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from models import db, PostPlugin, PostPluginService

logger = logging.getLogger(__name__)

BUILTIN_PLUGINS = frozenset({
    'region_gate',
    'default_pass',
    'user_script',
    'line_cross',
    'region_enter_exit',
    'dwell_timer',
    'headcount_gate',
})
BUILTIN_PLUGIN_IDS = BUILTIN_PLUGINS
WORKLOAD_TYPE = 'post_plugin'
PLUGIN_ID_RE = re.compile(r'^[a-z0-9][a-z0-9._-]{1,126}$')

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


def _now():
    return datetime.utcnow()


def _ensure_tables() -> None:
    try:
        from models import ensure_post_plugin_tables
        ensure_post_plugin_tables(db.engine)
    except Exception as exc:
        logger.debug('ensure_post_plugin_tables: %s', exc)


def list_plugin_catalog() -> Dict[str, Any]:
    _ensure_tables()
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


def validate_manifest(manifest: dict) -> dict:
    if not isinstance(manifest, dict):
        raise ValueError('manifest 必须是对象')
    pid = str(manifest.get('id') or '').strip()
    if not pid or not PLUGIN_ID_RE.match(pid):
        raise ValueError('manifest.id 非法（建议 org.name 小写点分）')
    if pid in BUILTIN_PLUGINS:
        raise ValueError(f'{pid} 为平台内置插件，不可登记为外置')
    name = str(manifest.get('name') or pid).strip()
    version = str(manifest.get('version') or '0.0.0').strip()
    runtime = str(manifest.get('runtime') or 'http').strip().lower()
    if runtime not in ('http', 'grpc', 'script'):
        raise ValueError(f'不支持的 runtime: {runtime}')
    entry = manifest.get('entrypoint') or {}
    if not isinstance(entry, dict):
        entry = {}
    return {
        'id': pid,
        'name': name,
        'version': version,
        'runtime': runtime,
        'entrypoint': entry,
        'manifest': manifest,
    }


def register_plugin(manifest: dict, endpoint: Optional[str] = None) -> PostPlugin:
    """登记 / 覆盖 Manifest；可选预填静态 endpoint。"""
    _ensure_tables()
    meta = validate_manifest(manifest)
    row = PostPlugin.query.get(meta['id'])
    raw = json.dumps(meta['manifest'], ensure_ascii=False)
    if row is None:
        row = PostPlugin(
            id=meta['id'],
            name=meta['name'],
            latest_version=meta['version'],
            runtime=meta['runtime'],
            enabled=True,
            manifest_json=raw,
            created_at=_now(),
            updated_at=_now(),
        )
        db.session.add(row)
    else:
        row.name = meta['name']
        row.latest_version = meta['version']
        row.runtime = meta['runtime']
        row.manifest_json = raw
        row.updated_at = _now()

    svc = PostPluginService.query.filter_by(plugin_id=meta['id'], version=meta['version']).first()
    if svc is None:
        svc = PostPluginService(
            plugin_id=meta['id'],
            version=meta['version'],
            replicas=1,
            status='stopped',
            deploy_mode='endpoint',
            updated_at=_now(),
        )
        db.session.add(svc)
    if endpoint:
        svc.endpoint = endpoint.rstrip('/')
        svc.deploy_mode = 'endpoint'
        svc.status = 'running'
        svc.updated_at = _now()
    db.session.commit()
    return row


def list_plugins(enabled: Optional[bool] = None) -> List[dict]:
    _ensure_tables()
    q = PostPlugin.query.order_by(PostPlugin.id.asc())
    if enabled is not None:
        q = q.filter(PostPlugin.enabled.is_(bool(enabled)))
    return [p.to_dict() for p in q.all()]


def get_plugin(plugin_id: str) -> PostPlugin:
    _ensure_tables()
    row = PostPlugin.query.get(plugin_id)
    if not row:
        raise ValueError(f'插件不存在: {plugin_id}')
    return row


def update_plugin(plugin_id: str, *, enabled: Optional[bool] = None, manifest: Optional[dict] = None) -> PostPlugin:
    row = get_plugin(plugin_id)
    if manifest is not None:
        meta = validate_manifest(manifest)
        if meta['id'] != plugin_id:
            raise ValueError('manifest.id 与路径不一致')
        row.name = meta['name']
        row.latest_version = meta['version']
        row.runtime = meta['runtime']
        row.manifest_json = json.dumps(meta['manifest'], ensure_ascii=False)
    if enabled is not None:
        row.enabled = bool(enabled)
    row.updated_at = _now()
    db.session.commit()
    return row


def delete_plugin(plugin_id: str, force: bool = False) -> None:
    row = get_plugin(plugin_id)
    svc = PostPluginService.query.filter_by(plugin_id=plugin_id).all()
    if not force:
        for s in svc:
            if (s.status or '') == 'running':
                raise ValueError('服务运行中，请先停止或 force=true')
    for s in svc:
        db.session.delete(s)
    db.session.delete(row)
    db.session.commit()


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
