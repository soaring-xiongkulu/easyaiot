# RUNTIME Python→C++/VIDEO 能力收归 + Windows 对等 Implementation Plan

> **状态：FINAL（2026-08-09）** — 产品拍板已锁定；交接见 [`HANDOFF.md`](./HANDOFF.md)。  
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 以标准测试场上的**功能表现一致**为唯一完成定义，将 `executor=python` 的算法热路径能力（**除算法任务 SAM 外全部保留**）收归到 **C++ RUNTIME（帧内）+ VIDEO（帧后）**，含 **目标追踪** 与 **Windows 可编译可运行**，最终删除 Python `*_algorithm_service`（不含 `AI/`；`AI/` 标注 SAM 保留）。

**Architecture:** Python realtime/snap/patrol 为 **行为 oracle**；C++ RUNTIME 负责拉流/解码/推理/追踪/门控/叠框推流/结构化 emit；VIDEO 在 alert hook 后补齐人脸/车牌/后处理/Kafka/通知；rebekah-learn 只迁移 **MSVC+vendor 构建** 与 **分层 certify 门禁思想**，不引入私有 CompatibleLib。

**Tech Stack:** C++17、ONNX Runtime（Linux CUDA EP / Windows DirectML 或 CUDA）、FFmpeg、OpenCV、VIDEO Flask 编排、`tools/runtime_parity_gate.py`、MediaMTX/ffmpeg 标准 RTSP 夹具。

## Global Constraints

- 评判标准：**功能表现一致**（非 API 通即可）；性能允许 C++ 更好或略降（默认见 `reports/06`，产品可改阈值）。
- Python `*_algorithm_service` 与 **`AI/` 模块**严格区分；删的是前者。
- 禁止静默降级：ini 未映射字段 = parity 债。
- **算法任务路径不考虑 SAM**（已产品否决）；`AI/` 标注 SAM 必须保留。
- **业务范围：全要**（测试场、Windows、追踪、匹配、门控、调度精细对齐、多模型、RTMP/叠框表现等）— 详见 `CAP-BUSINESS-DECISIONS.md` / `HANDOFF.md`。
- 热路径模型：**仅 ONNX**（`.pt` 经导出满足，不内嵌 ultralytics）。
- 商用禁止依赖 rebekah `RebCompatibleLib` / 原版 vendor DLL 再分发。
- 调研基线：`docs/runtime-parity/reports/01`–`06`（算法任务 SAM 强制项以 HANDOFF 否决为准）。

## 调研结论冻结（决策）

### A. 能力落点总表（产品 FINAL）

| 落点 | CAP（代表） | 决策 |
|------|-------------|------|
| **C++ 必做** | YOLO/ONNX、多 ONNX、区域、抽帧、告警图+hook、心跳、RTMP/叠框表现、重连、**tracking**、**motion_gate**、alert_class、face/plate **类过滤**、snap Cron（东八区秒级）、patrol pool/rotate/**hybrid**、国标源、NVENC 自动降档、detect_conf 语义、`POST /stop` | **要** |
| **VIDEO 吸收（帧后触发）** | **FACE/PLATE MATCH**、POST_PROCESS、POSE、Kafka/通知、布防字段消费、抓拍空间协同、SRS/告警图清理、任务热更新/模型分发 | **要**（从 python 触发上收） |
| **等价测试场** | certify 全层 | **要**（不可砍） |
| **Windows RUNTIME** | MSVC + vendor + VIDEO 拉起 | **要**（不可砍） |
| **明确砍掉** | **算法任务 SAM 补充** | **不要**；保留 `AI/` 标注 SAM |
| **工程降级（非砍业务）** | 热路径不跑 `.pt` | 导出 ONNX 对齐 |
| **UI** | cpp 假开关治理 | 按 CAP 门禁 / 标明帧后生效 |

### B. Windows

1. CMake `WIN32` + MSVC、POSIX 垫片。  
2. `vendor/runtime/win-x64`：ORT（DirectML 或 CUDA）、OpenCV、FFmpeg + `SetDllDirectory`/`deploy.env`。  
3. VIDEO 用 exe 拉起。  
4. 门禁：`win_default` → `win_cpp`。

### C. 等价工程 — 最先开工

```text
manifest → record-python（oracle）→ run-cpp / platform → certify
仅 certify 全绿可删 Python runtime
```

分层：`L_exec` → `L_platform` → `L_e2e` + `L_perf`。无算法任务 SAM 用例。

---

## File / Directory Map

| 路径 | 职责 |
|------|------|
| `docs/runtime-parity/reports/01`–`06` | 已冻结调研 |
| `docs/runtime-parity/PLAN.md` | 本计划 |
| `docs/runtime-parity/testbed/` | mock hook、compose、操作手册 |
| `docs/runtime-parity/HANDOFF.md` | **交接入口（FINAL 范围）** |
| `testdata/runtime-parity/` | manifest、thresholds、media、fixtures、golden |
| `tools/runtime_parity_gate.py` | doctor / record-python / run / certify |
| `RUNTIME/` | 帧内能力 + Windows 构建 |
| `VIDEO/app/services/alert_hook_service.py` 等 | 帧后触发吸收 |
| `VIDEO/services/*_algorithm_service/` | 最终删除（仅在 certify 通过后） |
| `WEB/.../AlgorithmTaskModal.vue` | cpp 能力门禁 |

---

## Phase 0 — 测试场骨架（先于功能开发）

### Task 0.1: 落盘测试场目录与阈值

**Files:**
- Create: `testdata/runtime-parity/{manifest.json,thresholds.json,media/README.md,fixtures/tasks/.gitkeep,golden/.gitkeep}`
- Create: `docs/runtime-parity/testbed/README.md`

- [ ] 按 `reports/06` §2.1 创建目录与空 manifest 骨架（含 P0 case id 列表）
- [ ] 写入默认 `thresholds.json`（IoU、告警容差、perf 倍率；标注「待产品拍板」）
- [ ] media README：≤5MB 样本策略 + `scripts/fetch_parity_media.sh` 约定
- [ ] Commit：`docs: scaffold runtime-parity testbed`

### Task 0.2: Mock Hook + RTSP relay

**Files:**
- Create: `docs/runtime-parity/testbed/mock_alert_hook.py`
- Create: `docs/runtime-parity/testbed/docker-compose.media.yml`

- [ ] Mock hook：记录 POST body/时间戳/图片路径到 `golden/video/<case>/`
- [ ] compose：MediaMTX 或 ffmpeg 将 MP4 转为稳定 RTSP
- [ ] Commit：`test: add parity mock hook and media relay`

### Task 0.3: Gate CLI（doctor / record-python）

**Files:**
- Create: `tools/runtime_parity_gate.py`
- Create: `tools/runtime_parity/`（diff 小模块可拆）

- [ ] 实现 `doctor`：检查 manifest、媒体、阈值、mock 端口
- [ ] 实现 `record-python`：按 case 起 python executor（或直连已有 VIDEO 任务），录 `detect/alarm/lifecycle/track/perf`（**无**算法任务 SAM）
- [ ] 输出 `logs/runtime_parity_report.json` 骨架
- [ ] 跑通至少 1 个 P0：`rt_p0_detect_single_onnx` 的 python 录制
- [ ] Commit：`test: runtime_parity_gate record-python MVP`

### Task 0.4: Gate CLI（run-cpp / certify）

- [ ] `run --executor cpp`：同 fixture 生成 ini、起 RUNTIME、采同样 artifact
- [ ] `certify`：分层 diff；红清单唯一待办；`run` 绿 ≠ 可替换
- [ ] Windows profile：`win_default` 可先跳过 cpp 对照，平台 P0 仍跑；`win_cpp` 就绪后开双端
- [ ] Commit：`test: runtime_parity certify MVP`

**Phase 0 出口：** `doctor` 绿；至少 3 个 P0 有 python golden；cpp 对照可跑（即便大量 fail）。

---

## Phase 1 — Windows RUNTIME 可编译可运行

### Task 1.1: CMake / POSIX 垫片

**Files:**
- Modify: `RUNTIME/CMakeLists.txt`
- Modify: `RUNTIME/src/Manage.cpp`（信号）
- Modify: 含 `unistd.h` / `localtime_r` 的源文件

- [ ] `if(WIN32)`：MSVC flags、`ws2_32`、去掉强制 `-pthread`
- [ ] Windows 信号处理 / 时间函数垫片
- [ ] VS2019/2022 x64 Release 产出 `RUNTIME.exe`
- [ ] Commit：`build: enable MSVC build for RUNTIME`

### Task 1.2: Windows vendor + ORT EP

**Files:**
- Create: `RUNTIME/scripts/fetch_deps_windows.ps1`（或 py）
- Create: `RUNTIME/vendor/win-x64/README.md`
- Modify: `Yolov11Engine.cpp`（DirectML 或 CUDA-on-Windows 分支）

- [ ] 文档化 ORT win 包布局与 `SetDllDirectory`
- [ ] CPU 路径先绿；再 GPU EP（DirectML 优先桌面，CUDA 可选）
- [ ] `deploy.env` Windows 对称字段
- [ ] Commit：`build: windows ORT vendor and EP fallback`

### Task 1.3: VIDEO 在 Windows 拉起 cpp

**Files:**
- Modify: `VIDEO/app/services/algorithm_task_daemon.py`
- Modify: `VIDEO/app/services/runtime_config_service.py`
- Create: `VIDEO/scripts/ensure_runtime_cpp.ps1`（或扩展 sh 检测）

- [ ] 解析 `RUNTIME.exe` 路径；生成 ini；子进程启停
- [ ] 门禁 `win_cpp`：`rt_p0_heartbeat_lifecycle` + `rt_p0_detect_single_onnx` 双端可跑
- [ ] Commit：`feat: launch cpp RUNTIME on Windows`

**Phase 1 出口：** Windows 上 cpp 任务能拉流推理并 hook（功能可比 Linux 少，但门禁可采样）。

---

## Phase 2 — 契约与静默丢失清零（D14）

### Task 2.1: ini 字段全集映射

**Files:**
- Modify: `VIDEO/app/services/runtime_config_service.py`
- Modify: `RUNTIME/src/Config.h` / `ConfigParser.cpp`

- [ ] 将 tracking / motion_gate / alert_class / face·plate detection flags / sam flags / multi model paths / patrol hybrid·focus 写入 ini（即便尚未实现，也要能解析并打日志）
- [ ] 未实现能力：启动时 `LOG(WARNING) unsupported cap=...` + health 列出
- [ ] Commit：`fix: map AlgorithmTask fields into RUNTIME ini`

### Task 2.2: Hook payload 对齐

**Files:**
- Modify: `RUNTIME/src/Detech.cpp`（告警 JSON）
- Modify: `VIDEO/app/services/alert_hook_service.py`（DB 回填 face/plate flags）

- [ ] cpp 带 `face_detection_enabled`/`plate_detection_enabled` 或 VIDEO 从 DB 补齐（二选一写死）
- [ ] 时间戳/correlation 规范化进 certify `L_alarm`
- [ ] P0：`rt_p0_alert_hook_roi` certify 字段集合绿
- [ ] Commit：`fix: align cpp alert hook payload with python`

---

## Phase 3 — VIDEO 吸收帧后触发（删 Python 前置）

### Task 3.1: Alert-hook 触发人脸/车牌匹配

**Files:**
- Modify: `VIDEO/app/services/alert_hook_service.py`
- Reuse: `face_matching_kafka_service.py` / `plate_matching_kafka_service.py`

- [ ] 当任务启用 matching：用 hook `image_path` + detections 入队（等价 python `try_send_*_for_frame`）
- [ ] P0：`vid_p0_face_match_chain` 在 **仅 cpp 执行器** 下绿
- [ ] Commit：`feat: trigger face/plate matching from alert hook`

### Task 3.2: 后处理 / 姿态投递

**Files:**
- Modify: `alert_hook_service.py` 或新建 `executor_post_alert_orchestrator.py`
- Reuse: `post_process_sink_client.py`

- [ ] cpp 告警后 `enqueue_post_process_request`（开关来自 DB）
- [ ] P1 platform cases 绿
- [ ] Commit：`feat: enqueue post-process from cpp alerts`

### Task 3.3: UI 假开关治理

**Files:**
- Modify: `WEB/src/views/camera/components/AlgorithmTask/AlgorithmTaskModal.vue`

- [ ] cpp 模式：帧内未实现 CAP 禁用；帧后由 VIDEO 生效的开关保留并改 help
- [ ] Commit：`fix: gate algorithm task UI by executor capabilities`

---

## Phase 4 — C++ 帧内能力补齐（按 certify 红清单驱动）

> 顺序以 `parity_report` 红项为准；下列为预期顺序。

### Task 4.1: 检测基线硬化

- [ ] 多 ONNX 串联或明确「仅首模型」产品语义并改 UI
- [ ] `detect_conf` / 引擎阈值语义与 Python 对齐
- [ ] alert_class 过滤
- [ ] P0 detect/alarm certify 绿
- [ ] Commit：`feat: harden cpp detection parity`

### Task 4.2: motion_gate + tracking

- [ ] 移植轻量 MotionGate（对照 `VIDEO/app/utils/motion_gate.py`）
- [ ] Tracker 接口 + `track_id` 进 overlay/hook（思想可参考 rebekah Track，实现用公开算法）
- [ ] P1：`rt_p1_motion_gate`、`rt_p1_tracking_stable`
- [ ] Commit：`feat: cpp motion_gate and tracking`

### Task 4.3: snap/patrol 调度对齐

- [x] Cron 东八区 6 段 / 槽位语义对齐 `cron_utils`
- [x] patrol hybrid + focus
- [x] snap-space / patrol 进度心跳字段对齐（能 VIDEO 做的不进 C++）
- [x] P0 snap/patrol schedule cases 绿
- [x] Commit：`feat: align snap/patrol schedulers with python`

### Task 4.4: SAM 路径 — **已取消**

- [x] 产品否决：算法任务 / Runtime 对等 **不做 SAM**；测试场删除 SAM P0；保留 `AI/` 标注 SAM
- [ ] （可选清理）UI/DB `sam_supplement_*` 从算法任务表单隐藏或标注废弃——不阻塞主线

### Task 4.5: RTMP / overlay 表现门槛

- [x] 不以双队列 1:1 复刻为阻塞；以 overlay 可见延迟阈值 + ffprobe 为 P1
- [x] Commit：`feat: cpp overlay/rtmp parity thresholds`

---

## Phase 5 — 全量 certify 与删除 Python runtime

### Task 5.1: 全 P0+P1 certify（Linux + win_cpp）

- [x] `certify --profile linux_full` 全绿
- [x] `certify --profile win_cpp` 全绿（或文档化豁免清单经产品签字）
- [x] 性能列不劣于 `thresholds.json`
- [x] 产出 `docs/runtime-parity/CERTIFY_STATUS.md` 附报告哈希

### Task 5.2: 默认只留 cpp + 删除 python 服务

**Files:**
- Modify: launcher/daemon/models 默认 executor
- Delete or quarantine: `VIDEO/services/realtime_algorithm_service/` 等三目录（可先移 `_retired/` 一版）
- Modify: README / VIDEO README

- [x] 代码路径无法再选 `executor=python`（G-5.4）
- [x] CI：本仓无独立 python executor job；parity gate 仍为本地 CLI（见 PHASE_5_GATE）
- [x] Quarantine 三服务 → `VIDEO/services/_retired/`（编排审查 dry-run 后 `--execute`）
- [x] Commit：`feat: remove python algorithm runtime executors`

---

## 工作量与难度（基于调研的客观再估）

| 块 | 难度 | 体量感 | 备注 |
|----|------|--------|------|
| Phase 0 测试场 | 中 | **大（本阶段最大工程之一）** | 夹具、录制、分层 diff；对齐 rebekah certify 纪律 |
| Phase 1 Windows | 中高 | 中大 | 工程债清晰，有 rebekah 可抄 |
| Phase 2–3 契约+VIDEO 吸收 | 中 | 中 | 性价比最高的「能力不丢」 |
| Phase 4 帧内补齐 | 中高 | 大 | tracking/SAM/调度最耗对齐时间 |
| Phase 5 删除 | 低 | 小 | 被 certify 门禁挡住即可安全删 |

**完全等价（已砍算法任务 SAM；其余业务全要，含追踪/测试场/Win）** 粗估：**约 2～4 人月**（熟手；含测试场与双端回归）。  
**不可压缩点：** 测试场、追踪、Windows、调度精细对齐、匹配上收与行为 diff。  
**工程约定：** 热路径仅 ONNX（不内嵌 `.pt`）。

---

## 交接

实施从 **Phase 0** 开始。范围与拍板以 [`HANDOFF.md`](./HANDOFF.md) 为准。规划侧已收尾。

---

## 执行纪律

1. **红清单驱动：** 只修 `runtime_parity_report.json` 红项；禁止无 case 的「感觉对齐」。
2. **先测后改：** 每个 CAP 先有 failing case，再实现。
3. **双轨录制：** 改 C++ 或 VIDEO 后必须 `record-python` 未漂（防 oracle 漂移）。
4. **子代理实施时：** 一次一块 Phase/Task；改完跑对应 case。

## 参考

- `docs/runtime-parity/reports/01-python-realtime.md`
- `docs/runtime-parity/reports/02-python-snap-patrol.md`
- `docs/runtime-parity/reports/03-cpp-runtime-baseline.md`
- `docs/runtime-parity/reports/04-video-absorb-surface.md`
- `docs/runtime-parity/reports/05-rebekah-windows-lessons.md`
- `docs/runtime-parity/reports/06-equivalence-testbed.md`
