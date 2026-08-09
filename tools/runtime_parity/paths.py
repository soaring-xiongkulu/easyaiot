"""Path resolution for runtime-parity gate (reads ACME_*_ROOT)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def _norm(p: Path) -> Path:
    return p.expanduser().resolve(strict=False)


def candidate_root() -> Path:
    env = os.environ.get("ACME_CANDIDATE_ROOT", "").strip()
    if env:
        return _norm(Path(env))
    return _norm(Path.cwd())


def oracle_root() -> Path:
    env = os.environ.get("ACME_ORACLE_ROOT", "").strip()
    if env:
        return _norm(Path(env))
    return candidate_root()


def testdata_root(root: Optional[Path] = None) -> Path:
    base = root or candidate_root()
    return base / "testdata" / "runtime-parity"


def manifest_path(root: Optional[Path] = None) -> Path:
    return testdata_root(root) / "manifest.json"


def thresholds_path(root: Optional[Path] = None) -> Path:
    return testdata_root(root) / "thresholds.json"


def golden_dir(executor: str, case_id: str, root: Optional[Path] = None) -> Path:
    return testdata_root(root) / "golden" / executor / case_id


def video_golden_dir(case_id: str, root: Optional[Path] = None) -> Path:
    return testdata_root(root) / "golden" / "video" / case_id


def logs_dir(root: Optional[Path] = None) -> Path:
    d = (root or candidate_root()) / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def report_path(root: Optional[Path] = None) -> Path:
    return logs_dir(root) / "runtime_parity_report.json"


def runtime_exe_candidates(root: Optional[Path] = None) -> list[Path]:
    """Search order for C++ RUNTIME binary."""
    base = root or candidate_root()
    names = [
        base / "RUNTIME" / "build" / "Release" / "RUNTIME.exe",
        base / "RUNTIME" / "build" / "RUNTIME.exe",
        base / "RUNTIME" / "build" / "Release" / "RUNTIME",
        base / "RUNTIME" / "build" / "RUNTIME",
    ]
    return names
