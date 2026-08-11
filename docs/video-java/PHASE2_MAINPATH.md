# Phase 2 — Main-path parity (local full stack)

> Worktree: `feat/video-java` · Profile: **`local`** (commercial defaults) · Oracle: `F:/acme/VIDEO/`

Phase 1 stack wiring is documented in [PHASE1_STACK.md](./PHASE1_STACK.md). This file tracks **main-path** parity packs (A-series) against Python Oracle on the local full stack.

---

## Pack A1 — Alert hook Kafka path

| Field | Value |
|-------|-------|
| **Status** | **PASS** |
| **Date** | 2026-08-11 |
| **Evidence** | `logs/phase2-a1-alert-kafka.json` |

### Goal

Prove Java `video-server` under `profile=local` sends alert hooks via **real Kafka** (`use-direct-persist=false`), aligned with Python non-mini `alert_hook_service.process_alert_hook`.

### Oracle reference (Python)

| Item | Location |
|------|----------|
| Direct-persist gate | `VIDEO/app/services/alert_hook_service.py` → `_should_use_direct_alert_persist()` — false when env unset and not mini |
| Kafka path | `get_kafka_producer()` → `producer.send(topic, key=device_id)` → returns `topic` / `partition` / `offset` |
| Fallback | `_fallback_persist_on_kafka_failure` only on Kafka failure (not primary local path) |

### Java candidate

| Item | Location |
|------|----------|
| Config | `application-local.yaml` → `video.alert.use-direct-persist: false` |
| Service | `AlertHookService.processHook()` → `sendViaKafka()` when `useDirectPersist` false |
| Response | `mode=kafka`, `topic`, `partition`, `offset` |

### Acceptance results

| # | Check | Result |
|---|-------|--------|
| 1 | `video.alert.use-direct-persist=false` (committed local + effective) | **PASS** |
| 2 | `POST /admin-api/video/alert/hook` (gateway) | **PASS** — `mode=kafka` |
| 3 | `POST /video/alert/hook` (direct :48096) | **PASS** — `mode=kafka` |
| 4 | Broker message on `iot-alert-notification` | **PASS** — consumed at partition 48 |
| 5 | No direct_persist fallback on success path | **PASS** |

### Fixture

- Device: `frb26_device` (task 61 `frb26_alert_e2e`, `alert_event_enabled=true`)

---

## Next pack

**A2** — TBD per brief / CUTOVER_BLOCKERS (MinIO alert image upload chain or next main-path item).
