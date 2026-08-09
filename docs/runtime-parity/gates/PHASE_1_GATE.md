# PHASE_1_GATE

- **Date:** 2026-08-09
- **Orchestrator:** Cursor Grok (main session)
- **Phase:** 1 — Windows RUNTIME 可编译可跑
- **Verdict:** **PASS**

## Checklist

| ID | Item | Evidence | OK |
|----|------|----------|----|
| G-1.1 | MSVC x64 Release 产出 `RUNTIME.exe` | `f4bfc0a`；`RUNTIME/build-win/Release/RUNTIME.exe` | **PASS** |
| G-1.2 | ORT CPU `infer_ep` | `deploy.env.ps1`；日志 `infer_ep=cpu`；`c966747` | **PASS** |
| G-1.3 | VIDEO 拉起 cpp 任务 | `g13_video_cpp_launch.py` exit 0；daemon 日志 `executor=cpp` + `infer_ep=cpu` | **PASS** |
| G-1.4 | win_cpp 双侧采样 | `run --executor cpp` 对 heartbeat + detect（及 alert）写出 `golden/cpp` 且 `infer_ep=cpu` | **PASS** |

## G-1.3 证据

```text
. .\RUNTIME\scripts\g13_video_cpp_smoke.ps1
# or:
. .\RUNTIME\scripts\deploy.env.ps1
python tools/runtime_parity/g13_video_cpp_launch.py --task-id 91301 --wait-sec 40
# → G-1.3 PASS: VIDEO daemon launched cpp RUNTIME; infer_ep observed
```

Windows 解析：`runtime_config_service.resolve_runtime_bin` 含 `build-win/Release/RUNTIME.exe`；daemon 通过 `runtime_library_path_env()` 写入 PATH。

## G-1.4 证据

```text
python tools/runtime_parity_gate.py run --executor cpp --case rt_p0_heartbeat_lifecycle
python tools/runtime_parity_gate.py run --executor cpp --case rt_p0_detect_single_onnx
# artifacts under testdata/runtime-parity/golden/cpp/<case>/
```

## Orchestrator acceptance

- Phase 1 **PASS**（2026-08-09）。
- 进入 Phase 2：ini/hook 契约清零。
