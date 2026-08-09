# Runtime Parity 测试场操作手册

> 权威门控：`docs/runtime-parity/EXECUTION.md` Phase 0（G-0.1～G-0.5）

## 环境变量

```bat
set ACME_ORACLE_ROOT=F:\acme
set ACME_CANDIDATE_ROOT=F:\acme\.worktrees\runtime-parity
cd /d %ACME_CANDIDATE_ROOT%
```

## 1. 校验骨架（doctor）

```bat
python tools\runtime_parity_gate.py doctor
```

检查：`manifest.json`、`thresholds.json`、`media/README.md`、目录结构、testbed 脚本存在性。

## 2. Mock Alert Hook

记录 VIDEO/RUNTIME 告警 POST 到 `testdata/runtime-parity/golden/video/<case_id>/`。

```bat
python docs\runtime-parity\testbed\mock_alert_hook.py --port 18080 --case rt_p0_alert_hook_roi
```

- 默认监听 `127.0.0.1:18080`（`--host` 可覆盖）
- 每次 POST 写入 `hook_<n>.json`（body + 时间戳 + headers 摘要）
- 停止：`Ctrl+C`

任务 ini / DB fixture 中 `alert_hook_url` 应指向 `http://127.0.0.1:18080/alert`。

## 3. 媒体中继（RTSP / RTMP）

### Windows 推荐：栈内 SRS

```bat
ffmpeg -re -stream_loop -1 -i testdata\runtime-parity\media\people-detection.mp4 ^
  -c copy -f flv rtmp://127.0.0.1:1935/live/parity_people
ffprobe rtmp://127.0.0.1:1935/live/parity_people
ffprobe http://127.0.0.1:8080/live/parity_people.flv
```

### Docker MediaMTX（可选）

```bat
docker compose -f docs\runtime-parity\testbed\docker-compose.media.yml up -d
```

- `rtsp://127.0.0.1:18554/people`
- 停止：`docker compose -f docs\runtime-parity\testbed\docker-compose.media.yml down`

### 原生 MediaMTX 包

下载到 `.tools/mediamtx/`（gitignore）后，用 ffmpeg 向 `rtsp://127.0.0.1:18554/people` 推流。
## 4. 录制 Python 黄金（oracle）

在 **candidate** 根执行；gate 读取 `ACME_ORACLE_ROOT` 定位 oracle 行为，**不修改** oracle 三服务代码。

```bat
python tools\runtime_parity_gate.py record-python --case rt_p0_detect_single_onnx
python tools\runtime_parity_gate.py record-python --case rt_p0_heartbeat_lifecycle
python tools\runtime_parity_gate.py record-python --case rt_p0_alert_hook_roi
```

MVP P0：`record-python` 与 `record-oracle-smoke` 等价，使用 Intel 样例片 + ultralytics/onnx 本地推理写出 `status=recorded`。

```bat
python tools\runtime_parity_gate.py record-oracle-smoke
python tools\runtime_parity_gate.py doctor --strict-golden
```

挂接真实 VIDEO：设置 `RPARITY_USE_VIDEO=1` 并确保 VIDEO 栈与 mock hook / RTSP 已起（后续 Phase 0 收尾）。

## 5. C++ 候选采样

```bat
python tools\runtime_parity_gate.py run --executor cpp --case rt_p0_detect_single_onnx
```

若 `RUNTIME` 可执行文件不存在，层状态为 `not_sampled` 或 `fail`，**不得伪造 ok**。

## 6. 分层 certify

```bat
python tools\runtime_parity_gate.py certify --case rt_p0_detect_single_onnx
python tools\runtime_parity_gate.py certify --profile win_default
```

报告：`logs/runtime_parity_report.json`。Phase 0 预期整体 `ok=false`（cpp 未对齐）。

## 目录产物

```text
testdata/runtime-parity/golden/
  python/<case_id>/   # oracle 录制
  cpp/<case_id>/      # candidate 采样
  video/<case_id>/    # mock hook 捕获
logs/runtime_parity_report.json
```
