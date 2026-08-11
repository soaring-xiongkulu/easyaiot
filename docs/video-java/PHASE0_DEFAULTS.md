# Phase 0 — Commercial defaults (shortcut-off)

> 阶段 0：规矩与商业默认已切换；完整替换进行中；Python 仍为对照，禁止删除。  
> 日常启动：`bootstrap.yaml` → `spring.profiles.active=local`（**非 mini**）。

## Defaults changed

| Key | Old | New | Notes |
|-----|-----|-----|-------|
| `video.alert.use-direct-persist` | `true` | **`false`** | Kafka first; fallback code may exist, not default success |
| `video.matching.use-direct-process` | `true` | **`false`** | |
| `video.post-process.use-stub-enqueue` | `true` | **`false`** | real iot-sink enqueue |
| `video.media.upload-mode` | `sync` | **`kafka`** | Python non-mini / cluster |
| `video.minio.enabled` | `false` | **`true`** | local MinIO formal path; env `MINIO_ENABLED=false` to disable |

Applied in: `VideoProperties.java` field defaults, `application.yaml`, `application-local.yaml`.

## Shortcut profile (certify only)

`--spring.profiles.active=mini` (or `local,mini` if needed):

| Key | mini value |
|-----|------------|
| `use-direct-persist` | `true` |
| `use-direct-process` | `true` |
| `use-stub-enqueue` | `true` |
| `upload-mode` | `sync` |
| `minio.enabled` | `false` |

Example certify:  
`java -jar …/iot-video-biz.jar --spring.profiles.active=mini`

## Daily candidate

```
java -jar DEVICE/iot-video/iot-video-biz/target/iot-video-biz.jar --spring.profiles.active=local
```

Must **not** default to direct/stub/sync/MinIO-off.

## Forbidden (from Phase 0)

- FR-B46+ / keys-matrix / field-matrix / POST 样本刷绿  
- COMPLETE / 删除 main 上 Python VIDEO  
- 本阶段不起全套中间件联调（阶段 1）
