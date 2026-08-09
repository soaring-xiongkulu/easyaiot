# PHASE_1_GATE (partial)

- **Date:** 2026-08-09
- **Orchestrator:** Cursor Grok (main session)
- **Phase:** 1 — Windows RUNTIME 可编译可跑
- **Verdict:** PARTIAL — G-1.1～G-1.4 PASS；Phase 1 整体仍待编排审查后宣告过门

## Checklist

| ID | Item | Evidence | OK |
|----|------|----------|----|
| G-1.1 | MSVC x64 Release 产出 `RUNTIME.exe` | `f4bfc0a`；`RUNTIME/build-win/Release/RUNTIME.exe`；见 `PHASE_1_BUILD_NOTES.md` | **PASS** |
| G-1.2 | 可加载 ORT（CPU）并见 `infer_ep` | `deploy.env.ps1` + smoke ini；日志 `infer_ep=cpu`；commit `c966747` | **PASS** |
| G-1.3 | candidate VIDEO 拉起 cpp 任务 | `g13_video_cpp_launch.py` + `AlgorithmTaskDaemon`；daemon 日志 `executor=cpp` + `infer_ep=cpu`（见下） | **PASS** |
| G-1.4 | `win_cpp` 双侧采样 heartbeat + detect | `runtime_parity_gate.py run --executor cpp` ×2；`logs/runtime_parity_report.json` + golden/cpp 产物 | **PASS** |

## Orchestrator acceptance (G-1.1)

- 验收 [Finish MSVC RUNTIME](204cc5c6-6fb0-4747-a749-2b3446709d53)：commit `f4bfc0a`。
- **G-1.1：PASS**。

## G-1.2 smoke evidence

```text
. .\RUNTIME\scripts\deploy.env.ps1
.\RUNTIME\build-win\Release\RUNTIME.exe <g12_smoke.ini>
# stderr:
[YOLO] Using CPU execution
[YOLO] Model loaded successfully infer_ep=cpu
[OK] YOLO thread pool initialized infer_ep=cpu
```

模板：`testdata/runtime-parity/config/g12_smoke.ini.example`（本地 ini 已 gitignore）。

依赖要点：`opencv_dnn` 需要 **libprotobuf 3.21.x**（不可用 base conda 的 3.20）；`deploy.env.ps1` 将 `vendor/win-x64/conda-pkgs/libprotobuf/Library/bin` 置于 PATH 前部。

## Orchestrator acceptance (G-1.2)

- **G-1.2：PASS**（2026-08-09 编排亲自复跑）。

## G-1.3 VIDEO cpp launch evidence

**路径（与 `algorithm_task_launcher_service.start_task_services` 同构）：**

1. `generate_runtime_ini(task, log_path)` → `RUNTIME/config/task_<id>.ini`
2. `AlgorithmTaskDaemon(executor=cpp, runtime_bin, runtime_ini)` → `Popen([RUNTIME.exe, ini])`

**复现：**

```powershell
. .\RUNTIME\scripts\g13_video_cpp_smoke.ps1
# 或
. .\RUNTIME\scripts\deploy.env.ps1
python tools\runtime_parity\g13_video_cpp_launch.py
```

**Daemon 日志摘录**（`logs/g13_task_91301/2026-08-09.log`）：

```text
# executor: cpp
# 命令: ...\RUNTIME\build-win\Release\RUNTIME.exe ...\RUNTIME\config\task_91301.ini
[YOLO] Model loaded successfully infer_ep=cpu
[OK] YOLO thread pool initialized infer_ep=cpu
```

配置要点：`prefer_gpu=false` / `force_cpu=true`；模型 `RUNTIME/models/yolov11n.onnx`；媒体 `testdata/runtime-parity/media/people-detection.mp4`。

## G-1.4 win_cpp sampling evidence

```powershell
. .\RUNTIME\scripts\deploy.env.ps1
python tools\runtime_parity_gate.py run --executor cpp --case rt_p0_detect_single_onnx
python tools\runtime_parity_gate.py run --executor cpp --case rt_p0_heartbeat_lifecycle
```

| Case | Artifact path | infer_ep | Layer status |
|------|---------------|----------|--------------|
| `rt_p0_detect_single_onnx` | `testdata/runtime-parity/golden/cpp/rt_p0_detect_single_onnx/lifecycle.json` | cpu | L_lifecycle=sampled, L_detect=sampled_partial |
| `rt_p0_heartbeat_lifecycle` | `testdata/runtime-parity/golden/cpp/rt_p0_heartbeat_lifecycle/lifecycle.json` | cpu | L_lifecycle=sampled |

报告：`logs/runtime_parity_report.json`（`ok=false` 预期；certify 全绿非 Phase 1 要求）。

## Known issues (non-blocking Phase 1)

- Windows 上 `AlgorithmTaskDaemon.stop()` 调用 `os.getpgid` 报错（无进程组）；不影响拉起证据。
- `generate_runtime_ini` 无 Flask 上下文时 regions 查询 warning（regions 为空可接受）。

## Next

Phase 2：契约与静默丢失清零（G-2.x）。
