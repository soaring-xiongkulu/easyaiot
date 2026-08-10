#!/usr/bin/env python3
"""FR-B42 — face entry update-with-image success (code=0 + FaceEntry.to_dict keys).

Python-first:
- face_library_service.update_entry L428-482 (delete old MinIO, re-extract, Milvus upsert)
- face_library_service.add_entry L303-380 (create setup)
- models.py FaceEntry.to_dict L1327-1341

Artifacts: logs/fr-b42-face-update-latest.{json,md}
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from field_contract import server_reachable
from fr_b37_multipart import (
    create_library,
    delete_path,
    http_post_multipart,
    utc_ts,
)
from fr_b39_multipart import http_put_multipart
from post_keys_matrix_b34_specs import FACE_ENTRY_KEYS
from vj_common import repo_root

_PY_FACE_SVC = "VIDEO/_retired_python_video/app/services/face_library_service.py"
_PY_FACE_REC = "VIDEO/_retired_python_video/app/services/face_recognition_service.py"
_PY_MODELS = "VIDEO/_retired_python_video/models.py"
_DOWNLOAD_SH = "VIDEO/scripts/download_face_rec_model.sh"

DISCLAIMER = (
    "FR-B42 requires real face_rec.onnx, Python worker health, Milvus, MinIO, and a detectable face fixture. "
    "Honest EX documented when deps missing — not COMPLETE."
)


def face_fixture_path() -> Path:
    path = repo_root() / "testdata" / "fr-b41" / "face_sample.jpg"
    if not path.exists():
        raise FileNotFoundError(f"fixture missing: {path}")
    return path


def probe_face_update_success(base_url: str, ts: str, image: bytes, timeout: float) -> Dict[str, Any]:
    lib_id = create_library(base_url, "/video/face/libraries", f"frb42_face_{ts}", timeout)
    row: Dict[str, Any] = {
        "id": "face_entry_update_multipart_success",
        "path": "PUT /video/face/entries/{id}",
        "python_source": (
            f"{_PY_FACE_SVC} update_entry L428-482 → "
            f"delete MinIO + extract_and_crop + add_face_to_library → "
            f"{_PY_MODELS} FaceEntry.to_dict L1327-1341"
        ),
        "model_script": _DOWNLOAD_SH,
        "multipart_fields": ["person_name", "file"],
        "checks": [],
    }
    if lib_id is None:
        row["ok"] = False
        row["checks"].append({"check": "setup", "status": "fail", "detail": "face library create failed"})
        return row

    create_path = f"/video/face/libraries/{lib_id}/entries"
    status, body, _ = http_post_multipart(
        base_url,
        create_path,
        {"person_name": f"frb42_person_{ts}"},
        [("file", "face_sample.jpg", image, "image/jpeg")],
        timeout=timeout,
    )
    if status >= 500 or not isinstance(body, dict) or body.get("code") != 0:
        row["ok"] = False
        row["checks"].append(
            {
                "check": "setup",
                "status": "fail",
                "detail": f"create entry failed HTTP {status} code={body.get('code') if isinstance(body, dict) else None}",
            }
        )
        delete_path(base_url, f"/video/face/libraries/{lib_id}", timeout)
        return row

    data = body.get("data") if isinstance(body, dict) else None
    entry_id = data.get("id") if isinstance(data, dict) else None
    original_image_url = data.get("image_url") if isinstance(data, dict) else None
    original_milvus_id = data.get("milvus_id") if isinstance(data, dict) else None
    if not entry_id:
        row["ok"] = False
        row["checks"].append({"check": "setup", "status": "fail", "detail": "create entry missing id"})
        delete_path(base_url, f"/video/face/libraries/{lib_id}", timeout)
        return row

    update_path = f"/video/face/entries/{entry_id}"
    row["probe_path"] = update_path
    row["setup_entry_id"] = entry_id
    row["original_image_url"] = original_image_url
    row["original_milvus_id"] = original_milvus_id
    updated_name = f"frb42_updated_{ts}"
    status, body, _ = http_put_multipart(
        base_url,
        update_path,
        {"person_name": updated_name},
        [("file", "face_sample.jpg", image, "image/jpeg")],
        timeout=timeout,
    )
    row["http_status"] = status
    row["business_code"] = body.get("code") if isinstance(body, dict) else None
    row["msg"] = body.get("msg") if isinstance(body, dict) else None
    ok = status < 500 and isinstance(body, dict) and body.get("code") == 0
    data = body.get("data") if isinstance(body, dict) else None
    if ok and isinstance(data, dict):
        missing = sorted(FACE_ENTRY_KEYS - set(data.keys()))
        if missing:
            row["checks"].append({"check": "data_keys", "status": "fail", "detail": f"missing keys: {missing}"})
            ok = False
        else:
            row["checks"].append({"check": "data_keys", "status": "pass", "detail": f"keys ok ({len(FACE_ENTRY_KEYS)})"})
        image_url = data.get("image_url")
        milvus_id = data.get("milvus_id")
        person_name = data.get("person_name")
        row["image_url"] = image_url
        row["milvus_id"] = milvus_id
        row["person_name"] = person_name
        if image_url and str(image_url).strip():
            row["checks"].append({"check": "image_url_set", "status": "pass", "detail": str(image_url)[:120]})
        else:
            row["checks"].append({"check": "image_url_set", "status": "fail", "detail": "image_url empty"})
            ok = False
        if milvus_id and str(milvus_id).strip():
            row["checks"].append({"check": "milvus_id_set", "status": "pass", "detail": str(milvus_id)})
        else:
            row["checks"].append({"check": "milvus_id_set", "status": "fail", "detail": "milvus_id empty"})
            ok = False
        if person_name == updated_name:
            row["checks"].append({"check": "person_name_updated", "status": "pass", "detail": person_name})
        else:
            row["checks"].append(
                {
                    "check": "person_name_updated",
                    "status": "fail",
                    "detail": f"expected {updated_name}, got {person_name}",
                }
            )
            ok = False
        if original_image_url and image_url and str(original_image_url) != str(image_url):
            row["checks"].append({"check": "image_url_changed", "status": "pass", "detail": "new MinIO object"})
        elif original_image_url and image_url:
            row["checks"].append(
                {
                    "check": "image_url_changed",
                    "status": "warn",
                    "detail": "image_url unchanged (same object?)",
                }
            )
        if original_milvus_id and milvus_id and str(original_milvus_id) != str(milvus_id):
            row["checks"].append({"check": "milvus_id_changed", "status": "pass", "detail": "re-upserted"})
        elif milvus_id:
            row["checks"].append(
                {
                    "check": "milvus_id_changed",
                    "status": "warn",
                    "detail": "milvus_id unchanged (reused id?)",
                }
            )
        delete_path(base_url, update_path, timeout)
    else:
        row["checks"].append(
            {
                "check": "success",
                "status": "fail",
                "detail": f"HTTP {status} code={body.get('code') if isinstance(body, dict) else None} msg={body.get('msg') if isinstance(body, dict) else body}",
            }
        )
    delete_path(base_url, f"/video/face/libraries/{lib_id}", timeout)
    row["ok"] = ok and all(c["status"] == "pass" for c in row["checks"])
    return row


def write_artifacts(payload: Dict[str, Any]) -> Tuple[Path, Path]:
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ts = payload.get("generated_at", utc_ts())
    json_path = logs / f"fr-b42-face-update-{ts}.json"
    md_path = logs / f"fr-b42-face-update-{ts}.md"
    latest_json = logs / "fr-b42-face-update-latest.json"
    latest_md = logs / "fr-b42-face-update-latest.md"
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    json_path.write_text(text + "\n", encoding="utf-8")
    latest_json.write_text(text + "\n", encoding="utf-8")

    lines = [
        "# FR-B42 Face Entry Update Success",
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
        notes = row.get("milvus_id") or row.get("image_url") or row.get("msg") or ""
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
    parser = argparse.ArgumentParser(description="FR-B42 face entry update-with-image success probe")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    image_path = face_fixture_path()
    image = image_path.read_bytes()
    server_up, health_detail = server_reachable(args.base_url, timeout=min(args.timeout, 3.0))

    probes: List[Dict[str, Any]] = []
    if server_up:
        probes.append(probe_face_update_success(args.base_url, ts, image, args.timeout))
    else:
        probes.append(
            {
                "id": "face_entry_update_multipart_success",
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
        "face_rec_onnx": str(repo_root() / "VIDEO" / "face_rec.onnx"),
        "probes": probes,
        "summary": {"pass": passed, "total": len(probes)},
        "disclaimer": DISCLAIMER,
    }
    write_artifacts(payload)

    for row in probes:
        flag = "OK" if row.get("ok") else "FAIL"
        print(f"  {row.get('id')}: {flag}")
    print(f"\nfr-b42: {passed}/{len(probes)} pass")
    return 0 if passed == len(probes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
