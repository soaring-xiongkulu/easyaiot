#!/usr/bin/env python3
"""FR-B44 — pose extract + match-test real YOLO evidence (Python-first).

Python-first:
- scenario_pose.py extract_preview L168-179 → scenario_pose_library_service L339-353
- scenario_pose.py match_test L182-193 → scenario_pose_library_service L356-391
- pose_analysis.py load_pose_model + run_pose_analysis (yolo26n-pose.pt)

Artifacts: logs/fr-b44-pose-latest.{json,md}
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from field_contract import http_post_json, server_reachable
from fr_b37_multipart import delete_path, http_post_multipart, utc_ts
from vj_common import repo_root

_PY_POSE_BP = "VIDEO/_retired_python_video/app/blueprints/scenario_pose.py"
_PY_POSE_SVC = "VIDEO/_retired_python_video/app/services/scenario_pose_library_service.py"
_PY_POSE_ANALYSIS = "VIDEO/_retired_python_video/app/utils/pose_analysis.py"
_POSE_CLI = "VIDEO/scripts/inference_workers/pose_inference_cli.py"

POSE_EXTRACT_KEYS: Set[str] = {"count", "persons"}
MATCH_TEST_KEYS: Set[str] = {"entry_id", "entry_name", "similarity", "matched", "person_index"}

DISCLAIMER = (
    "FR-B44 pose probes require live video-server + Python worker + yolo26n-pose.pt. "
    "Real keypoints/scores — not bypass. Local-only evidence — not COMPLETE."
)


def pose_fixture_path() -> Path:
    path = repo_root() / "testdata" / "fr-b41" / "face_sample.jpg"
    if not path.exists():
        raise FileNotFoundError(f"fixture missing: {path}")
    return path


def yolo_pose_weights() -> List[str]:
    root = repo_root()
    candidates = [
        root / "VIDEO" / "yolo26n-pose.pt",
        root / "AI" / "yolo26n-pose.pt",
        root / "yolo26n-pose.pt",
    ]
    return [str(p) for p in candidates if p.is_file()]


def probe_pose_extract(base_url: str, image: bytes, timeout: float) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "id": "pose_extract_real_keypoints",
        "path": "POST /video/scenario-pose/entries/extract",
        "python_source": (
            f"{_PY_POSE_BP} extract_preview L168-179 → "
            f"{_PY_POSE_SVC} extract_preview L339-353 → "
            f"{_PY_POSE_ANALYSIS} run_pose_analysis"
        ),
        "worker_cli": _POSE_CLI,
        "yolo_weights": yolo_pose_weights(),
        "checks": [],
    }
    status, body, _ = http_post_multipart(
        base_url,
        "/video/scenario-pose/entries/extract",
        {"conf": "0.25"},
        [("file", "face_sample.jpg", image, "image/jpeg")],
        timeout=timeout,
    )
    row["http_status"] = status
    row["business_code"] = body.get("code") if isinstance(body, dict) else None
    data = body.get("data") if isinstance(body, dict) else {}
    row["data_summary"] = {
        "count": data.get("count"),
        "persons_len": len(data.get("persons") or []),
    }
    ok = status < 500 and isinstance(body, dict) and body.get("code") == 0
    if not ok:
        row["checks"].append(
            {"check": "success", "status": "fail", "detail": f"HTTP {status} code={body.get('code') if isinstance(body, dict) else None}"}
        )
        row["ok"] = False
        return row

    missing = POSE_EXTRACT_KEYS - set(data.keys())
    if missing:
        row["checks"].append({"check": "data_keys", "status": "fail", "detail": f"missing: {sorted(missing)}"})
        ok = False
    else:
        row["checks"].append({"check": "data_keys", "status": "pass"})

    count = int(data.get("count") or 0)
    persons = data.get("persons") or []
    if count > 0 and persons:
        row["checks"].append({"check": "person_detected", "status": "pass", "detail": f"count={count}"})
    else:
        row["checks"].append({"check": "person_detected", "status": "fail", "detail": "count=0 (bypass or no YOLO)"})
        ok = False

    first = persons[0] if persons else {}
    kps = first.get("keypoints") or []
    if len(kps) >= 17:
        row["checks"].append({"check": "keypoint_count", "status": "pass", "detail": f"{len(kps)} keypoints"})
    else:
        row["checks"].append({"check": "keypoint_count", "status": "fail", "detail": f"only {len(kps)} keypoints"})
        ok = False

    scores = [kp[2] for kp in kps if isinstance(kp, list) and len(kp) >= 3]
    max_score = max(scores) if scores else 0.0
    row["max_keypoint_conf"] = round(max_score, 4)
    if max_score >= 0.5:
        row["checks"].append({"check": "real_scores", "status": "pass", "detail": f"max_conf={max_score:.4f}"})
    else:
        row["checks"].append({"check": "real_scores", "status": "fail", "detail": f"max_conf={max_score:.4f} (stub?)"})
        ok = False

    feat = first.get("feature_vector")
    if isinstance(feat, list) and len(feat) > 0:
        row["checks"].append({"check": "feature_vector", "status": "pass", "detail": f"len={len(feat)}"})
    else:
        row["checks"].append({"check": "feature_vector", "status": "warn", "detail": "feature_vector empty"})

    row["ok"] = ok and all(c["status"] == "pass" for c in row["checks"])
    return row


def create_pose_library(base_url: str, name: str, timeout: float) -> int | None:
    status, body, _ = http_post_json(
        base_url,
        "/video/scenario-pose/libraries",
        {"name": name, "similarity_threshold": 0.5, "match_mode": "angle"},
        timeout=timeout,
    )
    if status >= 500 or not isinstance(body, dict) or body.get("code") != 0:
        return None
    data = body.get("data")
    return int(data["id"]) if isinstance(data, dict) and data.get("id") is not None else None


def probe_pose_match_test(base_url: str, ts: str, image: bytes, timeout: float) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "id": "pose_match_test_real_similarity",
        "path": "POST /video/scenario-pose/libraries/{id}/match-test",
        "python_source": (
            f"{_PY_POSE_BP} match_test L182-193 → "
            f"{_PY_POSE_SVC} match_test L356-391 → pose_intent.match_person_to_entry"
        ),
        "checks": [],
    }
    lib_id = create_pose_library(base_url, f"frb44_pose_{ts}", timeout)
    if lib_id is None:
        row["ok"] = False
        row["checks"].append({"check": "setup", "status": "fail", "detail": "pose library create failed"})
        return row

    entry_status, entry_body, _ = http_post_multipart(
        base_url,
        f"/video/scenario-pose/libraries/{lib_id}/entries",
        {"name": f"frb44_ref_{ts}", "conf": "0.25"},
        [("file", "face_sample.jpg", image, "image/jpeg")],
        timeout=timeout,
    )
    entry_id = None
    if isinstance(entry_body, dict) and entry_body.get("code") == 0:
        entry_id = (entry_body.get("data") or {}).get("id")
        row["checks"].append({"check": "entry_created", "status": "pass", "detail": f"entry_id={entry_id}"})
    else:
        row["checks"].append(
            {
                "check": "entry_created",
                "status": "fail",
                "detail": f"HTTP {entry_status} code={entry_body.get('code') if isinstance(entry_body, dict) else None}",
            }
        )

    status, body, _ = http_post_multipart(
        base_url,
        f"/video/scenario-pose/libraries/{lib_id}/match-test",
        {"conf": "0.25"},
        [("file", "face_sample.jpg", image, "image/jpeg")],
        timeout=timeout,
    )
    row["http_status"] = status
    row["business_code"] = body.get("code") if isinstance(body, dict) else None
    data = body.get("data") if isinstance(body, dict) else []
    row["match_results"] = data

    ok = status < 500 and isinstance(body, dict) and body.get("code") == 0
    if not ok:
        row["checks"].append({"check": "success", "status": "fail", "detail": f"HTTP {status}"})
        row["ok"] = False
        delete_path(base_url, f"/video/scenario-pose/libraries/{lib_id}", timeout)
        return row

    if isinstance(data, list) and data:
        best = data[0]
        missing = MATCH_TEST_KEYS - set(best.keys())
        if missing:
            row["checks"].append({"check": "match_keys", "status": "fail", "detail": f"missing: {sorted(missing)}"})
            ok = False
        else:
            row["checks"].append({"check": "match_keys", "status": "pass"})
        sim = float(best.get("similarity") or 0)
        matched = bool(best.get("matched"))
        row["similarity"] = sim
        row["matched"] = matched
        if sim >= 0.5:
            row["checks"].append({"check": "real_similarity", "status": "pass", "detail": f"sim={sim}"})
        else:
            row["checks"].append({"check": "real_similarity", "status": "fail", "detail": f"sim={sim} too low"})
            ok = False
        if matched:
            row["checks"].append({"check": "hit", "status": "pass", "detail": "matched=true"})
        else:
            row["checks"].append({"check": "hit", "status": "warn", "detail": f"matched=false sim={sim}"})
    else:
        row["checks"].append({"check": "results", "status": "fail", "detail": "empty match-test results"})
        ok = False

    if entry_id:
        delete_path(base_url, f"/video/scenario-pose/entries/{entry_id}", timeout)
    delete_path(base_url, f"/video/scenario-pose/libraries/{lib_id}", timeout)
    row["ok"] = ok and all(c["status"] == "pass" for c in row["checks"])
    return row


def write_artifacts(payload: Dict[str, Any]) -> Tuple[Path, Path]:
    logs = repo_root() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ts = payload.get("generated_at", utc_ts())
    json_path = logs / f"fr-b44-pose-{ts}.json"
    md_path = logs / f"fr-b44-pose-{ts}.md"
    latest_json = logs / "fr-b44-pose-latest.json"
    latest_md = logs / "fr-b44-pose-latest.md"
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    json_path.write_text(text, encoding="utf-8")
    latest_json.write_text(text, encoding="utf-8")

    lines = [
        "# FR-B44 pose probes",
        "",
        f"- generated_at: {payload.get('generated_at')}",
        f"- base_url: {payload.get('base_url')}",
        f"- yolo_weights: {payload.get('yolo_weights')}",
        "",
        "## Python-first cites",
        "",
        f"- extract: `{_PY_POSE_BP}` + `{_PY_POSE_SVC}` + `{_PY_POSE_ANALYSIS}`",
        f"- match-test: `{_PY_POSE_BP}` match_test + `{_PY_POSE_SVC}` match_test",
        f"- worker: `{_POSE_CLI}`",
        "",
        "## Results",
        "",
        "| id | http | code | ok | detail |",
        "|----|------|------|-----|--------|",
    ]
    for row in payload.get("probes", []):
        detail = row.get("max_keypoint_conf") or row.get("similarity") or row.get("data_summary") or ""
        lines.append(
            f"| {row.get('id')} | {row.get('http_status', '—')} | {row.get('business_code', '—')} | "
            f"{row.get('ok')} | {detail} |"
        )
    lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"artifact: {json_path}")
    print(f"artifact: {md_path}")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="FR-B44 pose extract + match-test probes")
    parser.add_argument("--base-url", default="http://127.0.0.1:48096")
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    image = pose_fixture_path().read_bytes()
    server_up, health_detail = server_reachable(args.base_url, timeout=min(args.timeout, 5.0))

    probes: List[Dict[str, Any]] = []
    if server_up:
        probes.append(probe_pose_extract(args.base_url, image, args.timeout))
        probes.append(probe_pose_match_test(args.base_url, ts, image, args.timeout))
    else:
        probes.append({"id": "server", "ok": False, "checks": [{"check": "server", "status": "skip", "detail": health_detail}]})

    passed = sum(1 for p in probes if p.get("ok"))
    payload = {
        "generated_at": utc_ts(),
        "base_url": args.base_url,
        "server_up": server_up,
        "health_detail": health_detail,
        "fixture_image": "testdata/fr-b41/face_sample.jpg",
        "yolo_weights": yolo_pose_weights(),
        "probes": probes,
        "summary": {"pass": passed, "total": len(probes)},
        "disclaimer": DISCLAIMER,
    }
    write_artifacts(payload)

    for row in probes:
        flag = "OK" if row.get("ok") else "FAIL"
        print(f"  {row.get('id')}: {flag}")
    print(f"\nfr-b44-pose: {passed}/{len(probes)} pass")
    return 0 if passed == len(probes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
