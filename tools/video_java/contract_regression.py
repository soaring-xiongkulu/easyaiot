#!/usr/bin/env python3
"""Full-prefix route inventory + thin contract smoke for VIDEO Java.

Walks all 14 inventoried URL prefixes (not just phase0 ~18 certify cases),
writes an artifact under logs/, and documents that green inventory != COMPLETE.

Usage:
  python tools/video_java/contract_regression.py
  python tools/video_java/contract_regression.py --smoke --base-url http://127.0.0.1:48096
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from route_inventory import BLUEPRINT_SPECS, diff_sets, java_routes, python_routes, repo_root

# One representative GET per prefix for thin HTTP smoke (optional).
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
    "/video/device-detection": "/video/device-detection/regions",
    "/video/camera/audio/talk": "/video/camera/audio/talk/health",
    "/video/scenario-pose": "/video/scenario-pose/libraries",
}

DISCLAIMER = (
    "Green route inventory and thin smoke probes do NOT mean COMPLETE. "
    "They only verify HTTP path parity (~259 routes) and optional liveness. "
    "Behavior parity, prod broker/MinIO/device integration, and full contract "
    "tests remain open — see docs/video-java/FULL_REPLACEMENT_GAP.md."
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


def probe_endpoint(base_url: str, path: str, timeout: float = 5.0) -> Tuple[str, str]:
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return "pass", f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return "pass", f"HTTP {exc.code} (auth expected)"
        return "fail", f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return "skip", f"unreachable: {exc.reason}"
    except OSError as exc:
        return "skip", f"unreachable: {exc}"


def thin_smoke(base_url: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for prefix in sorted(SMOKE_ENDPOINTS.keys()):
        path = SMOKE_ENDPOINTS[prefix]
        status, detail = probe_endpoint(base_url, path)
        rows.append({"prefix": prefix, "path": path, "status": status, "detail": detail})
    return rows


def write_artifacts(
    inventory: List[Dict[str, Any]],
    smoke: List[Dict[str, Any]] | None,
    *,
    smoke_attempted: bool,
) -> Path:
    logs_dir = repo_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = logs_dir / f"fr-b16-contract-regression-{ts}.json"
    md_path = logs_dir / f"fr-b16-contract-regression-{ts}.md"

    total_py = sum(r["python_count"] for r in inventory)
    total_java = sum(r["java_count"] for r in inventory)
    total_diff = sum(r["diff"] for r in inventory)
    inventory_ok = total_diff == 0

    smoke_ok = True
    if smoke:
        smoke_ok = all(r["status"] in ("pass", "skip") for r in smoke)

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
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# FR-B16 Contract Regression — route inventory + thin smoke",
        "",
        f"**Generated:** {payload['generated_at']}",
        f"**Inventory OK:** {inventory_ok} (total diff={total_diff})",
        f"**Smoke attempted:** {smoke_attempted}",
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
                "## Thin smoke probes",
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
    md_path.write_text("\n".join(lines), encoding="utf-8")

    latest_json = logs_dir / "fr-b16-contract-regression-latest.json"
    latest_md = logs_dir / "fr-b16-contract-regression-latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"artifact: {json_path}")
    print(f"artifact: {md_path}")
    print(f"latest:   {latest_json}")
    return json_path


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VIDEO Java full-prefix contract regression scaffold")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="probe one GET endpoint per prefix (optional; skips when server down)",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:48096",
        help="Java candidate base URL for thin smoke",
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

    write_artifacts(inventory, smoke_rows, smoke_attempted=args.smoke)
    print(f"\n{DISCLAIMER}")

    if total_diff != 0:
        return 1
    if args.smoke and smoke_rows:
        hard_fails = [r for r in smoke_rows if r["status"] == "fail"]
        if hard_fails:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
