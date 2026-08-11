# Brief — CP-2: Matching consume chain (code-complete)

## CRITICAL — NO NESTED SUBAGENTS
Leaf only when executed (另令).

## Goal
Plate matching consumer enabled on commercial local path; face consume→process path (iot-sink FaceMatchingConsumer → `/face/matching/process`) provable. Engine missing → honest bypass/fail (Part2), **not** matched success. Never `use-direct-process=true`.

## Oracle / Java
- `library_matching_service.py`, face/plate kafka services
- `PlateMatchingKafkaConsumerRunner`, `VideoProperties.Matching`
- `DEVICE/iot-sink/.../FaceMatchingConsumer.java`, `PlateMatchingConsumer.java`, `*MatchingServiceImpl`

## Done when
- Evidence consume invoked process (or sink HTTP to process)
- Plate DB hit/miss via consume path acceptable
- Face: process reached with honest bypass if no InsightFace/Milvus
- `logs/cp-2-matching-consume.json` + `cp-2-report.md`

## Prereq
CP-1
