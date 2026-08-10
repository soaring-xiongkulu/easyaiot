# FR-B34 Report — POST 字段键矩阵扩至 ≥40（Python-first）

**STATUS:** DONE (local `:48096`) — **禁止 COMPLETE**

**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Python-first 映射（read before coding）

| id | POST path | Python cite | keys / mode |
|----|-----------|-------------|-------------|
| algo_task_create | `/video/algorithm/task` | `algorithm_task.py` L144-148 → `AlgorithmTask.to_dict` | 81 keys |
| snap_task_create | `/video/snap/task` | `snap.py` L309-313 → `SnapTask.to_dict` | 36 keys |
| face_library_create | `/video/face/libraries` | `face.py` L154 → `FaceLibrary.to_dict` | 10 keys |
| plate_library_create | `/video/plate/libraries` | `plate.py` L122 → `PlateLibrary.to_dict` | 9 keys |
| stream_forward_create | `/video/stream-forward/task` | `stream_forward.py` L103-107 | 27 keys |
| playback_create | `/video/playback/` | `playback.py` L150-154 | 11 keys |
| scenario_pose_library_create | `/video/scenario-pose/libraries` | `scenario_pose.py` L63 | 15 keys |
| patrol_session_create | `/video/patrol/session` | `patrol.py` L32 → `PatrolSession.to_dict` | 26 keys |
| camera_register | `/video/camera/register/device` | `camera.py` L844-848 | `{id}` |
| alert_hook_skipped | `/video/alert/hook` | `alert_hook_service.py` L802 | `{status,reason}` |
| alert_hook_success | `/video/alert/hook` | L922-927 kafka **or** Java direct_persist | alt keys |
| record_space_sync_minio | `/video/record/space/sync/minio` | `record.py` L186-195 → `sync_spaces_to_minio` | 4 keys |
| media_hook_snap_completed | `/video/media/hook/snap/completed` | `media_hook.py` L60-79 | envelope_success |
| media_hook_srs_on_dvr_empty | `/video/media/hook/srs/on_dvr` | `media_hook.py` L32-36 | envelope_success |
| media_hook_srs_on_unpublish | `/video/media/hook/srs/on_unpublish` | L55-57 | envelope_success |
| device_detection_region_missing_name_4xx | `.../regions` | `device_detection_region.py` L76-78 | envelope_only |
| device_detection_invalid_device_4xx | `.../regions` | L51-52 | envelope_only |
| camera_directory_create | `/video/camera/directory` | `camera.py` L2797-2806 | 5 keys |
| camera_ensure_spaces | `.../ensure-spaces` | L810-815 | `{snap_space,record_space}` |
| algo_task_stop | `.../task/{id}/stop` | `algorithm_task.py` L245-248 | `AlgorithmTask.to_dict` |
| algo_heartbeat_realtime | `/video/algorithm/heartbeat/realtime` | L328-335 | `{task_id,task_name}` |
| stream_forward_stop / sf_heartbeat | stream-forward task + heartbeat | `stream_forward.py` | task / ack keys |
| stream_forward_ensure_task | `.../ensure-task` | L524-532 | 4 keys |
| snap_task_stop | `.../snap/task/{id}/stop` | `snap.py` L433-437 | `SnapTask.to_dict` |
| patrol_session_stop / patrol_heartbeat | patrol session | `patrol.py` | session / envelope_success |
| plate_entry_create | `.../libraries/{id}/entries` | `plate.py` L182 → `PlateEntry.to_dict` | 12 keys |
| scenario_pose_rule_entry | `.../libraries/{id}/entries` | `scenario_pose.py` L118-125 | `ScenarioPoseEntry.to_dict` |
| face_auto_enroll_stop / plate_auto_enroll_stop | `.../auto-enroll/stop` | `FaceAutoEnrollTask.to_dict` / plate analog | 16 / 15 keys |
| *\_4xx samples* | various | blueprint validation | envelope_only |

完整 42 行见 artifact `mapping_table`：`logs/fr-b34-post-keys-matrix-latest.json`

## POST keys-matrix 结果

| Metric | Value |
|--------|-------|
| Samples | **42** (≥40 required) |
| Pass | **42/42** |
| Success-key asserts | **25** pass / **0** fail |
| Envelope-only / envelope_success | **17** |
| Total asserts | **169** pass / **0** fail |
| Prefix coverage | **13/14** inventoried（缺 `/video/camera/audio/talk` POST — mini 无稳定 talk 探针） |

**Tool:** `python tools/video_java/field_contract.py --post-keys-matrix`  
**Artifacts:** `logs/fr-b34-post-keys-matrix-latest.{json,md}`

## Java fixes

| 组件 | 变更 | 根因 |
|------|------|------|
| `DeviceDirectoryRepository.insert` | `getKeys().get("id")` 替代 `getKey()` | PG 多列 generated keys → create directory 500 |
| `FaceLibraryService.stopAutoEnroll` | 无任务时 400 | 对齐 Python `stop_auto_enroll` ValueError |
| `PlateLibraryService.stopAutoEnroll` | 同上 | 同上 |
| `FaceAutoEnrollRepository.mapTask` | 始终输出 `started_at/expires_at/last_tick_at`（可 null） | 对齐 `FaceAutoEnrollTask.to_dict` |
| `PlateAutoEnrollRepository.mapTask` | 同上 | 对齐 `PlateAutoEnrollTask.to_dict` |

## phase0

```
python tools/video_java/certify.py --phase 0
→ PASS 5/5 (logs/certify-frb34-phase0.log)
```

## Remaining (honest)

1. **prod soak** — post-keys-matrix 仅 local `:48096`
2. **~112 inventoried POST** 仍未全量字段键覆盖（42 curated ≠ exhaustive）
3. **`/video/camera/audio/talk`** POST（start/stop/send）无键矩阵样本
4. **device-detection snapshot** 依赖 ffmpeg 可读 `sample.mp4`；local 路径偶发失败，矩阵以 4xx 探针代替
5. **COMPLETE forbidden**

## Concerns

- `patrol_session_start` 因并发 running 上限不稳定，已换 `stream_forward_ensure_task` 稳定探针
- `alert_hook_success` mini 仍可能走 direct_persist 分支（`data_keys_alternatives`）
- Oracle Python 进程未起时 phase0 record_python  WARN，Java candidate 仍 PASS
