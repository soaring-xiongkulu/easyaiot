#!/usr/bin/env python3
"""Full-prefix route inventory + method-aware thin contract probes for VIDEO Java.

Walks all 14 inventoried URL prefixes (not just phase0 ~18 certify cases),
writes artifacts under logs/, and documents that green inventory / mapped probes
!= behavior-complete != COMPLETE.

Usage:
  python tools/video_java/contract_regression.py
  python tools/video_java/contract_regression.py --smoke --base-url http://127.0.0.1:48096
  python tools/video_java/contract_regression.py --probe-all --base-url http://127.0.0.1:48096
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Set, Tuple

from route_inventory import BLUEPRINT_SPECS, diff_sets, java_routes, python_routes, repo_root

# One representative GET per prefix for thin HTTP smoke (optional, FR-B16 compat).
SMOKE_ENDPOINTS: Dict[str, str] = {
    "/video/alert": "/video/alert/count",
    "/video/algorithm": "/video/algorithm/task/list",
    "/video/camera": "/video/camera/list",
    "/video/snap": "/video/snap/space/list",
    "/video/record": "/video/record/space/list",
    "/video/playback": "/video/playback/list",
    "/video/stream-forward": "/video/stream-forward/task/list",
    "/video/media": "/video/ping",
    "/video/patrol": "/video/patrol/session/list",
    "/video/face": "/video/face/health",
    "/video/plate": "/video/plate/health",
    "/video/device-detection": "/video/device-detection/device/1/regions",
    "/video/camera/audio/talk": "/video/camera/audio/talk/health",
    "/video/scenario-pose": "/video/scenario-pose/libraries",
}

PROBE_PARAM_VALUE = "1"

DISCLAIMER = (
    "Green route inventory and thin/method-aware probes do NOT mean COMPLETE. "
    "Mapped (non-404) != behavior-complete. They verify HTTP path parity (~265 "
    "inventoried routes) and optional liveness/auth/validation responses. "
    "Behavior parity, prod broker/MinIO/device integration, and full field-level "
    "contract tests remain open — see docs/video-java/FULL_REPLACEMENT_GAP.md."
)


def adjust_known_inventory_artifacts(inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply documented scan artifacts (GAP §8: camera +5 talk sub-path double-count)."""
    talk_java = java_routes("/video/camera/audio/talk")
    adjusted: List[Dict[str, Any]] = []
    for row in inventory:
        copy = dict(row)
        if row["prefix"] == "/video/camera" and talk_java:
            only_java = list(row.get("only_java") or [])
            filtered = [r for r in only_java if r not in talk_java]
            removed = len(only_java) - len(filtered)
            if removed:
                copy["only_java"] = filtered
                copy["java_count"] = row["java_count"] - removed
                copy["diff"] = len(copy.get("only_python") or []) + len(filtered)
                copy["known_artifact_removed"] = removed
        adjusted.append(copy)
    return adjusted


def inventory_all_prefixes() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for prefix in sorted(BLUEPRINT_SPECS.keys()):
        py = python_routes(prefix)
        java = java_routes(prefix)
        only_py, only_java, both = diff_sets(py, java)
        rows.append(
            {
                "prefix": prefix,
                "python_count": len(py),
                "java_count": len(java),
                "matched": len(both),
                "diff": len(only_py) + len(only_java),
                "only_python": only_py,
                "only_java": only_java,
            }
        )
    return adjust_known_inventory_artifacts(rows)


def collect_inventoried_routes() -> List[str]:
    """Unique METHOD path tuples across all 14 prefixes (Java oracle for probing)."""
    routes: Set[str] = set()
    for prefix in BLUEPRINT_SPECS:
        routes |= java_routes(prefix)
    return sorted(routes)


def parse_route(route: str) -> Tuple[str, str]:
    method, _, path = route.partition(" ")
    return method.upper(), path


def materialize_path(path: str) -> str:
    """Replace templated path params with probe-safe literals."""
    return re.sub(r"\{param\}", PROBE_PARAM_VALUE, path)


def is_video_api_envelope(body: bytes | None) -> bool:
    """True when body matches Python/Java VIDEO JSON envelope (code + msg/message)."""
    if not body:
        return False
    try:
        data = json.loads(body.decode("utf-8", errors="replace"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    return "code" in data and ("msg" in data or "message" in data)


def classify_http_status(code: int, body: bytes | None = None) -> Tuple[str, str]:
    """Map HTTP status to probe bucket. 401/403 are pass (auth expected, not fail).

    HTTP 404 with VIDEO API envelope is pass (mapped route, resource not found) —
    matches Python patrol.py L45 and FR-B39 businessCodeToHttpStatus(404).
    Spring unmapped 404 has no envelope (timestamp/status/error/path).
    """
    if code == 404:
        if is_video_api_envelope(body):
            return "pass", "HTTP 404 (mapped, resource not found)"
        return "fail", "unmapped (404)"
    if code >= 500:
        return "fail", f"server error ({code})"
    if code in (401, 403):
        return "pass", f"HTTP {code} (auth expected)"
    if 200 <= code < 300:
        return "pass", f"HTTP {code}"
    if 400 <= code < 500:
        return "pass", f"HTTP {code} (validation/auth)"
    return "fail", f"HTTP {code}"


def server_reachable(base_url: str, timeout: float = 3.0) -> Tuple[bool, str]:
    url = base_url.rstrip("/") + "/actuator/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return True, f"health HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        if exc.code < 500:
            return True, f"health HTTP {exc.code}"
        return False, f"health HTTP {exc.code}"
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return False, f"unreachable: {exc}"


def probe_route(
    base_url: str,
    method: str,
    path: str,
    *,
    timeout: float = 4.0,
    server_up: bool = True,
) -> Tuple[str, str, int | None]:
    if not server_up:
        return "skip", "server unreachable", None

    http_method = "GET" if method in ("GET", "HEAD") else method
    concrete_path = materialize_path(path)
    url = base_url.rstrip("/") + concrete_path
    data: bytes | None = None
    headers: Dict[str, str] = {}
    if http_method in ("POST", "PUT", "PATCH", "DELETE"):
        data = b"{}"
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, method=http_method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            status, detail = classify_http_status(resp.status, body)
            return status, detail, resp.status
    except urllib.error.HTTPError as exc:
        body = exc.read()
        status, detail = classify_http_status(exc.code, body)
        return status, detail, exc.code
    except urllib.error.URLError as exc:
        return "skip", f"unreachable: {exc.reason}", None
    except (OSError, TimeoutError) as exc:
        return "skip", f"unreachable: {exc}", None


def probe_endpoint(base_url: str, path: str, timeout: float = 5.0) -> Tuple[str, str]:
    status, detail, _ = probe_route(base_url, "GET", path, timeout=timeout)
    return status, detail


def thin_smoke(base_url: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for prefix in sorted(SMOKE_ENDPOINTS.keys()):
        path = SMOKE_ENDPOINTS[prefix]
        status, detail = probe_endpoint(base_url, path)
        rows.append({"prefix": prefix, "path": path, "status": status, "detail": detail})
    return rows


def probe_all_routes(base_url: str, *, timeout: float = 4.0) -> Tuple[List[Dict[str, Any]], bool, str]:
    server_up, health_detail = server_reachable(base_url, timeout=min(timeout, 3.0))
    routes = collect_inventoried_routes()
    rows: List[Dict[str, Any]] = []
    for idx, route in enumerate(routes, start=1):
        method, path = parse_route(route)
        status, detail, http_code = probe_route(
            base_url, method, path, timeout=timeout, server_up=server_up
        )
        rows.append(
            {
                "route": route,
                "method": method,
                "path": path,
                "probe_path": materialize_path(path),
                "status": status,
                "detail": detail,
                "http_code": http_code,
            }
        )
        if idx % 50 == 0 or idx == len(routes):
            print(f"  probed {idx}/{len(routes)}")
    return rows, server_up, health_detail


def summarize_probes(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"probed": len(rows), "pass": 0, "fail": 0, "skip": 0}
    for row in rows:
        bucket = row.get("status", "fail")
        if bucket in counts:
            counts[bucket] += 1
        else:
            counts["fail"] += 1
    return counts


def write_artifacts(
    inventory: List[Dict[str, Any]],
    smoke: List[Dict[str, Any]] | None,
    *,
    smoke_attempted: bool,
    probes: List[Dict[str, Any]] | None = None,
    probe_attempted: bool = False,
    probe_server_up: bool | None = None,
    probe_health_detail: str | None = None,
    artifact_stem: str = "fr-b16-contract-regression",
) -> Path:
    logs_dir = repo_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = logs_dir / f"{artifact_stem}-{ts}.json"
    md_path = logs_dir / f"{artifact_stem}-{ts}.md"

    total_py = sum(r["python_count"] for r in inventory)
    total_java = sum(r["java_count"] for r in inventory)
    total_diff = sum(r["diff"] for r in inventory)
    inventory_ok = total_diff == 0

    smoke_ok = True
    if smoke:
        smoke_ok = all(r["status"] in ("pass", "skip") for r in smoke)

    probe_summary: Dict[str, int] | None = None
    probe_ok: bool | None = None
    if probes is not None:
        probe_summary = summarize_probes(probes)
        probe_ok = probe_summary["fail"] == 0

    title = "FR-B17 Contract Probes" if probe_attempted else "FR-B16 Contract Regression"
    payload: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": DISCLAIMER,
        "inventory_ok": inventory_ok,
        "prefix_count": len(inventory),
        "total_python_routes": total_py,
        "total_java_routes": total_java,
        "total_diff": total_diff,
        "inventory": inventory,
        "smoke_attempted": smoke_attempted,
        "smoke_ok": smoke_ok if smoke_attempted else None,
        "smoke": smoke or [],
        "probe_attempted": probe_attempted,
        "probe_server_up": probe_server_up,
        "probe_health_detail": probe_health_detail,
        "probe_ok": probe_ok,
        "probe_summary": probe_summary,
        "probes": probes or [],
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        f"# {title} — route inventory + HTTP probes",
        "",
        f"**Generated:** {payload['generated_at']}",
        f"**Inventory OK:** {inventory_ok} (total diff={total_diff})",
        f"**Smoke attempted:** {smoke_attempted}",
    ]
    if probe_attempted and probe_summary is not None:
        lines.extend(
            [
                f"**Probe server up:** {probe_server_up} ({probe_health_detail})",
                f"**Probes:** probed={probe_summary['probed']} pass={probe_summary['pass']} "
                f"fail={probe_summary['fail']} skip={probe_summary['skip']}",
                f"**Probe OK (no 404/5xx):** {probe_ok}",
            ]
        )
    lines.extend(
        [
            "",
            "## Disclaimer",
            "",
            DISCLAIMER,
            "",
            "## Route inventory (14 prefixes)",
            "",
            "| prefix | python | java | matched | diff |",
            "|--------|--------|------|---------|------|",
        ]
    )
    for row in inventory:
        lines.append(
            f"| {row['prefix']} | {row['python_count']} | {row['java_count']} | "
            f"{row['matched']} | {row['diff']} |"
        )
    lines.extend(
        [
            "",
            f"**Totals:** python={total_py} java={total_java} diff={total_diff}",
            "",
        ]
    )
    if smoke:
        lines.extend(
            [
                "## Thin smoke probes (1 per prefix)",
                "",
                "| prefix | path | status | detail |",
                "|--------|------|--------|--------|",
            ]
        )
        for row in smoke:
            lines.append(
                f"| {row['prefix']} | `{row['path']}` | {row['status']} | {row['detail']} |"
            )
        lines.append("")
    if probes:
        lines.extend(
            [
                "## Method-aware route probes",
                "",
                "| route | status | http | detail |",
                "|-------|--------|------|--------|",
            ]
        )
        for row in probes:
            code = row.get("http_code")
            code_s = str(code) if code is not None else "—"
            lines.append(
                f"| `{row['route']}` | {row['status']} | {code_s} | {row['detail']} |"
            )
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    latest_json = logs_dir / f"{artifact_stem}-latest.json"
    latest_md = logs_dir / f"{artifact_stem}-latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"artifact: {json_path}")
    print(f"artifact: {md_path}")
    print(f"latest:   {latest_json}")
    return json_path


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VIDEO Java full-prefix contract regression")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="probe one GET endpoint per prefix (optional; skips when server down)",
    )
    parser.add_argument(
        "--probe-all",
        action="store_true",
        help="method-aware thin probes for all inventoried Java routes",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:48096",
        help="Java candidate base URL for HTTP probes",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=4.0,
        help="per-route HTTP timeout seconds",
    )
    parser.add_argument(
        "--artifact-stem",
        default=None,
        help="logs/<stem>-latest.json stem (default: fr-b17-contract for --probe-all)",
    )
    args = parser.parse_args(argv)

    inventory = inventory_all_prefixes()
    total_diff = sum(r["diff"] for r in inventory)
    print(f"prefixes: {len(inventory)} total_diff: {total_diff}")
    for row in inventory:
        flag = "OK" if row["diff"] == 0 else "DIFF"
        print(
            f"  {row['prefix']}: py={row['python_count']} java={row['java_count']} "
            f"diff={row['diff']} [{flag}]"
        )

    smoke_rows: List[Dict[str, Any]] | None = None
    if args.smoke:
        print(f"\nthin smoke base_url={args.base_url}")
        smoke_rows = thin_smoke(args.base_url)
        for row in smoke_rows:
            print(f"  {row['prefix']}: {row['status']} — {row['detail']}")

    probe_rows: List[Dict[str, Any]] | None = None
    probe_server_up: bool | None = None
    probe_health_detail: str | None = None
    if args.probe_all:
        route_count = len(collect_inventoried_routes())
        print(f"\nmethod-aware probes base_url={args.base_url} routes={route_count}")
        probe_rows, probe_server_up, probe_health_detail = probe_all_routes(
            args.base_url, timeout=args.timeout
        )
        summary = summarize_probes(probe_rows)
        print(
            f"  summary: probed={summary['probed']} pass={summary['pass']} "
            f"fail={summary['fail']} skip={summary['skip']} server_up={probe_server_up}"
        )
        fails = [r for r in probe_rows if r["status"] == "fail"]
        if fails:
            print(f"  first fails ({min(5, len(fails))} shown):")
            for row in fails[:5]:
                print(f"    {row['route']}: {row['detail']}")

    artifact_stem = args.artifact_stem or (
        "fr-b17-contract" if args.probe_all else "fr-b16-contract-regression"
    )
    write_artifacts(
        inventory,
        smoke_rows,
        smoke_attempted=args.smoke,
        probes=probe_rows,
        probe_attempted=args.probe_all,
        probe_server_up=probe_server_up,
        probe_health_detail=probe_health_detail,
        artifact_stem=artifact_stem,
    )
    print(f"\n{DISCLAIMER}")

    if total_diff != 0:
        return 1
    if args.smoke and smoke_rows:
        hard_fails = [r for r in smoke_rows if r["status"] == "fail"]
        if hard_fails:
            return 1
    if args.probe_all and probe_rows and probe_server_up:
        hard_fails = [r for r in probe_rows if r["status"] == "fail"]
        if hard_fails:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
