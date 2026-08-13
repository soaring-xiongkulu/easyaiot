"""工作区活跃时间存储 + 闲置停机。"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Dict, Optional

logger = logging.getLogger('easyaiot-idea.idle')


class ActivityStore:
    """持久化 last_active，避免依赖不可变的 Docker label。"""

    def __init__(self, data_dir: str) -> None:
        self.path = os.path.join(data_dir, 'activity.json')
        self._lock = threading.Lock()
        os.makedirs(data_dir, exist_ok=True)

    def _load(self) -> Dict[str, float]:
        if not os.path.isfile(self.path):
            return {}
        try:
            with open(self.path, encoding='utf-8') as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                return {str(k): float(v) for k, v in raw.items()}
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            logger.warning('failed to read activity store %s', self.path)
        return {}

    def _save(self, data: Dict[str, float]) -> None:
        tmp = f'{self.path}.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        os.replace(tmp, self.path)

    def touch(self, workspace_id: str, when: Optional[float] = None) -> float:
        ts = when if when is not None else time.time()
        with self._lock:
            data = self._load()
            data[workspace_id] = ts
            self._save(data)
        return ts

    def get(self, workspace_id: str) -> Optional[float]:
        with self._lock:
            return self._load().get(workspace_id)

    def remove(self, workspace_id: str) -> None:
        with self._lock:
            data = self._load()
            if workspace_id in data:
                del data[workspace_id]
                self._save(data)


class IdleReaper:
    def __init__(self, ops, idle_hours: float, check_seconds: int = 600) -> None:
        self.ops = ops
        self.idle_hours = max(0.0, float(idle_hours))
        self.check_seconds = max(60, int(check_seconds))
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self.idle_hours <= 0:
            logger.info('idle reaper disabled (IDEA_IDLE_TIMEOUT_HOURS<=0)')
            return
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, name='idea-idle-reaper', daemon=True)
        self._thread.start()
        logger.info(
            'idle reaper started: timeout=%sh check=%ss',
            self.idle_hours,
            self.check_seconds,
        )

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.wait(self.check_seconds):
            try:
                result = self.ops.reap_idle_workspaces()
                if result.get('stopped'):
                    logger.info('idle reaper stopped: %s', result['stopped'])
            except Exception:  # noqa: BLE001
                logger.exception('idle reaper tick failed')
