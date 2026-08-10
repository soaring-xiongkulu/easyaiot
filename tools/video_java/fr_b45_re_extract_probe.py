#!/usr/bin/env python3
"""FR-B45 — pose re_extract MinIO load evidence (Python-first).

Python-first:
- scenario_pose.py re_extract_entry L155-159
- scenario_pose_library_service.re_extract_entry L314-336 (MinIO get_object)

Artifacts: logs/fr-b45-re-extract-latest.{json,md}
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from field_contract import server_reachable
from fr_b37_multipart import create_library, delete_path, http_post_multipart, utc_ts
from vj_common import http_json, repo_root

_PY_POSE_BP = "VIDEO/_retired_python_video/app/blueprints/scenario_pose.py"
_PY_POSE_SVC = "VIDEO/_retired_python_video/app/services/scenario_pose_library_service.py"

DISCLAIMER = (
    "FR-B45 re_extract requires MinIO enabled (fr-b45-soak) + YOLO worker. "
    "Local-only evidence — not COMPLETE."
)


def pose_fixture_path() -> Path:
    path = repo_root() / "testdata" / "fr-b41" / "face_sample.jpg"
    if not path.exists():
        raise FileNotFoundError(f"fixture missing: {path}")
    return path


def probe_re_extract(base_url: str, ts: str, image: bytes, timeout: float) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "id": "pose_re_extract_minio",
        "path": "POST /video/scenario-pose/entries/{id}/re-extract",
        "python_source": (
            f"{_PY_POSE_BP} re_extract_entry L155-159 → "
            f"{_PY_POSE_SVC} re_extract_entry L314-336"
        ),
        "checks": [],
    }
    lib_id = create_library(base_url, "/video/scenario-pose/libraries", f"frb45_pose_{ts}", timeout)
    if lib_id is None:
        row["ok"] = False
        row["checks"].append({"check": "library", "status": "fail", "detail": "create library failed"})
        return row

    status, body, _ = http_post_multipart(
        base_url,
        f"/video/scenario-pose/libraries/{lib_id}/entries",
        {"name": f"frb45_pose_{ts}", "conf": "0.25"},
        [("file", "face_sample.jpg", image, "image/jpeg")],
        timeout=timeout,
    )
    entry_id = None
    if isinstance(body, dict) and body.get("code") == 0:
        entry_id = (body.get("data") or {}).get("id")
    if entry_id is None:
        msg = body.get("msg") if isinstance(body, dict) else str(body)
        delete_path(base_url, f"/video/scenario-pose/libraries/{lib_id}", timeout)
        row["ok"] = False
        if isinstance(body, dict) and body.get("code") == 400 and "姿态" in str(msg):
            row["checks"].append(
                {
                    "check": "add_entry",
                    "status": "honest_ex",
                    "detail": f"YOLO worker unavailable: {msg}",
                }
            )
            row["yolo_exemption"] = True
        else:
            row["checks"].append({"check": "add_entry", "status": "fail", "detail": f"HTTP {status} {msg}"})
        return row
    row["entry_id"] = entry_id
    row["checks"].append({"check": "add_entry", "status": "pass"})

    re_status, re_body, _ = http_json(
        "POST",
        f"{base_url.rstrip('/')}/video/scenario-pose/entries/{entry_id}/re-extract",
        {"conf": 0.25},
        timeout=timeout,
    )
    row["re_extract_http"] = re_status
    row["re_extract_code"] = re_body.get("code") if isinstance(re_body, dict) else None
    row["re_extract_data"] = re_body.get("data") if isinstance(re_body, dict) else None

    ok = re_status < 500 and isinstance(re_body, dict) and re_body.get("code") == 0
    if not ok:
        row["checks"].append(
            {
                "check": "re_extract",
                "status": "fail",
                "detail": f"HTTP {re_status} code={re_body.get('code') if isinstance(re_body, dict) else None} "
                f"msg={re_body.get('msg') if isinstance(re_body, dict) else re_body}",
            }
        )
        row["ok"] = False
    else:
        data = re_body.get("data") or {}
        kps = data.get("keypoints")
        feat = data.get("feature_vector")
        row["keypoints_present"] = kps is not None and str(kps) not in ("", "null", "[]")
        row["feature_vector_present"] = feat is not None and str(feat) not in ("", "null", "[]")
        if row["keypoints_present"] and row["feature_vector_present"]:
            row["checks"].append({"check": "re_extract", "status": "pass", "detail": "keypoints+feature_vector"})
            row["ok"] = True
        else:
            row["checks"].append(
                {
                    "check": "re_extract",
                    "status": "fail",
                    "detail": f"keypoints={row['keypoints_present']} feature_vector={row['feature_vector_present']}",
                }
            )
            row["ok"] = False

    delete_path(base_url, f"/video/scenario-pose/entries/{entry_id}", timeout)
    delete_path(base_url, f"/video/scenario-pose/libraries/{lib_id}", timeout)
    return row


def write_artifacts(payload: Dict[str, Any]) -> Tuple[Path, Path]:
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ts = payload.get("generated_at", utc_ts())
    json_path = logs / f"fr-b45-re-extract-{ts}.json"
    md_path = logs / f"fr-b45-re-extract-{ts}.md"
    latest_json = logs / "fr-b45-re-extract-latest.json"
    latest_md = logs / "fr-b45-re-extract-latest.md"
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    json_path.write_text(text, encoding="utf-8")
    latest_json.write_text(text, encoding="utf-8")

    lines = [
        "# FR-B45 pose re_extract probes",
        "",
        f"- generated_at: {payload.get('generated_at')}",
        f"- base_url: {payload.get('base_url')}",
        "",
        "| id | http | code | ok |",
        "|----|------|------|-----|",
    ]
    for row in payload.get("probes", []):
        lines.append(
            f"| {row.get('id')} | {row.get('re_extract_http', '—')} | "
            f"{row.get('re_extract_code', '—')} | {row.get('ok')} |"
        )
    lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"artifact: {json_path}")
    print(f"artifact: {md_path}")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="FR-B45 pose re_extract MinIO probes")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    image = pose_fixture_path().read_bytes()
    server_up, health_detail = server_reachable(args.base_url, timeout=min(args.timeout, 5.0))

    probes: List[Dict[str, Any]] = []
    if not server_up:
        probes.append({"id": "server", "ok": False, "checks": [{"check": "server", "status": "skip", "detail": health_detail}]})
    else:
        probes.append(probe_re_extract(args.base_url, ts, image, args.timeout))

    passed = sum(1 for p in probes if p.get("ok"))
    honest_ex = sum(1 for p in probes if p.get("yolo_exemption"))
    payload = {
        "generated_at": utc_ts(),
        "base_url": args.base_url,
        "server_up": server_up,
        "health_detail": health_detail,
        "profile_hint": "local,fr-b45-soak (minio.enabled=true)",
        "probes": probes,
        "summary": {"pass": passed, "total": len(probes), "honest_ex": honest_ex},
        "disclaimer": DISCLAIMER,
    }
    write_artifacts(payload)
    print(f"\nfr-b45-re-extract: {passed}/{len(probes)} pass (honest_ex={honest_ex})")
    return 0 if passed == len(probes) else (0 if honest_ex == len(probes) else 1)


if __name__ == "__main__":
    raise SystemExit(main())
