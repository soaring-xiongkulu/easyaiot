# FR-B16 Report — Snap Kafka upload consumer + 契约回归脚手架

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Implemented JVM-embedded Kafka consumer for `media.snap.completed` calling existing `SnapUploadService.processSnapEvent` with Python snap-worker retry/DLQ parity. Consumer gated by `video.media.snap-upload-mode` (explicit `kafka`/`sync`) or inherited `upload-mode` (`kafka`/`hybrid`); default `sync` needs no broker. Added `tools/video_java/contract_regression.py` — 14-prefix route inventory + optional thin HTTP smoke; artifacts under `logs/`.

**COMPLETE 未宣称** — prod broker 联调、全量 HTTP 契约执行、行为桩仍 open。

## Python files read (oracle)

| Path | Purpose |
|------|---------|
| `VIDEO/_retired_python_video/services/media_upload_worker/run_snap_worker.py` | Kafka consume `media.snap.completed` (L19–20); group `upload-worker-snap`; manual commit; retry `_retry`≤8 → `publish_snap_dlq` (L60–68); poll loop + broker-down sleep 5s (L70–72) |
| `VIDEO/_retired_python_video/app/services/snap_upload_service.py` | `process_snap_event` (L63–148): file stable wait, SnapSpace lookup, MinIO upload, metadata upsert, DLQ on MinIO failure (L124) |
| `VIDEO/_retired_python_video/app/services/media_kafka_service.py` | `is_snap_kafka_mode` (L30–36); `TOPIC_SNAP_COMPLETED` / `TOPIC_SNAP_DLQ` (L15–16); `publish_snap_event` / `publish_snap_dlq` (L139–160) |

## Java changes (key)

| Component | Change |
|-----------|--------|
| `SnapUploadKafkaConsumerRunner` | New `SmartLifecycle` daemon: `KafkaConsumer` poll, `processSnapEvent`, retry/backoff (max 8, cap 20s), DLQ via `SnapUploadService.publishDlq`, manual offset commit; mirrors `DvrUploadKafkaConsumerRunner` |
| `VideoProperties.Media` | `snapConsumerGroup`, `snapMaxRetries`, `snapPollTimeoutMs` |
| `application.yaml` | snap topic/consumer defaults documented |
| `contract_regression.py` | 14-prefix inventory + optional `--smoke`; camera/audio-talk double-count artifact adjusted per GAP §8 |
| `FULL_REPLACEMENT_GAP.md` | §3.1 snap worker row; §2.7/§5/§8/§9 refresh |
| `progress.md` | FR-B16 row |

## GAP deltas

- §3.1 **新增** snap `media_upload_worker` 行 → **FR-B16 ✅** `SnapUploadKafkaConsumerRunner`
- §2.7 media_hook：snap Kafka consumer → **FR-B16 ✅**
- §5 证据门禁：契约回归脚手架 `contract_regression.py`（绿 inventory ≠ COMPLETE）
- §8：snap Kafka consumer 行；去除「snap consumer 仍缺」
- §9：距完整替换去除 snap consumer；保留全量契约执行 + prod 联调

## certify --phase 0

```
exit 0
```

Log: `logs/fr-b16-phase0.log`（Java :48096 未运行 — run_java warnings; all cases ok/exempt）

## Contract regression

```
python tools/video_java/contract_regression.py
exit 0
```

Artifact: `logs/fr-b16-contract-regression-latest.json` — 14 prefixes, total_diff=0 (camera +5 talk artifact normalized)

## Remaining

- Prod `snap-upload-mode=kafka` + broker 端到端（consumer lag、DLQ 可观测）
- 全量 HTTP 契约回归 **执行**（259 路由字段级，非仅 inventory）
- MinIO/真机/WVP/iot-node prod 联调
- 生产回滚/切流演练

## Concerns

- Broker down + snap kafka mode: consumer logs + 5s reconnect（非静默）；未 commit offset 由 Kafka 重投
- Snap 无 hybrid 路径（hook 要么 kafka enqueue 要么 sync process）；与 Python 一致
- DLQ publish 失败仅 error 日志（对齐 Python `publish_snap_dlq` except）
- `contract_regression.py` inventory 绿 ≠ COMPLETE（脚本内 disclaimer + GAP 诚实表述）
- Default `sync`：consumer 不启动，mini/local 无需 broker
