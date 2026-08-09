"""Report writer for certify / run."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import report_path


def new_report(
    *,
    command: str,
    profile: Optional[str] = None,
    case_id: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "tool": "runtime_parity_gate",
        "command": command,
        "profile": profile,
        "case_id": case_id,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "ok": False,
        "cases": [],
        "summary": {"pass": 0, "fail": 0, "not_sampled": 0, "warn": 0},
    }


def write_report(report: Dict[str, Any], root: Optional[Path] = None) -> Path:
    out = report_path(root)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def bump_summary(report: Dict[str, Any], status: str) -> None:
    key = status if status in report["summary"] else "fail"
    report["summary"][key] = report["summary"].get(key, 0) + 1


def add_case_result(
    report: Dict[str, Any],
    case_id: str,
    layers: List[Dict[str, Any]],
    *,
    executor: str = "cpp",
) -> None:
    case_ok = all(l.get("status") == "pass" for l in layers)
    entry = {
        "case_id": case_id,
        "executor": executor,
        "ok": case_ok,
        "layers": layers,
    }
    report["cases"].append(entry)
    for layer in layers:
        bump_summary(report, layer.get("status", "fail"))
