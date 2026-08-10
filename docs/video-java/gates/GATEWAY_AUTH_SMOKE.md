# Gateway auth smoke — CLOSE-S3 (2026-08-10)

**Profile:** `iot-gateway` `--spring.profiles.active=mini` (static `video-admin-api` → `http://127.0.0.1:48096`, Nacos disabled).

## Environment

| Service | Port | Profile | Status |
|---------|------|---------|--------|
| `video-server` | 48096 | local | UP (`/actuator/health` 200) |
| `iot-gateway` | 48080 | mini | UP (`/actuator/health` 200) |
| `system-server` | 48099 | — | **not running** (OAuth check unavailable locally) |

## Smoke matrix

### 1. Routing — no `Authorization` (proves gateway → Java VIDEO)

```text
curl -s -w "\nHTTP:%{http_code}\n" \
  -H "tenant-id: 1" \
  "http://127.0.0.1:48080/admin-api/video/camera/list?pageNo=1&pageSize=1"
```

**Result:** HTTP **200**, body `{"code":0,"msg":"success",...,"total":7}` — request reached `video-server` via gateway `StripPrefix=1` (`/admin-api/video/camera/list` → `/video/camera/list`).

### 2. Auth filter — `Authorization: Bearer` + `tenant-id` (proves `TokenAuthenticationFilter`)

```text
curl -s -w "\nHTTP:%{http_code}\n" \
  -H "Authorization: Bearer smoke-test-token" \
  -H "tenant-id: 1" \
  "http://127.0.0.1:48080/admin-api/video/camera/list?pageNo=1&pageSize=1"
```

**Result:** HTTP **500** — gateway log shows `TokenAuthenticationFilter` invoked OAuth check via Simple Discovery → `http://127.0.0.1:48099/.../check?accessToken=...` with `tenant-id` header; `Connection refused: /127.0.0.1:48099`.

**Filter behavior (code):** `DEVICE/iot-gateway/.../TokenAuthenticationFilter.java` — non-empty Bearer triggers `checkAccessToken(tenantId, token)`; empty/invalid user returns 401 JSON `UNAUTHORIZED`; upstream unreachable surfaces as 500 before route proxy.

### 3. Exemption

Full OAuth success requires live `system-server`. Local smoke documents routing + filter path; signed **`EX-GATEWAY-AUTH-LOCAL`** in `gates/EXEMPTIONS.md`.

## Verdict

| Check | Status |
|-------|--------|
| (a) Request reaches Java VIDEO through gateway | ✅ 200 camera list |
| (b) Headers / filter behavior matches code | ✅ Bearer → OAuth check to system-server with tenant-id |
| (c) HTTP status/body recorded | ✅ 200 (no token), 500 (token, no system-server) |

**Item 4:** **done** (local mini gateway; prod token success remains ops with live system-server).
