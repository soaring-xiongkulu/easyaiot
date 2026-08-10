# PHASE 0 Gate — VIDEO Java minimal closed loop

**Status:** FAIL
**Updated:** 2026-08-10 02:22 UTC

Only layer status `pass` counts toward gate PASS. `exempt` layers are documented below but do not satisfy parity.

## Commands

```text
mvn -f DEVICE/pom.xml -pl iot-video/iot-video-biz -am package -DskipTests
python tools/video_java/doctor.py
python tools/video_java/certify.py --phase 0
```

## Case results

| case_id | ok | layers |
|---------|----|--------|
| vj_p0_health | False | api:exempt |
| vj_p0_task_start_stop | True | lifecycle:pass, ini:pass |
| vj_p0_heartbeat | True | lifecycle:pass |
| vj_p0_alert_hook | True | alarm:pass |

## Documented exemptions (this run)

- vj_p0_health/api: EX-ORACLE-HEALTH-DB
