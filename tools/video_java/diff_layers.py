#!/usr/bin/env python3
"""Layer diff for VIDEO Java certify (python golden vs java golden)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from vj_common import (
    LAYER_FILES,
    find_case,
    golden_dir,
    layer_satisfies,
    load_manifest,
    load_thresholds,
    normalize_value,
    resolve_exemption,
)


def _lifecycle_degenerate(snapshot: Any) -> bool:
    if not isinstance(snapshot, dict):
        return True
    if snapshot.get("heartbeat_ok") is False and snapshot.get("run_status") is None:
        return True
    if snapshot.get("process_alive") is False and snapshot.get("after_run_status") is None:
        return True
    return False


def _load(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _diff_dict(py: Any, java: Any, path: str = "") -> List[str]:
    reds: List[str] = []
    if type(py) is not type(java):
        reds.append(f"{path or '$'}: type {type(py).__name__} != {type(java).__name__}")
        return reds
    if isinstance(py, dict):
        keys = sorted(set(py) | set(java))
        for key in keys:
            sub = f"{path}.{key}" if path else key
            if key not in py:
                reds.append(f"{sub}: missing in python")
            elif key not in java:
                reds.append(f"{sub}: missing in java")
            else:
                reds.extend(_diff_dict(py[key], java[key], sub))
    elif isinstance(py, list):
        if len(py) != len(java):
            reds.append(f"{path or '$'}: list length {len(py)} != {len(java)}")
        else:
            for i, (a, b) in enumerate(zip(py, java)):
                reds.extend(_diff_dict(a, b, f"{path}[{i}]"))
    elif py != java:
        reds.append(f"{path or '$'}: {py!r} != {java!r}")
    return reds


def _exempt(layer: str, exemption_id: str, reason: str) -> Dict[str, Any]:
    return {
        "layer": layer,
        "status": "exempt",
        "exemption_id": exemption_id,
        "reason": f"{exemption_id}: {reason}",
    }


def _fail(layer: str, reason: str) -> Dict[str, Any]:
    return {"layer": layer, "status": "fail", "reason": reason}


def diff_layer(
    layer: str, py_data: Dict[str, Any], java_data: Dict[str, Any], *, case: Dict[str, Any]
) -> Dict[str, Any]:
    py_status = py_data.get("status", "unknown")
    java_status = java_data.get("status", "unknown")
    if py_status == "placeholder":
        return _fail(layer, "python golden is placeholder")
    if java_status in ("placeholder", "fail", "not_sampled", "unknown"):
        return {
            "layer": layer,
            "status": "fail" if java_status == "fail" else "not_sampled",
            "reason": java_data.get("reason", f"java status={java_status}"),
        }

    if layer == "api":
        py_norm = normalize_value(py_data.get("normalized") or py_data.get("body") or {})
        java_norm = normalize_value(java_data.get("normalized") or java_data.get("body") or {})
        reds = _diff_dict(py_norm, java_norm)
        for field in ("http_status",):
            if py_data.get(field) != java_data.get(field):
                reds.append(f"{field}: {py_data.get(field)!r} != {java_data.get(field)!r}")
    elif layer == "ini":
        py_keys = set((py_data.get("keys") or {}).keys())
        java_keys = set((java_data.get("keys") or {}).keys())
        missing = sorted(py_keys - java_keys)
        extra = sorted(java_keys - py_keys)
        reds = []
        if missing:
            reds.append(f"missing ini sections: {missing}")
        if extra:
            reds.append(f"extra ini sections: {extra}")
        for sec in sorted(py_keys & java_keys):
            py_sec = py_data["keys"][sec]
            java_sec = java_data["keys"][sec]
            if isinstance(py_sec, dict) and isinstance(java_sec, dict):
                for k in sorted(set(py_sec) | set(java_sec)):
                    if k not in py_sec:
                        reds.append(f"ini[{sec}].{k}: missing in python")
                    elif k not in java_sec:
                        reds.append(f"ini[{sec}].{k}: missing in java")
                    elif normalize_value(py_sec[k]) != normalize_value(java_sec[k]):
                        reds.append(
                            f"ini[{sec}].{k}: {normalize_value(py_sec[k])!r} != {normalize_value(java_sec[k])!r}"
                        )
    else:
        py_norm = normalize_value(py_data.get("snapshot") or py_data)
        java_norm = normalize_value(java_data.get("snapshot") or java_data)
        if _lifecycle_degenerate(py_norm):
            return _fail(
                layer,
                "oracle golden degenerate; no parity baseline (do not pass on java-only)",
            )
        reds = _diff_dict(py_norm, java_norm)

    return {
        "layer": layer,
        "status": "pass" if not reds else "fail",
        "reason": "; ".join(reds[:8]) if reds else "ok",
        "red_count": len(reds),
    }


def _diff_health_api(
    layer: str, py_data: Optional[Dict[str, Any]], java_data: Optional[Dict[str, Any]], *, case: Dict[str, Any]
) -> Dict[str, Any]:
    if java_data is None:
        return _fail(layer, "missing java api.json")
    java_body = java_data.get("body") or {}
    java_ok = java_data.get("http_status") == 200 and java_body.get("status") == "UP"
    if not java_ok:
        return _fail(layer, "java health not UP")

    py_ok = False
    if py_data is not None:
        py_body = py_data.get("body") or {}
        py_ok = py_data.get("http_status") == 200 and py_body.get("status") == "UP"

    if py_ok:
        return {"layer": layer, "status": "pass", "reason": "ok"}

    ex_id = resolve_exemption(case, layer, "EX-ORACLE-HEALTH-DB")
    if ex_id:
        return _exempt(
            layer,
            ex_id,
            "java UP; oracle health not UP (env DB probe)",
        )
    if py_data is None:
        return _fail(layer, "missing python golden")
    return _fail(
        layer,
        "oracle health not UP; case must reference EX-ORACLE-HEALTH-DB in manifest to exempt",
    )


def diff_case(case_id: str, layers: List[str]) -> Tuple[bool, List[Dict[str, Any]]]:
    load_thresholds()  # reserved for future numeric thresholds
    manifest = load_manifest()
    case = find_case(manifest, case_id)
    py_base = golden_dir("python", case_id)
    java_base = golden_dir("java", case_id)
    results: List[Dict[str, Any]] = []
    all_ok = True
    for layer in layers:
        fname = LAYER_FILES.get(layer)
        if not fname:
            results.append(_fail(layer, f"unknown layer {layer}"))
            all_ok = False
            continue
        py_data = _load(py_base / fname)
        java_data = _load(java_base / fname)
        if case_id == "vj_p0_health" and layer == "api":
            result = _diff_health_api(layer, py_data, java_data, case=case)
            results.append(result)
            all_ok = all_ok and layer_satisfies(result)
            continue
        if py_data is None:
            results.append(_fail(layer, f"missing python {fname}"))
            all_ok = False
            continue
        if java_data is None:
            results.append(_fail(layer, f"missing java {fname}"))
            all_ok = False
            continue
        result = diff_layer(layer, py_data, java_data, case=case)
        results.append(result)
        all_ok = all_ok and layer_satisfies(result)
    return all_ok, results


def main() -> int:
    parser = argparse.ArgumentParser(description="Diff VIDEO Java golden layers")
    parser.add_argument("case_id")
    parser.add_argument("--layers", nargs="*", default=["api", "lifecycle", "alarm", "ini"])
    args = parser.parse_args()
    ok, results = diff_case(args.case_id, args.layers)
    for r in results:
        print(f"{r['layer']}: {r['status']} — {r.get('reason', '')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
