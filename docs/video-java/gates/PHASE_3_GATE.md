# PHASE 3 Gate — cutover, rollback, retire

**Status:** IN PROGRESS (P3-S1 partial)
**Updated:** 2026-08-10

Phase 3 completes when gateway default traffic is on Java, rollback is drilled, Python VIDEO is retired, and certify/docs are terminal PASS. **P3-S1 only lands gateway URI cutover + runbooks** — items below marked partial until later stages.

## Checklist

| # | Item | P3-S1 | Owner |
|---|------|-------|-------|
| 1 | Phase 2 gate PASS (all `vj_p2_*`) | ✅ prerequisite | — |
| 2 | Gateway `video-admin-api` → `lb://video-server-java` | ✅ **done (P3-S1)** | — |
| 3 | `CUTOVER.md` runbook (precheck, steps, observe, auth) | ✅ **done (P3-S1)** | — |
| 4 | Gateway smoke with production token + `tenant-id` | ⬜ partial | ops |
| 5 | Observe 15–30 min (heartbeat, hook, tasks) post-cutover | ⬜ partial | ops |
| 6 | Rollback drill: gateway → `lb://video-server`, document in `ROLLBACK_LOG.md` | ⬜ P3-S2+ | — |
| 7 | Java `spring.application.name` → `video-server` (if needed) + Python deregister | ⬜ P3-S2+ | — |
| 8 | Python `VIDEO/` retire wave (safe_fsops dry-run → execute) | ⬜ P3-S3+ | — |
| 9 | `CERTIFY_STATUS.md` Phase 3 PASS | ⬜ pending | — |

## Commands (regression — unaffected by gateway)

Certify continues to use **direct** oracle/candidate ports; gateway change does not alter Phase 0/1/2 scripts.

```text
python tools/video_java/certify.py --phase 0 --no-record --no-java
python tools/video_java/certify.py --phase 1 --no-record --no-java
python tools/video_java/certify.py --phase 2
```

## Gateway verification (manual)

```text
# After gateway restart — replace TOKEN and TENANT
curl -s -H "Authorization: Bearer TOKEN" -H "tenant-id: TENANT" \
  "http://<gateway>/admin-api/video/video/camera/list?pageNo=1&pageSize=10"
```

Expect `{ "code": 0, ... }` envelope matching pre-cutover Python behavior.

## Gate PASS criteria (full Phase 3 — not yet)

- All checklist rows ✅
- Rollback drill recorded with elapsed time
- Python VIDEO deregistered / retired per runbook
- No open provisional exemptions blocking video-java gates
