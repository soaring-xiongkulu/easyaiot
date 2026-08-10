# PHASE 3 Gate — cutover, rollback, retire

**Status:** PASS (P3-S3)
**Updated:** 2026-08-10

Phase 3 completes when gateway default traffic is on Java, rollback is drilled, Python VIDEO is retired, and certify/docs are terminal PASS.

## Checklist

| # | Item | P3-S3 | Owner |
|---|------|-------|-------|
| 1 | Phase 2 gate PASS (all `vj_p2_*`) | ✅ prerequisite | — |
| 2 | Gateway `video-admin-api` → `lb://video-server` | ✅ **done (CLOSE-S2)** — renamed from `video-server-java` | — |
| 3 | `CUTOVER.md` runbook (precheck, steps, observe, auth) | ✅ **done (P3-S1)** | — |
| 4 | Gateway smoke with production token + `tenant-id` | ✅ **done (CLOSE-S3)** — [GATEWAY_AUTH_SMOKE.md](./GATEWAY_AUTH_SMOKE.md); mini gateway `:48080` → `:48096`; `EX-GATEWAY-AUTH-LOCAL` | — |
| 5 | Observe 15–30 min (heartbeat, hook, tasks) post-cutover | ✅ **done (CLOSE-S3)** — [OBSERVE_LOG.md](./OBSERVE_LOG.md) 16m38s, 22/22 OK | — |
| 6 | Rollback drill: gateway → `lb://video-server`, document in `ROLLBACK_LOG.md` | ✅ **done (P3-S2)** | — |
| 7 | Java `spring.application.name` → `video-server` + Python deregister | ✅ **done (CLOSE-S2)** — Python archived (P3-S3); Java renamed to `video-server` | — |
| 8 | Python `VIDEO/` retire wave (safe_fsops dry-run → execute) | ✅ **done (P3-S3)** | — |
| 9 | `CERTIFY_STATUS.md` Phase 3 PASS | ✅ **done (P3-S3)** | — |

## Python VIDEO archive (P3-S3)

Serving surface moved to `VIDEO/_retired_python_video/` via `safe_fsops.py` (dry-run → execute):

| Source | Archive destination |
|--------|-------------------|
| `VIDEO/app/` | `VIDEO/_retired_python_video/app/` |
| `VIDEO/run.py` | `VIDEO/_retired_python_video/run.py` |
| `VIDEO/models.py` | `VIDEO/_retired_python_video/models.py` |
| `VIDEO/services/` | `VIDEO/_retired_python_video/services/` |
| `VIDEO/start_prod.sh` | `VIDEO/_retired_python_video/start_prod.sh` |
| `VIDEO/docker-entrypoint.sh` | `VIDEO/_retired_python_video/docker-entrypoint.sh` |

**Retained under `VIDEO/`:** models (`*.onnx`, `*.pt`), docker-compose, requirements, install scripts, test media, docs, data. **Not touched:** `DEVICE/iot-video`, `docs/video-java`, `tools/video_java`.

**Future oracle:** external `F:/acme/VIDEO` (tag `video-java-oracle-baseline`) or archived copy; certify `--no-record` uses frozen golden.

## Commands (regression — unaffected by gateway / archive)

```text
python tools/video_java/certify.py --phase 0 --no-record --no-java
python tools/video_java/certify.py --phase 1 --no-record --no-java
python tools/video_java/certify.py --phase 2 --no-record
```

**P3-S3 certify (2026-08-10):** all three exit **0**.

## Gateway auth smoke (CLOSE-S3)

**Status:** ✅ **done** — see [GATEWAY_AUTH_SMOKE.md](./GATEWAY_AUTH_SMOKE.md).

**Local mini profile (`iot-gateway` `--spring.profiles.active=mini`):**

```text
# Routing (no Bearer) — proves gateway → video-server
curl -s -w "\nHTTP:%{http_code}\n" -H "tenant-id: 1" \
  "http://127.0.0.1:48080/admin-api/video/camera/list?pageNo=1&pageSize=1"
# → HTTP 200, code=0, camera list

# Auth filter (Bearer + tenant-id) — TokenAuthenticationFilter → system-server :48099
curl -s -w "\nHTTP:%{http_code}\n" \
  -H "Authorization: Bearer TOKEN" -H "tenant-id: 1" \
  "http://127.0.0.1:48080/admin-api/video/camera/list?pageNo=1&pageSize=1"
# → HTTP 500 locally (system-server not running); prod with live OAuth → expect 200 or 401
```

**Exemption:** `EX-GATEWAY-AUTH-LOCAL` (signed) — full OAuth success requires live `system-server`.

## Observe (CLOSE-S3)

**Status:** ✅ **done** — [OBSERVE_LOG.md](./OBSERVE_LOG.md): **16m 38s**, 22 polls @ 45s, **OK=22 FAIL=0**, verdict **PASS**.

## Rollback drill (P3-S2)

Recorded in `gates/ROLLBACK_LOG.md`. Config revert `lb://video-server` → archived Python → restore **40 ms** locally; production gateway uri **`lb://video-server`** (Java).

## Gate PASS criteria

- Code-path checklist rows ✅ (items 1–9)
- Rollback drill recorded with elapsed time
- Python VIDEO serving surface archived per safe_fsops discipline
- Gateway on `lb://video-server` (Java production name)
