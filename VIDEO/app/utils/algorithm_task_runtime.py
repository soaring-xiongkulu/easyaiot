"""算法任务控制面与 Worker 运行状态归一化工具。"""
from __future__ import annotations

from datetime import datetime
from typing import Tuple


VALID_SOURCE_MODES = frozenset({'pending', 'shared', 'direct', 'direct_fallback'})
VALID_STREAM_STATUSES = frozenset({
    'starting',
    'source_waiting',
    'inferencing',
    'publishing',
    'degraded',
    'stopped',
    'failed',
})


def resolve_task_run_status_from_heartbeat(is_enabled: bool) -> str:
    """仅允许启用任务的有效 Worker 心跳将任务标记为运行中。"""
    return 'running' if is_enabled else 'stopped'


def resolve_heartbeat_server_ip(
        reported_ip: str,
        current_ip: str,
        node_id=None,
) -> str:
    """Do not let a remote worker's loopback self-address hide its edge node host."""
    reported = str(reported_ip or '').strip()
    current = str(current_ip or '').strip()
    if node_id and reported in {'127.0.0.1', 'localhost', '::1'}:
        return current
    return reported or current


def resolve_heartbeat_stream_state(
        is_enabled: bool,
        source_mode: str,
        status: str,
) -> Tuple[str, str]:
    """归一化 Worker 心跳，阻止停用任务的迟到心跳重新激活运行态。"""
    if not is_enabled:
        return 'pending', 'stopped'

    normalized_source_mode = (
        source_mode if source_mode in VALID_SOURCE_MODES else 'pending'
    )
    normalized_status = (
        status if status in VALID_STREAM_STATUSES else 'starting'
    )
    return normalized_source_mode, normalized_status


def resolve_frame_runtime_status(
        source_mode: str,
        publisher_running: bool,
) -> str:
    """根据当前源流模式和推流进程计算每帧应上报的真实状态。"""
    if source_mode == 'direct_fallback':
        return 'degraded'
    if publisher_running:
        return 'publishing'
    return 'inferencing'


def mark_stream_runtime_stopped(runtime, stopped_at: datetime) -> None:
    """同步收敛停用任务的设备运行态，同时保留最后活动时间用于审计。"""
    runtime.source_mode = 'pending'
    runtime.status = 'stopped'
    runtime.error_message = None
    runtime.updated_at = stopped_at
