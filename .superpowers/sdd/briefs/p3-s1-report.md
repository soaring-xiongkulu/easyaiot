# P3-S1 Report — Gateway cutover to Java + runbooks

**Date:** 2026-08-10  
**Worktree:** `F:/acme/.worktrees/video-java`  
**Branch:** `feat/video-java`  
**Brief:** `.superpowers/sdd/briefs/p3-s1-brief.md`

## STATUS

**DONE** — Gateway `video-admin-api` points to `lb://video-server-java`; cutover runbook + partial Phase 3 gate landed; Phase 0/1/2 certify exit 0. Python VIDEO retained; Java service name unchanged.

## Commits

1. `feat(video-java): P3-S1 gateway cutover to video-server-java + runbooks` (this stage)

## Gateway URI

```yaml
# DEVICE/iot-gateway/.../application.yaml — video-admin-api
uri: lb://video-server-java
```

## Certify exits

| Phase | Exit | Notes |
|-------|------|-------|
| 0 | 0 | all `vj_p0_*` PASS |
| 1 | 0 | all `vj_p1_*` PASS |
| 2 | 0 | all `vj_p2_*` PASS |

```text
python tools/video_java/certify.py --phase 0 --no-record --no-java  # exit 0
python tools/video_java/certify.py --phase 1 --no-record --no-java  # exit 0
python tools/video_java/certify.py --phase 2 --no-record            # exit 0
```

## Deliverables

| Item | Path |
|------|------|
| Gateway URI cutover | `DEVICE/iot-gateway/src/main/resources/application.yaml` |
| Cutover runbook | `docs/video-java/CUTOVER.md` |
| Phase 3 gate (partial) | `docs/video-java/gates/PHASE_3_GATE.md` |
| Rollback log scaffold | `docs/video-java/gates/ROLLBACK_LOG.md` |
| Dual-run update | `docs/video-java/DUAL_RUN.md` |
| Certify status | `docs/video-java/CERTIFY_STATUS.md` — Phase 3 IN PROGRESS |

## Constraints honored

- Java `spring.application.name` remains `video-server-java` (no Nacos name steal).
- `VIDEO/` not deleted.
- Auth/token/`tenant-id` documented in `CUTOVER.md` for gateway path.

## Concerns

1. **Gateway restart required** — URI change is config-only until iot-gateway reloads; ops must restart or Nacos push per deploy model.
2. **Dual ownership** — cutover without stopping Python `auto_start` risks dual task/ffmpeg ownership; runbook stresses `VIDEO_SKIP_BACKGROUND_TASKS` / oracle auto_start off.
3. **Gateway smoke not automated** — Phase 3 gate item 4 (token + `tenant-id` via gateway) remains manual until P3-S2+.
4. **Rollback drill pending** — `ROLLBACK_LOG.md` empty; full Phase 3 PASS blocked until drill + retire stages.
