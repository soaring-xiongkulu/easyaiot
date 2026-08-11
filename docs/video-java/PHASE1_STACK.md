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
| Redis | Docker `redis-server` (host map **16379**→6379) | `127.0.0.1:16379` | **UP** |
| Gateway (`iot-gateway`) | `java -jar …/iot-gateway.jar --spring.profiles.active=local` | `127.0.0.1:48080` | **UP** |
| video-server | `java -jar …/iot-video-biz.jar --spring.profiles.active=local` | `127.0.0.1:48096` | **UP** |
| iot-sink (`sink-server`) | `java -jar …/iot-sink-biz.jar --spring.profiles.active=local` | `127.0.0.1:48092` | **UP** (CP-3) |

**Notes**

- Docker Desktop was down at brief time; started via `D:\Docker\App\Docker Desktop.exe`.
- Nacos image pulled from mirror `docker.1ms.run/nacos/nacos-server:v2.5.1`; fresh volume required admin init (`POST /nacos/v1/auth/users/admin`).
- **Why port 15432 (not 5432):** On this Windows desktop, native `postgresql-x64-17` binds **5432** with a different password — it is **not** the shared ACME `iot-video20` database. Docker `postgres-server` maps host **15432** → container **5432** (see `.scripts/docker` compose). Oracle `VIDEO/.env` uses `:5432` for Linux/container-native networking; on Windows docker-compose the host-facing port is **15432**. Committed `application-local.yaml` targets **15432** so `video-server` reaches the shared DB without CLI override.

## Config files changed

| File | Change |
|------|--------|
| `DEVICE/iot-video/iot-video-biz/src/main/resources/application-local.yaml` | Datasource **`15432`** / `iot-video20` (docker host map; see note above); MinIO `access-key` / `secret-key` env placeholders |
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
| JDBC config committed to port **15432** / `iot-video20` (no CLI override) | **PASS** |
| `GET /admin-api/video/camera/list` via gateway → `code:0`, real device rows | **PASS** |
| `GET /admin-api/video/alert/page` via gateway → `code:0`, real alert rows | **PASS** |

**Evidence:** `logs/phase1-0.3-reverify.json`, `logs/phase1-0.3-evidence.json` (prior run with CLI override)

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

# iot-sink (profile local — post-process enqueue :48092, CP-3)
# PG datasources use docker map 127.0.0.1:15432; Redis 16379; Nacos config center disabled in bootstrap-local.yaml
$env:NACOS_PASSWORD = "<from VIDEO/.env>"
java -jar DEVICE/iot-sink/iot-sink-biz/target/iot-sink-biz.jar --spring.profiles.active=local

# Kafka topics for sink post-process (first boot or if auto-create missed)
docker exec kafka-server /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 \
  --create --if-not-exists --topic iot-post-process-request --partitions 64 --replication-factor 1
docker exec kafka-server /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 \
  --create --if-not-exists --topic iot-post-process-result --partitions 64 --replication-factor 1
```

## Phase 2 readiness

**Ready — 0.1/0.2/0.3 green on committed `application-local.yaml` (port 15432, profile `local` only).**

Note: native `postgresql-x64-17` still occupies host `:5432`; that is a separate instance and intentionally not used.
