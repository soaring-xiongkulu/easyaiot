# P3-S3 Report — Python VIDEO archive retirement + Phase 3 PASS

**Date:** 2026-08-10  
**Worktree:** `F:/acme/.worktrees/video-java`  
**Branch:** `feat/video-java`  
**Brief:** `.superpowers/sdd/briefs/p3-s3-brief.md`

## STATUS

**DONE** — Python VIDEO serving surface archived to `VIDEO/_retired_python_video/` via safe_fsops (6 moves); `PHASE_3_GATE` PASS; `CERTIFY_STATUS` Phase 3 PASS; HANDOFF updated; gateway remains `lb://video-server-java`.

## Commits

1. `feat(video-java): P3-S3 archive Python VIDEO hot path + Phase 3 PASS` (this stage)

## safe_fsops summary

**Allowlist extended** in `tools/runtime_parity/safe_fsops.py` for `VIDEO/app`, `run.py`, `models.py`, `services`, entry scripts.

**Executed moves** (dry-run → `--execute` per action):

| # | src | dst | manifest (last) |
|---|-----|-----|-----------------|
| 1 | `VIDEO/app` | `VIDEO/_retired_python_video/app` | `logs/safe_fsops_dryrun_20260810_1335*.json` |
| 2 | `VIDEO/run.py` | `VIDEO/_retired_python_video/run.py` | same batch |
| 3 | `VIDEO/models.py` | `VIDEO/_retired_python_video/models.py` | same batch |
| 4 | `VIDEO/services` | `VIDEO/_retired_python_video/services` | same batch |
| 5 | `VIDEO/start_prod.sh` | `VIDEO/_retired_python_video/start_prod.sh` | same batch |
| 6 | `VIDEO/docker-entrypoint.sh` | `VIDEO/_retired_python_video/docker-entrypoint.sh` | same batch |

**Not touched:** `DEVICE/iot-video`, `docs/video-java`, `tools/video_java`, `DEVICE/iot-video` tree, models (`*.onnx`, `*.pt`), docker-compose under `VIDEO/`.

## Phase 3 status

| Item | Status |
|------|--------|
| `PHASE_3_GATE.md` | **PASS** |
| `CERTIFY_STATUS.md` Phase 3 | **PASS** |
| Gateway URI | `lb://video-server-java` |

## Certify exits (P3-S3)

| Phase | Exit | Command |
|-------|------|---------|
| 0 | 0 | `certify.py --phase 0 --no-record --no-java` |
| 1 | 0 | `certify.py --phase 1 --no-record --no-java` |
| 2 | 0 | `certify.py --phase 2 --no-record` |

## Deliverables

| Item | Path |
|------|------|
| Archive README | `VIDEO/_retired_python_video/README.md` |
| safe_fsops allowlist | `tools/runtime_parity/safe_fsops.py` |
| Phase 3 gate | `docs/video-java/gates/PHASE_3_GATE.md` |
| Certify status | `docs/video-java/CERTIFY_STATUS.md` |
| HANDOFF completion | `docs/video-java/HANDOFF.md` |
| Dual-run update | `docs/video-java/DUAL_RUN.md` |

## Concerns

1. **Ops smoke pending** — `PHASE_3_GATE` items 4–5 remain ops-owned (provisional since P3-S2); dev worktree has no gateway on `:48080`.
2. **Java service name** — `video-server-java` retained; rename to `video-server` deferred per HANDOFF §9.1.
3. **Future oracle** — in-repo hot path archived; new golden recording needs external `F:/acme/VIDEO` or archived copy under `_retired_python_video/`.
4. **doctor mvn** — `doctor.py` fails when `mvn` not on PATH (pre-existing env); certify phases 0–2 still exit 0.
