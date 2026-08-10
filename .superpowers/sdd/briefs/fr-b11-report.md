# FR-B11 Report — GB28181 目录同步 + Nacos 进程切换演练

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Ported Python `gb28181_sync_service` to Java `Gb28181SyncService`: WVP device/channel pull, frontend payload sync, default-directory layout, AI stream backfill, and patrol default-directory pre-sync. Removed warning-only stubs in `CameraDirectoryService.syncGb28181` and `PatrolSessionService.resolveDirectoryDevices`. Documented Nacos `video-server` process-swap dry-run in `ROLLBACK_LOG.md` (no live flip).

## Python files read (oracle)

| Path | Purpose |
|------|---------|
| `VIDEO/_retired_python_video/app/services/gb28181_sync_service.py` | WVP pull, payload sync, upsert, directory layout |
| `VIDEO/_retired_python_video/app/utils/gb28181_source.py` | Candidate bases, stream URLs, auth |
| `VIDEO/_retired_python_video/app/services/camera_service.py` | `get_or_create_default_directory`, `sync_unassigned_devices_to_default_directory`, `gb28181_device_stream_urls` |
| `VIDEO/_retired_python_video/app/services/directory_json_sync_service.py` | Directory JSON rules (reference) |
| `VIDEO/_retired_python_video/app/blueprints/camera.py` | `sync-gb28181`, `monitor-tree`, `skip_sync` |
| `VIDEO/_retired_python_video/app/services/patrol_session_service.py` | Default-directory GB sync before patrol device list |

## Java changes (key)

| Component | Change |
|-----------|--------|
| `Gb28181SourceSupport` | Candidate WVP bases, virtual device ID, AI stream URLs, auth header |
| `Gb28181SyncService` | `syncFromWvp`, `syncFromPayload`, `ensureDirectoryLayout`, `backfillAiStreamUrls` |
| `CameraDirectoryService` | Wire sync; `monitorTree` calls layout + optional WVP sync |
| `CameraController` | Dynamic sync message; auth headers forwarded |
| `PatrolSessionService` | Default directory → `syncFromWvp(strict=false)` (replaces warn-only) |
| `DeviceRepository` | `countBySourcePrefix`, `listBySourcePrefix`, `assignUnassignedToDefaultDirectory` |
| `FULL_REPLACEMENT_GAP.md` | §2.3 / §4 GB28181 → **FR-B11 ✅**; §5 Nacos dry-run → **FR-B11 ✅** |
| `gates/ROLLBACK_LOG.md` | FR-B11 Nacos process-swap dry-run row + detail |

## GAP

- §2.3 camera GB28181 目录同步 → **FR-B11 ✅**（无 WVP 时诚实错误/空统计，非静默成功）
- §4 ONVIF/NVR/GB28181 → GB28181 同步 **FR-B11 ✅**；FlightHub/大华 NVR 仍待
- §5 Nacos 进程切换 → **FR-B11 ✅** dry-run 证据；生产真切换 + 网关冒烟仍待 ops
- §8 behavior stubs → GB28181 目录同步行关闭

## certify --phase 0

```
exit 0
```

Log: `certify-frb11-phase0.log`（oracle `:6000` 未运行 — stale golden warnings; all cases ok/exempt）

## Nacos process-swap (dry-run)

| Check | Result |
|-------|--------|
| Gateway `lb://video-server` | **verified** |
| Java `:48096` | **UP** |
| Live stop Java → start Python | **NOT RUN** |
| Evidence | `logs/fr-b11-nacos-dryrun.txt`, `ROLLBACK_LOG.md` FR-B11 |

## Concerns / remaining

1. **WVP prod** — sync needs reachable `GATEWAY_URL` / `GB28181_SERVICE_URL` + JWT; mini 无 WVP 时返回配置提示（与 Python 一致）。
2. **目录 JSON 同步** — `syncDirectoryJson` 仍 500 未实现（非 FR-B11 范围）。
3. **GB 目录属性** — `ptz_type` 等列 Java `DeviceRow` 未映射；核心 device 字段已同步。
4. **Nacos live flip** — dry-run only; prod 需 ops 执行 CUTOVER 步骤 1–8 + 15–30min observe。
5. **媒体节点池** — AI 流地址使用本机 SRS 默认路径；Python media pool 未移植。
