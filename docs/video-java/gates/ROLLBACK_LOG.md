# VIDEO Java — rollback log

Record each production or staged rollback after gateway cutover to Java.

| Date | Trigger | Steps | Duration | Outcome | Author |
|------|---------|-------|----------|---------|--------|
| 2026-08-10 | P3-S2 staged rollback drill (no prod incident) | 1) `video-admin-api` uri `lb://video-server-java` → `lb://video-server` in `DEVICE/iot-gateway/.../application.yaml`; 2) verify YAML; 3) restore uri → `lb://video-server-java`; 4) verify restore | **<1 min** (40 ms config edit; gateway restart not run locally) | restored to Java URI | P3-S2 agent |

### P3-S2 drill detail

**Environment:** `F:/acme/.worktrees/video-java`, branch `feat/video-java`. No live `iot-gateway` on `:48080` — drill exercised config revert/restore only.

**Rollback steps (prod adds gateway restart + Java scale-down):**

1. Edit `DEVICE/iot-gateway/src/main/resources/application.yaml` — `video-admin-api` `uri: lb://video-server`.
2. Restart or Nacos-push gateway route config.
3. (Prod) Stop or scale `video-server-java` to 0; clear `VIDEO_SKIP_BACKGROUND_TASKS` on Python oracle; `auto_start_all_tasks` if needed.
4. Smoke via gateway with token + `tenant-id` — expect Python `video-server` responses.

**Restore steps (this drill):**

1. Revert `uri` to `lb://video-server-java`.
2. Restart gateway (prod).
3. Re-enable Java instances; keep Python `auto_start` off until Java owns enabled local tasks.

**Measured:** YAML rollback + restore elapsed **40 ms** (2026-08-10). Prod rollback budget: config + gateway reload typically **2–5 min** depending on deploy model.

Template row:

```text
YYYY-MM-DD | symptom (e.g. hook 5xx spike) | gateway→video-server, stop Java, Python auto_start | N min | restored | name
```
