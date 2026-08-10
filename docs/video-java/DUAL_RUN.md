# VIDEO Java — dual-run (Python oracle + Java candidate)

Phase 0/1 certify hits each side **directly** by base URL. Gateway cutover is **not** required for parity gates and is deferred to Phase 3.

## Services

| Role | Stack | Nacos name | Default port | Certify base URL |
|------|-------|------------|--------------|------------------|
| Oracle | Python `VIDEO/run.py` | `video-server` | `6000` | `http://127.0.0.1:6000` |
| Candidate | Java `iot-video-biz` | `video-server-java` | `48096` | `http://127.0.0.1:48096` |

Both may register in Nacos simultaneously. **Do not** rename the Java service to `video-server` during Phase 1.

## Background tasks / certify safety

| Flag | Python | Java (`application-local.yaml`) |
|------|--------|----------------------------------|
| Skip schedulers | `VIDEO_SKIP_BACKGROUND_TASKS=1` | `video.skip-background-tasks: true` |

Use skip mode during certify and when only one side should own task lifecycles. Oracle recording often sets `VIDEO_SKIP_BACKGROUND_TASKS=1` and starts tasks explicitly via scripts.

When skip is **off**, Java runs an algorithm-task health recovery timer aligned with Python:

- `ALGORITHM_HEALTH_MONITOR_ENABLED` / `video.health-monitor.enabled` (default `true`)
- `ALGORITHM_HEALTH_INTERVAL_SECONDS` / `video.health-monitor.interval-ms` (default `60000`)
- `ALGORITHM_HEARTBEAT_FAILOVER_SECONDS` / `video.health-monitor.heartbeat-failover-seconds` (default `90`)

Recovery scans **enabled** tasks with `schedule_policy=local` and calls start when the RUNTIME supervisor is down and heartbeat/run_status indicate unhealthy (mirrors `recover_unhealthy_algorithm_tasks`).

## Gateway (optional probe route)

Production default remains Python:

```yaml
# DEVICE/iot-gateway/.../application.yaml (unchanged in Phase 1)
- id: video-admin-api
  uri: lb://video-server
  predicates:
    - Path=/admin-api/video/**
```

Optional **side-by-side** route for manual Java probing (see `docs/video-java/gateway-optional-route.yaml`). Prefix `/admin-api/video-java/**` avoids stealing `/admin-api/video/**`.

**Phase 3 cutover:** prefer changing `video-admin-api` `uri` from `lb://video-server` to `lb://video-server-java` (or weighted routing) after Phase 2+ gates — not in Phase 1.

## Certify commands

```text
python tools/video_java/certify.py --phase 0 --no-record
python tools/video_java/certify.py --phase 1 --no-record
```

Direct bases are defined in `testdata/video-java/manifest.json` (`oracle_base_url` / `candidate_base_url`).

## Dual-run pitfalls

- Do not `auto_start` the same `task_id` on both stacks.
- Serial media cases (view-forward, stream-forward): stop oracle workers before sampling Java.
- Alarm hook cases must not dual-write the same fixture in parallel.
