#!/usr/bin/env python3
"""FR-B38 probes — plate entry image_url + face entry honest 400 when model missing.

Python-first:
- plate_library_service._upload_plate_image L103-109 / add_entry L271-273
- face_library_service.add_entry L323-326 → face.py L282-283 ValueError → HTTP 400

Artifacts: logs/fr-b38-multipart-latest.{json,md}
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from field_contract import http_post_json, server_reachable
from fr_b25_minio_upload_e2e import _MIN_JPEG
from fr_b37_multipart import (
    DISCLAIMER,
    create_library,
    delete_path,
    http_post_multipart,
    tiny_jpeg_path,
    utc_ts,
    write_artifacts as write_b37_artifacts,
)
from post_keys_matrix_b34_specs import FACE_ENTRY_KEYS, PLATE_ENTRY_KEYS
from vj_common import repo_root

_PY_PLATE_SVC = "VIDEO/_retired_python_video/app/services/plate_library_service.py"
_PY_FACE_SVC = "VIDEO/_retired_python_video/app/services/face_library_service.py"
_PY_FACE_BP = "VIDEO/_retired_python_video/app/blueprints/face.py"

FACE_MODEL_MSG = "人脸特征模型 face_rec.onnx 未安装，请在人脸库页面下载安装后再录入"


def probe_plate_image_url(base_url: str, ts: str, image: bytes, timeout: float) -> Dict[str, Any]:
    lib_id = create_library(base_url, "/video/plate/libraries", f"frb38_plate_{ts}", timeout)
    row: Dict[str, Any] = {
        "id": "plate_entry_image_url",
        "path": "/video/plate/libraries/{id}/entries",
        "python_source": f"{_PY_PLATE_SVC} _upload_plate_image L103-109 → add_entry L271-273",
        "checks": [],
    }
    if lib_id is None:
        row["ok"] = False
        row["checks"].append({"check": "setup", "status": "fail", "detail": "plate library create failed"})
        return row
    path = f"/video/plate/libraries/{lib_id}/entries"
    row["probe_path"] = path
    plate_no = f"FRB38{ts[-6:].upper()}"
    status, body, _ = http_post_multipart(
        base_url,
        path,
        {"plate_no": plate_no},
        [("file", "tiny.jpg", image, "image/jpeg")],
        timeout=timeout,
    )
    row["http_status"] = status
    row["business_code"] = body.get("code") if isinstance(body, dict) else None
    row["msg"] = body.get("msg") if isinstance(body, dict) else None
    ok = status < 500 and isinstance(body, dict) and body.get("code") == 0
    data = body.get("data") if isinstance(body, dict) else None
    if ok and isinstance(data, dict):
        image_url = data.get("image_url")
        row["image_url"] = image_url
        if image_url and str(image_url).strip():
            row["checks"].append({"check": "image_url_set", "status": "pass", "detail": str(image_url)[:120]})
        else:
            row["checks"].append({"check": "image_url_set", "status": "fail", "detail": "image_url empty/null"})
            ok = False
        missing = sorted(PLATE_ENTRY_KEYS - set(data.keys()))
        if missing:
            row["checks"].append({"check": "data_keys", "status": "fail", "detail": f"missing keys: {missing}"})
            ok = False
        else:
            row["checks"].append({"check": "data_keys", "status": "pass", "detail": f"keys ok ({len(PLATE_ENTRY_KEYS)})"})
        entry_id = data.get("id")
        if entry_id:
            delete_path(base_url, f"/video/plate/entries/{entry_id}", timeout)
    else:
        row["checks"].append(
            {
                "check": "success",
                "status": "fail",
                "detail": f"HTTP {status} code={body.get('code') if isinstance(body, dict) else None}",
            }
        )
    delete_path(base_url, f"/video/plate/libraries/{lib_id}", timeout)
    row["ok"] = ok and all(c["status"] == "pass" for c in row["checks"])
    return row


def probe_face_entry_no_model(base_url: str, ts: str, image: bytes, timeout: float) -> Dict[str, Any]:
    lib_id = create_library(base_url, "/video/face/libraries", f"frb38_face_{ts}", timeout)
    row: Dict[str, Any] = {
        "id": "face_entry_no_model_honest_400",
        "path": "/video/face/libraries/{id}/entries",
        "python_source": (
            f"{_PY_FACE_SVC} add_entry L323-326 FileNotFoundError → "
            f"{_PY_FACE_BP} add_face_entry L282-283 ValueError → HTTP 400"
        ),
        "expected": {"http_status": 400, "business_code": 400, "msg_contains": "face_rec.onnx"},
        "checks": [],
    }
    if lib_id is None:
        row["ok"] = False
        row["checks"].append({"check": "setup", "status": "fail", "detail": "face library create failed"})
        return row
    path = f"/video/face/libraries/{lib_id}/entries"
    row["probe_path"] = path
    status, body, _ = http_post_multipart(
        base_url,
        path,
        {"person_name": f"frb38_person_{ts}"},
        [("file", "tiny.jpg", image, "image/jpeg")],
        timeout=timeout,
    )
    row["http_status"] = status
    row["business_code"] = body.get("code") if isinstance(body, dict) else None
    row["msg"] = body.get("msg") if isinstance(body, dict) else None
    # Python: HTTP 400 + code=400 (face.py L282-283). Java envelope: HTTP 200 + code=400 (VideoApiResponseAdvice).
    biz_code = body.get("code") if isinstance(body, dict) else None
    msg = str(body.get("msg") or "") if isinstance(body, dict) else ""
    ok = isinstance(body, dict) and biz_code == 400 and status < 500
    if ok:
        if "face_rec.onnx" in msg or FACE_MODEL_MSG in msg:
            row["checks"].append({"check": "python_aligned_msg", "status": "pass", "detail": msg[:160]})
        else:
            row["checks"].append({"check": "python_aligned_msg", "status": "fail", "detail": msg[:160]})
            ok = False
        if status == 400:
            row["checks"].append({"check": "http_status", "status": "pass", "detail": "HTTP 400 (Python)"})
        elif status == 200:
            row["checks"].append(
                {
                    "check": "http_status",
                    "status": "pass",
                    "detail": "HTTP 200 envelope + code=400 (Java VideoApiResponseAdvice)",
                }
            )
        else:
            row["checks"].append({"check": "http_status", "status": "fail", "detail": f"unexpected HTTP {status}"})
            ok = False
        if biz_code == 500:
            row["checks"].append({"check": "not_500", "status": "fail", "detail": "still business code 500"})
            ok = False
        else:
            row["checks"].append({"check": "not_500", "status": "pass", "detail": f"business code {biz_code} not 500"})
    elif status == 500 or biz_code == 500:
        row["checks"].append({"check": "not_500", "status": "fail", "detail": "still HTTP/business 500 — Java not Python-aligned"})
    else:
        row["checks"].append(
            {
                "check": "honest_failure",
                "status": "fail",
                "detail": f"expected code=400 got HTTP {status} code={biz_code}",
            }
        )
    delete_path(base_url, f"/video/face/libraries/{lib_id}", timeout)
    row["ok"] = ok and all(c["status"] == "pass" for c in row["checks"])
    return row


def write_artifacts(payload: Dict[str, Any]) -> Tuple[Path, Path]:
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ts = payload.get("generated_at", utc_ts())
    json_path = logs / f"fr-b38-multipart-{ts}.json"
    md_path = logs / f"fr-b38-multipart-{ts}.md"
    latest_json = logs / "fr-b38-multipart-latest.json"
    latest_md = logs / "fr-b38-multipart-latest.md"
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    json_path.write_text(text + "\n", encoding="utf-8")
    latest_json.write_text(text + "\n", encoding="utf-8")

    lines = [
        "# FR-B38 Multipart Probes",
        "",
        f"**Generated:** {payload.get('generated_at')}",
        f"**Base URL:** {payload.get('base_url')}",
        f"**Server up:** {payload.get('server_up')}",
        f"**Pass:** {payload.get('summary', {}).get('pass')}/{payload.get('summary', {}).get('total')}",
        "",
        "## Python-first cites",
        "",
        "| id | python_source |",
        "|----|---------------|",
    ]
    for row in payload.get("probes", []):
        lines.append(f"| {row.get('id')} | {row.get('python_source', '')} |")
    lines.extend(["", "## Results", "", "| id | http | code | ok | notes |", "|----|------|------|-----|-------|"])
    for row in payload.get("probes", []):
        notes = row.get("image_url") or row.get("msg") or ""
        if len(str(notes)) > 60:
            notes = str(notes)[:57] + "..."
        lines.append(
            f"| {row.get('id')} | {row.get('http_status', '—')} | {row.get('business_code', '—')} | {row.get('ok')} | {notes} |"
        )
    lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"artifact: {json_path}")
    print(f"artifact: {md_path}")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="FR-B38 plate image_url + face honest 400 probes")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--timeout", type=float, default=12.0)
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    image_path = tiny_jpeg_path()
    image = image_path.read_bytes()
    server_up, health_detail = server_reachable(args.base_url, timeout=min(args.timeout, 3.0))

    probes: List[Dict[str, Any]] = []
    if server_up:
        probes.append(probe_plate_image_url(args.base_url, ts, image, args.timeout))
        probes.append(probe_face_entry_no_model(args.base_url, ts, image, args.timeout))
    else:
        for pid in ("plate_entry_image_url", "face_entry_no_model_honest_400"):
            probes.append(
                {
                    "id": pid,
                    "ok": False,
                    "checks": [{"check": "server", "status": "skip", "detail": health_detail}],
                }
            )

    passed = sum(1 for p in probes if p.get("ok"))
    payload = {
        "generated_at": utc_ts(),
        "base_url": args.base_url,
        "server_up": server_up,
        "health_detail": health_detail,
        "fixture_image": str(image_path.relative_to(repo_root())),
        "probes": probes,
        "summary": {"pass": passed, "total": len(probes)},
        "disclaimer": DISCLAIMER,
    }
    write_artifacts(payload)

    for row in probes:
        flag = "OK" if row.get("ok") else "FAIL"
        print(f"  {row.get('id')}: {flag}")
    print(f"\nfr-b38: {passed}/{len(probes)} pass")
    return 0 if passed == len(probes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
