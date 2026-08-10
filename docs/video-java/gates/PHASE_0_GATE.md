# PHASE 0 Gate — VIDEO Java minimal closed loop

**Status:** PASS
**Updated:** 2026-08-10 20:00 UTC

Gate PASS when every case `ok` — each layer `pass` or `exempt` with a **signed** exemption ID (see EXEMPTIONS.md). Provisional exemptions do not satisfy.

## Commands

```text
mvn -f DEVICE/pom.xml -pl iot-video/iot-video-biz -am package -DskipTests
python tools/video_java/doctor.py
python tools/video_java/certify.py --phase 0
```

## Case results

| case_id | ok | layers |
|---------|----|--------|
| vj_p0_health | True | api:exempt |
| vj_p0_task_start_stop | True | lifecycle:pass, ini:pass |
| vj_p0_heartbeat | True | lifecycle:pass |
| vj_p0_alert_hook | True | alarm:pass |
| vj_p0_restart | True | lifecycle:pass |

## Documented exemptions (this run)

- vj_p0_health/api: EX-ORACLE-HEALTH-DB
