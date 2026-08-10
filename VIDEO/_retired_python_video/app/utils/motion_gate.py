"""
运动检测门控：轻量帧差 + 变化面积占比，用于实时算法任务保守补检与统计。

采样帧（每 extract_interval 帧）上评估；触发条件偏保守，避免风吹草动频繁误触。
"""
from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field, replace
from typing import Any, Dict, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

MOTION_PRESETS: Dict[str, Dict[str, Any]] = {
    'conservative': {
        'min_changed_area_ratio': 0.08,
        'min_mean_score': 0.025,
        'consecutive_hits_required': 2,
        'cooldown_frames': 125,
    },
    'standard': {
        'min_changed_area_ratio': 0.05,
        'min_mean_score': 0.020,
        'consecutive_hits_required': 2,
        'cooldown_frames': 75,
    },
    'sensitive': {
        'min_changed_area_ratio': 0.03,
        'min_mean_score': 0.015,
        'consecutive_hits_required': 1,
        'cooldown_frames': 50,
    },
}


@dataclass
class MotionGateConfig:
    enabled: bool = False
    preset: str = 'conservative'
    pixel_diff_thresh: int = 25
    min_changed_area_ratio: float = 0.08
    min_mean_score: float = 0.025
    consecutive_hits_required: int = 2
    cooldown_frames: int = 125
    downscale_width: int = 160
    downscale_height: int = 90
    alert_motion_sync: bool = False

    @property
    def downscale(self) -> tuple:
        return (self.downscale_width, self.downscale_height)

    @classmethod
    def from_env(cls) -> 'MotionGateConfig':
        enabled = os.getenv('MOTION_GATE_ENABLED', 'false').strip().lower() in (
            '1', 'true', 'yes', 'on',
        )
        cfg = cls(enabled=enabled)
        raw = os.getenv('MOTION_GATE_CONFIG', '').strip()
        if raw:
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    cfg = cls.from_dict(data, base=cfg)
            except Exception as exc:
                logger.warning('MOTION_GATE_CONFIG 解析失败: %s', exc)
        cfg.min_changed_area_ratio = float(
            os.getenv('MOTION_MIN_CHANGED_AREA_RATIO', str(cfg.min_changed_area_ratio))
        )
        cfg.min_mean_score = float(os.getenv('MOTION_DIFF_THRESHOLD', str(cfg.min_mean_score)))
        cfg.consecutive_hits_required = int(
            os.getenv('MOTION_CONSECUTIVE_HITS', str(cfg.consecutive_hits_required))
        )
        cfg.cooldown_frames = int(os.getenv('MOTION_COOLDOWN_FRAMES', str(cfg.cooldown_frames)))
        cfg.downscale_width = int(os.getenv('MOTION_DOWNSCALE_WIDTH', str(cfg.downscale_width)))
        cfg.downscale_height = int(os.getenv('MOTION_DOWNSCALE_HEIGHT', str(cfg.downscale_height)))
        cfg.pixel_diff_thresh = int(os.getenv('MOTION_PIXEL_DIFF_THRESH', str(cfg.pixel_diff_thresh)))
        sync = os.getenv('ALERT_MOTION_SYNC', 'false').strip().lower()
        cfg.alert_motion_sync = sync in ('1', 'true', 'yes', 'on')
        return cfg

    @classmethod
    def from_task(cls, task, base: Optional['MotionGateConfig'] = None) -> 'MotionGateConfig':
        cfg = base or cls.from_env()
        if task is None:
            return cfg
        enabled = getattr(task, 'motion_gate_enabled', None)
        if enabled is not None:
            cfg.enabled = bool(enabled)
        raw = getattr(task, 'motion_gate_config', None)
        if raw:
            try:
                data = json.loads(raw) if isinstance(raw, str) else (raw or {})
                if isinstance(data, dict):
                    cfg = cls.from_dict(data, base=cfg)
            except Exception as exc:
                logger.warning('任务 motion_gate_config 解析失败: %s', exc)
        return cfg

    @classmethod
    def from_dict(cls, data: Dict[str, Any], base: Optional['MotionGateConfig'] = None) -> 'MotionGateConfig':
        cfg = replace(base) if base else cls()
        preset = str(data.get('preset') or cfg.preset).strip().lower()
        if preset in MOTION_PRESETS:
            for key, val in MOTION_PRESETS[preset].items():
                setattr(cfg, key, val)
            cfg.preset = preset
        for key in (
            'enabled', 'pixel_diff_thresh', 'min_changed_area_ratio', 'min_mean_score',
            'consecutive_hits_required', 'cooldown_frames', 'downscale_width',
            'downscale_height', 'alert_motion_sync',
        ):
            if key in data and data[key] is not None:
                setattr(cfg, key, data[key])
        return cfg


@dataclass
class MotionResult:
    triggered: bool = False
    score: float = 0.0
    changed_area_ratio: float = 0.0
    reason: str = 'skip'
    consecutive_hits: int = 0


@dataclass
class _DeviceMotionState:
    prev_gray: Optional[np.ndarray] = None
    consecutive_hits: int = 0
    cooldown_until: int = 0
    baseline_triggers: int = 0
    motion_triggers: int = 0
    supplement_triggers: int = 0
    last_score: float = 0.0
    last_area_ratio: float = 0.0


class MotionGate:
    """每设备独立状态；仅在采样帧调用 on_sample_frame。"""

    def __init__(self, config: Optional[MotionGateConfig] = None):
        self.config = config or MotionGateConfig.from_env()
        self._states: Dict[str, _DeviceMotionState] = {}
        self._lock = threading.Lock()
        self._kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    def reset(self, device_id: str) -> None:
        with self._lock:
            self._states.pop(device_id, None)

    def get_stats(self, device_id: str) -> Dict[str, Any]:
        with self._lock:
            st = self._states.get(device_id)
            if not st:
                return {}
            return {
                'baseline_triggers': st.baseline_triggers,
                'motion_triggers': st.motion_triggers,
                'supplement_triggers': st.supplement_triggers,
                'consecutive_hits': st.consecutive_hits,
                'last_score': st.last_score,
                'last_area_ratio': st.last_area_ratio,
                'cooldown_until': st.cooldown_until,
            }

    def _get_state(self, device_id: str) -> _DeviceMotionState:
        if device_id not in self._states:
            self._states[device_id] = _DeviceMotionState()
        return self._states[device_id]

    def _to_small_gray(self, frame_bgr: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        return cv2.resize(
            gray, self.config.downscale, interpolation=cv2.INTER_AREA,
        )

    def evaluate(self, prev_gray: np.ndarray, curr_gray: np.ndarray) -> tuple:
        diff = cv2.absdiff(prev_gray, curr_gray)
        mean_score = float(diff.mean()) / 255.0
        _, binary = cv2.threshold(
            diff, self.config.pixel_diff_thresh, 255, cv2.THRESH_BINARY,
        )
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, self._kernel)
        changed_ratio = cv2.countNonZero(binary) / float(binary.size)
        return mean_score, changed_ratio

    def on_sample_frame(
        self, device_id: str, frame_bgr: np.ndarray, frame_number: int,
    ) -> MotionResult:
        if not self.config.enabled:
            return MotionResult(reason='disabled')

        with self._lock:
            st = self._get_state(device_id)
            st.baseline_triggers += 1
            curr = self._to_small_gray(frame_bgr)
            prev = st.prev_gray
            st.prev_gray = curr

            if prev is None:
                return MotionResult(reason='warmup')

            mean_score, changed_ratio = self.evaluate(prev, curr)
            st.last_score = mean_score
            st.last_area_ratio = changed_ratio

            hit = (
                changed_ratio >= self.config.min_changed_area_ratio
                and mean_score >= self.config.min_mean_score
            )
            if hit:
                st.consecutive_hits += 1
            else:
                st.consecutive_hits = 0

            if frame_number <= st.cooldown_until:
                return MotionResult(
                    score=mean_score,
                    changed_area_ratio=changed_ratio,
                    reason='cooldown',
                    consecutive_hits=st.consecutive_hits,
                )

            if st.consecutive_hits >= self.config.consecutive_hits_required:
                st.motion_triggers += 1
                st.consecutive_hits = 0
                st.cooldown_until = frame_number + self.config.cooldown_frames
                return MotionResult(
                    triggered=True,
                    score=mean_score,
                    changed_area_ratio=changed_ratio,
                    reason='motion',
                    consecutive_hits=self.config.consecutive_hits_required,
                )

            return MotionResult(
                score=mean_score,
                changed_area_ratio=changed_ratio,
                reason='below_threshold',
                consecutive_hits=st.consecutive_hits,
            )

    def should_supplement_alert(self, device_id: str, frame_number: int) -> bool:
        """告警队列补检：最近一次采样命中运动且开启 alert_motion_sync。"""
        if not self.config.enabled or not self.config.alert_motion_sync:
            return False
        with self._lock:
            st = self._states.get(device_id)
            if not st:
                return False
            if frame_number <= st.cooldown_until:
                return False
            if (
                st.last_area_ratio >= self.config.min_changed_area_ratio
                and st.last_score >= self.config.min_mean_score
                and st.consecutive_hits >= self.config.consecutive_hits_required - 1
            ):
                st.supplement_triggers += 1
                return True
        return False
