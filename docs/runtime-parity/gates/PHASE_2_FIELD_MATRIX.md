# PHASE_2_FIELD_MATRIX — ini / Hook 字段缺口清单（编排用）

- **Date:** 2026-08-09
- **Phase:** 2 — ini / hook 契约清零
- **Scope:** `executor=cpp` 路径；对照源文件见文末 Evidence
- **Verdict:** **DRAFT**（供编排 Agent 拆任务；非 gate PASS）

---

## 0. 结论摘要

| 层级 | 状态 | 说明 |
|------|------|------|
| **ini key 字面量** | ✅ 无「写了未读」 | `generate_runtime_ini` 写出的 key 均被 `ConfigParser.cpp` 解析 |
| **AlgorithmTask → ini** | ⚠️ 大量 DB 字段未序列化 | cpp 路径静默丢失 tracking / alert_class / 匹配 / 姿态等 |
| **Hook JSON** | ⚠️ 部分字段 cpp 缺失 | `face_detection_enabled` / `plate_detection_enabled` 未发；`event` 语义与 python 不一致 |
| **CAP 门禁** | ❌ 未实现 | 任务启用 cpp 不支持能力时，daemon/launcher **尚无** WARNING |

---

## 1. AlgorithmTask 字段清单（`VIDEO/models.py`）

按业务分组；**W** = `generate_runtime_ini` 是否写入 ini；**R** = C++ `ConfigParser` 是否读取对应 ini key。

### 1.1 任务标识 / 调度（不进 ini 或仅启动时用）

| DB 字段 | W | R | 备注 |
|---------|---|---|------|
| `id` | ✅ `[task] id` | ✅ | |
| `task_name` | ❌ | ❌ | python hook `event` 用任务名；ini 用 `model_names` → `algorithm_name`（**语义分叉**） |
| `task_code` | ❌ | ❌ | 编排元数据 |
| `task_type` | ✅ `[video_task] task_type` | ✅ | `snap`→hook 写 `snapshot` |
| `executor` | ❌ | ❌ | daemon 分支用，不进 ini |
| `schedule_policy` / `target_node_id` / `node_id` | ❌ | ❌ | 集群编排 |
| `runtime_bin_path` / `runtime_control_port` | 部分 | ✅ `control_port` | bin 路径启动时用；port 写入 ini |
| `is_enabled` / `run_status` / `status` / 统计列 | ❌ | ❌ | VIDEO 侧状态 |
| `service_*` | ❌ | ❌ | 由心跳回写 DB |

### 1.2 模型 / 推理

| DB 字段 | W | R | 备注 |
|---------|---|---|------|
| `model_ids` | ✅ 解析为 `[ai] model_path` | ✅ | 仅 **首个** ONNX；非多模型串联 |
| `model_names` | ✅ `[video_task] algorithm_name` | ✅ | 取逗号首段；**非** `task_name` |
| `detect_conf` | ✅ `[alarm] confidence_threshold` | ✅ | |
| `extract_interval` | ✅ `[ai]`+`[video_task] frame_skip` | ✅ | realtime 抽帧 |
| `frame_skip` | ✅（snap 回退） | ✅ | `extract_interval` 优先 |
| `prefer_gpu` | ✅ `[ai] prefer_gpu` / `force_cpu` | ✅ | 另可被 env 覆盖 |
| `tracking_*` | ❌ | ❌ | **CAP-TRACKING**；仅 python |
| `motion_gate_*` | ❌ | ❌ | **CAP-MOTION-GATE**；仅 python env |

### 1.3 流 / 设备

| DB 字段 | W | R | 备注 |
|---------|---|---|------|
| `devices`（M2M） | ✅ `rtsp_url` / `devices_json` / `device_id` | ✅ | 主设备 RTSP + 全量 JSON |
| `rtmp_output_url` | ✅ `[video] rtmp_url` + `enable_rtmp` | ✅ | 亦读 `Device.ai_rtmp_stream` |
| `rtmp_input_url` | ❌ | ❌ | python 专用 |
| `DeviceDetectionRegion` | ✅ `[regions]` | ✅ | 按设备查库写入 |
| `focus_device_id` | ❌ | ❌ | **CAP-PATROL-HYBRID**；python patrol 用 |

### 1.4 告警 / 通知

| DB 字段 | W | R | 备注 |
|---------|---|---|------|
| `alert_event_enabled` | ✅ `[alarm] enable` + `[features] enable_alarm` | ✅ | |
| `alert_event_suppress_time` | ✅ `[alarm] cooldown_time` | ✅ | |
| `alert_class_names` | ❌ | ❌ | **CAP-ALERT-CLASS**；python 过滤类别 |
| `face_detection_enabled` / `plate_detection_enabled` | ❌ | ❌ | hook 字段；python 透传，cpp 不发 |
| `face_matching_*` / `plate_matching_*` | ❌ | ❌ | **CAP-FACE-MATCH** / **CAP-PLATE-MATCH** |
| `matching_business_tags` | ❌ | ❌ | python 透传子任务 |
| `alert_notification_*` / `alarm_suppress_time` | ❌ | ❌ | VIDEO `alert_hook_service` 查库 |
| `defense_mode` / `defense_schedule` | ❌ | ❌ | **CAP-DEFENSE**；sink/VIDEO 侧 |

### 1.5 抓拍 / 巡检

| DB 字段 | W | R | 备注 |
|---------|---|---|------|
| `cron_expression` | ✅ `[video_task]` | ✅ | snap；C++ 为简化 cron |
| `space_id` | ❌ | ❌ | **CAP-SNAP-SPACE** |
| `patrol_mode` | ✅ `[video_task]` | ✅ | 见 §3.1：`hybrid` 无效 |
| `patrol_interval_sec` / `patrol_pool_size` | ✅ | ✅ | |

### 1.6 扩展能力（python / VIDEO 帧后）

| DB 字段 | W | R | CAP |
|---------|---|---|-----|
| `sam_supplement_*` | ❌ | ❌ | ~~CAP-SAM-TASK~~（**不要**，无需 WARN） |
| `pose_analysis_*` / `pose_intent_*` | ❌ | ❌ | **CAP-POSE** |
| `post_process_*` | ❌ | ❌ | **CAP-POST-PROCESS** |

---

## 2. ini 段 — 已映射（supported）

`runtime_config_service.generate_runtime_ini` ↔ `ConfigParser.cpp` / `Config.h`：

| Section | Key | Task / 来源 | C++ `Config` 字段 |
|---------|-----|-------------|-------------------|
| `[video]` | `rtsp_url` | 主设备 `source` / `rtsp_direct` | `rtspUrl` |
| | `rtmp_url` | `rtmp_output_url` / `ai_rtmp_stream` | `rtmpUrl` |
| | `width` / `height` / `fps` | 固定 1920×1080@25 | `videoWidth` / `videoHeight` / `rtmpFps` |
| `[ai]` | `enable` | 固定 `true` | `enableAI` |
| | `model_path` / `classes_path` | `model_ids` 解析 | `modelPaths` / `modelClasses` |
| | `threads` | 固定 `2` | `threadNums` |
| | `frame_skip` | `extract_interval` ‖ `frame_skip` | `frameSkip` |
| | `prefer_gpu` / `force_cpu` / `gpu_device_id` | `prefer_gpu` + env | `preferGpu` / `forceCpu` / `gpuDeviceId` |
| `[alarm]` | `enable` | `alert_event_enabled` | `enableAlarm` |
| | `hook_url` | `resolve_alert_hook_url()` | `hookHttpUrl` |
| | `confidence_threshold` | `detect_conf` | `alarmConfidenceThreshold` |
| | `cooldown_time` | `alert_event_suppress_time` | `alarmCooldownTime` |
| | `image_dir` | 日志目录下 `alerts` | `alertImageDir` |
| `[task]` | `id` | `task.id` | `taskId` |
| | `control_port` | `runtime_control_port` ‖ `8000+id%1000` | `controlPort` |
| `[video_task]` | `device_id` / `device_name` | 主设备 | `deviceId` / `deviceName` |
| | `task_type` | `task_type`（snap→snapshot 仅 hook） | `taskType` |
| | `algorithm_name` | `model_names` 首段 | `algorithmName` |
| | `alert_hook_url` | 同 hook_url | `alertHookUrl` |
| | `heartbeat_url` | `resolve_video_service_base_url()` | `heartbeatUrl` |
| | `heartbeat_interval_sec` | realtime `10` / patrol `15` | `heartbeatIntervalSec` |
| | `log_path` | 入参 | `logPath` |
| | `alert_image_dir` | 同 alarm image_dir | `alertImageDir` |
| | `headless` | 固定 `true` | `headless` |
| | `frame_skip` | 同 `[ai]` | `frameSkip`（覆盖） |
| | `cron_expression` | `cron_expression` | `cronExpression` |
| | `patrol_mode` / `patrol_interval_sec` / `patrol_pool_size` | DB 字段 | `patrolMode` / … |
| | `devices_json` | 全设备 JSON | `devices[]` |
| `[features]` | `enable_rtmp` | 有 rtmp 且 realtime | `enableRtmp` |
| | `enable_draw` | 固定 `true` | `enableDrawRtmp` |
| | `enable_alarm` | `alert_event_enabled` | `enableAlarm` |
| `[regions]` | `{device}_{region}=` | `DeviceDetectionRegion` | `regions` |

**C++ 另读但未由 VIDEO 写入的 ini key：**

| Section | Key | 说明 |
|---------|-----|------|
| `[video]` | `devices_json` | 可选；VIDEO 仅写 `[video_task]`，启动时会从 `rtsp_url` 补主设备 |
| `[video_task]` | `event` | `algorithm_name` 别名；VIDEO 只写 `algorithm_name` |

---

## 3. VIDEO 写了但 C++ 未读 / 未生效（静默丢失风险）

### 3.1 ini 字面量：**无**

当前样例 `RUNTIME/config/task_91301.ini` 中每个 key 均有解析分支。

### 3.2 ini 值语义丢失（写了 key，行为不等价）

| 写入 | 风险 | 说明 |
|------|------|------|
| `[video_task] patrol_mode=hybrid` | **高** | C++ `PatrolScheduler` 仅 `pool` \| `rotate`；非 `rotate` 一律走 pool（`PatrolScheduler.cpp` L175） |
| `[video_task] algorithm_name` ← `model_names` | **中** | python hook `event`=`task_name`；cpp=`algorithm_name` |
| `[ai] model_path`（单模型） | **中** | `model_ids` 多个时仅第一个 ONNX；**CAP-MULTI-MODEL** |
| `[video_task] cron_expression` | **中** | C++ snap 为简化 cron（分/时字段）；复杂表达式不等价 **CAP-CRON-SNAP** |
| `[alarm] confidence_threshold` | **低** | C++ 按置信度过滤；**无** `alert_class_names` 类别过滤 |

### 3.3 DB 字段未写入 ini（cpp 完全无感）

| 字段组 | CAP | 编排动作 |
|--------|-----|----------|
| `tracking_*` | CAP-TRACKING | WARN + UI 禁用或 C++ 实现 |
| `alert_class_names` | CAP-ALERT-CLASS | 写入 ini 或 VIDEO hook 后过滤 |
| `motion_gate_*` | CAP-MOTION-GATE | env/ini 或 C++ |
| `face_*` / `plate_*` matching | CAP-FACE-MATCH / CAP-PLATE-MATCH | VIDEO hook 后编排触发 |
| `post_process_*` | CAP-POST-PROCESS | VIDEO hook 后 enqueue |
| `pose_*` | CAP-POSE | 同上 |
| `defense_*` | CAP-DEFENSE | 保持 VIDEO/sink；cpp 无责 |
| `space_id` | CAP-SNAP-SPACE | snap 落库路径；仅 python |
| `focus_device_id` | CAP-PATROL-HYBRID | ini + C++ hybrid 调度 |
| GB28181 源解析 | CAP-GB28181-SRC | 拉流前 VIDEO 解析（启动时） |
| NVENC / overlay 双队列 | CAP-NVENC-AUTO / CAP-OVERLAY-DUAL | 帧管道能力，非 ini |

---

## 4. C++ 支持但 VIDEO 未写

| 能力 | C++ 支持 | VIDEO 缺口 |
|------|----------|------------|
| `[video].devices_json` | ✅ 与 `[video_task]` 二选一 | 仅写后者（可接受） |
| `[video_task].event` | ✅ 等同 `algorithm_name` | 未写（有 `algorithm_name` 即可） |
| 多模型 `modelPaths` map | 结构支持 | 解析器只接受单个 `model_path` |
| HTTP 控制 `control_port` 动态 RTMP | ✅ `Detech::startStreaming` | ini `enable_rtmp` 静态；可 HTTP 控流 |
| Legacy hook `sendAlarm` JSON | ✅ `AlarmCallback::buildLegacyJsonBody` | VIDEO 仅契约 VIDEO schema |
| Env `RUNTIME_FORCE_CPU` 等 | ✅ 解析后覆盖 ini | daemon 注入 env，非 ini 字段 |

---

## 5. Hook JSON 对照（`POST /video/alert/hook`）

### 5.1 Python `realtime_algorithm_service/run_deploy.py`

`try_send_alert_for_detections` → `send_alert_event_async`：

| 字段 | 必填 | 来源 |
|------|------|------|
| `object` | ✅ | 检测主类别 |
| `event` | ✅ | **`task_name`** |
| `device_id` / `device_name` | ✅ | 设备 |
| `task_type` | ✅ | 固定 `realtime` |
| `correlation_id` | ✅ | UUID |
| `face_detection_enabled` / `plate_detection_enabled` | 否 | `task_config` 透传 |
| `time` | 否 | 东八区 `%Y-%m-%d %H:%M:%S` |
| `information` | 否 | JSON 字符串：`total_count`, `object_counts`, `detections[]`（含 `track_id`, `duration`）, `frame_number` |
| `image_path` | 否 | 本地 jpg |
| `region` | 否 | （可选，python 路径常省略） |

### 5.2 C++ `Detech::_alarmSenderThreadFunc` / `AlarmCallback`

| 字段 | cpp | 与 python 差异 |
|------|-----|----------------|
| `object` | ✅ | |
| `event` | ✅ | 来自 ini **`algorithm_name`**（`model_names`），非 `task_name` |
| `device_id` / `device_name` | ✅ | |
| `task_type` | ✅ | ini `task_type` |
| `correlation_id` | ✅ | `{taskId}_{utc_iso}`，非 UUID |
| `face_detection_enabled` / `plate_detection_enabled` | ❌ | hook 可从 DB 补（`alert_hook_service`） |
| `time` | ✅ | **UTC ISO** `formatUtcNow()`；hook 侧会归一化 |
| `information` | ✅ | `task_id`, `region`, `detection_count`, `detections[]`；**无** `track_id` / `object_counts` |
| `image_path` | ✅ | |
| `region` | ✅ | 区域名 |
| `record_path` | ❌ | 双方均未用 |

### 5.3 心跳 JSON（`POST .../heartbeat/realtime|patrol`）

| 字段 | python | cpp |
|------|--------|-----|
| `task_id` | ✅ | ✅ |
| `server_ip` | POD_IP / 探测 | 固定 `127.0.0.1` |
| `port` | `null` | **`control_port`** |
| `process_id` | ✅ | ✅ |
| `log_path` | ✅ | ✅ ini `log_path` |
| `total_patrols` / `total_detections` | — | patrol 时 ✅ |

---

## 6. 明确 unsupported — 应在启用 cpp 时打 WARNING 的 CAP

依据 `docs/runtime-parity/CAP-BUSINESS-DECISIONS.md`（**要** 且当前 cpp 无等价实现）。  
~~CAP-SAM-TASK~~ 已砍，**不** WARN。

| CAP ID | 触发条件（`AlgorithmTask`） | 建议 WARN 落点 | Phase 2 动作 |
|--------|----------------------------|----------------|--------------|
| **CAP-TRACKING** | `tracking_enabled=true` | `algorithm_task_daemon` / `generate_runtime_ini` | ini 字段或 UI 禁用 |
| **CAP-ALERT-CLASS** | `alert_class_names` 非空 | `generate_runtime_ini` | 序列化 + C++ 过滤 |
| **CAP-MOTION-GATE** | `motion_gate_enabled=true` | daemon env 注入处 | 仅 python 今日有 env |
| **CAP-MULTI-MODEL** | `len(model_ids)>1` | `generate_runtime_ini` | 多 ONNX 或文档声明 |
| **CAP-FACE-MATCH** | `face_matching_enabled=true` | daemon 启动 | VIDEO hook 后触发 |
| **CAP-PLATE-MATCH** | `plate_matching_enabled=true` | 同上 | 同上 |
| **CAP-POST-PROCESS** | `post_process_enabled=true` | launcher 启动 | hook 后 enqueue |
| **CAP-POSE** | `pose_analysis_enabled` \| `pose_intent_enabled` | 同上 | Worker 已有，缺触发 |
| **CAP-PATROL-HYBRID** | `patrol_mode=hybrid` 或 `focus_device_id`  set | `generate_runtime_ini` | C++ hybrid 或降级 WARN |
| **CAP-SNAP-SPACE** | `task_type=snap` 且 `space_id` set | daemon | 抓拍落库路径 |
| **CAP-GB28181-SRC** | 设备源需国标解析 | launcher | 启动前 VIDEO 解析 RTSP |
| **CAP-OVERLAY-DUAL** | （无单独 DB 开关） | — | 表现验收项；非单字段 |
| **CAP-NVENC-AUTO** | （无单独 DB 开关） | — | 推流质量；非单字段 |
| **CAP-DEFENSE** | `defense_schedule` 定制 | — | sink/VIDEO；cpp 可忽略 |

**已实现、无需 WARN：** CAP-YOLO-ONNX, CAP-REGION, CAP-ALERT-HOOK, CAP-ALERT-SUPPRESS, CAP-HEARTBEAT, CAP-RTMP（部分）, CAP-PATROL-POOL, CAP-PATROL-ROTATE, CAP-CRON-SNAP（弱等价）.

---

## 7. 编排建议（优先级）

1. **P0 — 契约：** 统一 hook `event` 来源（`task_name` vs `algorithm_name`）；cpp 补发 `face_detection_enabled` / `plate_detection_enabled` 或文档声明由 hook DB 补全。
2. **P0 — 门禁：** `generate_runtime_ini` 或 daemon 对 §6 表打 `logger.warning`（含 CAP ID）。
3. **P1 — 字段：** `alert_class_names` → ini；`patrol_mode=hybrid` 降级或实现。
4. **P1 — 平台：** `process_alert_hook` 内补人脸/车牌/后处理触发（python 删除前必做）。
5. **P2 — 能力：** tracking / motion_gate / multi-model / snap-space 进 C++ 或产品声明 cpp 不支持。

---

## 8. Evidence

|  artefact | Path |
|----------|------|
| AlgorithmTask model | `VIDEO/models.py` L902–1190 |
| ini 生成 | `VIDEO/app/services/runtime_config_service.py` `generate_runtime_ini` |
| C++ 配置 | `RUNTIME/src/Config.h`, `RUNTIME/src/ConfigParser.cpp` |
| C++ 告警/心跳 | `RUNTIME/src/Detech.cpp`, `RUNTIME/src/AlarmCallback.cpp` |
| Python 实时 hook | `VIDEO/services/realtime_algorithm_service/run_deploy.py` L1961–2127 |
| Hook 消费 | `VIDEO/app/services/alert_hook_service.py` `process_alert_hook` |
| 样例 ini | `RUNTIME/config/task_91301.ini` |
| CAP 表 | `docs/runtime-parity/CAP-BUSINESS-DECISIONS.md` |
| 编排调研 | `docs/runtime-parity/reports/04-video-absorb-surface.md` |
