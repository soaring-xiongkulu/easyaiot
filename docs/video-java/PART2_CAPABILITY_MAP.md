# VIDEO → Java — Part2 能力边界与依赖地图

> **话术：** Part1（代码可复刻）已收口至 PARTIAL；Part2 = 引擎/模型/真机/仍绑 Python 的执行体。  
> **目标：** 搞清「踹掉 Python VIDEO」前必须补什么、可延后什么、能力边界在哪。  
> **禁止：** 用 bypass/stub 冒充 Part2 完成；禁止未补齐关键引擎就删 `VIDEO/`。

**对照根：** Oracle `F:/acme/VIDEO` · Candidate `F:/acme/.worktrees/video-java`  
**既有清单：** [DEP_ENGINE_BACKLOG.md](./DEP_ENGINE_BACKLOG.md)（本文件是其展开）

---

## 1. 先澄清架构（避免把「该复用的」当成 Part2 自研）

```text
┌─────────────────────────────────────────────────────────┐
│  Java video-server（编排 / API / DB / Kafka / 调度）      │  ← Part1 主体已到这
└────────────┬────────────────────────────┬───────────────┘
             │                            │
             ▼                            ▼
   ┌─────────────────┐          ┌──────────────────────┐
   │ 已复用的外部组件  │          │ 仍绑 Python 的部分    │
   │ RUNTIME(C++)    │          │ PythonInferenceWorker│
   │ ffmpeg / SRS    │          │   face/plate/pose CLI│
   │ Kafka/MinIO/PG  │          │ Patrol run_deploy.py │
   │ Nacos / 网关    │          │ post_process worker  │
   │ WVP(国标SIP)    │          │ （+ 真机联调）        │
   └─────────────────┘          └──────────────────────┘
        ≠ Part2 自研                   = Part2 主战场
```

**约定（与 HANDOFF 一致）：**

| 不算 Part2「自己写引擎」 | 算 Part2 |
|--------------------------|----------|
| RUNTIME / ffmpeg / Kafka / MinIO / Nacos / 网关 / WVP 服务本身 | InsightFace/Milvus/车牌 OCR/YOLO Pose 的 **Java 侧可运行推理** |
| Java 已写好的 ONVIF/GB/FlightHub **代码面** | 真机/真账号 **联调验收** |
| 车牌 **已知号** 查 PG | 从图检测+OCR 出号 |

**踹 Python 的真实含义：**  
不是把 RUNTIME 改成 Java，而是：**Java 不再依赖 `VIDEO/` 里的 `.py` 子进程与 `_retired_python_video` 树**。RUNTIME/ffmpeg 等可继续作为外部二进制存在。

---

## 2. 现状一句话

| 层 | 状态 |
|----|------|
| 编排 / API / 告警 Kafka / matching 接线 / sink / 调度 | **Java（Part1）** |
| 检测热路径 | **RUNTIME C++**（Java Supervisor 拉起；不重写） |
| 人脸特征 + Milvus | **仍调** `face_inference_cli.py` → InsightFace + pymilvus |
| 车牌 OCR | **仍调** `plate_inference_cli.py` |
| 姿态 | **仍调** `pose_inference_cli.py` + YOLO pose |
| 巡检算法进程 | **仍拉** `run_deploy.py` |
| 后处理 worker | **仍拉** `run_worker.py` |
| 引擎缺失时 | Java **诚实 bypass/失败**（≠ 引擎完成） |

CLI bootstrap 还会把 `VIDEO/_retired_python_video` 塞进 `sys.path` → **删 VIDEO 目录会直接掐断这三路推理**。

---

## 3. Part2 依赖全表（按「踹 Python」相关度）

### 3.1 必须先处理（否则删不掉 Python）

| ID | 组件 | 类型 | Python/现状入口 | 用户可见能力 | Java 替代路线 | 自研难度 | 能力边界建议 |
|----|------|------|-----------------|--------------|---------------|----------|--------------|
| **P2-01** | InsightFace + `face_rec.onnx` | 库+模型 | `face_recognition_service` / `face_inference_cli.py` | 人脸入库、1:N 命中 | **ONNX Runtime Java** 加载同款 ONNX；或 DJL | **高**（对齐裁剪/阈值/精度） | **Must：先做** |
| **P2-02** | Milvus + pymilvus | 服务+SDK | `FaceVectorStore` | 向量检索 | **milvus-sdk-java** | **中** | **Must：与 P2-01 一起** |
| **P2-03** | `face_det.onnx` 抓脸 | 模型 | `face_capture_service` | 告警后抠脸/自动录入 | ORT Java 跑 det | **中** | **Must**（匹配闭环） |
| **P2-04** | 车牌 detect/rec ONNX | 模型+逻辑 | `plate_recognition/pipeline` / CLI | 图→车牌号 | ORT Java 移植 `PlatePipeline`；或 RapidOCR | **中高** | **Must**（若产品要车牌） |
| **P2-05** | YOLO Pose + ultralytics | 库+权重 | `pose_analysis` / `pose_inference_cli.py` | 姿态库/意图 | 导出 ONNX → ORT；或旁路保留小服务 | **中高** | **Should：有姿态产品再做** |
| **P2-06** | Patrol `run_deploy.py` | Python 执行体 | `PatrolSupervisor` | 巡检会话真跑算法 | 改为拉 RUNTIME/EDGE 非 py；或永久 sidecar | **高**（若重写）/**低**（策略允许 sidecar） | **决策点** |
| **P2-07** | post_process `run_worker.py` | Python 执行体 | `PostProcessLauncherService` | 用户后处理脚本 | Java worker 或「用户脚本仍 Python」产品声明 | **中** | **决策点** |

### 3.2 可延后（代码面已有 / 联调向）

| ID | 组件 | 说明 | 难度 | 建议 |
|----|------|------|------|------|
| **P2-08** | 真机 ONVIF/NVR | Java SOAP/发现已有；缺现场设备 | 联调 **低～中** | 有设备再 soak |
| **P2-09** | 真 GB28181/WVP | Java sync/resolve 已有；缺真 SIP 矩阵 | 联调 **中** | 有 WVP 环境再做 |
| **P2-10** | 真 FlightHub 账号 | HttpClient 已有；缺 token/机场 | 联调 **低** | 有账号再做 |
| **P2-11** | 远程 node / Ceph | 壳已有；真部署运维 | **中** | 集群阶段 |
| **P2-12** | ONVIF Audio 真机听感 | Java 对讲代码面已有；真 backchannel | 联调 **中** | 有话机再做 |
| **P2-13** | U3 alternate 行为证据 | 代码已接线；需双 scheme 失败流 | 环境 **中** | 有 WVP 再补证 |

### 3.3 不要当 Part2 自研（继续复用）

| 组件 | 理由 |
|------|------|
| RUNTIME C++ | 热路径已是它；HANDOFF 明确不重写 |
| ffmpeg / SRS / ZLM | 外挂二进制/服务 |
| Kafka / MinIO / PG / Nacos / 网关 | 基础设施 |
| WVP 进程本身 | 国标 SIP 在 WVP；VIDEO/Java 只 HTTP |

### 3.4 可忽略的死依赖（requirements 有、代码未用）

`paddleocr` / `openvino` / `pydub`（当前无业务 import）——换 Java 时不必移植。

---

## 4. 「踹掉 Python」时会丢什么？

### 4.1 若只删 VIDEO、Part2 一个都不做

| 仍可用（大致） | 立刻不可用 / 严重降级 |
|----------------|------------------------|
| 设备 CRUD、目录、告警 hook→Kafka（无匹配） | **人脸命中 / 入库特征** |
| 车牌 **已知号** 查库 | **从图 OCR 出号** |
| RUNTIME 若已有 ini/人工拉起（实际无 VIDEO 难自动） | **自动拉起算法任务**（Supervisor 还在，但姿态/后处理/巡检 py 断） |
| ONVIF/GB/FH **API 壳** | 真机联调本就未承诺 |
| MinIO/Kafka 媒体主路径 | 依赖 CLI 的匹配闭环 |

**结论：** 没有 Part2 Must，**不能**宣称「整个 VIDEO 已是纯 Java」。

### 4.2 若只完成 Must（P2-01…04）+ 保留 py sidecar 给巡检/后处理

- 人脸/车牌主业务可宣称 Java 推理闭环  
- 巡检/自定义后处理仍依赖 Python → **文档必须写清「允许 sidecar」**，否则仍不算踹干净  

### 4.3 若 Must + 迁出 P2-06/07

- 才接近「仓库可删 `VIDEO/`」  
- 真机联调仍可另册，不阻塞删目录（功能在无设备时诚实失败即可）

---

## 5. 怎么实现（三条技术路线）

对 **P2-01…05**，推荐优先级：

### 路线 A — ONNX Runtime Java（推荐主路）

1. 复用现有 `face_det.onnx` / `face_rec.onnx` / `plate_*.onnx`  
2. 用 **onnxruntime** Java API 替代 InsightFace Python 包（特征维、预处理必须对齐现网 Milvus 里已有向量，否则要 **全量重嵌入**）  
3. **milvus-sdk-java** 替换 pymilvus  
4. 替换 `PythonInferenceWorker` 调用为 `OnnxFaceEngine` / `OnnxPlateEngine`  

**优点：** 不重训模型；与现权重兼容。  
**风险：** 预处理差 1px 都可能导致向量不兼容 → 需对照 Python CLI 做 **同一张图 embedding 数值对齐**。

### 路线 B — 永久 Python Sidecar（能力边界内的务实选项）

- 单独部署极瘦 `inference-sidecar`（只含三 CLI），Java 只 HTTP/进程调用  
- **不算**「踹掉 Python」，但可删大块 Flask VIDEO  
- 适合：**没有精力做 ORT 对齐** 时的过渡  

### 路线 C — 自研算法（不推荐）

- 自己写检测/识别网络 → **超出当前团队能力边界**，明确不做。

---

## 6. 建议实施波次（重要的先做）

### Wave α — 人脸命中闭环（最高优先级） — **DONE 2026-08-12（Part2 Wave-A）**

**目标：** 本机装 Milvus + 模型；Java ORT 提特征；matching 不再 `bypassed`。  
**交付：** 同图 Python CLI vs Java embedding 余弦接近；库检索 hit/miss 证据。  
**含：** P2-01, P2-02, P2-03  

### Wave β — 车牌 OCR — **DONE 2026-08-12（Part2 Wave-A）**

**目标：** 无 plate_no 的图也能 OCR→查库。  
**含：** P2-04  

### Wave γ — 执行体去 py（产品决策）

| 选项 | 含义 |
|------|------|
| γ-1 | Patrol/PostProcess **允许** Python sidecar（写进 HANDOFF）→ 可先删 Flask 编排树 |
| γ-2 | 改为纯 RUNTIME/Java worker → 才能删全部 `.py` |

### Wave δ — 姿态（按需）

P2-05；无姿态产品可长期旁路。

### Wave ε — 真机联调（按需）

P2-08…12；**不阻塞**「删编排用 Python」，阻塞「全场景生产验收」。

---

## 7. 能力边界（什么做、什么不做）

| 做 | 不做 |
|----|------|
| 接线 ORT + 复用现有 ONNX | 自研人脸/车牌网络 |
| milvus-sdk-java | 自研向量库 |
| 对齐预处理与阈值 | 保证超越 InsightFace 精度 |
| 文档化 sidecar 边界 | 把 SRS/WVP/RUNTIME 改写成 Java |
| 真机有设备再联调 | 无设备时伪造联调 PASS |

---

## 8. 与「整仓 VIDEO 变 Java」的差距清单

**删 `VIDEO/` 前检查表：**

- [ ] `PythonInferenceWorker` 无人脸/车牌/姿态调用（或 worker 迁出仓外并产品批准）  
- [ ] `_retired_python_video` / `inference_workers` 无运行时依赖  
- [ ] PatrolSupervisor 不依赖仓内 `run_deploy.py`（或明确 sidecar 路径在仓外）  
- [ ] PostProcessLauncher 同理  
- [ ] 人脸 matching 证据：非 bypass 的 hit（至少本机）  
- [ ] 文档：COMPLETE 仍禁止，直到上列勾完 + 产品签字  

**当前：** Part1 编排 + Part2 Wave-A（face/plate ORT+Milvus）本机已证；**Patrol/post_process/pose 仍绑 py → 仍不能删 VIDEO。**

---

## 9. 下一步（仅建议，另令开工）

1. 产品确认：巡检/后处理是否允许长期 Python sidecar（γ-1 vs γ-2）。  
2. 另令 **Wave α**：本机 Milvus + face ORT 对齐实验（先不做真机）。  
3. 更新本文件与 `DEP_ENGINE_BACKLOG.md` 状态列。  

**禁止**在未开 Part2 令时用 mini/direct 冒充人脸命中。
