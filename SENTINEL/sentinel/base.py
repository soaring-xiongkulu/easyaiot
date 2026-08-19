from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ProbeLevel(str, Enum):
    L0 = 'L0'
    L1 = 'L1'
    L2 = 'L2'


class ComponentState(str, Enum):
    READY = 'ready'
    DEGRADED = 'degraded'
    UNAVAILABLE = 'unavailable'
    UNKNOWN = 'unknown'
    SKIPPED = 'skipped'


@dataclass
class ProbeResult:
    state: ComponentState
    reason: str = ''
    evidence: Dict[str, Any] = field(default_factory=dict)
    probed_at: float = field(default_factory=time.time)
    probe_level: ProbeLevel = ProbeLevel.L0
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'state': self.state.value,
            'reason': self.reason,
            'evidence': self.evidence,
            'probedAt': int(self.probed_at * 1000),
            'probeLevel': self.probe_level.value,
            'durationMs': self.duration_ms,
        }


@dataclass
class SentinelContext:
    node_id: int
    profile: str
    env: Dict[str, str]
    gpu_info: List[Dict[str, Any]]
    cluster_mode: bool
    nfs_mount_ready: bool
    component_states: Dict[str, ProbeResult] = field(default_factory=dict)
