"""
抓拍任务 Cron 表达式校验与规范化（与 WEB snap cron 规则对齐）。
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, Tuple

from app.utils.service_urls import epoch_to_shanghai_datetime, now_shanghai_naive

try:
    from croniter import croniter
except ImportError:  # pragma: no cover
    croniter = None  # type: ignore

MIN_SNAP_CRON_INTERVAL_SECONDS = 30


def _shanghai_naive_from_epoch(ts: float) -> datetime:
    """Unix 时间戳转为东八区 naive 墙钟，供 croniter 按业务时区匹配。"""
    return epoch_to_shanghai_datetime(float(ts)).replace(tzinfo=None)


def _cron_field_count(expression: str) -> int:
    return len((expression or "").strip().split())


def uses_second_field(expression: str) -> bool:
    """6 段且首段为秒字段时，croniter 需 second_at_beginning=True。"""
    return _cron_field_count(expression) >= 6


def normalize_cron_for_croniter(expression: str) -> str:
    """将 Quartz 风格 cron 规范为 croniter 可解析格式（保留 6 段秒级）。"""
    parts = expression.strip().split()
    if len(parts) == 6 and parts[0].startswith("*/") and parts[5] == "?":
        # Quartz: 秒 分 时 日 月 周(?) → 去掉周字段，仍保留秒在首段
        return " ".join("*" if p == "?" else p for p in parts[:5])
    return " ".join("*" if p == "?" else p for p in parts)


def make_snap_croniter(expression: str, start_time: datetime):
    """创建 croniter；6 段表达式按「秒 分 时 日 月 周」解析。"""
    if croniter is None:
        raise RuntimeError("croniter 未安装")
    expr = normalize_cron_for_croniter(expression)
    if uses_second_field(expr):
        return croniter(expr, start_time, second_at_beginning=True)
    return croniter(expr, start_time)


def snap_cron_interval_seconds(
    expression: str,
    ref_time: Optional[datetime] = None,
) -> float:
    """相邻两次触发间隔（秒）。"""
    ref = ref_time or now_shanghai_naive()
    it = make_snap_croniter(expression, ref)
    t0 = it.get_prev(float)
    t1 = it.get_next(float)
    return max(1.0, float(t1 - t0))


def snap_cron_match_window_seconds(
    expression: str,
    floor_sec: float = 5.0,
) -> float:
    """
    匹配窗口：触发后允许抓拍的秒数（非整个周期间隔）。
    秒级/分钟级短间隔用小窗口，避免 */30 时 25s 内每秒都判为「匹配」。
    """
    interval = snap_cron_interval_seconds(expression)
    floor_sec = float(floor_sec)
    if interval <= 120:
        # 例如 */30：约 10~13s，覆盖 HEVC 起播与异步 FIFO 延迟，且远小于 30s 周期
        return min(max(floor_sec, 10.0), interval * 0.45, interval - 1.0)
    if interval <= 3600:
        return min(max(floor_sec, 15.0), interval * 0.15, 120.0)
    return min(max(floor_sec, 30.0), interval * 0.05, 300.0)


def cron_slot_for_time(expression: str, current_time: float) -> Tuple[bool, Optional[datetime], float]:
    """
    判断当前时刻是否处于应抓拍的时间槽。

    croniter 在整秒边界上 get_prev/get_next 行为不同，需同时参考距上一触发与距下一触发的偏移。

    Returns:
        (in_window, fire_time, offset_sec)
    """
    current_dt = _shanghai_naive_from_epoch(current_time)
    it = make_snap_croniter(expression, current_dt)
    prev_time = it.get_prev(datetime)
    next_time = it.get_next(datetime)
    since_prev = (current_dt - prev_time).total_seconds()
    to_next = (next_time - current_dt).total_seconds()

    # 只匹配「已到达」的触发点，不在下一触发点之前提前匹配
    if since_prev <= to_next:
        fire_time = prev_time
        offset = since_prev
    else:
        fire_time = next_time
        offset = to_next
        if offset > 0.05:
            return False, fire_time, offset

    window = snap_cron_match_window_seconds(expression)
    in_window = 0 <= offset < window
    return in_window, fire_time, offset


def _min_interval_seconds(cron_expr: str, samples: int = 5) -> float:
    if croniter is None:
        raise RuntimeError("croniter 未安装")
    ref = now_shanghai_naive()
    it = make_snap_croniter(cron_expr, ref)
    times = [it.get_next(float) for _ in range(samples)]
    deltas = [times[i + 1] - times[i] for i in range(len(times) - 1)]
    return min(deltas) if deltas else float("inf")


def validate_snap_cron_min_interval(
    expression: str,
    min_seconds: int = MIN_SNAP_CRON_INTERVAL_SECONDS,
) -> str:
    """
    校验最短执行间隔并返回规范化后的 cron 字符串。
    无效时抛出 ValueError。
    """
    raw = (expression or "").strip()
    if not raw:
        raise ValueError("请填写 Cron 表达式")

    parts = raw.split()
    if len(parts) == 7:
        raw = " ".join(parts[:6])

    normalized = normalize_cron_for_croniter(raw)
    if croniter is None:
        return normalized

    try:
        make_snap_croniter(normalized, now_shanghai_naive())
    except Exception as e:
        raise ValueError(f"Cron 表达式错误：{e}") from e

    try:
        min_delta = _min_interval_seconds(normalized)
    except Exception as e:
        raise ValueError(f"Cron 表达式错误：{e}") from e

    if min_delta < min_seconds:
        raise ValueError(
            f"抓拍执行间隔不能小于 {min_seconds} 秒，请增大间隔（当前约 {int(min_delta)} 秒）"
        )

    if uses_second_field(normalized):
        sec_part = normalized.split()[0]
        if sec_part.startswith("*/"):
            step_m = re.match(r"\*/(\d+)", sec_part)
            if step_m:
                step = int(step_m.group(1))
                if step < min_seconds:
                    raise ValueError(
                        f"秒级 Cron 步长不能小于 {min_seconds} 秒（当前 */{step}）"
                    )

    return normalized
