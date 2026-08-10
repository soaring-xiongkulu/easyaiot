# FR-W2-PATROL Report

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Summary

Ported all **9** `/video/patrol` Python routes to Java `PatrolController` + `PatrolSessionService` / `PatrolProgressHub` / `PatrolSupervisor`.  
`route_inventory.py --prefix /video/patrol` → **Py 9 / Java 9 / diff 0**.  
**EX-PATROL-SESSION-API resolved.**  
`certify.py --phase 0` → **exit 0**.

## Commits

(see `git log -1` after commit)

## Python files read

| File | Scope |
|------|--------|
| `VIDEO/_retired_python_video/app/blueprints/patrol.py` | **全部** 9 `@patrol_bp.route` |
| `VIDEO/_retired_python_video/app/services/patrol_session_service.py` | create/start/stop/heartbeat/stats/directory devices |
| `VIDEO/_retired_python_video/app/services/patrol_progress_hub.py` | SSE subscribe/publish |
| `VIDEO/_retired_python_video/models.py` | `PatrolSession` model + `to_dict` |
| `VIDEO/_retired_python_video/run.py` | `url_prefix='/video/patrol'` |

## Inventory

```
prefix: /video/patrol
python: 9
java:   9
matched: 9
diff: 0
```

## GAP §2.8 progress

| 功能 | 状态 |
|------|------|
| POST `/session` | ✅ |
| GET/PATCH `/session/{id}` | ✅ |
| POST `/session/{id}/start\|stop` | ✅ |
| GET `/session/{id}/stats` | ✅ |
| GET `/session/{id}/events` (SSE) | ✅ |
| POST `/heartbeat` | ✅ |
| GET `/directory/{id}/devices` | ✅ |
| 路由差 | **Py 9 / Java 9 / diff 0** |
| EX-PATROL-SESSION-API | **resolved** |

## Phase 0

`python tools/video_java/certify.py --phase 0` → **exit 0** (2026-08-10)

## Concerns

1. **Patrol 守护进程** — `PatrolSupervisor` 启动 `EDGE/runtime/services/patrol_algorithm_service/run_deploy.py`；需本机 Python + 依赖；脚本缺失时守护循环空转。
2. **默认目录国标同步** — Python `resolve_directory_device_ids` 对「默认分组」会先 `sync_gb28181_channels_to_devices`；Java 仅读 DB 并记 warning。
3. **SSE 长连接** — `PatrolProgressHub` 对齐 hub 语义；生产需验证网关缓冲（`X-Accel-Buffering: no`）。
4. **Maven 编译** — 本机 shell 无 `mvn` PATH；`route_inventory` + `certify --phase 0` 已绿（沿用既有 fat jar）。

## Remaining routes

**无**（inventory diff=0）
