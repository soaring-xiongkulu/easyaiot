# CP-2 Report — Matching consume→process chain (handoff for CP-4/CP-5)

**Status:** PASS  
**Pack:** CP-2 (W2-second)  
**Date:** 2026-08-11  
**Evidence:** `logs/cp-2-matching-consume.json`  
**nested_subagents:** none

## Prior reports

- [cp-1-report.md](./cp-1-report.md) — Kafka alert honest-fail; no direct_persist fallback
- [cp-3-report.md](./cp-3-report.md) — sink `:48092` UP, PG 15432, `enqueue_ok=true`; consumers in sink
- [phase2-a7-report.md](./phase2-a7-report.md) — publish + direct process proven; consume path was blocked by sink RestTemplate crash

## What changed

| File | Change |
|------|--------|
| `DEVICE/iot-sink/.../PlateMatchingServiceImpl.java` | Dedicated `SimpleClientHttpRequestFactory` RestTemplate for matching HTTP (fixes shared HttpComponents pool `NoClassDefFoundError` / `Connection pool shut down` that stopped Kafka listener on first consume) |
| `DEVICE/iot-sink/.../FaceMatchingServiceImpl.java` | Same RestTemplate isolation |
| `DEVICE/iot-sink/.../application-local.yaml` | `basiclab.video.service-url` → gateway `48080`; explicit `spring.kafka.face-matching` / `plate-matching` topic config |
| `docs/video-java/PHASE1_STACK.md` | Kafka topic bootstrap for `iot-face-matching`, `iot-plate-matching`, `iot-snapshot-alert` |

**Not changed:** `video.matching.plate-matching-consumer-enabled` remains **false** — commercial local path uses **iot-sink** consumers (aligned with Python sink worker design), not `PlateMatchingKafkaConsumerRunner` in video-server.

## Runtime path (proven)

```
video-server publish (/matching/publish)
  → Kafka iot-plate-matching | iot-face-matching
  → iot-sink PlateMatchingConsumer | FaceMatchingConsumer
  → HTTP POST gateway /admin-api/video/{plate|face}/matching/process
  → LibraryMatchingProcessor (plate DB hit/miss; face honest bypass)
```

| Check | Result |
|-------|--------|
| `use-direct-process` | **false** (unchanged) |
| Plate hit via consume | `matched=true`, `alert_id=8510`, `correlation_id=cp-2-plate-hit-20260811222309` |
| Plate miss via consume | `matched=false`, `status=success` |
| Face via consume | `status=bypassed`, `matched=false` — engine absent (Part2), **not** fake match |
| Sink log consume→process | `收到*匹配消息` → `开始调用*匹配` → `*匹配处理完成` in `logs/cp-2-sink-server.log` |

## Oracle vs Java

| Concern | Oracle (Python) | Java (CP-2) |
|---------|-----------------|-------------|
| Publish | Kafka topics `iot-face-matching` / `iot-plate-matching` | `MatchingKafkaProducer` (video-server) |
| Consume | Worker/sink consumes → calls process | `iot-sink` `*MatchingConsumer` → HTTP `/matching/process` via gateway |
| Plate process | `plate_entry` DB lookup | Same via `LibraryMatchingProcessor.processPlate` |
| Face process | InsightFace + Milvus | Honest `bypassed` when engine absent |
| Local consumer owner | Sink-side worker pattern | **iot-sink** (not video `PlateMatchingKafkaConsumerRunner`) |

## Bug found & fixed

First consume attempt (pre-fix) crashed sink `PlateMatchingConsumer` Kafka container: injected shared `RestTemplate` (HttpComponents pool) threw `NoClassDefFoundError` / `Connection pool shut down`. Matching services now use an isolated `RestTemplate` with `SimpleClientHttpRequestFactory`.

## Notes for CP-4 / CP-5 (W3)

1. **Sink restarted** for CP-2 evidence — `logs/cp-2-sink-server.log`; CP-3 enqueue regression should re-check if needed.
2. **Do not** enable `plate-matching-consumer-enabled=true` in video without coordinating consumer groups — sink already owns matching consume on local.
3. **Face engine** still Part2 — consume→process PASS does not require Milvus/InsightFace install.
4. Kafka topics `iot-face-matching`, `iot-plate-matching`, `iot-snapshot-alert` exist (64 partitions).

## Ready for W3 (CP-4 ∥ CP-5)?

**Yes** — matching consume chain code-complete on local commercial path; plate hit/miss and face honest bypass proven via sink consumers.
