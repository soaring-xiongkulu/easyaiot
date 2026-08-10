# PHASE 1 Gate — camera / ffmpeg / stream-forward

**Status:** PASS
**Updated:** 2026-08-10 08:23 UTC

Gate PASS when every P1 case `ok` — each layer `pass` or signed `exempt`.
Media layer checks: stream status, ffmpeg process alive, codec summary (normalized).

## Commands

```text
python tools/video_java/seed_p1_fixture.py
python tools/video_java/certify.py --phase 1
```

## Case table

| case_id | layers | needs_ffmpeg | needs_runtime | notes |
|---------|--------|--------------|---------------|-------|
| vj_p1_camera_list | api | no | no | GET /video/camera/list |
| vj_p1_camera_get | api | no | no | GET /video/camera/device/{id} |
| vj_p1_view_forward_start_stop | media, lifecycle | yes | no | view-forward ffmpeg start/stop/status |
| vj_p1_stream_forward_start_stop | lifecycle, media | yes | yes | stream-forward task start/stop/status |

## Case results

| case_id | ok | layers |
|---------|----|--------|
| vj_p1_camera_list | True | api:pass |
| vj_p1_camera_get | True | api:pass |
| vj_p1_view_forward_start_stop | True | media:pass, lifecycle:pass |
| vj_p1_stream_forward_start_stop | True | lifecycle:pass, media:pass |

## Documented exemptions (this run)

- (none)
