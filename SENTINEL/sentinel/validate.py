"""部署前校验：对照 registry 检查组件/能力是否就绪。"""
from __future__ import annotations

from typing import Any, Dict, List

from sentinel.capability_deriver import derive_capabilities
from sentinel.orchestrator import run_sentinel_probe
from sentinel.base import ProbeLevel


def validate_workload(
    *,
    node_id: int,
    workload_type: str,
    requirements: Dict[str, Any] | None = None,
    gpu_info: List[Dict[str, Any]] | None = None,
    cluster_mode: bool = False,
    nfs_mount_ready: bool = False,
    ceph_mount_ready: bool = False,
) -> Dict[str, Any]:
    requirements = requirements or {}
    capabilities = requirements.get('capabilities') or []
    if not capabilities:
        capabilities = _default_capabilities(workload_type)
    probe = run_sentinel_probe(
        node_id=node_id,
        gpu_info=gpu_info or [],
        cluster_mode=cluster_mode,
        nfs_mount_ready=bool(nfs_mount_ready or ceph_mount_ready),
        level=ProbeLevel.L1,
    )
    sched = probe.get('schedulableCapabilities') or {}
    missing: List[str] = []
    for cap in capabilities:
        detail = sched.get(cap) if isinstance(sched, dict) else None
        if not isinstance(detail, dict) or not detail.get('schedulable'):
            missing.append(cap)
    ok = not missing
    return {
        'valid': ok,
        'workloadType': workload_type,
        'requiredCapabilities': capabilities,
        'missingCapabilities': missing,
        'schedulableCapabilities': sched,
        'probeLevel': probe.get('probeLevel'),
    }


def _default_capabilities(workload_type: str) -> List[str]:
    mapping = {
        'algorithm_task': ['algorithm_realtime'],
        'stream_forward': ['stream_forward', 'srs_live'],
        'model_train': ['model_train'],
        'llm_service': ['llm_inference'],
        'ai_service': ['ai_inference'],
        'auto_label': ['auto_label'],
    }
    return mapping.get(workload_type, [])
