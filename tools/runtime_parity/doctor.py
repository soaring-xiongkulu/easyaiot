"""doctor command — Phase 0 G-0.1 checks."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List, Tuple

from .manifest import load_manifest, load_thresholds, parse_cases
from .paths import candidate_root, manifest_path, testdata_root, thresholds_path


def _check_file(path: Path, label: str) -> Tuple[bool, str]:
    if path.is_file():
        return True, f"OK  {label}: {path}"
    return False, f"FAIL {label} missing: {path}"


def _check_dir(path: Path, label: str) -> Tuple[bool, str]:
    if path.is_dir():
        return True, f"OK  {label}: {path}"
    return False, f"FAIL {label} missing: {path}"


def run_doctor() -> int:
    root = candidate_root()
    td = testdata_root(root)
    lines: List[str] = []
    ok = True

    for passed, msg in (
        _check_file(manifest_path(root), "manifest.json"),
        _check_file(thresholds_path(root), "thresholds.json"),
        _check_file(td / "media" / "README.md", "media/README.md"),
        _check_dir(td / "fixtures" / "tasks", "fixtures/tasks/"),
        _check_dir(td / "golden", "golden/"),
    ):
        lines.append(msg)
        ok = ok and passed

    testbed = root / "docs" / "runtime-parity" / "testbed"
    for name in ("README.md", "mock_alert_hook.py", "docker-compose.media.yml"):
        passed, msg = _check_file(testbed / name, f"testbed/{name}")
        lines.append(msg)
        ok = ok and passed

    # manifest parse + P0 case ids
    required_p0 = {
        "rt_p0_detect_single_onnx",
        "rt_p0_heartbeat_lifecycle",
        "rt_p0_alert_hook_roi",
    }
    try:
        manifest = load_manifest(root)
        thresholds = load_thresholds(root)
        cases = parse_cases(manifest)
        case_ids = {c.id for c in cases}
        missing = required_p0 - case_ids
        if missing:
            ok = False
            lines.append(f"FAIL manifest missing P0 cases: {sorted(missing)}")
        else:
            lines.append(f"OK  manifest has {len(required_p0)} required P0 cases")
        if "cases" not in manifest or not manifest["cases"]:
            ok = False
            lines.append("FAIL manifest.cases empty")
        if "_note" not in thresholds and "detect" not in thresholds:
            lines.append("WARN thresholds.json has no _note/detect section")
        else:
            lines.append("OK  thresholds.json parseable")
    except (json.JSONDecodeError, OSError, KeyError) as exc:
        ok = False
        lines.append(f"FAIL manifest/thresholds parse: {exc}")

    lines.append(f"INFO candidate_root={root}")
    lines.append(f"INFO oracle_root env={os.environ.get('ACME_ORACLE_ROOT', '(unset)')}")

    print("=== runtime_parity_gate doctor ===")
    for line in lines:
        print(line)
        if line.startswith("FAIL"):
            ok = False

    print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1
