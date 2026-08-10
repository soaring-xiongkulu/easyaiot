# Report — P2-S0: Fix Phase 1 Important quality findings

## STATUS
**DONE** — P1-S6 Important I-1..I-3 addressed. Phase 0 + Phase 1 certify exit **0**.

## Commits
- (this commit) `fix(video-java): P2-S0 supervisor shutdown, bounded pools, non-RTSP ffmpeg timeout`

## Certify exits
| Phase | Command | Exit |
|-------|---------|------|
| 0 | `python tools/video_java/certify.py --phase 0 --no-record` | **0** |
| 1 | `python tools/video_java/certify.py --phase 1 --no-record` | **0** |

All P0/P1 cases `ok=True` (P0 health: signed exempt `EX-ORACLE-HEALTH-DB`).

## What changed

### I-1 — Non-RTSP ffmpeg timeout parity
- `FfmpegCompat.ffmpegNonRtspTimeoutArgs(ioUs)` mirrors Python `camera.py` FFmpegDaemon (lines 303–306).
- `ViewForwardService.buildFfmpegCommand` applies timeout args for HTTP/HTTPS/gb28181/file inputs when not RTSP.

### I-2 — Graceful supervisor shutdown await
- `ViewForwardSupervisor` and `StreamForwardSupervisor` `@PreDestroy` now call `SupervisorExecutors.shutdownAndAwait` (10s) after stopping children — aligned with `AlgorithmRuntimeSupervisor`.

### I-3 — Bounded watcher thread pools
- New `SupervisorExecutors` helper: fixed daemon pool capped at `VIDEO_SUPERVISOR_MAX_WORKERS` (default 64).
- Replaced `newCachedThreadPool` in all three supervisors (`ViewForward`, `StreamForward`, `AlgorithmRuntime`).

## Deferred (out of scope)
- **I-4** log path `deviceId` sanitization — Phase 2 / ops hardening.
- **I-5** view-forward auto-resume on boot — Phase 2 `ApplicationReadyEvent` or document in `DUAL_RUN.md`.

## Concerns
- Bounded pool (64) may queue daemon starts under very large multi-device stream-forward tasks; tune via `VIDEO_SUPERVISOR_MAX_WORKERS` if needed.
- Non-RTSP timeout args depend on ffmpeg build supporting `-rw_timeout` or `-timeout` (same as Python).
