# FR-W2-SF Report

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Summary

Ported all **13** `/video/stream-forward` Python routes to Java `StreamForwardController` + `StreamForwardService` / `StreamForwardAdminService` / `StreamForwardLogService`.  
`route_inventory.py --prefix /video/stream-forward` → **Py 13 / Java 13 / diff 0**.  
`certify.py --phase 0` → **exit 0**.

## Commits

(see `git log -1` after commit)

## Python files read

| File | Scope |
|------|--------|
| `VIDEO/_retired_python_video/app/blueprints/stream_forward.py` | **全部** 13 `@stream_forward_bp.route` |
| `VIDEO/_retired_python_video/app/services/stream_forward_service.py` | CRUD/list/start/stop/restart/ensure-device |
| `VIDEO/_retired_python_video/app/services/stream_forward_launcher_service.py` | 启动器/守护进程（对照 status/restart 语义） |
| `VIDEO/_retired_python_video/run.py` | `url_prefix='/video/stream-forward'` |

## Inventory

```
prefix: /video/stream-forward
python: 13
java:   13
matched: 13
diff: 0
```

## GAP §2.4 progress

| 功能 | 状态 |
|------|------|
| GET `/task/list` | ✅ |
| GET/POST/PUT/DELETE `/task` | ✅ |
| POST `/task/{id}/start\|stop\|restart` | ✅（start/stop/status 保留） |
| GET `/task/{id}/status` | ✅ |
| POST `/heartbeat` | ✅ |
| GET `/task/{id}/logs` | ✅ |
| GET `/task/{id}/streams` | ✅ |
| POST `/device/{device_id}/ensure-task` | ✅ |
| 路由差 | **Py 13 / Java 13 / diff 0** |

## Phase 0

`python tools/video_java/certify.py --phase 0` → **exit 0** (2026-08-10)

## Concerns

1. **`schedule_policy!=local`** — 远程 node/auto 分片仍 400（EX-REMOTE-NODE）；与既有 start 行为一致。
2. **update `sync_action`** — Python 顶层 `sync_action` 字段；Java 写入 `data.sync_action`（WEB 需确认读取路径）。
3. **ensure-task 启动失败** — 对齐 Python：创建成功但 start 失败仍返回 task 元数据。
4. **Fat jar** — 已停 `:48096` 后重打；本机无 JDK 21，使用 `-Dmaven.compiler.release=17` + JDK 17 编译通过。
5. **集群健康迁移** — `stream_forward_health_service` 周期迁移未迁入 Java。

## Remaining routes

**无**（inventory diff=0）
