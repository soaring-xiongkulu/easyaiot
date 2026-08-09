# PHASE_0_GATE (partial)

- **Date:** 2026-08-09
- **Orchestrator:** Cursor Grok (main session)
- **Phase:** 0 测试场骨架
- **Verdict:** PARTIAL — **not** full PASS

## Checklist

| ID | Item | Evidence | OK |
|----|------|----------|----|
| G-0.1 | doctor 绿 + manifest/thresholds | `python tools/runtime_parity_gate.py doctor` exit 0 | PASS |
| G-0.2 | mock hook + RTSP relay | hook 默认 `127.0.0.1`；`--case` 拒绝 `..`/分隔符；冒烟 POST → HTTP 200（见下） | **PARTIAL**（RTSP relay 配置已更新为 Intel 四路片名，compose 未在本轮实测） |
| G-0.3 | ≥3 P0 python golden from oracle | `record-oracle-smoke` 对 Intel `people-detection` 等写出 `status=recorded`（`source=oracle_smoke_ultralytics`）；`doctor --strict-golden` exit 0 | **PARTIAL**（本地 ultralytics 推理 smoke，非 live oracle VIDEO） |
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

RTSP relay 路径已对齐 Intel 样例片名：

```text
rtsp://127.0.0.1:18554/people     -> people-detection.mp4
rtsp://127.0.0.1:18554/one_by_one -> one-by-one-person-detection.mp4
```

## G-0.3 golden smoke（Intel sample-videos + ultralytics）

媒体来源：`testdata/runtime-parity/media/{people-detection,one-by-one-person-detection,...}.mp4`（与 rebekah 四路同源，gitignore）。

```text
# 2026-08-09 Subagent composer-2.5
set ACME_ORACLE_ROOT=F:\acme
set ACME_CANDIDATE_ROOT=F:\acme\.worktrees\runtime-parity
python tools/runtime_parity_gate.py record-oracle-smoke
# exit 0; wrote golden/python for 3 P0 cases

python tools/runtime_parity_gate.py doctor
# exit 0; OK golden/python recorded (non-placeholder) P0 cases: rt_p0_*

python tools/runtime_parity_gate.py doctor --strict-golden
# exit 0
```

样例产物：`golden/python/rt_p0_detect_single_onnx/detect.json` — `media_id=people-detection`，`model=ultralytics:...yolo11n.pt`，多帧 person bbox（conf ~0.84–0.90）。

`record-python --case <P0>` 与 `record-oracle-smoke` 等价（Intel 媒体 smoke 路径）。

## Review

审查 Subagent（composer-2.5）结论：Phase 0 **不允许全绿过门**。同意。

`oracle_smoke_ultralytics` 满足 G-0.3「非 placeholder + Intel 真实样例片」门控与 `doctor --strict-golden`，**不等价**于 oracle VIDEO 真录制；certify 对等声明仍禁止。

## Next

1. 真录制 oracle golden（替换 smoke，起 VIDEO + mock hook + RTSP）
2. RTSP relay compose 实测写入本文件
3. 并行准备 Phase 1 Windows 构建（不得宣称对等）
