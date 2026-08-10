#!/usr/bin/env python3
"""FR-B32 content-type probes for 6 non-JSON GET routes (Python-first).

Python blueprint handlers (read before probing):
  alert.py get_alert_image L133-206 — image/jpeg or stat.content_type
  alert.py get_alert_record L209-242 — video/mp4|x-flv|mp2t|octet-stream
  patrol.py session_events L88-118 — text/event-stream SSE
  playback.py get_playback_thumbnail L232-251 — application/json envelope
  record.py get_video L292-307 — send_file mimetype from get_record_video
  snap.py get_space_image L946-961 — Response mimetype from get_snap_image

Artifacts: logs/fr-b32-binary-get.*
Classification: content-type pass (not keys-matrix envelope).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from vj_common import repo_root

BASE_URL = "http://127.0.0.1:48096"
ARTIFACT_PREFIX = "fr-b32-binary-get"

# Python-first cites for report.
BINARY_GET_PROBES: List[Dict[str, Any]] = [
    {
        "id": "alert_image",
        "path_template": "/video/alert/image?path={path}",
        "python_cite": "alert.py get_alert_image L133-206",
        "expect_2xx_prefixes": ("image/", "application/octet-stream"),
        "expect_4xx_json": True,
        "fixture_key": "alert_image_path",
    },
    {
        "id": "alert_record",
        "path_template": "/video/alert/record?path={path}",
        "python_cite": "alert.py get_alert_record L209-242",
        "expect_2xx_prefixes": ("video/", "application/octet-stream"),
        "expect_4xx_json": True,
        "fixture_key": "alert_record_path",
    },
    {
        "id": "patrol_session_events",
        "path_template": "/video/patrol/session/{patrol_session_id}/events",
        "python_cite": "patrol.py session_events L88-118",
        "expect_2xx_prefixes": ("text/event-stream",),
        "expect_4xx_json": True,
        "sse": True,
    },
    {
        "id": "playback_thumbnail",
        "path_template": "/video/playback/thumbnail/{playback_id}",
        "python_cite": "playback.py get_playback_thumbnail L232-251",
        "expect_2xx_prefixes": ("application/json",),
        "expect_4xx_json": True,
        "json_envelope_route": True,
    },
    {
        "id": "record_video_file",
        "path_template": "/video/record/space/{record_space_id}/video/{object}",
        "python_cite": "record.py get_video L292-307",
        "expect_2xx_prefixes": ("video/", "application/octet-stream"),
        "expect_4xx_json": True,
        "fixture_key": "record_probe_object",
        "space_key": "record_space_id",
    },
    {
        "id": "snap_image_file",
        "path_template": "/video/snap/space/{snap_space_id}/image/{object}",
        "python_cite": "snap.py get_space_image L946-961",
        "expect_2xx_prefixes": ("image/", "application/octet-stream"),
        "expect_4xx_json": True,
        "fixture_key": "snap_probe_object",
        "space_key": "snap_space_id",
    },
]


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_fixture() -> Dict[str, Any]:
    path = repo_root() / "logs" / "fr-b32-seed-fixture.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def seed_fixture() -> Dict[str, Any]:
    script = repo_root() / "tools" / "video_java" / "seed_fr_b32_fixture.py"
    subprocess.run([sys.executable, str(script)], check=False)
    return load_fixture()


def materialize_path(spec: Dict[str, Any], fixture: Dict[str, Any]) -> str:
    tpl = spec["path_template"]
    if "{path}" in tpl:
        raw = fixture.get(spec.get("fixture_key", ""), "missing")
        # Windows path — encode but keep drive colon and slashes for Java FileSystemResource.
        encoded = urllib.parse.quote(str(raw), safe=":/\\")
        return tpl.format(path=encoded)
    if "{object}" in tpl:
        obj = fixture.get(spec.get("fixture_key", ""), "missing/object")
        space = fixture.get(spec.get("space_key", ""), 1)
        # Keep slash in object key — Java /** AntPathMatcher expects path segments.
        encoded = urllib.parse.quote(str(obj), safe="/")
        return tpl.format(object=encoded, **{spec["space_key"]: space})
    return tpl.format(**{k: fixture.get(k, 1) for k in ("patrol_session_id", "playback_id", "snap_space_id", "record_space_id")})


def probe_route(base_url: str, spec: Dict[str, Any], fixture: Dict[str, Any], timeout: float = 8.0) -> Dict[str, Any]:
    path = materialize_path(spec, fixture)
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url, method="GET", headers={"Accept": "*/*"})
    row: Dict[str, Any] = {
        "id": spec["id"],
        "path": path,
        "python_cite": spec["python_cite"],
        "classification": "content-type pass (not envelope)",
    }
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            ctype = (resp.getheader("Content-Type") or "").split(";")[0].strip().lower()
            if spec.get("sse"):
                resp.read(512)
            else:
                resp.read(4096)
    except urllib.error.HTTPError as exc:
        status = exc.code
        ctype = (exc.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        try:
            exc.read(1024)
        except Exception:
            pass

    row["http_status"] = status
    row["content_type"] = ctype

    if status >= 500:
        row["ok"] = False
        row["detail"] = f"HTTP {status} 5xx"
        return row

    if 200 <= status < 300:
        prefixes = tuple(p.lower() for p in spec.get("expect_2xx_prefixes", ()))
        if ctype.startswith("application/json") and not spec.get("json_envelope_route"):
            row["ok"] = False
            row["detail"] = f"2xx JSON envelope (expected binary/SSE) ctype={ctype}"
            return row
        match = any(ctype.startswith(p) for p in prefixes)
        row["ok"] = match
        row["detail"] = f"2xx ctype={ctype} expected_prefix={prefixes}"
        return row

    if 400 <= status < 500:
        if spec.get("expect_4xx_json"):
            ok = (
                ctype.startswith("application/json")
                or ctype.startswith("text/html")
                or spec.get("json_envelope_route")
            )
            row["ok"] = ok
            row["detail"] = f"4xx ctype={ctype} (json/html error acceptable)"
        else:
            row["ok"] = True
            row["detail"] = f"4xx ctype={ctype}"
        return row

    row["ok"] = False
    row["detail"] = f"unexpected status {status}"
    return row


def write_artifacts(rows: List[Dict[str, Any]], all_ok: bool) -> Tuple[Path, Path]:
    ts = utc_ts()
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    payload = {
        "fr": "FR-B32",
        "kind": "binary-get-content-type",
        "timestamp": ts,
        "base_url": BASE_URL,
        "classification": "content-type pass — not keys-matrix envelope",
        "probe_count": len(rows),
        "all_ok": all_ok,
        "probes": rows,
    }
    json_path = logs / f"{ARTIFACT_PREFIX}-{ts}.json"
    md_path = logs / f"{ARTIFACT_PREFIX}-{ts}.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# FR-B32 Binary/SSE GET Content-Type Probes",
        "",
        f"**Generated:** {payload['timestamp']}",
        f"**Classification:** content-type pass (not envelope)",
        f"**All OK:** {all_ok}",
        "",
        "| id | HTTP | Content-Type | OK | Python cite |",
        "|----|------|--------------|----|-------------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r.get('http_status')} | {r.get('content_type')} | "
            f"{'✅' if r.get('ok') else '⛔'} | {r.get('python_cite', '')} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for suffix in (".json", ".md"):
        latest = logs / f"{ARTIFACT_PREFIX}-latest{suffix}"
        src = json_path if suffix == ".json" else md_path
        latest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return json_path, md_path


def run_binary_get_probes(base_url: str = BASE_URL) -> Tuple[int, List[Dict[str, Any]]]:
    fixture = seed_fixture()
    rows = [probe_route(base_url, spec, fixture) for spec in BINARY_GET_PROBES]
    all_ok = all(r.get("ok") for r in rows)
    for r in rows:
        flag = "OK" if r.get("ok") else "FAIL"
        print(f"  [{flag}] {r['id']}: HTTP {r.get('http_status')} {r.get('content_type')} — {r.get('detail')}")
    json_path, md_path = write_artifacts(rows, all_ok)
    print(f"\nBinary-get artifacts: {json_path}\n                     {md_path}")
    return 0 if all_ok else 1, rows


def main() -> int:
    parser = argparse.ArgumentParser(description="FR-B32 binary/SSE GET content-type probes")
    parser.add_argument("--base-url", default=BASE_URL)
    args = parser.parse_args()
    code, _ = run_binary_get_probes(args.base_url)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
