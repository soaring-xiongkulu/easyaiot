# PHASE_0_GATE (partial)

- **Date:** 2026-08-09
- **Orchestrator:** Cursor Grok (main session)
- **Phase:** 0 测试场骨架
- **Verdict:** PARTIAL — **not** full PASS

## Checklist

| ID | Item | Evidence | OK |
|----|------|----------|----|
| G-0.1 | doctor 绿 + manifest/thresholds | `python tools/runtime_parity_gate.py doctor` exit 0 | PASS |
| G-0.2 | mock hook + RTSP relay | hook 默认 `127.0.0.1`；`--case` 拒绝 `..`/分隔符；冒烟 POST → HTTP 200（见下） | **PARTIAL**（RTSP relay 就位，未在本轮实测 compose） |
| G-0.3 | ≥3 P0 python golden from oracle | `record-oracle-smoke` 写出 `status=recorded`（`source=oracle_smoke_synthetic`）；`doctor --strict-golden` exit 0 | **PARTIAL**（smoke 非真 oracle VIDEO 录制，编排需后续换真采样） |
| G-0.4 | cpp run 可采样 | 有 cpp 骨架；RUNTIME 未找到 → not_sampled | PARTIAL |
| G-0.5 | certify 不伪造 ok | report ok=false | PASS |

## G-0.2 mock hook 冒烟

```text
# 2026-08-09 Subagent composer-2.5
python docs/runtime-parity/testbed/mock_alert_hook.py --port 18081 --case rt_p0_alert_hook_roi
# 另开 shell:
curl -s -o NUL -w "%{http_code}" -X POST http://127.0.0.1:18081/alert -H "Content-Type: application/json" -d "{\"test\":true}"
# → 200
```

无效 `--case` 示例：`--case foo/bar` → exit 2；`--case ..` → exit 2。

## G-0.3 golden smoke

```text
python tools/runtime_parity_gate.py record-oracle-smoke
python tools/runtime_parity_gate.py doctor          # PASS with WARNING if placeholders remain
python tools/runtime_parity_gate.py doctor --strict-golden  # exit 0 when all P0 recorded
```

## Review

审查 Subagent（composer-2.5）结论：Phase 0 **不允许全绿过门**。同意。

`oracle_smoke_synthetic` 满足「非 placeholder」门控与 doctor `--strict-golden`，**不等价**于 oracle VIDEO 真录制；certify 对等声明仍禁止。

## Next

1. 真录制 oracle golden（替换 smoke synthetic）
2. RTSP relay compose 实测写入本文件
3. 并行准备 Phase 1 Windows 构建（不得宣称对等）
