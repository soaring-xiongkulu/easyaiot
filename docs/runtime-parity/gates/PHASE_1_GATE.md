# PHASE_1_GATE (partial)

- **Date:** 2026-08-09
- **Orchestrator:** Cursor Grok (main session)
- **Phase:** 1 — Windows RUNTIME 可编译可跑
- **Verdict:** PARTIAL — G-1.1/G-1.2 PASS；G-1.3～G-1.4 未过

## Checklist

| ID | Item | Evidence | OK |
|----|------|----------|----|
| G-1.1 | MSVC x64 Release 产出 `RUNTIME.exe` | `f4bfc0a`；`RUNTIME/build-win/Release/RUNTIME.exe`；见 `PHASE_1_BUILD_NOTES.md` | **PASS** |
| G-1.2 | 可加载 ORT（CPU）并见 `infer_ep` | `deploy.env.ps1` + smoke ini；日志 `infer_ep=cpu`（见下）；commit `c966747` | **PASS** |
| G-1.3 | candidate VIDEO 拉起 cpp 任务 | 进行中 | PENDING |
| G-1.4 | `win_cpp` 双侧采样 heartbeat + detect | 未开始 | PENDING |

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
- Phase 1 整体不过门，直至 G-1.3/G-1.4。

## Next

1. G-1.3：VIDEO 拉起 cpp daemon（用 `deploy.env.ps1`）
2. G-1.4：gate 采样报告
