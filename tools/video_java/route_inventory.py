#!/usr/bin/env python3
"""Compare Python oracle routes vs Java @*Mapping for a URL prefix."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List, Set, Tuple

JAVA_MAPPING = re.compile(
    r"@(?P<ann>Get|Post|Put|Delete|Patch)Mapping\s*\(\s*(?:value\s*=\s*)?(?P<paths>\{[^}]+\}|['\"][^'\"]*['\"])",
    re.IGNORECASE,
)
CLASS_PREFIX = re.compile(r"@RequestMapping\s*\(\s*['\"](?P<prefix>[^'\"]+)['\"]")


def _mapping_subpaths(raw: str) -> List[str]:
    """Extract path literals from @XMapping('...') or @XMapping({'', '/'}) etc."""
    raw = raw.strip()
    if raw.startswith("{"):
        inner = raw[1:-1]
        return [p.strip().strip("'\"") for p in inner.split(",") if p.strip().strip("'\"") or p.strip() in ('""', "''")]
    return [raw.strip("'\"")]

BLUEPRINT_SPECS = {
    "/video/alert": {
        "file": "alert.py",
        "bp": "alert_bp",
    },
    "/video/algorithm": {
        "file": "algorithm_task.py",
        "bp": "algorithm_task_bp",
    },
    "/video/camera": {
        "file": "camera.py",
        "bp": "camera_bp",
    },
    "/video/snap": {
        "file": "snap.py",
        "bp": "snap_bp",
    },
    "/video/record": {
        "file": "record.py",
        "bp": "record_bp",
    },
    "/video/playback": {
        "file": "playback.py",
        "bp": "playback_bp",
    },
    "/video/stream-forward": {
        "file": "stream_forward.py",
        "bp": "stream_forward_bp",
    },
    "/video/media": {
        "file": "media_hook.py",
        "bp": "media_hook_bp",
    },
    "/video/patrol": {
        "file": "patrol.py",
        "bp": "patrol_bp",
    },
    "/video/face": {
        "file": "face.py",
        "bp": "face_bp",
    },
    "/video/plate": {
        "file": "plate.py",
        "bp": "plate_bp",
    },
    "/video/device-detection": {
        "file": "device_detection_region.py",
        "bp": "device_detection_region_bp",
    },
    "/video/camera/audio/talk": {
        "file": "audio_talk.py",
        "bp": "audio_talk_bp",
    },
    "/video/scenario-pose": {
        "file": "scenario_pose.py",
        "bp": "scenario_pose_bp",
    },
}

BLUEPRINT_ROUTE = re.compile(
    r"@(?P<bp>\w+_bp)\.route\(\s*['\"](?P<path>[^'\"]*)['\"]"
    r"(?:\s*,\s*methods\s*=\s*\[(?P<methods>[^\]]+)\])?",
    re.IGNORECASE,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def normalize_path_params(path: str) -> str:
    """Normalize Flask <int:id>, <path:name>, Spring {id}, {*name}, /** to {param}."""
    p = re.sub(r"<(?:int:|string:|path:)?\w+>", "{param}", path)
    p = re.sub(r"\{\*[^}]+\}", "{param}", p)
    p = re.sub(r"\{[^}]+\}", "{param}", p)
    p = re.sub(r"/\*\*$", "/{param}", p)
    return p


def normalize_route(method: str, path: str, prefix: str) -> str:
    method = method.upper()
    p = path.strip()
    if not p.startswith("/"):
        p = "/" + p
    full = prefix.rstrip("/") + p
    full = re.sub(r"/{2,}", "/", full)
    if full != "/" and full.endswith("/"):
        full = full.rstrip("/")
    full = normalize_path_params(full)
    return f"{method} {full}"


def python_routes(prefix: str) -> Set[str]:
    spec = BLUEPRINT_SPECS.get(prefix.rstrip("/"))
    if not spec:
        raise SystemExit(f"unsupported prefix for python oracle: {prefix}")
    blueprint = (
        repo_root()
        / "VIDEO"
        / "_retired_python_video"
        / "app"
        / "blueprints"
        / spec["file"]
    )
    text = blueprint.read_text(encoding="utf-8")
    bp_name = spec["bp"]
    routes: Set[str] = set()
    for match in BLUEPRINT_ROUTE.finditer(text):
        if match.group("bp") != bp_name:
            continue
        sub = match.group("path") or ""
        methods_raw = match.group("methods")
        if methods_raw:
            methods = [m.strip().strip("'\"").upper() for m in methods_raw.split(",")]
        else:
            methods = ["GET"]
        for method in methods:
            routes.add(normalize_route(method, sub, prefix))
    return routes


def java_routes(prefix: str) -> Set[str]:
    java_root = repo_root() / "DEVICE" / "iot-video" / "iot-video-biz" / "src" / "main" / "java"
    routes: Set[str] = set()
    for path in java_root.rglob("*Controller.java"):
        text = path.read_text(encoding="utf-8")
        class_prefix = ""
        class_match = CLASS_PREFIX.search(text)
        if class_match:
            class_prefix = class_match.group("prefix")
        if not class_prefix.startswith(prefix.rstrip("/")):
            continue
        for match in JAVA_MAPPING.finditer(text):
            method = match.group("ann").upper()
            for sub in _mapping_subpaths(match.group("paths")):
                routes.add(normalize_route(method, sub, class_prefix))
    return routes


def diff_sets(py: Set[str], java: Set[str]) -> Tuple[List[str], List[str], List[str]]:
    only_py = sorted(py - java)
    only_java = sorted(java - py)
    both = sorted(py & java)
    return only_py, only_java, both


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VIDEO route inventory (Python vs Java)")
    parser.add_argument("--prefix", default="/video/alert", help="URL prefix to compare")
    args = parser.parse_args(list(argv) if argv is not None else None)

    prefix = args.prefix.rstrip("/")
    py = python_routes(prefix)
    java = java_routes(prefix)
    only_py, only_java, both = diff_sets(py, java)

    print(f"prefix: {prefix}")
    print(f"python: {len(py)}")
    print(f"java:   {len(java)}")
    print(f"matched: {len(both)}")
    print(f"diff:   {len(only_py) + len(only_java)}")
    if only_py:
        print("\nonly python:")
        for row in only_py:
            print(f"  - {row}")
    if only_java:
        print("\nonly java:")
        for row in only_java:
            print(f"  - {row}")
    if not only_py and not only_java:
        print("\n(no diff)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
