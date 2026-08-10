# Report — P1-S4: Stream-forward local start/stop parity

## STATUS
**DONE** — `vj_p1_stream_forward_start_stop` certify `ok=True` (lifecycle + media). All 4 Phase 1 cases PASS. Phase 0 exit 0.

## Commits
- (this commit) `feat(video-java): P1-S4 stream-forward local start/stop/status`

## Phase 1 per-case results
| case_id | ok | layers |
|---------|----|--------|
| vj_p1_camera_list | **PASS** | api:pass |
| vj_p1_camera_get | **PASS** | api:pass |
| vj_p1_view_forward_start_stop | **PASS** | media:pass, lifecycle:pass |
| vj_p1_stream_forward_start_stop | **PASS** | lifecycle:pass, media:pass |

## Phase 0
`certify --phase 0 --no-record --no-java` exit **0**.

## What changed
- **Java**: `StreamForwardController` (`GET/POST start|stop/status`), `StreamForwardService`, `StreamForwardSupervisor` (ProcessBuilder ffmpeg per device, supervisor-alive parity with Python daemon), `StreamForwardTaskRepository` + `StreamForwardTaskRow`; `ViewForwardService.buildForwardCommand()` for shared ffmpeg argv.
- **Certify**: `record_python` stops oracle stream-forward before java sampling (serial SRS slot); 120s start timeout for oracle deploy.
- **Goldens**: Re-recorded python/java `vj_p1_stream_forward_start_stop`.

## Concerns
- Java `isAlive` treats active supervisor worker as `running` (matches Python `StreamForwardDaemon` process probe, not per-ffmpeg PID).
- Oracle stream-forward start can exceed 30s when cold-deploying `run_deploy.py`; certify uses 120s timeout.
- Serial certify: stop oracle task before java golden sampling (same RTMP publish name as view-forward fixture).
- Background HTTP-FLV source (`vj_p1_src`) still required for ffmpeg input; not wired into `certify.py`.
