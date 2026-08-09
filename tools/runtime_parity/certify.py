"""certify — layered diff python vs cpp golden (G-4.1)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .artifacts import layer_file_map
from .diff_layers import diff_layer
from .manifest import find_case, load_manifest, load_thresholds, parse_cases
from .paths import candidate_root, golden_dir, report_path
from .report import add_case_result, new_report, write_report

_INVALID_CPP_STATUS = frozenset({"placeholder", "fail", "not_sampled", "unknown"})


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

    if py_status == "placeholder":
        return {
            "layer": layer,
            "status": "fail",
            "reason": "python golden is placeholder",
            "python_artifact": str(py_path),
            "cpp_artifact": str(cpp_path),
        }
    if cpp_status in _INVALID_CPP_STATUS:
        return {
            "layer": layer,
            "status": "not_sampled" if cpp_status == "not_sampled" else "fail",
            "reason": cpp_data.get("reason", f"cpp status={cpp_status}"),
            "python_artifact": str(py_path),
            "cpp_artifact": str(cpp_path),
        }

    return diff_layer(
        layer,
        py_data,
        cpp_data,
        thresholds,
        py_path=str(py_path),
        cpp_path=str(cpp_path),
    )


def certify_case(case_id: str, profile: Optional[str] = None) -> Dict[str, Any]:
    root = candidate_root()
    manifest = load_manifest(root)
    thresholds_data = load_thresholds(root)
    case = find_case(manifest, case_id)

    # Platform / perf: re-sample before diff (fast mocks; keeps golden fresh)
    sample_mode = str(case.raw.get("sample_mode") or "")
    if sample_mode == "platform" or case_id.startswith("vid_") or case_id.startswith("perf_"):
        from .platform_sample import run_platform_case

        run_platform_case(case)

    py_base = golden_dir("python", case_id, root)
    cpp_base = golden_dir("cpp", case_id, root)

    layer_results: List[Dict[str, Any]] = []
    for layer, fname in layer_file_map(case).items():
        result = _diff_layer(layer, py_base / fname, cpp_base / fname, thresholds_data)
        layer_results.append(result)

    case_ok = all(l.get("status") == "pass" for l in layer_results)
    return {
        "case_id": case_id,
        "profile": profile,
        "ok": case_ok,
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
        prof = manifest.get("profiles", {}).get(profile, {})
        if prof.get("case_ids"):
            case_ids = list(prof["case_ids"])
        else:
            filt = prof.get("case_filter", "P0")
            case_ids = [c.id for c in parse_cases(manifest) if c.priority == filt]
    else:
        case_ids = [c.id for c in parse_cases(manifest) if c.priority == "P0"]

    all_ok = True
    for cid in case_ids:
        result = certify_case(cid, profile)
        add_case_result(report, cid, result["layers"], executor="cpp")
        all_ok = all_ok and result["ok"]
        print(f"certify: {cid} ok={result['ok']}")
        for layer in result["layers"]:
            print(f"  {layer['layer']}: {layer['status']} — {layer.get('reason', '')}")

    report["ok"] = all_ok
    report["note"] = (
        "G-4.2 P1 motion/tracking certify" if all_ok and profile == "win_cpp" else
        ("G-4.1 P0 certify" if all_ok else "red layers remain — see cases[].layers")
    )
    out = write_report(report, root)
    print(f"report: {out}")
    return 0 if all_ok else 1
