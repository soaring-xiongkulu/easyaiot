# Report — P1-S3: Camera view-forward (ffmpeg) start/stop/status

## STATUS
**DONE** — `vj_p1_view_forward_start_stop` certify `ok=True` (media + lifecycle). Phase 0 remains green (`certify --phase 0` exit 0). Phase 1 gate still FAIL overall (stream-forward out of scope).

## Commits
- (this commit) `feat(video-java): P1-S3 view-forward ffmpeg start/stop/status`

## Phase 1 per-case results
| case_id | ok | layers |
|---------|----|--------|
| vj_p1_camera_list | **PASS** | api:pass |
| vj_p1_camera_get | **PASS** | api:pass |
| vj_p1_view_forward_start_stop | **PASS** | media:pass, lifecycle:pass |
| vj_p1_stream_forward_start_stop | FAIL | lifecycle:fail, media:fail (404 — P1-S4) |

## Phase 0
`certify --phase 0 --no-record --no-java` exit **0**.

## What changed
- **Java**: `ViewForwardSupervisor` (ProcessBuilder + `cmd.exe /c` for `.cmd` ffmpeg), `ViewForwardService`, `FfmpegCompat`, `FfmpegPathBootstrap`; `CameraController` stream start/stop/status; `DeviceRepository.updateEnableForward`.
- **Config**: `video.ffmpeg-path` in `application-local.yaml`; fixture HTTP-FLV source + dedicated SRS RTMP publish name.
- **Certify**: `diff_layers` lifecycle degenerate check recognizes `after_stream_status`; `record_python` stops oracle before java sampling and waits 5s; sleep after start 5s.
- **Goldens**: Re-recorded python/java `vj_p1_view_forward_start_stop` with `stream_status=running`, `process_alive=true`.

## Testbed notes (EXEMPTIONS-adjacent)
- Fixture input: `http://127.0.0.1:8080/live/vj_p1_src.flv` (requires background loop publisher to SRS from `F:/acme/RUNTIME/testdata/sample.mp4`).
- Oracle ffmpeg needs `FFMPEG_PATH` (or `python run.py --env=acme` with env set); Java uses `video.ffmpeg-path`.
- Serial certify: stop oracle view-forward before java golden sampling (SRS holds RTMP publish slot ~5s).
- Re-run oracle golden may need a fresh `rtmp_stream` suffix if SRS stream name was left in a bad state.

## Concerns
- `vj_p1_certify5` RTMP name in fixture vs `certify4` in oracle golden recording — media/lifecycle diff ignores URL string (only `rtmp_url_present`).
- Background `vj_p1_src` publisher must be running before certify; not wired into `certify.py` yet.
- Oracle VIDEO service was restarted with `VIDEO_ENV=acme` + `FFMPEG_PATH` for golden recording; document for local certify.
