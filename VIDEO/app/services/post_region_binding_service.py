"""Explicit, revision-checked links between task geometry and business plugins."""
import json
from datetime import datetime

GEOMETRY = {'line_cross': 'line', 'region_enter_exit': 'area', 'dwell_timer': 'area', 'headcount_gate': 'area'}


def compatible(plugin, region):
    return plugin in GEOMETRY and ((region.region_type == 'line') == (GEOMETRY[plugin] == 'line'))


def binding_state(task):
    from models import DeviceDetectionRegion
    steps = json.loads(task.post_pipeline) if isinstance(task.post_pipeline, str) and task.post_pipeline else (task.post_pipeline or [])
    regions = DeviceDetectionRegion.query.filter_by(task_id=task.id).all()
    return {'revision': int(task.template_revision or 1), 'pipeline': steps,
            'task': {key: getattr(task, key, None) for key in ('id', 'task_name', 'task_type', 'executor', 'tracking_enabled', 'alert_event_enabled', 'post_process_enabled', 'pose_analysis_enabled', 'pose_intent_enabled', 'run_status')},
            'regions': [{'id': r.id, 'device_id': r.device_id, 'name': r.region_name, 'type': r.region_type, 'enabled': r.is_enabled} for r in regions],
            'legacy_plugins': [s['plugin'] for s in steps if s.get('plugin') in GEOMETRY and not (s.get('params') or {}).get('region_ids')]}


def save_binding(task_id, region_id, data):
    from models import db, AlgorithmTask, DeviceDetectionRegion
    from app.utils.region_hit_mode import validate_post_pipeline_runtime
    from app.services.device_detection_region_service import RegionRevisionConflict
    try:
        task = AlgorithmTask.query.filter_by(id=task_id).with_for_update().first()
        if not task:
            raise ValueError('任务不存在')
        if int(data.get('expected_revision', 0)) != int(task.template_revision or 1):
            raise RegionRevisionConflict('配置已变化，请刷新工作区后重试')
        region = DeviceDetectionRegion.query.filter_by(id=region_id, task_id=task_id).first()
        if not region:
            raise ValueError('请先保存当前任务的检测线或区域')
        plugin = data.get('plugin')
        if not compatible(plugin, region):
            raise ValueError('越线插件需绑定检测线，其他空间插件需绑定矩形或多边形')
        state = binding_state(task)
        steps = state['pipeline'] or [{'plugin': 'region_gate'}, {'plugin': 'default_pass'}]
        # Preserve each former implicit association when migrating to explicit rules.
        all_regions = DeviceDetectionRegion.query.filter_by(task_id=task_id).all()
        expanded = []
        for step in steps:
            params = step.get('params') or {}
            if step.get('plugin') in GEOMETRY and not params.get('region_ids'):
                ids = [r.id for r in all_regions if compatible(step['plugin'], r)]
            else:
                ids = params.get('region_ids') or []
            if ids:
                for rid in ids:
                    expanded.append({**step, 'params': {**params, 'region_ids': [rid]}})
            elif step.get('plugin') in GEOMETRY:
                # Keep dormant legacy parameters without allowing a missing
                # geometry rule to block every newly bound subscription.
                expanded.append({**step, 'enabled': False})
            else:
                expanded.append(step)
        steps = [s for s in expanded if not (s.get('plugin') == plugin and region_id in (s.get('params') or {}).get('region_ids', []))]
        if not data.get('remove'):
            if not task.alert_event_enabled:
                raise ValueError('请先在任务配置中开启告警事件')
            params = data.get('params') or {}
            if not isinstance(params, dict):
                raise ValueError('插件参数必须是对象')
            params = {**params, 'region_ids': [region_id]}
            if plugin == 'headcount_gate':
                params['count_mode'] = 'in_regions'
            at = next((i for i, s in enumerate(steps) if s.get('plugin') == 'default_pass'), len(steps))
            steps.insert(at, {'plugin': plugin, 'enabled': data.get('enabled') is not False, 'params': params, 'fail_strategy': 'fail_closed'})
        tail = next((s for s in steps if s.get('plugin') == 'default_pass'), None)
        if tail is None:
            tail = {'plugin': 'default_pass'}
            steps.append(tail)
        tail['params'] = {**(tail.get('params') or {}), 'monitoring_mode': 'bound'}
        tail['enabled'] = True
        validate_post_pipeline_runtime(steps, task.task_type, task.tracking_enabled, task.executor,
            any(getattr(task, key, False) for key in ('post_process_enabled', 'pose_analysis_enabled', 'pose_intent_enabled')))
        task.post_pipeline = json.dumps(steps, ensure_ascii=False)
        task.template_revision = int(task.template_revision or 1) + 1
        task.updated_at = datetime.utcnow()
        db.session.commit()
        return binding_state(task)
    except Exception:
        db.session.rollback()
        raise
