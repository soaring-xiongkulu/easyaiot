# FR-W1-KAFKA Report

**STATUS:** DONE  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Python files read (oracle)

1. `VIDEO/_retired_python_video/app/services/alert_hook_service.py` — Kafka produce, topic resolve, suppress, minimal/notification message body, direct_persist vs Kafka branch, fallback on failure
2. `VIDEO/_retired_python_video/app/blueprints/alert.py` — `POST /hook` entry, success/skipped/suppressed/failed response shells

## Python ↔ Java mapping

| Python | Java | Notes |
|--------|------|-------|
| `_should_use_direct_alert_persist()` | `VideoProperties.Alert.useDirectPersist` | local/mini yaml default `true` |
| `_kafka_topic_for_alert_task_type()` | `AlertKafkaProducer.resolveTopic()` | `snap` → `iot-snapshot-alert`; else `iot-alert-notification` |
| `_build_minimal_alert_kafka_message()` | `AlertKafkaMessageBuilder.buildMinimal()` | camelCase fields for iot-sink `AlertNotificationMessage` |
| `_should_suppress_alert_event_kafka()` | `AlertEventKafkaSuppressor` | in-memory per `(deviceId, taskType)` |
| `get_kafka_producer()` + `producer.send(key=device_id)` | `AlertKafkaProducer` + `KafkaTemplate` | `client-id=video-alert-producer`, 10s send timeout |
| `_fallback_persist_on_kafka_failure()` | `AlertHookService.fallbackPersistOnKafkaFailure()` | Kafka error → direct DB persist |
| `kafka_path_not_implemented_p0` | **removed** | `use-direct-persist=false` now attempts real produce |

## Short contract

| Config | Expected hook result |
|--------|---------------------|
| `use-direct-persist=true` (default local/mini) | `status=success`, `mode=direct_persist` |
| `use-direct-persist=false` + broker up | `status=success`, `mode=kafka`, `topic`/`partition`/`offset` present |
| `use-direct-persist=false` + broker down | `status=success` with `kafka_fallback=true` **or** `status=failed` + kafka error (not `kafka_path_not_implemented_p0`) |

## EXEMPTIONS

`EX-KAFKA-HOOK` → **resolved by FR-W1-KAFKA**

## GAP

§2.2 Kafka 行为行 + §4 Alert→Kafka + §7 P0 Kafka → ✅

## phase0

`python tools/video_java/certify.py --phase 0` → **exit 0** (default `use-direct-persist=true`; `vj_p0_alert_hook` alarm layer `success`)

## Concerns

- Notification-config rich message (`_build_notification_message_for_kafka`) not ported — minimal message only (matches Python no-notification-config path).
- Prod cutover still needs live Kafka + iot-sink consumer soak; local certify does not require broker.
- Suppress state is JVM in-memory (matches Python process-local dict).
