# Part2 剩余能力决策细则（假设 Wave-A 已完成）

> **前提：** Wave-A（人脸 ORT + milvus-sdk-java + 车牌 OCR Java、关掉 face/plate Python CLI）**已完成**。  
> **Wave-A 实绩（2026-08-12）：** 本机闭环 **PASS**（`f29cb6ab`）；报告 `.superpowers/sdd/briefs/part2-wave-a-report.md`；门控轻核可采信。  
> **目的：** 列出之后仍缺什么；哪些能靠第三方 SDK/开源；哪些搜完仍无「拿来即用」；便于逐项决策。  
> **对照：** 代码盘点 `video-java` + 公开检索（ORT / milvus / YOLO-pose Java / ONVIF / RapidOCR / HyperLPR）。  
> **地图：** [PART2_CAPABILITY_MAP.md](./PART2_CAPABILITY_MAP.md) · 执行包 [PART2_WAVE_A_PACK.md](./PART2_WAVE_A_PACK.md)

---

## 讨论纪要（2026-08-12）— **最终锁定**

> **终稿方案：** [PART2_FINAL_PLAN.md](./PART2_FINAL_PLAN.md)

### Wave-A

| 项 | 结论 |
|----|------|
| A0–A6 | **PASS**（`f29cb6ab`） |
| COMPLETE / 删 Python | **禁止**（直至 FINAL 方案 W1–W3 验收+签字） |

### 现在做（主动）

| ID | 结论 |
|----|------|
| **R-01 + R-02** | **做：** 姿态 ORT Java，收掉 pose Python CLI |
| **R-03** | **做：** 巡检挂 C++ RUNTIME `PatrolScheduler`，功能等价 |
| **R-04/R-05/R-06** | **做：** YAML + Java 规则引擎；不为插件留 Python；理顺路径 |

### 清出主动清单

| ID | 结论 |
|----|------|
| **R-07** | 远程推流节点 py — **清出**（本机 OK；有多节点再开） |
| **R-08/R-09** | EDGE — **清出（范围外，长期 py）** |
| **R-10** | AI auto_label/train — **清出（AI+node 旁路，非 VIDEO Must）** |
| **R-17** | 海康大华扫描深度 — **清出**（Java 已有壳） |
| **R-18** | SAM — **清出**（RUNTIME 已 veto；不实现） |
| **R-11…R-16** | 真机联调 — **归档按需**（代码多已有，缺环境） |

---

## 0. Wave-A 之后「已经不算缺口」的（对照用）

| 能力 | 状态 |
|------|------|
| 人脸特征 / Milvus 检索 / matching 非 bypass | Wave-A **已 PASS** |
| 车牌图→号 OCR + 查库 | Wave-A **已 PASS** |
| face/plate `PythonInferenceWorker` 商业主路径 | **已关**（`python-cli-enabled=false`） |
| Auto-enroll tick（无独立 py） | 随 face/plate Java；抓帧靠 ffmpeg |
| 中控 realtime/snap 算法热路径 | **已是 RUNTIME C++**（与巡检会话无关） |
| 本地 stream-forward（ffmpeg Supervisor） | **已不依赖 py** |

---

## B 类业务深解（供后人开发）

### B.1 巡检 `run_deploy.py`（R-03）

**产品是什么**  
「巡检会话」：选一批摄像头 + 模型，按间隔 **轮流抽查一眼**（短连抓 1 帧→检测→可选告警），不是 realtime 那种一直挂流盯着看。

**链路**  
- **Java（已有）：** create/start/stop/stats/SSE/心跳入库 — `PatrolSessionService` + `PatrolSupervisor`  
- **Python（执行体）：** `EDGE/runtime/services/patrol_algorithm_service/run_deploy.py`  
  - 读会话配置 → 解析 RTSP/GB → 加载 ONNX/YOLO → pool/rotate/hybrid 调度 → `capture_frame`（短连）→ 检测 → 告警 hook 或 sink 后处理 → 心跳回 Java  

**是否强绑某 Python SDK？**  
**不完全是。** 主体是 **流程编排**（调度+短连+告警）。推理用进程内 ONNX/YOLO（或 OpenCV/FFmpeg 解码），**不调用** InsightFace，也 **不调用** 中控那条 C++ RUNTIME。  
同仓 C++ 里其实已有 `PatrolScheduler`（中控 `task_type=patrol` + cpp 可走）；**UI 巡检会话按钮今天仍默认拉 Python**，两套并行。

**若换成 Java 会缺什么**  
- 会话/心跳/SSE：**不缺**（已有）  
- 缺：短连抓帧循环、通用检测引擎挂接、pool/rotate/hybrid 调度（或改挂 RUNTIME）  
- **务实路径：** 执行体切到已有 **C++ PatrolScheduler + AlgorithmRuntimeSupervisor**，比从零 Java 推理省  

**决策状态（2026-08-12 拍板）：**  
执行体 **改挂 C++ RUNTIME `PatrolScheduler`**，Java 只做会话/启停/心跳（替换原 Python 拉起角色）。要求与现 `run_deploy.py` **功能等价**（短连抽查、pool/rotate/hybrid、告警/进度）。**禁止**把 RUNTIME 负责的检测/调度重写成 Java。

### B.2 后处理 Worker + 用户脚本（R-04/R-05）

**产品是什么**  
算法告警之后的 **可插拔业务扩展**：用户写脚本做计数、越线、停留、自定义告警等，**不改检测模型本身**。

**和人脸 matching 的关系**  
同一告警编排可并行：matching = 人脸/车牌库命中；后处理 = 用户脚本（+ 可选姿态）。**互不替代。**

**链路**  
```text
告警 hook → AlertPostOrchestrator
  →（可选）face/plate matching
  →（若开启）HTTP → iot-sink enqueue → Kafka
  → Worker HTTP /execute → run_post_process
       → 姿态（若开）→ 意图 → 用户 process(ctx)
```

Worker 今日仍是 `run_worker.py`（`PostProcessLauncherService` 拉起）。用户工作区默认文件名 **`post_process.py`**，实现 `process(ctx)->dict`。

**Java 化难点**  
不是缺 Maven 库，而是 **产品契约允许用户写 Python**。把拉起器改成 Java 容易；强迫用户改语言会伤生态。

**决策倾向（讨论续 2026-08-12）：**  
- 产品 **不能接受**「整栈已 Java，只为插件再常驻一套 Python」。  
- **已拍板：以 YAML 配置为主**（框位置、阈值、入侵比例、规则类型等）；后端 Java 按规则类型承接；缺能力时 **加规则类型/承接逻辑**，而不是让用户写脚本。  
- 行业「解决方案包」= **检测模型（RUNTIME）+ 现场标定 YAML（每路摄像头不同）**，不是「每矿一份 Python」。  
- 极端定制：Webhook / 极少 JAR（可选逃逸口）；**默认路径不走 Python**。

### B.2.1 为什么「传送带跑偏」不证明必须用 Python

你举的煤矿传送带场景，拆开其实是三层（和语言无关）：

| 层 | 做什么 | 谁做 |
|----|--------|------|
| 1. 感知 | 检出传送带左右缘、左右滚轮等目标 | RUNTIME 检测模型（可专用权重） |
| 2. 标定 | 左/右兴趣区、滚轮框、「遮挡多少算入侵」——**每路摄像头不同，不能写死在模型里** | **YAML / 任务配置**（按 camera_id / task_id） |
| 3. 判定 | 左缘相对左滚轮入侵超阈值 → 告警 | **Java 规则引擎**读配置执行 |

Python 脚本显得「香」，是因为它把 2+3 糊活改；但交付给客户时，运维改脚本 = 不可控。  
**解决方案包**更干净的形态是：

```yaml
# 示意：conveyor_drift_left.yaml（每路摄像头一份标定）
rule: conveyor_edge_intrusion
camera_id: cam_belt_01
regions:
  belt_left_edge: { type: polyline, points: [...] }   # 或依赖检测类名
  roller_left:    { type: box, x, y, w, h }          # 现场标定
params:
  classes: [belt_edge, roller]
  intrusion_ratio_threshold: 0.35
  min_confidence: 0.5
  suppress_sec: 30
alarm:
  event: conveyor_left_drift
```

- 换摄像头 → **只改 YAML 标定**，不改算法包  
- 要新行业逻辑 → **你们加一种 `rule` + Java 承接**，用户仍只填配置  
- 这正是「不能在算法里写死几个框」的正解；**不是 Java 做不到，是以前用 Python 脚本在偷懒承载标定**

### B.2.2 与「整栈退回 Python」的关系

矛盾感来自：把「可编程扩展」和「Python」绑死了。  
Wave-A 已证明推理可 ORT/Java；巡检将挂 RUNTIME。  
后处理用 YAML **不会削弱**解决方案包交付能力，反而更适合给煤矿现场人员改阈值/框，而不是改代码。  
**结论：不因此推倒 Java 迁移；插件位走配置化。**

**决策状态（2026-08-12 拍板）：YAML + Java 规则承接；不为插件留 Python。**

### B.3 远程 stream-forward 下发 Python（R-07）

**产品是什么**  
推流转发 / 预览观看：摄像头 RTSP → SRS（HTTP-FLV/RTMP），**不做 AI**。多节点时把任务派到 **iot-node** 管理的机器上跑。

**它是 EDGE 吗？**  
**不是。**  

| | 远程 stream-forward | EDGE |
|--|---------------------|------|
| 通道 | **iot-node** HTTP（`allocateNode` / `deployWorkload`） | MQTT / `edge` CLI |
| 用途 | 集群节点上的 **纯推流**（预览） | 端侧 **算法** 执行包 |
| 触发 | `NODE_REMOTE_DEPLOY` 开，且任务 `schedule_policy=auto\|node` | 边缘独立 enroll/run |

本机默认 `local` → Java `StreamForwardSupervisor` + **ffmpeg**，根本不走 py。

**为何远程还下发 py**  
节点上历史整包是 `run_deploy.py`（内部也是 ffmpeg + 心跳/failover 等）。本地已迁 Java；**远程节点 agent 未迁**，所以仍下发该脚本。

**决策状态：** 与 EDGE 无关；可后续做「节点侧 ffmpeg agent」；**不紧急**。不接受「为推流在中控再挂 Python」。

- EDGE = **端侧无限联邦边缘组件**（CLI + MQTT），与中控 `video-server` **解耦**  
- **不归 VIDEO Java 化 Must**；**长期留 Python** 合理（部署轻、独立迭代）  
- 后人开发中控时 **不要**把 EDGE 列入「踹掉 Python」的阻塞项  

---

## C 类定性（代码有 vs 缺验证）

| 判断 | 含义 |
|------|------|
| **代码面已有** | Controller/Service/协议客户端已实现；无设备时诚实失败 |
| **缺的是验证/环境** | 真摄像头、真 WVP、真司空账号、双 scheme 失败流等 |

→ **暂时不做 C 类**；等具体项目需要该功能再开联调包。

---
## 1. 剩余缺口总表（决策用）

图例：

- **SDK 前景：** `有现成` / `有基建需自研胶水` / `无拿来即用` / `不适用（真机/产品）`
- **建议决策：** `可做下一波` / `策略选择` / `延后联调` / `永久 sidecar` / `不做`

| ID | 能力 | 用户感知若不做 | 代码锚点 | 缺口本质 | SDK/开源检索结果 | 难度 | 建议决策 |
|----|------|----------------|----------|----------|------------------|------|----------|
| **R-01** | **YOLO Pose 姿态提取** | 姿态库入库/预览空；意图场景弱 | `PoseAnalysisService` → `pose_inference_cli.py` | 算法执行体 | ORT/DJL | 中高 | **做（W1）** |
| **R-02** | **PythonInferenceWorker 残留** | 姿态仍起 py | `PythonInferenceWorker.java` | 执行体桥 | 随 W1 | 低 | **做（随 W1）** |
| **R-03** | **巡检会话算法** | 开巡检后算法不跑 | `PatrolSupervisor` → 现 py；目标改 `AlgorithmRuntimeSupervisor` + RUNTIME `PatrolScheduler` | 执行体改挂 | **不靠 Python SDK**；C++ 已有 PatrolScheduler | 中（接线+等价验收） | **已拍板：挂 RUNTIME，功能等价** |
| **R-04** | **后处理 Worker 拉起** | 自定义后处理起不来 | 现 `run_worker.py` → 目标 **Java 规则引擎读 YAML** | 执行体 | 配置驱动，非 Python SDK | 中 | **已拍板：YAML + Java 承接** |
| **R-05** | **用户后处理脚本默认语言** | 原 `post_process.py` | 改为任务/场景 **YAML**（框、阈值、规则类型） | 产品策略 | 行业包用「模型+标定 YAML」 | 产品 | **已拍板：配置不脚本；不为插件留 Python** |
| **R-06** | **后处理路径/打包** | 脚本路径指向不存在的 `VIDEO/services/` | 实物在 `_retired_python_video/services/...` | 打包布局 | 不适用 SDK；运维/路径修复 | 低 | **随插件方案一并修** |
| **R-07** | **stream-forward 远程部署** | 远程节点推流 | `StreamForwardRemoteDeployService` → iot-node | 执行体（非 EDGE） | — | — | **清出主动清单** |
| **R-08** | **EDGE 边缘代理整栈** | 边缘算法 | `EDGE/` | 范围外 | — | — | **清出；长期 py** |
| **R-09** | **EDGE overlay** | 边缘叠框 | EDGE scripts | 范围外 | — | — | **随 R-08 清出** |
| **R-10** | **AI auto_label / train** | 数据集标注/训练 | `AI/services/*_worker`；iot-node AI bundle | AI 旁路 | — | — | **清出（非 VIDEO Must）** |
| **R-11** | **ONVIF 发现/PTZ/注册真机** | 无设备时仅诚实失败 | `OnvifWsDiscovery` / `OnvifSoapClient` / `CameraHardwareService` | **真机联调** | 代码已有；增强库可选 [Gamer08YT/onvif-java](https://github.com/Gamer08YT/onvif-java)、[link-onvif-client](https://github.com/openlink2/link-onvif-client)（**非必须**，你们已自研 SOAP） | 联调低～中 | **暂不做；有项目再验** |
| **R-12** | **AudioTalk 真机听感** | 无话机仅错误码 | `AudioTalkSession` / `OnvifAudioBackchannelClient` / `G711Codec` | 真机 + 协议细节 | **无完整「对讲 SDK」开箱即用**；库可给 talkback URI，RTP/G.711/backchannel 仍要自研（你们已有）。规范见 ONVIF Audio Backchannel | 联调中 | **暂不做；有项目再验** |
| **R-13** | **GB28181 真 SIP/NVR 矩阵** | 无 WVP/设备则目录空/点播失败 | `Gb28181*` + `iot-gb28181`；SIP 在 **WVP** | 真机/环境 | **不需要自研 SIP 栈**；继续用 WVP。无「替代 WVP 的轻量 Java SIP 国标全家桶」可一键替换 | 联调中 | **暂不做；有项目再验** |
| **R-14** | **GB alternate 失败流证据** | 主 RTMP 挂→RTSP 降级难证 | `resolveAlternatePullUrl` 已接线 | 环境证据 | 不适用 SDK | 环境 | **暂不做（已 PARTIAL）** |
| **R-15** | **FlightHub 真开播** | 无 token 仅 400 | `CameraFlighthubService` | 真账号 | 官方 OpenAPI；**不是缺 SDK**，缺司空凭证/机场 | 低（有账号） | **暂不做；有账号再验** |
| **R-16** | **远程 node / Ceph** | 集群存储/调度 | `IotNodeClient` 等壳 | 基础设施 | MinIO 已够本机；Ceph Java 客户端有，但是运维项目 | 中 | **暂不做** |
| **R-17** | **海康/大华扫描深度** | 网段扫描/NVR 枚举弱 | `HikScanService` / ISAPI / Dahua CGI | 厂商协议 | 无单一官方 Java SDK 覆盖全家；多是自研 HTTP；开源零散 | 中高 | **按需** |
| **R-18** | **SAM 补充分割** | YOLO+SAM 精修不可用 | Python `SamClient`→AI HTTP | 可选算法 | 可继续 HTTP 调 AI 服务；或 ORT 跑 SAM（重） | 高 | **不做 / 旁路** |
| **R-19** | **删干净 VIDEO 运维树** | 大量 test/fix 脚本 | `VIDEO/scripts`、`_retired_python_video` | 仓库卫生 | 不适用 SDK；删前须 R-01/R-03/R-04/R-08 有归宿 | 低～中 | **最后做** |

---

## 2. 按「能不能找到第三方」分组（决策主视图）

### A. 有现成 SDK / 开源基建 → **值得做（胶水工程）**

| ID | 能力 | 可用资源 | 你们还要自写什么 | 风险 |
|----|------|----------|------------------|------|
| *(Wave-A)* | 人脸 | ORT Java + milvus-sdk-java + 现有 ONNX | 预处理对齐、阈值 | 旧向量不兼容需重嵌入 |
| *(Wave-A)* | 车牌 OCR | ORT + 自有 plate onnx；备选 RapidOCR4j / RapidOcr-Java（通用 OCR，**不一定**对齐现网车牌模型） | 移植 `PlatePipeline` 或接受换模型重测 | 换 RapidOCR 可能掉精度/格式 |
| **R-01** | Pose | ORT Java + ultralytics 导出 ONNX；参考 [java-onnx-yolo](https://github.com/mazp99/java-onnx-yolo)；或 **AWS DJL** `YoloPoseTranslator` + OnnxRuntime 引擎（[文档](https://javadoc.io/static/ai.djl/api/0.35.1/ai/djl/modality/cv/translator/YoloPoseTranslator.html)） | 导出/对齐现 `yolo26n-pose` 权重；接 `PoseAnalysisService` | 后处理/NMS 易错；DJL 可减胶水但依赖更重 |

### B. 有部分开源，但 **解决不了「产品执行体」** → **策略题，不是找库题**

| ID | 能力 | 检索结论 | 真实选项 |
|----|------|----------|----------|
| **R-03** | 巡检 | 没有「Patrol-as-a-library」 | ① sidecar 保留 `run_deploy.py`；② 改造成只拉 RUNTIME（对齐中控算法任务）；③ 大改写 EDGE |
| **R-04/R-05** | 后处理 | 没有替代「用户自定义脚本」的 SDK | ① 拉起器改 Java，**脚本仍允许 Python**；② 强制用户改语言（伤产品） |
| **R-07** | 远程推流部署 | 无专用 SDK | 远程改为 ffmpeg 命令协议（复用本地 Supervisor 思路） |
| **R-08/R-09** | EDGE 整栈 | 无替代开源产品 | 长期保留 Python 边缘，或单独立项 Java Edge |

### C. 搜完仍 **无拿来即用完整方案** → **联调或自研协议/运维**

| ID | 能力 | 为什么「找不到就完事」 |
|----|------|------------------------|
| **R-12** | 对讲听感 | 库最多给 URI；RTP backchannel + 品牌差异要自测；你们已有代码，缺真机 |
| **R-13** | 国标全矩阵 | SIP 在 WVP；不是缺一个 Maven 依赖 |
| **R-15** | 司空真开播 | 缺账号/设备，不是缺 HTTP 客户端 |
| **R-11** | ONVIF 真机 | 代码已有；增强库可选但非关键路径 |
| **R-10** | 训练/auto_label | 行业默认 Python；不建议 Java 化 |
| **R-18** | SAM | 可选；无强依赖 |

### D. 明确 **超出能力边界 / 不建议做**

| 项 | 原因 |
|----|------|
| 自研人脸/车牌/姿态网络 | 无数据/训练管线 |
| 把 RUNTIME / ffmpeg / WVP 重写成 Java | HANDOFF 禁止；无收益 |
| 用 Java 重写整套 EDGE+训练 | 工作量≈新产品 |

---

## 3. 「踹掉 Python」分层目标（方便拍板）

### 目标 L1 — 中控推理无 py（Wave-A + R-01）

- 完成：face / plate / **pose** 全 Java ORT  
- 仍可留：Patrol / post_process / EDGE `.py`  
- **可删：** `inference_workers` + 对 `_retired` 的 CLI 依赖  
- **不可删：** 整棵 `VIDEO/`（若还要 sidecar）

### 目标 L2 — 中控执行体无 py（再加策略）

- Patrol → RUNTIME 化或仓外 sidecar  
- PostProcess → Java 拉起 + **允许用户 py 脚本**（推荐）或放弃自定义脚本  
- 远程 stream-forward → 非 py 协议  

### 目标 L3 — 仓内无 VIDEO 目录

- L2 + EDGE 外置或废弃 + 运维脚本迁出  
- **真机联调不是 L3 前置**（无设备可诚实失败）

### 目标 L4 — 生产全场景验收

- L3 + R-11…R-16 真机/账号 soak  

---

## 4. 推荐决策顺序（讨论用）

1. **姿态要不要？**  
   - 要 → 下一包做 R-01（ORT+导出），与 Wave-A 同技术栈。  
   - 不要 → 产品下线姿态入口，删 CLI 依赖即可。  

2. **巡检怎么做？**（R-03）  
   - A：永久 sidecar（最快，不算纯 Java）  
   - B：改造成 RUNTIME Supervisor（与现算法任务一致，推荐若要「中控无 py」）  
   - C：重写 EDGE（不建议现在）  

3. **后处理用户脚本？**（R-04/R-05）  
   - 推荐：**拉起器可 Java，脚本语言继续 Python**（行业常识）  
   - 若坚持零 py：只能砍自定义后处理或提供极弱 DSL  

4. **EDGE / 远程 node？**  
   - 建议：**边缘长期 Python**；中控先 L1/L2  

5. **真机联调**  
   - 单列项目；**不阻塞** L1；有设备再开  

---

## 5. 检索来源（便于复核）

| 主题 | 代表链接 |
|------|----------|
| ORT Java | https://onnxruntime.ai/docs/get-started/with-java.html |
| milvus-sdk-java | https://github.com/milvus-io/milvus-sdk-java |
| ORT+Milvus 叙事 | https://milvus.io/blog/no-python-no-problem-model-inference-with-onnx-in-java-or-any-other-language.md |
| YOLO pose Java 示例 | https://github.com/mazp99/java-onnx-yolo |
| RapidOCR Java | https://github.com/hzkitty/rapidocr4j 、 https://github.com/MyMonsterCat/RapidOcr-Java |
| HyperLPR | 以 Android/C++/Python 为主，**桌面 JVM 车牌不如自有 ONNX+ORT 贴合** |
| ONVIF Java | https://github.com/Gamer08YT/onvif-java 、 https://github.com/openlink2/link-onvif-client |

---

## 6. 一句话给决策会

**Wave-A 之后，还能靠「找 SDK」解决的，主要只剩姿态（ORT 胶水）。**  
巡检/后处理/EDGE **不是缺 Maven 依赖，是产品执行体与用户脚本语言选择。**  
真机/司空/国标矩阵 **不是缺库，是缺环境。**  
训练链与自研网络 **建议永久不做。**
