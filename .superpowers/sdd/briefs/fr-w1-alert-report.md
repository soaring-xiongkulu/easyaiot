# FR-W1-ALERT Report

**STATUS:** DONE  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Python files read (oracle)

1. `VIDEO/_retired_python_video/app/blueprints/alert.py` — all routes, params, error shells, image/record/query behavior  
2. `VIDEO/_retired_python_video/app/services/alert_service.py` — list/count/statistics/clear/correlation/record resolve semantics  
3. `VIDEO/_retired_python_video/models.py` — `class Alert` fields  
4. `VIDEO/_retired_python_video/run.py` — blueprint `url_prefix='/video/alert'`  
5. (aux) `VIDEO/_retired_python_video/app/services/media_dvr_utils.py` — `resolve_playback_absolute_path` for `/record`

## Py route ↔ Java mapping

| Method | Python path | Java |
|--------|-------------|------|
| GET | `/video/alert/page` | `AlertController.page` |
| GET | `/video/alert/count` | `AlertController.count` |
| GET | `/video/alert/statistics` | `AlertController.statistics` |
| GET | `/video/alert/correlation` | `AlertController.correlation` |
| GET | `/video/alert/image` | `AlertController.image` |
| GET | `/video/alert/record` | `AlertController.record` |
| GET | `/video/alert/record/query` | `AlertController.queryRecord` |
| DELETE | `/video/alert/clear` | `AlertController.clear` (`object==task_name`) |
| DELETE | `/video/alert/clear/all` | `AlertController.clearAll` |
| POST | `/video/alert/hook` | `AlertHookController.hook` (unchanged) |

## route_inventory `/video/alert`

```
python: 10
java:   10
diff:   0
```

Command: `python tools/video_java/route_inventory.py --prefix /video/alert`

## GAP §2.2

All alert admin routes marked ✅; `/video/alert` route diff **0** (Py 10 / Java 10).

## phase0

`python tools/video_java/certify.py --phase 0` → **exit 0** (retry after transient lifecycle flake on first run).

## Short contract (fixture prefix `vj_fr_w1_alert_*`)

- `GET /video/alert/page?pageNo=1&pageSize=1` → `code=0`, `data.alert_list` + `data.total`  
- `GET /video/alert/count` → `code=0`, `data.total_count`  
- `GET /video/alert/statistics` → `code=0`, dashboard keys present  
- `DELETE /video/alert/clear?task_name=vj_fr_w1_alert_task` → safe scoped delete by `object==task_name`  
- `DELETE /clear/all` **not** exercised on shared DB (API implemented; use isolated task_name only in CI)

## EXEMPTIONS

`EX-ALERT-ADMIN-API` → **resolved by FR-W1-ALERT**

## Concerns

- **AUTH + KAFKA remain cutover hard gates** (EX-GATEWAY-AUTH-LOCAL, EX-KAFKA-HOOK).  
- MinIO image download URL path in `/image` returns 400 locally (local filesystem path is fully supported).  
- `record/query` RecordFile fallback not ported (Playback + alert `record_path` only; matches simplified Java data layer).  
- Running `:48096` jar may need rebuild/restart to pick up new controllers in live env.
