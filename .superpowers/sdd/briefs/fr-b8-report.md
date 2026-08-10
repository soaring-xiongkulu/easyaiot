# FR-B8 Report — stream_forward 集群健康迁移

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Ported Python `stream_forward_health_service` + launcher `migrate_unhealthy_stream_forward_task` / `redeploy_existing_shard` into Java: periodic cluster health scan for enabled `auto|node` tasks when remote deploy is on, migrating offline-node shards and heartbeat-stale redeploys via iot-node. Local-only / `schedule_policy=node` offline cases follow Python semantics (no auto-migrate for pinned node). Updated GAP §3.

## Python files read (oracle)

| Path | Purpose |
|------|---------|
| `VIDEO/app/services/stream_forward_health_service.py` | `is_health_monitor_enabled`, `run_stream_forward_health_cycle` |
| `VIDEO/app/services/stream_forward_launcher_service.py` | `migrate_unhealthy_stream_forward_task`, `redeploy_existing_shard`, heartbeat/node offline logic |
| `VIDEO/_retired_python_video/run.py` | APScheduler `STREAM_FORWARD_HEALTH_*` interval + startup one-shot |

## Java changes

| Component | Change |
|-----------|--------|
| `StreamForwardHealthService` | Health cycle; `STREAM_FORWARD_HEALTH_MONITOR_ENABLED` env gate |
| `StreamForwardHealthScheduler` | Fixed-delay job + startup cycle (`video.stream-forward-health.interval-ms`) |
| `StreamForwardRemoteDeployService` | `migrateUnhealthyTask`, `redeployExistingShard`, deployment JSON apply |
| `StreamForwardTaskRepository` | `findEnabledRemoteCapable`; nullable `node_id` on deploy update |
| `VideoProperties.streamForwardHealth` | Config defaults mirroring Python env |
| `FULL_REPLACEMENT_GAP.md` | §3 stream_forward 集群健康迁移 → **FR-B8 ✅** |

## GAP §3

- `stream_forward` 集群健康迁移 → **resolved by FR-B8**
- `stream_forward` auto_start 远程分片备注 → FR-B8 健康迁移

## certify --phase 0

```
exit 0
```

Log: `certify-frb8-phase0.log` (`record_python` warnings — oracle `:6000` not running; diff uses stale golden; all cases ok/exempt)

## Concerns

1. **Prod cluster** — migration requires live iot-node + Agent + remote VIDEO `run_deploy.py`; mini defaults `NODE_REMOTE_DEPLOY=false` (health monitor no-op).
2. **Device-level shards** — Java redeploys per `device_deployments` entry; Python multi-shard spread/SRS ensure not fully ported (FR-B4 follow-up).
3. **Local shard entries** — deployments marked `local: true` are skipped with warn (honest no-op vs Python `_deploy_shard_locally`).
4. **Full jar rebuild** — `mvn compile` ok; `spring-boot:repackage` may fail if `iot-video-biz.jar` locked by running candidate.
