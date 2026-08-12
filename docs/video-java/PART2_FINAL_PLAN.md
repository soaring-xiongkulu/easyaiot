# VIDEO → Java — Part2 最终方案（决策锁定版）

> **日期：** 2026-08-12  
> **状态：** 决策已全部确认，可按本文件开工。  
> **工作树：** `F:/acme/.worktrees/video-java` @ `feat/video-java`  
> **Oracle：** `F:/acme/VIDEO/`（对照只读；**禁止删除**直至本方案「现在做」全部验收且产品签字）  
> **关联：** [PART2_CAPABILITY_MAP.md](./PART2_CAPABILITY_MAP.md) · [PART2_REMAINING_DECISION_MATRIX.md](./PART2_REMAINING_DECISION_MATRIX.md) · [PART2_WAVE_A_PACK.md](./PART2_WAVE_A_PACK.md)

---

## 0. 一句话

中控 VIDEO：**编排与人脸/车牌已在 Java**；剩余主线只做三件事——**姿态 ORT、巡检挂 C++ RUNTIME、后处理 YAML 规则引擎**。  
EDGE / AI 训练标注 / SAM / 真机联调 / 远程推流节点 py：**不进本方案主动范围**。  
**禁止 COMPLETE、禁止未验收就删 `VIDEO/`、禁止为插件常驻 Python、禁止把 RUNTIME 重写成 Java。**

---

## 1. 已完成（基线）

| 项 | 证据 / 提交 |
|----|-------------|
| Part1 编排与深对齐（CP-1…CP-12 主路径） | 见 `CODE_PARITY_INDEX`；Overall 曾 PARTIAL 处已按门控修正 |
| **Part2 Wave-A** 人脸 ORT + Milvus + 车牌 OCR + 关 face/plate CLI | `f29cb6ab`；`.superpowers/sdd/briefs/part2-wave-a-report.md` |
| 中控 realtime/snap | Java → **C++ RUNTIME** |
| 本地 stream-forward | Java → **ffmpeg** |

---

## 2. 现在做（主动交付，按序）

### W1 — 姿态 Java ORT（原 R-01 + R-02）

| 字段 | 内容 |
|------|------|
| **目标** | `PoseAnalysisService` 不再依赖 `pose_inference_cli.py`；用 ORT Java（或 DJL+ORT）跑现有 YOLO Pose 权重（导出 ONNX） |
| **Done when** | 姿态提取行为证据；`python-cli` 对 pose 默认关闭或删除路径；意图匹配仍可用上游关键点 |
| **Out** | 不自研网络；不要求真机 |
| **锚点** | `PoseAnalysisService`；`pose_inference_cli.py`；`yolo26n-pose.pt` |

### W2 — 巡检挂 C++ RUNTIME（原 R-03）

| 字段 | 内容 |
|------|------|
| **目标** | `PatrolSupervisor` 不再拉 `run_deploy.py`；改挂 **RUNTIME `PatrolScheduler`**（经 `AlgorithmRuntimeSupervisor` / ini） |
| **等价要求** | 与现 Python 巡检：**短连抽查、pool/rotate/hybrid、告警、进度/心跳** 语义对齐 |
| **Done when** | 会话 start→进度→stop 行为证据；进程为 RUNTIME 非 python |
| **禁止** | 把检测/短连调度重写成 Java 推理 |
| **锚点** | `PatrolSupervisor`；`AlgorithmRuntimeSupervisor`；`RuntimeIniGenerator`（patrol）；C++ `PatrolScheduler` |

### W3 — 后处理 YAML 规则引擎（原 R-04/R-05/R-06）

| 字段 | 内容 |
|------|------|
| **目标** | 用 **YAML 配置**（框/区域、阈值、规则类型、按摄像头标定）+ **Java 规则承接** 替换 `run_worker.py` / 默认 `post_process.py` 主路径 |
| **行业包模型** | 检测模型（RUNTIME）+ **每路摄像头标定 YAML**（如传送带左右缘/滚轮/入侵比例） |
| **扩展方式** | 缺能力 → **加规则类型与后端逻辑**；不为插件常驻 Python |
| **逃逸口（非默认）** | 日后可选 Webhook；默认路径不走 py |
| **Done when** | 至少 1～2 类规则（如区域计数/入侵）+ YAML 标定可跑通行为证据；商业路径不拉 post_process Python worker |
| **路径清理** | 一并理顺 worker 路径相对 `_retired_python_video` 的错位（R-06） |

**建议实施序：** W1 ∥ W2 可并行（不同文件）；**W3 可与 W1/W2 并行**但规则引擎面较大，宜单独包。全部完成后才讨论删 VIDEO。

---

## 3. 已清出主动清单（不做 / 非本范围）

| ID | 项 | 处置 | 说明 |
|----|----|------|------|
| R-07 | 远程 stream-forward（iot-node 下发 py） | **清出** | 本机已 ffmpeg；**不是 EDGE**；有多节点项目再开 |
| R-08/R-09 | EDGE 整栈 | **清出（范围外）** | 端侧组件，**长期留 Python** |
| R-10 | AI auto_label / model_train | **清出（范围外）** | 属 **AI + iot-node**，非 video-server Must |
| R-17 | 海康/大华扫描深度 | **清出** | Java 已有扫描/NVR 枚举壳；真机深度按需 |
| R-18 | SAM | **清出** | RUNTIME **已 product-veto**；Java 不实现；清单曾因 VIDEO 旁路字段误显眼 |
| R-11…R-16 | ONVIF/对讲/国标/司空/Ceph 等真机 | **归档按需** | **代码面多已有**；缺环境验证；有项目再联调 |
| — | 自研网络 / 重写 RUNTIME·ffmpeg·WVP | **永久不做** | — |
| R-19 | 删 `VIDEO/` 目录 | **禁止（直至 W1–W3 验收+签字）** | — |

---

## 4. 架构（锁定后）

```text
WEB / 用户
  └─ Java video-server
        ├─ 告警 / matching（人脸·车牌 ORT + Milvus）     ✅ Wave-A
        ├─ 姿态提取（ORT Java）                           ← W1
        ├─ 巡检会话 → C++ RUNTIME PatrolScheduler         ← W2
        ├─ 后处理 → YAML + Java 规则引擎                  ← W3
        ├─ 算法任务 realtime/snap → C++ RUNTIME           ✅
        ├─ 本地推流 → ffmpeg                              ✅
        └─ Kafka / MinIO / PG / Nacos / WVP               ✅ 外挂

EDGE（端侧）          → 不迁，留 Python
AI 标注/训练 worker   → 不迁，留 Python（iot-node）
真机联调              → 按需，不挡 W1–W3
```

---

## 5. 验收与纪律

1. **Leaf only** 执行包；禁止嵌套 Task。  
2. **零 Fallback** 冒充引擎/规则成功。  
3. 证据行为级（`logs/p2-final-*.json` 或分包装证据）。  
4. 每包报告 + 更新 INDEX / HANDOFF / 本文件状态。  
5. **不宣称 COMPLETE / 不删 Python**，直至 W1–W3 全 PASS 且产品明确签字。

---

## 6. 主 Agent 总提示词（可直接粘贴）

```text
执行 docs/video-java/PART2_FINAL_PLAN.md（Part2 最终方案锁定版）。

范围仅 W1→W3：
- W1 姿态 ORT Java，关掉 pose Python CLI
- W2 巡检改挂 C++ RUNTIME PatrolScheduler，功能等价，禁止重写 RUNTIME 推理
- W3 后处理 YAML + Java 规则引擎，不为插件留 Python；行业包=模型+每路标定 YAML

清出不做：EDGE、AI train/auto_label、SAM、远程推流节点 py、真机联调（归档按需）。

约束：工作树 F:/acme/.worktrees/video-java；Oracle VIDEO 只读；Leaf only；禁止 COMPLETE；禁止删 VIDEO；禁止嵌套 Task。

先读 PART2_FINAL_PLAN.md 与 PART2_REMAINING_DECISION_MATRIX.md 讨论纪要。可按 W1∥W2 与 W3 分提交。做完给出每项 PASS/证据/哈希，并更新 HANDOFF。
```

---

## 7. 状态看板（开工时更新）

| 包 | 状态 |
|----|------|
| Wave-A face/plate | **PASS** |
| W1 Pose ORT | **PASS** |
| W2 Patrol → RUNTIME | **PASS** |
| W3 Post-process YAML | **PASS** |
| 清出项 | **已锁定，不排期** |
