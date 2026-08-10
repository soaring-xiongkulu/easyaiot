# CLOSE-S2 Report — Rename Java service to `video-server` + gateway URI align

**Date:** 2026-08-10  
**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## STATUS

**PASS** — production name `video-server`, gateway `lb://video-server`, port `48096`, certify phases 0/1/2 exit 0.

## Changes

| Area | Before | After |
|------|--------|-------|
| `spring.application.name` | `video-server-java` | `video-server` |
| Gateway `video-admin-api` uri | `lb://video-server-java` | `lb://video-server` |
| `/video/ping` `data.service` | `video-server-java` | `video-server` |
| `VideoApiConstants.SERVICE_NAME` | `video-server-java` | `video-server` |

### Files (primary)

- `DEVICE/iot-video/iot-video-biz/src/main/resources/bootstrap.yaml`
- `DEVICE/iot-gateway/src/main/resources/application.yaml`
- `DEVICE/iot-video/iot-video-api/.../VideoApiConstants.java`
- `DEVICE/iot-video/iot-video-biz/.../VideoPingController.java`
- `tools/video_java/certify.py` (CERTIFY_STATUS template strings)
- Docs: `DUAL_RUN.md`, `CUTOVER.md`, `CERTIFY_STATUS.md`, `HANDOFF.md`, `PHASE_3_GATE.md`, `testbed/README.md`, `gateway-optional-route.yaml`, `PHASE_-1_GATE.md`, retired Python README

## Verification

```text
mvn -f DEVICE/pom.xml -pl iot-video/iot-video-biz -am package -DskipTests  # SUCCESS
curl http://127.0.0.1:48096/video/ping
# {"code":0,"data":{"service":"video-server","phase":"0"},...}

python tools/video_java/certify.py --phase 0 --no-record  # exit 0
python tools/video_java/certify.py --phase 1 --no-record  # exit 0
python tools/video_java/certify.py --phase 2 --no-record  # exit 0
```

## Concerns

- **STACK.md / PLAN.md** still describe dual-run `video-server-java` policy (historical); production truth is in HANDOFF §7, DUAL_RUN, CERTIFY_STATUS.
- **ROLLBACK_LOG.md** P3-S2 drill row is historical (Java was `video-server-java` at drill time).
- **Ops residual** unchanged: gateway auth smoke + 15–30 min observe in prod/staging (`PHASE_3_GATE` items 4–5).
- **Nacos prod:** deploy must restart Java with new name; ensure no stale `video-server-java` registration lingers.
