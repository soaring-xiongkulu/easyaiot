"""doctor command — Phase 0 G-0.1 checks."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List, Set, Tuple

from .manifest import load_manifest, load_thresholds, parse_cases
from .paths import candidate_root, manifest_path, testdata_root, thresholds_path

P0_CASES = {
    "rt_p0_detect_single_onnx",
    "rt_p0_heartbeat_lifecycle",
    "rt_p0_alert_hook_roi",
}


def _check_file(path: Path, label: str) -> Tuple[bool, str]:
    if path.is_file():
        return True, f"OK  {label}: {path}"
    return False, f"FAIL {label} missing: {path}"


def _check_dir(path: Path, label: str) -> Tuple[bool, str]:
    if path.is_dir():
        return True, f"OK  {label}: {path}"
    return False, f"FAIL {label} missing: {path}"


def _json_has_placeholder(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    if isinstance(data, dict) and data.get("status") == "placeholder":
        return True
    return False


def _find_placeholder_cases(td: Path) -> Set[str]:
    """Return case ids under golden/python with any placeholder JSON."""
    placeholder_cases: Set[str] = set()
    python_golden = td / "golden" / "python"
    if not python_golden.is_dir():
        return placeholder_cases
    for case_dir in python_golden.iterdir():
        if not case_dir.is_dir():
            continue
        for json_file in case_dir.rglob("*.json"):
            if _json_has_placeholder(json_file):
                placeholder_cases.add(case_dir.name)
                break
    return placeholder_cases


def run_doctor(*, strict_golden: bool = False) -> int:
    root = candidate_root()
    td = testdata_root(root)
    lines: List[str] = []
    ok = True
    golden_warn = False

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

    # manifest parse + P0 case ids + fixture paths
    try:
        manifest = load_manifest(root)
        thresholds = load_thresholds(root)
        cases = parse_cases(manifest)
        case_ids = {c.id for c in cases}
        missing = P0_CASES - case_ids
        if missing:
            ok = False
            lines.append(f"FAIL manifest missing P0 cases: {sorted(missing)}")
        else:
            lines.append(f"OK  manifest has {len(P0_CASES)} required P0 cases")

        missing_fixtures: List[str] = []
        for case in cases:
            if not case.fixture:
                continue
            fixture_path = td / case.fixture
            if not fixture_path.is_file():
                missing_fixtures.append(case.fixture)
        if missing_fixtures:
            ok = False
            lines.append(f"FAIL manifest fixtures missing: {sorted(missing_fixtures)}")
        else:
            lines.append(f"OK  manifest fixtures present ({len(cases)} cases)")

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

    # G-0.3: placeholder golden detection
    placeholder_cases = _find_placeholder_cases(td)
    recorded_p0 = P0_CASES - placeholder_cases
    if placeholder_cases:
        case_list = ", ".join(sorted(placeholder_cases))
        if strict_golden:
            ok = False
            lines.append(
                f"FAIL golden/python placeholder status in P0 cases: {case_list} "
                f"(run record-oracle-smoke or record-python against oracle)"
            )
        else:
            golden_warn = True
            lines.append(
                f"WARN golden/python has placeholder status in cases: {case_list} "
                f"(G-0.3 not satisfied; use --strict-golden to fail)"
            )
    if recorded_p0:
        lines.append(
            f"OK  golden/python recorded (non-placeholder) P0 cases: "
            f"{', '.join(sorted(recorded_p0))}"
        )
    elif not placeholder_cases:
        lines.append("WARN golden/python: no P0 golden directories found yet")

    lines.append(f"INFO candidate_root={root}")
    lines.append(f"INFO oracle_root env={os.environ.get('ACME_ORACLE_ROOT', '(unset)')}")

    print("=== runtime_parity_gate doctor ===")
    for line in lines:
        print(line)
        if line.startswith("FAIL"):
            ok = False

    if golden_warn and ok:
        print("RESULT: PASS (with golden placeholder WARNINGs)")
    else:
        print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1
