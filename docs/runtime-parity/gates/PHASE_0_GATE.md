# PHASE_0_GATE (partial)

- **Date:** 2026-08-09
- **Orchestrator:** Cursor Grok (main session)
- **Phase:** 0 测试场骨架
- **Verdict:** PARTIAL — **not** full PASS（G-0.2/G-0.3 有实质进展，仍缺 live oracle VIDEO golden）

## Checklist

| ID | Item | Evidence | OK |
|----|------|----------|----|
| G-0.1 | doctor 绿 + manifest/thresholds | `python tools/runtime_parity_gate.py doctor` exit 0 | **PASS** |
| G-0.2 | mock hook + RTSP relay | hook 冒烟 POST→200；RTSP `people` 流 ffmpeg 实测可读（见下） | **PASS** |
| G-0.3 | ≥3 P0 python golden from oracle | 3 case `status=recorded` + `doctor --strict-golden` exit 0；来源为 Intel smoke，非 live VIDEO | **PARTIAL** |
| G-0.4 | cpp run 可采样 | `rt_p0_detect_single_onnx` cpp golden `status=sampled`/`sampled_partial`，`infer_ep=cpu`（见下） | **PASS** |
| G-0.5 | certify 不伪造 ok | `certify --profile win_default` exit 1，`ok=false`，summary fail/not_sampled | **PASS** |

## G-0.2 mock hook 冒烟

```text
# 2026-08-09 Subagent composer-2.5
python docs/runtime-parity/testbed/mock_alert_hook.py --port 18081 --case rt_p0_alert_hook_roi
# 另开 shell:
curl -s -o NUL -w "%{http_code}" -X POST http://127.0.0.1:18081/alert -H "Content-Type: application/json" -d "{\"test\":true}"
# → 200
```

无效 `--case` 示例：`--case foo/bar` → exit 2；`--case ..` → exit 2。

### G-0.2 RTSP relay 实测（2026-08-09 Subagent composer-2.5）

**方式：** Docker `bluenviron/mediamtx:latest` + 本机 ffmpeg 推流（Intel `people-detection.mp4`）。

```text
# 1) 起 MediaMTX（映射 18554→8554）
docker run -d --name runtime-parity-mediamtx \
  -p 18554:8554 -p 18888:8888 \
  -v F:/acme/.worktrees/runtime-parity/docs/runtime-parity/testbed/mediamtx.yml:/mediamtx.yml:ro \
  bluenviron/mediamtx:latest /mediamtx.yml

# 2) 本机循环推流
ffmpeg -re -stream_loop -1 -i testdata/runtime-parity/media/people-detection.mp4 \
  -c copy -f rtsp -rtsp_transport tcp rtsp://127.0.0.1:18554/people

# 3) 验证可读（exit 0）
ffmpeg -hide_banner -rtsp_transport tcp -i rtsp://127.0.0.1:18554/people -t 2 -f null -
# → Stream #0:0 Video: h264 (Baseline), 768x432, 12 fps
# → Stream #0:1 Audio: aac (LC), 48000 Hz, stereo

# 4) 停服
docker stop runtime-parity-mediamtx && docker rm runtime-parity-mediamtx
# （ffmpeg 推流进程 Ctrl+C / Stop-Process）
```

`docker-compose.media.yml` 亦已配置 `mediamtx` + `ffmpeg-people`/`ffmpeg-one-by-one` 伴随推流；首次 `compose up` 需拉取 `jrottenberg/ffmpeg` 镜像（网络慢时可沿用上述「单容器 mediamtx + 本机 ffmpeg」路径）。

RTSP 路径：

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

python tools/runtime_parity_gate.py doctor --strict-golden
# exit 0
```

样例产物：`golden/python/rt_p0_detect_single_onnx/detect.json` — `media_id=people-detection`，`model=ultralytics:...yolo11n.pt`，多帧 person bbox（conf ~0.84–0.90）。

`record-python --case <P0>` 与 `record-oracle-smoke` 等价（Intel 媒体 smoke 路径）。`RPARITY_USE_VIDEO=1` 当前仍回退 smoke（`tools/runtime_parity/record.py` 未实现 live VIDEO 抓取）。

### G-0.3 live oracle 阻塞说明

- Oracle `F:/acme/VIDEO` 存在但本轮未起 python 任务真采样。
- Gate 代码无 live VIDEO 集成；**不得伪造** live golden。
- 建议编排接受的 **Phase 0 smoke 过门条件**（供拍板，非 certify 依据）：
  1. ≥3 P0 case `golden/python/*/meta.json` 中 `status=recorded` 且 `synthetic=false`
  2. `doctor --strict-golden` exit 0
  3. 媒体为 Intel sample-videos（非 ffmpeg 色条/不明来源）
  4. detect 层含真实 ultralytics 推理 bbox（非空壳）
  5. **明确标注** `source=oracle_smoke_*`，Phase 4+ certify 对等声明前须替换为 live oracle `record-python`

## G-0.4 cpp 采样（2026-08-09 Subagent composer-2.5）

```text
python tools/runtime_parity_gate.py run --executor cpp --case rt_p0_detect_single_onnx
# 本轮首跑：WARN RUNTIME binary not found → not_sampled skeleton

# 同窗口 RTSP 实测期间另一采样写出（RUNTIME 曾可用）：
# golden/cpp/rt_p0_detect_single_onnx/meta.json
#   runtime_boot.started=true, infer_ep=cpu, exit_code=1, duration_sec=20.27
#   log_tail 含 YOLO person detections (83%–91%)
# lifecycle.json status=sampled; detect.json status=sampled_partial
```

报告：`logs/runtime_parity_report.json`（`command=run` 或 `certify` 均含 cpp 侧 artifact 路径）。

## G-0.5 certify 红清单

```text
python tools/runtime_parity_gate.py certify --profile win_default
# exit 1
# ok=false
# summary: pass=0, fail=3, not_sampled=3
```

未伪造 `ok=true`；缺层为 `fail` / `not_sampled`（cpp 未对齐或缺 golden）。

## Review

审查 Subagent（composer-2.5）结论：**Phase 0 仍不建议全绿过门**。

- G-0.2、G-0.4、G-0.5 本轮可标 **PASS**。
- G-0.3 维持 **PARTIAL**：smoke golden 满足骨架门控，**不等价**于 oracle VIDEO 真录制。
- 若编排采纳上文 smoke 过门条件，可 **有条件放行 Phase 1 构建并行**，但 certify 对等声明仍禁止直至 live oracle golden。

### Orchestrator acceptance (2026-08-09)

- 验收 [Record Intel goldens](7bd2054a-af8d-4679-b692-38abc0aca705)：commit `ac9e899`（及后续 `6593641` testbed 对齐）。
- **G-0.3 维持 PARTIAL**，Phase 0 **不过门**（除非编排书面采纳 smoke 条件）。
- 本轮新增：RTSP relay 实测 PASS；cpp 采样证据 PASS；certify 红清单 PASS。

## Next

1. 真录制 oracle golden（起 VIDEO + mock hook + RTSP，`RPARITY_USE_VIDEO` 实装）
2. 固化 `docker compose -f docs/runtime-parity/testbed/docker-compose.media.yml up -d` 一键起停（ffmpeg 镜像已缓存后）
3. 并行 Phase 1 Windows RUNTIME 构建（不得宣称对等）
