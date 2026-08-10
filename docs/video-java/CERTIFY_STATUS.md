# VIDEO Java — CERTIFY_STATUS

| Phase | Status | Updated | Notes |
|-------|--------|---------|-------|
| Phase -1 | PASS | 2026-08-10 | shell + doctor |
| Phase 0 | PASS | 2026-08-10 | vj_p0_health=PASS, vj_p0_task_start_stop=PASS, vj_p0_heartbeat=PASS, vj_p0_alert_hook=PASS, vj_p0_restart=PASS; exemptions: vj_p0_health/api: EX-ORACLE-HEALTH-DB |
| Phase 1 | PASS | 2026-08-10 | vj_p1_camera_list=PASS, vj_p1_camera_get=PASS, vj_p1_view_forward_start_stop=PASS, vj_p1_stream_forward_start_stop=PASS |
| Phase 2 | PASS | 2026-08-10 | vj_p2_face_publish_process=PASS, vj_p2_plate_publish_process=PASS, vj_p2_post_process_enqueue=PASS, vj_p2_snap_list_or_create=PASS, vj_p2_record_query=PASS, vj_p2_playback_url=PASS, vj_p2_patrol_task_list=PASS, vj_p2_media_hook=PASS, vj_p2_detection_region_get=PASS |
| Phase 3 | PASS | 2026-08-10 | P3-S3: Python VIDEO hot path archived to `VIDEO/_retired_python_video/`; gateway `lb://video-server` (CLOSE-S2 rename); rollback drill done (P3-S2); ops residual: gateway token smoke + 15–30min observe |

P0 direct: oracle `:6000` / candidate `:48096`. Gateway default `/admin-api/video/**` → `lb://video-server`.
