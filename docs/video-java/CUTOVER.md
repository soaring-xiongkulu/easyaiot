# VIDEO Java — Gateway cutover runbook

> **CLOSE-S2 (2026-08-10):** Production name `video-server`; gateway `lb://video-server`. Original P3-S1 used `video-server-java` during dual-run.

## Preconditions

1. **Phase 2 gate PASS** — all `vj_p2_*` cases green (`python tools/video_java/certify.py --phase 2` exit 0).
2. **Java candidate healthy** — `video-server` registered in Nacos (or local profile reachable at `:48096`); `/actuator/health` UP.
3. **Python rollback source available** — serving surface archived under `VIDEO/_retired_python_video/` (P3-S3) or external oracle `F:/acme/VIDEO` (tag `video-java-oracle-baseline`). Java owns Nacos name `video-server`; Python is **not** running during normal cutover.
4. **Background tasks** — stop Python `auto_start` / set `VIDEO_SKIP_BACKGROUND_TASKS=1` on oracle before cutover so enabled tasks are not dual-owned. Java should own `schedule_policy=local` enabled tasks.
5. **DB** — shared `iot-video20`; certify uses isolated `task_id` fixtures; production cutover must not run parallel auto_start on both stacks for the same task.

## Auth / token (mandatory for gateway path)

- Traffic through `iot-gateway` must use the **same** auth as other admin APIs: client sends `Authorization` token and `tenant-id` header (or gateway-injected tenant context) exactly as for Python `video-server`.
- P0 certify hits **direct** bases (`:6000` / `:48096`) and may bypass gateway auth; **cutover validation must include at least one gateway-proxied call** with production token headers.
- Do not ship a state where Python enforced tenant/token checks but Java behind the same route is unauthenticated.

## Cutover steps

1. **Announce** maintenance window (optional for dev; required for prod).
2. **Precheck** — `python tools/video_java/doctor.py`; Phase 0/1/2 certify exit 0 on candidate.
3. **Stop Python background ownership** — `VIDEO_SKIP_BACKGROUND_TASKS=1` or disable oracle auto_start for enabled local tasks.
4. **Deploy / restart Java** — ensure `video-server` is UP and registered (`spring.application.name` is **`video-server`**).
5. **Gateway URI change** — in `DEVICE/iot-gateway/src/main/resources/application.yaml`:

   ```yaml
   - id: video-admin-api
     uri: lb://video-server
     predicates:
       - Path=/admin-api/video/**
   ```

6. **Restart or refresh gateway** — reload route config (Nacos config push or gateway restart per your deploy model).
7. **Smoke via gateway** — e.g. `GET /admin-api/video/video/camera/list` with valid token + `tenant-id`; compare HTTP `code` and key fields to pre-cutover baseline.
8. **Observe 15–30 minutes** — see checklist below.

## Observe checklist (15–30 min)

| Signal | Action |
|--------|--------|
| Gateway route | `video-admin-api` resolves to `video-server` (Java) instances only |
| Error rate | No spike in 5xx on `/admin-api/video/**` |
| Heartbeat | `POST /video/algorithm/heartbeat/realtime` (or patrol) updating DB on schedule |
| Alert hook | Test hook or monitor alert insert/Kafka path; no duplicate rows from Python side |
| Algorithm tasks | Enabled local tasks RUNNING under Java supervisor; no orphan Python ffmpeg/RUNTIME |
| Sink / post-process | Face/plate/post-process enqueue still reaching iot-sink or stub path as configured |
| Logs | Java `iot-video-biz` no repeated restart loops; gateway no `503` from missing Nacos name |

## Rollback (fast path)

See [PLAN.md §3.3](./PLAN.md) and `gates/ROLLBACK_LOG.md`.

**Naming reality (CLOSE-S2 + P3-S3):** Gateway `video-admin-api` is **`lb://video-server`** (Java). Python serving surface is archived; rollback **does not** flip gateway URI — it swaps which process owns the Nacos name `video-server`.

| Step | Action |
|------|--------|
| 1 | **Stop Java** — scale `video-server` (Java, `:48096`) to 0; confirm Nacos deregister |
| 2 | **Restore Python serving surface** — choose one: |
| | **A (in-repo):** copy/move from `VIDEO/_retired_python_video/` back to `VIDEO/` (`app/`, `run.py`, `models.py`, `services/`, `start_prod.sh`, `docker-entrypoint.sh`) |
| | **B (external):** use `F:/acme/VIDEO` oracle checkout (tag `video-java-oracle-baseline`) |
| 3 | **Start Python** — `python VIDEO/run.py` (or external path) on `:6000`; register Nacos as `video-server` |
| 4 | **Gateway** — keep `uri: lb://video-server` (unchanged); Nacos now resolves to Python `:6000` |
| 5 | **Background tasks** — unset `VIDEO_SKIP_BACKGROUND_TASKS`; run `auto_start_all_tasks` if required |
| 6 | **Smoke** — gateway `GET /admin-api/video/camera/list` + token/`tenant-id`; expect Python responses |
| 7 | **Record** — incident in `gates/ROLLBACK_LOG.md` with timestamps and symptom |

**Restore to Java (post-incident):** stop Python → re-archive serving surface if needed → start Java `video-server` on `:48096` → gateway unchanged.

## What this stage does **not** do

- Java production name is `video-server` (CLOSE-S2).
- Does **not** delete or archive `VIDEO/`.
- Does **not** complete Phase 3 gate — rollback drill and Python retire are later stages (P3-S2+).

## References

- [DUAL_RUN.md](./DUAL_RUN.md) — service names and ports
- [PLAN.md §3.2–3.3](./PLAN.md) — cutover / rollback policy
- [HANDOFF.md §9.1](./HANDOFF.md) — hard constraints
- Optional probe route: [gateway-optional-route.yaml](./gateway-optional-route.yaml)
