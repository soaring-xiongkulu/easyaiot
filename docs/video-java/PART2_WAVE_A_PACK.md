# Part2 Wave-A — 外部 SDK / Java 可替代推理收口包

> **发给主 Agent 的执行指令（另令开工）。**  
> **话术：** Part1 编排已收口（PARTIAL）；本包只做 **可用外部 SDK、可用 Java 替代 Python CLI** 的推理闭环；真机联调 / 自研算法 / 重写 RUNTIME **不做**；做完再讨论做不了的边界项。  
> **工作树：** `F:/acme/.worktrees/video-java` @ `feat/video-java`  
> **Oracle：** `F:/acme/VIDEO/`（只读对照；禁止删）  
> **地图：** `docs/video-java/PART2_CAPABILITY_MAP.md`

---

## 0. 全局约束（强制）

1. **Leaf only：** 禁止嵌套 `Task` / 禁止再派子代理。主 Agent 自改、自测、写证据与报告。  
2. **禁止 COMPLETE / 禁止删 `VIDEO/` / 禁止 FR-B 刷绿。**  
3. **禁止**用 `use-direct-process` / mini / stub / 假 matched 冒充引擎完成。  
4. **禁止自研神经网络**；禁止把 RUNTIME / ffmpeg / Kafka / MinIO / WVP **重写成 Java**。  
5. **本包范围 = 推理 SDK 替代 Python CLI**（见 §1 In）。巡检 `run_deploy.py`、后处理 `run_worker.py`、真机联调 = **Out**（下一讨论波）。  
6. **唯一环境 = 本机**；Milvus / 模型文件必须在本机可跑或诚实 `BLOCKED`（不得伪造 hit）。  
7. **证据必须行为级：** embedding 对齐数字、matching hit/miss、OCR 出号；禁止仅 `mvn compile`。  
8. 交付：`logs/p2a-*.json`（或 `.superpowers/sdd/evidence/p2a-*.json`）；报告 `.superpowers/sdd/briefs/part2-wave-a-report.md`；更新 `DEP_ENGINE_BACKLOG.md` / `PART2_CAPABILITY_MAP.md` / `HANDOFF.md` / INDEX。

---

## 1. 范围

### In（本包必须推进）

| ID | 目标 | 技术路线 |
|----|------|----------|
| **A1** | 人脸特征提取 **不再走** `face_inference_cli.py` | **ONNX Runtime Java** 加载现有 `face_det`/`face_rec`（或 InsightFace 导出的同维 ONNX） |
| **A2** | Milvus 读写 **不再走** pymilvus（经 Python） | **milvus-sdk-java** |
| **A3** | `LibraryMatchingProcessor` 人脸路径：引擎可用时 **非 bypass**，可 hit/miss | 接 A1+A2 |
| **A4** | 车牌 OCR **不再走** `plate_inference_cli.py`（图→plate_no） | ORT Java 移植 `PlatePipeline` 或等价加载现有 `plate_*.onnx` |
| **A5** | `PythonInferenceWorker` 对 face/plate：**默认走 Java 引擎**；Python CLI 仅作 fallback 且 **local 商业默认关闭**（或删除调用） | 配置开关清晰 |

### Out（明确不做，写入报告「留给下一波讨论」）

| ID | 项 | 原因 |
|----|----|------|
| X1 | Patrol `run_deploy.py` | 执行体策略未定（sidecar vs 迁出） |
| X2 | post_process `run_worker.py` | 同上 |
| X3 | YOLO Pose / `pose_inference_cli.py` | Should；本包不做（可诚实保留 CLI） |
| X4 | 真机 ONVIF/NVR/SIP/司空联调 | 缺设备；代码面已有 |
| X5 | 自研检测网络、重写 RUNTIME | 能力边界外 |
| X6 | U3 alternate 真流证据 | 环境 BLOCKED，已 PARTIAL |

---

## 2. 成功定义（Done when）

**整体：**

1. 本机 `profile=local`：人脸 matching 对 **已知入库样本** 能 `matched=true`（或可解释 miss），**不得**再因「无 Python CLI」而整段 `bypassed`。  
2. 本机：给一张含车牌图，Java OCR 给出 `plate_no`，再走现有查库 hit/miss。  
3. 关闭/移除 face+plate 的 Python CLI 依赖后，上述仍成立（或 CLI 开关默认 false 且证据在 false 下采集）。  
4. 报告列出 Out 项为「未做 / 另议」，**不宣称**可删 VIDEO / COMPLETE。

**若 Milvus 或模型文件本机缺失：** 该项标 `BLOCKED` + 安装步骤；**禁止**假 hit。优先把引擎代码与开关落地，并在报告写清阻塞环境。

---

## 3. 任务分解（按序）

### A0 — 环境与资产盘点（先做）

1. 定位模型文件：`face_rec.onnx` / `face_det.onnx` / `plate_detect.onnx` / `plate_rec.onnx`（worktree `VIDEO/`、RUNTIME、文档路径）。  
2. 确认或安装 **本机 Milvus**（默认 `:19530`，对齐 Python `MILVUS_URI`）。  
3. 读清 Python 预处理：`face_recognition_service` embedding 尺寸、归一化、det 阈值；`PlatePipeline` 步骤。  
4. 证据：`logs/p2a-a0-assets.json`（路径是否存在、Milvus ping）。

### A1 — ONNX Runtime Java 人脸引擎

1. Maven 引入 `com.microsoft.onnxruntime:onnxruntime`（或 gpu 变体，与本机一致，文档写明）。  
2. 实现 `FaceOnnxEngine`（名称可调整）：detect（若需要）+ embed(crop/image) → `float[]`。  
3. **对齐实验（强制）：** 同一张图，Python CLI embed vs Java embed，记录余弦相似度；目标 **≥ 0.99**（或报告实际值；若 &lt;0.95 不得宣称可复用旧 Milvus 库，需文档「必须重嵌入」）。  
4. 替换 `FaceRecognitionService` 内对 `PythonInferenceWorker` 的主路径。  
5. 证据：`logs/p2a-a1-face-ort.json`（余弦、维度、耗时）。

### A2 — milvus-sdk-java

1. 引入官方 Java SDK；连接参数对齐 Python（uri/collection/metric）。  
2. 实现 insert / search / delete 与现 collection schema 兼容。  
3. Health：`isEngineAvailable` = ORT 模型可加载 **且** Milvus 可 ping。  
4. 证据：`logs/p2a-a2-milvus.json`（ping + 一次 search 往返）。

### A3 — Matching 闭环（人脸）

1. 入库 1 张 → process matching → **hit**；换无关图 → **miss**（非 bypass）。  
2. 引擎关闭时仍 **诚实 bypass/失败**（回归 Part1 纪律）。  
3. 证据：`logs/p2a-a3-face-match.json`。

### A4 — 车牌 OCR Java

1. ORT 加载 plate onnx；移植透视/字库等 **必要**后处理（对照 `plate_recognition/pipeline`）。  
2. `PlateRecognitionService` 主路径改 Java；去掉对 plate CLI 的默认依赖。  
3. 证据：`logs/p2a-a4-plate-ocr.json`（输入图路径、输出 plate_no、再查库可选）。

### A5 — 关掉商业路径 Python CLI（face/plate）

1. `VideoProperties.Inference`：`python-cli-enabled` 默认 **false**（或等价）；仅 debug 可开。  
2. 确认 auto-enroll / matching / library API 在 false 下走 Java。  
3. Pose 可继续 CLI（本包 Out），但文档写明。  
4. 证据：`logs/p2a-a5-cli-off.json`（配置快照 + 一次 face/plate 调用栈不含 cli 脚本）。

### A6 — 文档收口

1. `.superpowers/sdd/briefs/part2-wave-a-report.md`：逐项 PASS/BLOCKED/PARTIAL。  
2. 更新 `DEP_ENGINE_BACKLOG.md` E-01…E-04 状态。  
3. 更新 `PART2_CAPABILITY_MAP.md` Wave α/β 状态。  
4. `HANDOFF.md`：下一步 = 讨论 X1/X2/X3（sidecar）与真机；**禁止删 Python**。

---

## 4. 关键代码锚点（起点）

| 角色 | 路径 |
|------|------|
| Java worker 现状 | `…/service/inference/PythonInferenceWorker.java` |
| 人脸服务 | `…/service/face/FaceRecognitionService.java` |
| 匹配 | `…/service/LibraryMatchingProcessor.java` |
| 车牌 | `…/service/plate/PlateRecognitionService.java`（或等价） |
| 配置 | `VideoProperties.Inference`；`application-local.yaml` |
| Python 对照 | `VIDEO/app/services/face_recognition_service.py`；`face_vector_store.py`；`plate_recognition/pipeline.py` |
| CLI（将被替代） | `VIDEO/scripts/inference_workers/face_inference_cli.py`；`plate_inference_cli.py` |

---

## 5. 验收自检清单

```text
[ ] Milvus 本机可 ping（或 A2 BLOCKED 有安装说明）
[ ] 人脸 embed Python vs Java 余弦已记录
[ ] matching hit 证据非 bypass
[ ] 车牌 OCR 出号证据存在
[ ] local 默认不调 face/plate Python CLI
[ ] 未改 RUNTIME/ffmpeg；未删 VIDEO
[ ] Out 项未假装完成
[ ] 报告无 COMPLETE / 可删 Python
```

---

## 6. 主 Agent 开场提示词（可直接粘贴）

```text
执行 docs/video-java/PART2_WAVE_A_PACK.md（Part2 Wave-A：外部 SDK / Java 替代 face+plate 推理）。

约束：
- 工作树 F:/acme/.worktrees/video-java；Oracle F:/acme/VIDEO 只读
- Leaf only：禁止嵌套 Task；禁止 COMPLETE；禁止删 Python
- 只用 ORT Java + milvus-sdk-java 等外部 SDK；禁止自研网络；禁止重写 RUNTIME/ffmpeg
- In：A0–A6（人脸 ORT、Milvus、matching 非 bypass、车牌 OCR、关掉 face/plate Python CLI）
- Out：Patrol/post_process py、Pose、真机联调 —— 只记账不宣称完成
- 证据行为级 logs/p2a-*.json；报告 .superpowers/sdd/briefs/part2-wave-a-report.md
- 缺 Milvus/模型标 BLOCKED，禁止假 hit

先读 PART2_CAPABILITY_MAP.md 与本包再改代码。做完给出每项 PASS|BLOCKED|PARTIAL、证据路径、提交哈希。
```

---

## 7. Brief 镜像

`.superpowers/sdd/briefs/part2-wave-a-brief.md` → 指向本文件为 SSOT。
