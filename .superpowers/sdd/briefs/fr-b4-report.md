# FR-B4 Report — Remote node / EX-REMOTE-NODE

**Date:** 2026-08-10  
**Worktree:** `video-java`  
**Status:** DONE

## Summary

Implemented Java iot-node remote deploy client aligned with retired Python `node_client.py`, replacing hard HTTP 400 rejects for `schedule_policy=auto|node` when remote deploy is enabled. Mini profile falls back to local supervisor (mirrors Python `is_remote_deploy_enabled()`).

## Python-first references read

| Path | Purpose |
|------|---------|
| `VIDEO/_retired_python_video/app/utils/node_client.py` | allocate / deploy / stop / release API contract |
| `VIDEO/_retired_python_video/app/services/algorithm_task_launcher_service.py` | algorithm remote deploy env + RUNTIME ini files |
| `VIDEO/_retired_python_video/app/services/stream_forward_launcher_service.py` | stream_forward remote deploy + env |
| `VIDEO/_retired_python_video/app/services/runtime_config_service.py` | `REMOTE_RUNTIME_BIN` paths |
| `DEVICE/iot-node/.../NodeSchedulerController.java` | `/node/scheduler/allocate` |
| `DEVICE/iot-node/.../NodeWorkloadController.java` | `/node/workload/deploy` + `/stop` |

## Java changes

| Component | Change |
|-----------|--------|
| `IotNodeClient` | HTTP client for iot-node scheduler + workload APIs |
| `RemoteScheduleSupport` | policy gating + env copy (Python parity) |
| `AlgorithmRemoteDeployService` | algorithm_task remote deploy |
| `StreamForwardRemoteDeployService` | stream_forward remote deploy |
| `AlgorithmTaskLifecycleService` | remote start/stop/status; remove hard 400 |
| `StreamForwardService` | remote start/stop; remove hard 400 |
| `RuntimeIniGenerator` | remote ini artifact for Agent `files` payload |
| `VideoProperties.nodeRemote` | config + `application-mini.yaml` default off |
| `EXEMPTIONS.md` | EX-REMOTE-NODE **resolved** |
| `FULL_REPLACEMENT_GAP.md` | algorithm + stream_forward remote rows ✅ |

## EX-REMOTE-NODE

**Resolved** — client implemented; prod still needs live iot-node + Agent + compute nodes.

## certify --phase 0

```
exit 0
```

Log: `certify-frb4-phase0.log`

## Concerns / follow-ups

1. **Prod cluster:** remote path requires iot-node online, Agent on compute nodes, `/opt/easyaiot/VIDEO` + RUNTIME on nodes.
2. **Stream-forward shards:** Java implements single-workload remote deploy; Python device-level shard spread / SRS ensure / failover migration not fully ported.
3. **Ceph mount:** Python `requireCephMount` on allocate not yet mirrored in Java client.
4. **Post-process cluster:** remote algorithm start does not yet chain `_start_post_process_cluster` (Python behavior).
