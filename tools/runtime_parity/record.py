"""record-python command — oracle golden sampling (MVP skeleton)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional

from .artifacts import write_skeleton_golden
from .manifest import find_case, load_manifest
from .paths import candidate_root, golden_dir, oracle_root
from .report import add_case_result, new_report, write_report


def _find_runtime_for_oracle() -> Optional[Path]:
    """MVP: detect if we could invoke VIDEO; does not start services."""
    return None


def run_record_python(case_id: str) -> int:
    root = candidate_root()
    manifest = load_manifest(root)
    case = find_case(manifest, case_id)

    out_dir = golden_dir("python", case_id, root)
    use_video = os.environ.get("RPARITY_USE_VIDEO", "").strip() in ("1", "true", "yes")

    if use_video:
        # Hook point for future: spawn oracle VIDEO task and parse logs.
        # MVP does not modify production processes.
        print(
            "WARN RPARITY_USE_VIDEO=1 set but full VIDEO integration not in Phase 0 MVP; "
            "writing skeleton golden.",
            file=sys.stderr,
        )

    written = write_skeleton_golden(out_dir, case, "python")
    print(f"record-python: case={case_id} executor=python (oracle={oracle_root()})")
    for p in written:
        print(f"  wrote {p}")

    report = new_report(command="record-python", case_id=case_id)
    from .artifacts import layer_file_map

    layers = [
        {
            "layer": layer,
            "status": "recorded",
            "artifact": str(out_dir / fname),
            "note": "MVP skeleton; replace with real oracle sample",
        }
        for layer, fname in layer_file_map(case).items()
    ]
    add_case_result(report, case_id, layers, executor="python")
  # MVP skeleton is not full parity — overall ok stays false
    report["ok"] = False
    report["note"] = "MVP skeleton recorded; certify requires real oracle samples"
    out = write_report(report, root)
    print(f"report: {out}")
    return 0

