"""双任务双模型并行执行的结构化日志工具。"""
from __future__ import annotations

import json
import time


def _epoch_ms(value=None) -> int:
    """将可选时间转换为毫秒时间戳。"""
    return int((time.time() if value is None else float(value)) * 1000)


def _normalize_task_ids(task_ids) -> list[str]:
    """对任务标识去重并稳定排序。"""
    normalized = {str(task_id).strip() for task_id in (task_ids or []) if str(task_id).strip()}
    return sorted(normalized, key=lambda value: (not value.isdigit(), int(value) if value.isdigit() else value))


def build_shared_source_topology_evidence(
        *,
        device_id: str,
        task_ids,
        subscriber_count: int,
        reason: str,
        observed_at_epoch_ms=None,
) -> dict:
    """构建同一摄像头共享订阅拓扑证据。"""
    normalized_task_ids = _normalize_task_ids(task_ids)
    return {
        'device_id': str(device_id),
        'task_ids': normalized_task_ids,
        'subscriber_count': int(subscriber_count),
        'parallel_task_execution_expected': len(normalized_task_ids) >= 2,
        'reason': str(reason),
        'observed_at_epoch_ms': (
            _epoch_ms() if observed_at_epoch_ms is None else int(observed_at_epoch_ms)
        ),
    }


def build_parallel_inference_evidence(
        *,
        task_id: int,
        process_id: int,
        worker_instance: str,
        device_id: str,
        source_mode: str,
        frame_number: int,
        model_stats,
        observed_at_epoch_ms=None,
) -> dict:
    """构建单个算法 Worker 的模型推理进度证据。"""
    models = sorted(
        [dict(item) for item in (model_stats or [])],
        key=lambda item: int(item.get('model_id')),
    )
    return {
        'task_id': int(task_id),
        'process_id': int(process_id),
        'worker_instance': str(worker_instance),
        'device_id': str(device_id),
        'source_mode': str(source_mode or 'pending'),
        'frame_number': int(frame_number),
        'active_model_ids': [int(item['model_id']) for item in models],
        'models': models,
        'observed_at_epoch_ms': (
            _epoch_ms() if observed_at_epoch_ms is None else int(observed_at_epoch_ms)
        ),
    }


def format_observability_event(event_name: str, payload: dict) -> str:
    """生成便于 grep 与机器解析的单行 JSON 日志。"""
    return '[{}] {}'.format(
        str(event_name).strip().upper(),
        json.dumps(payload, ensure_ascii=False, separators=(',', ':'), sort_keys=True),
    )
