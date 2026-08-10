# Report — P1-S1: Phase 1 certify scaffolding

**Status:** DONE  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Summary

Added Phase 1 manifest cases, `vj_p1` fixture/seed, media-layer diff tooling, and `--phase 1` certify runner. Java candidate honestly fails on missing camera/stream-forward endpoints; Phase 0 remains green.

## Deliverables

| Item | Path |
|------|------|
| Manifest P1 cases (4) | `testdata/video-java/manifest.json` |
| P1 fixture + seed | `testdata/video-java/fixtures/vj_p1.json`, `tools/video_java/seed_p1_fixture.py` |
| Media layer | `tools/video_java/vj_common.py`, `diff_layers.py` (`media.json`) |
| Record/run P1 | `record_python.py`, `run_java.py` |
| Certify phase 1 | `tools/video_java/certify.py` |
| Gate scaffold | `docs/video-java/gates/PHASE_1_GATE.md` |
| Status | `docs/video-java/CERTIFY_STATUS.md` |

## Cases

| case_id | layers | result |
|---------|--------|--------|
| `vj_p1_camera_list` | api | FAIL — Java 404 |
| `vj_p1_camera_get` | api | FAIL — Java 404 |
| `vj_p1_view_forward_start_stop` | media, lifecycle | FAIL — Java 404 |
| `vj_p1_stream_forward_start_stop` | lifecycle, media | FAIL — Java 404 |

## Verify

```text
python tools/video_java/seed_p1_fixture.py
python tools/video_java/certify.py --phase 0 --no-record --no-java   # exit 0
python tools/video_java/certify.py --phase 1 --no-record             # exit 1 (honest FAIL)
```

Recorded oracle golden for all four P1 cases; Java golden written with `status: fail` and 404 reason.

## Concerns

- Oracle `vj_p1_camera_list` search by `device_id` returned empty list (search matches name/model, not id); `camera_get` golden is authoritative for device row.
- View-forward oracle media snapshot recorded `stream_status: stopped` (ffmpeg may not have started in this env); P1-S2+ should re-record with ffmpeg running.
- `stream_forward_task_id=3` is environment-specific; re-run `seed_p1_fixture.py` on fresh DB.

## Next (P1-S2+)

Implement Java camera + stream-forward controllers and ffmpeg ProcessBuilder parity; re-run `certify.py --phase 1` until green.
