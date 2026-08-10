# FR-B1 Report — Post-process 真 sink

**STATUS:** DONE  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Python files read (oracle)

1. `VIDEO/_retired_python_video/app/services/post_process_sink_client.py` — `_sink_enqueue_url()`, `build_post_process_request_message()`, `publish_post_process_request()` HTTP POST + code check
2. `VIDEO/_retired_python_video/app/services/post_process_service.py` — workspace/status (no direct sink; orchestration via runner)
3. `VIDEO/_retired_python_video/app/services/alert_post_orchestrator.py` — `_try_post_process_enqueue()` cpp hook follow-on
4. `VIDEO/_retired_python_video/app/utils/post_process_runner.py` — `enqueue_post_process_request()` → `publish_post_process_request_async`

## Python ↔ Java mapping

| Python | Java | Notes |
|--------|------|-------|
| `IOT_SINK_API_URL` / host:port / gateway | `VideoProperties.PostProcess` + env overrides in `sinkEnqueueUrl()` | direct `http://host:48092/post-process/enqueue` or gateway `/admin-api/sink/post-process/enqueue` |
| `publish_post_process_request()` | `PostProcessSinkClient.publishPostProcessRequest()` | `use-stub-enqueue=false` → real HTTP; 5s timeout |
| `build_post_process_request_message()` | `buildPostProcessRequestMessage()` | camelCase JSON body aligned |
| mini stub (certify) | `use-stub-enqueue: true` (local/mini yaml) | audit `enqueue_ok=true` for `vj_p2_post_process_enqueue` |
| HTTP failure → `False` + warn log | non-2xx / `code!=0` / `RestClientException` → `enqueue_ok=false` + warn | no silent success when stub off |

## Short contract

| Config | Expected |
|--------|----------|
| `use-stub-enqueue=true` (default local/mini) | stub log + audit `enqueue_ok=true` (certify-safe) |
| `use-stub-enqueue=false` + sink up | HTTP 2xx + `code` 0/null → `enqueue_ok=true` |
| `use-stub-enqueue=false` + sink down | `enqueue_ok=false`, warn log (not stub success) |

## GAP §4

`Post-process → iot-sink` → **resolved by FR-B1** (local/mini default stub; prod set `use-stub-enqueue=false` + reachable iot-sink)

## phase0

`python tools/video_java/certify.py --phase 0` → **exit 0**

## p2 post_process

`vj_p2_post_process_enqueue` not re-run this slice; relies on stub path + `PostProcessEnqueueAudit` (same as pre-FR-B1). Real-sink path requires live iot-sink on 48092 — not required for phase 0.

## Concerns

- Prod cutover needs iot-sink soak with `use-stub-enqueue=false`; certify does not start sink-server.
- Gateway path (`sink-use-gateway=true`) coded but not exercised in local certify.
- `mvn package` repackage may fail if `iot-video-biz.jar` locked by running candidate; `mvn compile` succeeds.
