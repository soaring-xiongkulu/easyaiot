# FR-B30 Report — Snap/Record 存储用量真 MinIO 统计 + GAP/HANDOFF 收口

**Date:** 2026-08-11  
**Branch:** `feat/video-java` @ `F:/acme/.worktrees/video-java`  
**Status:** DONE (≠ COMPLETE)

## Python-first（read before Java fix）

| Python | 行为 |
|--------|------|
| `VIDEO/_retired_python_video/app/services/storage_service.py` `get_bucket_size` | MinIO `list_objects` + `stat_object` → `(bytes, count)`；失败返回 `(0,0)` |
| 同文件 `get_device_storage_info` | 仅当 `snap_storage_bucket` / `video_storage_bucket` 配置时查询；前缀 `{device_id}/`；计算 `*_usage_ratio` |
| `snap.py` `GET /device/<id>/storage` | `config.to_dict()` + `storage_info` 合并返回 |

**Java 对照（FR-B29 前）：** `SnapStorageService.getOrCreate` 硬编码 `snap_size=0` 等占位符。

## Java changes

| 组件 | 变更 |
|------|------|
| `VideoMinioService.getBucketUsage` | 新增 `BucketUsage` record；对齐 Python `get_bucket_size` |
| `SnapStorageService.enrichWithStorageStats` | `video.minio.enabled=true` 且 bucket 配置时真统计；否则诚实 0 |

## Local evidence (`:9000`)

| Step | Result |
|------|--------|
| MinIO disabled | `snap_size=0 snap_count=0 video_size=0 video_count=0` |
| MinIO enabled + 测试对象 | `snap_size=58 snap_count=1 video_size=58 video_count=1`（对齐 Python `get_bucket_size`） |

Artifacts: `logs/fr-b30-storage-stats-latest.{json,md}`

## GAP / HANDOFF cleanup

- `FULL_REPLACEMENT_GAP.md` §8：新增 FR-B30 存储统计行
- `FULL_REPLACEMENT_GAP.md` §9：移除重复 FR-B28/B29 判定块；单一 **FR-B30** 当前判定；B28/B29 收入 `<details>` 历史归档
- `HANDOFF.md` §8–§9：更新至 FR-B30；下一步改为 prod soak + 6 envelope-only GET + POST keys-matrix backlog

## Phase 0

```
python tools/video_java/certify.py --phase 0
→ PASS 5/5 (logs/certify-frb30-phase0.log)
```

## Remaining (honest)

1. **prod soak** — `PROD_SOAK_CHECKLIST.md` 大部仍 ⬜
2. **6 GET envelope-only** 路由 keys 映射
3. **POST keys-matrix** backlog
4. **`check_and_cleanup_storage` MinIO 真清理** — Java `cleanup()` 仍走 DB 元数据路径（非本包范围）
5. **COMPLETE forbidden**

## Concerns

- E2E 需可靠杀掉全部 `iot-video-biz.jar` 进程后再切换 `minio.enabled`（Windows wmic 字段顺序）
- `listObjects` 对大 bucket 可能慢（与 Python 相同语义）；prod 可考虑缓存或 DB 汇总（未做）
