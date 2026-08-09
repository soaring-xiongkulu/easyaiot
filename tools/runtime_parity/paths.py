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


def windows_runtime_path_entries(root: Optional[Path] = None) -> list[str]:
    """DLL directories for RUNTIME.exe on Windows (mirrors deploy.env.ps1)."""
    import sys

    if sys.platform != "win32":
        return []
    base = root or candidate_root()
    runtime = base / "RUNTIME"
    vendor = runtime / "vendor" / "win-x64"
    conda_pkgs = vendor / "conda-pkgs"
    entries = [
        runtime / "build-win" / "Release",
        conda_pkgs / "libprotobuf" / "Library" / "bin",
        conda_pkgs / "opencv" / "Library" / "bin",
        conda_pkgs / "ffmpeg" / "Library" / "bin",
        conda_pkgs / "jsoncpp" / "Library" / "bin",
        vendor / "_conda_ffmpeg4" / "Library" / "bin",
    ]
    for candidate in (
        "F:/anaconda/Library/bin",
        os.path.expanduser("~/anaconda3/Library/bin"),
        os.path.expanduser("~/miniconda3/Library/bin"),
    ):
        entries.append(Path(candidate))
    return [str(p) for p in entries if p.is_dir()]


def runtime_exe_candidates(root: Optional[Path] = None) -> list[Path]:
    """Search order for C++ RUNTIME binary."""
    base = root or candidate_root()
    names = [
        base / "RUNTIME" / "build-win" / "Release" / "RUNTIME.exe",
        base / "RUNTIME" / "build" / "Release" / "RUNTIME.exe",
        base / "RUNTIME" / "build" / "RUNTIME.exe",
        base / "RUNTIME" / "build" / "Release" / "RUNTIME",
        base / "RUNTIME" / "build" / "RUNTIME",
    ]
    return names
