# FR-B32 Report — MinIO 超配额 cleanup 真删除 E2E + 6 非 JSON GET content-type 探针

**STATUS:** DONE (local `:48096` / `:9000`) — **禁止 COMPLETE**

**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Python-first（read before coding）

| Python | 行为 |
|--------|------|
| `storage_service.py` `check_and_cleanup_storage` L150-205 | 超阈值 → `cleanup_old_files(device_id/)`；返回 `snap_cleaned` / `*_deleted_count` |
| `storage_service.py` `cleanup_old_files` L89-147 | `list_objects` + `stat_object` → 按 `last_modified` 删最老 → `remove_object` |
| `alert.py` `get_alert_image` L133-206 | `image/jpeg` 或 MinIO `stat.content_type`；4xx JSON |
| `alert.py` `get_alert_record` L209-242 | `video/mp4` 等；Range/conditional |
| `patrol.py` `session_events` L88-118 | `text/event-stream` SSE |
| `playback.py` `get_playback_thumbnail` L232-251 | JSON 信封（thumbnail_path 元数据） |
| `record.py` `get_video` L292-307 | `send_file` + `content_type` |
| `snap.py` `get_space_image` L946-961 | `Response` + `content_type` |

## Cleanup E2E（`:9000` local）

| Step | Result |
|------|--------|
| Seed `frb32_device` 500B 配额 + 5×100B 对象 | OK |
| `POST /video/snap/device/frb32_device/storage/cleanup` | `snap_cleaned=true` `snap_deleted_count=2` |
| MinIO before/after | **5 → 3** objects（真 `remove_object`） |

**Artifacts:** `logs/fr-b32-cleanup-e2e-latest.{json,md}`

**Tool:** `python tools/video_java/fr_b32_cleanup_e2e.py`（or `fr_b32_e2e.py` orchestrator）

## 6 非 JSON GET content-type 探针

分类：**content-type pass**（非 keys-matrix envelope）

| id | HTTP | Content-Type | Python cite |
|----|------|--------------|-------------|
| alert_image | 200 | image/jpeg | alert.py L133-206 |
| alert_record | 200 | video/mp4 | alert.py L209-242 |
| patrol_session_events | 200 | text/event-stream | patrol.py L88-118 |
| playback_thumbnail | 200 | application/json | playback.py L232-251 |
| record_video_file | 200 | video/mp4 | record.py L292-307 |
| snap_image_file | 200 | image/jpeg | snap.py L946-961 |

**Artifacts:** `logs/fr-b32-binary-get-latest.{json,md}`

**Tool:** `python tools/video_java/fr_b32_binary_get.py`

## Java fix（B32 范围）

| 组件 | 变更 |
|------|------|
| `MediaPathSupport.pathWithinHandlerMapping` | Boot 2.7 `/**` 全路径回退时提取 `/image/`、`/video/` 后缀（对齐 Python `<path:object_name>`） |

## GAP / HANDOFF / checklist

- `FULL_REPLACEMENT_GAP.md` §9 更新为 **FR-B32** 当前判定
- `HANDOFF.md` §8–§9 更新至 FR-B32
- `PROD_SOAK_CHECKLIST.md` §0.4 phase0 + §2.5 cleanup local 证据
- `field_contract.py` 注释 6 路由 content-type 探针分类
- `progress.md` FR-B32 行

## phase0

```
python tools/video_java/certify.py --phase 0
→ PASS 5/5 (logs/certify-frb32-phase0.log)
```

## Remaining (honest)

1. **prod soak** — checklist 大部仍 ⬜（local ≠ prod）
2. **POST field-key matrix** backlog
3. **prod cleanup threshold** — 超配额真删除 prod 取证
4. **COMPLETE forbidden**

## Concerns

- `snap_image` / `record_file` GET 依赖 DB `url` 本地路径（与 Python mini 一致）；MinIO-only 对象需 sync 或 DB 行
- Windows `wmic`/`taskkill` 杀 Java 偶发 Unicode 解码警告（不影响 E2E 结果）
- `playback/thumbnail` 为 JSON 元数据路由（非二进制），归入 6 路由 content-type 探针而非 envelope 键矩阵
