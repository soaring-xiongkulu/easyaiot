# OBSERVE_EVID-S6 — alert-hook SUCCESS probe

**Purpose:** Close EVID-S5 gap where alert-hook returned `status=skipped` (`alert_event_disabled`). Re-run with `ensure_p0_alert_fixture` so observe evidence shows **`status=success`** + `alert_id`.

**Date:** 2026-08-10  
**Target:** Java `video-server` (`:48096`)

## Precondition

```powershell
cd F:/acme/.worktrees/video-java/tools/video_java
python -c "from vj_common import ensure_p0_alert_fixture, load_fixture; fx=load_fixture(); ensure_p0_alert_fixture(fx['task_id'], fx['device_id'])"
```

Re-enables certify task 35 (`is_enabled=true`, `alert_event_enabled=true`) after prior `stop()` cases.

## Alert hook (direct)

```powershell
$payload = @{
  object          = "person"
  event           = "vj_p0_certify_task"
  device_id       = "vj_p0_device"
  device_name     = "vj_p0 certify camera"
  task_type       = "realtime"
  region          = "zone_a"
  information     = '{"detections":[]}'
  time            = "2026-08-10 16:25:00"
  correlation_id  = "evid_s6_probe_69d915e0"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:48096/video/alert/hook" `
  -Method POST -Body $payload -ContentType "application/json"
```

### Response (evidence JSON)

```json
{
  "code": 0,
  "msg": "告警事件已发送",
  "message": "告警事件已发送",
  "data": {
    "mode": "direct_persist",
    "alert_id": 4509,
    "status": "success"
  }
}
```

| Field | Result |
|-------|--------|
| HTTP | **200** |
| `code` | **0** |
| `data.status` | **success** (not skipped) |
| `data.alert_id` | **4509** |
| `data.mode` | **direct_persist** |
| Verdict | **PASS** |

## Summary

| Probe | Route | Result |
|-------|-------|--------|
| Alert hook | Direct `:48096` | ✅ `status=success`, `alert_id=4509` |

**Cross-ref:** [OBSERVE_LOG.md](./OBSERVE_LOG.md) (EVID-S6 extension), [OBSERVE_EVID-S5.md](./OBSERVE_EVID-S5.md) (heartbeat + prior skipped hook).
