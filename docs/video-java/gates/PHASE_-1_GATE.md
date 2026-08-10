# Phase -1 Gate — VIDEO Java baseline

> **Verdict:** PASS  
> **Date:** 2026-08-10  
> **Branch:** `feat/video-java`  
> **Oracle tag:** `video-java-oracle-baseline` @ `bfbe7457ac65c90eb49d59247a1a2706d55c677d`

## Checklist

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | `DEVICE/iot-video` api+biz registered in `DEVICE/pom.xml` | PASS | module tree present |
| 2 | `spring.application.name=video-server-java`, port `48096` | PASS | `bootstrap.yaml` |
| 3 | `local`/`mini` profiles disable Nacos discovery+config | PASS | `bootstrap-local.yaml`, `bootstrap-mini.yaml` |
| 4 | `/actuator/health` UP without DB | PASS | smoke below |
| 5 | `{code,msg,message,data}` adapter + demo `/video/ping` | PASS | smoke below |
| 6 | `testdata/video-java/manifest.json` P0 case ids | PASS | doctor |
| 7 | `tools/video_java/doctor.py` structural PASS | PASS | doctor output |
| 8 | No Phase 0 business logic | PASS | only ping shell |

## Commands

```text
# Build (JDK 21 + Maven from F:\acme\.tools)
set JAVA_HOME=F:\acme\.tools\jdk-21.0.2
set PATH=%JAVA_HOME%\bin;F:\acme\.tools\apache-maven-3.9.16\bin;%PATH%

mvn -f DEVICE/pom.xml -pl iot-video/iot-video-biz -am package -DskipTests
# BUILD SUCCESS (iot-video-biz repackaged)

python tools/video_java/doctor.py
# doctor: PASS (structural)

java -jar DEVICE/iot-video/iot-video-biz/target/iot-video-biz.jar --spring.profiles.active=local
# curl http://127.0.0.1:48096/actuator/health  -> {"status":"UP"}
# curl http://127.0.0.1:48096/video/ping       -> {"code":0,"msg":"success","message":"success","data":{...}}
```

## Smoke results (2026-08-10)

| Endpoint | Profile | Result |
|----------|---------|--------|
| `GET /actuator/health` | `local` | `{"status":"UP"}` |
| `GET /video/ping` | `local` | `code=0`, `msg`/`message`=`success`, `data.service=video-server-java` |
| `GET /actuator/health` | `mini` | `{"status":"UP"}` |

## Notes

- Phase -1 `iot-video-api` intentionally has **no** `iot-common-base` dependency to avoid knife4j/springfox bootstrap failure on empty shell; Phase 0 will reintroduce shared DTO deps as needed.
- P0 certify cases in manifest are **skeleton only**; golden recording starts in Phase 0.

## Exit

Phase -1 PASS — **do not** start Phase 0 business until orchestrator opens next task.
