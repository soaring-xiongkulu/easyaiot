#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G-1.3 smoke: VIDEO AlgorithmTaskDaemon launches executor=cpp (RUNTIME.exe).

Mirrors algorithm_task_launcher_service.start_task_services cpp path without DB:
  generate_runtime_ini → AlgorithmTaskDaemon → RUNTIME subprocess.

Prerequisite: `. .\\RUNTIME\\scripts\\deploy.env.ps1` (PATH for ORT/OpenCV DLLs).

Exit 0 when daemon log shows task start + infer_ep=cpu (or configured EP).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

_REPO = Path(__file__).resolve().parents[2]
_VIDEO = _REPO / "VIDEO"
if str(_VIDEO) not in sys.path:
    sys.path.insert(0, str(_VIDEO))

DEFAULT_TASK_ID = 91301
DEFAULT_WAIT_SEC = 45


def _media_path(name: str = "people-detection.mp4") -> Path:
    p = _REPO / "testdata" / "runtime-parity" / "media" / name
    if not p.is_file():
        raise FileNotFoundError(
            f"media missing: {p}\n"
            "Run: python tools/runtime_parity/fetch_parity_media.py"
        )
    return p.resolve()


def _build_task(task_id: int, media: Path) -> SimpleNamespace:
    device = SimpleNamespace(
        id=913,
        name="g13_smoke",
        source=str(media),
        rtsp_direct=None,
        ai_rtmp_stream=None,
    )
    return SimpleNamespace(
        id=task_id,
        task_type="realtime",
        executor="cpp",
        prefer_gpu=False,
        model_ids=None,
        model_names="detection",
        detect_conf=0.5,
        alert_event_enabled=False,
        alert_event_suppress_time=30,
        rtmp_output_url="",
        extract_interval=8,
        runtime_control_port=8000 + (task_id % 1000),
        devices=[device],
    )


def _tail_for_markers(log_dir: Path, timeout: float) -> tuple[bool, str]:
    """Wait for executor=cpp launch + infer_ep in daemon/RUNTIME logs."""
    deadline = time.time() + timeout
    saw_executor = False
    saw_infer = False
    infer_line = ""
    while time.time() < deadline:
        for log_file in sorted(log_dir.glob("*.log")):
            try:
                text = log_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "executor=cpp" in text or "# executor: cpp" in text:
                saw_executor = True
            for line in text.splitlines():
                if "infer_ep=" in line:
                    saw_infer = True
                    infer_line = line.strip()
                if "RUNTIME.exe" in line and "命令:" in line:
                    saw_executor = True
        if saw_executor and saw_infer:
            return True, infer_line
        time.sleep(0.5)
    return False, infer_line


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", type=int, default=DEFAULT_TASK_ID)
    parser.add_argument("--media", default="people-detection.mp4")
    parser.add_argument("--wait-sec", type=float, default=DEFAULT_WAIT_SEC)
    args = parser.parse_args(argv)

    os.environ.setdefault("RUNTIME_FORCE_CPU", "true")
    os.environ.setdefault("USE_GPU", "false")
    os.environ.setdefault("RUNTIME_PREFER_GPU", "false")

    media = _media_path(args.media)
    task = _build_task(args.task_id, media)
    log_path = _REPO / "logs" / f"g13_task_{args.task_id}"
    log_path.mkdir(parents=True, exist_ok=True)

    from app.services.runtime_config_service import (  # noqa: WPS433
        ensure_runtime_bin_ready,
        generate_runtime_ini,
    )
    from app.services.algorithm_task_daemon import AlgorithmTaskDaemon  # noqa: WPS433

    runtime_bin = ensure_runtime_bin_ready(task)
    runtime_ini = generate_runtime_ini(task, str(log_path))
    print(f"INFO RUNTIME_BIN={runtime_bin}")
    print(f"INFO runtime_ini={runtime_ini}")

    extra_env = {
        "RUNTIME_FORCE_CPU": "true",
        "USE_GPU": "false",
        "RUNTIME_PREFER_GPU": "false",
    }
    daemon = AlgorithmTaskDaemon(
        task_id=args.task_id,
        log_path=str(log_path),
        task_type="realtime",
        executor="cpp",
        runtime_bin=runtime_bin,
        runtime_ini=runtime_ini,
        extra_env=extra_env,
    )

    ok, infer_line = _tail_for_markers(log_path, args.wait_sec)
    print(f"INFO daemon_log_dir={log_path}")
    if infer_line:
        print(f"INFO {infer_line}")

    try:
        daemon.stop()
        daemon.join_daemon_thread(timeout=15)
    except Exception as exc:  # noqa: BLE001
        print(f"WARN stop daemon: {exc}", file=sys.stderr)

    if ok:
        print("G-1.3 PASS: VIDEO daemon launched cpp RUNTIME; infer_ep observed")
        return 0

    print(
        "G-1.3 FAIL: timeout waiting for executor=cpp + infer_ep in daemon logs",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
