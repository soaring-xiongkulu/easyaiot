#!/usr/bin/env python3
"""FR-B44 — matching hit → alert local evidence (Python-first).

Python-first:
- library_matching_service.process_face_matching_message L215-300
- library_matching_service._create_match_alert L110-152 (face_library_match)
- face_matching_kafka_service.build_face_matching_message L25-62

Requires server profile with use-direct-process=false (fr-b44-soak).
Artifacts: logs/fr-b44-matching-alert-latest.{json,md}
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
from fr_b37_multipart import create_library, delete_path, http_post_multipart
from seed_fr_b44_fixture import seed_fixture
from vj_common import http_json, repo_root

_PY_LIB_MATCH = "VIDEO/_retired_python_video/app/services/library_matching_service.py"
_PY_FACE_KAFKA = "VIDEO/_retired_python_video/app/services/face_matching_kafka_service.py"
_PY_FACE_MATCHING = "VIDEO/_retired_python_video/app/blueprints/face.py"
_EVENT_FACE = "face_library_match"

DISCLAIMER = (
    "FR-B44 matching-alert requires enrolled face (FR-B41 path), Milvus, "
    "use-direct-process=false, and matching task with face_library_ids. "
    "Local-only evidence — not COMPLETE."
)


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def face_fixture_path() -> Path:
    path = repo_root() / "testdata" / "fr-b41" / "face_sample.jpg"
    if not path.exists():
        raise FileNotFoundError(f"fixture missing: {path}")
    return path


def enroll_face(base_url: str, ts: str, image: bytes, timeout: float) -> Tuple[Optional[int], Optional[int]]:
    lib_id = create_library(base_url, "/video/face/libraries", f"frb44_face_{ts}", timeout)
    if lib_id is None:
        return None, None
    status, body, _ = http_post_multipart(
        base_url,
        f"/video/face/libraries/{lib_id}/entries",
        {"person_name": f"frb44_person_{ts}"},
        [("file", "face_sample.jpg", image, "image/jpeg")],
        timeout=timeout,
    )
    entry_id = None
    if isinstance(body, dict) and body.get("code") == 0:
        entry_id = (body.get("data") or {}).get("id")
    else:
        delete_path(base_url, f"/video/face/libraries/{lib_id}", timeout)
        return None, None
    return lib_id, entry_id


def probe_face_matching_alert(
    base_url: str,
    ts: str,
    image_path: str,
    task_id: int,
    face_lib_id: int,
    timeout: float,
) -> Dict[str, Any]:
    correlation_id = f"frb44_match_{ts}"
    row: Dict[str, Any] = {
        "id": "face_matching_hit_alert",
        "path": "POST /video/face/matching/process",
        "python_source": (
            f"{_PY_LIB_MATCH} process_face_matching_message L215-300 → "
            f"_create_match_alert L110-152 event={_EVENT_FACE}"
        ),
        "kafka_builder": f"{_PY_FACE_KAFKA} build_face_matching_message L25-62",
        "http_route": f"{_PY_FACE_MATCHING} matching/process",
        "checks": [],
        "correlation_id": correlation_id,
    }
    payload = {
        "taskId": task_id,
        "taskName": f"frb44_match_{ts}",
        "taskType": "realtime",
        "deviceId": "frb44_device",
        "deviceName": "FR-B44 Matching Alert",
        "libraryId": face_lib_id,
        "faceImagePath": image_path,
        "threshold": 0.55,
        "correlationId": correlation_id,
        "sourceEvent": "frb44_probe",
    }
    status, body, _ = http_json(
        "POST",
        f"{base_url.rstrip('/')}/video/face/matching/process",
        payload,
        timeout=timeout,
    )
    row["http_status"] = status
    row["business_code"] = body.get("code") if isinstance(body, dict) else None
    row["msg"] = body.get("msg") if isinstance(body, dict) else None
    data = body.get("data") if isinstance(body, dict) else {}
    row["process_data"] = data

    ok = status < 500 and isinstance(body, dict) and body.get("code") == 0
    if not ok:
        row["checks"].append(
            {
                "check": "process_success",
                "status": "fail",
                "detail": f"HTTP {status} code={body.get('code') if isinstance(body, dict) else None} msg={body.get('msg') if isinstance(body, dict) else body}",
            }
        )
        row["ok"] = False
        return row
    row["checks"].append({"check": "process_success", "status": "pass"})

    matched = data.get("matched")
    alert_id = data.get("alert_id")
    status_field = data.get("status")
    row["matched"] = matched
    row["alert_id"] = alert_id
    row["record_status"] = status_field

    if matched is True:
        row["checks"].append({"check": "matched", "status": "pass", "detail": "matched=true"})
    elif status_field == "bypassed":
        row["checks"].append(
            {
                "check": "matched",
                "status": "honest_bypass",
                "detail": data.get("error_message") or "engine bypassed (use-direct-process or no worker)",
            }
        )
        ok = False
    else:
        row["checks"].append({"check": "matched", "status": "fail", "detail": f"matched={matched}"})
        ok = False

    if alert_id:
        row["checks"].append({"check": "alert_id", "status": "pass", "detail": str(alert_id)})
        page_status, page_body, _ = http_json(
            "GET",
            f"{base_url.rstrip('/')}/video/alert/page?page=1&page_size=5&correlation_id={correlation_id}",
            timeout=timeout,
        )
        row["alert_page_http"] = page_status
        alerts = []
        if isinstance(page_body, dict):
            data = page_body.get("data") or {}
            alerts = data.get("alert_list") or data.get("list") or []
        face_alerts = [a for a in alerts if isinstance(a, dict) and a.get("event") == _EVENT_FACE]
        row["alert_events_found"] = len(face_alerts)
        if face_alerts:
            row["alert_event"] = face_alerts[0].get("event")
            row["checks"].append(
                {"check": "alert_event", "status": "pass", "detail": f"event={_EVENT_FACE} id={face_alerts[0].get('id')}"}
            )
        else:
            row["checks"].append(
                {"check": "alert_event", "status": "fail", "detail": f"page query: {len(alerts)} alerts, none {_EVENT_FACE}"}
            )
            ok = False
    else:
        row["checks"].append({"check": "alert_id", "status": "fail", "detail": "alert_id null"})
        ok = False

    sim = data.get("similarity")
    if sim is not None:
        row["similarity"] = sim
        row["checks"].append({"check": "similarity", "status": "pass", "detail": str(sim)})

    row["ok"] = ok and all(c["status"] == "pass" for c in row["checks"])
    return row


def write_artifacts(payload: Dict[str, Any]) -> Tuple[Path, Path]:
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ts = payload.get("generated_at", utc_ts())
    json_path = logs / f"fr-b44-matching-alert-{ts}.json"
    md_path = logs / f"fr-b44-matching-alert-{ts}.md"
    latest_json = logs / "fr-b44-matching-alert-latest.json"
    latest_md = logs / "fr-b44-matching-alert-latest.md"
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    json_path.write_text(text, encoding="utf-8")
    latest_json.write_text(text, encoding="utf-8")

    lines = [
        "# FR-B44 matching-alert probes",
        "",
        f"- generated_at: {payload.get('generated_at')}",
        f"- base_url: {payload.get('base_url')}",
        f"- profile_hint: {payload.get('profile_hint')}",
        "",
        "## Python-first cites",
        "",
        f"- process: `{_PY_LIB_MATCH}` process_face_matching_message",
        f"- alert: `{_PY_LIB_MATCH}` _create_match_alert",
        f"- kafka: `{_PY_FACE_KAFKA}`",
        "",
        "## Results",
        "",
        "| id | http | code | ok | matched | alert_id |",
        "|----|------|------|-----|---------|----------|",
    ]
    for row in payload.get("probes", []):
        lines.append(
            f"| {row.get('id')} | {row.get('http_status', '—')} | {row.get('business_code', '—')} | "
            f"{row.get('ok')} | {row.get('matched', '—')} | {row.get('alert_id', '—')} |"
        )
    lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"artifact: {json_path}")
    print(f"artifact: {md_path}")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="FR-B44 matching hit → alert probes")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--skip-seed", action="store_true")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    image_path = str(face_fixture_path().resolve()).replace("\\", "/")
    image = face_fixture_path().read_bytes()
    server_up, health_detail = server_reachable(args.base_url, timeout=min(args.timeout, 5.0))

    fixture: Dict[str, Any] = {}
    if not args.skip_seed:
        try:
            fixture = seed_fixture()
            print(f"seed: device={fixture.get('device_id')} task_id={fixture.get('task_id')}")
        except Exception as exc:
            print(f"seed warning: {exc}")

    probes: List[Dict[str, Any]] = []
    if not server_up:
        probes.append({"id": "server", "ok": False, "checks": [{"check": "server", "status": "skip", "detail": health_detail}]})
    else:
        face_lib_id, entry_id = enroll_face(args.base_url, ts, image, args.timeout)
        if face_lib_id is None:
            probes.append(
                {
                    "id": "face_enroll",
                    "ok": False,
                    "checks": [{"check": "enroll", "status": "fail", "detail": "face library entry failed"}],
                }
            )
        else:
            task_id = fixture.get("task_id")
            if task_id is None:
                probes.append(
                    {
                        "id": "fixture",
                        "ok": False,
                        "checks": [{"check": "task", "status": "fail", "detail": "seed fixture task_id missing"}],
                    }
                )
            else:
                seed_fixture(face_lib_id=face_lib_id, task_id=task_id)
                probes.append(
                    probe_face_matching_alert(
                        args.base_url, ts, image_path, int(task_id), int(face_lib_id), args.timeout
                    )
                )
            if entry_id:
                delete_path(args.base_url, f"/video/face/entries/{entry_id}", args.timeout)
            if face_lib_id:
                delete_path(args.base_url, f"/video/face/libraries/{face_lib_id}", args.timeout)

    passed = sum(1 for p in probes if p.get("ok"))
    payload = {
        "generated_at": utc_ts(),
        "base_url": args.base_url,
        "server_up": server_up,
        "health_detail": health_detail,
        "profile_hint": "local,fr-b44-soak (use-direct-process=false)",
        "fixture_image": image_path,
        "face_rec_onnx": str(repo_root() / "VIDEO" / "face_rec.onnx"),
        "seed_fixture": fixture,
        "probes": probes,
        "summary": {"pass": passed, "total": len(probes)},
        "disclaimer": DISCLAIMER,
    }
    write_artifacts(payload)

    for row in probes:
        flag = "OK" if row.get("ok") else "FAIL"
        print(f"  {row.get('id')}: {flag}")
    print(f"\nfr-b44-matching-alert: {passed}/{len(probes)} pass")
    return 0 if passed == len(probes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
