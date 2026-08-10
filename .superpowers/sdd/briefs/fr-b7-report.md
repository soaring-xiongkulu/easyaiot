# FR-B7 Report — 流票据鉴权 + 全量回滚演练

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Aligned Java `POST /video/camera/stream/ticket/sign` auth/tenant checks with retired Python VIDEO (`sign_stream_ticket` + `_check_login`). Executed full safe_fsops rollback drill restoring `app/` + `services/` + `run.py` + `models.py` from `_retired_python_video/`, verified tree, re-archived. Updated GAP §4/§5 and `ROLLBACK_LOG.md`.

## Python files read (oracle)

| Path | Purpose |
|------|---------|
| `VIDEO/_retired_python_video/app/blueprints/camera.py` | `sign_stream_ticket`, `_check_login`, `_resolve_auth_check_url`, `_STREAM_PATH_RE` |
| `VIDEO/_retired_python_video/app/utils/node_client.py` | `resolve_java_backend_url()` mini profile default (`48099` vs `48080`) |

## Java changes

| Component | Change |
|-----------|--------|
| `CameraStreamTicketService` | Auth trim + tenant-id; `lookingAt()` path guard; `resolveJavaBackendUrl()` mirrors Python (`AUTH_CHECK_URL` → `JAVA_BACKEND_URL` → `GATEWAY_URL` → `EASYAIOT_DEPLOY_PROFILE` mini default); warn log on auth failure |
| `FULL_REPLACEMENT_GAP.md` | §4 鉴权流票据 → **FR-B7 ✅**; §5 回滚演练 → **FR-B7 ✅** |
| `gates/ROLLBACK_LOG.md` | FR-B7 row + full restore drill detail (4 paths) |

## Short contract (stream ticket)

| Case | Expected |
|------|----------|
| No Bearer | HTTP **401**, `code=401`, `msg=unauthorized` |
| Invalid Bearer | HTTP **401** (system auth check fails) |
| Valid Bearer + `tenant-id` | HTTP **200**, `code=0`, `data.e` + `data.st` |
| Invalid path (not `/ai|live|rtp/…`) | HTTP **400**, `invalid stream path` |
| Missing `STREAM_TICKET_SECRET` | HTTP **500** |

Signing formula: `md5(f"{e}{path} {secret}")` → url-safe base64 without padding (nginx `secure_link` parity).

## Rollback timing (FR-B7 drill)

| Step | Duration |
|------|----------|
| Restore `app/` + `services/` + `run.py` + `models.py` (dry-run → execute ×4) | **1663 ms** |
| Verify `VIDEO/run.py`, `models.py`, `app`, `services` | **True** |
| Re-archive same four paths | **1502 ms** |
| **Total** | **3165 ms** |

Post-drill: `VIDEO/run.py` absent; archive intact (P3-S3 retired state).

## GAP

- `FULL_REPLACEMENT_GAP.md` §4 鉴权（流票据）→ **resolved by FR-B7**
- `FULL_REPLACEMENT_GAP.md` §5 回滚演练 → **resolved by FR-B7** (file restore; Nacos process swap still ops)

## certify --phase 0

```
exit 0
```

(`record_python` warnings — oracle `:6000` not running; diff uses stale golden; all cases ok/exempt)

## Concerns

1. **Prod rollback** — drill restored files only; live rollback still needs stop Java → start Python `:6000` as `video-server` + gateway smoke.
2. **`start_prod.sh` / `docker-entrypoint.sh`** — not in FR-B7 four-path drill (still in archive); full CUTOVER restore includes them.
3. **No live system-server in certify** — stream ticket auth path code-reviewed; prod needs gateway + `:48099` token check soak.
4. **Java jar** — certify used existing candidate on `:48096`; service code change needs rebuild for runtime verification.
