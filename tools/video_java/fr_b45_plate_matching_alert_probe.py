#!/usr/bin/env python3
"""FR-B45 — plate matching hit → alert local evidence (Python-first).

Python-first:
- library_matching_service.process_plate_matching_message L303-382
- library_matching_service._create_match_alert L110-152 (plate_library_match)
- plate_matching_kafka_service.build_plate_matching_message L23-60

Requires server profile with use-direct-process=false (fr-b45-soak).
Artifacts: logs/fr-b45-plate-matching-alert-latest.{json,md}
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
from seed_fr_b45_fixture import seed_fixture
from vj_common import http_json, repo_root

_PY_LIB_MATCH = "VIDEO/_retired_python_video/app/services/library_matching_service.py"
_PY_PLATE_KAFKA = "VIDEO/_retired_python_video/app/services/plate_matching_kafka_service.py"
_PY_PLATE_MATCHING = "VIDEO/_retired_python_video/app/blueprints/plate.py"
_EVENT_PLATE = "plate_library_match"

DISCLAIMER = (
    "FR-B45 plate matching-alert requires enrolled plate, matching task with plate_library_ids, "
    "use-direct-process=false. Local-only evidence — not COMPLETE."
)


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def enroll_plate(base_url: str, ts: str, plate_no: str, timeout: float) -> Tuple[Optional[int], Optional[int]]:
    lib_id = create_library(base_url, "/video/plate/libraries", f"frb45_plate_{ts}", timeout)
    if lib_id is None:
        return None, None
    status, body, _ = http_json(
        "POST",
        f"{base_url.rstrip('/')}/video/plate/libraries/{lib_id}/entries",
        {
            "plate_no": plate_no,
            "plate_color": "blue",
            "owner_name": f"frb45_owner_{ts}",
            "is_enabled": True,
        },
        timeout=timeout,
    )
    entry_id = None
    if isinstance(body, dict) and body.get("code") == 0:
        entry_id = (body.get("data") or {}).get("id")
    else:
        delete_path(base_url, f"/video/plate/libraries/{lib_id}", timeout)
        return None, None
    return lib_id, entry_id


def probe_plate_matching_alert(
    base_url: str,
    ts: str,
    plate_no: str,
    task_id: int,
    plate_lib_id: int,
    timeout: float,
) -> Dict[str, Any]:
    correlation_id = f"frb45_plate_match_{ts}"
    row: Dict[str, Any] = {
        "id": "plate_matching_hit_alert",
        "path": "POST /video/plate/matching/process",
        "python_source": (
            f"{_PY_LIB_MATCH} process_plate_matching_message L303-382 → "
            f"_create_match_alert L110-152 event={_EVENT_PLATE}"
        ),
        "kafka_builder": f"{_PY_PLATE_KAFKA} build_plate_matching_message L23-60",
        "http_route": f"{_PY_PLATE_MATCHING} matching/process",
        "checks": [],
        "correlation_id": correlation_id,
        "plate_no": plate_no,
    }
    payload = {
        "taskId": task_id,
        "taskName": f"frb45_match_{ts}",
        "taskType": "realtime",
        "deviceId": "frb45_device",
        "deviceName": "FR-B45 Plate Matching Alert",
        "libraryId": plate_lib_id,
        "plateNo": plate_no,
        "plateColor": "blue",
        "correlationId": correlation_id,
    }
    status, body, _ = http_json(
        "POST",
        f"{base_url.rstrip('/')}/video/plate/matching/process",
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
                "detail": f"HTTP {status} code={body.get('code') if isinstance(body, dict) else None}",
            }
        )
        row["ok"] = False
        return row
    row["checks"].append({"check": "process_success", "status": "pass"})

    matched = data.get("matched")
    alert_id = data.get("alert_id")
    row["matched"] = matched
    row["alert_id"] = alert_id

    if matched is True:
        row["checks"].append({"check": "matched", "status": "pass", "detail": "matched=true"})
    else:
        row["checks"].append({"check": "matched", "status": "fail", "detail": f"matched={matched}"})
        ok = False

    if alert_id:
        row["checks"].append({"check": "alert_id", "status": "pass", "detail": str(alert_id)})
        page_status, page_body, _ = http_json(
            "GET",
            f"{base_url.rstrip('/')}/video/alert/correlation?correlation_id={correlation_id}",
            timeout=timeout,
        )
        row["alert_corr_http"] = page_status
        alerts = []
        if isinstance(page_body, dict):
            data = page_body.get("data") or {}
            alerts = data.get("alerts") or []
        plate_alerts = [a for a in alerts if isinstance(a, dict) and a.get("event") == _EVENT_PLATE]
        row["alert_events_found"] = len(plate_alerts)
        if plate_alerts:
            row["alert_event"] = plate_alerts[0].get("event")
            row["checks"].append(
                {
                    "check": "alert_event",
                    "status": "pass",
                    "detail": f"event={_EVENT_PLATE} id={plate_alerts[0].get('id')} (correlation API)",
                }
            )
        else:
            row["checks"].append(
                {
                    "check": "alert_event",
                    "status": "fail",
                    "detail": f"correlation query: {len(alerts)} alerts, none {_EVENT_PLATE}",
                }
            )
            ok = False
    else:
        row["checks"].append({"check": "alert_id", "status": "fail", "detail": "alert_id null"})
        ok = False

    row["ok"] = ok and all(c["status"] == "pass" for c in row["checks"])
    return row


def write_artifacts(payload: Dict[str, Any]) -> Tuple[Path, Path]:
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ts = payload.get("generated_at", utc_ts())
    json_path = logs / f"fr-b45-plate-matching-alert-{ts}.json"
    md_path = logs / f"fr-b45-plate-matching-alert-{ts}.md"
    latest_json = logs / "fr-b45-plate-matching-alert-latest.json"
    latest_md = logs / "fr-b45-plate-matching-alert-latest.md"
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    json_path.write_text(text, encoding="utf-8")
    latest_json.write_text(text, encoding="utf-8")

    lines = [
        "# FR-B45 plate matching-alert probes",
        "",
        f"- generated_at: {payload.get('generated_at')}",
        f"- base_url: {payload.get('base_url')}",
        f"- profile_hint: {payload.get('profile_hint')}",
        "",
        "## Python-first cites",
        "",
        f"- process: `{_PY_LIB_MATCH}` process_plate_matching_message",
        f"- alert: `{_PY_LIB_MATCH}` _create_match_alert",
        f"- kafka: `{_PY_PLATE_KAFKA}`",
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
    parser = argparse.ArgumentParser(description="FR-B45 plate matching hit → alert probes")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--skip-seed", action="store_true")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    plate_no = f"FRB45{ts[-6:]}"
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
        plate_lib_id, entry_id = enroll_plate(args.base_url, ts, plate_no, args.timeout)
        if plate_lib_id is None:
            probes.append(
                {
                    "id": "plate_enroll",
                    "ok": False,
                    "checks": [{"check": "enroll", "status": "fail", "detail": "plate library entry failed"}],
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
                seed_fixture(plate_lib_id=plate_lib_id, task_id=task_id)
                probes.append(
                    probe_plate_matching_alert(
                        args.base_url, ts, plate_no, int(task_id), int(plate_lib_id), args.timeout
                    )
                )
            if entry_id:
                delete_path(args.base_url, f"/video/plate/entries/{entry_id}", args.timeout)
            if plate_lib_id:
                delete_path(args.base_url, f"/video/plate/libraries/{plate_lib_id}", args.timeout)

    passed = sum(1 for p in probes if p.get("ok"))
    payload = {
        "generated_at": utc_ts(),
        "base_url": args.base_url,
        "server_up": server_up,
        "health_detail": health_detail,
        "profile_hint": "local,fr-b45-soak (use-direct-process=false)",
        "seed_fixture": fixture,
        "probes": probes,
        "summary": {"pass": passed, "total": len(probes)},
        "disclaimer": DISCLAIMER,
    }
    write_artifacts(payload)

    for row in probes:
        flag = "OK" if row.get("ok") else "FAIL"
        print(f"  {row.get('id')}: {flag}")
    print(f"\nfr-b45-plate-matching-alert: {passed}/{len(probes)} pass")
    return 0 if passed == len(probes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
