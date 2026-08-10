# FR-B19 Report — P0/P1 字段级 JSON 契约抽样（Python-first）

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Added `tools/video_java/field_contract.py`: Python-first P0/P1 GET sampling against live Java `:48096`, asserting `{code,msg,data}` envelope plus documented data/list-item keys from oracle `to_dict` / blueprint responses. Live run: **12 endpoints / 67 pass / 0 fail / 2 skip** (empty-list item keys deferred). Artifacts: `logs/fr-b19-field-contract-latest.{json,md}`.

Fixed clear Java field mismatches on **face/plate health** (keys now match Python `face_vector_store.ping` + `get_plate_model_status`). Patrol sampled via `GET /video/patrol/directory/1/devices` — oracle has **no** `GET /session/list`.

**COMPLETE 未宣称** — 全量 259 路由字段矩阵 + prod 联调仍 open。

## Python-first reads

| Path | Purpose |
|------|---------|
| `VIDEO/_retired_python_video/app/services/alert_service.py` | `get_alert_list` → `{alert_list,total}`; `get_alert_count` → `{count_list,total_count}`; `_alert_to_dict` item keys |
| `VIDEO/_retired_python_video/app/blueprints/algorithm_task.py` | `list_tasks` envelope + `AlgorithmTask.to_dict` |
| `VIDEO/_retired_python_video/app/services/camera_service.py` | `_to_dict` camera list/get |
| `VIDEO/_retired_python_video/models.py` | `SnapSpace.to_dict`, `RecordSpace.to_dict`, `StreamForwardTask.to_dict`, `Playback.to_dict` |
| `VIDEO/_retired_python_video/app/blueprints/snap.py` / `record.py` | space list top-level `total,parent_key,breadcrumbs,is_search,scope` |
| `VIDEO/_retired_python_video/app/blueprints/face.py` | `face_health` + `face_vector_store.ping` |
| `VIDEO/_retired_python_video/app/utils/plate_model_download.py` | `get_plate_model_status` |
| `VIDEO/_retired_python_video/app/blueprints/patrol.py` | `directory_patrol_devices` (no session list route) |
| `VIDEO/_retired_python_video/app/blueprints/playback.py` | `list_playbacks` |

## Changes

| Component | Change |
|-----------|--------|
| `tools/video_java/field_contract.py` | **New** — 12 sampled GETs, envelope + key asserts, artifacts under `logs/fr-b19-field-contract-*` |
| `FaceModelService.java` | `collection_name` / `collection_exists` / optional `error` (was `collection` / `status`) |
| `PlateModelService.java` | Health payload aligns `get_plate_model_status` keys (`detect_model`, `rec_path`, `stage`, …) |
| `PatrolSessionRepository.java` | JDBC `RowCallbackHandler` iterates all device name rows (multi-device sessions) |
| `FULL_REPLACEMENT_GAP.md` | §5 FR-B19 证据行；§8 字段抽样计数；§9 诚实表述（≠ 全量矩阵） |
| `progress.md` | FR-B19 row |

## Field assert counts (live `:48096`)

| Metric | Count |
|--------|------:|
| endpoints sampled | 12 |
| endpoint pass | 12 |
| asserts pass | 67 |
| asserts fail | 0 |
| asserts skip | 2 |

**Skips:** `alert_page` / `playback_list` — empty lists; item-key asserts deferred (envelope + data shape still checked).

## Fixes applied

1. **Face `/health`:** `collection`→`collection_name`, `status`→`collection_exists`, add `error` when Milvus unavailable (`FaceModelService.java`).
2. **Plate `/health`:** replace stub `{path,size_bytes,status}` with Python `get_plate_model_status` shape (`PlateModelService.java`).
3. **Patrol device names:** fix JDBC callback to read all rows when resolving `device_names` (`PatrolSessionRepository.java`).

## GAP deltas

- §5：FR-B19 ✅ 字段级 P0/P1 抽样 + artifact path
- §8：新增 FR-B19 行（12 端点 / 67/0/2 assert）
- §9：字段抽样已执行；剩余 = 全量 259 字段矩阵 + prod 联调

## certify --phase 0

```
exit 0
```

Log: `logs/fr-b19-phase0.log`（Java :48096 UP；oracle :6000 down → EX-ORACLE-HEALTH-DB exempt）

## Remaining

- 全量 **259 路由** 字段级契约矩阵（非 12 端点抽样）
- `alert_page` / `playback_list` item keys when DB has rows
- Oracle `GET /video/patrol/session/list` **不存在** — 若 WEB 需要列表 API，需产品/后端单独 backlog
- prod broker/MinIO/真机/WVP/iot-node 联调
- 生产回滚/切流演练

## Concerns

- Field pass = **key presence** only; values/types not diffed
- Empty-list skips mean alert/playback item shapes unverified until fixture data exists
- Java adds benign extras (`message` alias, snap/record tree enrich keys) — asserts are Python-required keys only
- Patrol brief said "session list" but oracle route inventory has no such GET — documented substitution
