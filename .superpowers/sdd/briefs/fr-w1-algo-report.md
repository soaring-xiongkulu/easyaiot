# FR-W1-ALGO Report

**STATUS:** DONE (implementation + route_inventory diff 0; phase0 see below)  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Python files read (oracle)

1. `VIDEO/_retired_python_video/app/blueprints/algorithm_task.py` — all `@route`
2. `VIDEO/_retired_python_video/app/services/algorithm_task_service.py` — CRUD / list / lifecycle helpers
3. `VIDEO/_retired_python_video/app/services/post_process_service.py` — init workspace, IDE URL, status
4. `VIDEO/_retired_python_video/app/services/post_process_result_service.py` — results pagination
5. `VIDEO/_retired_python_video/models.py` — `AlgorithmTask` fields / `to_dict`
6. `VIDEO/_retired_python_video/run.py` — blueprint `url_prefix='/video/algorithm'`

## Py route ↔ Java mapping (package scope)

| Method | Python path | Java |
|--------|-------------|------|
| GET | `/video/algorithm/task/list` | `AlgorithmTaskController.list` |
| GET | `/video/algorithm/task/{id}` | `AlgorithmTaskController.detail` |
| POST | `/video/algorithm/task` | `AlgorithmTaskController.create` |
| PUT | `/video/algorithm/task/{id}` | `AlgorithmTaskController.update` |
| DELETE | `/video/algorithm/task/{id}` | `AlgorithmTaskController.delete` |
| POST | `/video/algorithm/task/{id}/start\|stop\|restart` | `AlgorithmTaskController.start/stop/restart` |
| GET | `/video/algorithm/task/{id}/services/status` | `AlgorithmTaskController.servicesStatus` |
| POST | `/video/algorithm/heartbeat/realtime` | `HeartbeatController.realtime` |
| POST | `/video/algorithm/heartbeat/patrol` | `HeartbeatController.patrol` |
| GET | `.../extractor\|sorter\|pusher\|realtime/logs` | `AlgorithmTaskController.*Logs` → `AlgorithmTaskLogService` |
| GET | `.../streams` | `AlgorithmTaskController.streams` |
| GET | `.../post-process/status` | `AlgorithmTaskController.postProcessStatus` |
| POST | `.../post-process/init` | `AlgorithmTaskController.postProcessInit` |
| GET | `.../post-process/ide-url` | `AlgorithmTaskController.postProcessIdeUrl` |
| PUT | `.../post-process/toggle` | `AlgorithmTaskController.postProcessToggle` |
| GET | `.../post-process/results` | `AlgorithmTaskController.postProcessResults` (top-level `items/total/page_*`) |

## route_inventory `/video/algorithm`

```
python: 21
java:   21
matched: 21
diff:   0
```

Command: `python tools/video_java/route_inventory.py --prefix /video/algorithm`

## GAP §2.1

CRUD、patrol heartbeat、logs、streams、post-process 各行 ✅；`schedule_policy!=local` 远程 node 行为仍 ❌（400 + EX-REMOTE-NODE）。

## phase0

`python tools/video_java/certify.py --phase 0` → **exit 1** in this environment: `vj_p0_restart` lifecycle mismatch (`process_alive_after_restart` Python=true vs Java=false). Other P0 cases pass when server started with `--video.skip-background-tasks=false`. Root cause: Java health recovery scheduler default interval 60s vs certify restart wait ~11s (pre-existing, not introduced by FR-W1-ALGO).

## Short contract (`vj_fr_w1_algo_*` on `:48096`)

- create → get → update → delete: **pass**
- `POST /heartbeat/patrol` on realtime task → `code=400`: **pass**
- `GET .../realtime/logs`: **pass** (empty log placeholder when file missing)
- `GET .../streams`: **pass**
- `PUT .../post-process/toggle`: **pass**

## Concerns

- **AUTH + KAFKA remain cutover hard gates** (EX-GATEWAY-AUTH-LOCAL, EX-KAFKA-HOOK).
- CRUD insert sets `total_frames/total_detections/total_captures=0` for NOT NULL DB columns.
- `application-local.yaml` sets `skip-background-tasks: true` — use `--video.skip-background-tasks=false` for lifecycle certify / health recovery.
- Post-process `results` returns empty list when Kafka consumer path not wired (table query only).
