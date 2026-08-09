"""certify — layered diff skeleton (Phase 0 MVP)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .artifacts import layer_file_map
from .manifest import find_case, load_manifest, load_thresholds, parse_cases
from .paths import candidate_root, golden_dir, report_path
from .report import add_case_result, new_report, write_report


def _load_layer(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _diff_layer(
    layer: str,
    py_path: Path,
    cpp_path: Path,
    thresholds: Dict[str, Any],
) -> Dict[str, Any]:
    py_data = _load_layer(py_path)
    cpp_data = _load_layer(cpp_path)

    if py_data is None:
        return {
            "layer": layer,
            "status": "fail",
            "reason": f"missing python golden: {py_path}",
        }
    if cpp_data is None:
        return {
            "layer": layer,
            "status": "not_sampled",
            "reason": f"missing cpp golden: {cpp_path}",
        }

    py_status = py_data.get("status", "unknown")
    cpp_status = cpp_data.get("status", "unknown")

    if cpp_status == "not_sampled":
        return {
            "layer": layer,
            "status": "not_sampled",
            "reason": cpp_data.get("reason", "cpp not sampled"),
            "python_artifact": str(py_path),
            "cpp_artifact": str(cpp_path),
        }
    if py_status == "placeholder" or cpp_status == "placeholder":
        return {
            "layer": layer,
            "status": "fail",
            "reason": "MVP placeholder artifacts cannot certify pass",
            "python_artifact": str(py_path),
            "cpp_artifact": str(cpp_path),
        }

    # Future: real IoU / alarm count diff using thresholds
    return {
        "layer": layer,
        "status": "fail",
        "reason": "diff not implemented in Phase 0 MVP",
        "python_artifact": str(py_path),
        "cpp_artifact": str(cpp_path),
        "thresholds_ref": list(thresholds.keys()),
    }


def certify_case(case_id: str, profile: Optional[str] = None) -> Dict[str, Any]:
    root = candidate_root()
    manifest = load_manifest(root)
    thresholds_data = load_thresholds(root)
    case = find_case(manifest, case_id)

    py_base = golden_dir("python", case_id, root)
    cpp_base = golden_dir("cpp", case_id, root)

    layer_results: List[Dict[str, Any]] = []
    for layer, fname in layer_file_map(case).items():
        result = _diff_layer(layer, py_base / fname, cpp_base / fname, thresholds_data)
        layer_results.append(result)

    return {
        "case_id": case_id,
        "profile": profile,
        "ok": False,
        "layers": layer_results,
    }


def run_certify(case_id: Optional[str] = None, profile: Optional[str] = None) -> int:
    root = candidate_root()
    manifest = load_manifest(root)
    report = new_report(command="certify", profile=profile, case_id=case_id)

    case_ids: List[str]
    if case_id:
        case_ids = [case_id]
    elif profile:
        filt = manifest.get("profiles", {}).get(profile, {}).get("case_filter", "P0")
        case_ids = [c.id for c in parse_cases(manifest) if c.priority == filt]
    else:
        case_ids = [c.id for c in parse_cases(manifest) if c.priority == "P0"]

    for cid in case_ids:
        result = certify_case(cid, profile)
        add_case_result(report, cid, result["layers"], executor="cpp")
        print(f"certify: {cid} ok={result['ok']}")
        for layer in result["layers"]:
            print(f"  {layer['layer']}: {layer['status']} — {layer.get('reason', '')}")

    # Phase 0: never ok=true unless all layers pass with real samples
    report["ok"] = False
    report["note"] = "Phase 0 MVP: certify always ok=false until real golden diff passes"
    out = write_report(report, root)
    print(f"report: {out}")
    return 1  # non-zero until real parity
