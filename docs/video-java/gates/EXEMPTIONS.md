# Phase 0 exemptions

All rows are **provisional** until Owner sign-off is recorded (not `pending`). Certify may mark a layer `exempt` only when the case manifest references a listed ID.

| ID | Capability | Reason | Owner sign-off |
|----|------------|--------|----------------|
| EX-REMOTE-NODE | Remote iot-node deploy for algorithm tasks | Phase 0 local-only; `schedule_policy!=local` rejected with 400 | pending |
| EX-KAFKA-HOOK | Kafka alert path when `use-direct-persist=false` | mini/local uses DB direct persist aligned with Python mini | pending |
| EX-ORACLE-HEALTH-DB | Oracle `/actuator/health` HTTP 500 (DB probe encoding) | Env-specific; P0 requires Java candidate UP; oracle DB health documented | pending |
