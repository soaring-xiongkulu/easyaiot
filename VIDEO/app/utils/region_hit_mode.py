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
        if step.get('plugin') != 'region_gate':
            continue
        params = step.get('params')
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise ValueError(f'post_pipeline[{index}].params 必须是对象')

        normalize_region_hit_config(
            params.get('hit_mode', REGION_HIT_MODE_CENTER),
            params.get('min_overlap_ratio'),
        )
