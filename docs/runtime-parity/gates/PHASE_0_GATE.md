# PHASE_0_GATE (partial)

- **Date:** 2026-08-09
- **Orchestrator:** Cursor Grok (main session)
- **Phase:** 0 测试场骨架
- **Verdict:** PARTIAL — **not** full PASS

## Checklist

| ID | Item | Evidence | OK |
|----|------|----------|----|
| G-0.1 | doctor 绿 + manifest/thresholds | candidate `ee99ef7`; doctor exit 0 | PASS |
| G-0.2 | mock hook + RTSP relay | hook script + compose 就位；hook 冒烟待写入本文件更新 | PARTIAL |
| G-0.3 | ≥3 P0 python golden from oracle | 当前均为 `status=placeholder` | **FAIL** |
| G-0.4 | cpp run 可采样 | 有 cpp 骨架；RUNTIME 未找到 → not_sampled | PARTIAL |
| G-0.5 | certify 不伪造 ok | report ok=false | PASS |

## Review

审查 Subagent（composer-2.5）结论：Phase 0 **不允许全绿过门**。同意。

## Next

1. 真录制 oracle golden（非 placeholder）
2. 补 fixture/媒体；doctor 拒绝 placeholder
3. 并行准备 Phase 1 Windows 构建（不得宣称对等）
