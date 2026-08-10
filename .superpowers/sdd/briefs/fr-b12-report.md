# FR-B12 Report — 目录 JSON 同步 + FlightHub/大华 NVR

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Ported Python directory JSON sync rules to Java `DirectoryJsonSyncService` (no more 500 stub on `/directory/sync-json`). Implemented FlightHub OpenAPI live/register path via `FlighthubSourceSupport` + `CameraFlighthubService` HTTP client (honest 400/502/409 when misconfigured or SDK provider). Added Dahua NVR CGI channel enumeration in `DahuaNvrSupport` wired into `HikScanService.enumerateNvrChannels` with vendor auto-detect / Hik fallback.

**COMPLETE 未宣称** — prod 司空真机、大华 NVR 真机、全量契约回归仍待。

## Python files read (oracle)

| Path | Purpose |
|------|---------|
| `VIDEO/_retired_python_video/app/services/directory_json_sync_service.py` | 目录 JSON 校验/同步全规则 |
| `VIDEO/_retired_python_video/app/utils/flighthub_source.py` | FlightHub config、live start、register info |
| `VIDEO/_retired_python_video/app/vendor/hiktools/core/dahua_cgi.py` | 大华 CGI Digest + table 解析 |
| `VIDEO/_retired_python_video/app/vendor/hiktools/core/nvr.py` | 海康/大华 NVR 通道枚举、vendor detect |
| `VIDEO/_retired_python_video/app/services/nvr_service.py` | NVR vendor 标签、通道登记语义 |
| `VIDEO/_retired_python_video/app/blueprints/camera.py` | `directory/sync-json`、`flighthub/*`、`register/device/dji-live` |

## Java changes (key)

| Component | Change |
|-----------|--------|
| `DirectoryJsonSyncService` | `parsePayload` / `validateTree` / `syncFromJson` — parity with Python |
| `DeviceDirectoryRepository` | `findByNameAndParentId`, `findAllByName`, `findAll` |
| `CameraDirectoryService` | Wire sync/validate; accept `Object` body (array or `{tree}`) |
| `CameraController` | `validate-json` / `sync-json` `@RequestBody Object` |
| `FlighthubSourceSupport` | Config、register info、live provider 解析 |
| `CameraFlighthubService` | OpenAPI POST live start; register/refresh; honest errors |
| `DahuaNvrSupport` | CGI channel enum + vendor detect |
| `HikScanService` | Dahua path + auto-fallback when Hik ISAPI empty |
| `FULL_REPLACEMENT_GAP.md` | §2.3 / §4 / §7 P2 → **FR-B12 ✅** |
| `progress.md` | FR-B12 row |

## GAP deltas

- §2.3 camera 行为：目录 JSON 同步、FlightHub live/register、大华 NVR CGI 枚举 → **FR-B12 ✅**（prod 联调仍待）
- §4 下游集成 ONVIF/NVR/GB28181/FlightHub → FlightHub + 大华 NVR 行更新 **FR-B12 ✅**
- §7 P2 NVR/扫描/FlightHub/GB28181 → **FR-B12 ✅** 目录 JSON + FlightHub + 大华 CGI

## certify --phase 0

```
exit 0
```

Log: `certify-frb12-phase0.log`（oracle `:6000` 未运行 — stale golden warnings; all cases ok/exempt）

## Remaining

- FlightHub 真机/OpenAPI token 联调；SDK 型 volc 供应商需前端/SDK 桥接
- 大华 NVR RTSP 模板填充、通道登记持久化（`CameraNvrService.registerChannelRow` 仍轻量）
- 全量 HTTP 契约回归（259 路由）
- 行为桩：MinIO/推理/Milvus/SSE 真流等

## Concerns

- FlightHub 不可达时返回 502/400，非静默成功；缺 env 时明确错误
- Dahua 枚举依赖 CGI Digest（与 Python 一致）；无设备时 mini 仅结构验证
- 目录 JSON 同步无 `@Transactional`；与 Python 双 commit 语义近似（单条 JDBC 自动提交）
