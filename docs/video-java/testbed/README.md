# VIDEO Java — 等价测试场提纲

## 1. 目标

对 **同一夹具**，分别命中：

- Oracle：Python VIDEO — **P0 直连** `http://127.0.0.1:6000`（Nacos 名 `video-server`）
- Candidate：Java `iot-video-biz` — **P0 直连** `http://127.0.0.1:48096`（Nacos 名 `video-server-java`）

**P0 不以改 WEB 代理或网关为前置。** 网关 `/admin-api/video-java/**` 仅可选联通。

采集分层产物并 diff；红则只改 Java（或修正夹具 bug，须记录）。Alarm 录制/回放须串行，禁止双边并行双写同一夹具。

## 2. 目录（待 Phase -1 创建）

```text
testdata/video-java/
  manifest.json          # case id → 夹具、层、优先级
  thresholds.json
  fixtures/
    tasks/               # 任务/设备种子描述（JSON）
    http/                # 可选：录制的请求序列
  golden/
    python/<case_id>/
    java/<case_id>/
  media/                 # README + 获取方式（勿强行提交大 mp4）
```

工具：

```text
tools/video_java/
  doctor.py              # 路径与依赖
  record_python.py       # 打 oracle、落 golden/python
  run_java.py            # 打 candidate、落 golden/java
  diff_layers.py         # 分层对比
  certify.py             # 汇总 PASS/FAIL
```

## 3. P0 种子用例（manifest 最小集）

| case_id | 层 | 说明 |
|---------|----|------|
| `vj_p0_health` | api | `/actuator/health` DB UP |
| `vj_p0_task_start_stop` | lifecycle + ini | 启停 cpp 任务；进程在/不在；ini 关键键 |
| `vj_p0_heartbeat` | lifecycle | RUNTIME（或 mock）POST 心跳 → DB 字段更新 |
| `vj_p0_alert_hook` | alarm | POST hook → Kafka 和/或 alert 表字段对齐 |

可选 mock：不依赖真摄像机时，用固定 RTSP 环或「仅 hook/心跳注入」模式（在 case 元数据声明 `needs_runtime: true/false`）。

## 4. 归一化规则（防假红）

- 时间戳、绝对路径、pid、host IP → 占位符  
- ini 中 `model_path`/`log_path` → 相对化或 basename  
- JSON 键序排序后比  

## 5. 与 runtime-parity 媒体

可复用 Intel sample 视频获取脚本思想（`tools/runtime_parity/fetch_parity_media.py`），**输出目录必须是 `testdata/video-java/media`**，不要写进 runtime-parity golden。

## 6. 本地双跑注意

- 两侧不要 `auto_start` 同一 `task_id`  
- Oracle 录制时可 `VIDEO_SKIP_BACKGROUND_TASKS=1` 后按脚本显式 start  
- Gateway 测试走 `/admin-api/video-java/**` 或直连 `:48096`（在 case 中写明 base URL）

## 7. PASS 出口

`python tools/video_java/certify.py --phase 0`（名称可议）退出码 0，并生成/更新 `docs/video-java/gates/PHASE_0_GATE.md` 证据表。
