# Subagent 共享背景包（Runtime Parity）

> 每次派发 Subagent 时，在 prompt 中给出**本文件的绝对路径**并要求先读。  
> 编排规则与门控：`F:/acme/docs/runtime-parity/EXECUTION.md`  
> Worktree：`F:/acme/docs/runtime-parity/WORKTREE.md`

## 项目一句话

公司仓 `F:/acme`（EasyAIoT 硬分叉）。任务：把 Python 算法执行后端能力行为对齐收归到 **C++ RUNTIME（帧内）+ VIDEO（帧后）**，Windows 可跑，最终删除 Python 三服务。完成定义是 **certify 全绿**，不是 API 通。

## 双 Worktree

- Oracle：`F:/acme`（main）— 冻结 `VIDEO/services/{realtime,snapshot,patrol}_algorithm_service` 行为  
- Candidate：`F:/acme/.worktrees/runtime-parity`（`feat/runtime-parity`）— 只在此改 RUNTIME / VIDEO 编排 / WEB 门禁 / 测试场  

环境变量：`ACME_ORACLE_ROOT`、`ACME_CANDIDATE_ROOT`。

## 产品冻结（不可自作主张）

- **要：** 测试场、Windows、追踪、多模型(ONNX)、区域、告警过滤/冷却、心跳、RTMP/叠框、运动门控、人脸车牌过滤+库匹配（触发上收 VIDEO）、后处理、姿态、布防、Cron 抓拍、patrol hybrid、国标源、NVENC 降档等 — 见 `CAP-BUSINESS-DECISIONS.md`  
- **不要：** 算法任务 SAM；热路径内嵌 ultralytics/.pt（导出 ONNX）；rebekah 私有 DLL  
- **保留：** `AI/` 标注 SAM  

## 必读调研（按需）

| 路径 | 内容 |
|------|------|
| `F:/acme/docs/runtime-parity/HANDOFF.md` | 拍板与交接 |
| `F:/acme/docs/runtime-parity/PLAN.md` | Phase/Task checklist |
| `F:/acme/docs/runtime-parity/reports/01-python-realtime.md` | Python 能力 |
| `F:/acme/docs/runtime-parity/reports/02-python-snap-patrol.md` | snap/patrol |
| `F:/acme/docs/runtime-parity/reports/03-cpp-runtime-baseline.md` | C++ 缺口 |
| `F:/acme/docs/runtime-parity/reports/04-video-absorb-surface.md` | VIDEO 帧后吸收 |
| `F:/acme/docs/runtime-parity/reports/05-rebekah-windows-lessons.md` | Windows/certify 可迁移 |
| `F:/acme/docs/runtime-parity/reports/06-equivalence-testbed.md` | 测试场设计（忽略算法任务 SAM 强制项） |
| `F:/biofactory/rebekah-learn/docs/decisions/ORACLE_GATE.md` | 门禁思想（只读） |
| `F:/biofactory/rebekah-learn/docs/decisions/PARITY_CERTIFY.md` | 分层 certify（只读） |

## 架构落点

```text
VIDEO：编排、ini、启停、hook 消费、Kafka、人/车牌匹配触发、后处理、UI
   ▲ HTTP hook / heartbeat
C++ RUNTIME：拉流→解码→(motion_gate)→ONNX→track→region→emit / RTMP
```

禁止静默降级：字段未进 ini / 未实现必须打日志。

## 质量与 Git

- 代码风格与 main 一致；关键路径留可供人审的注释。  
- 波次 commit；禁止 `git clean -fd`、`reset --hard`、force push main。  
- 文件本体 copy/move/delete：仅 `python tools/runtime_parity/safe_fsops.py`（先 dry-run，编排确认后再 `--execute --confirm-token`）。  

## 学习仓边界

可借鉴：`F:/biofactory/rebekah-learn` 的 MSVC、vendor、supervisor、certify 纪律。  
不可引入：CompatibleLib、Frida 打原版作为 acme 主路径、私有 DLL 再分发。

## Subagent 输出模板（强制）

```markdown
## 做了什么
## 变更文件列表
## 运行的命令与退出码
## 门控证据（对应 G-x.y）
## 风险 / 未完成
## 是否建议编排 Agent 过门（是/否 + 理由）
```
