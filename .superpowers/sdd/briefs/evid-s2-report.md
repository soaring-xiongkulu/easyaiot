# EVID-S2 Report — Enforce media thresholds + view-forward process ALIVE

## STATUS
**DONE** — `thresholds.json` media rules enforced in `diff_layers`; `vj_p1_view_forward_start_stop` goldens show `ffmpeg_process_alive=true` on **both** sides; certify `--phase 0` exit **0**, `--phase 1` exit **0** (view-forward media+lifecycle pass).

## Commit
`fix(video-java): EVID-S2 media thresholds + view-forward alive`

## Root cause
1. `media.ffmpeg_process_alive_required` in thresholds was never checked — bilateral `stopped/stopped` falsely passed.
2. View-forward sampling raced SRS RTMP slot: prior publish on `vj_p1_certify5` blocked ffmpeg output → process exited → `stream_status=stopped`.

## Fixes
1. **`diff_layers.py`** — absolute media/lifecycle checks: `ffmpeg_process_alive=true` and `stream_status=running` (and lifecycle `process_alive` / `after_stream_status` for view-forward).
2. **`vj_common.py`** — `ensure_p1_src_feeder()`, `prepare_p1_view_forward()` (stop oracle+candidate, 6s SRS release), `wait_until_view_forward_running()`.
3. **`record_python.py`** — view-forward uses feeder prep + wait-until-running instead of fixed 5s sleep.
4. **`seed_p1_fixture.py`** — ensures HTTP-FLV source after DB seed.
5. **`ViewForwardService.java`** — `waitUntilAlive(15s)` after supervisor start.
6. Re-recorded python/java `vj_p1_view_forward_start_stop` media + lifecycle goldens.

## Verify
```text
python tools/video_java/seed_p1_fixture.py
python tools/video_java/record_python.py vj_p1_view_forward_start_stop
python tools/video_java/run_java.py vj_p1_view_forward_start_stop
python tools/video_java/certify.py --phase 0
python tools/video_java/certify.py --phase 1
```

| case_id | media alive (py / java) | certify phase |
|---------|-------------------------|---------------|
| **vj_p1_view_forward_start_stop** | **true / true** | **P1 pass** |

**media snapshot (both sides):** `stream_status=running`, `ffmpeg_process_alive=true`, `service_status=running`.

## Concerns
- SRS RTMP publish slot must be free — `prepare_p1_view_forward` stops both stacks; 6s wait required after contested `vj_p1_certify5` name.
- Java `waitUntilAlive` needs candidate restart after deploy (mvn repackage failed while jar locked by running process).
- Full certify still warns on oracle `vj_p0_restart` / `vj_p1_stream_forward` record timeouts (pre-existing); diff uses stale python goldens for those cases.
- `ensure_p1_src_feeder` spawns background ffmpeg when HTTP-FLV down; not auto-started from `certify.py` (wired via seed + record helpers).
