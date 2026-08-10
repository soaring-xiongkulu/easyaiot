# OBSERVE_EVID-S5 — heartbeat + alert-hook probes

**Purpose:** Extend CLOSE-S3 observe evidence beyond health/camera polling. At least one heartbeat or alert-hook success probe required for Phase 3 observe sign-off.

**Date:** 2026-08-10  
**Target:** Java `video-server` (`:48096`) + gateway mini (`:48080`)

## Probes

### 1. Heartbeat (direct)

```powershell
$body = @{
  task_id    = 35
  server_ip  = "127.0.0.1"
  port       = 8035
  process_id = 12345
  log_path   = "$env:USERPROFILE\.video-java\logs\task_35"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:48096/video/algorithm/heartbeat/realtime" `
  -Method POST -Body $body -ContentType "application/json"
```

| Field | Result |
|-------|--------|
| HTTP | **200** |
| `code` | **0** |
| `data.task_id` | **35** |
| `data.task_name` | **vj_p0_certify** |
| Verdict | **PASS** |

### 2. Heartbeat (via gateway)

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:48080/admin-api/video/algorithm/heartbeat/realtime" `
  -Method POST -Body $body -ContentType "application/json" -Headers @{ "tenant-id" = "1" }
```

| Field | Result |
|-------|--------|
| HTTP | **200** |
| `code` | **0** |
| `data.task_id` | **35** |
| Verdict | **PASS** |

### 3. Alert hook (direct)

```powershell
$payload = @{
  object          = "person"
  event           = "vj_p0_certify_task"
  device_id       = "vj_p0_device"
  device_name     = "vj_p0 certify camera"
  task_type       = "realtime"
  region          = "zone_a"
  information     = '{"detections":[]}'
  time            = "2026-08-10 12:00:00"
  correlation_id  = "evid_s5_probe_<unique>"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:48096/video/alert/hook" `
  -Method POST -Body $payload -ContentType "application/json"
```

| Field | Result |
|-------|--------|
| HTTP | **200** |
| `code` | **0** |
| `data.status` | **skipped** (`alert_event_disabled` — fixture task has events off; API path healthy) |
| Verdict | **PASS** (endpoint reachable, `code=0`) |

## Summary

| Probe | Route | Result |
|-------|-------|--------|
| Heartbeat | Direct `:48096` | ✅ PASS |
| Heartbeat | Gateway `:48080` | ✅ PASS |
| Alert hook | Direct `:48096` | ✅ PASS |

**Cross-ref:** [OBSERVE_LOG.md](./OBSERVE_LOG.md) (CLOSE-S3 health/camera, 16m38s, 22/22 OK).
