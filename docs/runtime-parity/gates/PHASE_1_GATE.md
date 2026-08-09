# PHASE_1_GATE (partial)

- **Date:** 2026-08-09
- **Orchestrator:** Cursor Grok (main session)
- **Phase:** 1 — Windows RUNTIME 可编译可跑
- **Verdict:** PARTIAL — G-1.1 PASS；G-1.2～G-1.4 未过

## Checklist

| ID | Item | Evidence | OK |
|----|------|----------|----|
| G-1.1 | MSVC x64 Release 产出 `RUNTIME.exe` | `f4bfc0a`；`RUNTIME/build-win/Release/RUNTIME.exe`（530944 B）；`cmake --build … --config Release` exit 0；见 `PHASE_1_BUILD_NOTES.md` | **PASS** |
| G-1.2 | 可加载 ORT（CPU）并见 `infer_ep` | 待 PATH + `config.ini` + `RUNTIME/models/yolov11n.onnx` 冒烟 | PENDING |
| G-1.3 | candidate VIDEO 拉起 cpp 任务 | 未开始 | PENDING |
| G-1.4 | `win_cpp` 双侧采样 heartbeat + detect | 未开始 | PENDING |

## Orchestrator acceptance (G-1.1)

- 验收 [Finish MSVC RUNTIME](204cc5c6-6fb0-4747-a749-2b3446709d53)：commit `f4bfc0a`。
- **G-1.1：PASS**。Phase 1 整体不过门，直至 G-1.2+。
- 本机产物不入库（`build-win/` gitignore）；复现步骤以 `PHASE_1_BUILD_NOTES.md` 为准。

## Next

1. G-1.2：`deploy.env.ps1`（或等价 PATH）+ 最小 ini + `force_cpu=1` → 日志 `[YOLO] … infer_ep=cpu`
2. G-1.3：VIDEO 拉起 cpp daemon
3. G-1.4：gate 采样报告
