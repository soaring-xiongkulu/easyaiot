# PHASE_3_GATE

- **Date:** 2026-08-09
- **Orchestrator:** Cursor Composer (subagent)
- **Phase:** 3 — VIDEO 吸收帧后触发
- **Verdict:** **PASS**（建议编排 Agent 过门）

## Checklist

| ID | Item | Evidence | OK |
|----|------|----------|----|
| G-3.1 | cpp 告警 hook 后触发 face/plate matching | `alert_post_orchestrator.py` + `alert_hook_service.py` 调度；`test_alert_post_orchestrator.py` 断言 cpp 入队 | **PASS** |
| G-3.2 | 后处理 enqueue 路径接通 | 同模块 `_try_post_process_enqueue` → `enqueue_post_process_request`；单测 `test_cpp_face_matching_enqueued` 断言 `post_process=True` | **PASS** |
| G-3.3 | UI 按 executor 门禁 | `AlgorithmTaskModal.vue`：`isCppExecutor` 禁用 tracking/motion_gate/SAM；保留 face/plate/post_process 并更新 help；提交时强制清零假开关 | **PASS** |

## G-3.1 设计要点

```text
C++ RUNTIME 告警 HTTP hook
  → process_alert_hook（提前解析 alert_event_task）
  → schedule_post_alert_orchestration（仅 executor=cpp）
  → 读 image_path + information.detections
  → face_capture_queue / plate_capture_queue（懒启动 Worker）
  → /video/face|plate/matching/publish → Kafka 匹配链
```

- **不双触发：** `executor=python` 时 orchestrator 返回 `not_cpp_executor`，匹配仍由 `run_deploy.try_send_*` 负责。
- **Kafka 抑制不挡匹配：** `alert_event_task` 查询前移至 Kafka 抑制之前，cpp 帧后能力不受 `alert_event_suppress_interval` 影响。

## G-3.2 后处理

- 触发条件与 Python 一致：`task_needs_sink_processing(task)`（`post_process_enabled` / `pose_*`）。
- 使用 hook `information.detections` + `image_path` 组装 ctx，经 `post_process_sink_client.publish_post_process_request_async` 入队 iot-sink。

## G-3.3 UI

| 能力 | cpp UI | 实际落点 |
|------|--------|----------|
| tracking / motion_gate / SAM | 隐藏或提交强制 false | 帧内未实现（Phase 4） |
| face/plate matching | 可配置 | VIDEO hook 后触发 |
| post_process / pose | 可配置 | VIDEO hook 后入队 |

## 测试命令

```text
cd F:/acme/.worktrees/runtime-parity
set PYTHONPATH=VIDEO
python VIDEO/test_alert_post_orchestrator.py   # exit 0
python VIDEO/test_runtime_ini_contract.py      # exit 0（Phase 2 回归）
```

## 风险 / 未完成

- `vid_p0_face_match_chain` 尚未写入 `manifest.json`；端到端 certify 需在具备 Kafka/人脸库夹具的环境补跑。
- 人脸/车牌 ONNX 模型依赖本机 `face_capture_service`；无模型时队列会 WARN 跳过（不静默成功）。
- 后处理入队依赖 iot-sink 可达；不可达时 `publish_post_process_request` 记录 WARNING（与 Python 路径一致）。

## Orchestrator acceptance

- 验收 [Phase 3](af4450a9-a3b8-407c-a152-aec260ef45b3)：commit `fa180e0`；`test_alert_post_orchestrator` / `test_runtime_ini_contract` 复验 exit 0。
- **Phase 3：PASS**（2026-08-09 编排）。
- `vid_p0_face_match_chain` 端到端 certify 为加强项，不挡 Phase 4。
- 进入 Phase 4（优先 G-4.1 P0 certify）。
