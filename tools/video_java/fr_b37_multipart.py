#!/usr/bin/env python3
"""FR-B37 multipart success probes — face/plate entry (+ scenario-pose extract if feasible).

Python-first: multipart fields + success to_dict keys from retired blueprints.
Artifacts: logs/fr-b37-multipart-latest.{json,md}
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# tools/video_java on path when run as script
_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from bucket_naming import certify_bucket_name, is_valid_s3_bucket_name
from field_contract import http_post_json, server_reachable
from fr_b25_minio_upload_e2e import _MIN_JPEG
from post_keys_matrix_b34_specs import FACE_ENTRY_KEYS, PLATE_ENTRY_KEYS
from vj_common import http_json, repo_root

_PY = "VIDEO/_retired_python_video"
_FACE_BP = f"{_PY}/app/blueprints/face.py"
_PLATE_BP = f"{_PY}/app/blueprints/plate.py"
_POSE_BP = f"{_PY}/app/blueprints/scenario_pose.py"
_MODELS = f"{_PY}/models.py"

# scenario_pose_library_service.extract_preview L339-353
POSE_EXTRACT_KEYS: Set[str] = {"count", "persons"}

DISCLAIMER = (
    "FR-B37 multipart success probes use tiny fixture JPEG under testdata/fr-b37/. "
    "Face/plate entry assert Python to_dict keys on code==0. "
    "Inference-engine or pose-model absence may yield honest 500 — documented as EX, not COMPLETE."
)


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def tiny_jpeg_path() -> Path:
    path = repo_root() / "testdata" / "fr-b37" / "tiny.jpg"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(_MIN_JPEG)
    return path


def http_post_multipart(
    base_url: str,
    path: str,
    fields: Dict[str, str],
    files: List[Tuple[str, str, bytes, str]],
    timeout: float = 12.0,
) -> Tuple[int, Dict[str, Any], str]:
    import urllib.error
    import urllib.request

    boundary = f"----frb37{uuid.uuid4().hex}"
    body = bytearray()
    for key, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        body.extend(value.encode("utf-8"))
        body.extend(b"\r\n")
    for field_name, filename, content, content_type in files:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode()
        )
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.extend(content)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())

    url = base_url.rstrip("/") + path
    req = urllib.request.Request(
        url,
        data=bytes(body),
        headers={
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        status = 0
        raw = str(exc)
    try:
        parsed = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        parsed = {"_raw": raw}
    if not isinstance(parsed, dict):
        parsed = {"data": parsed}
    return status, parsed, raw


def assert_data_keys(data: Any, expected: Set[str], checks: List[Dict[str, Any]]) -> bool:
    if not isinstance(data, dict):
        checks.append({"check": "data_keys", "status": "fail", "detail": "data is not object"})
        return False
    missing = sorted(expected - set(data.keys()))
    if missing:
        checks.append({"check": "data_keys", "status": "fail", "detail": f"missing keys: {missing}"})
        return False
    checks.append({"check": "data_keys", "status": "pass", "detail": f"keys ok ({len(expected)})"})
    return True


def create_library(base_url: str, path: str, name: str, timeout: float) -> Optional[int]:
    status, body, _ = http_post_json(base_url, path, {"name": name}, timeout=timeout)
    if status >= 500 or not isinstance(body, dict) or body.get("code") != 0:
        return None
    data = body.get("data")
    if isinstance(data, dict) and data.get("id") is not None:
        return int(data["id"])
    return None


def delete_path(base_url: str, path: str, timeout: float) -> None:
    import urllib.error
    import urllib.request

    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url, method="DELETE", headers={"Accept": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError:
        pass
    except (urllib.error.URLError, OSError, TimeoutError):
        pass


def probe_face_entry(base_url: str, ts: str, image: bytes, timeout: float) -> Dict[str, Any]:
    lib_id = create_library(base_url, "/video/face/libraries", f"frb37_face_{ts}", timeout)
    row: Dict[str, Any] = {
        "id": "face_entry_multipart_success",
        "path": "/video/face/libraries/{id}/entries",
        "python_source": f"{_FACE_BP} add_face_entry L262-281 → {_MODELS} FaceEntry.to_dict L1327-1341",
        "multipart_fields": ["person_name", "file"],
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
        {"person_name": f"frb37_person_{ts}"},
        [("file", "tiny.jpg", image, "image/jpeg")],
        timeout=timeout,
    )
    row["http_status"] = status
    row["business_code"] = body.get("code") if isinstance(body, dict) else None
    row["msg"] = body.get("msg") if isinstance(body, dict) else None
    ok = status < 500 and isinstance(body, dict) and body.get("code") == 0
    if ok:
        ok = assert_data_keys(body.get("data"), FACE_ENTRY_KEYS, row["checks"])
        entry_id = (body.get("data") or {}).get("id")
        if entry_id:
            delete_path(base_url, f"/video/face/entries/{entry_id}", timeout)
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


def probe_plate_entry(base_url: str, ts: str, image: bytes, timeout: float) -> Dict[str, Any]:
    lib_id = create_library(base_url, "/video/plate/libraries", f"frb37_plate_{ts}", timeout)
    row: Dict[str, Any] = {
        "id": "plate_entry_multipart_success",
        "path": "/video/plate/libraries/{id}/entries",
        "python_source": f"{_PLATE_BP} add_plate_entry L166-182 → {_MODELS} PlateEntry.to_dict",
        "multipart_fields": ["plate_no", "file"],
        "checks": [],
    }
    if lib_id is None:
        row["ok"] = False
        row["checks"].append({"check": "setup", "status": "fail", "detail": "plate library create failed"})
        return row
    path = f"/video/plate/libraries/{lib_id}/entries"
    row["probe_path"] = path
    plate_no = f"FRB37{ts[-6:].upper()}"
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
    if ok:
        ok = assert_data_keys(body.get("data"), PLATE_ENTRY_KEYS, row["checks"])
        entry_id = (body.get("data") or {}).get("id")
        if entry_id:
            delete_path(base_url, f"/video/plate/entries/{entry_id}", timeout)
    else:
        row["checks"].append(
            {
                "check": "success",
                "status": "fail",
                "detail": f"HTTP {status} code={body.get('code') if isinstance(body, dict) else None} msg={body.get('msg') if isinstance(body, dict) else body}",
            }
        )
    delete_path(base_url, f"/video/plate/libraries/{lib_id}", timeout)
    row["ok"] = ok and all(c["status"] == "pass" for c in row["checks"])
    return row


def probe_pose_extract(base_url: str, image: bytes, timeout: float) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "id": "scenario_pose_extract_multipart_success",
        "path": "/video/scenario-pose/entries/extract",
        "python_source": f"{_POSE_BP} extract_preview L168-173 → scenario_pose_library_service L339-353",
        "multipart_fields": ["file", "conf (optional)"],
        "checks": [],
    }
    status, body, _ = http_post_multipart(
        base_url,
        "/video/scenario-pose/entries/extract",
        {},
        [("file", "tiny.jpg", image, "image/jpeg")],
        timeout=timeout,
    )
    row["http_status"] = status
    row["business_code"] = body.get("code") if isinstance(body, dict) else None
    row["msg"] = body.get("msg") if isinstance(body, dict) else None
    ok = status < 500 and isinstance(body, dict) and body.get("code") == 0
    if ok:
        ok = assert_data_keys(body.get("data"), POSE_EXTRACT_KEYS, row["checks"])
    else:
        row["checks"].append(
            {
                "check": "success",
                "status": "fail",
                "detail": f"HTTP {status} code={body.get('code') if isinstance(body, dict) else None} (pose engine may be absent)",
            }
        )
    row["ok"] = ok and all(c["status"] == "pass" for c in row["checks"])
    row["feasible"] = ok
    return row


def probe_bucket_naming() -> Dict[str, Any]:
    bad = "certify-vj_p2_record"
    good = certify_bucket_name("vj_p2_record")
    return {
        "id": "bucket_naming_fixture",
        "illegal_example": bad,
        "legal_example": good,
        "illegal_has_underscore": "_" in bad,
        "legal_valid": is_valid_s3_bucket_name(good),
        "ok": is_valid_s3_bucket_name(good) and not is_valid_s3_bucket_name(bad),
        "python_source": "tools/video_java/bucket_naming.py + seed_p2_fixture.py _ensure_space",
    }


def probe_metadata_sync(base_url: str, fixture: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    """POST images/videos sync on vj_p2 fixture space — expect 0 not 500 after bucket fix."""
    snap_id = fixture.get("snap_space_id")
    record_id = fixture.get("record_space_id")
    rows = []
    for label, space_id, path in (
        ("snap_images_sync", snap_id, f"/video/snap/space/{snap_id}/images/sync"),
        ("record_videos_sync", record_id, f"/video/record/space/{record_id}/videos/sync"),
    ):
        if not space_id:
            rows.append({"id": label, "ok": False, "detail": "fixture space_id missing"})
            continue
        status, body, _ = http_post_json(base_url, path, {}, timeout=timeout)
        code = body.get("code") if isinstance(body, dict) else None
        ok = status < 500 and code == 0
        rows.append(
            {
                "id": label,
                "path": path,
                "http_status": status,
                "business_code": code,
                "msg": body.get("msg") if isinstance(body, dict) else None,
                "ok": ok,
                "python_source": f"{_PY}/app/blueprints/snap.py|record.py sync metadata",
            }
        )
    return {"id": "metadata_sync_after_bucket_fix", "probes": rows, "ok": all(r.get("ok") for r in rows)}


def load_vj_p2_fixture() -> Dict[str, Any]:
    path = repo_root() / "testdata" / "video-java" / "fixtures" / "vj_p2.json"
    return json.loads(path.read_text(encoding="utf-8"))


def write_artifacts(payload: Dict[str, Any]) -> Tuple[Path, Path]:
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ts = payload.get("generated_at", utc_ts())
    json_path = logs / f"fr-b37-multipart-{ts}.json"
    md_path = logs / f"fr-b37-multipart-{ts}.md"
    latest_json = logs / "fr-b37-multipart-latest.json"
    latest_md = logs / "fr-b37-multipart-latest.md"
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    json_path.write_text(text + "\n", encoding="utf-8")
    latest_json.write_text(text + "\n", encoding="utf-8")

    lines = [
        "# FR-B37 Multipart Success Probes",
        "",
        f"**Generated:** {payload.get('generated_at')}",
        f"**Base URL:** {payload.get('base_url')}",
        f"**Server up:** {payload.get('server_up')}",
        f"**Pass:** {payload.get('summary', {}).get('pass')}/{payload.get('summary', {}).get('total')}",
        "",
        "## Disclaimer",
        "",
        DISCLAIMER,
        "",
        "## Python-first mapping",
        "",
        "| id | path | multipart fields | python_source |",
        "|----|------|------------------|---------------|",
    ]
    for row in payload.get("probes", []):
        if row.get("id") == "metadata_sync_after_bucket_fix":
            continue
        lines.append(
            f"| {row.get('id')} | `{row.get('path', '')}` | "
            f"{row.get('multipart_fields', '—')} | {row.get('python_source', '')} |"
        )
    lines.extend(["", "## Results", "", "| id | http | code | key_assert | ok |", "|----|------|------|------------|-----|"])
    for row in payload.get("probes", []):
        if row.get("id") == "metadata_sync_after_bucket_fix":
            for sub in row.get("probes", []):
                ka = "pass" if sub.get("ok") else "fail"
                lines.append(
                    f"| {sub.get('id')} | {sub.get('http_status')} | {sub.get('business_code')} | {ka} | {sub.get('ok')} |"
                )
            continue
        ka = next(
            (c["status"] for c in row.get("checks", []) if c["check"] == "data_keys"),
            "—",
        )
        lines.append(
            f"| {row.get('id')} | {row.get('http_status', '—')} | {row.get('business_code', '—')} | {ka} | {row.get('ok')} |"
        )
    bn = payload.get("bucket_naming", {})
    lines.extend(
        [
            "",
            "## Bucket naming",
            "",
            f"- illegal: `{bn.get('illegal_example')}` valid={not bn.get('legal_valid') if bn.get('illegal_example') else 'n/a'}",
            f"- legal: `{bn.get('legal_example')}` valid={bn.get('legal_valid')}",
            "",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"artifact: {json_path}")
    print(f"artifact: {md_path}")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="FR-B37 multipart success probes")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--timeout", type=float, default=12.0)
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    image_path = tiny_jpeg_path()
    image = image_path.read_bytes()
    server_up, health_detail = server_reachable(args.base_url, timeout=min(args.timeout, 3.0))

    probes: List[Dict[str, Any]] = []
    probes.append(probe_bucket_naming())

    if server_up:
        probes.append(probe_face_entry(args.base_url, ts, image, args.timeout))
        probes.append(probe_plate_entry(args.base_url, ts, image, args.timeout))
        probes.append(probe_pose_extract(args.base_url, image, args.timeout))
        try:
            fixture = load_vj_p2_fixture()
            probes.append(probe_metadata_sync(args.base_url, fixture, args.timeout))
        except Exception as exc:
            probes.append({"id": "metadata_sync_after_bucket_fix", "ok": False, "detail": str(exc)})
    else:
        for pid in (
            "face_entry_multipart_success",
            "plate_entry_multipart_success",
            "scenario_pose_extract_multipart_success",
        ):
            probes.append(
                {
                    "id": pid,
                    "ok": False,
                    "checks": [{"check": "server", "status": "skip", "detail": health_detail}],
                }
            )

    core = [p for p in probes if p.get("id") not in ("bucket_naming_fixture", "metadata_sync_after_bucket_fix")]
    passed = sum(1 for p in core if p.get("ok"))
    payload = {
        "generated_at": utc_ts(),
        "base_url": args.base_url,
        "server_up": server_up,
        "health_detail": health_detail,
        "fixture_image": str(image_path.relative_to(repo_root())),
        "bucket_naming": probes[0],
        "probes": probes[1:],
        "summary": {"pass": passed, "total": len(core), "bucket_ok": probes[0].get("ok")},
        "disclaimer": DISCLAIMER,
    }
    write_artifacts(payload)

    for row in core:
        flag = "OK" if row.get("ok") else "FAIL"
        print(f"  {row.get('id')}: {flag}")
    print(f"\nmultipart: {passed}/{len(core)} pass | bucket_naming={probes[0].get('ok')}")
    print(f"\n{DISCLAIMER}")
    return 0 if passed == len(core) and probes[0].get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
