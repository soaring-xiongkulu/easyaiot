# EasyAIoT Platform macOS Deployment Guide

> Document version: 1.1  
> Updated: 2026-08-01  
> Supported OS: macOS (Intel / Apple Silicon)  
> Deploy mode: **pre-built images only** (no local build of business code)

Overview and command matrix: [Platform Deployment Guide](./平台部署文档.md#macos--windows-image-only-deploy).  
PANEL desktop installer build: [COMPILE/README.md](../../COMPILE/README.md).

---

## Quick Start

Open the docs and mutter: “This Mac… can it run?” — **Yes. Don’t panic.**

Desktop is image-only; start light with **edge / mini**. Then open `https://localhost:8888` (default `admin` / `admin123`).

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

bash .scripts/docker/install_mac.sh bootstrap
EASYAIOT_DEPLOY_PROFILE=edge bash .scripts/docker/install_mac.sh install
bash .scripts/docker/install_mac.sh verify
bash .scripts/docker/install_mac.sh resources
```

All green? You’re done—easier than you feared. Go grab that coffee early.

> Environment prep, mirrors, and troubleshooting: see sections below.

## Table of Contents

0. [Quick Start](#quick-start)
1. [Overview](#1-overview)
2. [Environment Preparation](#2-environment-preparation)
3. [One-Click Deploy](#3-one-click-deploy)
4. [Common Commands](#4-common-commands)
5. [Notes & Troubleshooting](#5-notes--troubleshooting)

---

## 1. Overview

macOS uses a single entry point:

```bash
.scripts/docker/install_mac.sh
```

Prefer Homebrew bash 4+ (system `/bin/bash` is 3.2):

```bash
/opt/homebrew/bin/bash .scripts/docker/install_mac.sh <command>
```

The script will:

1. **Prerequisite checks** (Docker Desktop / Compose / bash 4+ / curl): prints what to install if missing, then **aborts**
2. If needed, try `open -a Docker` and wait for the engine
3. **As needed**, write China `registry-mirrors` and tune Docker engine memory for the deploy profile
4. Pull pre-built business images by profile (mini / standard / full)
5. Pull and start middleware via `install_middleware_desktop.sh` (**FUXA** uses dedicated `pull_fuxa.sh`)
6. Call each module’s `install_linux.sh` with `EASYAIOT_SKIP_BUILD=1` to start containers only

**Not supported:** `build`, `build-runtime`, `clean-build-runtime`. Images must be built on Linux CI/servers and pushed to the registry (see `runtime_registry.conf`).

---

## 2. Environment Preparation

### 2.1 Hardware & Docker Engine Memory

| Profile | Host recommendation | Docker engine target memory | Notes |
|---------|---------------------|-----------------------------|-------|
| mini | ≥ 8 GB | **8 GB** | Edge / PoC |
| standard | ≥ 24 GB | **16 GB** | Daily dev & demos |
| full | ≥ 32 GB (48 GB+ recommended) | **24 GB** | Full features |

Disk: reserve **≥ 100 GB** free (images and volumes).

> Desktop often defaults to ~8 GB for the engine; `resources` / `bootstrap` / `install` raise it when needed (writes Docker Desktop `settings-store.json` and restarts the engine). Override with env: `EASYAIOT_DOCKER_MEMORY_GB` / `EASYAIOT_DOCKER_CPUS` / `EASYAIOT_DOCKER_DISK_GB`; skip with `EASYAIOT_DOCKER_SKIP_RESOURCES=1`.

### 2.2 Software Dependencies

| Dependency | Notes |
|------------|-------|
| Homebrew | [brew.sh](https://brew.sh) |
| Docker engine | Docker Desktop (recommended) or Colima (`brew install docker colima`); `docker info` must work |
| Homebrew bash 4+ | `brew install bash` (system `/bin/bash` 3.2 cannot run image-pull logic) |
| Git | Clone the repository |
| curl | Health checks (usually preinstalled) |
| python3 | Used by `mirrors` / `resources` config rewrites (macOS / Homebrew usually provide it) |

### 2.3 One-Click Prerequisite Install (Recommended)

Install deps and self-check before the first deploy (prints a checklist; installs guidance for anything missing):

```bash
bash .scripts/docker/install_mac.sh bootstrap   # Homebrew bash + Docker Desktop (fallback Colima) + mirrors/resources
bash .scripts/docker/install_mac.sh check       # Prerequisite self-check
bash .scripts/docker/install_mac.sh mirrors     # China registry-mirrors (aligned with Linux)
bash .scripts/docker/install_mac.sh resources   # Engine memory by profile: mini 8G / standard 16G / full 24G
```

`install` / `pull` / `update` / `start` **auto-run prerequisite checks** before real deploy; if unmet, they print install guidance and abort.

Verify:

```bash
docker --version
docker compose version
docker info | grep -A5 'Registry Mirrors'
docker info | grep -E 'CPUs|Total Memory'
bash --version   # Prefer ≥ 4; Homebrew path is often /opt/homebrew/bin/bash
```

### 2.4 China Image Acceleration (Same as Linux)

Desktop and Linux share `DOCKER_MIRROR` / `DOCKER_MIRROR_FALLBACKS`:

| Use | Behavior |
|-----|----------|
| Docker Hub / middleware | Write `registry-mirrors` in `~/.docker/daemon.json`: default DaoCloud → 1ms → 1panel |
| **FUXA** | **Exception:** `pull_fuxa.sh` **prefers docker.1ms.run** (DaoCloud often 403 on `frangoteam/fuxa`); compose pin name `docker.1panel.live/frangoteam/fuxa:…` |
| Business pre-built images | From `runtime_registry.conf` (e.g. `docker.cnb.cool/...`), **not** affected by `registry-mirrors` |

```bash
# Auto-write and restart Docker Desktop (also triggered by bootstrap / install)
bash .scripts/docker/install_mac.sh mirrors

# Skip auto mirror write
EASYAIOT_DOCKER_SKIP_MIRROR=1 bash .scripts/docker/install_mac.sh install
```

Manual equivalent (GUI usually not needed):

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1ms.run",
    "https://docker.1panel.live"
  ]
}
```

### 2.5 Apple Silicon Notes

Scripts use `linux/arm64` for runtime images and Nacos based on `uname -m`. Ensure the remote registry publishes that architecture; if only amd64 exists, add arm64 on the registry side, or use an Intel Mac / remote Linux. Do not force amd64 for Nacos (QEMU is extremely slow).

### 2.6 PANEL Desktop Installer (Optional)

For a double-click ops panel, build the macOS package locally (round white-background icon, same as Linux):

```bash
bash COMPILE/build.sh macos --dmg
# Output: COMPILE/dist/macos/easyaiot-panel-<version>.dmg
```

See [COMPILE/README.md](../../COMPILE/README.md#macos-打包dmg).

---

## 3. One-Click Deploy

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# First time: deps → check → deploy
bash .scripts/docker/install_mac.sh bootstrap
bash .scripts/docker/install_mac.sh check
EASYAIOT_DEPLOY_PROFILE=full bash .scripts/docker/install_mac.sh install

# Or interactive wizard
bash .scripts/docker/install_mac.sh

# Verify
bash .scripts/docker/install_mac.sh verify
```

Non-interactive profile:

```bash
export EASYAIOT_DEPLOY_PROFILE=mini   # or standard / full
bash .scripts/docker/install_mac.sh install
```

After install, open:

| Service | URL |
|---------|-----|
| WEB | https://localhost:8888 |
| Gateway | http://localhost:48080 |
| Nacos | http://localhost:8848/nacos |
| MinIO | http://localhost:9001 |
| FUXA (full) | http://localhost:1881 |
| PANEL (if enabled) | http://localhost:9200 |

---

## 4. Common Commands

| Command | Description |
|---------|-------------|
| `bootstrap` | Install prerequisites (bash4 + Docker); try mirrors / resources |
| `check` | Prerequisite self-check (checklist; install hints for gaps) |
| `mirrors` | Configure China `registry-mirrors` (aligned with Linux) |
| `resources` | Tune Docker CPU/memory/disk by profile (`resources force` to rewrite) |
| `install` | Pull images and install/start |
| `pull` / `update` | Pull only / pull latest and restart |
| `start` / `stop` / `restart` | Lifecycle |
| `status` / `logs` / `verify` | Status, logs, health checks |
| `profile` / `menu` / `help` | Profile, interactive menu, help |

```bash
bash .scripts/docker/install_mac.sh start
bash .scripts/docker/install_mac.sh stop
bash .scripts/docker/install_mac.sh logs VIDEO
bash .scripts/docker/install_mac.sh update
```

Log directory: `.scripts/docker/logs/install_mac_*.log`

---

## 5. Notes & Troubleshooting

| Issue | Action |
|-------|--------|
| Need bash 4+ | `brew install bash`, run with `/opt/homebrew/bin/bash`; or `bootstrap` first |
| Docker daemon not ready | Open Docker Desktop; wait until the whale icon is stable |
| Engine OOM / low memory | `EASYAIOT_DEPLOY_PROFILE=full bash .scripts/docker/install_mac.sh resources`; or Desktop → Settings → Resources ≥24GB |
| Middleware pull fails | `bash .scripts/docker/install_mac.sh mirrors` then check Registry Mirrors in `docker info`; for FUXA see `pull_fuxa.sh` logs |
| Business images (cnb) fail | `registry-mirrors` does not apply to `docker.cnb.cool`; check network / proxy / `runtime_registry.conf` |
| Nacos unhealthy for long | Confirm `NACOS_PLATFORM=linux/arm64`; cold start can take minutes; `docker logs nacos-server` |
| iot-tdengine Restarting | Ensure `tdengine-server` is healthy, then `start` |
| Media / GB28181 issues | `export HOST_IP=<LAN IP>` then `start` / `install` again |
| Accidental `build` | Desktop rejects it; use `pull` + `install` |
| SRS data dirs | Media root `EASYAIOT_MEDIA_ROOT` (default `/mnt/easyaiot-media`; desktop fallback `$HOME/easyaiot/media`) |
| Mixing Colima & Desktop | `docker context use desktop-linux` (or `colima`); keep one engine before deploy |

For production and full local builds, use Linux: `.scripts/docker/install_linux.sh`.
