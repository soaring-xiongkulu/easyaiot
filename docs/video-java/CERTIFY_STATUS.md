# VIDEO Java — CERTIFY_STATUS

| Phase | Status | Updated | Notes |
|-------|--------|---------|-------|
| Phase -1 | PASS | 2026-08-10 | shell + doctor |
| Phase 0 | PASS | 2026-08-10 | vj_p0_* cases green |
| Phase 1 | PASS | 2026-08-10 | vj_p1_* cases green |
| Phase 2 | PASS | 2026-08-10 | vj_p2_face_publish_process=PASS, vj_p2_plate_publish_process=PASS, vj_p2_post_process_enqueue=PASS, vj_p2_snap_list_or_create=PASS, vj_p2_record_query=PASS, vj_p2_playback_url=PASS, vj_p2_patrol_task_list=PASS, vj_p2_media_hook=PASS, vj_p2_detection_region_get=PASS |
| Phase 3 | IN PROGRESS | 2026-08-10 | P3-S1: gateway `video-admin-api` → `lb://video-server-java`; CUTOVER.md + PHASE_3_GATE partial; rollback drill + retire pending |

P0 direct: oracle `:6000` / candidate `:48096`. Gateway default `/admin-api/video/**` → `lb://video-server-java` (P3-S1); certify still uses direct ports.
