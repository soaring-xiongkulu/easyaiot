"""Shared helpers for VIDEO Java certify tooling."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

LAYER_FILES = {
    "api": "api.json",
    "lifecycle": "lifecycle.json",
    "alarm": "alarm.json",
    "ini": "ini.json",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def manifest_path() -> Path:
    return repo_root() / "testdata" / "video-java" / "manifest.json"


def thresholds_path() -> Path:
    return repo_root() / "testdata" / "video-java" / "thresholds.json"


def fixtures_path() -> Path:
    return repo_root() / "testdata" / "video-java" / "fixtures" / "vj_p0.json"


def golden_dir(side: str, case_id: str) -> Path:
    return repo_root() / "testdata" / "video-java" / "golden" / side / case_id


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest() -> Dict[str, Any]:
    return load_json(manifest_path())


def load_thresholds() -> Dict[str, Any]:
    return load_json(thresholds_path())


def load_fixture() -> Dict[str, Any]:
    fx = load_json(fixtures_path())
    if not fx.get("task_id"):
        raise RuntimeError(
            "fixture task_id is null — run: python tools/video_java/seed_p0_fixture.py"
        )
    return fx


def find_case(manifest: Dict[str, Any], case_id: str) -> Dict[str, Any]:
    for case in manifest.get("cases", []):
        if case.get("case_id") == case_id:
            return case
    raise KeyError(f"unknown case_id: {case_id}")


def http_json(
    method: str,
    url: str,
    body: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0,
) -> Tuple[int, Dict[str, Any], str]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8", errors="replace")
    try:
        parsed = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        parsed = {"_raw": raw}
    if not isinstance(parsed, dict):
        parsed = {"data": parsed}
    return status, parsed, raw


_PATH_RE = re.compile(r"([A-Za-z]:\\[^\s\"']+|/[^\s\"']+)")


def normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: normalize_value(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [normalize_value(v) for v in value]
    if isinstance(value, str):
        if re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", value):
            return "<TIMESTAMP>"
        if _PATH_RE.fullmatch(value) or "\\" in value or value.startswith("/"):
            return Path(value).name or value
        if re.fullmatch(r"\d+", value) and len(value) > 6:
            return "<NUM>"
        return value
    if isinstance(value, int) and value > 100000:
        return "<NUM>"
    return value


def normalize_api_layer(payload: Dict[str, Any]) -> Dict[str, Any]:
    out = normalize_value(payload)
    if isinstance(out, dict):
        data = out.get("data")
        if isinstance(data, dict):
            for key in (
                "service_last_heartbeat",
                "last_process_time",
                "last_success_time",
                "last_capture_time",
                "created_at",
                "updated_at",
                "last_notify_time",
            ):
                if key in data:
                    data[key] = "<TIMESTAMP>"
            for key in ("service_process_id", "service_port"):
                if key in data and data[key] is not None:
                    data[key] = "<NUM>"
    return out


def write_layer(path: Path, layer: str, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {"layer": layer, "status": "sampled", **payload}
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def phase0_case_ids(manifest: Dict[str, Any]) -> List[str]:
    return [
        c["case_id"]
        for c in manifest.get("cases", [])
        if c.get("priority") == "P0"
    ]


def exemptions_path() -> Path:
    return repo_root() / "docs" / "video-java" / "gates" / "EXEMPTIONS.md"


def load_exemption_ids() -> set[str]:
    path = exemptions_path()
    if not path.is_file():
        return set()
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| EX-"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) > 1 and parts[1].startswith("EX-"):
            ids.add(parts[1])
    return ids


def case_layer_exemption_ids(case: Dict[str, Any], layer: str) -> List[str]:
    ids: List[str] = []
    ids.extend(case.get("exemptions") or [])
    ids.extend((case.get("layer_exemptions") or {}).get(layer) or [])
    return ids


def resolve_exemption(
    case: Dict[str, Any], layer: str, exemption_id: str
) -> Optional[str]:
    known = load_exemption_ids()
    if exemption_id not in known:
        return None
    if exemption_id in case_layer_exemption_ids(case, layer):
        return exemption_id
    return None
