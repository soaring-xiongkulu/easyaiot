"""Bootstrap retired VIDEO Flask app modules for standalone inference CLI workers."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def repo_root() -> Path:
    env = (os.getenv("ACME_ROOT") or os.getenv("RUNTIME_ROOT") or "").strip()
    if env:
        return Path(env).resolve()
    # inference_workers -> scripts -> VIDEO -> repo root
    return Path(__file__).resolve().parents[3]


def bootstrap() -> Path:
    root = repo_root()
    retired = root / "VIDEO" / "_retired_python_video"
    if not retired.is_dir():
        raise RuntimeError(f"retired python video not found: {retired}")
    retired_str = str(retired)
    if retired_str not in sys.path:
        sys.path.insert(0, retired_str)
    os.chdir(retired_str)
    return retired
