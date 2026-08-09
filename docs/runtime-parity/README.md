# RUNTIME 能力收归与 Windows 对等 — 文档索引

## 阶段目标（FINAL）

将 VIDEO 侧 **Python 算法执行后端**（`executor=python`）能力按「帧内 → C++ RUNTIME / 帧后 → VIDEO」收归，**功能表现与 Python 路径等价**，**Windows 可编译可运行**，最终删除 Python runtime。

**产品拍板：** 测试场、C++ Runtime、追踪及几乎全部算法任务能力均为 **要**；**仅算法任务 SAM 砍掉**；**`AI/` 标注 SAM 保留**。

**评判标准：** 标准测试场 certify 功能表现一致。  
**不含：** 将 `AI/` 训练实验并进 Runtime。

## 交接入口（给实施负责人）

→ **[`EXECUTION.md`](./EXECUTION.md)**（执行手册：阶段门控 / Worktree / 安全 FS / Git / Subagent）  
→ [`WORKTREE.md`](./WORKTREE.md) · [`AGENT-CONTEXT.md`](./AGENT-CONTEXT.md)  
→ **[`HANDOFF.md`](./HANDOFF.md)**（范围拍板）  
→ [`PLAN.md`](./PLAN.md)（Phase 任务）  
→ [`CAP-BUSINESS-DECISIONS.md`](./CAP-BUSINESS-DECISIONS.md)

## 报告目录

| 文件 | 调研范围 |
|------|----------|
| `reports/01-python-realtime.md` | Python realtime 能力清单 |
| `reports/02-python-snap-patrol.md` | Python snap / patrol |
| `reports/03-cpp-runtime-baseline.md` | C++ 基线与 Windows 阻滞 |
| `reports/04-video-absorb-surface.md` | VIDEO 帧后吸收面 |
| `reports/05-rebekah-windows-lessons.md` | 学习项目可迁移经验 |
| `reports/06-equivalence-testbed.md` | 等价测试场设计（算法任务 SAM 项以 HANDOFF 否决为准） |

## 状态

- 2026-08-09：调研完成；方案按最终拍板修订为 **FINAL**；**规划侧工作结束**。  
- 下一动作（实施）：从 **Phase 0 测试场骨架**开工。

## 报告模板

见 `_report-template.md`。
