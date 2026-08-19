from __future__ import annotations

from typing import Any, Dict, List

from sentinel.base import ComponentState, ProbeResult

# capability -> 组合规则（all 必须 ready；any 至少一个 ready/degraded）
CAPABILITY_RULES: Dict[str, Dict[str, Any]] = {
    'algorithm_realtime': {
        'all': ['nfs_mount'],
        'any': ['runtime', 'video_bundle_realtime'],
    },
    'algorithm_snap': {
        'all': ['nfs_mount'],
        'any': ['runtime', 'video_bundle_realtime'],
    },
    'algorithm_patrol': {
        'all': ['nfs_mount'],
        'any': ['runtime', 'video_bundle_realtime'],
    },
    'stream_forward': {
        'all': ['srs_live'],
        'any': ['runtime', 'ffmpeg'],
    },
    'model_train': {
        'all': ['model_train_bundle', 'cuda', 'nfs_mount', 'gpu_vram'],
        'any': [],
    },
    'llm_inference': {
        'all': ['cuda', 'gpu_vram'],
        'any': [],
    },
    'srs_live': {
        'all': ['docker', 'srs_live'],
        'any': [],
    },
    'ai_inference': {
        'all': ['nfs_mount'],
        'any': ['runtime', 'video_bundle_realtime'],
    },
    'auto_label': {
        'all': ['nfs_mount'],
        'any': ['runtime', 'video_bundle_realtime'],
    },
}


def _component_pass(state: ComponentState) -> bool:
    return state in (ComponentState.READY, ComponentState.DEGRADED)


def _lookup_component(components: Dict[str, ProbeResult], comp_id: str) -> ProbeResult | None:
    result = components.get(comp_id)
    if result is None and comp_id == 'nfs_mount':
        result = components.get('ceph_mount')
    return result


def derive_capabilities(
    components: Dict[str, ProbeResult],
    declared: Dict[str, bool] | None = None,
) -> Dict[str, Dict[str, Any]]:
    declared = declared or {}
    derived: Dict[str, Dict[str, Any]] = {}
    for cap_id, rule in CAPABILITY_RULES.items():
        if declared and cap_id in declared and not declared.get(cap_id):
            derived[cap_id] = {
                'schedulable': False,
                'state': 'disabled',
                'reason': '节点未声明该能力',
                'missingComponents': [],
            }
            continue

        missing: List[str] = []
        reasons: List[str] = []

        for comp_id in rule.get('all') or []:
            result = _lookup_component(components, comp_id)
            if result is None or result.state == ComponentState.UNKNOWN:
                missing.append(comp_id)
                reasons.append(f'{comp_id}: unknown')
            elif not _component_pass(result.state):
                missing.append(comp_id)
                if result.reason:
                    reasons.append(f'{comp_id}: {result.reason}')

        any_list = rule.get('any') or []
        if any_list:
            any_ok = False
            for comp_id in any_list:
                result = _lookup_component(components, comp_id)
                if result and _component_pass(result.state):
                    any_ok = True
                    break
            if not any_ok:
                missing.extend(any_list)
                reasons.append('requires any of: ' + ', '.join(any_list))

        schedulable = not missing
        state = 'ready' if schedulable else 'unavailable'
        if schedulable and any(
            components.get(c) and components[c].state == ComponentState.DEGRADED
            for c in (rule.get('all') or []) + (rule.get('any') or [])
            if components.get(c)
        ):
            state = 'degraded'

        derived[cap_id] = {
            'schedulable': schedulable,
            'state': state,
            'reason': '; '.join(reasons) if reasons else '',
            'missingComponents': missing,
        }
    return derived
