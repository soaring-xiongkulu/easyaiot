#!/usr/bin/env python3
"""Compare Python oracle routes vs Java @*Mapping for a URL prefix."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List, Set, Tuple

ROUTE_DECORATOR = re.compile(
    r"@(?:\w+\.)?(?:route|get|post|put|delete|patch)mapping\s*\(\s*['\"]([^'\"]*)['\"]"
    r"(?:\s*,\s*methods\s*=\s*\[([^\]]+)\])?",
    re.IGNORECASE,
)
JAVA_MAPPING = re.compile(
    r"@(?P<ann>Get|Post|Put|Delete|Patch)Mapping\s*\(\s*(?:value\s*=\s*)?['\"](?P<path>[^'\"]+)['\"]",
    re.IGNORECASE,
)
CLASS_PREFIX = re.compile(r"@RequestMapping\s*\(\s*['\"](?P<prefix>[^'\"]+)['\"]")
BLUEPRINT_ROUTE = re.compile(
    r"@alert_bp\.route\(\s*['\"](?P<path>[^'\"]*)['\"]"
    r"(?:\s*,\s*methods\s*=\s*\[(?P<methods>[^\]]+)\])?",
    re.IGNORECASE,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def normalize_route(method: str, path: str, prefix: str) -> str:
    method = method.upper()
    p = path.strip()
    if not p.startswith("/"):
        p = "/" + p
    full = prefix.rstrip("/") + p
    full = re.sub(r"/{2,}", "/", full)
    if full != "/" and full.endswith("/"):
        full = full.rstrip("/")
    return f"{method} {full}"


def python_routes(prefix: str) -> Set[str]:
    blueprint = repo_root() / "VIDEO" / "_retired_python_video" / "app" / "blueprints" / "alert.py"
    text = blueprint.read_text(encoding="utf-8")
    routes: Set[str] = set()
    for match in BLUEPRINT_ROUTE.finditer(text):
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
            sub = match.group("path")
            method = match.group("ann").upper()
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
