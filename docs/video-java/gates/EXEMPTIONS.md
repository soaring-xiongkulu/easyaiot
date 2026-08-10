# Phase 0 exemptions

Rows with Owner sign-off `pending` are **provisional** — certify may mark a layer `exempt` but the case does not satisfy gate PASS until sign-off is recorded. Signed exemptions (`pass` or `exempt` with a signed ID) count toward case `ok`.

| ID | Capability | Reason | Owner sign-off |
|----|------------|--------|----------------|
| EX-REMOTE-NODE | Remote iot-node deploy for algorithm tasks | Phase 0 local-only; `schedule_policy!=local` rejected with 400 | orchestrator, 2026-08-10 |
| EX-KAFKA-HOOK | Kafka alert path when `use-direct-persist=false` | mini/local uses DB direct persist aligned with Python mini | orchestrator, 2026-08-10 |
| EX-ORACLE-HEALTH-DB | Oracle `/actuator/health` HTTP 500 (DB probe encoding) | Env-specific; P0 requires Java candidate UP; oracle DB health documented | orchestrator, 2026-08-10 |
