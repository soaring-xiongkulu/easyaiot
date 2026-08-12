> **话术更新（2026-08-12）：Part2 Wave-A face+plate Java ORT+Milvus 本机 PASS；Pose/Patrol/post_process 仍 Out。**
# CODE-PARITY — Part 2 Dependency / Engine Backlog（只读清单）

> **本波不开工。** Part1 完成前 **不允许**用旁路/stub/mini 冒充 Part1 完成。  
> 唯一环境 = 本机；禁止「等线上」。

---

## 规则

| 项 | 要求 |
|----|------|
| 角色 | 依赖/引擎/真机/远程基础设施清单 |
| 旁路 | 默认 **不允许** 用旁路冒充 Part1 PASS |
| 诚实失败 | Part1 代码在引擎缺失时应 **诚实 bypass/失败**（见 Part1 纪律），不算 Part2 完成 |

---

## 依赖表

| ID | 依赖是什么 | Python 怎么用 | Java 现状 | 允许旁路冒充 Part1？ |
|----|------------|---------------|-----------|----------------------|
| E-01 | **InsightFace / face 推理引擎** | `library_matching_service` / face library 调本地推理 | Part2 Wave-A：`FaceOnnxEngine` ORT Java（余弦≥0.99）；matching 非 bypass | **是（本机 Wave-A PASS）** |
| E-02 | **Milvus**（人脸向量库） | face 库检索 | Part2 Wave-A：`milvus-sdk-java` + docker `milvus-server:19530` | **是（本机 Wave-A PASS）** |
| E-03 | **`face_rec.onnx` / face 模型文件** | VIDEO/RUNTIME 侧模型 | worktree `VIDEO/face_rec.onnx` + `face_det.onnx` 已用于 Wave-A | **是（本机资产齐）** |
| E-04 | **车牌识别模型**（若路径含 OCR，而非仅 DB `plate_entry` 查库） | plate matching 视实现可能含检测+识别 | Part2 Wave-A：`PlateOnnxEngine`；HTTP `engine=onnx-java` 出号 | **是（本机 Wave-A PASS）** |
| E-05 | **YOLO pose 权重**（如 `yolo26n-pose.pt`） | pose 相关脚本/服务 | 仓库可能有未提交大文件；推理归 inference workers | **否** |
| E-06 | **真机 ONVIF / NVR** | camera ONVIF 发现/注册 | Java ONVIF 路由存在；A5 **未**要求真机 | **否**（代码面归 Part1 CP 外的已有 camera；真机联调归本表） |
| E-07 | **真机 GB28181 / SIP** | `gb28181_source` / sync | Java `Gb28181*` 代码存在；真 SIP 设备 | **否**；**代码路径证据**归 Part1 CP-8 |
| E-08 | **FlightHub 真账号/无人机** | `flighthub_source` OpenAPI | Java `CameraFlighthubService`；真 token/设备 | **否**；**API/配置代码**归 Part1 CP-9 |
| E-09 | **远程 node / Ceph** | remote deploy / 对象存储变体 | Java remote/Ceph 相关历史 FR 端口；本机默认 MinIO | **否**（本机 MinIO 是 Part1/阶段2 路径） |
| E-10 | **iot-sink 运行时进程** | VIDEO HTTP 入队到 sink | 仓库内有 `DEVICE/iot-sink`；A6 未起 | **进程启动与 PG 对齐 = Part1 CP-3**（不是引擎）；列于此仅防与「缺模型」混淆 |

---

## 与阶段 2 的关系

| 阶段 2 | Part2 含义 |
|--------|------------|
| A7 ⛔缺 Milvus/InsightFace | = E-01/E-02/E-03；**不要**为绿测打开 `use-direct-process` |
| A6 ⛔缺 sink | **优先按 Part1 CP-3** 处理（仓库内 Java），不是「买引擎」 |

---

## 已读路径（摘要）

- Python：`library_matching_service.py`、face/plate matching kafka services、`run.py` Kafka topic 配置  
- Java：`LibraryMatchingProcessor`（`bypassed`）、`VideoProperties.Inference`、`iot-sink` Face/Plate consumers → HTTP process  
- 证据：`logs/phase2-a7-matching.json`
