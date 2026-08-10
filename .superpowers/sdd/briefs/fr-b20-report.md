# FR-B20 Report — 14 前缀字段契约扩面 + 空列表 item-key 实测（Python-first）

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Expanded `tools/video_java/field_contract.py` from 12 → **16** sampled GETs covering all **14 inventoried URL prefixes**. Added POST setup seeds for `alert_page` / `playback_list` / `scenario_pose_libraries` (Python-first on create body). Live run on `:48096`: **16 endpoints / 88 pass / 0 fail / 0 skip**. Artifacts: `logs/fr-b20-field-contract-latest.{json,md}`.

Fixed **PlaybackRepository.insert** PostgreSQL generated-key handling (`new String[]{"id"}`) so `POST /video/playback/` returns `code=0` instead of JDBC `getKey` multi-column error.

**COMPLETE 未宣称** — 全量 ~259 路由字段矩阵 + prod 联调仍 open。

## Python-first reads (new endpoints)

| Endpoint | Python oracle cite | Asserted keys |
|----------|-------------------|---------------|
| `GET /video/ping` (media prefix smoke) | `contract_regression.py` `SMOKE_ENDPOINTS["/video/media"]`; Java `VideoPingController` | `service`, `phase` |
| `GET /video/device-detection/device/{id}/regions` | `models.py` `DeviceDetectionRegion.to_dict` L2004-2035; `device_detection_region.py` `list_device_regions` | 14 item keys incl. `model_ids`, `points` |
| `GET /video/camera/audio/talk/health` | `audio_talk.py` `health()` L179-188 | `status`, `onvif_available`, `audio_talk_available` |
| `GET /video/scenario-pose/libraries` | `models.py` `ScenarioPoseLibrary.to_dict` L1663-1687; `scenario_pose_library_service.list_libraries` adds `entry_count` | 15 library keys + top `total` |

## Python-first reads (setup / skip clearance)

| Case | Setup | Python cite |
|------|-------|-------------|
| `alert_page` item keys | `POST /video/alert/hook` with `image_url` | `alert_service._get_alert_filter_query` L192-195 filters `image_url IS NOT NULL` |
| `playback_list` item keys | `POST /video/playback/` | `playback.py` `create_playback` required fields L120 |
| `scenario_pose_libraries` | `POST /video/scenario-pose/libraries` `{name}` | `scenario_pose.py` `create_library` L48-63 |

## Changes

| Component | Change |
|-----------|--------|
| `tools/video_java/field_contract.py` | +4 prefix samples; POST `setup` hook; `fr-b20` artifacts; 88 asserts |
| `PlaybackRepository.java` | Fix PG `GeneratedKeyHolder` — specify `id` column for insert return |
| `FULL_REPLACEMENT_GAP.md` | §5 / §8 / §9 FR-B20 evidence rows |

## Field assert counts (live `:48096`)

| Metric | FR-B19 | FR-B20 |
|--------|-------:|-------:|
| endpoints sampled | 12 | **16** |
| prefixes covered | 10 | **14** |
| asserts pass | 67 | **88** |
| asserts fail | 0 | **0** |
| asserts skip | 2 | **0** |

## Fixes applied

1. **Playback `POST /`:** `PlaybackRepository.insert` — use `prepareStatement(sql, new String[]{"id"})` instead of `RETURN_GENERATED_KEYS` (PG returned full row → `getKey` exception after successful insert).

## GAP deltas

- §5：FR-B20 ✅ 14-prefix field samples + artifact path
- §8：FR-B20 行（16 端点 / 88/0/0）
- §9：14 前缀字段抽样已执行；剩余 = 全量 259 字段矩阵 + prod 联调

## certify --phase 0

```
exit 0
```

Log: `logs/fr-b20-phase0.log`

## Remaining

- 全量 **~259 路由** 字段级契约矩阵（非 16 端点抽样）
- `device-detection` POST region 仍受 oracle 算法模型校验约束（mini 设备无模型时 400 — list GET 已有存量行可测 item keys）
- prod broker/MinIO/真机/WVP/iot-node 联调
- 生产回滚/切流演练

## Concerns

- Field pass = **key presence** only; values/types not diffed
- Media prefix samples `/video/ping` (Java liveness), not media_hook POST hooks
- `points` shape may differ (Python dict coords vs Java nested arrays) — keys only asserted
- Java benign extras (`message` alias) not asserted
