#!/usr/bin/env python3
"""FR-B43 — face/plate /health truthful probes (Python key parity).

Python-first:
- face_vector_store.ping L164-179 + face.py health L83-90
- plate_model_download.get_plate_model_status L47-62 + plate.py health L55-59

Artifacts: logs/fr-b43-health-latest.{json,md}
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from field_contract import server_reachable
from vj_common import http_json, repo_root

_PY_FACE_PING = "VIDEO/_retired_python_video/app/services/face_vector_store.py ping L164-179"
_PY_FACE_HEALTH = "VIDEO/_retired_python_video/app/blueprints/face.py health L83-90"
_PY_PLATE_STATUS = "VIDEO/_retired_python_video/app/utils/plate_model_download.py get_plate_model_status L47-62"
_PY_PLATE_HEALTH = "VIDEO/_retired_python_video/app/blueprints/plate.py health L55-59"

FACE_HEALTH_KEYS: Set[str] = {
    "milvus_uri",
    "collection_name",
    "collection_exists",
    "recognition_model_loaded",
    "recognition_model_downloading",
}
PLATE_HEALTH_KEYS: Set[str] = {
    "exists",
    "detect_model",
    "rec_model",
    "detect_path",
    "rec_path",
    "downloading",
    "stage",
    "progress",
    "error",
}

DISCLAIMER = (
    "FR-B43 health probes require live video-server + ACME_ROOT + models on disk. "
    "Milvus down → collection_exists=false (honest). Models missing → exists=false. "
    "Local-only evidence — not COMPLETE."
)


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def missing_keys(data: Dict[str, Any], required: Set[str]) -> List[str]:
    return sorted(k for k in required if k not in data)


def probe_face_health(base_url: str, timeout: float) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "id": "face_health_truthful",
        "path": "GET /video/face/health",
        "python_source": f"{_PY_FACE_PING} + {_PY_FACE_HEALTH}",
        "required_keys": sorted(FACE_HEALTH_KEYS),
        "checks": [],
    }
    status, body, _ = http_json("GET", f"{base_url.rstrip('/')}/video/face/health", timeout=timeout)
    row["http_status"] = status
    row["business_code"] = body.get("code")
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    row["data"] = data
    missing = missing_keys(data, FACE_HEALTH_KEYS)
    if missing:
        row["checks"].append({"check": "keys", "status": "fail", "detail": f"missing: {missing}"})
    else:
        row["checks"].append({"check": "keys", "status": "pass"})
    if body.get("code") != 0:
        row["checks"].append({"check": "code", "status": "fail", "detail": body.get("msg")})
    else:
        row["checks"].append({"check": "code", "status": "pass"})
    coll = data.get("collection_exists")
    model = data.get("recognition_model_loaded")
    if coll is True and model is True:
        row["checks"].append({"check": "truthful_green", "status": "pass", "detail": "milvus+collection+model"})
    elif coll is False or model is False:
        row["checks"].append(
            {
                "check": "truthful_green",
                "status": "honest_false",
                "detail": f"collection_exists={coll} recognition_model_loaded={model}",
            }
        )
    row["ok"] = all(c.get("status") == "pass" for c in row["checks"])
    return row


def probe_plate_health(base_url: str, timeout: float) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "id": "plate_health_truthful",
        "path": "GET /video/plate/health",
        "python_source": f"{_PY_PLATE_STATUS} + {_PY_PLATE_HEALTH}",
        "required_keys": sorted(PLATE_HEALTH_KEYS),
        "checks": [],
    }
    status, body, _ = http_json("GET", f"{base_url.rstrip('/')}/video/plate/health", timeout=timeout)
    row["http_status"] = status
    row["business_code"] = body.get("code")
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    row["data"] = data
    missing = missing_keys(data, PLATE_HEALTH_KEYS)
    if missing:
        row["checks"].append({"check": "keys", "status": "fail", "detail": f"missing: {missing}"})
    else:
        row["checks"].append({"check": "keys", "status": "pass"})
    if body.get("code") != 0:
        row["checks"].append({"check": "code", "status": "fail", "detail": body.get("msg")})
    else:
        row["checks"].append({"check": "code", "status": "pass"})
    exists = data.get("exists")
    if exists is True:
        row["checks"].append({"check": "truthful_green", "status": "pass", "detail": "plate models ready"})
    elif exists is False:
        row["checks"].append({"check": "truthful_green", "status": "honest_false", "detail": "exists=false"})
    row["ok"] = all(c.get("status") == "pass" for c in row["checks"])
    return row


def write_artifacts(payload: Dict[str, Any]) -> tuple[Path, Path]:
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = logs / f"fr-b43-health-{ts}.json"
    md_path = logs / f"fr-b43-health-{ts}.md"
    latest_json = logs / "fr-b43-health-latest.json"
    latest_md = logs / "fr-b43-health-latest.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")

    lines = [
        "# FR-B43 health probes",
        "",
        f"- generated_at: {payload.get('generated_at')}",
        f"- base_url: {payload.get('base_url')}",
        f"- server_up: {payload.get('server_up')}",
        "",
        "## Python-first cites",
        "",
        f"- face ping: `{_PY_FACE_PING}`",
        f"- face health: `{_PY_FACE_HEALTH}`",
        f"- plate status: `{_PY_PLATE_STATUS}`",
        f"- plate health: `{_PY_PLATE_HEALTH}`",
        "",
        "## Results",
        "",
        "| id | http | code | ok | collection_exists / exists | model_loaded |",
        "|----|------|------|-----|------------------------------|--------------|",
    ]
    for row in payload.get("probes", []):
        data = row.get("data") or {}
        coll = data.get("collection_exists", "—")
        exists = data.get("exists", "—")
        model = data.get("recognition_model_loaded", "—")
        lines.append(
            f"| {row.get('id')} | {row.get('http_status', '—')} | {row.get('business_code', '—')} | "
            f"{row.get('ok')} | {coll}/{exists} | {model} |"
        )
    lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"artifact: {json_path}")
    print(f"artifact: {md_path}")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="FR-B43 face/plate health truthful probes")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    server_up, health_detail = server_reachable(args.base_url, timeout=min(args.timeout, 5.0))
    probes: List[Dict[str, Any]] = []
    if server_up:
        probes.append(probe_face_health(args.base_url, args.timeout))
        probes.append(probe_plate_health(args.base_url, args.timeout))
    else:
        probes.append(
            {
                "id": "server",
                "ok": False,
                "checks": [{"check": "server", "status": "skip", "detail": health_detail}],
            }
        )

    passed = sum(1 for p in probes if p.get("ok"))
    root = repo_root()
    payload = {
        "generated_at": utc_ts(),
        "base_url": args.base_url,
        "server_up": server_up,
        "health_detail": health_detail,
        "acme_root": str(root),
        "face_rec_onnx": str(root / "VIDEO" / "face_rec.onnx"),
        "plate_detect_onnx": str(root / "VIDEO" / "plate_detect.onnx"),
        "plate_rec_onnx": str(root / "VIDEO" / "plate_rec.onnx"),
        "probes": probes,
        "summary": {"pass": passed, "total": len(probes)},
        "disclaimer": DISCLAIMER,
    }
    write_artifacts(payload)

    for row in probes:
        flag = "OK" if row.get("ok") else "FAIL"
        print(f"  {row.get('id')}: {flag}")
    print(f"\nfr-b43: {passed}/{len(probes)} pass")
    return 0 if passed == len(probes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
