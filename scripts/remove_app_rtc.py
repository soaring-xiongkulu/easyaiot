#!/usr/bin/env python3
"""Delete APP + RTC module trees (and a few dedicated files).

Content/reference edits are NOT done here — use the editor on those.

Modes:
  --dry-run  Plan only (default). Write report JSON. No deletes.
  --apply    Execute deletes after human review of dry-run.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List


ROOT = Path(r"F:/acme")
REPORT_DIR = ROOT / "scripts" / "reports"


@dataclass
class Op:
    action: str  # delete_tree | delete_file
    path: str
    detail: str = ""
    bytes_hint: int = 0
    file_count: int = 0


@dataclass
class Report:
    mode: str
    started_at: str
    ops: List[Op] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tree_stats(p: Path) -> tuple[int, int]:
    n, b = 0, 0
    if not p.exists():
        return 0, 0
    for f in p.rglob("*"):
        if f.is_file():
            n += 1
            try:
                b += f.stat().st_size
            except OSError:
                pass
    return n, b


# Trees to remove
DELETE_TREES = [
    ROOT / "APP",
    ROOT / "RTC",
]

# Standalone files that only exist for APP/RTC consumer bridge (not industrial WebRTC players)
DELETE_FILES = [
    ROOT / "WEB" / "src" / "views" / "camera" / "components" / "DeviceCreate" / "panels" / "RtcPlatformPanel.vue",
    ROOT / "VIDEO" / "app" / "utils" / "rtc_source.py",
]


def plan(report: Report) -> None:
    report.notes.append(
        "Content patches (install scripts, nginx, WEB/VIDEO API, README) are manual editor edits — not this script."
    )
    report.notes.append(
        "Do NOT delete WEB rtcPlayer.vue / ZLMRTCClient.js (industrial WebRTC playback, unrelated to RTC module)."
    )
    for t in DELETE_TREES:
        n, b = tree_stats(t)
        if t.exists():
            report.ops.append(
                Op("delete_tree", str(t), detail=f"remove module tree ({n} files)", bytes_hint=b, file_count=n)
            )
        else:
            report.notes.append(f"already absent: {t}")
    for f in DELETE_FILES:
        if f.exists():
            try:
                sz = f.stat().st_size
            except OSError:
                sz = 0
            report.ops.append(Op("delete_file", str(f), detail="RTC/APP-only source file", bytes_hint=sz, file_count=1))
        else:
            report.notes.append(f"already absent: {f}")


def _rmtree_win(path: Path) -> None:
    def onerror(func, p, _exc_info):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except Exception:
            raise

    last = None
    for i in range(5):
        try:
            if not path.exists():
                return
            shutil.rmtree(path, onerror=onerror)
            return
        except PermissionError as e:
            last = e
            time.sleep(0.4 * (i + 1))
    tomb = path.with_name(path.name + ".__removed__")
    try:
        if tomb.exists():
            shutil.rmtree(tomb, onerror=onerror)
        path.rename(tomb)
        print(f"[apply] WARN renamed locked {path} -> {tomb}")
        return
    except Exception as e2:
        raise last from e2


def apply_ops(report: Report) -> None:
    for op in report.ops:
        p = Path(op.path)
        if op.action == "delete_tree":
            if p.exists():
                _rmtree_win(p)
                print(f"[apply] deleted tree {p} exists_now={p.exists()}")
            else:
                print(f"[apply] already gone {p}")
        elif op.action == "delete_file":
            if p.exists():
                p.unlink()
                print(f"[apply] deleted file {p}")
            else:
                print(f"[apply] already gone {p}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", default=True)
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    mode = "apply" if args.apply else "dry-run"

    report = Report(mode=mode, started_at=utc_now())
    plan(report)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": mode,
        "started_at": report.started_at,
        "notes": report.notes,
        "errors": report.errors,
        "ops": [asdict(o) for o in report.ops],
        "op_counts": {},
    }
    for o in report.ops:
        payload["op_counts"][o.action] = payload["op_counts"].get(o.action, 0) + 1
    out = REPORT_DIR / f"remove_app_rtc_{mode}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\n[report] {out}")

    if mode == "dry-run":
        print("\nDRY-RUN only. Review ops, then --apply after content edits (or before — order flexible).")
        return 0

    apply_ops(report)
    payload["finished_at"] = utc_now()
    out_a = REPORT_DIR / "remove_app_rtc_apply.json"
    out_a.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[report] {out_a}")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
