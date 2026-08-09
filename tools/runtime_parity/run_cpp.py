"""run --executor cpp — candidate RUNTIME sampling."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .artifacts import _write_json, layer_file_map, write_skeleton_golden
from .manifest import find_case, load_manifest
from .paths import candidate_root, golden_dir, runtime_exe_candidates, testdata_root
from .report import add_case_result, new_report, write_report

_SAMPLE_SEC = 20


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
    case_id: str,
    media: Path,
    control_port: int,
) -> Path:
    ini_dir = root / "logs" / "cpp_sample"
    ini_dir.mkdir(parents=True, exist_ok=True)
    ini_path = ini_dir / f"{case_id}.ini"
    rel_media = media
    try:
        rel_media = media.relative_to(root)
    except ValueError:
        pass
    model = root / "RUNTIME" / "models" / "yolov11n.onnx"
    names = root / "RUNTIME" / "models" / "coco.names"
    content = f"""# Auto-generated for runtime_parity_gate run --executor cpp
[video]
rtsp_url={rel_media.as_posix()}
rtmp_url=
width=768
height=432
fps=25

[ai]
enable=true
model_path={model.relative_to(root).as_posix() if model.is_file() else model}
classes_path={names.relative_to(root).as_posix() if names.is_file() else names}
threads=1
prefer_gpu=false
force_cpu=true
gpu_device_id=0

[alarm]
enable=false
hook_url=http://127.0.0.1:18082/alert
confidence_threshold=0.5
cooldown_time=30

[task]
id={case_id}
control_port={control_port}

[video_task]
device_id=cpp_sample
device_name={case_id}
task_type=realtime
algorithm_name=detection
alert_hook_url=
heartbeat_url=
heartbeat_interval_sec=30
log_path=logs/cpp_sample/{case_id}
headless=true

[features]
enable_rtmp=false
enable_draw=false
enable_alarm=false
"""
    ini_path.write_text(content, encoding="utf-8")
    return ini_path


def _run_runtime_sample(runtime: Path, ini: Path, timeout: float) -> Dict[str, Any]:
    """Spawn RUNTIME briefly; capture stdout for infer_ep and boot status."""
    started = time.time()
    proc = subprocess.Popen(
        [str(runtime), str(ini)],
        cwd=str(candidate_root()),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=os.environ.copy(),
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


def _write_sampled_layers(
    out_dir: Path,
    case,
    boot: Dict[str, Any],
) -> List[Dict[str, Any]]:
    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    layers_out: List[Dict[str, Any]] = []
    infer_ep = boot.get("infer_ep")
    boot_ok = boot.get("started") and infer_ep

    for layer, fname in layer_file_map(case).items():
        artifact = out_dir / fname
        if layer == "L_lifecycle":
            data: Dict[str, Any] = {
                "case_id": case.id,
                "layer": layer,
                "executor": "cpp",
                "task_type": case.task_type,
                "sampled_at": ts,
                "source": "runtime_parity_gate_cpp_sample",
                "status": "sampled" if boot_ok else "fail",
                "boot": {
                    "started": bool(boot.get("started")),
                    "exit_code": boot.get("exit_code"),
                    "infer_ep": infer_ep,
                    "duration_sec": boot.get("duration_sec"),
                },
                "heartbeats": [],
                "heartbeat_count": 0,
                "fields_expected": ["task_id", "process_id", "log_path"],
            }
            if not boot_ok:
                data["reason"] = boot.get("error") or "infer_ep not observed in RUNTIME stdout"
        elif layer == "L_detect":
            data = {
                "case_id": case.id,
                "layer": layer,
                "executor": "cpp",
                "task_type": case.task_type,
                "sampled_at": ts,
                "source": "runtime_parity_gate_cpp_sample",
                "status": "sampled_partial" if boot_ok else "fail",
                "frames": [],
                "detection_count": 0,
                "model": "onnx",
                "infer_ep": infer_ep,
                "_note": "Phase 1: boot/infer only; bbox certify deferred to Phase 4",
            }
            if not boot_ok:
                data["reason"] = "RUNTIME did not reach infer_ep"
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
            port = 18200 + (hash(case_id) % 200)
            ini = _build_ini(root, case_id, media, port)
            print(f"INFO sampling RUNTIME with {ini} ({_SAMPLE_SEC}s)")
            boot = _run_runtime_sample(runtime, ini, _SAMPLE_SEC)
            print(f"INFO boot infer_ep={boot.get('infer_ep')} exit={boot.get('exit_code')}")
            layers = _write_sampled_layers(out_dir, case, boot)

    report = new_report(command="run", case_id=case_id)
    add_case_result(report, case_id, layers, executor="cpp")
    report["ok"] = False
    report["runtime_binary"] = str(runtime) if runtime else None
    out = write_report(report, root)
    print(f"run-cpp: case={case_id} artifacts under {out_dir}")
    print(f"report: {out}")
    return exit_code
