# Phase 2 A3 Report — ViewForward / stream-forward ffmpeg lifecycle (handoff for A4)

**Status:** PASS  
**Pack:** P2-A3  
**Date:** 2026-08-11  
**Commit:** `27e84e2` — `feat(video-java): phase2 A3 forward ffmpeg parity`  
**Evidence:** `logs/phase2-a3-forward.json`

## Prior packs

- A1 PASS (`2b3d483`) — alert Kafka; fixture device `frb26_device`, task 61
- A2 PASS (`e214456`) — algo RUNTIME lifecycle; same device; `file://` → plain path for Windows ffmpeg input
- Phase 1 stack PASS — profile `local`, PG 15432

## What was proven

On local full stack (`profile=local`):

1. **ViewForward** — `POST /admin-api/video/camera/device/frb26_device/stream/start` → real ffmpeg subprocess alive (supervisor PID 25320, child `ffmpeg-win-x86_64-v7.1` encoding `sample.mp4` → SRS `rtmp://127.0.0.1/live/frb26_device`)
2. `GET .../stream/status` → `status=running`, `enable_forward=true`, `pid` set
3. `POST .../stream/stop` → PID gone, `status=stopped`, `enable_forward=false`
4. **Stream-forward** — task 63 (`vj_p2_device`, same file source): `POST .../stream-forward/task/63/start` → `status=running`, ffmpeg log shows decode activity; `stop` → disabled

## Oracle vs Java

| Concern | Oracle (Python) | Java candidate |
|---------|-----------------|----------------|
| ViewForward API | `camera.py` → `/device/{id}/stream/start`, `/stop`, `/status` | `CameraController` → `ViewForwardService` |
| ffmpeg spawn | `camera.py` FFmpegDaemon → `subprocess.Popen(ffmpeg_cmd)` | `ViewForwardSupervisor` → `ProcessBuilder` + daemon worker |
| Stream-forward API | `stream_forward.py` → `/task/{id}/start`, `/stop`, `/status` | `StreamForwardController` → `StreamForwardService` |
| ffmpeg command | `camera.py` + `ffmpeg_compat.py` | `ViewForwardService.buildFfmpegCommand()` + `FfmpegCompat` |
| Auto-resume | `auto_start_streaming()` on boot | `ViewForwardAutoResumeScheduler` |

## Code changes (this pack)

1. **`FfmpegCompat.java`** — fix Windows file-input forward path:
   - `ffmpegSupportsRwTimeout()` uses `-h full` help text (lavfi probe falsely rejects `-rw_timeout`)
   - `ffmpegNonRtspTimeoutArgs()` no longer falls back to global `-timeout` (RTSP-demuxer-only on essentials build → immediate exit)
   - `buildProcess()` wraps `.cmd`/`.bat` binaries with `cmd.exe /c` for capability probes

## Root cause fixed

Before fix, ViewForward ffmpeg exited immediately with:

```
Option timeout not found.
Error opening input file F:/acme/RUNTIME/testdata/sample.mp4.
```

Cause: lavfi-based `rw_timeout` probe returned false → global `-timeout` added → invalid for file inputs on ffmpeg 7.1 essentials.

## Fixture state after evidence run

- `frb26_device`: `enable_forward=false` (stopped after run)
- Stream-forward task 63: `is_enabled=false` (stopped after run)

## Constraints for A4

- Do NOT flip shortcuts / mini / stub executor
- Do NOT claim COMPLETE / delete Python
- SRS on `127.0.0.1:1935` required for RTMP publish acceptance; preclean stale ffmpeg if `StreamBusy`
- `ffmpeg-path` in `application-local.yaml` points to host `ffmpeg.cmd` — supervisor PID may be `cmd.exe` wrapper
- Stack unchanged: PG 15432, Kafka 9092, Nacos 8848, MinIO 9000, GW 48080, video 48096 **local**

## Next pack

**P2-A4** — Media MinIO path (`logs/phase2-a4-media-minio.json`)
