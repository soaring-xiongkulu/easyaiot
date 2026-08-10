# FR-B21 Report — GET 信封自动矩阵 + 信封缺口修复（Python-first）

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Commits:** `0649efe`  
**Date:** 2026-08-11

## Summary

Extended `tools/video_java/field_contract.py` with `--matrix`: auto-probes all **98 inventoried GET** routes (within **265** total inventoried routes), materializing `{param}` → `1` or seed `vj_p2_device`, asserting Python envelope `{code,msg,data}` and HTTP not 5xx. Skips non-GET (167) and non-JSON GET (`alert/image`, `alert/record`, patrol SSE `/events`). Retains FR-B20 **16** deep samples (`--deep`).

Live run on `:48096`:

| Layer | Counts |
|-------|--------|
| Matrix routes | **265 pass / 0 fail** (170 skip) |
| JSON GET envelope asserts | **190 pass / 0 fail** |
| FR-B20 deep samples | **16 / 88 pass / 0 fail / 0 skip** |

Artifacts: `logs/fr-b21-field-matrix-latest.{json,md}`, `logs/fr-b20-field-contract-latest.{json,md}`.

**COMPLETE 未宣称** — 字段键级 ~259 矩阵 + prod 联调仍 open。

## Python-first reads

| Concern | Python oracle cite |
|---------|-------------------|
| Envelope shape | Flask `api_response` → `{code, msg, data}` always (data may be null) |
| Device storage defaults | `models.py` `DeviceStorageConfig` L2047-2055 (`cleanup_enabled=True`, thresholds 0.8/0.3) |
| Device storage create | `storage_service.get_or_create_device_storage_config` L17-27 |
| Face/plate not-found | Blueprint 404 semantics — business `code=404` not `500` on missing library |

## Changes

| Component | Change |
|-----------|--------|
| `field_contract.py` | `--matrix` mode; `fr-b21-field-matrix-*` artifacts; query suffixes for required params |
| `VideoApiResponse.java` | `data` always serialized (`ALWAYS`) — null included in JSON |
| `AlertController.java` | `recordError` adds `msg` alongside `message` |
| `DeviceStorageRepository.java` | `insertDefault` with Python-aligned NOT NULL defaults |
| `CameraHardwareService.java` | Missing ONVIF config / preset list errors → `400` not `500` |
| `FaceLibraryService.java` | Library not-found GET → `404` not `500` |
| `PlateLibraryService.java` | Library not-found GET → `404` not `500` |
| `FULL_REPLACEMENT_GAP.md` | §5 / §8 / §9 FR-B21 evidence rows |

## Matrix counts (live `:48096`)

| Metric | Value |
|--------|------:|
| Inventoried routes | 265 |
| GET routes | 98 |
| Non-JSON GET skip | 3 |
| JSON GET envelope probes | 95 |
| Matrix endpoint pass | 265 |
| Matrix asserts pass / fail / skip | 190 / 0 / 170 |
| FR-B20 deep endpoints | 16 / 88 / 0 / 0 |

## Fixes applied

1. **Envelope `data` omitted on errors** — `@JsonInclude(NON_NULL)` on `VideoApiResponse.data` dropped; Python always emits `data` (null ok).
2. **`GET /video/alert/record` validation** — `recordError` missing `msg` key.
3. **`GET /video/snap/device/{id}/storage`** — `insertDefault` violated PG NOT NULL on `snap_storage_cleanup_enabled`; now inserts Python defaults.
4. **Face/plate library GET by id** — not-found returned `code=500`; now `404`.
5. **ONVIF presets GET** — missing credentials returned `code=500`; now `400`.

## GAP deltas

- §5：FR-B21 ✅ GET envelope matrix artifact path
- §8：FR-B21 行（98 GET / 95 JSON probes / 190 pass）
- §9：GET 信封矩阵已执行；剩余 = 字段键级 ~259 矩阵 + prod 联调

## certify --phase 0

```
exit 0
```

Log: `logs/fr-b21-phase0.log`

## Remaining

- **字段键级 ~259 路由矩阵**（非信封 presence）
- POST/PUT/DELETE 自动探针（本包刻意 GET-only）
- prod broker/MinIO/真机/WVP/iot-node 联调
- 生产回滚/切流演练

## Concerns

- Matrix green = **envelope keys + HTTP<500** only; business `code` may be 400/404
- 3 GET routes honestly skipped (binary/SSE) — not envelope-testable
- Probe ids (`1`, `vj_p2_device`) may not exercise happy-path data shapes
- Oracle Python health DB not UP during certify (EX-ORACLE-HEALTH-DB exempt) — unchanged from prior FRs
