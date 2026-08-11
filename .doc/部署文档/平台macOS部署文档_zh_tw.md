# EasyAIoT 平台 macOS 部署文件

> 文件版本：1.1  
> 更新日期：2026-08-01  
> 適用系統：macOS（Intel / Apple Silicon）  
> 部署方式：**僅預建構映像**（不在本機編譯業務程式碼）

總覽與命令對照見 [平台部署文档_zh_tw.md](./平台部署文档_zh_tw.md#macos--windows-鏡像部署)。  
PANEL 桌面安裝包編譯見倉庫根目錄 [COMPILE/README.md](../../COMPILE/README.md)。

---

## 目錄

1. [概述](#1-概述)
2. [環境準備](#2-環境準備)
3. [一鍵部署](#3-一鍵部署)
4. [常用命令](#4-常用命令)
5. [注意事項與排障](#5-注意事項與排障)

---

## 1. 概述

macOS 使用統一入口：

```bash
.scripts/docker/install_mac.sh
```

建議使用 Homebrew bash 4+ 執行（系統 `/bin/bash` 為 3.2）：

```bash
/opt/homebrew/bin/bash .scripts/docker/install_mac.sh <命令>
```

腳本會：

1. **前置環境檢測**（Docker Desktop / Compose / bash 4+ / curl）：缺什麼提示裝什麼，不滿足則**中止**
2. 必要時嘗試 `open -a Docker` 等待引擎就緒
3. **按需**寫入國內 `registry-mirrors`、按部署形態調配 Docker 引擎記憶體
4. 按部署規格（mini / standard / full）拉取預建構業務映像
5. 透過 `install_middleware_desktop.sh` 拉取並啟動中間件（**FUXA** 走專用 `pull_fuxa.sh`）
6. 以 `EASYAIOT_SKIP_BUILD=1` 呼叫各模組 `install_linux.sh` 僅啟動容器

**不支援**：`build`、`build-runtime`、`clean-build-runtime`。映像需在 Linux CI/伺服器上建構並推送到倉庫（見 `runtime_registry.conf`）。

---

## 2. 環境準備

### 2.1 硬體與 Docker 引擎記憶體

| 規格 | 主機建議 | Docker 引擎目標記憶體 | 說明 |
|------|----------|---------------------|------|
| mini | ≥ 8 GB | **8 GB** | 邊緣 / PoC |
| standard | ≥ 24 GB | **16 GB** | 日常開發演示 |
| full | ≥ 32 GB（推薦 48 GB+） | **24 GB** | 完整功能 |

磁碟建議預留 **≥ 100 GB** 可用空間（映像與資料卷）。

> Desktop 預設常只給引擎約 8 GB；`resources` / `bootstrap` / `install` 在不足時會自動調高（寫入 Docker Desktop `settings-store.json` 並重啟引擎）。可用環境變數覆蓋：`EASYAIOT_DOCKER_MEMORY_GB` / `EASYAIOT_DOCKER_CPUS` / `EASYAIOT_DOCKER_DISK_GB`；`EASYAIOT_DOCKER_SKIP_RESOURCES=1` 跳過。

### 2.2 軟體依賴

| 依賴 | 說明 |
|------|------|
| Homebrew | [brew.sh](https://brew.sh) |
| Docker 引擎 | Docker Desktop（推薦）或 Colima（`brew install docker colima`）；`docker info` 可用即可 |
| Homebrew bash 4+ | `brew install bash`（系統 `/bin/bash` 為 3.2，無法跑映像拉取邏輯） |
| Git | 用於 clone 倉庫 |
| curl | 健康檢查（一般系統自帶） |
| python3 | `mirrors` / `resources` 改寫配置時使用（macOS / Homebrew 一般自帶） |

### 2.3 一鍵安裝前置依賴（推薦）

首次部署前先裝依賴並自檢（腳本會列印前置操作清單，缺什麼提示裝什麼）：

```bash
bash .scripts/docker/install_mac.sh bootstrap   # Homebrew bash + Docker Desktop（失敗可回退 Colima）+ 映像源/資源
bash .scripts/docker/install_mac.sh check       # 前置環境自檢
bash .scripts/docker/install_mac.sh mirrors     # 國內 registry-mirrors（對齊 Linux）
bash .scripts/docker/install_mac.sh resources   # 按形態調引擎記憶體：mini 8G / standard 16G / full 24G
```

`install` / `pull` / `update` / `start` 會在真正部署前**自動做前置檢測**；不滿足則列印安裝指引並中止。

驗證：

```bash
docker --version
docker compose version
docker info | grep -A5 'Registry Mirrors'
docker info | grep -E 'CPUs|Total Memory'
bash --version   # 建議 ≥ 4；Homebrew 路徑多為 /opt/homebrew/bin/bash
```

### 2.4 國內映像加速（與 Linux 一致）

桌面端與 Linux 共用 `DOCKER_MIRROR` / `DOCKER_MIRROR_FALLBACKS`：

| 用途 | 行為 |
|------|------|
| Docker Hub / 中間件 | 寫入 `~/.docker/daemon.json` 的 `registry-mirrors`：預設 DaoCloud → 1ms → 1panel |
| **FUXA** | **例外**：`pull_fuxa.sh` **優先 docker.1ms.run**（DaoCloud 對 `frangoteam/fuxa` 常 403）；compose 固定名為 `docker.1panel.live/frangoteam/fuxa:…` |
| 業務預建構映像 | 來自 `runtime_registry.conf`（如 `docker.cnb.cool/...`），**不受** `registry-mirrors` 影響 |

```bash
# 自動寫入並重啟 Docker Desktop（也可由 bootstrap / install 觸發）
bash .scripts/docker/install_mac.sh mirrors

# 跳過自動寫 mirrors
EASYAIOT_DOCKER_SKIP_MIRROR=1 bash .scripts/docker/install_mac.sh install
```

手動等價配置（一般無需再改 GUI）：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1ms.run",
    "https://docker.1panel.live"
  ]
}
```

### 2.5 Apple Silicon 說明

腳本按 `uname -m` 使用 `linux/arm64` 平台拉取執行時映像與 Nacos。請確認遠端倉庫已發布對應架構清單；若只有 amd64 映像，需在倉庫側補齊 arm64，或改用 Intel Mac / 遠端 Linux。勿對 Nacos 強制 amd64，以免 QEMU 極慢。

### 2.6 PANEL 桌面安裝包（可選）

若需要「雙擊即用」的運維面板，可在本機編譯 macOS 安裝包（圓形白底圖示與 Linux 一致）：

```bash
bash COMPILE/build.sh macos --dmg
# 產物：COMPILE/dist/macos/easyaiot-panel-<版本>.dmg
```

詳見 [COMPILE/README.md](../../COMPILE/README.md#macos-打包dmg)。

---

## 3. 一鍵部署

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# 首次：安裝前置依賴 → 自檢 → 部署
bash .scripts/docker/install_mac.sh bootstrap
bash .scripts/docker/install_mac.sh check
EASYAIOT_DEPLOY_PROFILE=full bash .scripts/docker/install_mac.sh install

# 或互動引導
bash .scripts/docker/install_mac.sh

# 驗證
bash .scripts/docker/install_mac.sh verify
```

非互動指定形態：

```bash
export EASYAIOT_DEPLOY_PROFILE=mini   # 或 standard / full
bash .scripts/docker/install_mac.sh install
```

安裝完成後訪問：

| 服務 | 地址 |
|------|------|
| WEB | http://localhost:8888 |
| Gateway | http://localhost:48080 |
| Nacos | http://localhost:8848/nacos |
| MinIO | http://localhost:9001 |
| FUXA（full） | http://localhost:1881 |
| PANEL（若啟用） | http://localhost:9200 |

---

## 4. 常用命令

| 命令 | 說明 |
|------|------|
| `bootstrap` | 安裝前置依賴（bash4 + Docker）；並嘗試 mirrors / resources |
| `check` | 前置自檢（列印清單；缺什麼提示裝什麼） |
| `mirrors` | 配置國內 `registry-mirrors`（對齊 Linux） |
| `resources` | 按形態調配 Docker CPU/記憶體/磁碟（`resources force` 強制重寫） |
| `install` | 拉取映像並安裝啟動 |
| `pull` / `update` | 僅拉取 / 拉最新並重啟 |
| `start` / `stop` / `restart` | 啟停 |
| `status` / `logs` / `verify` | 狀態、日誌、健康檢查 |
| `profile` / `menu` / `help` | 規格、互動選單、說明 |

```bash
bash .scripts/docker/install_mac.sh start
bash .scripts/docker/install_mac.sh stop
bash .scripts/docker/install_mac.sh logs VIDEO
bash .scripts/docker/install_mac.sh update
```

日誌目錄：`.scripts/docker/logs/install_mac_*.log`

---

## 5. 注意事項與排障

| 問題 | 處理 |
|------|------|
| 需要 bash 4+ | `brew install bash`，用 `/opt/homebrew/bin/bash` 執行腳本；或先 `bootstrap` |
| Docker daemon 未就緒 | 打開 Docker Desktop，等待鯨魚圖示穩定後再試 |
| 引擎記憶體不足 / OOM | `EASYAIOT_DEPLOY_PROFILE=full bash .scripts/docker/install_mac.sh resources`；或在 Desktop → Settings → Resources 手動調到 ≥24GB |
| 中間件拉不動 | `bash .scripts/docker/install_mac.sh mirrors` 後 `docker info` 確認 Registry Mirrors；FUXA 看 `pull_fuxa.sh` 日誌 |
| 業務映像（cnb）拉不動 | `registry-mirrors` 不作用於 `docker.cnb.cool`；檢查本機網路 / 代理 / `runtime_registry.conf` |
| Nacos 長期 unhealthy | 確認 `NACOS_PLATFORM=linux/arm64`；冷啟動可達數分鐘；`docker logs nacos-server` |
| iot-tdengine Restarting | 先保證 `tdengine-server` healthy，再 `start` |
| 媒體地址 / GB28181 異常 | `export HOST_IP=<本機區域網路IP>` 後重新 `start` / `install` |
| 誤執行 `build` | 桌面端會直接拒絕；請改用 `pull` + `install` |
| SRS 等資料目錄 | 媒體根 `EASYAIOT_MEDIA_ROOT`（預設 `/mnt/easyaiot-media`；桌面端 fallback `$HOME/easyaiot/media`） |
| Colima 與 Desktop 混用 | `docker context use desktop-linux`（或 `colima`）；部署前只保留一個引擎 |

生產與完整本機建構請使用 Linux：`.scripts/docker/install_linux.sh`。
