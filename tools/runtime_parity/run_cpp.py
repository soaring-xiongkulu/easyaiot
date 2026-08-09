"""run --executor cpp — candidate RUNTIME sampling."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from .artifacts import layer_file_map, write_skeleton_golden
from .manifest import find_case, load_manifest
from .paths import candidate_root, golden_dir, runtime_exe_candidates
from .report import add_case_result, new_report, write_report


def _find_runtime() -> Optional[Path]:
    for p in runtime_exe_candidates():
        if p.is_file():
            return p
    return None


def run_cpp(case_id: str) -> int:
    root = candidate_root()
    manifest = load_manifest(root)
    case = find_case(manifest, case_id)

    runtime = _find_runtime()
    out_dir = golden_dir("cpp", case_id, root)

    exit_code = 0
    if runtime is None:
        print("WARN RUNTIME binary not found; writing not_sampled skeleton", file=sys.stderr)
        write_skeleton_golden(out_dir, case, "cpp", runtime_found=False)
    else:
        print(f"INFO found RUNTIME at {runtime}")
        # MVP: do not spawn RUNTIME against production stack; skeleton only.
        print(
            "WARN Phase 0 MVP does not launch RUNTIME process; writing placeholder skeleton",
            file=sys.stderr,
        )
        write_skeleton_golden(out_dir, case, "cpp", runtime_found=True)

    layers = []
    for layer, fname in layer_file_map(case).items():
        artifact = out_dir / fname
        status = "not_sampled"
        reason = "RUNTIME not executed in MVP"
        if artifact.is_file():
            data = json.loads(artifact.read_text(encoding="utf-8"))
            status = data.get("status", "not_sampled")
            reason = data.get("reason", reason)
        layers.append(
            {
                "layer": layer,
                "status": "fail" if status in ("not_sampled", "placeholder") else status,
                "artifact": str(artifact),
                "reason": reason,
            }
        )

    report = new_report(command="run", case_id=case_id)
    add_case_result(report, case_id, layers, executor="cpp")
    report["ok"] = False
    report["runtime_binary"] = str(runtime) if runtime else None
    out = write_report(report, root)
    print(f"run-cpp: case={case_id} artifacts under {out_dir}")
    print(f"report: {out}")
    return exit_code
