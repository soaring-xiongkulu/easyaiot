# RUNTIME 能力收归 — 最终方案（交接版）

| 项 | 内容 |
|----|------|
| **状态** | **FINAL（2026-08-09）** — 规划侧工作结束，交给实施负责人 |
| **仓库** | `F:/acme`（EasyAIoT 硬分叉） |
| **权威计划** | 本文 + [`PLAN.md`](./PLAN.md)（分 Phase 任务勾选） |
| **调研基线** | [`reports/01`](./reports/01-python-realtime.md)～[`06`](./reports/06-equivalence-testbed.md) |
| **业务取舍** | [`CAP-BUSINESS-DECISIONS.md`](./CAP-BUSINESS-DECISIONS.md) |

---

## 1. 目标（一句话）

以**标准测试场上的功能表现一致**为完成定义，将 `executor=python` 的算法热路径能力全部收归到 **C++ RUNTIME（帧内）+ VIDEO（帧后）**，保证 **Windows 可编译可运行**，最终**删除** `VIDEO/services/*_algorithm_service`；**不**把 `AI/` 训练/标注模块并进 Runtime。

---

## 2. 产品拍板（已冻结）

### 2.1 必须做（不可砍）

| 类别 | 内容 |
|------|------|
| **等价测试场** | manifest → record-python → run-cpp → certify；分层 L_exec / L_platform / L_e2e / L_perf |
| **C++ RUNTIME** | 唯一热路径执行器；含 **Windows** 交付 |
| **目标追踪** | CAP-TRACKING 必须与 Python 表现对齐 |
| **其余算法任务能力** | 多模型、区域、告警类过滤、冷却、心跳、RTMP/叠框表现、运动门控、人脸/车牌类过滤与**库匹配**、后处理、姿态、布防、Cron 抓拍精度、抓拍空间、patrol pool/rotate/**hybrid**、国标源解析、NVENC 自动降档等 —— **全部纳入范围**（见取舍表「要」） |

### 2.2 明确不做 / 边界

| 项 | 决定 |
|----|------|
| **算法任务 SAM 补充**（`sam_supplement_*`） | **砍掉**；不进 C++、不进 VIDEO 帧后必做、不进 parity P0 |
| **`AI/` 模块内标注用 SAM** | **保留**（数据标注刚需） |
| **热路径模型格式** | **仅 ONNX**；业务上的「多模型/.pt 能力」通过**导出 ONNX**满足，不在 C++ 内嵌 ultralytics |
| **私有学习仓依赖** | 禁止 RebCompatibleLib / 原版 vendor 再分发；可借鉴 MSVC、vendor 布局、certify 思想（见 report 05） |

### 2.3 架构原则（实施必须遵守）

```text
VIDEO：编排、ini、启停、hook 消费、Kafka、人/车牌匹配触发、后处理投递、UI
   ▲ HTTP hook / heartbeat
C++ RUNTIME：拉流→解码→(motion_gate)→ONNX→track→region→emit / RTMP
```

- 帧内能力 → C++；帧后触发（匹配/后处理）→ VIDEO（今天在 Python `run_deploy` 里触发的要上收）。
- 禁止静默降级：任务字段未进 ini / 未实现须打日志，不得假装支持。
- 完成定义：仅 **`certify` 全绿**可删 Python runtime；`run` 绿不算。

---

## 3. 实施顺序（给负责人）

按 [`PLAN.md`](./PLAN.md) Phase 执行，**不得跳过 Phase 0**：

| Phase | 内容 | 出口 |
|-------|------|------|
| **0** | 测试场骨架（夹具、mock hook、gate CLI） | doctor 绿；≥3 个 P0 有 python golden |
| **1** | Windows RUNTIME 可编译 + VIDEO 拉起 | win 上检测+hook 可采样 |
| **2** | ini 全字段映射 + hook payload 对齐 | 无静默丢失 |
| **3** | VIDEO 吸收人/车牌/后处理触发 + UI 门禁 | 仅 cpp 时匹配链仍绿 |
| **4** | C++ 按红清单补齐（追踪、门控、调度、多模型、RTMP/叠框等） | P0+P1 certify 收敛 |
| **5** | linux_full + win_cpp certify 全绿 → 删 Python 三服务 | 默认只留 cpp |

**红清单驱动：** 只修 `logs/runtime_parity_report.json`（或等价报告）中的红项。

---

## 4. 工作量提示（给排期）

在「几乎全要 + 已砍算法任务 SAM」前提下，粗估仍约 **2～4 人月**（熟手；含测试场与双端回归）。大头仍是：测试场、Windows、追踪、snap/patrol 精细对齐、匹配上收与全程行为 diff。

---

## 5. 文档地图（交接阅读顺序）

1. 本文（范围与拍板）  
2. `PLAN.md`（任务级 checklist）  
3. `CAP-BUSINESS-DECISIONS.md`（能力要/不要）  
4. `reports/06`（测试场设计；**忽略其中算法任务 SAM 强制项**，以本文为准）  
5. `reports/01`～`04`（能力与缺口）  
6. `reports/05`（Windows / certify 可迁移经验）  
7. 学习仓参考（只读思想）：`F:/biofactory/rebekah-learn`（勿引入私有 DLL）

---

## 6. 规划侧收尾声明

本目录调研与方案已按产品拍板修订完毕；**后续编码、测试场落地、certify 与删 Python 由实施负责人按 `PLAN.md` 推进。** 规划对话任务结束。
