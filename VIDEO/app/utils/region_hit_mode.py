"""算法任务区域命中模式及后处理规则链校验。"""
from __future__ import annotations

import math
from typing import Any, Iterable


REGION_HIT_MODE_CENTER = 'center'
REGION_HIT_MODE_BOTTOM_CENTER = 'bottom_center'
REGION_HIT_MODE_ANY_INTERSECTION = 'any_intersection'
REGION_HIT_MODE_OVERLAP_RATIO = 'overlap_ratio'
REGION_HIT_MODE_FULLY_INSIDE = 'fully_inside'

SELECTABLE_REGION_HIT_MODES = (
    REGION_HIT_MODE_CENTER,
    REGION_HIT_MODE_BOTTOM_CENTER,
    REGION_HIT_MODE_ANY_INTERSECTION,
    REGION_HIT_MODE_OVERLAP_RATIO,
    REGION_HIT_MODE_FULLY_INSIDE,
)

LEGACY_REGION_HIT_MODES = ('any_corner', 'any', 'all', 'bottom')
SUPPORTED_REGION_HIT_MODES = frozenset(
    (*SELECTABLE_REGION_HIT_MODES, *LEGACY_REGION_HIT_MODES)
)

DEFAULT_MIN_OVERLAP_RATIO = 0.5
MIN_OVERLAP_RATIO = 0.01
MAX_OVERLAP_RATIO = 1.0


def normalize_region_hit_config(mode: Any, ratio: Any = None) -> tuple[str, float]:
    """校验并规范化单个检测区域的命中配置。"""
    if mode is None:
        mode = REGION_HIT_MODE_CENTER
    if not isinstance(mode, str) or not mode.strip():
        raise ValueError('区域命中模式必须是非空字符串')
    normalized_mode = mode.strip()
    if normalized_mode not in SUPPORTED_REGION_HIT_MODES:
        raise ValueError(f'不支持的区域命中模式: {normalized_mode}')

    if ratio is None:
        return normalized_mode, DEFAULT_MIN_OVERLAP_RATIO
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)):
        raise ValueError('区域重叠比例阈值必须是数字')
    normalized_ratio = float(ratio)
    if not math.isfinite(normalized_ratio):
        raise ValueError('区域重叠比例阈值必须是有限数字')
    if normalized_ratio < MIN_OVERLAP_RATIO or normalized_ratio > MAX_OVERLAP_RATIO:
        raise ValueError('区域重叠比例阈值必须在 1% ~ 100% 之间')
    return normalized_mode, normalized_ratio


def validate_post_pipeline(pipeline: Iterable[Any]) -> None:
    """校验规则链中所有 region_gate 参数；旧命中模式只为兼容存量配置。"""
    for index, step in enumerate(pipeline):
        if not isinstance(step, dict):
            raise ValueError(f'post_pipeline[{index}] 必须是对象')
        params = step.get('params')
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise ValueError(f'post_pipeline[{index}].params 必须是对象')

        plugin = step.get('plugin')
        if 'region_ids' in params:
            ids = params['region_ids']
            if not isinstance(ids, list) or not ids or any(isinstance(rid, bool) or not isinstance(rid, int) or rid <= 0 for rid in ids):
                raise ValueError('绑定区域必须是非空的正整数 ID 列表')
        if not isinstance(plugin, str) or not plugin.strip():
            raise ValueError('插件 ID 必须为非空字符串')
        if plugin == 'line_cross' and params.get('direction', 'both') not in ('both', 'forward', 'backward', 'a_to_b', 'b_to_a'):
            raise ValueError('越线方向无效')
        if plugin == 'region_enter_exit' and params.get('event_type', 'both') not in ('enter', 'exit', 'both'):
            raise ValueError('区域进出事件类型无效')
        if plugin in ('headcount_gate', 'dwell_timer'):
            key = 'threshold' if plugin == 'headcount_gate' else 'min_dwell_sec'
            value = params.get(key, 1 if plugin == 'headcount_gate' else 5)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f'{key} 必须为非负有限数字')
            if plugin == 'headcount_gate' and int(value) != value:
                raise ValueError('人数阈值必须是整数')
        if plugin == 'headcount_gate' and params.get('operator', 'gte') not in ('gte', 'lte', 'eq'):
            raise ValueError('人数比较方式无效')
        if plugin == 'headcount_gate':
            cooldown = params.get('cooldown_sec', 0)
            if isinstance(cooldown, bool) or not isinstance(cooldown, (int, float)) or not math.isfinite(cooldown) or cooldown < 0:
                raise ValueError('重复提醒间隔必须为非负有限数字')
        if plugin != 'region_gate':
            continue

        normalize_region_hit_config(
            params.get('hit_mode', REGION_HIT_MODE_CENTER),
            params.get('min_overlap_ratio'),
        )


def validate_post_pipeline_runtime(raw, task_type, tracking_enabled, executor='python', sink_processing=False):
    import json
    steps = json.loads(raw) if isinstance(raw, str) and raw else raw
    if not steps:
        return
    validate_post_pipeline(steps)
    if any(step.get('enabled') is not False and step.get('plugin') in
           ('line_cross', 'region_enter_exit', 'dwell_timer') for step in steps):
        if task_type != 'realtime' or not tracking_enabled:
            raise ValueError('越线、区域进出和停留监测需要实时算法任务并开启目标追踪')
        if executor == 'cpp':
            raise ValueError('当前 C++ 执行器尚未输出目标轨迹 ID，请使用 Python 实时算法模式运行越线、进出和停留监测')
        if sink_processing:
            raise ValueError('连续轨迹插件暂不能与业务脚本或姿态分析同时启用，请分别创建任务')
