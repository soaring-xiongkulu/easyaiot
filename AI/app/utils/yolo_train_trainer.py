"""Ultralytics trainer adaptations required by EasyAIoT multi-GPU jobs."""
from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path

import torch
from ultralytics.models.yolo.detect.train import DetectionTrainer
from ultralytics.utils import RANK

from app.utils.train_runtime import TrainingProgressSnapshot, write_progress_snapshot


def _env_enabled(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ('1', 'true', 'yes', 'on')


@contextmanager
def allow_unused_ddp_parameters(*, enabled: bool):
    """Enable DDP graph traversal for conditional YOLO loss branches."""
    original_ddp = torch.nn.parallel.DistributedDataParallel

    def compatible_ddp(*args, **kwargs):
        if enabled and not kwargs.get('static_graph'):
            kwargs.setdefault('find_unused_parameters', True)
        return original_ddp(*args, **kwargs)

    torch.nn.parallel.DistributedDataParallel = compatible_ddp
    try:
        yield
    finally:
        if torch.nn.parallel.DistributedDataParallel is compatible_ddp:
            torch.nn.parallel.DistributedDataParallel = original_ddp


class ReliableDetectionTrainer(DetectionTrainer):
    """Detection trainer with DDP-safe loss branches and rank-0 progress snapshots."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._platform_batch_count = 0
        self._platform_val_batch_count = 0
        self._platform_last_snapshot_at = 0.0
        self.add_callback('on_train_start', self._on_platform_train_start)
        self.add_callback('on_train_epoch_start', self._on_platform_epoch_start)
        self.add_callback('on_train_batch_end', self._on_platform_batch_end)
        self.add_callback('on_train_epoch_end', self._on_platform_epoch_end)
        self.add_callback('on_fit_epoch_end', self._on_platform_fit_epoch_end)
        self.add_callback('on_val_start', self._on_platform_val_start)
        self.add_callback('on_val_batch_end', self._on_platform_val_batch_end)
        self.add_callback('on_val_end', self._on_platform_val_end)
        self.add_callback('on_train_end', self._on_platform_train_end)

    def _setup_train(self):
        if int(getattr(self, 'world_size', 1) or 1) <= 1:
            return super()._setup_train()
        with allow_unused_ddp_parameters(
            enabled=_env_enabled('TRAIN_DDP_FIND_UNUSED_PARAMETERS', True)
        ):
            return super()._setup_train()

    def _platform_model_dir(self) -> Path:
        project = getattr(self.args, 'project', None)
        if project:
            return Path(str(project))
        return Path(self.save_dir).parent

    def _platform_total_batches(self) -> int:
        train_loader = getattr(self, 'train_loader', None)
        try:
            return len(train_loader) if train_loader is not None else 0
        except TypeError:
            return 0

    def _write_platform_snapshot(
        self,
        *,
        phase: str,
        completed_epochs: int,
        force: bool = False,
        batch: int | None = None,
        total_batches: int | None = None,
    ) -> None:
        if RANK not in (-1, 0):
            return
        now = time.time()
        interval = max(1.0, float(os.getenv('TRAIN_PROGRESS_SNAPSHOT_SECONDS', '5')))
        if not force and now - self._platform_last_snapshot_at < interval:
            return
        self._platform_last_snapshot_at = now
        write_progress_snapshot(
            self._platform_model_dir(),
            TrainingProgressSnapshot(
                epoch=max(1, int(getattr(self, 'epoch', 0)) + 1),
                completed_epochs=max(0, int(completed_epochs)),
                batch=max(0, int(self._platform_batch_count if batch is None else batch)),
                total_batches=max(0, int(
                    self._platform_total_batches() if total_batches is None else total_batches
                )),
                phase=phase,
                updated_at=now,
            ),
        )

    def _on_platform_train_start(self, _trainer) -> None:
        self._write_platform_snapshot(
            phase='train',
            completed_epochs=max(0, int(getattr(self, 'start_epoch', 0))),
            force=True,
        )

    def _on_platform_epoch_start(self, _trainer) -> None:
        self._platform_batch_count = 0
        self._write_platform_snapshot(
            phase='train',
            completed_epochs=max(0, int(getattr(self, 'epoch', 0))),
            force=True,
        )

    def _on_platform_batch_end(self, _trainer) -> None:
        self._platform_batch_count += 1
        self._write_platform_snapshot(
            phase='train',
            completed_epochs=max(0, int(getattr(self, 'epoch', 0))),
            force=self._platform_batch_count >= self._platform_total_batches(),
        )

    def _on_platform_epoch_end(self, _trainer) -> None:
        self._write_platform_snapshot(
            phase='validation',
            completed_epochs=max(0, int(getattr(self, 'epoch', 0))),
            force=True,
        )

    def _on_platform_fit_epoch_end(self, _trainer) -> None:
        self._write_platform_snapshot(
            phase='train',
            completed_epochs=max(0, int(getattr(self, 'epoch', 0)) + 1),
            force=True,
        )

    def _on_platform_val_start(self, validator) -> None:
        self._platform_val_batch_count = 0
        try:
            total_batches = len(validator.dataloader)
        except (AttributeError, TypeError):
            total_batches = 0
        self._write_platform_snapshot(
            phase='validation',
            completed_epochs=max(0, int(getattr(self, 'epoch', 0))),
            force=True,
            batch=0,
            total_batches=total_batches,
        )

    def _on_platform_val_batch_end(self, validator) -> None:
        self._platform_val_batch_count += 1
        try:
            total_batches = len(validator.dataloader)
        except (AttributeError, TypeError):
            total_batches = 0
        self._write_platform_snapshot(
            phase='validation',
            completed_epochs=max(0, int(getattr(self, 'epoch', 0))),
            force=bool(total_batches and self._platform_val_batch_count >= total_batches),
            batch=self._platform_val_batch_count,
            total_batches=total_batches,
        )

    def _on_platform_val_end(self, validator) -> None:
        try:
            total_batches = len(validator.dataloader)
        except (AttributeError, TypeError):
            total_batches = self._platform_val_batch_count
        self._write_platform_snapshot(
            phase='validation',
            completed_epochs=max(0, int(getattr(self, 'epoch', 0))),
            force=True,
            batch=self._platform_val_batch_count,
            total_batches=total_batches,
        )

    def _on_platform_train_end(self, _trainer) -> None:
        self._write_platform_snapshot(
            phase='completed',
            completed_epochs=max(0, int(getattr(self, 'epoch', 0)) + 1),
            force=True,
        )
