# Report — EVID-S5: Fix Phase 3 rollback narrative after rename

**Date:** 2026-08-10  
**Branch:** `feat/video-java`  
**Status:** ✅ DONE

## Problem

After CLOSE-S2 (`video-server-java` → `video-server`), rollback docs still described a gateway URI flip and mixed pre/post-rename naming. OBSERVE_LOG only polled health/camera.

## Changes

| File | Change |
|------|--------|
| `docs/video-java/CUTOVER.md` | Rewrote rollback fast path: stop Java → restore Python archive → start `:6000` as `video-server`; gateway `lb://video-server` unchanged |
| `docs/video-java/gates/ROLLBACK_LOG.md` | Post-CLOSE-S2 naming table; EVID-S5 runbook; P3-S2 drill marked historical |
| `docs/video-java/gates/PHASE_3_GATE.md` | Rollback + observe sections aligned with new narrative |
| `docs/video-java/gates/OBSERVE_EVID-S5.md` | **New** — heartbeat + alert-hook probe evidence |
| `docs/video-java/gates/OBSERVE_LOG.md` | Cross-ref to EVID-S5 appendix |
| `docs/video-java/DUAL_RUN.md` | One-line rollback pointer fix |

## Rollback summary (current)

1. Gateway stays `lb://video-server` — no URI change.
2. Stop Java `video-server` (`:48096`).
3. Restore Python from `VIDEO/_retired_python_video/` **or** external `F:/acme/VIDEO`.
4. Start Python on `:6000`, register Nacos as `video-server`.
5. Smoke via gateway; record in `ROLLBACK_LOG.md`.

## Observe probe results

| Probe | Route | Result |
|-------|-------|--------|
| Heartbeat | Direct `:48096` | ✅ HTTP 200, `code=0`, task_id=35 |
| Heartbeat | Gateway `:48080` | ✅ HTTP 200, `code=0`, task_id=35 |
| Alert hook | Direct `:48096` | ✅ HTTP 200, `code=0` (`status=skipped`, fixture events off) |

## Concerns

- No live end-to-end rollback drill post-rename (doc-only narrative fix; P3-S2 drill predates CLOSE-S2).
- Alert-hook probe returns `skipped` because certify fixture has `alert_event` disabled — endpoint path is healthy but no DB row inserted.
- Full Python archive restore untested in this stage; prod should rehearse `_retired_python_video` → `VIDEO/` copy before relying on it.

## Commit

`fix(docs): EVID-S5 Phase 3 rollback narrative + observe probes`
