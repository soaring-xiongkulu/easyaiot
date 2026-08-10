# Gateway auth smoke — FR-W1-AUTH (2026-08-10)

**Profile:** `iot-gateway` `--spring.profiles.active=mini` (static `video-admin-api` → `http://127.0.0.1:48096`, Nacos disabled).  
**Token check:** `system-server` `:48099` (`local,mini`; Postgres `host.docker.internal:15432`, Redis `:16379`).

## Environment

| Service | Port | Profile | Status |
|---------|------|---------|--------|
| `video-server` | 48096 | local | UP (`/actuator/health` 200) |
| `iot-gateway` | 48080 | mini | UP (`/actuator/health` 200) |
| `system-server` | 48099 | local,mini | UP (`/actuator/health` 200) |

## Smoke matrix

### 1. Routing — no `Authorization` (gateway → Java VIDEO passthrough)

```text
curl -s -w "\nHTTP:%{http_code}\n" \
  -H "tenant-id: 1" \
  "http://127.0.0.1:48080/admin-api/video/camera/list?pageNo=1&pageSize=1"
```

**Result:** HTTP **200**, body `{"code":0,"msg":"success",...,"total":7}` — request reached `video-server` via gateway `StripPrefix=1`.  
**Note:** `TokenAuthenticationFilter` passes through when Bearer is absent (auth enforcement delegated to downstream / product policy).

### 2. Auth filter — invalid `Authorization: Bearer` + `tenant-id`

```text
curl -s -w "\nHTTP:%{http_code}\n" \
  -H "Authorization: Bearer invalid-token-xyz" \
  -H "tenant-id: 1" \
  "http://127.0.0.1:48080/admin-api/video/camera/list?pageNo=1&pageSize=1"
```

**Result:** HTTP **401**, body `{"code":401,"msg":"账号未登录"}` — `TokenAuthenticationFilter` invoked OAuth check via Simple Discovery → `http://127.0.0.1:48099/rpc-api/system/oauth2/token/check?accessToken=...` with `tenant-id` header; invalid token rejected.

### 3. Auth filter — valid Bearer (login → gateway → video-server)

Obtain token (direct system-server, tenant 1):

```text
curl -s -X POST -H "tenant-id: 1" -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  "http://127.0.0.1:48099/admin-api/system/auth/login"
```

**Login result:** `accessToken=fef03f51511245e48e11b6bda2feeb95` (example run 2026-08-10).

Gateway request:

```text
curl -s -w "\nHTTP:%{http_code}\n" \
  -H "Authorization: Bearer fef03f51511245e48e11b6bda2feeb95" \
  -H "tenant-id: 1" \
  "http://127.0.0.1:48080/admin-api/video/camera/list?pageNo=1&pageSize=1"
```

**Result:** HTTP **200**, body `{"code":0,"msg":"success",...,"total":7}` — OAuth check succeeded; response from `video-server`.

### 4. system-server token check (RPC)

```text
curl -s "http://127.0.0.1:48099/rpc-api/system/oauth2/token/check?accessToken=fef03f51511245e48e11b6bda2feeb95"
```

**Result:** HTTP **200**, `{"code":0,"data":{"userId":1,"userType":2,"tenantId":1,...}}`.

## Verdict

| Check | Status |
|-------|--------|
| (a) Request reaches Java VIDEO through gateway | ✅ 200 camera list |
| (b) Invalid Bearer → real OAuth check + 401 | ✅ system-server `:48099` live |
| (c) Valid Bearer → 200 body from video-server | ✅ token login + gateway proxy |
| (d) `EX-GATEWAY-AUTH-LOCAL` | ✅ **resolved by FR-W1-AUTH** |

**Reproduce:** `tools/video_java/gateway_auth_smoke.ps1` (requires `video-server`, `system-server`, `iot-gateway` mini up).
