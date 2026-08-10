# CLOSE-S3 Report — Gateway auth smoke + observe evidence

**Date:** 2026-08-10  
**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## STATUS

**PASS** — PHASE_3_GATE items 4–5 marked done with recorded evidence.

## Commits

`d164338` — `feat(video-java): CLOSE-S3 gateway auth smoke and 16m observe evidence`

## Auth smoke

| Test | Result |
|------|--------|
| Gateway health `:48080/actuator/health` | 200 UP |
| `GET /admin-api/video/camera/list` (tenant-id, no Bearer) | **200** — routing to `video-server:48096` proven |
| Same + `Authorization: Bearer …` | **500** — `TokenAuthenticationFilter` calls `system-server:48099` OAuth check (refused locally) |

Evidence: `docs/video-java/gates/GATEWAY_AUTH_SMOKE.md`  
Exemption: `EX-GATEWAY-AUTH-LOCAL` (signed in `gates/EXEMPTIONS.md`)

## Observe

| Metric | Value |
|--------|-------|
| Duration | **16m 38s** (wall-clock) |
| Interval | 45s |
| Polls | 22 OK / 0 FAIL |
| Verdict | **PASS** |

Evidence: `docs/video-java/gates/OBSERVE_LOG.md`  
Script: `tools/video_java/gateway_observe.ps1`

## Certify exits

| Phase | Exit |
|-------|------|
| 0 (`--no-record --no-java`) | **0** |
| 1 (`--no-record --no-java`) | **0** |
| 2 (`--no-record`) | **0** |

## Changes

- `DEVICE/iot-gateway/.../application-mini.yaml` — static `video-admin-api` → `http://127.0.0.1:48096`, Nacos off
- `DEVICE/iot-gateway/.../bootstrap-mini.yaml` — Nacos discovery/config disabled
- `tools/video_java/gateway_observe.ps1` — observe loop helper
- Gate docs: `PHASE_3_GATE.md`, `GATEWAY_AUTH_SMOKE.md`, `OBSERVE_LOG.md`, `EXEMPTIONS.md`, `CERTIFY_STATUS.md`

## Concerns

- Full OAuth **200** with Bearer token requires live `system-server` on `:48099`; local smoke uses signed `EX-GATEWAY-AUTH-LOCAL`.
- Production `application.yaml` unchanged (`lb://video-server`); mini overrides are profile-only.
- Gateway process started ad-hoc for smoke (`--spring.profiles.active=mini`); not part of commit runtime.
