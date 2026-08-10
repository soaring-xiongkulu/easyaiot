# FR-B33 Report — POST 成功路径字段键矩阵（Python-first）

**STATUS:** DONE (local `:48096`) — **禁止 COMPLETE**

**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Python-first 映射（read before coding）

| id | POST path | Python cite | data keys |
|----|-----------|-------------|-----------|
| algo_task_create | `/video/algorithm/task` | `algorithm_task.py` L144-148 → `AlgorithmTask.to_dict` | 81 keys (`ALGORITHM_TASK_KEYS`) |
| snap_task_create | `/video/snap/task` | `snap.py` L309-313 → `SnapTask.to_dict` + device_name | 36 keys (`SNAP_TASK_ITEM_KEYS`) |
| face_library_create | `/video/face/libraries` | `face.py` L154 → `FaceLibrary.to_dict` | 10 keys (`FACE_LIBRARY_ITEM_KEYS`) |
| plate_library_create | `/video/plate/libraries` | `plate.py` L122 → `PlateLibrary.to_dict` | 9 keys (`PLATE_LIBRARY_ITEM_KEYS`) |
| stream_forward_create | `/video/stream-forward/task` | `stream_forward.py` L103-107 → `StreamForwardTask.to_dict` | 27 keys (`STREAM_FORWARD_TASK_KEYS`) |
| playback_create | `/video/playback/` | `playback.py` L150-154 → `Playback.to_dict` | 11 keys (`PLAYBACK_ITEM_KEYS`) |
| scenario_pose_library_create | `/video/scenario-pose/libraries` | `scenario_pose.py` L63 → `ScenarioPoseLibrary.to_dict` | 15 keys (`SCENARIO_POSE_LIBRARY_KEYS`) |
| patrol_session_create | `/video/patrol/session` | `patrol.py` L32 → `PatrolSession.to_dict` | 26 keys (`PATROL_SESSION_KEYS`) |
| camera_register | `/video/camera/register/device` | `camera.py` L844-848 `data.id` | `{id}` |
| alert_hook_skipped | `/video/alert/hook` | `alert_hook_service.py` L802 | `{status, reason}` |
| alert_hook_success | `/video/alert/hook` | `alert_hook_service.py` L922-927 **or** Java `AlertHookService` direct_persist L115-119 | kafka: `{status,topic,partition,offset}` / mini: `{status,alert_id,mode}` |
| algo_empty_body_4xx | `/video/algorithm/task` | `algorithm_task.py` L72-73 | envelope-only |
| snap_task_missing_name_4xx | `/video/snap/task` | `snap.py` L269-270 | envelope-only |
| face_library_missing_name_4xx | `/video/face/libraries` | `face.py` create ValueError | envelope-only |
| playback_missing_fields_4xx | `/video/playback/` | `playback.py` L120-123 | envelope-only |
| snap_space_create_forbidden | `/video/snap/space` | `snap.py` L104-109 403 | envelope-only |

## POST keys-matrix 结果

| Metric | Value |
|--------|-------|
| Samples | **16** (≥12 required) |
| Pass | **16/16** |
| Success-key asserts | **11** pass / **0** fail |
| Envelope-only (4xx) | **5** |
| Total asserts | **67** pass / **0** fail |

**Tool:** `python tools/video_java/field_contract.py --post-keys-matrix`  
**Artifacts:** `logs/fr-b33-post-keys-matrix-latest.{json,md}`

## Java fix

| 组件 | 变更 | 根因 |
|------|------|------|
| `DeviceRepository.insert` | INSERT 补 `auto_snap_enabled=false` | Python `models.py` Device L81 NOT NULL default；注册 POST 500 |

## phase0

```
python tools/video_java/certify.py --phase 0
→ PASS 5/5 (certify-frb33-phase0.log)
```

## Remaining (honest)

1. **prod soak** — post-keys-matrix 仅 local `:48096` 证据
2. **全量 POST 覆盖** — 16 curated 样本 ≠ ~112 inventoried POST
3. **multipart POST**（upload/import）仍无键矩阵
4. **COMPLETE forbidden**

## Concerns

- `snap/space` POST 在 Python 为 403 禁止手动创建；矩阵以 envelope-only 探针覆盖
- `alert_hook_success` mini 走 direct_persist 分支，与 Python Kafka `{topic,partition,offset}` 不同；用 `data_keys_alternatives` 诚实映射
- `patrol/session` 需 `model_ids`（Python `patrol_session_service.py` L75-76）；无 cleanup DELETE 路由
