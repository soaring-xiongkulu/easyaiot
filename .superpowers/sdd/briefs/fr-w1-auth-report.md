# FR-W1-AUTH Report

**STATUS:** DONE  
**Branch:** `feat/video-java`  
**Date:** 2026-08-10

## Goal

Prove gateway `/admin-api/video/**` + `system-server` OAuth token check end-to-end (cutover hard gate).

## Environment

| Service | Port | How started |
|---------|------|-------------|
| `video-server` | 48096 | existing local jar |
| `system-server` | 48099 | `iot-module-system-biz:latest` docker (`local,mini`; PG `:15432`, Redis `:16379`) |
| `iot-gateway` | 48080 | `iot-gateway.jar --spring.profiles.active=mini` |

## Smoke evidence (short)

| Case | HTTP | Body / behavior |
|------|------|-----------------|
| No Bearer + `tenant-id: 1` → `/admin-api/video/camera/list` | **200** | `code=0`, `total=7` from video-server (filter passthrough) |
| Invalid Bearer | **401** | `{"code":401,"msg":"账号未登录"}` after real `:48099` OAuth check |
| Valid Bearer (admin login) | **200** | `code=0`, camera list from video-server |
| `GET /rpc-api/system/oauth2/token/check` | **200** | `userId=1`, `tenantId=1` |

Token example (run 2026-08-10): `fef03f51511245e48e11b6bda2feeb95` via `POST /admin-api/system/auth/login` (`admin` / `admin123`, tenant 1).

Evidence: `docs/video-java/gates/GATEWAY_AUTH_SMOKE.md`  
Script: `tools/video_java/gateway_auth_smoke.ps1`

## EXEMPTIONS

`EX-GATEWAY-AUTH-LOCAL` → **resolved by FR-W1-AUTH**

## GAP

§4 鉴权行 + §7 P0 gateway auth → ✅

## phase0

`python tools/video_java/certify.py --phase 0` → **exit 0**

## Concerns

- No Bearer still returns 200 at gateway (by `TokenAuthenticationFilter` design); invalid Bearer is the enforced reject path.
- `system-server` started via docker image + `host.docker.internal` DB/Redis; jar-from-source not rebuilt in this worktree.
- Production `lb://video-server` + live Nacos/system cluster still needs ops cutover drill (out of FR-W1-AUTH scope).
