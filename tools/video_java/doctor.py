#!/usr/bin/env python3
"""VIDEO Java Phase -1 doctor — structural checks for certify testbed."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Tuple

REQUIRED_CASE_IDS = {
    "vj_p0_health",
    "vj_p0_task_start_stop",
    "vj_p0_heartbeat",
    "vj_p0_alert_hook",
    "vj_p0_restart",
}

P0_PORTS_DOC = "P0 direct ports: oracle http://127.0.0.1:6000 | candidate http://127.0.0.1:48096"

DEFAULT_EXTERNAL_ORACLE = Path("F:/acme/VIDEO")


def resolve_oracle_video_root(root: Path) -> Path | None:
    """First valid oracle VIDEO root: env, archived in-repo, repo VIDEO/, or external."""
    candidates: List[Path] = []
    env = os.environ.get("VIDEO_JAVA_ORACLE_ROOT", "").strip()
    if env:
        candidates.append(Path(env))
    candidates.extend(
        (
            root / "VIDEO" / "_retired_python_video",
            root / "VIDEO",
            DEFAULT_EXTERNAL_ORACLE,
        )
    )

    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate.expanduser().resolve(strict=False)
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        if _is_oracle_video_root(resolved):
            return resolved
    return None


def _is_oracle_video_root(path: Path) -> bool:
    if not path.is_dir():
        return False
    if (path / "run.py").is_file() and (path / "app").is_dir():
        return True
    retired = path / "_retired_python_video"
    if retired.is_dir() and (retired / "run.py").is_file() and (retired / "app").is_dir():
        return True
    return (path / "app").is_dir()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def check_path(path: Path, label: str, *, directory: bool = False) -> Tuple[bool, str]:
    if directory:
        ok = path.is_dir()
    else:
        ok = path.is_file()
    if ok:
        return True, f"OK  {label}: {path}"
    kind = "dir" if directory else "file"
    return False, f"FAIL {label} missing ({kind}): {path}"


def tool_version(cmd: List[str]) -> str:
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"unavailable ({exc})"
    out = (proc.stdout or proc.stderr or "").strip().splitlines()
    if not out:
        return f"exit {proc.returncode}"
    return out[0]


def probe_health(url: str, timeout: float = 2.0) -> Tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read(512).decode("utf-8", errors="replace")
        return True, f"OK  health probe {url} -> HTTP {resp.status} {body[:80]!r}"
    except urllib.error.URLError as exc:
        return False, f"WARN health probe {url} down: {exc.reason}"
    except Exception as exc:  # noqa: BLE001 — doctor reports all probe failures
        return False, f"WARN health probe {url} failed: {exc}"


def run_doctor() -> int:
    root = repo_root()
    lines: List[str] = []
    ok = True

    lines.append(f"repo root: {root}")
    lines.append(P0_PORTS_DOC)

    oracle_root = resolve_oracle_video_root(root)
    if oracle_root is not None:
        lines.append(f"OK  oracle VIDEO tree: {oracle_root}")
    else:
        ok = False
        lines.append(
            "FAIL oracle VIDEO tree missing "
            "(checked VIDEO_JAVA_ORACLE_ROOT, VIDEO/_retired_python_video, VIDEO/, F:/acme/VIDEO)"
        )

    structural_checks = [
        check_path(root / "docs" / "video-java", "docs/video-java", directory=True),
        check_path(root / "DEVICE" / "iot-video", "DEVICE/iot-video", directory=True),
        check_path(root / "testdata" / "video-java" / "manifest.json", "manifest.json"),
        check_path(root / "testdata" / "video-java" / "thresholds.json", "thresholds.json"),
        check_path(root / "testdata" / "video-java" / "fixtures", "fixtures/", directory=True),
        check_path(root / "testdata" / "video-java" / "golden", "golden/", directory=True),
        check_path(root / "testdata" / "video-java" / "media" / "README.md", "media/README.md"),
        check_path(
            root / "RUNTIME" / "build-win" / "Release" / "RUNTIME.exe",
            "RUNTIME.exe (Release build required for P0 certify)",
        ),
    ]
    for passed, msg in structural_checks:
        lines.append(msg)
        ok = ok and passed

    java_bin = shutil.which("java")
    mvn_bin = shutil.which("mvn")
    if java_bin:
        lines.append(f"OK  java: {tool_version([java_bin, '-version'])}")
    else:
        ok = False
        lines.append("FAIL java not found on PATH")

    if mvn_bin:
        mvn_version = tool_version([mvn_bin, "-version"])
        if mvn_version.startswith("unavailable"):
            ok = False
            lines.append(f"FAIL mvn: {mvn_version}")
        else:
            lines.append(f"OK  mvn: {mvn_version}")
    else:
        ok = False
        lines.append("FAIL mvn not found on PATH")

    manifest_path = root / "testdata" / "video-java" / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        case_ids = {c.get("case_id") for c in manifest.get("cases", [])}
        missing = REQUIRED_CASE_IDS - case_ids
        if missing:
            ok = False
            lines.append(f"FAIL manifest missing case ids: {sorted(missing)}")
        else:
            lines.append(f"OK  manifest has {len(REQUIRED_CASE_IDS)} required P0 case ids")
        for case in manifest.get("cases", []):
            if case.get("oracle_base_url") != "http://127.0.0.1:6000":
                lines.append(
                    f"WARN case {case.get('case_id')}: unexpected oracle_base_url {case.get('oracle_base_url')!r}"
                )
            if case.get("candidate_base_url") != "http://127.0.0.1:48096":
                lines.append(
                    f"WARN case {case.get('case_id')}: unexpected candidate_base_url {case.get('candidate_base_url')!r}"
                )
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        ok = False
        lines.append(f"FAIL manifest parse: {exc}")

    health_base = os.environ.get("VIDEO_JAVA_BASE", "http://127.0.0.1:48096").rstrip("/")
    health_url = f"{health_base}/actuator/health"
    _, health_msg = probe_health(health_url)
    lines.append(health_msg)

    for line in lines:
        print(line)

    if ok:
        print("doctor: PASS (structural)")
        return 0
    print("doctor: FAIL")
    return 1


def main() -> None:
    raise SystemExit(run_doctor())


if __name__ == "__main__":
    main()
