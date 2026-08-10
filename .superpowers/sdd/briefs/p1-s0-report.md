# P1-S0 Report — Fix P0 Important findings + restart case

**Worktree:** `F:/acme/.worktrees/video-java` @ `feat/video-java`  
**Date:** 2026-08-10  
**Gate:** Phase 0 certify **exit 0**

---

## STATUS

**DONE** — All P0-S6 Important items (I-1..I-5) addressed; Phase 0 restart gap closed with `vj_p0_restart`; certify PASS.

---

## Fixes

| ID | Fix |
|----|-----|
| I-1 | `@PreDestroy shutdownAll()` on `AlgorithmRuntimeSupervisor` — stops children, shuts down log pump |
| I-2 | Per-`task_id` lock (`ConcurrentHashMap` + `synchronized`) around start/stop/restart paths |
| I-3 | `AlgorithmTaskRepository.count()` + `listTasks` uses real `COUNT(*)`; list API exposes `total` |
| I-4 | `video.runtime.repo-root` / `ACME_ROOT` / `RUNTIME_ROOT`; removed hardcoded `F:/acme` fallback |
| I-5 | `management.health.db.enabled: false` in `application-local.yaml` — candidate health UP without DB probe |
| M-1 | `VideoPingController` phase `"0"` |
| Phase 0 gap | New case `vj_p0_restart` + `stub_runtime_exit.bat` proving auto-restart after unexpected exit |

---

## Certify

```text
python tools/video_java/certify.py --phase 0
exit 0
```

| case_id | ok |
|---------|-----|
| vj_p0_health | True (api exempt EX-ORACLE-HEALTH-DB) |
| vj_p0_task_start_stop | True |
| vj_p0_heartbeat | True |
| vj_p0_alert_hook | True |
| vj_p0_restart | True |

---

## Concerns

1. **Worktree RUNTIME shadowing:** If the worktree contains `RUNTIME/` and `ACME_ROOT` / `video.runtime.repo-root` is unset, ini paths resolve to the worktree instead of the main repo — ini parity with oracle fails. Certify/start should pass `--video.runtime.repo-root=F:/acme` or set `ACME_ROOT`.
2. **Restart timing:** `vj_p0_restart` uses fixed sleeps (3s + 8s) around 5s supervisor backoff; slow hosts may need threshold tuning in Phase 1.
3. **M-5 (restart budget):** Unbounded cached thread pool on crash loops — deferred to Phase 1.

---

## Commits

Single commit on `feat/video-java` (see `git log -1`).
