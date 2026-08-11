# Phase 2 A1 Report — Alert Kafka path (handoff for subsequent packs)

**Status:** PASS  
**Pack:** P2-A1  
**Date:** 2026-08-11  
**Commit:** `2b3d483` — `feat(video-java): phase2 A1 alert kafka parity`  
**Evidence:** `logs/phase2-a1-alert-kafka.json`  
**Docs:** `docs/video-java/PHASE2_MAINPATH.md` (A1 section)

## Prior packs
- Phase 1 stack: `docs/video-java/PHASE1_STACK.md` (0.1/0.2/0.3 PASS; PG **15432**)

## What was proven
- Profile `local`, `video.alert.use-direct-persist=false`
- Gateway `POST /admin-api/video/alert/hook` → `mode=kafka`, topic `iot-alert-notification`, partition 48, offset 1
- Direct `:48096` → same path, offset 2
- Broker consume verified; correlationId `phase2-a1-20260811172715`
- No `direct_persist` fallback on success path

## Oracle vs Java
- Python `alert_hook_service.py`: non-mini → Kafka primary
- Java `AlertHookService` / `AlertKafkaProducer`: aligned

## Fixture left in DB
- Device `frb26_device`, task 61 `frb26_alert_e2e`

## Constraints for next agents
- Do NOT flip shortcuts / mini to fake green
- Do NOT claim COMPLETE / delete Python
- Do NOT open FR-Bxx
- Stack: PG 15432, Kafka 9092, Nacos 8848, MinIO 9000, GW 48080, video 48096 **local**

## Next pack
**P2-A2** — algo task start/stop + real RUNTIME (`logs/phase2-a2-runtime-lifecycle.json`)
