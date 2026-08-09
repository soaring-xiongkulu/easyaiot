"""record-python command — oracle golden sampling."""

from __future__ import annotations

import os
import sys
from typing import List

from .manifest import find_case, load_manifest
from .paths import candidate_root, oracle_root
from .record_oracle_smoke import P0_CASES, run_record_oracle_smoke
from .report import add_case_result, new_report, write_report


def run_record_python(case_id: str) -> int:
    root = candidate_root()
    manifest = load_manifest(root)
    case = find_case(manifest, case_id)
    use_video = os.environ.get("RPARITY_USE_VIDEO", "").strip() in ("1", "true", "yes")

    if use_video:
        # Hook point for future: spawn oracle VIDEO task and parse logs.
        print(
            "WARN RPARITY_USE_VIDEO=1 set but full VIDEO integration not in Phase 0; "
            "falling back to intel-media smoke path.",
            file=sys.stderr,
        )

    # Phase 0 G-0.3: P0 cases use Intel sample-video smoke (non-placeholder).
    if case_id in P0_CASES:
        rc = run_record_oracle_smoke(case_id)
        if rc != 0:
            return rc
        from .artifacts import layer_file_map
        from .paths import golden_dir

        out_dir = golden_dir("python", case_id, root)
        report = new_report(command="record-python", case_id=case_id)
        layers: List[dict] = [
            {
                "layer": layer,
                "status": "recorded",
                "artifact": str(out_dir / fname),
                "note": "Intel sample-video smoke (oracle_smoke_intel_media)",
            }
            for layer, fname in layer_file_map(case).items()
        ]
        add_case_result(report, case_id, layers, executor="python")
        report["ok"] = False
        report["note"] = (
            "Smoke golden recorded from Intel media; certify parity still requires "
            "live oracle VIDEO samples"
        )
        out = write_report(report, root)
        print(f"record-python: case={case_id} executor=python (oracle={oracle_root()})")
        print(f"report: {out}")
        return 0

    # Non-P0: skeleton placeholder until VIDEO integration.
    from .artifacts import layer_file_map, write_skeleton_golden
    from .paths import golden_dir

    out_dir = golden_dir("python", case_id, root)
    written = write_skeleton_golden(out_dir, case, "python")
    print(f"record-python: case={case_id} executor=python (oracle={oracle_root()})")
    for p in written:
        print(f"  wrote {p}")

    report = new_report(command="record-python", case_id=case_id)
    layers = [
        {
            "layer": layer,
            "status": "placeholder",
            "artifact": str(out_dir / fname),
            "note": "MVP skeleton; replace with real oracle sample",
        }
        for layer, fname in layer_file_map(case).items()
    ]
    add_case_result(report, case_id, layers, executor="python")
    report["ok"] = False
    report["note"] = "MVP skeleton recorded; certify requires real oracle samples"
    out = write_report(report, root)
    print(f"report: {out}")
    return 0
