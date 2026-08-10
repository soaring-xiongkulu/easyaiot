# FR-B18 Report — 收口 FR-B17 六条契约探针失败

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Closed all **6** FR-B17 HTTP probe failures on Java `:48096`. Live re-probe: **265 pass / 0 fail / 0 skip**; inventory **diff=0**; thin smoke **14/14 pass**. `certify --phase 0` exit **0**.

**COMPLETE 未宣称** — 字段级 JSON 契约、prod broker/MinIO/真机联调仍 open。

## Python-first cites (read before Java fix)

| Fail | Python blueprint | Key handler |
|------|------------------|-------------|
| GET/PATCH `/video/patrol/session/{id}` + stats | `VIDEO/_retired_python_video/app/blueprints/patrol.py` L41–46, L76–84, L146–161 | `get_session` / `session_stats` / `patch_session` — 404 in JSON body when missing |
| POST `/video/playback` | `VIDEO/_retired_python_video/app/blueprints/playback.py` L111–123 | `@playback_bp.route('/', methods=['POST'])` — Flask maps both `/playback` and `/playback/` |
| GET `/video/record/space/{id}/video/{file}` | `VIDEO/_retired_python_video/app/blueprints/record.py` L292–307 | `<path:object_name>` + `send_file`; ValueError→400 |
| GET `/video/snap/space/{id}/image/{file}` | `VIDEO/_retired_python_video/app/blueprints/snap.py` L946–961 | `<path:object_name>` + `Response`; ValueError→400 |
| smoke device-detection | `VIDEO/_retired_python_video/app/blueprints/device_detection_region.py` L22–34 | `/device/<device_id>/regions` (not bare `/regions`) |

## Root causes & Java fixes

| # | Symptom | Root cause | Fix |
|---|---------|------------|-----|
| 1–3 | patrol session GET/PATCH/stats HTTP **404** | `PatrolController` returned `ResponseEntity` HTTP 404 for missing session; probe treats any HTTP 404 as unmapped | Remove 404 `ResponseEntity` catches; let `VideoApiResponseAdvice` return HTTP 200 + `{code:404}` |
| 4 | `POST /video/playback` HTTP **404** | `@PostMapping("/")` only matched trailing-slash path | `@PostMapping({"", "/"})` |
| 5–6 | record/snap nested GET HTTP **500** | `{*objectName}` incompatible with `ANT_PATH_MATCHER` (`application.yaml`); whitelabel `IllegalArgumentException` | `@GetMapping(".../video/**")` / `.../image/**` + `MediaPathSupport.pathWithinHandlerMapping`; inline `VideoBusinessException`→JSON |
| smoke | `/video/device-detection/regions` 404 | SMOKE_ENDPOINTS wrong shape | → `/video/device-detection/device/1/regions` |

## Probe counts

| Metric | FR-B17 before | FR-B18 after |
|--------|--------------:|-------------:|
| probed | 265 | 265 |
| pass | 259 | **265** |
| fail | 6 | **0** |
| skip | 0 | 0 |
| smoke | 13/14 | **14/14** |
| inventory diff | 0 | 0 |

Artifact: `logs/fr-b17-contract-latest.json`

## certify --phase 0

```
exit 0
```

All `vj_p0_*` green (oracle record skipped — DB not UP; EX-ORACLE-HEALTH-DB exempt).

## Remaining

- 字段级 JSON 契约（`{code,msg,data}` 全接口对表）
- prod broker/MinIO/真机/WVP/iot-node 联调
- 生产回滚/切流演练
- patrol smoke still hits `/session/list` via `{sessionId}` wildcard (HTTP 200 + code 500) — cosmetic, not inventoried route

## Concerns

- Probe pass = non-404/non-5xx only; business `{code:404}` in HTTP 200 body is intentional for thin probes
- `ANT_PATH_MATCHER` retained; nested file paths use `/**` not `{*var}` (Spring 5.3 PathPattern not enabled)
- Missing session still returns JSON `code:404` (Python parity on body, not HTTP status)
