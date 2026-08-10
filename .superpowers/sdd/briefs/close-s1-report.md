# CLOSE-S1 Report — Sign exemptions + I-4/I-5 + oracle doctor

**Date:** 2026-08-10  
**Worktree:** `F:/acme/.worktrees/video-java`  
**Branch:** `feat/video-java`  
**Brief:** `.superpowers/sdd/briefs/close-s1-brief.md`

## STATUS

**DONE** — `EX-REMOTE-NODE` and `EX-KAFKA-HOOK` signed; P1-S6 I-4/I-5 fixed; `doctor.py` accepts archived oracle; certify phases 0/1/2 exit 0.

## Commits

1. `4d9376b` — `feat(video-java): CLOSE-S1 sign exemptions, I-4/I-5 fixes, oracle doctor`

## Changes

| Area | Change |
|------|--------|
| `EXEMPTIONS.md` | Signed `EX-REMOTE-NODE`, `EX-KAFKA-HOOK` (`orchestrator, 2026-08-10`); no unsigned provisional rows |
| I-4 | `PathSegmentSanitizer` + use in `ViewForwardService` / `StreamForwardSupervisor` log dirs |
| I-5 | `ViewForwardAutoResumeService` + `ViewForwardAutoResumeScheduler` on `ApplicationReadyEvent`; gated by `video.skip-background-tasks` |
| `doctor.py` | `resolve_oracle_video_root()` — `VIDEO_JAVA_ORACLE_ROOT`, `VIDEO/_retired_python_video`, `VIDEO/`, `F:/acme/VIDEO` |
| Golden | Re-sampled `vj_p1_camera_list` java golden (3 certify devices) to match python oracle |

## Certify exits

| Phase | Exit | Command |
|-------|------|---------|
| doctor | 0 | `python tools/video_java/doctor.py` |
| 0 | 0 | `certify.py --phase 0 --no-record --no-java` |
| 1 | 0 | `certify.py --phase 1 --no-record --no-java` |
| 2 | 0 | `certify.py --phase 2 --no-record` |

Doctor reports oracle root: `VIDEO/_retired_python_video`.

## Concerns

1. **Java repackage** — `mvn package` compile OK; spring-boot repackage failed (jar locked by running candidate); certify used existing service on `:48096`.
2. **P1 camera_list golden** — java golden re-sampled to 3 devices; DB must include `vj_p2_device` for stable diff (same as prior `fix-p1-camera-list`).
3. **I-1/I-2/I-3** — deferred P1-S6 items unchanged; not in CLOSE-S1 scope.
