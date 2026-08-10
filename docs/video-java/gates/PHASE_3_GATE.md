# PHASE 3 Gate — cutover, rollback, retire

**Status:** IN PROGRESS (P3-S2 partial)
**Updated:** 2026-08-10

Phase 3 completes when gateway default traffic is on Java, rollback is drilled, Python VIDEO is retired, and certify/docs are terminal PASS. **P3-S2 lands rollback drill + provisional gateway auth smoke** — retire wave remains P3-S3+.

## Checklist

| # | Item | P3-S2 | Owner |
|---|------|-------|-------|
| 1 | Phase 2 gate PASS (all `vj_p2_*`) | ✅ prerequisite | — |
| 2 | Gateway `video-admin-api` → `lb://video-server-java` | ✅ **done (P3-S1)** | — |
| 3 | `CUTOVER.md` runbook (precheck, steps, observe, auth) | ✅ **done (P3-S1)** | — |
| 4 | Gateway smoke with production token + `tenant-id` | ⚠️ **provisional (P3-S2)** | ops |
| 5 | Observe 15–30 min (heartbeat, hook, tasks) post-cutover | ⬜ partial | ops |
| 6 | Rollback drill: gateway → `lb://video-server`, document in `ROLLBACK_LOG.md` | ✅ **done (P3-S2)** | — |
| 7 | Java `spring.application.name` → `video-server` (if needed) + Python deregister | ⬜ P3-S3+ | — |
| 8 | Python `VIDEO/` retire wave (safe_fsops dry-run → execute) | ⬜ P3-S3+ | — |
| 9 | `CERTIFY_STATUS.md` Phase 3 PASS | ⬜ pending | — |

## Commands (regression — unaffected by gateway)

Certify continues to use **direct** oracle/candidate ports; gateway change does not alter Phase 0/1/2 scripts.

```text
python tools/video_java/certify.py --phase 0 --no-record --no-java
python tools/video_java/certify.py --phase 1 --no-record --no-java
python tools/video_java/certify.py --phase 2
```

**P3-S2 certify (2026-08-10):** all three exit **0**.

## Gateway auth smoke (P3-S2 evidence)

**Status:** ⚠️ provisional — no local gateway or production token in dev worktree.

**Attempted (local):**

```text
curl -s -w "%{http_code}" --connect-timeout 3 \
  -H "Authorization: Bearer TOKEN" \
  -H "tenant-id: TENANT" \
  "http://127.0.0.1:48080/admin-api/video/video/camera/list?pageNo=1&pageSize=10"
```

**Result:** connection failed (`000`, curl exit 28). `iot-gateway` not listening on `:48080` in this worktree. Port probe: `:8080` HTTP 200 (other service), `:48080` unreachable.

**Run in prod / staging (required to clear item 4):**

```text
# Replace GATEWAY_HOST, TOKEN, TENANT after gateway cutover to video-server-java
curl -s -H "Authorization: Bearer TOKEN" -H "tenant-id: TENANT" \
  "http://GATEWAY_HOST/admin-api/video/video/camera/list?pageNo=1&pageSize=10"
```

Expect `{ "code": 0, ... }` envelope matching pre-cutover Python behavior. Repeat for one mutating path if policy requires (e.g. patrol list read-only is sufficient for smoke).

## Gateway verification (manual)

```text
# After gateway restart — replace TOKEN and TENANT
curl -s -H "Authorization: Bearer TOKEN" -H "tenant-id: TENANT" \
  "http://<gateway>/admin-api/video/video/camera/list?pageNo=1&pageSize=10"
```

Expect `{ "code": 0, ... }` envelope matching pre-cutover Python behavior.

## Rollback drill (P3-S2)

Recorded in `gates/ROLLBACK_LOG.md`. Config revert `lb://video-server-java` → `lb://video-server` → restore **40 ms** locally; final gateway uri **`lb://video-server-java`**.

## Gate PASS criteria (full Phase 3 — not yet)

- All checklist rows ✅
- Rollback drill recorded with elapsed time
- Python VIDEO deregistered / retired per runbook
- No open provisional exemptions blocking video-java gates
