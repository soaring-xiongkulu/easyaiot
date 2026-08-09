# Report: rebekah-learn Windows 与架构可迁移经验

- **Agent role:** rebekah-learn 精读调研 Agent（Windows / 架构 / 等价性工程）
- **Scope paths:** `F:/biofactory/rebekah-learn`（README、SMOKE_SPLIT、docs/learn、docs/decisions、docs/specs、CMake、tools）；对照 `F:/acme/RUNTIME/`（README、CMakeLists.txt，接口级）
- **Date:** 2026-08-09
- **Confidence:** high（决策文档与工具链已逐份核对；rebekah 商用边界按文档声明，未深挖 CompatibleLib 逆向实现）

## 1. Executive summary

`rebekah-learn` 是一套 **Windows 一等公民** 的学习向 C++ 分析引擎复刻仓：MSVC + CMake 单仓双目标（`rebekah_core` / `rebekah_media`），运行时依赖通过 **`vendor/` 快照 + 动态加载 DLL** 与自研骨架解耦，启停由 **Python supervisor** 按固定顺序管理多进程（ZLM → media → core → admin）。其最大工程资产不是「抄 rebekah 业务」，而是 **等价性门禁体系**：manifest 冻结输入 → 录黄金（oracle）→ 双端回放 → 分层 diff（A'/B/C/D）→ `certify` 唯一完成定义。

对照 EasyAIoT **C++ RUNTIME**：acme 已是 Linux 向单二进制（`Pull+Decode → FrameRing → Infer → Emit`），README 明示 **Windows 本轮不管**；CMake 无 `WIN32` 分支、ORT 仅拉 `linux-*` 包、VIDEO `ensure_runtime_cpp.sh` 非 Linux 直接跳过。rebekah 可直接迁移的是 **构建/依赖/启停工程模式** 与 **分层 parity 思想**；**不可**迁移 RebCompatibleLib、授权剥离、Ghidra 全量还原纪律及 rebekah 专有 HTTP 契约。

架构上，rebekah 的 **Scheduler → Worker（双线程帧环）→ WorkerFlowMode → Behaviour/Track → Alarm** 链路，为 acme 补齐 `CAP-TRACKING`、行为后处理（停留/越线/计数）、告警 payload 结构化、Mode 化流水线扩展提供了 **原则级蓝图**，但不应整仓替换 VIDEO 编排面。等价性应迁移为：**Python executor（oracle）vs C++ RUNTIME（candidate）** 同任务 ini / 同媒体 / 同 hook 的分层对照，落点以 **测试场（report 06）+ VIDEO ini 生成** 为主，Runtime 内核只暴露可观测 trace 与稳定 hook JSON。

---

## 2. Inventory / Findings

### 2.1 Windows 一等公民：构建 / 依赖 / 启停

| 主题 | rebekah-learn 做法 | acme RUNTIME 现状 | 可迁移性 |
|------|-------------------|-------------------|----------|
| **CMake / MSVC** | `cmake -G "Visual Studio 16 2019" -A x64`；`WIN32` 下 `WIN32_LEAN_AND_MEAN`、`NOMINMAX`、`_CRT_SECURE_NO_WARNINGS`、`ws2_32` | `CMakeLists.txt` 无 Windows 分支；`-pthread`/`dl` 硬编码 | **高**：加 `if(WIN32)` 与生成器文档即可起步 |
| **头文件 vendor** | `python tools/vendor_headers.py` 拉 cpp-httplib、nlohmann/json 到 `third_party/vendor` | cpp-httplib 在 `3rdparty/`；JSON 用 jsoncpp 链接 | **高**：统一「脚本拉公开头 + README 说明」 |
| **二进制 vendor 布局** | `vendor/core`（DLL/ZLM/字体）、`vendor/weight`（模型权重）；`SMOKE_SPLIT` 迁仓时重写配置路径 | `.deps/onnxruntime-linux-*`；无 Windows vendor 树 | **高**：`vendor/runtime/` 快照 ORT/OpenCV/FFmpeg **win-x64** + `deploy.env` 写 `PATH`/`DLL` 目录 |
| **动态加载** | `Compatible/*Loader.cpp`：`LoadLibraryA` + `SetDllDirectoryA`（同目录 CUDA/TRT 依赖） | 静态 `find_package` + `link_libraries` | **中**：商用 ORT/OpenCV 可静态/CMake target；**原则**是「重依赖不绑死编译期路径」 |
| **权重/模型路径** | 配置 `algorithmWeightDir`；Worker 将相对路径展开为绝对路径 | ini `model_path` 单文件；集群 Ceph | **高**：统一「配置根 + 相对权重展开」避免 cwd 漂移 |
| **进程启停** | `tools/rebekah_supervisor.py`：顺序 start、逆序 stop、`taskkill` 扫尾、TCP/HTTP 探活 | VIDEO daemon 起子进程；无 Windows supervisor | **高（测试场）**：本地 Win 联调用薄 Python supervisor 起 RUNTIME+SRS+mock VIDEO hook |
| **端口约定** | 原版 `:9004` / 复刻 `:19004` 双端口并行 diff | RUNTIME `control_port` per task | **高**：parity 时固定 oracle 端口 vs candidate 端口 |
| **构建产物路径** | `build/Release/rebekah_core.exe`（VS 多配置） | `build/RUNTIME`（单配置 Makefile 风格） | **中**：文档写清 `Release` vs 单配置差异 |

**对比句（构建）：** rebekah 把「能编过」和「能对照跑」拆成 **CMake 只编自研 exe + vendor 承载运行时 DLL**；acme RUNTIME 把「能编过」绑在 **Linux conda + apt 库 + ORT linux 包**，Windows 缺的是后一半而非 C++ 源码本身。

### 2.2 架构可吸收（原则级，非整仓替换 VIDEO）

| rebekah 概念 | 职责 | 映射 acme 缺口（CAP ID） | 吸收方式 |
|--------------|------|--------------------------|----------|
| **CoreScheduler** | `controlCode → Worker` 生命周期；不碰帧 | VIDEO 已有任务 daemon；RUNTIME 单任务单进程 | **不替换 VIDEO**；RUNTIME 内可类比「单 control 的 Worker」 |
| **Worker 双线程** | `pullLoop` + `processLoop`；`XcFramePool` 有界丢弃 | `CAP-PIPELINE-PULL/RING` 已有三线程 Pipeline | **对齐**：pull/decode 与 infer/emit 解耦已有；可借鉴 **满池计数与 drop 可观测** |
| **WorkerFlowMode 1–9** | 工厂决定 Detect/Classify/Feature/Track 串序 | `CAP-MULTI-MODEL`、检测+分类+特征组合 | **原则**：用「模式表」扩展流水线，而非堆 if-else；首阶段只需 realtime 的 Mode1 等价 |
| **TrackDeepSort** | Mode2/7/8/9；特征+关联 | **`CAP-TRACKING` 缺失** | **cpp**：infer 后插 Tracker 接口；输出 `track_id` 进 hook/overlay |
| **Behaviour + PostProcess*** | `wayCode` → Area/Stay/Count/Cross…；`fired`/`happenDesc` | 区域过滤仅有 `CAP-REGION-FILTER`；无停留/越线/计数行为 | **cpp** 帧内：在 emit 前加 **Behaviour 链**；复杂帧后仍留 VIDEO |
| **XcAlarm** | `minInterval`、HTTP(S) payload | `CAP-ALERT-HOOK` + `CAP-ALERT-COOLDOWN` | **对齐 payload 字段** + 冷却；学习 rebekah「正/负例均比关键字段」 |
| **DecisionTrace** | 管线决策序列可 dump | 无 | **测试场**：RUNTIME 可选 `RUNTIME_DUMP_DECISION` 环境变量输出 JSON trace |
| **Admin FPS 上报** | `adminReporter` 周期 POST | `CAP-HEARTBEAT` 已有 VIDEO 契约 | 保持 VIDEO 心跳，不引入 rebekah Admin |

**帧管线对照（rebekah vs acme）：**

```text
rebekah:  Pull → FramePool → Mode.processFrame → Behaviour → Alarm/Push
acme:     Pull+Decode → FrameRing → Infer(YOLO) → ResultRing → Emit(hook)
缺口:     ─────────────────── Track ─ Behaviour(wayCode) ─ 结构化 alarm 字段 ─
```

### 2.3 等价性工程（rebekah → Python vs C++ RUNTIME）

rebekah 门禁栈（权威：`ORACLE_GATE.md`、`PARITY_CERTIFY.md`、`REPLACEABILITY.md`）：

```text
testdata/oracle/manifest.json     # 冻结：start body、媒体、期望层
        ↓ record-orig（原版进程 + Frida 采样）
golden/orig/<case>/               # 黄金：detect/flow/behaviour/alarm/...
        ↓ run|certify（复刻同输入）
golden/rebuild/<case>/
        ↓ 分层 diff
logs/parity_certify_report.json   # 红清单 = 唯一待办
```

| rebekah 层 | 产物 | 判定要点 | 迁移到 acme（Python oracle → C++ candidate） |
|------------|------|----------|-----------------------------------------------|
| **L_http** | start/stop meta | code/msg 精确 | 任务启停：ini 生成 + `GET /health` 字段 |
| **L_flow** | `flow_trace.json` | 规范化算子序完全相等 | `infer_started` → `nms` → `region_filter` → `track_update` → `alarm_allow` |
| **L_detect** | `detect.json` | IoU 配对 + class_id | 同帧 bbox 集合；阈值进 `thresholds.json` |
| **L_classify / L_feat** | 分类/特征向量 | 配对后 id 或 cosine | 若启用多模型/SAM 再扩展 |
| **L_track** | `track.json` | id 稳定映射 / 几何×id | **`CAP-TRACKING` 门禁核心** |
| **L_behaviour** | `behaviour.json` | `fired`/`wayCode`/… | 行为后处理上线后纳入 |
| **L_alarm** | `alarm.json` | hook payload 结构硬比 | 对齐 `POST /video/alert/hook` JSON（strip 时间戳/uuid） |
| **L_push / L_facedb** | 推流/人脸库 | rebekah 特有 | acme：可选 `L_rtmp_meta` 或 **drop**（由 VIDEO 测） |

**命令映射建议（acme 测试场）：**

| rebekah | acme 对等物 |
|---------|-------------|
| `oracle_gate.py doctor` | 校验 manifest、媒体、ini 模板、阈值文件 |
| `record-orig --case X` | 起 **Python executor** 同 task_id，录 hook + 检测 dump |
| `run --case X` | 起 **C++ RUNTIME** 同 ini，录同等 artifact |
| `certify` | 全层绿才宣称「executor 可替换」；`run` 绿 ≠ 可替换 |
| `diff_harness.py` | 薄 HTTP 对照（health、控制口）；深度以 certify 为准 |

**黄金样本来源：** rebekah 用 `golden/` + `testdata/` + RTSP loop（ZLM）；acme 应用 **标准测试场短视频 + 固定 ini**（见 `runtime-parity` 规划 report 06），避免依赖 rebekah vendor 权重。

**阈值与禁止项（必继承）：**

- 禁止静默降阈值、几何豁免、smoke-only 充绿（rebekah D14 / PARITY_CERTIFY §7）。
- 禁止「C++ 少字段仍报等价」—— 对应 acme 现状：`generate_runtime_ini` 未写字段即 **parity 债**，不是 C++ 通过。
- 开发门禁 `run` vs 发布门禁 `certify` 分离（rebekah `ORACLE_GATE.md` §1）。

### 2.4 不可直接搬进商用产品的部分

| 类别 | 内容 | 原因 |
|------|------|------|
| **RebCompatibleLib.dll** | Xcc 推理、硬解编 | 私有/授权；学习仓 **dynload 借力**，商用须 ORT/自研引擎（acme 已走 ONNX） |
| **Ghidra 全量反编译树** | `docs/evidence/ghidra/**` | 学习证据；不可作发行依赖 |
| **原版 rebekah 安装包 DLL 快照** | `vendor/core` 整包 | 许可证与再分发限制；商用需自有依赖栈 |
| **授权绕过** | `getAuthInfo` 恒 true、不写 `.license` | 仅学习约束；产品须走正式授权 |
| **rebekah HTTP API 面** | `/api/control/start` JSON 形态 | 与 EasyAIoT VIDEO/ini 契约不同；只借 **分层思想**，不借路由 |
| **Admin / ZLM 1:1 复刻** | REPLACEABILITY 永久非目标 | VIDEO 已承担编排与 SRS |
| **Frida 钩原版 EA** | oracle `record-orig` | 生产门禁改为 **Python 进程为 oracle**（合法、可 CI） |
| **「无模型 passthrough」联调路径** | rebekah Detect 空结果继续 PP | 学习联调技巧；商用须 **显式降级标志 + 告警**（D14 精神） |

**借力 vs 商用边界一句话：** 可学 **Loader 模式、SetDllDirectory、vendor 目录契约、supervisor 启停、parity 分层**；不可学 **把 RebCompatibleLib 当生产推理栈** 或 **携带原版 vendor 再分发**。

### 2.5 Placement hint（经验落点）

| 能力 / 经验 | 建议落点 | 理由 |
|-------------|----------|------|
| MSVC CMake、`WIN32` 编译定义、`install_windows` | **构建系统** | 不改业务即可解锁 Win 编译 |
| `vendor_headers.py` 式公开依赖拉取 | **构建系统** | 减少 Windows 上找头文件摩擦 |
| `vendor/` + `deploy.env` DLL 路径 | **构建系统 / 部署** | 与 Linux `deploy.env` 对称 |
| `rebekah_supervisor.py` 启停与探活 | **测试场** | 本地 Win 多进程联调；生产仍 VIDEO daemon |
| manifest + golden + `oracle_gate` 分层 | **测试场** | 本阶段最大工程；驱动 ini/字段补齐 |
| `thresholds.json`、红清单 JSON 报告 | **测试场** | CI 可读；禁止口头「感觉一致」 |
| Worker 双环 + FramePool 丢弃策略 | **Runtime 内核** | 与现有 FrameRing 对齐、可观测 |
| WorkerFlowMode 工厂 / Mode 表 | **Runtime 内核** | 渐进扩展多模型与 track，不推翻 Pipeline |
| TrackDeepSort 类接口 | **Runtime 内核** | 直接服务 `CAP-TRACKING` |
| Behaviour / PostProcess 链 | **Runtime 内核**（帧内）+ **video**（重帧后） | 停留/越线/计数宜帧内；Kafka 匹配仍 VIDEO |
| Alarm payload 字段对齐 | **Runtime 内核** + **测试场** | hook JSON 由 cpp 产出；门禁在测试场 diff |
| DecisionTrace dump | **Runtime 内核**（可选编译开关） | 仅 parity/debug；默认关 |
| RebCompatibleLib / Xcc | **drop** | 商用用 ORT + DirectML/CUDA |
| rebekah Admin / 授权 | **drop** | VIDEO 已有 |

---

## 3. Placement hint（Capability ID 视角）

| Capability ID | 建议落点 | 理由 |
|---------------|----------|------|
| `CAP-TRACKING` | **cpp** | rebekah Mode2/7 TrackDeepSort 证明 track 属帧内；门禁用 L_track |
| `CAP-REGION-FILTER` | **cpp**（已有） | 扩展为 Behaviour 前置几何 |
| `CAP-ALERT-HOOK` | **cpp** 发送 + **测试场** diff | rebekah L_alarm 硬比 payload |
| `CAP-ALERT-COOLDOWN` | **cpp**（已有） | 对齐 `minInterval` 语义 |
| `CAP-MULTI-MODEL` | **cpp** | WorkerFlow 串行多 session；ini 需先由 VIDEO 写入 |
| `CAP-OVERLAY-QUEUE` | **cpp** 或 **video** | rebekah 推流在 Worker 内同步；acme 可简化 |
| `CAP-MOTION-GATE` | **cpp** | infer 前；与 rebekah Mode5「无 Detect 仅 Behaviour」不同但可共存 |
| `CAP-FACE-MATCH` / `CAP-PLATE-MATCH` | **video** | rebekah faceDb 独立 media；acme 保持队列+HTTP |
| `CAP-GPU-DIRECTML` | **构建系统** + **cpp** | Windows 推理 EP；对应 rebekah CUDA DLL 路径布局经验 |
| `CAP-TASK-*` / 心跳 / ini | **video** + **测试场** | 编排不在 RUNTIME 复制 rebekah Scheduler |
| Parity manifest / certify | **测试场** | Python executor 为 oracle 的唯一可持续商用路径 |

---

## 4. Gaps / Risks

1. **目标不同：** rebekah 追求替换 **rebekah_core**；acme 追求替换 **Python executor**。HTTP 面与配置载体（JSON start vs ini）皆不同，不可照搬 manifest case builder，需重写 `easyaiot_oracle` 适配层。
2. **Windows 推理 EP：** rebekah 借 TRT/CUDA DLL；acme 需 **ORT DirectML 或 CUDA on Windows**，与 `SetDllDirectory` 经验可组合，但无 RebCompatibleLib 捷径。
3. **跟踪与行为债：** acme 报告 03 已列 `CAP-TRACKING` 缺失；rebekah 证明 track/behaviour 必须进入 **certify 硬层**，否则「主推理绿」仍不可宣称 executor 等价。
4. **静默能力丢失：** acme `generate_runtime_ini` 未写字段与 rebekah D14 反对的「静默缩小行为面」同构；parity 应先 **债表化缺失字段**，再修 C++。
5. **CI 成本：** rebekah `record-orig` 依赖原版 exe + Frida；acme 应用 **Python 录一次、多分支复用 golden**，降低 Windows CI 负担。
6. **法律/合规：** 任何从 rebekah `vendor/` 复制的二进制 **不得** 进入 acme 发行物；仅复用工程结构与脚本模式。

---

## 5. Equivalence notes

### 5.1 怎样才算「Python runtime vs C++ RUNTIME 表现一致」

采用 rebekah **非比特级、分层硬对齐** 定义，映射如下：

| 块 | acme 含义 | 最低发布线（MVP） | 完整线（certify） |
|----|-----------|-------------------|-------------------|
| **A'** | 帧内推理 | 同媒体同 ini：检测框 IoU≥τ、class 一致；`GET /health` 字段 | + 多模型序；+ track 关联（若 `tracking_enabled`） |
| **B** | 行为 + 告警 | 区域过滤结果一致；hook JSON 关键字段一致（strip volatile） | + cooldown 时序；+ `alert_class_names` 过滤 |
| **C** | 帧后 / 推流 | realtime：心跳 URL 200；可选 RTMP 元数据 | snap/patrol 调度对齐；face/plate 仍由 VIDEO 测 |
| **D** | 决策序（可选） | Pipeline 阶段计数：pull/infer/emit | 规范化 `flow_trace` 与 Python 侧等价 |

**夹具需求：**

- `testdata/easyaiot/manifest.json`：task_type、ini 片段、媒体路径、期望层。
- `golden/python/<case>/`：Python executor 录 `detections.json`、`alerts.json`、`heartbeat.json`。
- `golden/cpp/<case>/`：C++ RUNTIME 同输入回放产物。
- `thresholds.json`：detect IoU、track 映射、cosine、时间戳忽略列表（复用 `diff_harness.strip_volatile` 思想）。

**不算一致：**

- 仅 `run_smoke` / 单帧肉眼看框；
- C++ 无 tracking 但 Python 有 track_id；
- ini 未下发字段导致 Python 走默认、C++ 走另一默认且无告警。

### 5.2 与 rebekah 差异的有意简化

- **无 Frida：** Python 侧用显式 hook 日志或测试桩录 golden。
- **无双端口原版 exe：** oracle 固定为 `executor=python` 进程。
- **无 RebCompatibleLib：** L_detect 数值阈针对 ONNX 输出，允许 τ 与 rebekah 不同，但 **两侧须同 τ**。

---

## 6. Evidence

### rebekah-learn

- `README.md` — VS2019 x64 构建、`oracle_gate` / `diff_harness` 入口
- `SMOKE_SPLIT.md` — `vendor/core` + `vendor/weight` 快照与路径重写
- `docs/learn/00-project-composition.md` — 四进程拓扑与 supervisor 启停顺序
- `docs/learn/01-core-architecture.md` — Scheduler/Worker/Mode/Behaviour/Alarm 协作
- `docs/decisions/STRATEGY.md` — D05 oracle、D09 公共库不自研、D14 禁止静默降级
- `docs/decisions/REPLACEABILITY.md` — `certify` 唯一完成定义 A'+B+C
- `docs/decisions/PARITY_CERTIFY.md` — L_http…L_track、L_behaviour、L_alarm 层规格
- `docs/decisions/ORACLE_GATE.md` — record-orig → run → certify 流水线
- `docs/decisions/SUPERVISOR.md` — ZLM→media→core 启动序与 `taskkill` 扫尾
- `docs/decisions/D14-no-silent-downgrade.md` — libcurl HTTPS 与债表纪律
- `docs/specs/worker-flow-modes.md` — Mode1–9 算子顺序
- `docs/specs/frame-pipeline.md` — Pull→Pool→Mode→Behaviour→Alarm
- `docs/specs/behaviour-postprocess.md` — wayCode → PostProcess 映射
- `CMakeLists.txt:77-84` — `WIN32` 编译定义与 `ws2_32`
- `src/Compatible/XccLoader.cpp:17-31` — `SetDllDirectoryA` + `LoadLibraryA`
- `src/main.cpp:37-73` — FFmpeg/OpenCV/Curl/Xcc 按配置 dynload
- `tools/rebekah_supervisor.py:27-34` — 进程名表与 PID 状态文件
- `tools/oracle_gate.py:81-88` — MANIFEST、双 URL、CERTIFY_REPORT 路径
- `testdata/oracle/manifest.json` — case 层声明（detect/track/behaviour/alarm/decision）
- `tools/diff_harness.py:24-43` — volatile 字段剥离

### acme RUNTIME（对照）

- `RUNTIME/README.md:59-60` — Windows「本轮不管」
- `RUNTIME/README.md:103` — `Pull+Decode → FrameRing → Infer → ResultRing → Emit`
- `RUNTIME/CMakeLists.txt:12-14` — `-pthread` 无 `WIN32` 分支
- `RUNTIME/CMakeLists.txt:101-102` — `pthread`、`dl` 链接
- `docs/runtime-parity/reports/03-cpp-runtime-baseline.md` — `CAP-TRACKING` 缺失、ini 静默丢失、Windows 阻滞表

---

## 附录 A：可迁移 Top 10 清单

| # | 经验 | Placement |
|---|------|-----------|
| 1 | **分层 parity 门禁**：manifest → 录 Python golden → C++ 回放 → A'/B/C diff → 仅 `certify` 可宣称 executor 等价 | 测试场 |
| 2 | **红清单驱动开发**：`parity_certify_report.json` 唯一待办；禁止 `run` 绿即收口 | 测试场 |
| 3 | **Windows CMake 一等公民**：`WIN32` 宏、`ws2_32`、VS 多配置 `Release` 路径文档化 | 构建系统 |
| 4 | **vendor 目录 + deploy.env**：运行时 DLL/ORT/OpenCV/FFmpeg 与 exe 分离，可复制快照 | 构建系统 / 部署 |
| 5 | **`SetDllDirectory` / 同目录依赖解析**：Windows 加载 ORT/CUDA 附属 DLL | 构建系统 / Runtime |
| 6 | **Python supervisor 薄启停**：顺序起依赖、逆序停、探活、无孤儿进程（Win 联调） | 测试场 |
| 7 | **双线程帧环 + 有界池**：pull/decode 与 process 解耦；满池 drop 可计数 | Runtime 内核 |
| 8 | **WorkerFlow 工厂 / Mode 表**：扩展 Detect→Feature→Track 而不推翻 Pipeline | Runtime 内核 |
| 9 | **Behaviour 链 + 结构化 Alarm**：wayCode 后处理与 hook payload 硬比门禁 | Runtime 内核 + 测试场 |
| 10 | **D14 反静默降级**：ini 未映射字段 = parity 债；禁止 C++ 悄悄少能力 | 测试场 + VIDEO ini 生成 |
