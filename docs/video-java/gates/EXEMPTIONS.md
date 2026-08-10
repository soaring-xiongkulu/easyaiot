# Phase 0 exemptions

Rows with Owner sign-off `pending` are **provisional** — certify may mark a layer `exempt` but the case does not satisfy gate PASS until sign-off is recorded. Signed exemptions (`pass` or `exempt` with a signed ID) count toward case `ok`.

| ID | Capability | Reason | Owner sign-off |
|----|------------|--------|----------------|
| EX-REMOTE-NODE | Remote iot-node deploy for algorithm tasks | Phase 0 local-only; `schedule_policy!=local` rejected with 400 | orchestrator, 2026-08-10 |
| EX-KAFKA-HOOK | Kafka alert path when `use-direct-persist=false` | mini/local uses DB direct persist aligned with Python mini | orchestrator, 2026-08-10 |
| EX-ORACLE-HEALTH-DB | Oracle `/actuator/health` HTTP 500 (DB probe encoding) | Env-specific; P0 requires Java candidate UP; oracle DB health documented | orchestrator, 2026-08-10 |
| EX-GATEWAY-AUTH-LOCAL | Gateway OAuth token check via `system-server` on mini profile | CLOSE-S3: routing proven (200); Bearer triggers `TokenAuthenticationFilter` → `:48099` check; system-server not running locally | orchestrator, 2026-08-10 |
| EX-AUDIO-TALK | ONVIF audio back-channel (`/video/camera/audio/talk/*`) | Out of Phase 0–2; requires ONVIF back-channel service + device probe stack; deferred Phase 3+ | orchestrator, 2026-08-10 |
| EX-SCENARIO-POSE | Scenario pose library (`/video/scenario-pose/*`) | Out of Phase 0–2; library CRUD, entry extract, match-test; deferred Phase 3+ | orchestrator, 2026-08-10 |
| EX-PATROL-SESSION-API | Patrol session orchestration (`/video/patrol/session/*`, heartbeat, SSE events) | Phase 2 certifies algorithm `task_type=patrol` list only (`vj_p2_patrol_task_list`); interactive session API deferred Phase 3+ | orchestrator, 2026-08-10 |
| EX-ALERT-ADMIN-API | Alert admin/query surface (`/video/alert/page`, count, statistics, clear, image, record query) | Phase 0 certifies `POST /video/alert/hook` only (`vj_p0_alert_hook`); dashboard/list/clear deferred Phase 3+ | orchestrator, 2026-08-10 |
