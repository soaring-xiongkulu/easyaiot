# RUNTIME 行为对等收归 — 执行手册（权威）

> **状态：** ACTIVE（2026-08-09）  
> **上级权威（范围）：** [`HANDOFF.md`](./HANDOFF.md)、[`PLAN.md`](./PLAN.md)、[`CAP-BUSINESS-DECISIONS.md`](./CAP-BUSINESS-DECISIONS.md)  
> **本文件权威：** 阶段门控、仓库双轨、文件本体安全、Git 纪律、Subagent 调度规则  
> **共享背景包（给 Subagent）：** [`AGENT-CONTEXT.md`](./AGENT-CONTEXT.md)、[`WORKTREE.md`](./WORKTREE.md)

---

## 1. 目标与完成定义

将 `executor=python` 的算法热路径（`VIDEO/services/{realtime,snapshot,patrol}_algorithm_service`）按「帧内 → C++ RUNTIME / 帧后 → VIDEO」收归，**Windows 可编译可运行**，行为与 Python oracle **功能表现一致**。

```text
manifest → record-python（oracle worktree）→ run-cpp（candidate worktree）→ certify
仅 certify 全绿可删 Python 三服务；run 绿 ≠ 可替换
```

- 算法任务 SAM：**不做**；`AI/` 标注 SAM：**保留**  
- 热路径模型：**仅 ONNX**  
- 禁止引入 rebekah 私有 CompatibleLib / vendor DLL  

---

## 2. 双 Worktree 布局

详见 [`WORKTREE.md`](./WORKTREE.md)。摘要：

| 角色 | 路径 | 分支 | 用途 |
|------|------|------|------|
| Oracle | `F:/acme` | `main` + tag `runtime-parity-oracle-baseline` | 冻结 Python runtime 行为；`record-python` |
| Candidate | `F:/acme/.worktrees/runtime-parity` | `feat/runtime-parity` | 修订 VIDEO + C++ RUNTIME；日常开发与 `run-cpp` |

共享 Docker 中间件（Postgres `15432` / Redis `16379` / MinIO / SRS）；用不同 `task_id` / `control_port` / 流名防冲突。

环境变量：

- `ACME_ORACLE_ROOT=F:/acme`
- `ACME_CANDIDATE_ROOT=F:/acme/.worktrees/runtime-parity`

---

## 3. 阶段门控（未过门禁止进入下一阶段）

每个阶段结束必须留下 **GATE 记录**（写入 `docs/runtime-parity/gates/PHASE_<N>_GATE.md` 或更新本表勾选），由编排 Agent **人工审查证据**后再开下一阶段。

### Phase -1 — 仓库就位

**入口：** 本手册已落盘。  
**出口（全部满足）：**

| # | 门控项 | 证据 |
|---|--------|------|
| G-1 | `docs/runtime-parity/**` 已在 git 中（含本手册） | `git ls-files docs/runtime-parity` |
| G-2 | `.gitignore` 含 `.worktrees/`，且 `.local/`、`.tools/` 已忽略 | `git check-ignore -v .worktrees .local .tools` |
| G-3 | 存在 tag `runtime-parity-oracle-baseline` | `git rev-parse runtime-parity-oracle-baseline` |
| G-4 | candidate worktree 存在且在 `feat/runtime-parity` | `git worktree list` |
| G-5 | [`WORKTREE.md`](./WORKTREE.md) / [`AGENT-CONTEXT.md`](./AGENT-CONTEXT.md) 可读 | 文件存在 |

**未过门：** 不得改 `RUNTIME/` 或 VIDEO 编排收归代码。

### Phase 0 — 测试场骨架

**入口：** Phase -1 全绿。  
**出口：**

| # | 门控项 | 证据 |
|---|--------|------|
| G-0.1 | `testdata/runtime-parity/{manifest,thresholds}.json` 存在且 `doctor` 通过 | `python tools/runtime_parity_gate.py doctor` exit 0 |
| G-0.2 | mock alert hook + RTSP relay 可起停 | testbed README 命令实测 |
| G-0.3 | ≥ **3** 个 P0 case 有 **python golden**（从 **oracle** 录出） | `testdata/runtime-parity/golden/python/<case>/` |
| G-0.4 | `run --executor cpp` 能对至少 1 个 case 采样（允许大量 fail） | `logs/runtime_parity_report.json` 含 cpp 侧产物路径 |
| G-0.5 | `certify` 能产出红清单（不得伪造 ok=true） | 报告存在且缺层为 `fail`/`not_sampled` |

**未过门：** 不得开始 Windows RUNTIME 功能补齐以外的「宣称对等」工作；Phase 1 构建允许并行准备，但不得跳过 G-0.3。

### Phase 1 — Windows RUNTIME 可编译可跑

**入口：** G-0.1～G-0.3 已过（G-0.4/0.5 可与 Phase 1 重叠收尾）。  
**出口：**

| # | 门控项 | 证据 |
|---|--------|------|
| G-1.1 | MSVC x64 Release 产出 `RUNTIME.exe` | 构建日志 + 文件存在 |
| G-1.2 | `vendor/win-x64`（或文档等价路径）可加载 ORT（DirectML 或 CPU） | 启动日志 `infer_ep` |
| G-1.3 | candidate 上 VIDEO 能拉起 cpp 任务 | daemon 日志 |
| G-1.4 | `win_cpp`：`rt_p0_heartbeat_lifecycle` + `rt_p0_detect_single_onnx` 双侧可采样 | gate 报告 |

**未过门：** 不得进入 Phase 2「契约清零」以外的大范围帧内新能力（可并行读代码）。

### Phase 2 — 契约与静默丢失清零

**入口：** G-1.3 或 Linux 上等价「cpp 可拉起」。  
**出口：**

| # | 门控项 | 证据 |
|---|--------|------|
| G-2.1 | AlgorithmTask 关键字段均写入 ini 或显式 `unsupported` 日志 | ini 样例 + 启动 WARNING 列表 |
| G-2.2 | hook payload 字段与 python 对齐（含 face/plate flags 策略写死） | `rt_p0_alert_hook_roi` certify 字段层绿 |
| G-2.3 | 无「假支持」：未实现 CAP 不得静默当成功 | health/unsupported 列表抽查 |

**未过门：** 不得删 Python；不得宣称匹配链已在仅 cpp 下可用。

### Phase 3 — VIDEO 吸收帧后触发

**入口：** G-2.2。  
**出口：**

| # | 门控项 | 证据 |
|---|--------|------|
| G-3.1 | cpp 告警 hook 后触发 face/plate matching（与 python 等价触发） | `vid_p0_face_match_chain` 仅 cpp 绿 |
| G-3.2 | 后处理 enqueue 路径接通 | platform P1 case 或报告层绿 |
| G-3.3 | UI 按 executor 门禁，无假开关 | AlgorithmTaskModal 变更 + 截图/说明 |

**未过门：** 不得进入「追踪/门控等大功能」以外的删除准备。

### Phase 4 — C++ 帧内按红清单补齐

**入口：** G-3.1（匹配链不挡 tracking 开发，但 **删除 Python 前** 必须 G-3.1）。  
**出口：**

| # | 门控项 | 证据 |
|---|--------|------|
| G-4.1 | P0 detect/alarm/lifecycle certify 绿 | report |
| G-4.2 | P1：`rt_p1_motion_gate`、`rt_p1_tracking_stable` 绿 | report |
| G-4.3 | snap/patrol 调度 P0 case 绿 | report |
| G-4.4 | overlay/RTMP 达 `thresholds.json` | report L_overlay/L_stream |

**驱动规则：** 只修 `logs/runtime_parity_report.json` 红项。

### Phase 5 — 全量 certify 与删除 Python runtime

**入口：** G-4.1～G-4.4 + linux_full 与 win_cpp 计划内 case 全绿（或产品签字豁免清单落盘）。  
**出口：**

| # | 门控项 | 证据 |
|---|--------|------|
| G-5.1 | `certify --profile linux_full` exit 0 且 ok=true | 报告 + 哈希写入 `CERTIFY_STATUS.md` |
| G-5.2 | `certify --profile win_cpp` exit 0 或豁免清单经产品确认 | 同上 |
| G-5.3 | **删除三服务前** 必须走 §4 安全文件脚本：dry-run 清单经编排 Agent 书面确认后再 `--execute` | dry-run 输出归档 |
| G-5.4 | 默认无法再选 `executor=python`；CI 去掉 python executor job | 代码审查 |

**未过 G-5.3：** 任何 Agent **禁止** `rm`/`Remove-Item`/`git clean` 删除三服务目录。

---

## 4. 文件本体操作安全规则（强制）

**适用范围：** 复制、移动、重命名、删除**文件或目录本体**（非「编辑文件内容」）。包括 Phase 5 删除 Python 服务、搬迁 `_retired/`、同步 golden 目录等。

### 4.1 唯一入口

必须使用：

```text
python tools/runtime_parity/safe_fsops.py <subcommand> ...
```

禁止 Agent 直接调用：`rm -rf`、`Remove-Item -Recurse`、`Move-Item`、`Copy-Item`、`shutil.rmtree`（业务代码内除外）、`git clean`。

### 4.2 两阶段协议

1. **试运行（默认）：** 不加 `--execute`。脚本执行到「破坏性动作之前」的最后一步，打印完整清单（源/目标/动作/字节数/是否在允许根下），写入 `logs/safe_fsops_dryrun_<ts>.json`，**exit 0 且无实际变更**。  
2. **编排 Agent 审查：** 必须阅读清单；确认无越界路径、无错误目录、无误删。将确认记录进 `docs/runtime-parity/gates/` 或 commit message。  
3. **正式执行：** 同一命令追加 `--execute --confirm-token <dryrun文件中的token>`。token 不匹配则拒绝执行。

### 4.3 多重检查

脚本必须校验：

- 路径解析为绝对路径且归一化（拒绝 `..` 逃逸）  
- 所有操作路径位于允许根：`ACME_ORACLE_ROOT` / `ACME_CANDIDATE_ROOT` / 显式 `--allow-root`（可重复）  
- 删除类：目标必须命中预声明的 glob/前缀白名单（如仅 `VIDEO/services/{realtime,snapshot,patrol}_algorithm_service`）  
- 拒绝删除：仓库根、`.git`、`.worktrees` 整树、`C:\`、用户家目录等  
- dry-run 与 execute 的清单哈希一致，否则拒绝  

### 4.4 内容编辑

编辑源码/配置内容可用常规编辑工具；**不**走 safe_fsops。若「编辑」实际是替换整个目录树，仍算本体操作。

---

## 5. Git 纪律

### 5.1 按开发波次提交

- 每个可审查单元结束（Task / Gate 子项）做一次 commit。  
- 消息风格：`docs:` / `test:` / `feat:` / `fix:` / `build:` + 简短 why。  
- 仅在用户已授权本项目波次提交时执行（本执行手册开工即授权波次提交）。

### 5.2 禁止的破坏性 Git 指令

**绝对禁止：**

- `git clean -fd` / `git clean -fdx`（丢弃未跟踪文件）  
- `git reset --hard`（除非用户对本句明确点名，且不针对无关未跟踪文件）  
- `git push --force` 到 `main`/`master`  
- `git checkout -- .` 用于「清掉别人的未跟踪工作」  
- 修改 `git config`  

**允许：** 正常 `add`/`commit`/`status`/`diff`/`log`；创建 worktree；在 feature 分支常规 merge/rebase（无 `-i`）。

### 5.3 Oracle 纯度

- **禁止**在 oracle worktree 修改 `VIDEO/services/*_algorithm_service/**` 以实现「对等」。  
- ops 修复（代理、camera 竞态）可留 main；收归相关只进 candidate。

---

## 6. Subagent 调度规则（编排 Agent 必遵）

### 6.1 角色

| 角色 | 谁 | 职责 |
|------|----|------|
| 编排 | 主会话 Agent | 调度、门控审查、合并结论、Git 波次、safe_fsops 审批 |
| 执行 / 阅读 / 规划 | Subagent | 读代码、写实现、跑局部验证、出书面报告 |
| 审查 | 另一 Subagent（推荐） | 对照 EXECUTION/GATE 审报告与 diff，不共享执行上下文 |

### 6.2 模型

- Subagent 模型：**`composer-2.5`**（**不要** `composer-2.5-fast`）。  
- 未点名时默认 `inherit` 仅用于编排侧；委派执行/审查时显式 `model: composer-2.5`。

### 6.3 提示词必须自洽

Subagent **没有**主会话上下文。每次 prompt 必须包含：

1. 目标与非目标（3～8 条）  
2. 允许修改的路径白名单 / 禁止路径  
3. 必读文档绝对路径：至少 `AGENT-CONTEXT.md`、本阶段相关 `reports/0x`、`WORKTREE.md`  
4. 验收命令与门控编号（如 G-0.1）  
5. 输出格式：变更文件列表、命令与退出码、风险、是否建议过门  
6. Git / safe_fsops / 质量注释要求摘要  

### 6.4 编排审查

- 不盲目信任 Subagent「已完成」；核对门控证据。  
- 重要阶段：派 **审查 Subagent** 只读审 diff + 报告。  
- 红清单驱动：无 case 不扩 scope。

---

## 7. 代码质量

- 与当前 main 线风格一致（命名、错误处理、日志）。  
- 关键路径保留可供人审的注释：契约假设、与 Python 行为差异、为什么不静默降级。  
- 禁止为过门禁降低 `thresholds.json` 而不改实现（改阈值须债表说明）。  
- C++：Windows 垫片与 Linux 行为差异必须注释。  

---

## 8. 日常对照命令（摘要）

```bat
set ACME_ORACLE_ROOT=F:\acme
set ACME_CANDIDATE_ROOT=F:\acme\.worktrees\runtime-parity

python tools\runtime_parity_gate.py doctor
python tools\runtime_parity_gate.py record-python --case rt_p0_detect_single_onnx
python tools\runtime_parity_gate.py run --executor cpp --case rt_p0_detect_single_onnx
python tools\runtime_parity_gate.py certify --case rt_p0_detect_single_onnx
```

安全删除示例：

```bat
python tools\runtime_parity\safe_fsops.py delete-tree --path VIDEO/services/realtime_algorithm_service --allow-root %ACME_CANDIDATE_ROOT%
REM 审查 logs\safe_fsops_dryrun_*.json 后：
python tools\runtime_parity\safe_fsops.py delete-tree --path ... --allow-root ... --execute --confirm-token <token>
```

---

## 9. 文档地图

| 文件 | 用途 |
|------|------|
| 本文件 | 执行门控与纪律 |
| [`WORKTREE.md`](./WORKTREE.md) | 双轨路径与操作 |
| [`AGENT-CONTEXT.md`](./AGENT-CONTEXT.md) | Subagent 背景包 |
| [`HANDOFF.md`](./HANDOFF.md) | 产品拍板 |
| [`PLAN.md`](./PLAN.md) | Task checklist |
| [`gates/`](./gates/) | 各阶段 GATE 证据 |

---

## 10. 开工声明

本手册生效后，编排 Agent 从 **Phase -1** 开始持续推进；每一阶段仅在对应门控证据齐备后进入下一阶段。
