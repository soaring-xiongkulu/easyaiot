# Phase 0 exemptions

Rows with Owner sign-off `pending` are **provisional** — certify may mark a layer `exempt` but the case does not satisfy gate PASS until sign-off is recorded. Signed exemptions (`pass` or `exempt` with a signed ID) count toward case `ok`.

| ID | Capability | Reason | Owner sign-off |
|----|------------|--------|----------------|
| EX-REMOTE-NODE | Remote iot-node deploy for algorithm tasks | Phase 0 local-only; `schedule_policy!=local` rejected with 400 | orchestrator, 2026-08-10 |
| EX-KAFKA-HOOK | Kafka alert path when `use-direct-persist=false` | **resolved by FR-W1-KAFKA** (2026-08-10): `AlertKafkaProducer` + minimal camelCase message to `iot-alert-notification` / `iot-snapshot-alert`; suppress interval; Kafka failure → direct_persist fallback; local/mini default `use-direct-persist=true` | orchestrator, 2026-08-10 |
| EX-ORACLE-HEALTH-DB | Oracle `/actuator/health` HTTP 500 (DB probe encoding) | Env-specific; P0 requires Java candidate UP; oracle DB health documented | orchestrator, 2026-08-10 |
| EX-GATEWAY-AUTH-LOCAL | Gateway OAuth token check via `system-server` on mini profile | **resolved by FR-W1-AUTH** (2026-08-10): `system-server` `:48099` live; invalid Bearer → 401; valid token (admin login) → gateway 200 + video-server body; see `GATEWAY_AUTH_SMOKE.md` | orchestrator, 2026-08-10 |
| EX-AUDIO-TALK | ONVIF audio back-channel (`/video/camera/audio/talk/*`) | **resolved by FR-W3-TALK** (2026-08-10): Java `AudioTalkController` + `AudioTalkService` / `OnvifAudioBackchannelClient`; route_inventory `/video/camera/audio/talk` diff=0 | orchestrator, 2026-08-10 |
| EX-SCENARIO-POSE | Scenario pose library (`/video/scenario-pose/*`) | Out of Phase 0–2; library CRUD, entry extract, match-test; deferred Phase 3+ | orchestrator, 2026-08-10 |
| EX-PATROL-SESSION-API | Patrol session orchestration (`/video/patrol/session/*`, heartbeat, SSE events) | **resolved by FR-W2-PATROL** (2026-08-10): Java `PatrolController` + `PatrolSessionService` / `PatrolProgressHub`; route_inventory `/video/patrol` diff=0 | orchestrator, 2026-08-10 |
| EX-ALERT-ADMIN-API | Alert admin/query surface (`/video/alert/page`, count, statistics, clear, image, record query) | **resolved by FR-W1-ALERT** (2026-08-10): Java admin APIs ported from retired Python `alert.py` + `alert_service.py`; route_inventory `/video/alert` diff=0 | orchestrator, 2026-08-10 |
