# Brief — FR-B1: Post-process 真 sink（Python-first）

## HARD RULE — NO NESTED SUBAGENTS
Do ALL work yourself. No Task tool.

## 0. Python-first
Read BEFORE writing Java:
1. `VIDEO/_retired_python_video/app/services/post_process_service.py`（及 enqueue / sink 调用链）
2. `VIDEO/_retired_python_video/app/services/alert_post_orchestrator.py` 若相关
3. Java: `PostProcessService`, `PostProcessSinkClient`, `application-local.yaml` `post-process.use-stub-enqueue`

## Goal
- 关闭 local/mini 默认 stub **或** 提供可配置真 sink 路径，使 `use-stub-enqueue=false` 时真实 HTTP/Kafka 调用 iot-sink（对齐 Python）
- 不再仅写审计假计数；无 sink 可达时返回明确错误（非 silent stub success）
- 更新 GAP §4「Post-process → iot-sink」行
- `certify --phase 0` exit 0；若有 p2 post_process case 尽量绿或诚实说明
- Commit + `.superpowers/sdd/briefs/fr-b1-report.md`

## Toolchain
`JAVA_HOME=F:\acme\.tools\jdk-21.0.2`；Maven `F:\acme\.tools\apache-maven-3.9.16\bin`

## Return
STATUS, commits, Python files read, GAP §4, phase0, concerns
