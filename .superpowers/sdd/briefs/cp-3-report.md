# CP-3 Report — iot-sink 15432 + enqueue_ok (handoff for CP-2)

**Status:** PASS  
**Pack:** CP-3 (W2-first)  
**Date:** 2026-08-11  
**Evidence:** `logs/cp-3-sink-enqueue.json`  
**nested_subagents:** none

## Prior reports

- [cp-1-report.md](./cp-1-report.md) — Kafka alert honest-fail; sink `:48092` still down
- [phase2-a6-report.md](./phase2-a6-report.md) — A6 ⛔缺 sink; wiring correct, `enqueue_ok=false`

## What changed

| File | Change |
|------|--------|
| `DEVICE/iot-sink/iot-sink-biz/src/main/resources/application-local.yaml` | PG `master` / `video` / `node` → **`127.0.0.1:15432`**; Redis **`16379`**; `tdengine.lazy=true`; disable EMQX/Modbus/OPC UA on local commercial path |
| `DEVICE/iot-sink/iot-sink-biz/src/main/resources/bootstrap-local.yaml` | Nacos discovery on; **config center disabled** (same as `video-server` — avoids Nacos `:5432` override) |
| `docs/video-java/PHASE1_STACK.md` | Added Redis/sink rows + start commands + Kafka topic bootstrap |

## Runtime (local commercial stack)

| Service | Port | Notes |
|---------|------|-------|
| `sink-server` | **48092** | `bootstrap.yaml` `server.port`; matches `VideoProperties.PostProcess.sinkPort` |
| PostgreSQL | **15432** | `iot-device20`, `iot-video20`, `iot-node20` datasources |
| Redis | **16379** | docker map (not host 6379) |
| Kafka | **9092** | Topics `iot-post-process-request` / `iot-post-process-result` created for enqueue |

**Start (after `mvn -f DEVICE/pom.xml -pl iot-sink/iot-sink-biz -am package -DskipTests`):**

```powershell
$env:NACOS_PASSWORD = "<from F:/acme/VIDEO/.env>"
java -jar DEVICE/iot-sink/iot-sink-biz/target/iot-sink-biz.jar --spring.profiles.active=local
```

Sink listens on `http://127.0.0.1:48092/post-process/enqueue` (direct, `sink-use-gateway=false`).

## Evidence summary

| Check | Result |
|-------|--------|
| Sink health `48092` | `{"status":"UP"}` |
| Direct `POST /post-process/enqueue` | `code=0`, `data=true` (warm ~3s) |
| Alert hook → orchestrator → sink | `enqueue_ok=true`, `enqueue_url=post-process/enqueue` |
| `use-stub-enqueue` | **false** (unchanged) |

Correlation: `cp-3-evidence-20260811215606` — alert hook `mode=kafka` + status `enqueue_ok=true`.

## Oracle vs Java

- Python `post_process_sink_client._sink_enqueue_url()` → `http://127.0.0.1:48092/post-process/enqueue`
- Java `PostProcessSinkClient.sinkEnqueueUrl()` — same default direct path
- Sink `PostProcessController.enqueue` → Kafka `iot-post-process-request` (honest failure if topic/broker down)

## Notes for CP-2

1. **Sink UP** — `FaceMatchingConsumer` / `PlateMatchingConsumer` / post-process consumers run in sink process (not video).
2. **Kafka topics still missing on fresh stack** (create before matching evidence): `iot-face-matching`, `iot-plate-matching`, `iot-snapshot-alert` (see sink consumer WARN spam).
3. **Post-process worker** `127.0.0.1:19680` not required for enqueue PASS; consumer will WARN on worker connect refused.
4. **PG** — all sink dynamic datasources committed to **15432**; do not revert to `:5432`.
5. **First enqueue after cold sink** may exceed video `enqueue-timeout-ms=5000` until Kafka topic metadata exists — create topics per `PHASE1_STACK.md` or wait for auto-create.

## Ready for CP-2?

**Yes** — sink running on `:48092`, PG aligned, `enqueue_ok=true` proven on commercial `local` path without stub.
