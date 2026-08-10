# VIDEO Java — CERTIFY_STATUS

| Phase | Status | Updated | Notes |
|-------|--------|---------|-------|
| Phase -1 | PASS | 2026-08-10 | shell + doctor |
| Phase 0 | PASS | 2026-08-10 | vj_p0_* cases green |
| Phase 1 | PASS | 2026-08-10 | vj_p1_* cases green |
| Phase 2 | PASS | 2026-08-10 | vj_p2_face_publish_process=PASS, vj_p2_plate_publish_process=PASS, vj_p2_post_process_enqueue=PASS, vj_p2_snap_list_or_create=PASS, vj_p2_record_query=PASS, vj_p2_playback_url=PASS, vj_p2_patrol_task_list=PASS, vj_p2_media_hook=PASS, vj_p2_detection_region_get=PASS |
| Phase 3 | PASS | 2026-08-10 | P3-S3: Python VIDEO hot path archived to `VIDEO/_retired_python_video/`; gateway `lb://video-server-java`; rollback drill done (P3-S2); future parity via archived oracle or Java-only smoke |

P0 direct: oracle `:6000` / candidate `:48096`. Gateway default `/admin-api/video/**` → `lb://video-server-java`. Oracle recording: external `F:/acme/VIDEO` or in-repo `VIDEO/_retired_python_video/`; certify `--no-record` uses frozen golden.
