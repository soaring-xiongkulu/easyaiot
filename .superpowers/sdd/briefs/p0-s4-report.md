# P0-S4 Report — Heartbeat bilateral parity

## STATUS
**DONE** — `vj_p0_heartbeat` lifecycle pass with fresh Java sampling on `:48096`. `vj_p0_task_start_stop` and `vj_p0_alert_hook` remain pass. Phase 0 gate still **FAIL** (health exempt only — expected out of scope).

## Commit
`fix(video-java): P0-S4 heartbeat bilateral parity for lifecycle`

## Root cause
1. Java `HeartbeatService.receiveRealtime` always wrote `run_status=running` on heartbeat POST.
2. Oracle Python only promotes `run_status` when it is **not** already `stopped` (`algorithm_task.py`); after `_ensure_task_stopped`, heartbeat leaves `run_status=stopped`.
3. Java `run_java.py` sampled lifecycle from `GET /task/{id}` instead of `/services/status` contract shared with `record_python.py`.

## Fixes
1. **HeartbeatService** — mirror oracle: pass `null` for `run_status` update when task is `stopped`; only promote to `running` otherwise (`COALESCE` in repo preserves DB value).
2. **run_java.py** — `_record_heartbeat` calls `_ensure_task_stopped`, uses `_task_service_status` + `_lifecycle_from_service`, aligned `control_port`/`log_path` with oracle sampler.
3. Fresh `golden/java/vj_p0_heartbeat` sampled after rebuild + restart of `:48096`.

## Verify
```text
mvn -f DEVICE/pom.xml -pl iot-video/iot-video-biz -am package -DskipTests
java -jar DEVICE/iot-video/iot-video-biz/target/iot-video-biz.jar --spring.profiles.active=local
python tools/video_java/certify.py --phase 0
```

| case_id | ok | layers | notes |
|---------|----|--------|-------|
| vj_p0_health | FAIL | api:exempt | EX-ORACLE-HEALTH-DB (expected) |
| vj_p0_task_start_stop | PASS | lifecycle:pass, ini:pass | unchanged |
| **vj_p0_heartbeat** | **PASS** | **lifecycle:pass** | **P0-S4 target** |
| vj_p0_alert_hook | PASS | alarm:pass | unchanged |

**heartbeat lifecycle snapshot (both sides):** `run_status=stopped`, `service_server_ip=127.0.0.1`, `service_port=8101`, `heartbeat_ok=true`.

## Concerns
- Health layer remains `exempt` not `pass` — gate cannot claim full Phase 0 PASS (P0-S5/S6).
- Oracle and Java share task_id=35 + DB; certify stops task before heartbeat on both sides.
- Java candidate jar must be rebuilt/restarted after code changes (file lock during repackage).
