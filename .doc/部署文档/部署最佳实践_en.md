# EasyAIoT Deployment Best Practices

> This document stays in sync with project scripts and covers production deployment and operations.  
> For a quick start, see [Platform Deployment Guide](./平台部署文档.md).

---

## Table of Contents

- [Two Usage Modes (Detailed)](#two-usage-modes-detailed)
- [5-Minute Deployment Flow](#5-minute-deployment-flow)
- [Deployment Profile Selection](#deployment-profile-selection)
- [Environment Requirements & Pre-Deployment Checks](#environment-requirements--pre-deployment-checks)
- [One-Click & Step-by-Step Deployment](#one-click--step-by-step-deployment)
- [RUNTIME Atomic Mode (Lightweight Compute Nodes)](#runtime-atomic-mode-lightweight-compute-nodes)
- [Common Operations](#common-operations)
- [Pre-Built Images](#pre-built-images)
- [GPU Configuration](#gpu-configuration)
- [Special Environments](#special-environments)
- [Database Notes](#database-notes)
- [Default Credentials](#default-credentials)
- [Troubleshooting](#troubleshooting)
- [Log Locations](#log-locations)
- [Update & Uninstall](#update--uninstall)
- [Architecture Reference](#architecture-reference)

---

## Two Usage Modes (Detailed)

Unified entry scripts (`install_linux.sh` / `install_linux_centos.sh` / `install_linux_centos_arm.sh` / `install_linux_openeuler.sh` / `install_linux_arm.sh` / `install_linux_kylin.sh` / `install_mac.sh` / `install_windows.sh`) support **two equivalent usage patterns**:

| Mode | Entry | Audience | Characteristics |
|------|-------|----------|-----------------|
| **Interactive** | No args / `menu` / `interactive` | On-site ops, manual operations | Menu-driven, step-by-step, returns to current menu after execution |
| **Direct command** | `<command> [args]` | Dev, SRE, CI/CD | Scriptable, repeatable, exits when done |

```bash
# Interactive
sudo .scripts/docker/install_linux.sh

# Direct command
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh status
```

**Selection guide:** Prefer interactive for manual ops; use direct commands for scripted scenarios (Cron / Ansible / CI). **Do not** invoke without args in automation.

### Interactive: Menu Structure

**Root menu**

```
  1) Deploy — install, start/stop, update, status, logs
  2) Analyze — logs, disk, status diagnostics
  0) Exit
```

**[Deploy] submenu**

| # | Action | Equivalent command |
|:-:|--------|-------------------|
| 1 | First install & start | `install` |
| 2 | Start all services | `start` |
| 3 | Stop all services | `stop` |
| 4 | Restart all services | `restart` |
| 5 | View status | `status` |
| 6 | View logs | `logs` |
| 7 | Health verification | `verify` |
| 8 | Update images & restart | `update` |
| 9 | Check Docker environment | `check` |
| 10 | View deploy profile | `profile` |
| 11 | Full CLI help | `help` |

**[Analyze] submenu** — output suitable for support teams

| # | Action | Equivalent command |
|:-:|--------|-------------------|
| 1 | Multi-module log merge | `analyze-logs` |
| 2 | Disk usage analysis | `analyze-disk` |
| 3 | Status + health verification | `status` + `verify` |
| 4 | Docker environment check | `check` |

**Log merge inner menu** (from Analyze → 1): select sources by number (e.g. `24,23,27`), `0` = all for current profile, `b` = back to [Analyze].

### Direct Command: Full Reference

```bash
cd .scripts/docker   # or use .scripts/docker/install_linux.sh from project root

# Lifecycle
./install_linux.sh install | start | stop | restart | update | clean

# Observability
./install_linux.sh status | logs | logs WEB | verify | check | profile

# Build & images
./install_linux.sh build | pull | build-runtime [module]

# Diagnostics
./install_linux.sh diagnose          # Enter [Analyze] submenu (still interactive)
./install_linux.sh analyze-logs      # Log merge
./install_linux.sh analyze-disk      # Disk report

# Help
./install_linux.sh help | menu
```

### Analysis Tools: Advanced Usage

Analysis scripts in `.scripts/docker/` can run standalone:

**Multi-module log merge `analyze_merge_logs.sh`**

```bash
cd .scripts/docker

# Non-interactive (recommended for runbooks)
./analyze_merge_logs.sh --non-interactive \
  --modules dev-iot-sink,dev-iot-message,biz-video --lines 500 --save

# Module aliases
./analyze_merge_logs.sh --non-interactive --modules DEVICE
./analyze_merge_logs.sh --non-interactive --modules .scripts/docker
./analyze_merge_logs.sh --non-interactive --modules all --save

# Common unit IDs: mw-nacos / mw-postgres / dev-iot-gateway / dev-iot-sink / biz-ai / biz-video / biz-web
./analyze_merge_logs.sh --help
```

Collection strategy: `docker logs` (last N lines) → host log files if container unavailable → latest rotated file tail.

**Disk usage `analyze_disk_usage.sh`**

```bash
./analyze_disk_usage.sh                  # Terminal report
./analyze_disk_usage.sh --save           # Save to logs/disk_usage_*.log
./analyze_disk_usage.sh --top 20
```

Key directories: MinIO `record-space` / `alert-images`, local `playbacks`, alert image staging.

### Automation Notes

- Cron / Ansible / CI **must not** invoke without args (blocks on menu)
- Menu-triggered ops set `EASYAIOT_FROM_MENU=1` to avoid returning to root menu after install
- Non-interactive profile: `export EASYAIOT_DEPLOY_PROFILE=full`

### Relationship to Per-Module Scripts

Module directories (`DEVICE/`, `AI/`, `VIDEO/` …) have independent `install_linux.sh` for that module only — **no** unified [Analyze] menu.  
Full platform orchestration + interactive guide + cross-module log/disk analysis → use `.scripts/docker/install_linux.sh` only.

---

## 5-Minute Deployment Flow

```bash
git clone https://gitee.com/volara/easyaiot.git && cd easyaiot

docker --version && docker compose version

# Option A: Direct command
sudo .scripts/docker/install_linux.sh pull    # Optional: pre-built images
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh verify

# Option B: Interactive
sudo .scripts/docker/install_linux.sh         # 1 Deploy → 1 Install → 7 Verify

# Access: http://<server-ip>:8888
```

### Install Duration

| Scenario | Time |
|----------|------|
| Pre-built images pulled | 10–30 minutes |
| Full local build | 30 minutes to several hours |

---

## Deployment Profile Selection

Selected interactively on first `install`, or via `export EASYAIOT_DEPLOY_PROFILE=mini|standard|full`.  
Saved to `.scripts/docker/.deploy_profile`, reused by `start` / `stop` / `update`.

| Profile | Aliases | Recommended RAM | Use case |
|---------|---------|-----------------|----------|
| **mini** | `1` / `4g` | ≥ 8 GB | Edge nodes, PoC |
| **standard** | `2` / `16g` | ≥ 16 GB | Regular production |
| **full** | `3` (default) | ≥ 20 GB | Full features + APP H5 |

```bash
.scripts/docker/install_linux.sh profile
```

### Services per Profile

**mini**

- Business: `iot-system`, `iot-gateway`, `iot-sink`, `iot-infra`, VIDEO, AI, WEB
- Middleware: Nacos, PostgreSQL, Redis, Kafka, MinIO, SRS, EMQX
- Not started: `iot-device`, `iot-dataset`, `iot-node`, `iot-visualize`, `iot-file`, `iot-message`, `iot-gb28181`, `iot-tdengine`, Milvus, ZLMediaKit, Node-RED, FUXA, TDengine, APP / VISUALIZE / TRANSFORM, etc.
- Event plane: same as standard/full — MQTT → Gateway → iot-sink for ingest and archive
- Media: NFS media stack auto-prepared on install (`EASYAIOT_MEDIA_ROOT`)
- API routing: unified entry via Gateway (48080)

**standard**

- Not started: TDengine, Node-RED, `iot-device`, `iot-tdengine`
- All others started

**full**

- All business modules and middleware, including **APP mobile H5** (9010)

Memory analysis:

```bash
.scripts/docker/analyze_deploy_memory.sh
.scripts/docker/analyze_deploy_memory.sh --all-profiles
```

### NFS shared media storage

Alert images and SRS DVR files are written to a **shared NFS media root** (`EASYAIOT_MEDIA_ROOT`). Single-node installs export locally; clusters use iot-node NFS assignment; desktop installs bind a local directory.

| Item | Description |
|------|-------------|
| Default path | `/mnt/easyaiot-media` (`alert_images/`, `playbacks/`, etc.) |
| No sudo | Falls back to `$HOME/easyaiot/media` |
| In containers | Always mounted at `/mnt/easyaiot-media` |
| DVR archive | SRS `on_dvr` → iot-sink → MinIO → playback URL |
| Alerts | RUNTIME/VIDEO → MQTT → iot-sink reads NFS path → MinIO → DB |

Install scripts call `.scripts/media-cluster/nfs/ensure_nfs_media_stack.sh`. Verification:

```bash
.scripts/docker/verify_dvr_nfs_chain.sh
.scripts/docker/verify_alert_mqtt_chain.sh
```

---

## Environment Requirements & Pre-Deployment Checks

### Hardware

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | See profiles (full ≥ 20 GB) | 32 GB+ |
| Disk | **300 GB** free | 500 GB+ SSD |
| GPU | None (CPU works) | NVIDIA GPU (CUDA 12.8) |

### Software

| Software | Requirement |
|----------|-------------|
| OS | Ubuntu 24.04+ (26.04 recommended); CentOS/RHEL, **Kylin (麒麟) / openEuler (欧拉)**, ARM64 also supported |
| Docker | Installed and daemon accessible |
| Docker Compose | **v2.35.0+** (`docker compose` plugin) |
| NVIDIA Driver / Container Toolkit | GPU scenarios only |

### Docker Permissions

```bash
sudo usermod -aG docker $USER && newgrp docker
docker ps   # should succeed without permission denied
```

Use `sudo` on first install for mirror and RTP port setup.

### Pre-Deployment Checks

```bash
.scripts/docker/detect_system_info.sh
.scripts/docker/install_linux.sh check
df -h / && docker system df
```

### Port Requirements

| Port | Service | Notes |
|------|---------|-------|
| 1880 | Node-RED | full/standard |
| 1883 | EMQX | full/standard |
| 1935 | SRS | RTMP |
| 5432 | PostgreSQL | Primary database |
| 6000 | VIDEO | Video processing |
| 6030 | TDengine | full |
| 6080 | ZLMediaKit | Media server |
| 6379 | Redis | Cache |
| 8848 | Nacos | Registry/config |
| 8888 | WEB | Management UI |
| 9000/9001 | MinIO | Object storage |
| 9010 | APP | full only |
| 9092 | Kafka | Message queue |
| 19530 | Milvus | Vector DB |
| 48080 | Gateway | API gateway |
| 5000 | AI | AI service |
| 30000-30500 | ZLM RTP | Script attempts reservation |

```bash
ss -tlnp | grep -E '8848|5432|6379|9092|5000|6000|8888|48080'
```

---

## One-Click & Step-by-Step Deployment

### One-Click

```bash
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh verify
```

**Automatic `install` flow:**

1. Select profile → save to `.deploy_profile`
2. Pre-built image detection (skip local build if pulled)
3. Docker / Compose / container creation checks
4. Host IP detection (set `HOST_IP=<ip>` to override)
5. RTP port 30000-30500 reservation (requires root)
6. Docker mirror configuration (requires root)
7. Create `easyaiot-network`
8. Deploy in order: middleware → DEVICE → AI → VIDEO → WEB → APP (full)
9. Wait for PostgreSQL / Nacos / Redis
10. Ensure edge Agent when needed

### Step-by-Step

Set profile first:

```bash
export EASYAIOT_DEPLOY_PROFILE=full
```

**Step 1: Middleware**

```bash
cd .scripts/docker && ./install_middleware_linux.sh install
```

| Middleware | Port | Purpose |
|------------|------|---------|
| Nacos | 8848 | Registry/config |
| PostgreSQL | 5432 | Primary DB (6 databases) |
| Redis | 6379 | Cache |
| Kafka | 9092 | Message queue |
| MinIO | 9000/9001 | Object storage |
| Milvus | 19530/9091 | Vector DB |
| SRS | 1935 | Streaming |
| EMQX | 1883 | MQTT (full/standard) |
| ZLMediaKit | 6080 | Media server |
| TDengine | 6030 | Time-series DB (full) |
| Node-RED | 1880 | Rule engine |

**Steps 2+: Business modules**

```bash
cd DEVICE && ./install_linux.sh install
cd AI    && ./install_linux.sh install
cd VIDEO && ./install_linux.sh install
cd WEB   && ./install_linux.sh install
cd APP   && ./install_linux.sh install   # full only
```

**Business modules only**

```bash
cd .scripts/docker
./install_business_linux.sh install
./install_business_linux.sh update DEVICE WEB
./install_business_linux.sh verify
```

---

## RUNTIME Atomic Mode (Lightweight Compute Nodes)

Plan center full-stack and lightweight compute nodes separately:

| Role | What to install | Entry |
|------|-----------------|-------|
| **Center / all-in-one** | Middleware + DEVICE/AI/VIDEO/WEB…; VIDEO auto-mounts RUNTIME | `install_linux.sh install` |
| **Compute node** | **RUNTIME only** | `VIDEO_BASE_URL=… install_linux.sh runtime` |
| **Batch nodes** | Same, via SSH | WEB “workload distribute” → RUNTIME(C++) |

```bash
VIDEO_BASE_URL=http://<center-VIDEO>:6000 \
  sudo -E bash .scripts/docker/install_linux.sh runtime

./RUNTIME/install_linux.sh status
source /opt/easyaiot/RUNTIME/env.sh
```

Notes:

- **Required** `VIDEO_BASE_URL`; optional `SRS_RTMP_BASE` / `AI_RTMP_URL` (example ini only)
- Default install dir `/opt/easyaiot/RUNTIME`
- Atomic ≠ never push: formal `executor=cpp` + `realtime` still default-pushes center `ai/{device}`
- Independent of mini/standard/full profiles—do **not** run full `install` on compute boxes
- Details: [`RUNTIME/README.md`](../../RUNTIME/README.md)

| Variable | Meaning |
|----------|---------|
| `VIDEO_BASE_URL` | Center VIDEO base URL (required for atomic) |
| `EASYAIOT_RUNTIME_INSTALL_DIR` | Install dir, default `/opt/easyaiot/RUNTIME` |
| `SRS_RTMP_BASE` / `AI_RTMP_URL` | Optional example-ini detection stream |
| `EASYAIOT_RUNTIME_BUILD_MODE` | `docker` (default) / `host` |

---

## Common Operations

### Unified Script

```bash
./install_linux.sh install | start | stop | restart | status
./install_linux.sh logs | logs WEB | verify | check | profile
./install_linux.sh build | pull | update | clean
./install_linux.sh runtime          # atomic mode (needs VIDEO_BASE_URL)
./install_linux.sh diagnose | analyze-logs | analyze-disk | help
```

### Per-Module Scripts

Each module (`DEVICE` / `AI` / `VIDEO` / `WEB` / `APP`):

```bash
./install_linux.sh install | start | stop | restart | status | logs | build | clean | update
```

Middleware:

```bash
cd .scripts/docker
./install_middleware_linux.sh install | start | stop | restart | status | logs | build | clean | update
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `EASYAIOT_DEPLOY_PROFILE` | `mini` / `standard` / `full` |
| `HOST_IP` | Force host IP |
| `PARALLEL_MODULES=true` | Parallel start/update for business modules |
| `PARALLEL_BUILD=true` | Parallel build (default serial to avoid OOM) |
| `FORCE_NETWORK_RECREATE=true` | Recreate network after IP change |
| `EASYAIOT_RUNTIME_REGISTRY` | Pre-built image registry |

---

## Pre-Built Images

Config: `.scripts/docker/runtime_registry.conf`

```bash
.scripts/docker/install_linux.sh pull                    # Interactive pull
.scripts/docker/install_linux.sh build-runtime           # Build & push (CI/release)
.scripts/docker/install_linux.sh build-runtime DEVICE    # Single module
```

After pull, `install` / `update` detects `.runtime_images_pulled` and starts containers directly.

---

## GPU Configuration

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi
```

Auto-detection: GPU present → `runtime: nvidia`; no GPU → CPU mode.

Multi-GPU: `export CUDA_VISIBLE_DEVICES=0,1`

---

## Special Environments

```bash
# CentOS / RHEL / Rocky / Alma x86 (auto-upgrade Docker CE, open firewalld ports)
sudo .scripts/docker/install_linux_centos.sh install
# Docker only: sudo .scripts/docker/install_linux_centos.sh --upgrade-docker-only

# CentOS / RHEL family ARM (then delegates to install_linux_arm.sh)
sudo .scripts/docker/install_linux_centos_arm.sh install
# Docker only: sudo .scripts/docker/install_linux_centos_arm.sh --upgrade-docker-only

# openEuler (replace stock docker-engine, fix repo releasever, install Docker CE)
sudo .scripts/docker/install_linux_openeuler.sh install
# Docker only: sudo .scripts/docker/install_linux_openeuler.sh --upgrade-docker-only
# el9 unavailable: --el-release 7

# Kylin OS
sudo .scripts/docker/install_linux_kylin.sh install

# ARM64 (generic, non-EL)
sudo .scripts/docker/install_linux_arm.sh install

# macOS (Docker Desktop + bash 4+)
bash .scripts/docker/install_mac.sh install

# Windows (PowerShell: install_windows.ps1; or Git Bash / WSL)
bash .scripts/docker/install_windows.sh install
```

CentOS notes: x86 entry `install_linux_centos.sh` prepares Docker CE (replaces CentOS 7 stock docker 1.13), DaoCloud mirror, and firewalld; then delegates to `install_linux.sh`. ARM entry `install_linux_centos_arm.sh` uses the same prep then delegates to `install_linux_arm.sh`. On CentOS 7 the platform agent uses `ensure_platform_agent_centos7.sh`. Details (ZH): [平台部署文档_zh.md](./平台部署文档_zh.md#centos--rhel-系--arm-说明).

**openEuler (欧拉)** notes: `install_linux_openeuler.sh` removes conflicting stock `docker-engine`, rewrites Docker CE repo `$releasever` (default el9), configures DaoCloud mirror + DNS and firewalld, then delegates to `install_linux.sh`. Details (ZH): [平台部署文档_zh.md](./平台部署文档_zh.md#openeuler-24x-说明).

Desktop notes: shared logic in `install_desktop_common.sh`; middleware via `install_middleware_desktop.sh`; no local build. See Chinese guides [macOS](./平台macOS部署文档_zh.md) / [Windows](./平台Windows部署文档_zh.md).

---

## Database Notes

### PostgreSQL (6 databases, scripts in `.scripts/postgresql/`)

| Database | Purpose |
|----------|---------|
| ruoyi-vue-pro20 | System management |
| iot-ai20 | AI service |
| iot-device10 | Device management |
| iot-gb2818110 | Video surveillance |
| iot-message10 | Messaging |
| iot-video10 | Video processing |

### TDengine

SQL in `.scripts/tdengine/tdengine_super_tables.sql`; auto-initialized under full profile.

### Backup

```bash
.scripts/postgresql/backup_databases.sh
```

---

## Default Credentials

| Middleware | Username | Password | Console |
|------------|----------|----------|---------|
| Nacos | nacos | nacos | :8848/nacos |
| PostgreSQL | postgres | iot45722414822 | — |
| Redis | — | basiclab@iot975248395 | — |
| MinIO | minioadmin | basiclab@iot975248395 | :9001 |
| EMQX | admin | basiclab@iot6874125784 | :18083 |
| Milvus | — | — | :9091 |

> **Change all default passwords in production.**

---

## Troubleshooting

### Recommended Flow

**Interactive:**

```
No args → 2 Analyze → 4 Docker check → 3 Status+health → 1 Logs → 2 Disk
```

**Direct command:**

```bash
.scripts/docker/install_linux.sh check
.scripts/docker/install_linux.sh status
.scripts/docker/install_linux.sh verify

cd .scripts/docker
./analyze_disk_usage.sh --save
./analyze_merge_logs.sh --non-interactive --modules dev-iot-sink,biz-video,mw-nacos --lines 500 --save
```

### Common Issues

**Service start failures**

```bash
docker ps -a
docker logs -f postgres-server
.scripts/docker/install_linux.sh logs
```

**Network (host IP changed)**

```bash
export FORCE_NETWORK_RECREATE=true
.scripts/docker/install_linux.sh restart
```

**PostgreSQL / Redis**

```bash
.scripts/docker/fix_postgresql.sh
.scripts/docker/fix_redis.sh
```

**Docker system**

```bash
sudo .scripts/docker/diagnose_docker_systemd.sh diagnose
.scripts/docker/cleanup_docker_space.sh
```

**Kafka consumer group**

```bash
cd VIDEO && ./fix_kafka_consumer_group.sh
```

**WEB after profile change**

```bash
cd WEB && ./install_linux.sh build
```

---

## Log Locations

| Location | Description |
|----------|-------------|
| `.scripts/docker/logs/` | Install script logs; `merged_logs_*`, `disk_usage_*` reports |
| `.scripts/docker/standalone-logs/` | Nacos and other middleware on-disk logs |
| `.build-cache/device/logs/` | DEVICE microservice Spring logs |
| `${EASYAIOT_MEDIA_ROOT:-/mnt/easyaiot-media}/srs.log` | SRS streaming (media root resolved by `deploy_profile`) |
| `WEB/logs/runtime.log` | WEB runtime log |
| `docker logs <container>` | Container stdout (common for AI/VIDEO) |

| Need | Interactive | Direct command |
|------|-------------|----------------|
| Last 500 lines, multi-service | Analyze → 1 | `analyze-logs` or `analyze_merge_logs.sh --modules ...` |
| Single module, live tail | Deploy → 6 | `logs VIDEO` or `docker compose logs -f` |
| Install failure | — | `tail .scripts/docker/logs/install_linux_*.log` |

---

## Update & Uninstall

```bash
git pull origin main
sudo .scripts/docker/install_linux.sh update
.scripts/docker/install_linux.sh verify
```

Single module: `cd AI && ./install_linux.sh update`

Uninstall:

```bash
sudo .scripts/docker/install_linux.sh clean   # ⚠️ Removes containers, images, volumes
```

---

## Architecture Reference

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEB Frontend (:8888)                          │
├─────────────────────────────────────────────────────────────────┤
│                 API Gateway (:48080)                              │
├───────────┬───────────┬───────────┬───────────┬─────────────────┤
│ iot-system│ iot-infra │ iot-device│ iot-dataset│  iot-message   │
│ iot-file  │ iot-sink  │ iot-gb28181                        │
├───────────┴───────────┴───────────┴───────────┴─────────────────┤
│  AI (:5000)              │  VIDEO (:6000)    │  APP H5 (:9010) │
├──────────────────────────┴───────────────────┴─────────────────┤
│  Nacos │ PostgreSQL │ Redis │ Kafka │ MinIO │ TDengine          │
│  Milvus │ SRS │ EMQX │ ZLMediaKit │ Node-RED                     │
└─────────────────────────────────────────────────────────────────┘
```

---

*Doc version: 3.1 | 2026-07-08 | Script entry: `.scripts/docker/install_linux.sh` (no args=interactive; `<command>`=direct)*
