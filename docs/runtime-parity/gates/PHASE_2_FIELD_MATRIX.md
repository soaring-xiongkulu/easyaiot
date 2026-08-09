# PHASE_2_FIELD_MATRIX — AlgorithmTask → RUNTIME ini

> **Date:** 2026-08-09  
> **Phase:** 2 — 契约与静默丢失清零  
> **Authority:** `CAP-BUSINESS-DECISIONS.md`, `reports/03-cpp-runtime-baseline.md`, `reports/04-video-absorb-surface.md`

## Legend

| Status | Meaning |
|--------|---------|
| **supported** | Written to ini and consumed by C++ hot path |
| **partial** | Written to ini; parsed; hook passthrough or skeleton only — frame-in behavior Phase 4+ |
| **unsupported** | Written to ini `[unsupported]` + startup `LOG(WARNING)`; not implemented in C++ frame-in |
| **video_only** | Written for contract audit; execution stays in VIDEO (Phase 3+) |

## Core task & stream

| Source (AlgorithmTask / Device) | ini key | Status | Notes |
|---------------------------------|---------|--------|-------|
| `devices[].source` / `rtsp_direct` | `[video] rtsp_url` | supported | Primary device RTSP |
| `devices[].ai_rtmp_stream` / `rtmp_output_url` | `[video] rtmp_url` | supported | |
| `model_ids` → first `.onnx` | `[ai] model_path` | supported | Single model hot path |
| `model_ids` → additional `.onnx` | `[models] extra_paths` | unsupported | `CAP-MULTI-MODEL` when non-empty |
| `detect_conf` | `[alarm] confidence_threshold` | supported | Alarm filter only (infer threshold separate) |
| `extract_interval` (realtime) | `[ai] frame_skip`, `[video_task] frame_skip` | supported | |
| `frame_skip` (snap) | `[ai] frame_skip`, `[video_task] frame_skip` | supported | Snap uses DB `frame_skip`, not `extract_interval` |
| `alert_event_enabled` | `[alarm] enable`, `[features] enable_alarm` | supported | |
| `alert_event_suppress_time` | `[alarm] cooldown_time` | supported | |
| `model_names` | `[video_task] algorithm_name` | supported | |
| `task_type` | `[video_task] task_type` | supported | `snap` → `snapshot` for hook |
| `cron_expression` | `[video_task] cron_expression` | partial | C++ parses minute+hour only |
| `patrol_mode` / `patrol_interval_sec` / `patrol_pool_size` | `[video_task] patrol_*` | partial | `hybrid` → unsupported |
| `focus_device_id` | `[patrol_extra] focus_device_id` | unsupported | `CAP-PATROL-HYBRID` |
| `prefer_gpu` + env | `[ai] prefer_gpu`, `force_cpu` | supported | |
| `runtime_control_port` | `[task] control_port` | supported | |
| `id` | `[task] id` | supported | |
| Device regions | `[regions] {deviceId}_{name}=[[x,y],...]` | supported | Normalized 0–1 coords |
| `devices` | `[video_task] devices_json` | supported | Multi-device snap/patrol |

## Tracking & gating

| Source | ini key | Status | Notes |
|--------|---------|--------|-------|
| `tracking_enabled` + `tracking_*` | `[tracking] *` | unsupported | `CAP-TRACKING` when enabled |
| `motion_gate_enabled` + `motion_gate_config` | `[motion_gate] *` | unsupported | `CAP-MOTION-GATE` when enabled |
| `alert_class_names` | `[alert_filter] alert_class_names` | unsupported | `CAP-ALERT-CLASS-FILTER` when non-empty |

## Face / plate flags (G-2.2 写死策略)

| Source | ini key | Status | Notes |
|--------|---------|--------|-------|
| `face_detection_enabled` | `[alert_filter]`, `[hook]` | **partial** | **Hook passthrough supported** (`Detech` JSON); frame-in class filter Phase 4 → `CAP-FACE-FILTER` |
| `plate_detection_enabled` | `[alert_filter]`, `[hook]` | **partial** | Same as face |

**策略（冻结）：** C++ 从 ini `[hook]` 读取并写入告警 JSON；VIDEO `alert_hook_service._resolve_detection_switches` 在缺字段时回查 DB 任务（兜底，不静默默认 true）。

## VIDEO 帧后（ini 审计 + `[unsupported]`）

| Source | ini key | Status | Notes |
|--------|---------|--------|-------|
| `face_matching_enabled` + libraries | `[matching] *` | video_only | `CAP-FACE-MATCH` — Phase 3 VIDEO absorb |
| `plate_matching_enabled` + libraries | `[matching] *` | video_only | `CAP-PLATE-MATCH` |
| `matching_business_tags` | `[matching] matching_business_tags` | video_only | |
| `post_process_enabled` + script | `[post_process] *` | video_only | `CAP-POST-PROCESS` |
| `pose_analysis_enabled` / `pose_intent_*` | `[pose] *` | video_only | `CAP-POSE` |
| `sam_supplement_enabled` | `[sam] supplement_enabled` | unsupported | Product veto `CAP-SAM-TASK` |
| `defense_mode` / `defense_schedule` | `[defense] *` | video_only | `CAP-DEFENSE` — hook/Kafka 侧 |
| `alert_notification_*` | _(not in ini)_ | video_only | Daemon / hook only |

## Hook payload golden keys (G-2.2)

Both python `run_deploy` and cpp `Detech::_alarmSenderThreadFunc` must emit:

`object`, `event`, `device_id`, `device_name`, `task_type`, `correlation_id`, `time`, `image_path`, `region`, `information`, `face_detection_enabled`, `plate_detection_enabled`

Reference: `tools/runtime_parity/hook_payload_fields.py`, tests `VIDEO/test_hook_payload_fields.py`.

## G-2.3 禁止假支持

1. **VIDEO** `generate_runtime_ini`: enabled 但未热路径实现的 CAP → `[unsupported] CAP-xxx=true` + `logger.warning`
2. **C++** `ConfigParser::parse`: 解析契约段；derive + log `unsupported cap=...`
3. **C++** `Detech::start`: 再次 `LOG(WARNING)` 每条 unsupported
4. **GET `/health`**: `unsupported_caps` JSON 数组

## 未映射（刻意 / 编排层）

| Field | Reason |
|-------|--------|
| `task_name`, `task_code`, `description` | UI/DB only |
| `status`, `run_status`, `service_*` | VIDEO daemon 维护 |
| `schedule_policy`, `target_node_id`, `node_id` | Cluster launcher |
| `rtmp_input_url` | Python-only pull variant |
| `space_id`, snap stats | Snap space / VIDEO stats |
