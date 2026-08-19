from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from sentinel.base import ComponentState, ProbeLevel, ProbeResult, SentinelContext
from sentinel.environment_profile import collect_environment_profile
from sentinel.capability_deriver import derive_capabilities
from sentinel.components import (
    COMPONENT_DEPENDS,
    COMPONENT_PROBES,
    expected_components_for,
)

SENTINEL_VERSION = '1.0.0'


def _remediation_snapshot() -> Dict[str, Any]:
    try:
        from sentinel.remediator import snapshot
        return snapshot()
    except Exception:
        return {}


def _build_env() -> Dict[str, str]:
    keys = [
        'NODE_ID', 'AI_ROOT', 'VIDEO_ROOT', 'RUNTIME_BIN', 'MEDIA_HOST_DATA_ROOT',
        'NFS_MOUNT_ROOT', 'CEPH_MOUNT_ROOT', 'MEDIA_CLUSTER_ROOT', 'NODE_FUNCTIONS',
    ]
    env: Dict[str, str] = {}
    for key in keys:
        val = os.environ.get(key)
        if val:
            env[key] = val
    env.setdefault('AI_ROOT', '/opt/easyaiot/AI')
    env.setdefault('VIDEO_ROOT', '/opt/easyaiot/VIDEO')
    return env


def _resolve_functions(env: Dict[str, str]) -> List[str]:
    raw = (env.get('NODE_FUNCTIONS') or '').strip().lower()
    return [part.strip() for part in raw.split(',') if part.strip()]


def _topo_sort(component_ids: List[str]) -> List[str]:
    ordered: List[str] = []
    seen = set()

    def visit(cid: str) -> None:
        if cid in seen:
            return
        seen.add(cid)
        for dep in COMPONENT_DEPENDS.get(cid, []):
            if dep in COMPONENT_PROBES:
                visit(dep)
        ordered.append(cid)

    for cid in component_ids:
        if cid in COMPONENT_PROBES:
            visit(cid)
    return ordered


def run_sentinel_probe(
    *,
    node_id: int,
    gpu_info: Optional[List[Dict[str, Any]]] = None,
    cluster_mode: bool = False,
    nfs_mount_ready: bool = False,
    ceph_mount_ready: Optional[bool] = None,
    declared_capabilities: Optional[Dict[str, bool]] = None,
    level: ProbeLevel = ProbeLevel.L0,
) -> Dict[str, Any]:
    env = _build_env()
    functions = _resolve_functions(env)
    profile = ','.join(functions)
    ctx = SentinelContext(
        node_id=node_id,
        profile=profile,
        env=env,
        gpu_info=gpu_info or [],
        cluster_mode=cluster_mode,
        nfs_mount_ready=bool(nfs_mount_ready or ceph_mount_ready),
    )

    component_ids = list(COMPONENT_PROBES.keys())
    results: Dict[str, ProbeResult] = {}
    expected = set(expected_components_for(functions))

    for comp_id in _topo_sort(component_ids):
        ctx.component_states = results
        probe_fn = COMPONENT_PROBES[comp_id]
        try:
            result = probe_fn(ctx, level)
        except Exception as exc:
            result = ProbeResult(ComponentState.UNKNOWN, str(exc))
        results[comp_id] = result

    components_payload = []
    for comp_id, result in results.items():
        item = result.to_dict()
        item['componentId'] = comp_id
        item['expected'] = comp_id in expected
        components_payload.append(item)

    schedulable = derive_capabilities(results, declared_capabilities)
    env_profile = collect_environment_profile(
        gpu_info=gpu_info or [],
        cluster_mode=cluster_mode,
        nfs_mount_root=env.get('MEDIA_HOST_DATA_ROOT') or env.get('NFS_MOUNT_ROOT') or env.get('CEPH_MOUNT_ROOT') or '',
        nfs_mount_ready=bool(nfs_mount_ready or ceph_mount_ready),
        agent_version=SENTINEL_VERSION,
    )

    missing_expected = [
        comp_id for comp_id in expected
        if comp_id in results and results[comp_id].state in (ComponentState.UNAVAILABLE, ComponentState.UNKNOWN)
    ]

    try:
        from sentinel.remediator import annotate_components
        annotate_components(components_payload)
    except Exception:
        pass

    ready_count = sum(1 for r in results.values() if r.state == ComponentState.READY)
    return {
        'sentinelVersion': SENTINEL_VERSION,
        'nodeProfile': profile,
        'nodeFunctions': functions,
        'probeLevel': level.value,
        'probedAt': int(time.time() * 1000),
        'components': components_payload,
        'schedulableCapabilities': schedulable,
        'environmentProfile': env_profile,
        'missingExpectedComponents': missing_expected,
        'remediation': _remediation_snapshot(),
        'summary': {
            'componentTotal': len(results),
            'componentReady': ready_count,
            'capabilitySchedulable': sum(1 for v in schedulable.values() if v.get('schedulable')),
        },
    }
