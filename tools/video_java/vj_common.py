"""Shared helpers for VIDEO Java certify tooling."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

LAYER_FILES = {
    "api": "api.json",
    "lifecycle": "lifecycle.json",
    "alarm": "alarm.json",
    "ini": "ini.json",
    "media": "media.json",
    "side_effect": "effects.json",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def manifest_path() -> Path:
    return repo_root() / "testdata" / "video-java" / "manifest.json"


def thresholds_path() -> Path:
    return repo_root() / "testdata" / "video-java" / "thresholds.json"


def fixtures_path() -> Path:
    return repo_root() / "testdata" / "video-java" / "fixtures" / "vj_p0.json"


def runtime_exe_path() -> Path:
    """Release RUNTIME.exe relative to repo root (EVID-S3: real binary, not stub)."""
    return (repo_root() / "RUNTIME" / "build-win" / "Release" / "RUNTIME.exe").resolve()


def is_real_runtime_bin(path: str | Path | None) -> bool:
    if not path:
        return False
    name = Path(str(path)).name.lower()
    if "stub_runtime" in name:
        return False
    return name == "runtime.exe"


def windows_process_image_name(pid: int | None) -> str | None:
    """Best-effort Windows process image name for certify evidence."""
    if pid is None or int(pid) <= 0:
        return None
    try:
        proc = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"(Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue).ProcessName",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        name = (proc.stdout or "").strip()
        return name or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def runtime_executor_fields(
    task_data: Dict[str, Any], service_row: Dict[str, Any]
) -> Dict[str, Optional[str]]:
    """Lifecycle evidence: configured launcher basename + live process image."""
    runtime_bin = task_data.get("runtime_bin_path") or service_row.get("runtime_bin_path")
    executor_bin = Path(str(runtime_bin)).name if runtime_bin else None
    pid = service_row.get("process_id")
    if pid is None:
        pid = task_data.get("service_process_id")
    try:
        pid_int = int(pid) if pid is not None else None
    except (TypeError, ValueError):
        pid_int = None
    process_image = windows_process_image_name(pid_int)
    if process_image and not process_image.lower().endswith(".exe"):
        process_image = f"{process_image}.exe"
    return {"executor_bin": executor_bin, "process_image": process_image}


def p1_fixtures_path() -> Path:
    return repo_root() / "testdata" / "video-java" / "fixtures" / "vj_p1.json"


def p2_fixtures_path() -> Path:
    return repo_root() / "testdata" / "video-java" / "fixtures" / "vj_p2.json"


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


def load_p1_fixture() -> Dict[str, Any]:
    fx = load_json(p1_fixtures_path())
    if not fx.get("stream_forward_task_id"):
        raise RuntimeError(
            "fixture stream_forward_task_id is null — run: python tools/video_java/seed_p1_fixture.py"
        )
    return fx


def load_p2_fixture() -> Dict[str, Any]:
    fx = load_json(p2_fixtures_path())
    if not fx.get("face_task_id"):
        raise RuntimeError(
            "fixture face_task_id is null — run: python tools/video_java/seed_p2_fixture.py"
        )
    return fx


def ensure_p0_alert_fixture(task_id: int, device_id: str) -> None:
    """Test-only: re-enable certify task for alert hook SUCCESS (stop() clears is_enabled)."""
    try:
        import os

        import psycopg2
    except ImportError as exc:
        raise RuntimeError("psycopg2 required for ensure_p0_alert_fixture") from exc
    db_url = os.environ.get(
        "VIDEO_JAVA_DB_URL",
        "postgresql://postgres:iot45722414822@127.0.0.1:15432/iot-video20",
    )
    conn = psycopg2.connect(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO algorithm_task_device (task_id, device_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (task_id, device_id),
                )
                cur.execute(
                    """
                    UPDATE algorithm_task
                    SET is_enabled = true,
                        alert_event_enabled = true
                    WHERE id = %s
                    """,
                    (task_id,),
                )
    finally:
        conn.close()


def update_task_runtime_bin(task_id: int, runtime_bin_path: str) -> None:
    """Test-only: point fixture task at a specific RUNTIME stub/binary."""
    try:
        import os

        import psycopg2
    except ImportError as exc:
        raise RuntimeError("psycopg2 required for runtime_bin_path updates") from exc
    db_url = os.environ.get(
        "VIDEO_JAVA_DB_URL",
        "postgresql://postgres:iot45722414822@127.0.0.1:15432/iot-video20",
    )
    conn = psycopg2.connect(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE algorithm_task SET runtime_bin_path = %s WHERE id = %s",
                    (runtime_bin_path, task_id),
                )
    finally:
        conn.close()


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
        # Java candidate adds duplicate msg alias and nullable total on non-list responses.
        out.pop("message", None)
        if out.get("total") is None:
            out.pop("total", None)
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
                "last_heartbeat",
                "start_time",
            ):
                if key in data:
                    data[key] = "<TIMESTAMP>"
            for key in ("service_process_id", "service_port", "process_id", "pid"):
                if key in data and data[key] is not None:
                    data[key] = "<NUM>"
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    for key in ("updated_at", "created_at", "last_heartbeat"):
                        if key in item:
                            item[key] = "<TIMESTAMP>"
    return out


def normalize_media_layer(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize media/stream snapshot for machine-checkable diff."""
    snap = payload.get("snapshot") if isinstance(payload.get("snapshot"), dict) else payload
    if not isinstance(snap, dict):
        return normalize_value(payload)
    out = dict(snap)
    for key in ("pid", "process_id", "service_process_id", "start_time", "last_heartbeat"):
        if key in out and out[key] is not None:
            out[key] = "<NUM>"
    for key in ("log_path", "service_log_path", "rtmp_url", "http_stream"):
        if key in out and isinstance(out[key], str) and out[key]:
            out[key] = Path(out[key]).name or "<PATH>"
    return normalize_value(out)


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


def phase1_case_ids(manifest: Dict[str, Any]) -> List[str]:
    return [
        c["case_id"]
        for c in manifest.get("cases", [])
        if c.get("priority") == "P1"
    ]


def phase2_case_ids(manifest: Dict[str, Any]) -> List[str]:
    return [
        c["case_id"]
        for c in manifest.get("cases", [])
        if c.get("priority") == "P2"
    ]


def exemptions_path() -> Path:
    return repo_root() / "docs" / "video-java" / "gates" / "EXEMPTIONS.md"


def _parse_exemption_rows() -> List[Tuple[str, str]]:
    """Return (exemption_id, owner_sign_off) for each EX-* table row."""
    path = exemptions_path()
    if not path.is_file():
        return []
    rows: List[Tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| EX-"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) > 4 and parts[1].startswith("EX-"):
            rows.append((parts[1], parts[4]))
    return rows


def load_exemption_ids() -> set[str]:
    return {ex_id for ex_id, _ in _parse_exemption_rows()}


def load_signed_exemption_ids() -> set[str]:
    return {
        ex_id
        for ex_id, sign_off in _parse_exemption_rows()
        if sign_off and sign_off.lower() != "pending"
    }


def layer_satisfies(layer: Dict[str, Any]) -> bool:
    """Layer counts toward case ok when status is pass or signed exempt."""
    status = layer.get("status")
    if status == "pass":
        return True
    if status == "exempt":
        ex_id = layer.get("exemption_id")
        return bool(ex_id and ex_id in load_signed_exemption_ids())
    return False


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


_P1_SRC_FEEDER_PROC: Optional[subprocess.Popen] = None


def resolve_ffmpeg_binary() -> str:
    explicit = (os.environ.get("FFMPEG_PATH") or "").strip().strip('"')
    if explicit and Path(explicit).is_file():
        return explicit
    local_yaml = repo_root() / "DEVICE" / "iot-video" / "iot-video-biz" / "src" / "main" / "resources" / "application-local.yaml"
    if local_yaml.is_file():
        for line in local_yaml.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("ffmpeg-path:"):
                candidate = stripped.split(":", 1)[1].strip()
                if candidate and Path(candidate).is_file():
                    return candidate
    return "ffmpeg"


def _flv_source_ready(url: str, timeout: float = 3.0) -> bool:
    try:
        req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 206)
    except urllib.error.HTTPError as exc:
        return exc.code in (200, 206)
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def ensure_p1_src_feeder() -> None:
    """Start loop publisher to SRS HTTP-FLV source if not already reachable."""
    global _P1_SRC_FEEDER_PROC
    fixture = load_json(p1_fixtures_path())
    flv_url = fixture.get("source") or "http://127.0.0.1:8080/live/vj_p1_src.flv"
    if _flv_source_ready(flv_url):
        return
    if _P1_SRC_FEEDER_PROC is not None and _P1_SRC_FEEDER_PROC.poll() is None:
        for _ in range(20):
            if _flv_source_ready(flv_url):
                return
            time.sleep(0.5)
    sample = Path("F:/acme/RUNTIME/testdata/sample.mp4")
    if not sample.is_file():
        raise RuntimeError(f"P1 HTTP-FLV source down and sample missing: {sample}")
    ffmpeg = resolve_ffmpeg_binary()
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-re",
        "-stream_loop",
        "-1",
        "-i",
        str(sample),
        "-c",
        "copy",
        "-f",
        "flv",
        "rtmp://127.0.0.1/live/vj_p1_src",
    ]
    _P1_SRC_FEEDER_PROC = subprocess.Popen(cmd)
    for _ in range(40):
        if _flv_source_ready(flv_url):
            return
        time.sleep(0.5)
    raise RuntimeError(f"P1 HTTP-FLV source not ready after feeder start: {flv_url}")


def prepare_p1_view_forward(case: Dict[str, Any], fixture: Dict[str, Any]) -> None:
    """Stop view-forward on oracle + candidate so SRS RTMP publish slot is free."""
    device_id = fixture["device_id"]
    for key in ("oracle_base_url", "candidate_base_url"):
        base = (case.get(key) or "").rstrip("/")
        if not base:
            continue
        try:
            http_json("POST", f"{base}/video/camera/device/{device_id}/stream/stop", timeout=10.0)
        except (urllib.error.URLError, OSError, TimeoutError):
            pass
    time.sleep(6.0)


def wait_until_view_forward_running(
    base: str,
    device_id: str,
    *,
    timeout: float = 30.0,
    poll: float = 0.5,
) -> Dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: Dict[str, Any] = {}
    url = f"{base.rstrip('/')}/video/camera/device/{device_id}/stream/status"
    while time.monotonic() < deadline:
        try:
            _, body, _ = http_json("GET", url, timeout=10.0)
        except (urllib.error.URLError, OSError, TimeoutError):
            time.sleep(poll)
            continue
        data = body.get("data") if isinstance(body.get("data"), dict) else {}
        last = data
        if (data.get("status") or "stopped") == "running":
            return data
        time.sleep(poll)
    return last
