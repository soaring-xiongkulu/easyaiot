# PHASE_0_GATE

- **Date:** 2026-08-09
- **Orchestrator:** Cursor Grok (main session)
- **Phase:** 0 测试场骨架
- **Verdict:** **PASS**

## Checklist

| ID | Item | Evidence | OK |
|----|------|----------|----|
| G-0.1 | doctor 绿 + manifest/thresholds | `python tools/runtime_parity_gate.py doctor` / `--strict-golden` exit 0 | **PASS** |
| G-0.2 | mock hook + 媒体中继可起停 | hook POST → 200；本机 SRS `rtmp://127.0.0.1:1935/live/parity_people` ffprobe 见 video/audio（Docker MediaMTX 本机不稳定，改用已有 SRS 作中继证据） | **PASS** |
| G-0.3 | ≥3 P0 python golden | Intel sample + ultralytics `status=recorded`；`source=oracle_smoke_ultralytics`；`--strict-golden` exit 0 | **PASS** |
| G-0.4 | cpp run 可采样 | `run --executor cpp` → `infer_ep=cpu` + person 检测日志；`golden/cpp/rt_p0_*` | **PASS** |
| G-0.5 | certify 不伪造 ok | `certify` report `ok=false`（diff MVP 未实现） | **PASS** |

## G-0.2 证据

```text
# mock hook
python docs/runtime-parity/testbed/mock_alert_hook.py --port 18083 --case rt_p0_alert_hook_roi
curl → HTTP 200

# media relay (SRS already running in stack)
ffmpeg -re -stream_loop -1 -i testdata/runtime-parity/media/people-detection.mp4 \
  -c copy -f flv rtmp://127.0.0.1:1935/live/parity_people
ffprobe rtmp://127.0.0.1:1935/live/parity_people  → audio + video
ffprobe http://127.0.0.1:8080/live/parity_people.flv → audio + video
```

MediaMTX compose 仍保留于 `docs/runtime-parity/testbed/`（可选）；本机 Docker Desktop 曾出现容器瞬态消失，故门控证据采用 SRS。

## G-0.3 编排拍板

Phase 0 出口接受 **Intel sample-videos + ultralytics smoke** 作为「非 placeholder python golden」。  
**不等于** live oracle VIDEO 真采样；`meta.limitations` 已声明。certify 对等声明前须替换为 live `record-python`（跟踪至 Phase 4/5）。

## G-0.4 证据

```text
. .\RUNTIME\scripts\deploy.env.ps1
python tools/runtime_parity_gate.py run --executor cpp --case rt_p0_detect_single_onnx
# boot infer_ep=cpu; Detected: person (83%+)
# report: logs/runtime_parity_report.json
```

## Orchestrator acceptance

- Phase 0 **PASS**（2026-08-09）。
- 允许正式推进 Phase 1 收尾与 Phase 2（已并行的 G-1.x 继续）。
