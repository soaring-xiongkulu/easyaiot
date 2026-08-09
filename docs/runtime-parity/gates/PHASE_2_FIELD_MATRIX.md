# Phase 2 — AlgorithmTask → ini → RUNTIME 字段矩阵

> 状态：草稿+首轮落地（2026-08-09）  
> 关联：G-2.1 / G-2.3；`runtime_config_service.generate_runtime_ini`；`ConfigParser.cpp`

## 约定

| status | 含义 |
|--------|------|
| **supported** | VIDEO 写入 ini 且 C++ 读取生效 |
| **unsupported** | 写入 `[unsupported]` + VIDEO WARNING；C++ 打 WARNING，不假装成功 |
| **video_only** | 帧后能力，应在 VIDEO 吸收（Phase 3），热路径不实现 |
| **cut** | 产品砍掉（算法任务 SAM） |

## 矩阵（核心）

| AlgorithmTask 字段 | ini | status | 备注 |
|--------------------|-----|--------|------|
| task_type | video_task.task_type | supported | snap→snapshot |
| model_ids / model_names | ai.model_path / algorithm_name | supported | 解析 ONNX |
| detect_conf | alarm.confidence_threshold | supported | |
| extract_interval / frame_skip | ai.frame_skip + video_task.frame_skip | supported | |
| rtmp_output_url / ai_rtmp_stream | video.rtmp_url + features.enable_rtmp | supported | |
| alert_event_enabled | alarm.enable / features.enable_alarm | supported | |
| alert_event_suppress_time | alarm.cooldown_time | supported | |
| prefer_gpu | ai.prefer_gpu / force_cpu | supported | |
| runtime_control_port | task.control_port | supported | |
| cron / patrol_* | video_task.* | supported | snap/patrol |
| devices / regions | devices_json / regions.* | supported | |
| tracking_* | unsupported.tracking | unsupported | Phase 4 |
| motion_gate_* | unsupported.motion_gate | unsupported | Phase 4 |
| pose_* | unsupported.pose_* | unsupported | |
| sam_supplement_* | unsupported.sam_supplement | **cut** | 不得静默成功 |
| post_process_* | unsupported.post_process | video_only | Phase 3 |
| face_matching_* / plate_matching_* | unsupported.*_matching | video_only | Phase 3 |
| face_detection_enabled / plate_detection_enabled | unsupported.*_detection_flag | video_only flags | hook 策略 Phase 2/3 |
| alert_notification_* | unsupported.alert_notification | video_only | |
| alert_class_names | unsupported.alert_class_names | partial | 待 C++ 过滤 |

## G-2.3 机制

1. VIDEO：`_log_cpp_unsupported_fields` 对已开启的 deferred CAP 打 WARNING。  
2. VIDEO：ini 追加 `[unsupported]` 段。  
3. C++：`ConfigParser` 对 `[unsupported]`/`[contract]` 与未知 key 打 WARNING（禁止静默忽略当成功）。

## 下一步（G-2.2）

对齐 alert hook JSON 字段（python vs cpp），含 face/plate flags；更新 `rt_p0_alert_hook_roi` 比较脚本。
