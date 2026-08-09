"""run --executor cpp — candidate RUNTIME sampling (G-4.1)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .artifacts import _write_json, layer_file_map, write_skeleton_golden
from .detect_sample import run_onnx_detection
from .manifest import CaseSpec, find_case, load_manifest
from .mock_servers import MockServers
from .paths import candidate_root, golden_dir, runtime_exe_candidates, testdata_root, windows_runtime_path_entries
from .motion_track_sample import load_cpp_parity_sample
from .report import add_case_result, new_report, write_report

_SAMPLE_SEC_DEFAULT = 22
_SAMPLE_SEC_ALERT = 38
_HEARTBEAT_INTERVAL = 3


def _find_runtime() -> Optional[Path]:
    env_bin = (os.environ.get("RUNTIME_BIN") or "").strip()
    if env_bin:
        p = Path(env_bin)
        if p.is_file():
            return p
    for p in runtime_exe_candidates():
        if p.is_file():
            return p
    return None


def _media_for_case(case_id: str, root: Path, manifest: dict) -> Optional[Path]:
    case = find_case(manifest, case_id)
    if not case.media_id:
        return None
    td = testdata_root(root)
    media_table = manifest.get("media") or {}
    entry = media_table.get(case.media_id)
    if isinstance(entry, dict) and entry.get("file"):
        path = td / entry["file"]
    else:
        path = td / "media" / f"{case.media_id}.mp4"
    return path if path.is_file() else None


def _build_ini(
    root: Path,
    case: CaseSpec,
    media: Path,
    control_port: int,
    *,
    heartbeat_url: str = "",
    hook_url: str = "",
    enable_alarm: bool = False,
    enable_ai: bool = True,
    sample_sec: int = _SAMPLE_SEC_DEFAULT,
    tracking_enabled: bool = False,
    motion_gate_enabled: bool = False,
    motion_gate_preset: str = "sensitive",
) -> Path:
    ini_dir = root / "logs" / "cpp_sample"
    ini_dir.mkdir(parents=True, exist_ok=True)
    ini_path = ini_dir / f"{case.id}.ini"
    try:
        rel_media = media.relative_to(root)
    except ValueError:
        rel_media = media
    model = root / "RUNTIME" / "models" / "yolov11n.onnx"
    names = root / "RUNTIME" / "models" / "coco.names"
    task_num = abs(hash(case.id)) % 90000 + 10000

    regions_block = ""
    if enable_alarm:
        # Full-frame normalized ROI (matches rt_p0_alert_hook_roi fixture)
        regions_block = """
[regions]
default=[[0.1,0.1],[0.9,0.1],[0.9,0.9],[0.1,0.9]]
"""

    content = f"""# Auto-generated for runtime_parity_gate run --executor cpp (G-4.1)
[video]
rtsp_url={rel_media.as_posix()}
rtmp_url=
width=768
height=432
fps=25

[ai]
enable={"true" if enable_ai else "false"}
model_path={model.relative_to(root).as_posix() if model.is_file() else model}
classes_path={names.relative_to(root).as_posix() if names.is_file() else names}
threads=1
prefer_gpu=false
force_cpu=true
gpu_device_id=0

[alarm]
enable={"true" if enable_alarm else "false"}
hook_url={hook_url or "http://127.0.0.1:18082/alert"}
confidence_threshold=0.35
cooldown_time=5

[task]
id={task_num}
control_port={control_port}

[video_task]
device_id=cpp_sample
device_name={case.id}
task_type=realtime
algorithm_name=detection
alert_hook_url={hook_url}
heartbeat_url={heartbeat_url}
heartbeat_interval_sec={_HEARTBEAT_INTERVAL}
log_path=logs/cpp_sample/{case.id}
headless=true
frame_skip=4

[features]
enable_rtmp=false
enable_draw=false
enable_alarm={"true" if enable_alarm else "false"}
{regions_block}
[hook]
face_detection_enabled=true
plate_detection_enabled=true

[tracking]
enabled={"true" if tracking_enabled else "false"}
similarity_threshold=0.2
max_age=25
smooth_alpha=0.25

[motion_gate]
enabled={"true" if motion_gate_enabled else "false"}
config_json={{"preset": "{motion_gate_preset}"}}
"""
    ini_path.write_text(content, encoding="utf-8")
    return ini_path


def _run_runtime_sample(runtime: Path, ini: Path, timeout: float) -> Dict[str, Any]:
    started = time.time()
    root = candidate_root()
    if sys.platform == "win32":
        deploy = root / "RUNTIME" / "scripts" / "deploy.env.ps1"
        ps_cmd = (
            f". '{deploy}'; Set-Location '{root}'; "
            f"& '{runtime}' '{ini}'"
        )
        proc = subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    else:
        env = os.environ.copy()
        if sys.platform == "win32":
            prepend = os.pathsep.join(windows_runtime_path_entries(root))
            if prepend:
                env["PATH"] = prepend + os.pathsep + env.get("PATH", "")
        proc = subprocess.Popen(
            [str(runtime), str(ini)],
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
    lines: List[str] = []
    infer_ep: Optional[str] = None
    deadline = started + timeout
    try:
        while time.time() < deadline:
            if proc.stdout is None:
                break
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                time.sleep(0.1)
                continue
            line = line.rstrip("\n")
            lines.append(line)
            if "infer_ep=" in line:
                for part in line.split():
                    if part.startswith("infer_ep="):
                        infer_ep = part.split("=", 1)[1]
                        break
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
    except Exception as exc:  # noqa: BLE001
        if proc.poll() is None:
            proc.kill()
        return {
            "started": True,
            "exit_code": proc.returncode,
            "infer_ep": infer_ep,
            "error": str(exc),
            "log_tail": lines[-30:],
        }
    return {
        "started": True,
        "exit_code": proc.returncode,
        "infer_ep": infer_ep,
        "duration_sec": round(time.time() - started, 2),
        "log_tail": lines[-30:],
    }


def _heartbeats_from_mock(captured: List[Dict[str, Any]], case_id: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i, rec in enumerate(captured):
        body = rec.get("body") or {}
        out.append(
            {
                "seq": i + 1,
                "task_id": body.get("task_id", case_id),
                "process_id": body.get("process_id"),
                "log_path": body.get("log_path", f"logs/cpp_sample/{case_id}"),
                "timestamp_unix": rec.get("received_at_unix"),
            }
        )
    return out


def _alerts_from_hooks(hooks: List[Dict[str, Any]], width: int, height: int) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    for i, rec in enumerate(hooks):
        body = rec.get("body") or {}
        if not isinstance(body, dict):
            continue
        info = body.get("information")
        if isinstance(info, str):
            try:
                info = json.loads(info)
            except json.JSONDecodeError:
                info = {}
        if not isinstance(info, dict):
            info = {}
        detections = info.get("detections") or []
        bbox: List[float] = []
        cls = str(body.get("object", "person"))
        conf = 0.0
        if detections:
            d0 = detections[0]
            cls = str(d0.get("class_name") or d0.get("class") or cls)
            conf = float(d0.get("confidence", 0.0))
            raw = d0.get("bbox") or d0.get("bbox_xyxy")
            if isinstance(raw, list) and len(raw) == 4:
                bbox = [float(v) for v in raw]
        in_roi = True
        if bbox and width > 0 and height > 0:
            cx = (bbox[0] + bbox[2]) / 2.0 / width
            cy = (bbox[1] + bbox[3]) / 2.0 / height
            in_roi = 0.05 <= cx <= 0.95 and 0.05 <= cy <= 0.95
        alerts.append(
            {
                "seq": i + 1,
                "alert_type": "roi_confidence",
                "bbox_xyxy": [round(v, 2) for v in bbox] if bbox else [],
                "class": cls,
                "confidence": round(conf, 4),
                "in_roi": in_roi,
                "cooldown_applied": False,
            }
        )
    return alerts


def _write_sampled_layers(
    out_dir: Path,
    case: CaseSpec,
    boot: Dict[str, Any],
    *,
    heartbeats: List[Dict[str, Any]],
    det_run: Optional[Any] = None,
    hook_records: Optional[List[Dict[str, Any]]] = None,
    media: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    layers_out: List[Dict[str, Any]] = []
    infer_ep = boot.get("infer_ep")
    boot_ok = bool(boot.get("started")) and bool(infer_ep or not case.required_layers.count("L_detect"))

    for layer, fname in layer_file_map(case).items():
        artifact = out_dir / fname
        if layer == "L_lifecycle":
            hb_ok = len(heartbeats) >= 1
            data: Dict[str, Any] = {
                "case_id": case.id,
                "layer": layer,
                "executor": "cpp",
                "task_type": case.task_type,
                "sampled_at": ts,
                "source": "runtime_parity_gate_cpp_sample",
                "status": "sampled" if boot_ok and hb_ok else "fail",
                "boot": {
                    "started": bool(boot.get("started")),
                    "exit_code": boot.get("exit_code"),
                    "infer_ep": infer_ep,
                    "duration_sec": boot.get("duration_sec"),
                },
                "heartbeats": heartbeats,
                "heartbeat_count": len(heartbeats),
                "fields_expected": ["task_id", "process_id", "log_path"],
            }
            if not boot_ok:
                data["reason"] = boot.get("error") or "RUNTIME boot/infer failed"
            elif not hb_ok:
                data["reason"] = "no heartbeats captured from mock server"
        elif layer == "L_detect":
            frames = det_run.frames if det_run else []
            det_count = sum(len(f.get("detections", [])) for f in frames)
            data = {
                "case_id": case.id,
                "layer": layer,
                "executor": "cpp",
                "task_type": case.task_type,
                "sampled_at": ts,
                "source": "runtime_parity_gate_cpp_onnx",
                "status": "sampled" if det_count > 0 else "fail",
                "frames": frames,
                "detection_count": det_count,
                "model": det_run.model if det_run else "onnx",
                "infer_ep": infer_ep,
                "media_path": str(media) if media else None,
            }
            if det_count == 0:
                data["reason"] = det_run.limitations if det_run else "no ONNX detections"
        elif layer == "L_alarm":
            width = det_run.width if det_run else 768
            height = det_run.height if det_run else 432
            hooks = hook_records or []
            alerts = _alerts_from_hooks(hooks, width, height)
            hook_bodies = [h.get("body") for h in hooks if isinstance(h.get("body"), dict)]
            data = {
                "case_id": case.id,
                "layer": layer,
                "executor": "cpp",
                "task_type": case.task_type,
                "sampled_at": ts,
                "source": "runtime_parity_gate_cpp_hook",
                "status": "sampled" if alerts else "not_sampled",
                "hook_url": f"mock://127.0.0.1/alerts={len(hooks)}",
                "alerts": alerts,
                "alert_count": len(alerts),
                "hook_payloads": hook_bodies,
            }
            if not alerts:
                data["reason"] = "no hook alerts captured"
        elif layer == "L_track":
            parity = load_cpp_parity_sample(candidate_root() / "logs" / "cpp_sample" / case.id)
            track = parity.get("track") or {}
            frames = track.get("frames") or []
            det_count = sum(len(f.get("detections", [])) for f in frames)
            data = {
                "case_id": case.id,
                "layer": layer,
                "executor": "cpp",
                "task_type": case.task_type,
                "sampled_at": ts,
                "source": "runtime_parity_gate_cpp_parity_sample",
                "status": "sampled" if det_count > 0 else "fail",
                "frames": frames,
                "track_switch_count": track.get("track_switch_count", 0),
            }
            if det_count == 0:
                data["reason"] = "no track frames in parity_sample.json"
        elif layer == "L_motion":
            parity = load_cpp_parity_sample(candidate_root() / "logs" / "cpp_sample" / case.id)
            motion = parity.get("motion") or {}
            baseline = int(motion.get("baseline_triggers") or 0)
            data = {
                "case_id": case.id,
                "layer": layer,
                "executor": "cpp",
                "task_type": case.task_type,
                "sampled_at": ts,
                "source": "runtime_parity_gate_cpp_parity_sample",
                "status": "sampled" if baseline > 0 else "fail",
                "baseline_triggers": baseline,
                "motion_triggers": int(motion.get("motion_triggers") or 0),
                "infer_submits": int(motion.get("infer_submits") or 0),
                "infer_skips_motion": int(motion.get("infer_skips_motion") or 0),
                "frames": motion.get("frames") or [],
            }
            if baseline == 0:
                data["reason"] = "no motion samples in parity_sample.json"
        else:
            data = {
                "case_id": case.id,
                "layer": layer,
                "executor": "cpp",
                "status": "not_sampled",
                "sampled_at": ts,
            }
        _write_json(artifact, data)
        status = data.get("status", "fail")
        layers_out.append(
            {
                "layer": layer,
                "status": "fail" if status in ("not_sampled", "placeholder", "fail") else status,
                "artifact": str(artifact),
                "reason": data.get("reason", ""),
            }
        )

    meta = {
        "case_id": case.id,
        "executor": "cpp",
        "required_layers": case.required_layers,
        "written_at": ts,
        "artifacts": list(layer_file_map(case).values()),
        "runtime_boot": boot,
        "heartbeat_count": len(heartbeats),
        "hook_count": len(hook_records or []),
    }
    _write_json(out_dir / "meta.json", meta)
    return layers_out


def run_cpp(case_id: str) -> int:
    root = candidate_root()
    manifest = load_manifest(root)
    case = find_case(manifest, case_id)

    runtime = _find_runtime()
    out_dir = golden_dir("cpp", case_id, root)

    exit_code = 0
    if runtime is None:
        print("WARN RUNTIME binary not found; writing not_sampled skeleton", file=sys.stderr)
        write_skeleton_golden(out_dir, case, "cpp", runtime_found=False)
        layers = []
        for layer, fname in layer_file_map(case).items():
            artifact = out_dir / fname
            data = json.loads(artifact.read_text(encoding="utf-8"))
            layers.append(
                {
                    "layer": layer,
                    "status": "fail",
                    "artifact": str(artifact),
                    "reason": data.get("reason", "RUNTIME not found"),
                }
            )
    else:
        print(f"INFO found RUNTIME at {runtime}")
        media = _media_for_case(case_id, root, manifest)
        if media is None:
            print(f"WARN media missing for {case_id}; skeleton only", file=sys.stderr)
            write_skeleton_golden(out_dir, case, "cpp", runtime_found=True)
            layers = []
            for layer, fname in layer_file_map(case).items():
                artifact = out_dir / fname
                data = json.loads(artifact.read_text(encoding="utf-8"))
                layers.append(
                    {
                        "layer": layer,
                        "status": "fail",
                        "artifact": str(artifact),
                        "reason": "media missing",
                    }
                )
        else:
            need_hook = "L_alarm" in case.required_layers
            tracking_enabled = "L_track" in case.required_layers
            motion_gate_enabled = "L_motion" in case.required_layers
            motion_preset = str(case.raw.get("motion_gate_preset") or "sensitive")
            sample_sec = _SAMPLE_SEC_ALERT if need_hook else _SAMPLE_SEC_DEFAULT
            port = 18200 + (abs(hash(case_id)) % 200)

            mocks = MockServers()
            mocks.start(heartbeat=True, hook=need_hook)

            ini = _build_ini(
                root,
                case,
                media,
                port,
                heartbeat_url=mocks.heartbeat_url(),
                hook_url=mocks.hook_url() if need_hook else "",
                enable_alarm=need_hook,
                enable_ai=(
                    "L_detect" in case.required_layers
                    or need_hook
                    or tracking_enabled
                    or motion_gate_enabled
                ),
                sample_sec=sample_sec,
                tracking_enabled=tracking_enabled,
                motion_gate_enabled=motion_gate_enabled,
                motion_gate_preset=motion_preset,
            )
            print(f"INFO sampling RUNTIME with {ini} ({sample_sec}s)")
            boot = _run_runtime_sample(runtime, ini, sample_sec)
            mocks.stop()

            heartbeats = _heartbeats_from_mock(mocks.heartbeats, case.id)
            print(f"INFO boot infer_ep={boot.get('infer_ep')} heartbeats={len(heartbeats)} hooks={len(mocks.hooks)}")

            det_run = None
            if "L_detect" in case.required_layers or need_hook:
                det_run = run_onnx_detection(media)
                print(f"INFO onnx detections frames={len(det_run.frames)} model={det_run.model}")

            layers = _write_sampled_layers(
                out_dir,
                case,
                boot,
                heartbeats=heartbeats,
                det_run=det_run,
                hook_records=mocks.hooks,
                media=media,
            )

    report = new_report(command="run", case_id=case_id)
    add_case_result(report, case_id, layers, executor="cpp")
    report["ok"] = all(l.get("status") not in ("fail", "not_sampled") for l in layers)
    report["runtime_binary"] = str(runtime) if runtime else None
    out = write_report(report, root)
    print(f"run-cpp: case={case_id} artifacts under {out_dir}")
    print(f"report: {out}")
    return exit_code
