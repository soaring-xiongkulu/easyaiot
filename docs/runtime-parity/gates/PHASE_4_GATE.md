# PHASE_4_GATE

- **Date:** 2026-08-09
- **Orchestrator:** Cursor Composer (subagent G-4.1 wave)
- **Phase:** 4 — C++ 帧内按红清单补齐
- **Verdict:** **G-4.1 PASS** / G-4.2～G-4.4 **PENDING**

## Checklist

| ID | Item | Evidence | OK |
|----|------|----------|----|
| G-4.1 | P0 detect/alarm/lifecycle certify 绿 | `certify --profile win_cpp` exit 0；`logs/runtime_parity_report.json` ok=true | **PASS** |
| G-4.2 | P1 motion_gate + tracking | 未在本波实现 | **PENDING** |
| G-4.3 | snap/patrol P0 schedule | 未在本波实现 | **PENDING** |
| G-4.4 | overlay/RTMP thresholds | 未在本波实现 | **PENDING** |

## Orchestrator acceptance (G-4.1)

- 验收 [G-4.1 certify](a2d56c5f-73aa-4932-bf2c-0ecefb5670a2)：commits `0b6c8a6` / `69a112e` / `5dfb341`；编排复验 `certify --profile win_cpp` exit 0。
- **G-4.1：PASS**。Phase 4 整体未完。
- 下一波：**G-4.2**（`rt_p1_motion_gate` + `rt_p1_tracking_stable`）。

## G-4.1 证据

### certify 命令（win_cpp P0 三 case 全绿）

```text
cd F:/acme/.worktrees/runtime-parity
set ACME_ORACLE_ROOT=F:/acme
set ACME_CANDIDATE_ROOT=F:/acme/.worktrees/runtime-parity
. .\RUNTIME\scripts\deploy.env.ps1

python tools/runtime_parity_gate.py run --executor cpp --case rt_p0_heartbeat_lifecycle
python tools/runtime_parity_gate.py run --executor cpp --case rt_p0_detect_single_onnx
python tools/runtime_parity_gate.py run --executor cpp --case rt_p0_alert_hook_roi
python tools/runtime_parity_gate.py record-oracle-smoke --engine onnx
python tools/runtime_parity_gate.py certify --profile win_cpp
# → exit 0, report ok=true
```

### 分层结果（2026-08-09）

| case | L_lifecycle | L_detect | L_alarm |
|------|-------------|----------|---------|
| `rt_p0_heartbeat_lifecycle` | pass | — | — |
| `rt_p0_detect_single_onnx` | pass | pass | — |
| `rt_p0_alert_hook_roi` | pass | pass | pass |

### 实现要点

1. **certify 分层 diff 落地**（`tools/runtime_parity/diff_layers.py`）
   - `L_lifecycle`：boot.started + cpp 实采 heartbeat ≥ `thresholds.lifecycle.min_heartbeat_count_cpp`
   - `L_detect`：bbox IoU + `matched_bbox_ratio_min` + `count_tolerance`
   - `L_alarm`：alert 计数容差 + hook golden keys（G-2.2）+ class/roi；smoke 路径见 thresholds 债注

2. **run_cpp 真实采样**（`tools/runtime_parity/run_cpp.py`）
   - Mock heartbeat/hook HTTP 服务捕获 RUNTIME 实发
   - ONNX Intel 媒体帧扫描（`detect_sample.py`，`yolov11n.onnx`）
   - `rt_p0_alert_hook_roi`：RUNTIME 实发 hook payload 写入 `golden/cpp/.../alarm.json`

3. **Python golden 对齐 ONNX**（`record-oracle-smoke --engine onnx`）
   - 与 cpp RUNTIME 同模型同媒体，避免 ultralytics vs ONNX 误红

4. **阈值债（显式，非静默过关）**
   - `thresholds.alarm.smoke_allow_hook_bbox_drift=true`：live hook 帧与 smoke 快照 bbox 可不同；仍校验 hook 契约字段 + class/roi/count

## 风险 / 未完成

- Python golden 仍为 Intel 媒体 smoke，非 live oracle VIDEO 任务录制（limitations 字段保留）。
- `L_alarm` smoke 路径不强制 hook bbox 与 oracle 快照 IoU 一致（见 thresholds 债注）；删 Python 前建议补 live oracle 录制。
- G-4.2～G-4.4 仍红/未采样（tracking、snap/patrol、RTMP）。

## Orchestrator acceptance

- 建议编排 Agent **过 G-4.1 子门**（非整个 Phase 4）：`certify --profile win_cpp` P0 三层已绿，证据见本文件 + `logs/runtime_parity_report.json` 哈希。
- G-4.2 下一波可继续按红清单驱动。
