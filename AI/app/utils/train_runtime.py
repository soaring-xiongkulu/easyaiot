"""Local training resource leases and cross-process progress snapshots."""
from __future__ import annotations

import json
import math
import os
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


PROGRESS_SNAPSHOT_FILENAME = '.train-progress.json'


class GpuLeaseConflict(RuntimeError):
    def __init__(self, gpu_ids: Iterable[int], task_ids: Iterable[int]):
        self.gpu_ids = sorted({int(gpu_id) for gpu_id in gpu_ids})
        self.task_ids = sorted({int(task_id) for task_id in task_ids})
        gpu_text = ','.join(str(gpu_id) for gpu_id in self.gpu_ids)
        task_text = ','.join(str(task_id) for task_id in self.task_ids)
        super().__init__(f'GPU {gpu_text} 正被训练任务 {task_text} 使用，请等待任务结束后重试')


class LocalGpuLeaseRegistry:
    """Process-local, atomic ownership registry for local training GPUs."""

    def __init__(self):
        self._lock = threading.RLock()
        self._leases: dict[int, tuple[int, ...]] = {}

    def reserve(self, task_id: int, gpu_ids: Iterable[int] | None) -> None:
        requested = tuple(sorted({int(gpu_id) for gpu_id in (gpu_ids or [])}))
        if not requested:
            return
        task_id = int(task_id)
        with self._lock:
            conflicts: dict[int, set[int]] = {}
            requested_set = set(requested)
            for owner_task_id, owner_gpu_ids in self._leases.items():
                if owner_task_id == task_id:
                    continue
                overlap = requested_set.intersection(owner_gpu_ids)
                if overlap:
                    conflicts[owner_task_id] = overlap
            if conflicts:
                raise GpuLeaseConflict(
                    gpu_ids=set().union(*conflicts.values()),
                    task_ids=conflicts.keys(),
                )
            self._leases[task_id] = requested

    def release(self, task_id: int) -> None:
        with self._lock:
            self._leases.pop(int(task_id), None)

    def snapshot(self) -> dict[int, tuple[int, ...]]:
        with self._lock:
            return dict(self._leases)


@dataclass(frozen=True)
class TrainingProgressSnapshot:
    epoch: int
    completed_epochs: int
    batch: int
    total_batches: int
    phase: str
    updated_at: float

    @classmethod
    def from_dict(cls, value: dict) -> 'TrainingProgressSnapshot':
        return cls(
            epoch=max(0, int(value.get('epoch') or 0)),
            completed_epochs=max(0, int(value.get('completed_epochs') or 0)),
            batch=max(0, int(value.get('batch') or 0)),
            total_batches=max(0, int(value.get('total_batches') or 0)),
            phase=str(value.get('phase') or 'train'),
            updated_at=float(value.get('updated_at') or 0),
        )


def progress_snapshot_path(model_dir: str | os.PathLike) -> Path:
    return Path(model_dir) / PROGRESS_SNAPSHOT_FILENAME


def write_progress_snapshot(
    model_dir: str | os.PathLike,
    snapshot: TrainingProgressSnapshot,
) -> None:
    path = progress_snapshot_path(model_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(
        f'{path.name}.{os.getpid()}.{threading.get_ident()}.tmp'
    )
    try:
        with temp_path.open('w', encoding='utf-8') as snapshot_file:
            json.dump(asdict(snapshot), snapshot_file, ensure_ascii=True)
            snapshot_file.flush()
            os.fsync(snapshot_file.fileno())
        os.replace(temp_path, path)
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


def read_progress_snapshot(
    model_dir: str | os.PathLike,
) -> TrainingProgressSnapshot | None:
    path = progress_snapshot_path(model_dir)
    try:
        with path.open('r', encoding='utf-8') as snapshot_file:
            value = json.load(snapshot_file)
        if not isinstance(value, dict):
            return None
        return TrainingProgressSnapshot.from_dict(value)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def clear_progress_snapshot(model_dir: str | os.PathLike) -> None:
    try:
        progress_snapshot_path(model_dir).unlink(missing_ok=True)
    except OSError:
        pass


def calculate_snapshot_progress(
    snapshot: TrainingProgressSnapshot,
    *,
    total_epochs: int,
    current_progress: int = 0,
) -> int:
    total_epochs = max(1, int(total_epochs))
    completed_epochs = min(total_epochs, max(0, int(snapshot.completed_epochs)))
    if snapshot.total_batches > 0 and snapshot.epoch <= total_epochs:
        epoch_base = max(completed_epochs, max(0, int(snapshot.epoch) - 1))
        completed_units = epoch_base * snapshot.total_batches + min(
            snapshot.total_batches,
            max(0, int(snapshot.batch)),
        )
        total_units = total_epochs * snapshot.total_batches
        progress_delta = math.ceil(completed_units * 74 / total_units)
    else:
        progress_delta = math.ceil(completed_epochs * 74 / total_epochs)
    return min(89, max(16, int(current_progress or 0), 15 + progress_delta))


def is_progress_snapshot_stalled(
    snapshot: TrainingProgressSnapshot | None,
    *,
    now: float,
    timeout_seconds: float,
    started_at: float | None = None,
) -> bool:
    timeout_seconds = max(1.0, float(timeout_seconds))
    activity_at = snapshot.updated_at if snapshot is not None else started_at
    if activity_at is None:
        return False
    return float(now) - float(activity_at) > timeout_seconds
