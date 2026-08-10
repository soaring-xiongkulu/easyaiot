# Brief — FR-B25: DVR/Snap 真文件 → MinIO+DB 成功链（Python-first）

## HARD RULE — NO NESTED SUBAGENTS
Do ALL work yourself. No Task/subagent tools.

## Python-first
Read before coding:
1. `dvr_upload_service.py` / `snap_upload_service.py` — success path requirements (file stable, device resolve, MinIO put, metadata)
2. `media_kafka_service.py` + workers
3. Java `DvrUploadService` / `SnapUploadService` / `VideoMinioService`

## Goal
Close FR-B24 remaining “真文件 → MinIO + 可播放 record_path” for **local soak**:

1. Create synthetic device `frb25_*` + real temp media files (small jpg/mp4 under a known path).
2. With MinIO enabled + Kafka consumers (hosts/`Kafka` as FR-B24), publish/process events so `processDvrEvent` / `processSnapEvent` return success; verify object in MinIO + DB row; capture playable path shape.
3. Evidence: `logs/fr-b25-minio-upload-e2e.*`
4. Update `PROD_SOAK_CHECKLIST` 2.4 (and related) as **local-only ✅** with log cites — not prod.
5. Restore mini-safe defaults; phase0 0; GAP/progress; commit; `fr-b25-report.md`.
6. Still **forbid COMPLETE**.

## Constraints
- Worktree: `F:/acme/.worktrees/video-java`
- Toolchain as prior
- Prefer hook or Kafka path that matches Python
- Do not claim COMPLETE

## Done when
- Success-path evidence for at least one DVR and one snap upload (or honest EX if MinIO auth/bucket blocks after attempts); checklist updated; phase0 0; commit; report
