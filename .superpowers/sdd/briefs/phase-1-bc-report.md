# Phase -1 Task B+C Report — iot-video shell + doctor

**Agent:** Phase -1 implementer  
**Date:** 2026-08-10  
**Worktree:** `F:/acme/.worktrees/video-java`  
**Branch:** `feat/video-java`  
**Brief:** `.superpowers/sdd/briefs/phase-1-bc-brief.md`

## Summary

Delivered Phase -1 empty `DEVICE/iot-video` module (api+biz), `{code,msg,message,data}` adapter skeleton with `GET /video/ping`, `local`/`mini` no-Nacos profiles, testbed manifest skeleton, `tools/video_java/doctor.py`, and `gates/PHASE_-1_GATE.md`. Oracle SHA written back to HANDOFF §3.

## Deliverables

### B1 — Maven module

| Path | Notes |
|------|-------|
| `DEVICE/iot-video/pom.xml` | aggregator |
| `DEVICE/iot-video/iot-video-api/` | `VideoApiConstants` stub; **zero deps** in Phase -1 |
| `DEVICE/iot-video/iot-video-biz/` | runnable jar |
| `DEVICE/pom.xml` | `<module>iot-video</module>` added |
| `VideoServerApplication.java` | minimal `@SpringBootApplication`, no `@EnableCustomConfig` |
| `bootstrap*.yaml` / `application*.yaml` | name `video-server-java`, port `48096`, default profile `local` |

### B2 — Health

- `management.health.db.enabled: false` + no datasource autoconfig
- `/actuator/health` returns `UP` without PostgreSQL

### B3 — Adapter skeleton

- `VideoApiResponse<T>` — fields `code`, `msg`, `message`, `data`
- `VideoApiResponseAdvice` — documented `@RestControllerAdvice` for Python parity vs `CommonResult`
- `GET /video/ping` — success envelope `code=0`

### B4 — local/mini boot

- `bootstrap-local.yaml` + `bootstrap-mini.yaml`: `nacos.discovery.enabled=false`, `config.enabled=false`
- Verified jar boot under `local` and `mini` without Nacos

### C1 — Testbed

- `testdata/video-java/manifest.json` — cases: `vj_p0_health`, `vj_p0_task_start_stop`, `vj_p0_heartbeat`, `vj_p0_alert_hook`
- `thresholds.json` stub, `fixtures/`, `golden/`, `media/README.md`

### C2 — doctor.py

- Structural checks: docs, module, manifest, Java/Maven versions, oracle `VIDEO/` tree, P0 ports 6000/48096
- Soft health probe via `VIDEO_JAVA_BASE` or default `:48096/actuator/health`

### C3 — Gate

- `docs/video-java/gates/PHASE_-1_GATE.md` — PASS with command evidence

### C4 — Docs

- `CERTIFY_STATUS.md` — Phase -1 PASS
- `HANDOFF.md` §3 — oracle SHA `bfbe7457ac65c90eb49d59247a1a2706d55c677d`

## Verification

```text
mvn -f DEVICE/pom.xml -pl iot-video/iot-video-biz -am package -DskipTests
→ BUILD SUCCESS

python tools/video_java/doctor.py
→ doctor: PASS (structural)

local profile:
  GET /actuator/health → {"status":"UP"}
  GET /video/ping → {"code":0,"msg":"success","message":"success","data":{"service":"video-server-java","phase":"-1"}}

mini profile:
  GET /actuator/health → {"status":"UP"}
```

**Toolchain note:** Build/smoke used `JAVA_HOME=F:\acme\.tools\jdk-21.0.2` and `F:\acme\.tools\apache-maven-3.9.16\bin` (not on default PATH).

## Self-review vs brief

| Brief item | Status |
|------------|--------|
| Work only in video-java worktree | ✅ |
| No Phase 0 business | ✅ |
| Exact runtime values (name/port/profile) | ✅ |
| Oracle SHA in HANDOFF | ✅ |
| Adapter with `message` alias | ✅ |
| local/mini no Nacos | ✅ |
| manifest P0 case ids + base URLs | ✅ |
| doctor exit 0 structural | ✅ |
| gate PASS only if package+doctor | ✅ |
| 1–2 commits, no push | ✅ (see below) |

## Concerns / follow-ups

1. **`iot-video-api` zero-deps:** Initial api module depended on `iot-common-base`, which transitively pulled knife4j/springfox and crashed startup (`documentationPluginsBootstrapper` NPE). Removed for Phase -1; Phase 0 should add api deps deliberately (likely `iot-common-base` with swagger exclusions or springdoc-only path).
2. **Default PATH:** `mvn`/`java` not on machine PATH; doctor documents versions when `F:\acme\.tools` is prepended. CI/local runbooks should set `JAVA_HOME` to JDK 21.
3. **Manifest cases:** Skeleton only — no fixtures/golden yet (by design for Phase -1).

## Out of scope (confirmed not done)

- Task lifecycle, ini, heartbeat, alert hook, camera, gateway routes, RUNTIME/ffmpeg changes, push to remote.
