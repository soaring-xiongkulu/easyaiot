# Worktree 双轨操作说明

> 权威执行规则见 [`EXECUTION.md`](./EXECUTION.md)。本文只描述路径与日常命令。

## 布局

| 角色 | 绝对路径 | 分支 | 用途 |
|------|----------|------|------|
| Oracle | `F:/acme` | `main`（tag `runtime-parity-oracle-baseline`） | Python runtime 行为真理；`record-python` |
| Candidate | `F:/acme/.worktrees/runtime-parity` | `feat/runtime-parity` | 修订 VIDEO + C++ RUNTIME；日常开发 |

`.worktrees/` 必须被 gitignore，不得提交 worktree 内容。

## 环境变量

```bat
set ACME_ORACLE_ROOT=F:\acme
set ACME_CANDIDATE_ROOT=F:\acme\.worktrees\runtime-parity
```

Gate / 构建脚本应优先读上述变量，避免写死相对路径导致打到错误 worktree。

## 创建（Phase -1）

在 **oracle 根**（`F:/acme`）执行：

```bat
git check-ignore -v .worktrees
git worktree add .worktrees/runtime-parity -b feat/runtime-parity
git worktree list
```

若分支已存在：

```bat
git worktree add .worktrees/runtime-parity feat/runtime-parity
```

## 日常

- 编码 / 编译 RUNTIME / 改 VIDEO 编排：进入 **candidate** 目录。  
- 录制 python golden：在 gate 中指定 `ACME_ORACLE_ROOT`，**不要**在 oracle 改三服务代码。  
- 共享中间件：`127.0.0.1:15432` / `16379` / SRS / ZLM；任务与端口错开。  

## 禁止

- 在 oracle 为「过 certify」修改 `VIDEO/services/*_algorithm_service/**`  
- 用 `git clean` 清理另一 worktree 的未跟踪文件  
- 文件本体复制/移动/删除不经 `tools/runtime_parity/safe_fsops.py`  
