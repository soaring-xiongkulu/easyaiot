# FR-B17 Report — 全量路由 method-aware 薄契约探针

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Expanded `tools/video_java/contract_regression.py` with `--probe-all`: method-aware thin HTTP probes for all **265** inventoried Java routes (GET/HEAD→GET; POST/PUT/DELETE/PATCH with `{}` body). Live run against Java `:48096` (local profile): **259 pass / 6 fail / 0 skip**. Artifacts: `logs/fr-b17-contract-latest.{json,md}`. GAP §5/§8/§9 updated; `progress.md` FR-B15/B16 hashes corrected.

**COMPLETE 未宣称** — 6 probe fails、字段级契约、prod 联调仍 open。

## Python-first reads

| Path | Purpose |
|------|---------|
| `tools/video_java/route_inventory.py` | 14-prefix `BLUEPRINT_SPECS`, `java_routes` / `python_routes`, `{param}` normalization |
| `VIDEO/_retired_python_video/app/blueprints/alert.py` | Flask `@alert_bp.route` method defaults (GET) + explicit `methods=[...]` |
| `tools/video_java/contract_regression.py` (FR-B16) | Extended — not replaced |

## Changes

| Component | Change |
|-----------|--------|
| `contract_regression.py` | `--probe-all` + `collect_inventoried_routes`, `probe_route`, `summarize_probes`; `fr-b17-contract-*` artifacts |
| `IsapiHttpClient.java` | `@Service` — required for Spring context boot (was blocking `:48096` startup) |
| `FULL_REPLACEMENT_GAP.md` | §5 证据门禁 FR-B17 行；§8 探针计数表；§9 6 fail 诚实表述 |
| `progress.md` | FR-B15→`68f6811`, FR-B16→`8b71d4b`, FR-B17 row |

## Probe counts (live `:48096`)

| Metric | Count |
|--------|------:|
| probed | 265 |
| pass | 259 |
| fail | 6 |
| skip | 0 |

**Fails (mapped ≠ behavior-complete):**

1. `GET /video/patrol/session/{param}` — 404  
2. `GET /video/patrol/session/{param}/stats` — 404  
3. `PATCH /video/patrol/session/{param}` — 404  
4. `POST /video/playback` — 404  
5. `GET /video/record/space/{param}/video/{param}` — 500  
6. `GET /video/snap/space/{param}/image/{param}` — 500  

Thin smoke (14-prefix): 13/14 pass; `/video/device-detection/regions` smoke path 404 (pre-existing SMOKE_ENDPOINTS shape).

## GAP deltas

- §5：FR-B17 ✅ 265-route probe execution + artifact path
- §8：新增 FR-B17 探针行（259/6/0）
- §9：全量回归“仅 inventory”→已执行；剩余 6 fail + 字段级 + prod 联调

## certify --phase 0

```
exit 0
```

Log: `logs/fr-b17-phase0.log`（Java :48096 UP；vj_p0_* green）

## Remaining

- 6 HTTP probe fails（patrol session 路径、playback POST、record/snap 嵌套 GET 500）
- 字段级 JSON 契约（`{code,msg,data}` 全接口对表）
- prod broker/MinIO/真机/WVP/iot-node 联调
- 生产回滚/切流演练

## Concerns

- Probe pass = non-404/non-5xx only; 401/403/4xx validation counted pass per brief
- `{param}` materialized as `1` — may not match Spring path variable semantics for all routes
- `IsapiHttpClient` missing `@Service` was latent startup blocker (fixed minimally for live probes)
- 6 fails are honest backlog — do not treat 259/265 as COMPLETE
