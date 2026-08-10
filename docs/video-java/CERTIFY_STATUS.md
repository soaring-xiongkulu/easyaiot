# VIDEO Java — CERTIFY_STATUS

| Phase | Status | Updated | Notes |
|-------|--------|---------|-------|
| Phase -1 | PASS | 2026-08-10 | shell + doctor |
| Phase 0 | PASS | 2026-08-10 | vj_p0_health=PASS, vj_p0_task_start_stop=PASS, vj_p0_heartbeat=PASS, vj_p0_alert_hook=PASS, vj_p0_restart=PASS; exemptions: vj_p0_health/api: EX-ORACLE-HEALTH-DB |
| Phase 1 | PASS (archive) | 2026-08-10 | 窄切片；≠ camera 域完成 |
| Phase 2 | PASS (archive) | 2026-08-10 | 最少端点刷绿；≠ 帧后平台完成 |
| Phase 3 | PASS (archive) | 2026-08-10 | 切名/归档/观察；≠ 完整替换 |

P0 direct: oracle `:6000` / candidate `:48096`. Gateway default `/admin-api/video/**` → `lb://video-server`.
