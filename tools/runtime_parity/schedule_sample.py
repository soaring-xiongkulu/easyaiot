"""Schedule sampling helpers for L_schedule (G-4.3)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import candidate_root


def load_cpp_parity_sample(log_dir: Path) -> Dict[str, Any]:
    path = log_dir / "parity_sample.json"
    if not path.is_file():
        return {}
    try:
        import json

        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def synthetic_snap_schedule(
    *,
    case_id: str,
    cron_expression: str,
    duration_sec: float = 20.0,
    interval_sec: float = 5.0,
) -> Dict[str, Any]:
    """Oracle smoke schedule for snap cron (deterministic stub slots)."""
    now = time.time()
    events: List[Dict[str, Any]] = []
    t = now - duration_sec
    slot_i = 0
    while t <= now:
        slot_i += 1
        events.append(
            {
                "kind": "cron_slot",
                "device_id": "cpp_sample",
                "slot_key": f"smoke_slot_{slot_i}",
                "unix_ts": t,
            }
        )
        t += interval_sec
    return {
        "cron_expression": cron_expression,
        "slot_count": len(events),
        "patrol_count": 0,
        "events": events,
        "mean_interval_sec": interval_sec,
        "device_intervals": {},
    }


def synthetic_patrol_schedule(
    *,
    device_ids: List[str],
    interval_sec: float,
    duration_sec: float = 20.0,
    mode: str = "pool",
) -> Dict[str, Any]:
    """Oracle smoke schedule for patrol pool/hybrid."""
    now = time.time()
    events: List[Dict[str, Any]] = []
    by_device: Dict[str, List[float]] = {d: [] for d in device_ids}
    t = now - duration_sec
    while t <= now:
        for did in device_ids:
            events.append(
                {
                    "kind": "patrol",
                    "device_id": did,
                    "slot_key": "",
                    "unix_ts": t,
                }
            )
            by_device[did].append(t)
        t += interval_sec
    intervals: Dict[str, List[float]] = {}
    means: List[float] = []
    for did, ts in by_device.items():
        deltas = [ts[i] - ts[i - 1] for i in range(1, len(ts))]
        intervals[did] = deltas
        means.extend(deltas)
    return {
        "mode": mode,
        "slot_count": 0,
        "patrol_count": len(events),
        "events": events,
        "mean_interval_sec": (sum(means) / len(means)) if means else interval_sec,
        "device_intervals": intervals,
    }


def schedule_from_parity(parity: Dict[str, Any]) -> Dict[str, Any]:
    schedule = parity.get("schedule") or {}
    return {
        "slot_count": int(schedule.get("slot_count") or 0),
        "patrol_count": int(schedule.get("patrol_count") or 0),
        "events": schedule.get("events") or [],
        "mean_interval_sec": float(schedule.get("mean_interval_sec") or 0.0),
        "device_intervals": schedule.get("device_intervals") or {},
    }
