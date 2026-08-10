# FR-B15 Report — DVR Kafka upload consumer + VIDEO/services 处置表

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Implemented JVM-embedded Kafka consumer for `media.dvr.completed` calling existing `DvrUploadService.processDvrEvent` with Python upload-worker retry/DLQ parity. Consumer gated by `video.media.upload-mode` (`kafka`/`hybrid` only; default `sync` needs no broker). Added `VIDEO/services/*` disposition table to `FULL_REPLACEMENT_GAP.md` §3.1.

**COMPLETE 未宣称** — prod broker 联调、snap Kafka consumer、全量契约回归仍 open。

## Python files read (oracle)

| Path | Purpose |
|------|---------|
| `VIDEO/_retired_python_video/services/media_upload_worker/run_worker.py` | Kafka consume `media.dvr.completed` (L21–22); manual commit; retry `_retry`≤12 → `publish_dvr_dlq` (L63–79); poll loop + broker-down sleep 5s (L80–82) |
| `VIDEO/_retired_python_video/app/services/dvr_upload_service.py` | `process_dvr_event` (L32–167): device resolve, file stable wait, MinIO upload, playback/record metadata, DLQ on S3Error (L155) |
| `VIDEO/_retired_python_video/app/services/media_kafka_service.py` | `is_kafka_upload_mode` / `is_hybrid_upload_mode` (L21–27); `publish_dvr_event` / `publish_dvr_dlq` (L105–126); topic defaults `media.dvr.completed` / `media.dvr.dlq` |
| `VIDEO/_retired_python_video/app/blueprints/media_hook.py` | Hook path: kafka enqueue vs sync `process_dvr_event` (L38–45, L96–103) |
| `VIDEO/_retired_python_video/services/{frame_extractor,pusher,sorter,stream_forward,post_process,media_janitor}_*` | Worker inventory for §3.1 disposition |

## Java changes (key)

| Component | Change |
|-----------|--------|
| `DvrUploadKafkaConsumerRunner` | New `SmartLifecycle` daemon thread: `KafkaConsumer` poll, `processDvrEvent`, retry/backoff, DLQ via `DvrUploadService.publishDlq`, manual offset commit |
| `VideoProperties.Media` | `dvrConsumerGroup`, `dvrMaxRetries`, `dvrPollTimeoutMs` |
| `application.yaml` | `video.media.upload-mode: sync` + DVR consumer defaults documented |
| `FULL_REPLACEMENT_GAP.md` | §3.1 services disposition table; §2.7/§8/§9 honesty refresh |
| `progress.md` | FR-B15 row |

## GAP deltas

- §3.1 **新增** `VIDEO/services/*` 七项处置表（迁入 Java / 保留外部 / FR 覆盖）
- §2.7 media_hook：DVR Kafka consumer → **FR-B15 ✅**
- §8：DVR Kafka consumer 行；去除笼统「大量行为桩」表述
- §9：距完整替换改为 prod 联调 + snap consumer + 契约回归

## certify --phase 0

```
exit 0
```

Log: `logs/fr-b15-phase0.log`（oracle `:6000` 未运行 — stale golden warnings; all cases ok/exempt）

## Remaining

- Prod `upload-mode=kafka` + broker 端到端（consumer group lag、DLQ topic 可观测）
- `media.snap.completed` Kafka consumer（对称于 DVR）
- 全量 HTTP 契约回归（259 路由）
- 生产回滚/切流演练

## Concerns

- Broker down + `upload-mode=kafka`: consumer logs error + 5s reconnect（非静默）；未 commit 的 offset 由 Kafka 重投
- `hybrid` 模式：hook 同步处理 + consumer 异步处理（与 Python 一致；`processDvrEvent` 幂等靠 RecordFile 去重）
- DLQ publish 失败时仅 error 日志（对齐 Python `publish_dvr_dlq` except 路径）
- Default `sync`：consumer 不启动，mini/local 无需 broker
