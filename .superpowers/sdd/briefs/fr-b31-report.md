# FR-B31 Report — POST/PUT mutating-matrix + storage cleanup MinIO 对齐

**STATUS:** DONE (local `:48096`) — **禁止 COMPLETE**

**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Python-first（read before coding）

| Python | 响应/行为 |
|--------|-----------|
| `algorithm_task.py` create_task L144-148 | 成功 `{'code':0,'msg':...,'data': task.to_dict()}` |
| `snap.py` cleanup_device_storage L889-893 | 成功 `{'code':0,'msg':'存储清理完成','data': result}` |
| `playback.py` create_playback | 成功 `{'code':0,'msg':...,'data': playback.to_dict()}` |
| `storage_service.py` `check_and_cleanup_storage` L150-205 | 阈值检查 + `cleanup_old_files` MinIO `device_id/` 前缀删除；返回 `snap_cleaned`/`video_cleaned`/`*_deleted_count`/`*_freed_size` |
| `storage_service.py` `cleanup_old_files` L89-147 | `list_objects` + `stat_object` → 按 `last_modified` 排序 → `remove_object` |

## Mutating-matrix counts

| 指标 | 值 |
|------|-----|
| Inventoried routes | 265 |
| Routes pass | **265** / 0 fail |
| POST inventoried | 112 |
| PUT inventoried | 28 |
| Mutating probed (POST+PUT) | 140 |
| Skipped destructive | 3 (`/storage/cleanup`, `/images/cleanup`, `/videos/cleanup`) |
| Skipped multipart | 1 (`/import-template`) |
| Skipped non-mutating (GET/DELETE/…) | 125 |
| Asserts | pass=272 fail=0 skip=129 |

**Artifacts:** `logs/fr-b31-mutating-matrix-latest.{json,md}`

**Tool:** `python tools/video_java/field_contract.py --mutating-matrix`

## Storage cleanup result

| Step | Result |
|------|--------|
| `POST /video/snap/device/vj_p2_device/storage/cleanup` | HTTP 200 code=0 |
| data keys | `snap_cleaned`, `video_cleaned`, `snap_deleted_count`, `snap_freed_size`, `video_deleted_count`, `video_freed_size`, `message` |
| MinIO disabled | 诚实 no-op（`message: MinIO 未启用，跳过存储清理`） |

**Java changes:**

| 组件 | 变更 |
|------|------|
| `VideoMinioService.cleanupOldFiles` | 对齐 Python `cleanup_old_files` |
| `SnapStorageService.cleanup` | 对齐 Python `check_and_cleanup_storage`（替换原 save_time 元数据路径） |
| `DeviceStorageRepository` | `touchLastSnapCleanupTime` / `touchLastVideoCleanupTime` |

**Artifacts:** `logs/fr-b31-storage-cleanup-latest.{json,md}`

## phase0

```
python tools/video_java/certify.py --phase 0
→ PASS 5/5 (logs/certify-frb31-phase0.log)
```

## Remaining (honest)

1. **prod soak** — `PROD_SOAK_CHECKLIST.md` 大部仍 ⬜
2. **6 GET envelope-only** 路由 keys 映射
3. **POST field-key matrix** — mutating-matrix 仅信封层，非 data 键断言
4. **cleanup threshold E2E** — MinIO enabled + 超阈值真删除未 local/prod 取证
5. **COMPLETE forbidden**

## Concerns

- `cleanup()` 响应在 MinIO disabled 时多 `message` 键（Python 无 config 时才有 message）；核心 6 键已对齐
- Oracle `:6000` 未运行 → phase0 stale golden warnings（Java 侧 5/5 pass）
- 空间级 `images/cleanup`（save_time 过期）与设备级 `storage/cleanup`（配额阈值）为不同 Python 路径；B31 对齐后者
