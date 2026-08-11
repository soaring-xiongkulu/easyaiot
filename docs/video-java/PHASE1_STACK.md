# Phase 1 — Local Full-Stack Wire-Up (0.1 / 0.2 / 0.3)

> Date: 2026-08-11 · Worktree: `feat/video-java` · Profile: **`local`** (commercial defaults, not `mini`)

## Dependency table

| Component | How started | Listen address | Status |
|-----------|-------------|----------------|--------|
| PostgreSQL (`iot-video20`) | Docker `postgres-server` (pre-existing) | `127.0.0.1:15432` → container `:5432` | **UP** (16 devices, 19 alerts) |
| Native PostgreSQL 17 | Windows service `postgresql-x64-17` | `127.0.0.1:5432` | **UP** (blocks port; wrong password for shared DB) |
| Nacos | `docker compose up -d Nacos` in `.scripts/docker` (+ admin init) | `127.0.0.1:8848` | **UP** |
| Kafka | Docker `kafka-server` (auto-started with Docker Desktop) | `127.0.0.1:9092` | **UP** |
| MinIO | Docker `minio-server` | `127.0.0.1:9000` | **UP** |
| Gateway (`iot-gateway`) | `java -jar …/iot-gateway.jar --spring.profiles.active=local` | `127.0.0.1:48080` | **UP** |
| video-server | `java -jar …/iot-video-biz.jar --spring.profiles.active=local` | `127.0.0.1:48096` | **UP** |

**Notes**

- Docker Desktop was down at brief time; started via `D:\Docker\App\Docker Desktop.exe`.
- Nacos image pulled from mirror `docker.1ms.run/nacos/nacos-server:v2.5.1`; fresh volume required admin init (`POST /nacos/v1/auth/users/admin`).
- Desktop PG port conflict: docker-compose maps Postgres to **15432** because native PG17 occupies **5432**. Committed `application-local.yaml` uses canonical **5432** per Oracle `.env`; runtime 0.3 evidence used `--spring.datasource.url=…15432…` override to reach shared `iot-video20` data.

## Config files changed

| File | Change |
|------|--------|
| `DEVICE/iot-video/iot-video-biz/src/main/resources/application-local.yaml` | Datasource `15432` → **`5432`**; MinIO `access-key` / `secret-key` env placeholders |
| `DEVICE/iot-video/iot-video-biz/src/main/resources/bootstrap-local.yaml` | Nacos discovery **enabled** (`video-server`); config center disabled; credentials via `${NACOS_*}` env |

## 0.1 — Nacos registration + `/actuator/health`

| Check | Result |
|-------|--------|
| Nacos instance `video-server` healthy | **PASS** |
| `GET http://127.0.0.1:48096/actuator/health` → `{"status":"UP"}` | **PASS** |

**Evidence:** `logs/phase1-0.1-evidence.json`, `logs/phase1-0.1-video-server.log`

## 0.2 — Gateway `lb://video-server` (not `application-mini` static)

| Check | Result |
|-------|--------|
| Gateway profile `local` (production `application.yaml` routes) | **PASS** |
| `GET http://127.0.0.1:48080/admin-api/video/ping` → `code:0`, `data.service=video-server` | **PASS** |

Route: `application.yaml` → `uri: lb://video-server` for `/admin-api/video/**` (not `application-mini.yaml` static URI).

**Evidence:** `logs/phase1-0.2-evidence.json`, `logs/phase1-0.2-gateway.log`

## 0.3 — Shared DB read-only smoke

| Check | Result |
|-------|--------|
| JDBC config committed to port **5432** / `iot-video20` | **PASS** (config) |
| `GET /admin-api/video/camera/list` via gateway → `code:0`, 16 devices | **PASS** |
| `GET /admin-api/video/alert/page` via gateway → `code:0`, real alert rows | **PASS** |
| Literal port **5432** connect without override on this desktop | **⛔** (native PG17 password mismatch; shared data on docker **15432**) |

**Evidence:** `logs/phase1-0.3-evidence.json`, `logs/phase1-0.3-video-server.log`

## Start commands (reference)

```powershell
# Middleware (from .scripts/docker)
docker compose up -d Nacos   # after mirror pull if needed
# Kafka / MinIO / Postgres typically already running

# Nacos admin init (fresh volume only)
# POST http://127.0.0.1:8848/nacos/v1/auth/users/admin  password=<from env>

# video-server (profile local, NOT mini)
$env:NACOS_PASSWORD = "<from VIDEO/.env>"
$env:MINIO_SECRET_KEY = "<from VIDEO/.env>"
java -jar DEVICE/iot-video/iot-video-biz/target/iot-video-biz.jar --spring.profiles.active=local

# gateway (profile local)
java -jar DEVICE/iot-gateway/target/iot-gateway.jar --spring.profiles.active=local
```

## Phase 2 readiness

**Partial — 0.1/0.2 green; 0.3 functional smoke green with desktop PG port caveat.**

Resolve before Phase 2: stop `postgresql-x64-17` (admin) or remap docker Postgres to host `:5432` so committed `application-local.yaml` connects without override.
