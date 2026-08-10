#!/usr/bin/env python3
"""VIDEO Java certify — Phase 0 gate runner."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from diff_layers import diff_case
from vj_common import find_case, load_manifest, phase0_case_ids, repo_root


def _run(cmd: List[str]) -> int:
    print("+", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(repo_root() / "tools" / "video_java"))


def _case_passes(layer_results: List[Dict[str, Any]]) -> bool:
    """Overall case ok only when every required layer status is pass (not exempt)."""
    return all(layer.get("status") == "pass" for layer in layer_results)


def _collect_exemptions(results: List[Dict[str, Any]]) -> List[str]:
    rows: List[str] = []
    for r in results:
        for layer in r["layers"]:
            if layer.get("status") == "exempt":
                ex_id = layer.get("exemption_id", "?")
                rows.append(f"{r['case_id']}/{layer['layer']}: {ex_id}")
    return rows


def certify_phase0(*, record_oracle: bool, sample_java: bool) -> int:
    manifest = load_manifest()
    case_ids = phase0_case_ids(manifest)
    results: List[Dict[str, Any]] = []
    all_ok = True

    for case_id in case_ids:
        case = find_case(manifest, case_id)
        layers = case.get("layers", ["api"])
        if record_oracle:
            rc = _run([sys.executable, "record_python.py", case_id])
            if rc != 0:
                print(f"WARN record_python failed for {case_id} (rc={rc}) — diff may use stale/missing python golden")
        if sample_java:
            rc = _run([sys.executable, "run_java.py", case_id])
            if rc != 0:
                print(f"WARN run_java failed for {case_id} (rc={rc})")
        try:
            _, layer_results = diff_case(case_id, layers)
            ok = _case_passes(layer_results)
        except Exception as exc:
            ok = False
            layer_results = [{"layer": "all", "status": "fail", "reason": str(exc)}]
        results.append({"case_id": case_id, "ok": ok, "layers": layer_results})
        all_ok = all_ok and ok
        print(f"certify: {case_id} ok={ok}")
        for layer in layer_results:
            print(f"  {layer['layer']}: {layer['status']} — {layer.get('reason', '')}")

    exemptions = _collect_exemptions(results)
    _write_gate_report(results, all_ok, exemptions)
    _update_certify_status(results, all_ok, exemptions)
    return 0 if all_ok else 1


def _write_gate_report(
    results: List[Dict[str, Any]], all_ok: bool, exemptions: List[str]
) -> None:
    gate = repo_root() / "docs" / "video-java" / "gates" / "PHASE_0_GATE.md"
    gate.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# PHASE 0 Gate — VIDEO Java minimal closed loop",
        "",
        f"**Status:** {'PASS' if all_ok else 'FAIL'}",
        f"**Updated:** {ts}",
        "",
        "Only layer status `pass` counts toward gate PASS. `exempt` layers are documented below but do not satisfy parity.",
        "",
        "## Commands",
        "",
        "```text",
        "mvn -f DEVICE/pom.xml -pl iot-video/iot-video-biz -am package -DskipTests",
        "python tools/video_java/doctor.py",
        "python tools/video_java/certify.py --phase 0",
        "```",
        "",
        "## Case results",
        "",
        "| case_id | ok | layers |",
        "|---------|----|--------|",
    ]
    for r in results:
        layer_summary = ", ".join(f"{l['layer']}:{l['status']}" for l in r["layers"])
        lines.append(f"| {r['case_id']} | {r['ok']} | {layer_summary} |")
    lines.extend(["", "## Documented exemptions (this run)", ""])
    if exemptions:
        for row in exemptions:
            lines.append(f"- {row}")
    else:
        lines.append("- (none)")
    lines.append("")
    gate.write_text("\n".join(lines), encoding="utf-8")
    print(f"gate report: {gate}")


def _update_certify_status(
    results: List[Dict[str, Any]], all_ok: bool, exemptions: List[str]
) -> None:
    path = repo_root() / "docs" / "video-java" / "CERTIFY_STATUS.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary = ", ".join(f"{r['case_id']}={'PASS' if r['ok'] else 'FAIL'}" for r in results)
    ex_note = f"; exemptions: {', '.join(exemptions)}" if exemptions else ""
    body = f"""# VIDEO Java — CERTIFY_STATUS

| Phase | Status | Updated | Notes |
|-------|--------|---------|-------|
| Phase -1 | PASS | 2026-08-10 | shell + doctor |
| Phase 0 | {'PASS' if all_ok else 'FAIL'} | {ts} | {summary}{ex_note} |

P0 direct: oracle `:6000` / candidate `:48096`.
"""
    path.write_text(body, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="VIDEO Java certify")
    parser.add_argument("--phase", type=int, default=0)
    parser.add_argument("--no-record", action="store_true", help="skip oracle recording")
    parser.add_argument("--no-java", action="store_true", help="skip java sampling")
    args = parser.parse_args()
    if args.phase != 0:
        print(f"only phase 0 supported (got {args.phase})")
        return 2
    return certify_phase0(record_oracle=not args.no_record, sample_java=not args.no_java)


if __name__ == "__main__":
    raise SystemExit(main())
