# Brief — FR-B18: 收口 FR-B17 六条契约探针失败（Python-first）

## HARD RULE — NO NESTED SUBAGENTS
Do ALL work yourself. No Task/subagent tools.

## Python-first (mandatory before Java)
For each failing route, read the Python blueprint handler first, then Java controller/service:

1. `GET/PATCH /video/patrol/session/{id}` (+ stats) — Python `app/blueprints/patrol*.py` / session service
2. `POST /video/playback` — Python playback blueprint
3. `GET /video/record/space/{id}/video/{file}` — Python record file serve
4. `GET /video/snap/space/{id}/image/{file}` — Python snap image serve

Also read `logs/fr-b17-contract-latest.json` for exact failing method+path.

## Goal
1. Fix Java so these routes are **mapped and do not 404/500** on thin probes (missing id → 4xx is OK; auth 401 OK; empty file → 404 OK if Python does that — but Spring must own the path).
2. Re-run expanded `contract_regression.py` against `:48096`; target **fail=0** for inventory probes (or document only if Python itself 404s the same shape — then fix inventory path template instead).
3. Fix B16 SMOKE_ENDPOINTS `device-detection/regions` path shape if still wrong.
4. Update GAP + progress; phase0 0; commit + `fr-b18-report.md`.

## Constraints
- Worktree: `F:/acme/.worktrees/video-java`
- Toolchain as prior briefs
- Do **not** announce COMPLETE

## Done when
- Six fails closed or honest EX with Python parity cite; re-probe artifact; phase0 0; commit; report
