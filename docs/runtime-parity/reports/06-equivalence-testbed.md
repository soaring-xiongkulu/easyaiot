# Report: Python runtime vs C++ RUNTIME（+VIDEO 帧后）功能表现等价测试场

- **Agent role:** 调研 Agent（测试场设计；引用 `01`–`04` 能力清单，不重复发明 CAP 定义）
- **Scope paths:**
  - 上游报告：`docs/runtime-parity/reports/01-python-realtime.md`、`02-python-snap-patrol.md`、`03-cpp-runtime-baseline.md`、`04-video-absorb-surface.md`
  - 执行器：`VIDEO/services/*_algorithm_service/`、`RUNTIME/`、`VIDEO/app/services/{algorithm_task_daemon,runtime_config_service,alert_hook_service}.py`
  - 参考思想（只读）：`rebekah-learn/docs/decisions/{PARITY_CERTIFY,ORACLE_GATE}.md`、`golden/README.md`
- **Date:** 2026-08-09
- **Confidence:** high（测试场架构与用例矩阵已对齐四份基线报告；具体阈值默认值待产品拍板）

## 1. Executive summary

本报告定义 EasyAIoT **功能表现等价**验收测试场：以 **Python `executor=python` 为行为黄金参考（oracle）**，在同一冻结输入（标准视频流/夹具 + 任务 DB 配置）下，对照 **C++ `executor=cpp` RUNTIME** 与 **VIDEO 帧后编排**（Hook→Kafka/匹配/后处理），判定是否「用户可见行为一致」。

设计吸收 rebekah-learn 的 **先录黄金、再 diff、分层 certify** 纪律：`manifest.json` 冻结 case → `record-python` 录基准 → `run` 对候选路径采样 → `certify` 出红清单。与 rebekah 不同，EasyAIoT 分 **三层尺子**：**L_exec**（执行器帧内）、**L_platform**（VIDEO 帧后）、**L_e2e**（全链路）；**仅 L_exec 绿不得宣称可替换 Python runtime**。

测试场提供：**标准 RTSP/MP4 夹具库**、**Mock SAM/Hook 服务**、**用例矩阵（CAP-* × P0/P1/P2）**、**性能列（延迟/吞吐/资源 + 可接受下降阈值）**。SAM 在 C++ 未实现时仍执行 **同一图片分割对比协议**（Python 为 oracle；C++ 记录 `not_implemented` 或 mock 对齐，不得静默跳过）。

**Windows / Linux 双门禁：** Linux 跑完整 `certify`（含 cpp RUNTIME）；Windows 默认 **python oracle + VIDEO 平台门禁**，cpp 子门禁在 `RUNTIME` Windows 构建就绪后启用（`gate_profile=win_cpp`）。两平台共享同一 `manifest` 与阈值文件，仅 `media_server` 与 `executor_bin` 路径分叉。

建议落盘目录：`testdata/runtime-parity/`（夹具与黄金）、`docs/runtime-parity/testbed/`（README 与操作手册）、`tools/runtime_parity_gate.py`（门禁入口，待实现）。

---

## 2. Inventory / Findings

### 2.1 测试场组件清单（非能力堆砌）

| 组件 ID | 名称 | 职责 | 建议路径 |
|---------|------|------|----------|
| **TB-MANIFEST** | 用例清单 | 冻结 case：`task_type`、executor、CAP 覆盖、媒体、DB fixture、必选层 | `testdata/runtime-parity/manifest.json` |
| **TB-THRESHOLDS** | 全局阈值 | IoU、告警计数容差、延迟倍率、资源上限；case 可覆盖 | `testdata/runtime-parity/thresholds.json` |
| **TB-MEDIA** | 标准视频夹具 | 循环 MP4、多路延迟源、花屏注入、已知目标 ROI | `testdata/runtime-parity/media/`（小体积样本；大文件 git-lfs 或 CI 缓存） |
| **TB-DB-FIXTURE** | 任务/设备 SQL 种子 | `AlgorithmTask` + `Device` + 区域多边形；双 executor 共用 | `testdata/runtime-parity/fixtures/tasks/*.json` |
| **TB-GOLDEN-PY** | Python 黄金产物 | `record-python` 输出：detect/alarm/track/stream/perf | `testdata/runtime-parity/golden/python/<case_id>/` |
| **TB-GOLDEN-CPP** | C++ 候选产物 | `run --executor cpp` 同构采样 | `testdata/runtime-parity/golden/cpp/<case_id>/` |
| **TB-GOLDEN-VID** | VIDEO 平台产物 | Hook mock 捕获、Kafka 落库、匹配记录 | `testdata/runtime-parity/golden/video/<case_id>/` |
| **TB-MOCK-HOOK** | 告警 Hook 采集器 | 记录 POST body、时间戳、图片路径；可回放 | `docs/runtime-parity/testbed/mock_alert_hook.py` |
| **TB-MOCK-SAM** | SAM 对照服务 | 固定图片+框输入 → 确定性 mask/bbox JSON；Python/C++ 同端点 | `docs/runtime-parity/testbed/mock_sam_server.py` |
| **TB-RTSP-RELAY** | 本地 RTSP 回放 | ffmpeg/MediaMTX 将 MP4 转为稳定 RTSP（消网络抖动） | `docs/runtime-parity/testbed/docker-compose.media.yml` |
| **TB-GATE** | 门禁 CLI | `doctor` / `record-python` / `run` / `certify` | `tools/runtime_parity_gate.py` |
| **TB-REPORT** | 红清单报告 | `logs/runtime_parity_report.json` | CI 产物 |
| **TB-PERF-HARNESS** | 性能采样 | 进程 CPU/GPU/内存、帧延迟直方图、告警 TTF | `docs/runtime-parity/testbed/perf_sampler.py` |

### 2.2 采样层（certify 尺子）

借鉴 rebekah `PARITY_CERTIFY` 分层，映射 EasyAIoT：

| 块 | 层 ID | 产物文件 | 判定要点 | 主要 CAP |
|----|-------|----------|----------|----------|
| **L_exec** | `L_lifecycle` | `lifecycle.json` | 拉起/退出码、心跳 200、间隔、字段完整 | `CAP-TASK-BOOT`, `CAP-HEARTBEAT` |
| **L_exec** | `L_detect` | `detect.json` | 同帧 bbox IoU≥阈值、class 一致、数量容差 | `CAP-YOLO-INFER`, `CAP-ONNX-INFER`, `CAP-MULTI-MODEL` |
| **L_exec** | `L_track` | `track.json` | track_id 映射稳定率、切换次数 ±10% | `CAP-TRACKING` |
| **L_exec** | `L_overlay` | `overlay.json` | 框出现/消失相对帧时间戳 P95 延迟 | `CAP-OVERLAY-*`, `CAP-DRAW-OVERLAY` |
| **L_exec** | `L_stream` | `stream.json` | ffprobe：分辨率/fps/码率档位；灰屏计数 | `CAP-RTMP-PUSH`, `CAP-FIXED-RATE-PUSH` |
| **L_exec** | `L_schedule` | `schedule.json` | snap 槽位时间、patrol 间隔分布 | `CAP-CRON-SNAP`, `CAP-PATROL-*` |
| **L_exec** | `L_sam` | `sam.json` | **同图同框**：mask IoU 或合并框 IoU；source 标记 | `CAP-SAM` |
| **L_exec** | `L_motion` | `motion.json` | 运动触发次数、补检帧数 | `CAP-MOTION-GATE` |
| **L_platform** | `L_alarm` | `alarm.json` | Hook payload 字段集合、抑制、cooldown、计数 | `CAP-ALERT-HOOK`, `CAP-ALERT-SUPPRESS` |
| **L_platform** | `L_kafka` | `kafka.json` | topic、关键字段、`faceDetectionEnabled` | `CAP-ALERT-KAFKA` |
| **L_platform** | `L_face` | `face_match.json` | publish/process 次数、hit 记录 | `CAP-FACE-MATCH` |
| **L_platform** | `L_plate` | `plate_match.json` | 同上 | `CAP-PLATE-MATCH` |
| **L_platform** | `L_post` | `post_process.json` | enqueue 次数、Worker 产出 | `CAP-POST-PROCESS` |
| **L_e2e** | `L_e2e_alarm` | `e2e_alarm.json` | 同场景告警条数 ±容差、端到端延迟 | 多 CAP 组合 |
| **L_perf** | `L_perf` | `perf.json` | 延迟 P50/P95、FPS、CPU/GPU/内存 | 全局 |

**可替换宣称（等价 Python runtime 删除）：** `L_exec` 必选层全绿 **且** `L_platform` 对启用能力全绿 **且** `L_e2e` P0 case 全绿；`L_perf` 不劣于阈值。缺层记 `not_sampled` → 不得 `ok=true`。

### 2.3 标准视频流 / 夹具规格

| 夹具 ID | 内容 | 时长 | 用途 |
|---------|------|------|------|
| `media_person_roi_30s` | 单人走动，已知 bbox 黄金 JSON | 30s@25fps | 检测/追踪/告警基线 |
| `media_multi_person_60s` | 2–4 人交叉 | 60s | 追踪 ID 稳定性 |
| `media_static_30s` | 空场景 | 30s | 负例：零告警 |
| `media_motion_trigger_20s` | 前 10s 静止 + 后 10s 运动 | 20s | `CAP-MOTION-GATE` |
| `media_gray_inject_30s` | 中段 2s 花屏 | 30s | `CAP-CRON-GRAY-SKIP` / 重连 |
| `media_plate_face_15s` | 含车牌/人脸样本 | 15s | 匹配链（平台层） |
| `media_sam_ref_1f` | 单帧 PNG + YOLO 框 JSON | 1 帧 | **SAM 分割对比协议** |
| `media_8ch_stagger` | 8 路循环 MP4（可配置延迟） | 各 30s | 多路 patrol pool / snap 并行 |
| `media_rtsp_relay_*` | 上述 MP4 经 MediaMTX 转 RTSP | 同左 | 消除解码差异；**两侧必须用同 relay URL** |

> 不批量提交大视频二进制：仓库内放 **≤5MB 样本** + `media/README.md` 说明 CI 下载脚本（`scripts/fetch_parity_media.sh`）。

### 2.4 SAM 分割对比协议（C++ 缺 SAM 时仍执行）

**目的：** 效果一致可验收；性能允许 C++ 更优或略降（见 §2.6）。

**冻结输入（每 case 一份）：**

- `sam_input.png`：固定分辨率 BGR/PNG
- `sam_boxes.json`：`[{ "bbox": [x1,y1,x2,y2], "class": "person", "conf": 0.9 }]`
- `sam_config.json`：与 DB `sam_supplement_config` 同构（阈值、合并策略）

**流程：**

1. **Python 路径（oracle）：** 启用 `sam_supplement_enabled`，指向 `TB-MOCK-SAM` 或真实 AI `/model/sam/predict`；输出 `sam.json`：`masks[]` / `merged_detections[]` / `source` 标记。
2. **C++ 路径：**
   - **未实现：** 必须显式产出 `sam.json`：`{ "status": "not_implemented", "cap": "CAP-SAM" }` → certify 记 **fail**（产品可选择「cpp 不支持 SAM」豁免，须 manifest 标注 `cpp_sam: skip_allowed`）。
   - **mock 对齐：** C++ 调同一 `TB-MOCK-SAM` → 与 Python 比 mask IoU（≥0.85）或合并框 IoU（≥0.5）。
   - **内嵌实现：** 同协议比效果；**perf 列**记录 SAM 增量延迟。
3. **禁止：** C++ 静默不调用、不用同图、或以「无 SAM」跳过 case。

### 2.5 性能列与「可接受下降」阈值

默认阈值（**待产品拍板**，manifest case 可覆盖）：

| 指标 | 采样方法 | Python 基准 | C++ / VIDEO 可接受 | 备注 |
|------|----------|-------------|-------------------|------|
| **端到端告警延迟** | 画面目标进入 ROI → Hook 收到 POST | 录 P50/P95 | P95 ≤ Python×**1.2** 或 +**200ms**（取较宽） | `PERF_LATENCY_ALERT_P95_RATIO=1.2` |
| **叠框可见延迟** | 检测日志帧号 vs 推流录屏 | P95 | ≤ Python P95 + **200ms@25fps** | 见 `01` §5 |
| **推理吞吐** | 稳态 FPS（单路 1080p） | 实测 | ≥ Python×**0.9** 或更高 | C++ 允许更快 |
| **多路并发（8 路）** | 总 CPU%、GPU 显存 | 实测 | CPU ≤ Python×**0.85**；显存 ≤ Python×**1.1** | 省核为目标 |
| **SAM 增量延迟** | 启用 SAM 单帧 | 实测 | ≤ Python×**1.0**（可更快）；慢于 ×**1.3** 记 WARN | 效果优先于 SAM 性能 |
| **内存 RSS** | 进程稳态 | 实测 | ≤ Python×**0.8** 或绝对 +**512MB** 内 | snap/patrol 单设备 |
| **告警吞吐** | 告警/分钟（压力场景） | 实测 | 计数差异 ≤ **1 次/分钟** | 与 `L_alarm` 联动 |

性能 **不单独充绿**：功能层 fail 则 perf 再优也不算通过。

### 2.6 用例矩阵（CAP-* × 优先级）

优先级定义：

- **P0：** 阻塞「cpp 替代 python」宣称；CI `certify` 默认必跑
- **P1：** 核心体验完整；发布前全绿
- **P2：** 边缘/运维/优化；债表可延期

#### Realtime（`task_type=realtime`）

| Case ID | P | CAP 覆盖 | 简述 | L_exec 必选层 | 备注 |
|---------|---|----------|------|---------------|------|
| `rt_p0_detect_single_onnx` | P0 | `CAP-YOLO-INFER`, `CAP-ONNX-INFER` | 单设备单 ONNX，`media_person_roi_30s` | detect, lifecycle | cpp 主路径；对齐 `03` 黄金基线 |
| `rt_p0_alert_hook_roi` | P0 | `CAP-ALERT-HOOK`, `CAP-REGION-FILTER` | 区域内置信度告警 + cooldown | detect, alarm, lifecycle | Mock hook；比次数与 payload |
| `rt_p0_heartbeat_lifecycle` | P0 | `CAP-HEARTBEAT`, `CAP-TASK-BOOT` | 启动 2min 心跳 ≥10 次 | lifecycle | 字段 `task_id/process_id/log_path` |
| `rt_p0_sam_same_image` | P0 | `CAP-SAM` | `media_sam_ref_1f` + mock SAM | sam, detect | **无 SAM 也跑**；见 §2.4 |
| `rt_p1_tracking_stable` | P1 | `CAP-TRACKING` | `media_multi_person_60s` | detect, track, overlay | cpp 未实现 → fail/债 |
| `rt_p1_overlay_timing` | P1 | `CAP-OVERLAY-*`, `CAP-DRAW-OVERLAY` | overlay/alert 分轨采样 | overlay, detect | overlay vs alert imgsz 分别覆盖 |
| `rt_p1_rtmp_stream` | P1 | `CAP-RTMP-PUSH`, `CAP-FIXED-RATE-PUSH` | ffprobe 输出流 | stream, lifecycle | |
| `rt_p1_motion_gate` | P1 | `CAP-MOTION-GATE` | `media_motion_trigger_20s` | motion, detect, alarm | |
| `rt_p1_multi_model` | P1 | `CAP-MULTI-MODEL` | 双 ONNX 串联 | detect | cpp 当前单模型 → 预期 fail |
| `rt_p1_face_plate_filter` | P1 | `CAP-CLASS-FILTER`, `CAP-FACE-DETECT`, `CAP-PLATE-DETECT` | 类名过滤 | detect, alarm | |
| `rt_p2_gpu_sched` | P2 | `CAP-GPU-SCHED` | 多卡 round_robin | perf | |
| `rt_p2_quality_nvenc` | P2 | `CAP-NVENC`, `CAP-QUALITY-AUTO` | 编码降档 | stream, perf | |
| `rt_p2_gb28181_relay` | P2 | `CAP-GB28181-SOURCE`, `CAP-STREAM-INPUT` | 国标解析回放 | lifecycle, detect | 夹具模拟 URL |

#### Snap（`task_type=snap`）

| Case ID | P | CAP 覆盖 | 简述 | L_exec 必选层 |
|---------|---|----------|------|---------------|
| `snap_p0_cron_slot` | P0 | `CAP-CRON-SNAP` | `0 */30 * * * *` 东八区，单设备 | schedule, detect, alarm |
| `snap_p0_alert_payload` | P0 | `CAP-ALERT-HOOK`, `CAP-ALERT-IMAGE` | `task_type=snapshot` 字段 | alarm, lifecycle |
| `snap_p1_multi_device_cron` | P1 | `CAP-CRON-SNAP`, `CAP-SNAPSHOT-PENDING` | 8 设备同槽 | schedule, detect |
| `snap_p1_gray_retry` | P1 | `CAP-CRON-GRAY-SKIP` | `media_gray_inject_30s` | schedule, detect |
| `snap_p1_snap_space` | P1 | `CAP-SNAP-SPACE` | 入库计数（VIDEO） | schedule + **L_platform** kafka |
| `snap_p2_no_cron_fallback` | P2 | `CAP-CRON-NO-FALLBACK` | 无 cron 行为对齐 | schedule | Python vs cpp 语义差异显式测 |

#### Patrol（`task_type=patrol`）

| Case ID | P | CAP 覆盖 | 简述 | L_exec 必选层 |
|---------|---|----------|------|---------------|
| `patrol_p0_pool_interval` | P0 | `CAP-PATROL-POOL` | 8 设备 pool=4，interval=30s | schedule, lifecycle |
| `patrol_p0_heartbeat_progress` | P0 | `CAP-PATROL-PROGRESS`, `CAP-HEARTBEAT` | `total_patrols` 递增 | lifecycle |
| `patrol_p1_rotate_order` | P1 | `CAP-PATROL-ROTATE` | 顺序轮巡 | schedule |
| `patrol_p1_hybrid_focus` | P1 | `CAP-PATROL-HYBRID` | 焦点 15s / 背景 30s | schedule | cpp 缺失 → 预期 fail |
| `patrol_p1_oneshot_warmup` | P1 | `CAP-PATROL-ONESHOT` | 预热帧数对齐 | detect, schedule |

#### VIDEO 帧后（executor 无关或 cpp 触发）

| Case ID | P | CAP 覆盖 | 简述 | 块 |
|---------|---|----------|------|-----|
| `vid_p0_hook_kafka` | P0 | `CAP-ALERT-KAFKA`, `CAP-ALERT-SUPPRESS` | python/cpp 形 Hook 各 1 份 | L_platform |
| `vid_p0_face_match_chain` | P0 | `CAP-FACE-MATCH` | 告警图 → 匹配记录 | L_platform + L_e2e |
| `vid_p1_plate_match_chain` | P1 | `CAP-PLATE-MATCH` | 同上 | L_platform |
| `vid_p1_post_process_enqueue` | P1 | `CAP-POST-PROCESS` | hook 后入队 | L_platform |
| `vid_p1_cpp_hook_orchestrator` | P1 | `04` 方案 A | **仅 cpp 任务**：VIDEO 补触发 | L_e2e |
| `vid_p2_pose_intent` | P2 | `CAP-POSE-ANALYSIS`, `CAP-POSE-INTENT` | Worker 产出 | L_platform |

#### 端到端与性能

| Case ID | P | 覆盖 | 简述 |
|---------|---|------|------|
| `e2e_p0_realtime_python_vs_cpp` | P0 | realtime 检测+告警 | 同 `task fixture` 双 executor 60s |
| `e2e_p0_sam_enabled` | P0 | SAM + 告警 | 同图协议 + 告警计数 |
| `perf_p0_realtime_latency` | P0 | `L_perf` | 单路延迟/资源 |
| `perf_p1_realtime_8ch` | P1 | `L_perf` | 8 路并发 |

### 2.7 Windows 与 Linux 门禁组织

```
                    testdata/runtime-parity/manifest.json
                    testdata/runtime-parity/thresholds.json
                                    │
            ┌───────────────────────┴───────────────────────┐
            ▼                                               ▼
   gate_profile=linux_full                          gate_profile=win_default
            │                                               │
   ┌────────┴────────┐                         ┌────────────┴────────────┐
   │ L_exec (py+cpp) │                         │ L_exec (python only)    │
   │ L_platform      │                         │ L_platform              │
   │ L_e2e P0+P1     │                         │ L_e2e P0 (py baseline)  │
   │ L_perf          │                         │ L_perf (python)         │
   └────────┬────────┘                         │ optional: win_cpp P0    │
            │                                  └────────────┬────────────┘
            ▼                                               ▼
   CI: ubuntu-22.04 + CUDA                          CI: windows-2022
   ensure_runtime_cpp.sh                             executor=python 默认
   docker-compose.media.yml                          MediaMTX win 包
```

| 维度 | Linux `linux_full` | Windows `win_default` | Windows `win_cpp`（可选） |
|------|-------------------|----------------------|---------------------------|
| **执行器** | python + cpp | python | python + cpp（构建可用时） |
| **P0 case** | 全部 | `vid_*` + `rt_p0_*`（python 侧）+ SAM 协议 | 与 Linux P0 对齐的子集 |
| **RTSP 回放** | Docker MediaMTX | 原生 MediaMTX 或 ffmpeg `-re` | 同左 |
| **GPU** | CUDA EP | DirectML/CUDA（待 `03` W1–W10） | 同左 |
| **通过条件** | `certify --profile linux_full` ok | `certify --profile win_default` ok | 额外 `win_cpp` ok 才可宣称 Windows cpp 对等 |
| **阻断策略** | 阻塞 merge 至 main | 阻塞 Windows 安装包 | 不阻塞，债表跟踪 |

**纪律（来自 ORACLE_GATE）：**

- `run` 绿 ≠ 可替换；仅 `certify` + 全 P0 绿可宣称阶段性等价。
- 红清单只来自 `logs/runtime_parity_report.json`；禁止静默降阈值。
- cpp 未实现能力必须在 manifest 标 `expected_fail: true` 直至实现，避免假绿。

---

## 3. Placement hint

| 测试场组件 / 层 | 建议落点 | 理由 |
|-----------------|----------|------|
| `TB-GATE` / `certify` 主逻辑 | `tools/runtime_parity_gate.py` | 与 rebekah `oracle_gate.py` 同层级 |
| 夹具与黄金 | `testdata/runtime-parity/` | 与 `rebekah-learn/testdata/oracle` 同构 |
| Mock 服务、compose | `docs/runtime-parity/testbed/` | 文档+脚本，非生产代码 |
| `L_exec` 采样钩子 | Python：`run_deploy` 调试 env；C++：`RUNTIME` 测试构建或日志解析 | 尽量少侵入；优先离线 MP4 回放 |
| `L_platform` 采样 | VIDEO 测试库 + mock Kafka | 已有 `alert_hook_service` 可测 |
| CI 入口 | `.github/workflows/runtime-parity.yml`（待建） | Linux 全量；Windows 矩阵分 profile |
| SAM 协议 | `TB-MOCK-SAM` 独立进程 | Python/C++ 同 URL，保证同输入 |

---

## 4. Gaps / Risks

1. **cpp 大量 CAP 缺失**（`03`）：P0 中 `rt_p0_sam_same_image`、`rt_p1_tracking_stable` 等将长期红；需 `expected_fail` + 债表，避免阻塞 python 侧回归。
2. **双队列 vs 单 frame_skip**：Python overlay/alert 双推理；cpp 单次 — `e2e` 告警计数可能系统性偏差，需 manifest 分轨或合并推理后重测。
3. **推理阈值不一致**：cpp 引擎固定 0.25 vs Python `YOLO_DETECT_CONF` — `L_detect` 须用 **同一 ONNX + 对齐后处理**，或单独 `calibration case`。
4. **帧后断链**（`04`）：cpp 仅 Hook；`vid_p1_cpp_hook_orchestrator` 未实现前，`L_face`/`L_post` 仅能以 python executor 绿。
5. **Windows cpp 未就绪**：`win_cpp` 门禁空跑会误报；默认关闭直至 `install_windows` 存在。
6. **媒体版权与体积**：黄金视频不可入仓 → CI 依赖缓存；首次 `record-python` 成本高。
7. **时间语义**：snap 东八区 vs patrol UTC — `schedule.json` 比较须显式时区 normalization。
8. **Kafka 环境**：平台层需 testcontainer 或 mock；否则 `L_kafka` 长期 `not_sampled`。

---

## 5. Equivalence notes

### 5.1 怎样才算「功能表现一致」

| 场景 | 一致标准 | 采样层 |
|------|----------|--------|
| 实时检测 | 同流同模型：matched bbox 比例 ≥ **95%**（IoU≥0.5，class 相同） | `L_detect` |
| 追踪 | track 切换次数 ±**10%**；同源 ID 映射率 ≥ **90%** | `L_track` |
| 叠框/推流 | 框延迟 P95 ≤ Python + **200ms**；分辨率/fps 一致 | `L_overlay`, `L_stream` |
| 告警 | 同场景计数差 ≤ **1/min**；payload 字段集合一致（cpp 缺字段由 VIDEO 补全后比 Kafka） | `L_alarm`, `L_kafka` |
| SAM | 同图：合并框 IoU≥**0.5** 或 mask IoU≥**0.85**；`source` 标记一致 | `L_sam` |
| snap Cron | 每槽每设备 ≤1 张；槽时间偏差 ≤ `snap_cron_match_window_seconds` | `L_schedule` |
| patrol pool | 间隔 **30s±3s**；并行度 ≤ pool_size；无饿死 | `L_schedule` |
| 人脸/车牌 | 匹配记录数一致；阈值行为一致 | `L_face`, `L_plate` |
| 性能 | 见 §2.5；**不得**牺牲召回率换性能 | `L_perf` |

### 5.2 建议目录结构（规划，本次不批量建二进制）

```
F:/acme/
├── docs/runtime-parity/testbed/
│   ├── README.md                 # 操作：record-python / run / certify
│   ├── docker-compose.media.yml  # MediaMTX + 可选 mock 服务
│   ├── mock_alert_hook.py
│   ├── mock_sam_server.py
│   └── perf_sampler.py
├── testdata/runtime-parity/
│   ├── manifest.json
│   ├── thresholds.json
│   ├── media/README.md           # 样本列表 + fetch 脚本
│   ├── fixtures/tasks/           # DB JSON 种子
│   └── golden/
│       ├── python/<case_id>/
│       ├── cpp/<case_id>/
│       └── video/<case_id>/
├── tools/runtime_parity_gate.py
└── logs/runtime_parity_report.json   # gitignore
```

### 5.3 最小闭环命令（目标态）

```bat
REM 校验 manifest / 夹具 / 媒体可达
python tools\runtime_parity_gate.py doctor

REM 录 Python 黄金（需 VIDEO + 媒体栈）
python tools\runtime_parity_gate.py record-python --case rt_p0_detect_single_onnx

REM 对照 cpp（Linux）
python tools\runtime_parity_gate.py run --case rt_p0_detect_single_onnx --executor cpp

REM 门禁（Linux 全量 / Windows 分 profile）
python tools\runtime_parity_gate.py certify --profile linux_full
python tools\runtime_parity_gate.py certify --profile win_default
```

### 5.4 不等价可接受项（须 manifest 明示）

- Python 独有：Ultralytics `.pt`（cpp 仅 ONNX）— 用 ONNX 导出对齐后测。
- `CAP-PATROL-HYBRID`、`CAP-POST-PROCESS`、`CAP-POSE-*`：cpp 可不实现，但 UI 须禁用或走 VIDEO 帧后。
- NVENC 自检回退策略差异：记 `L_stream` WARN，不 fail。

---

## 6. Evidence

### 上游能力定义（引用，不重复）

- `docs/runtime-parity/reports/01-python-realtime.md` — realtime CAP 全集与 §5 等价维度
- `docs/runtime-parity/reports/02-python-snap-patrol.md` — snap/patrol 调度与 §5.2 夹具建议
- `docs/runtime-parity/reports/03-cpp-runtime-baseline.md` — cpp 缺口表与 §5.1 可对齐基线
- `docs/runtime-parity/reports/04-video-absorb-surface.md` — 帧后分层验收与 Hook 契约

### 测试思想来源

- `rebekah-learn/docs/decisions/ORACLE_GATE.md` — 先录黄金、红清单收口
- `rebekah-learn/docs/decisions/PARITY_CERTIFY.md` — 分层 certify、禁止 smoke 充绿
- `rebekah-learn/golden/README.md` — `orig/` vs `rebuild/` 布局
- `rebekah-learn/testdata/oracle/manifest.json` — case + layers 冻结模式

### 代码锚点（测试场对接）

- `VIDEO/app/services/algorithm_task_daemon.py` — executor 分支（被测入口）
- `VIDEO/app/services/runtime_config_service.py:generate_runtime_ini` — cpp 配置生成
- `VIDEO/app/services/alert_hook_service.py:process_alert_hook` — `L_platform` 采样点
- `VIDEO/services/realtime_algorithm_service/run_deploy.py` — Python oracle 热路径
- `RUNTIME/src/pipeline/Pipeline.cpp` — cpp realtime 流水线
- `RUNTIME/src/pipeline/SnapScheduler.cpp` / `PatrolScheduler.cpp` — 调度 oracle 对照

---

## 附录 A：P0 用例一览（摘要）

| Case ID | 类型 | 核心 CAP |
|---------|------|----------|
| `rt_p0_detect_single_onnx` | realtime | 单模型检测框 |
| `rt_p0_alert_hook_roi` | realtime | 区域告警 + Hook |
| `rt_p0_heartbeat_lifecycle` | realtime | 心跳/生命周期 |
| `rt_p0_sam_same_image` | realtime | **SAM 同图分割协议** |
| `snap_p0_cron_slot` | snap | Cron 槽位 |
| `snap_p0_alert_payload` | snap | 告警 payload |
| `patrol_p0_pool_interval` | patrol | pool 间隔 |
| `patrol_p0_heartbeat_progress` | patrol | 巡检进度心跳 |
| `vid_p0_hook_kafka` | VIDEO | Hook→Kafka |
| `vid_p0_face_match_chain` | VIDEO | 人脸匹配链 |
| `e2e_p0_realtime_python_vs_cpp` | e2e | 60s 双 executor 对照 |
| `e2e_p0_sam_enabled` | e2e | SAM + 告警 |
| `perf_p0_realtime_latency` | perf | 延迟/资源基准 |

**Linux P0 共 14 case**；Windows `win_default` 跳过 cpp 对照类（`e2e_p0_realtime_python_vs_cpp` 仅 python 基准），**`rt_p0_sam_same_image` 仍必跑**（建立 SAM 协议基线）。
