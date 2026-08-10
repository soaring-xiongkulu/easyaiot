# FR-B13 Report — 媒体节点池 + Ceph mount allocate

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Ported Python `media_client` to Java `MediaPoolClient` and wired media-pool-aware stream URL resolution into device registration, GB28181 sync/backfill, and stream-forward remote deploy sync. Added `requireCephMount` / `ceph_mount_ready` parity to `IotNodeClient.allocateNode` matching Python `node_client.allocate_node` cluster gate.

**COMPLETE 未宣称** — prod 媒体池 API、Ceph 集群 allocate、全量契约回归仍待。

## Python files read (oracle)

| Path | Purpose |
|------|---------|
| `VIDEO/_retired_python_video/app/utils/media_client.py` | `is_media_pool_enabled`, `allocate_device_media`, `get_device_media_binding`, `stream_urls_from_binding` |
| `VIDEO/_retired_python_video/app/services/stream_url_sync_service.py` | `build_stream_urls_for_host`, `sync_device_stream_urls`, media pool binding on sync |
| `VIDEO/_retired_python_video/app/services/camera_service.py` | `_default_stream_urls`, `gb28181_device_stream_urls`, `_legacy_local_stream_urls` (L768–817) |
| `VIDEO/_retired_python_video/app/utils/node_client.py` | `_node_ceph_mount_ready`, `require_ceph_mount` on `allocate_node` (L95–150) |
| `VIDEO/_retired_python_video/app/services/post_process_launcher_service.py` | `_deploy_worker_remote` → `allocate_node` (ceph default via cluster mode) |

## Java changes (key)

| Component | Change |
|-----------|--------|
| `MediaPoolClient` | HTTP client to `/admin-api/node/media/allocate` + `/binding`; honest `MediaPoolException` when pool enabled but API fails |
| `StreamUrlSupport` | `defaultStreamUrls`, `gb28181DeviceStreamUrls`, `buildStreamUrlsForHost`; pool-enabled → allocate; disabled → local SRS default |
| `StreamUrlSyncService` | Mirrors `sync_device_stream_urls`; media pool or host/tags fallback |
| `IotNodeClient` | `requireCephMount` param; target-node ceph gate; scheduler `requireCephMount` requirement |
| `CameraAdminService` | Registration uses `StreamUrlSupport.defaultStreamUrls` |
| `Gb28181SyncService` | Upsert + `backfillAiStreamUrls` via `StreamUrlSupport.gb28181DeviceStreamUrls` |
| `StreamForwardRemoteDeployService` | Post-deploy `syncDeviceStreamUrls` |
| `VideoProperties.MediaPool` | Config for `MEDIA_NODE_POOL_ENABLED` / region / http play host |
| `FULL_REPLACEMENT_GAP.md` | §2.3 / §4 / §8 media pool + ceph allocate → **FR-B13 ✅** |

## GAP deltas

- §2.3 camera 行为：媒体节点池 AI/流地址接线 → **FR-B13 ✅**（prod iot-node 媒体 API 联调仍待）
- §4 远程 node：`requireCephMount` / `ceph_mount_ready` → **FR-B13 ✅**
- §8 行为桩：媒体节点池行关闭（prod 联调仍待）

## certify --phase 0

```
exit 0
```

Log: `logs/fr-b13-phase0.log`（oracle `:6000` 未运行 — stale golden warnings; all cases ok/exempt）

## Remaining

- Prod 媒体节点池 + iot-node `/node/media/*` 集群联调（`MEDIA_NODE_POOL_ENABLED=true`）
- CephFS `ceph_mount_ready` 真机 gate 与 post-process 远程 allocate 演练
- `resolve_device_stream_urls` 只读路径（Python `get_device_media_binding`）未全面接线到 list/get API
- 全量 HTTP 契约回归（259 路由）

## Concerns

- Pool enabled + API down：warn 日志 + 回退本机/节点 host URL（与 Python 一致），非静默假绑定
- Pool disabled：保持本机 SRS 默认（mini 默认）
- `CLUSTER_MODE` 未设时 `requireCephMount` 默认 false（与 Python 无 cluster_storage 时一致）
