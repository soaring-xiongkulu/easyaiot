# VIDEO Java — CERTIFY_STATUS

| Phase | Status | Updated | Notes |
|-------|--------|---------|-------|
| Phase -1 | PASS | 2026-08-10 | shell + doctor |
| Phase 0 | PASS | 2026-08-10 | vj_p0_* cases green |
| Phase 1 | PASS | 2026-08-10 | vj_p1_* cases green |
| Phase 2 | PASS | 2026-08-10 | vj_p2_* cases green |
| Phase 3 | PASS | 2026-08-10 | P3-S3: Python VIDEO hot path archived to `VIDEO/_retired_python_video/`; gateway `lb://video-server-java`; rollback drill done (P3-S2); ops residual: gateway token smoke + 15–30min observe |

P0 direct: oracle `:6000` / candidate `:48096`. Gateway default `/admin-api/video/**` → `lb://video-server-java`.
