# CP-11 Report — Part1 Deep Gap Cleanup

**Status:** PASS (T1–T12)  
**Pack:** CP-11  
**Date:** 2026-08-12  
**SSOT:** `docs/video-java/CODE_PARITY_DEEP_GAP_PACK.md`  
**nested_subagents:** none

## Prior

CP-1…CP-10 PASS per [CODE_PARITY_INDEX.md](../CODE_PARITY_INDEX.md).

## Task results

| ID | Status | Evidence | Notes |
|----|--------|----------|-------|
| T1 | PASS | `logs/cp-11-t1-alert-notify.json` | Full Kafka notification payload when `alert_notification_enabled` + config |
| T2 | PASS | `logs/cp-11-t2-post-matching.json` | Face/plate publish path in post-alert orchestration |
| T3 | PASS | `logs/cp-11-t3-sink-enqueue-fail.json` | Kafka unavailable → HTTP error, no silent success |
| T4 | PASS | `logs/cp-11-t4-flighthub-data.json` | Failure responses include `data` with suggestion |
| T5 | PASS | `logs/cp-11-t5-audiotalk.json` | Dynamic RTP port + noise gate threshold 500 |
| T6 | PASS | `logs/cp-11-t6-gb28181.json` | Alternate RTSP pull + channel attribute sync |
| T7 | PASS | `logs/cp-11-t7-directory.json` | Implicit GB sync, ensure spaces, cascade save_time |
| T8 | PASS | `logs/cp-11-t8-boot-reset-nvr.json` | Auto-enroll reset + NVR link repair on boot |
| T9 | PASS | `logs/cp-11-t9-boot-srs-ip.json` | SRS mount check + IP monitor registration |
| T10 | PASS | `logs/cp-11-t10-status-consumer.json` | No start heartbeat seed; plate consumer group mutex |
| T11 | PASS | `logs/cp-11-t11-hardening.json` | Patrol SSE, alert degraded, snap fixes |
| T12 | PASS | this file + INDEX/BACKLOG/HANDOFF | CP-10 M-04 ONVIF mislabel corrected |

## Verification

- `mvn compile -pl iot-video/iot-video-biz,iot-sink/iot-sink-biz -am` → **BUILD SUCCESS**
- Profile: `local`, zero Fallback, no mini/stub as PASS

## Part2 leftovers (honest gaps)

- InsightFace / Milvus / RUNTIME binary quality on host  
- Real ONVIF/NVR/SIP device联调  
- FlightHub live token / 真机司空  
- Deep SRS `fix_srs.sh` auto-repair (Java logs mismatch only)

**No COMPLETE. No delete Python.**
