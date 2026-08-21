# EasyAIoT 平台部署文件

> 首次部署請參閱 [快速開始](#快速開始)；進階運維、GPU、資料庫與故障排查見 [部署最佳實踐.md](./部署最佳实践_zh_tw.md)。

---

## 目錄

- [概述](#概述)
- [兩種使用模式](#兩種使用模式)
- [快速開始](#快速開始)
- [macOS / Windows 鏡像部署](#macos--windows-鏡像部署)
- [部署規格](#部署規格)
- [腳本命令參考](#腳本命令參考)
- [RUNTIME 原子模式（計算節點）](#runtime-原子模式計算節點)
- [服務存取與連接埠](#服務存取與連接埠)
- [常見問題](#常見問題)
- [環境要求](#環境要求)

---

## 概述

EasyAIoT 採用 **Docker 容器化 + 統一安裝腳本** 部署，平台由基礎中介軟體與 DEVICE / AI / VIDEO / WEB / APP 等業務模組組成。

| 模組 | 目錄 | 說明 |
|------|------|------|
| 基礎服務 | `.scripts/docker` | Nacos、PostgreSQL、Redis、Kafka、MinIO 等 |
| DEVICE | `DEVICE/` | 裝置管理與 API 閘道（Java / Spring Cloud） |
| AI | `AI/` | 模型訓練、推理（Python） |
| VIDEO | `VIDEO/` | 視訊串流處理、告警、錄影（Python）；算法任務默認可拉起 RUNTIME |
| RUNTIME | `RUNTIME/` | C++ 高速幀執行器；中心機隨 VIDEO 掛載，計算節點可 **原子模式只裝執行器** |
| WEB || WEB | `WEB/` | 管理主控台（Vue 3） |
| APP | `APP/` | 行動端 H5（僅 **full** 規格） |

**統一入口腳本**（下文以 Linux x86 為例）：

| 系統 | 腳本 |
|------|------|
| Linux x86 | `.scripts/docker/install_linux.sh` |
| CentOS / RHEL 系（x86） | `.scripts/docker/install_linux_centos.sh` |
| **CentOS / RHEL 系 · ARM** | `.scripts/docker/install_linux_centos_arm.sh` |
| **麒麟(Kylin)** | `.scripts/docker/install_linux_kylin.sh` |
| **歐拉(openEuler)** | `.scripts/docker/install_linux_openeuler.sh` |
| Linux ARM（通用） | `.scripts/docker/install_linux_arm.sh` |
| macOS | `.scripts/docker/install_mac.sh` |
| Windows | `.scripts/docker/install_windows.ps1` / `install_windows.sh` |

---

## 兩種使用模式

統一入口腳本支援 **互動引導** 與 **指定命令** 兩種用法，底層能力一致，可按場景選擇：

| | 互動引導 | 指定命令 |
|---|---|---|
| **入口** | 無參數 / `menu` / `interactive` | `<命令> [參數]` |
| **適用場景** | 首次部署、現場運維、問題排查 | 開發除錯、腳本化運維、CI/CD |
| **操作方式** | 中文選單，數字選擇 | 直接執行子命令 |
| **執行後** | 自動回到當前選單層 | 執行完畢即退出 |

```bash
# 互動引導
sudo .scripts/docker/install_linux.sh

# 指定命令
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh status
```

**選型建議：**

- 日常手動運維、不熟悉命令參數 → 互動引導
- 已知目標操作、需寫入腳本或定時任務 → 指定命令（**禁止**在 Cron/CI 中無參數呼叫，否則會阻塞等待輸入）

### 互動引導：選單結構

**根選單**

```
  1) 部署 — 安裝、啟停、更新、狀態、日誌
  2) 分析 — 日誌合併、磁碟占用、健康檢查
  0) 退出
```

**【部署】子選單**

| # | 操作 | 等價命令 |
|:-:|------|----------|
| 1 | 首次安裝並啟動 | `install` |
| 2 | 啟動所有服務 | `start` |
| 3 | 停止所有服務 | `stop` |
| 4 | 重啟所有服務 | `restart` |
| 5 | 查看執行狀態 | `status` |
| 6 | 查看服務日誌 | `logs` |
| 7 | 驗證服務健康 | `verify` |
| 8 | 更新映像並重啟 | `update` |
| 9 | 檢查 Docker 環境 | `check` |
| 10 | 查看部署規格 | `profile` |
| 11 | 完整命令列說明 | `help` |

**【分析】子選單**

| # | 操作 | 等價命令 |
|:-:|------|----------|
| 1 | 多模組日誌合併（各源約 500 行） | `analyze-logs` |
| 2 | 磁碟占用分析 | `analyze-disk` |
| 3 | 服務狀態 + 健康驗證 | `status` + `verify` |
| 4 | Docker 環境檢查 | `check` |

**典型操作路徑：**

| 場景 | 互動路徑 |
|------|----------|
| 首次部署 | 1 → 1 → 7 |
| 重啟後拉起服務 | 1 → 2 → 7 |
| 故障資訊採集 | 2 → 3 → 1 → 2 |

---

## 快速開始

打開文件心裏嘀咕：「我這破機器……裝得動嗎？」——**能。先別慫。**

最輕一檔 **edge**，容器總佔用大約就 **1 GB**。攝像頭接入、即時分析、智能告警，小機器也能閉環——舊筆記本先爽一把，上癮了再升檔也不遲。

### 三步上車（推薦輕量檔）

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# 方式 A（推薦）
EASYAIOT_DEPLOY_PROFILE=edge sudo bash .scripts/docker/install_linux.sh install

# 方式 B
# sudo bash .scripts/docker/install_linux.sh edge install
```

裝完瀏覽器打開 `https://<伺服器IP>:8888`，預設帳號 `admin` / `admin123`。驗證一把：

```bash
.scripts/docker/install_linux.sh verify
# 可選：再瞄一眼記憶體是否還在規格內
.scripts/docker/install_linux.sh resources
```

綠燈齊了就收工——比你想的輕鬆，今天可以提前喝杯咖啡了。

> 需要完整規格、互動選單或 CentOS / ARM / 歐拉等入口時，繼續看下面的「環境前提」與兩種安裝方式。

### 環境前提

- 作業系統：**Ubuntu 24.04+**（建議 26.04）；亦支援 **CentOS/RHEL 系**、ARM、**麒麟(Kylin) / 歐拉(openEuler)**
- Docker + Docker Compose **v2.35+**（CentOS / **歐拉(openEuler)** 可用對應入口腳本自動安裝/升級 Docker CE）
- 磁碟可用空間 **≥ 300 GB**（輕量 **edge** 可顯著放寬；完整檔建議按此預留）

```bash
docker --version && docker compose version && docker ps
```

### 方式一：互動引導

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# Ubuntu / 通用 Linux x86
sudo .scripts/docker/install_linux.sh

# CentOS / RHEL / Rocky / Alma x86
# sudo .scripts/docker/install_linux_centos.sh

# CentOS / RHEL 系 ARM
# sudo .scripts/docker/install_linux_centos_arm.sh

# openEuler（卸載自帶 docker-engine、修復倉庫 releasever、裝 Docker CE）
# sudo .scripts/docker/install_linux_openeuler.sh

# 1 部署 → 1 首次安裝 → 7 健康驗證
```

首次安裝會互動選擇部署規格（含 **edge**），完成後瀏覽器存取 `https://<伺服器IP>:8888`（預設 `admin` / `admin123`）。

### 方式二：指定命令

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# 可選：拉取預建構映像，縮短 install 耗時
sudo .scripts/docker/install_linux.sh pull
# CentOS x86：sudo .scripts/docker/install_linux_centos.sh pull
# CentOS ARM：sudo .scripts/docker/install_linux_centos_arm.sh pull
# openEuler：sudo .scripts/docker/install_linux_openeuler.sh pull

sudo .scripts/docker/install_linux.sh install
# CentOS x86：sudo .scripts/docker/install_linux_centos.sh install
# CentOS ARM：sudo .scripts/docker/install_linux_centos_arm.sh install
# openEuler：sudo .scripts/docker/install_linux_openeuler.sh install

.scripts/docker/install_linux.sh verify
# CentOS x86：.scripts/docker/install_linux_centos.sh verify
# CentOS ARM：.scripts/docker/install_linux_centos_arm.sh verify
# openEuler：.scripts/docker/install_linux_openeuler.sh verify

# 可選：再瞄一眼記憶體是否還在規格內
.scripts/docker/install_linux.sh resources
```

裝完瀏覽器打開 `https://<伺服器IP>:8888`。綠燈齊了就收工——比你想的輕鬆。

### CentOS / RHEL 系說明

適用 CentOS 7/8/Stream、Rocky、Alma、RHEL（x86）。入口 `install_linux_centos.sh` 會自動升級 Docker CE、配置鏡像源與 firewalld，再轉交 `install_linux.sh`。詳見簡體中文：[平台部署文档_zh.md](./平台部署文档_zh.md#centos--rhel-系说明)。

### CentOS / RHEL 系 · ARM 說明

適用 aarch64/arm64 上的 CentOS/RHEL 系。入口 `install_linux_centos_arm.sh` 完成與 x86 相同的環境準備後，轉交 `install_linux_arm.sh`（預設 `DOCKER_PLATFORM=linux/arm64`）。詳見簡體中文：[平台部署文档_zh.md](./平台部署文档_zh.md#centos--rhel-系--arm-说明)。

### **歐拉(openEuler)** 說明

適用 **歐拉(openEuler)** 24.03 LTS 等 24.x。入口 `install_linux_openeuler.sh` 會卸載自帶 docker-engine、修復倉庫 `$releasever`、配置鏡像源與 firewalld，再轉交 `install_linux.sh`。詳見簡體中文：[平台部署文档_zh.md](./平台部署文档_zh.md#openeuler-24x-说明)。

### 安裝耗時

| 情況 | 預計耗時 |
|------|----------|
| 已拉取預建構映像 | 10～30 分鐘 |
| 本地完整建構 | 30 分鐘～數小時 |

`install` 執行流程：選擇部署規格 → 環境檢查 → 建立網路 → 按序部署中介軟體與業務模組 → 健康等待。詳見 [部署最佳實踐 - 一鍵部署](./部署最佳实践_zh_tw.md#一鍵部署與分步部署)。

---

## macOS / Windows 鏡像部署

桌面端（macOS、Windows）**僅支援預建構映像部署**，不在本機編譯。詳見簡體中文專文：

- [平台部署文档_zh.md · macOS / Windows](./平台部署文档_zh.md#macos--windows-镜像部署)
- [平台macOS部署文档_zh_tw.md](./平台macOS部署文档_zh_tw.md)（簡體：[平台macOS部署文档_zh.md](./平台macOS部署文档_zh.md)）
- [平台Windows部署文档_zh_tw.md](./平台Windows部署文档_zh_tw.md)（簡體：[平台Windows部署文档_zh.md](./平台Windows部署文档_zh.md)）

```bash
# macOS
bash .scripts/docker/install_mac.sh install

# Windows（Git Bash / WSL）
bash .scripts/docker/install_windows.sh install
```

```powershell
# Windows PowerShell
.\.scripts\docker\install_windows.ps1 install
```

不支援：`build` / `build-runtime`。訪問位址：`https://localhost:8888`。

---

## 部署規格

首次 `install` 時互動選擇，結果保存在 `.scripts/docker/.deploy_profile`，後續 `start` / `stop` / `update` 自動沿用。

| 選項 | 名稱 | 建議記憶體 | 適用場景 |
|:----:|------|----------|----------|
| 0 | **edge** | ≥ 2 GB | 最輕量邊緣 / 舊機器嘗鮮（見 [快速開始](#快速開始)） |
| 1 | **mini** | ≥ 8 GB | 邊緣節點、PoC 驗證 |
| 2 | **standard** | ≥ 16 GB | 常規生產 |
| 3 | **full**（預設） | ≥ 20 GB | 完整功能，含 APP H5 |

```bash
.scripts/docker/install_linux.sh profile                              # 查看當前規格
export EASYAIOT_DEPLOY_PROFILE=full && sudo .../install_linux.sh install  # 非互動指定
```

各規格服務差異見 [部署最佳實踐 - 部署規格選型](./部署最佳实践_zh_tw.md#部署規格選型)。

---

## 腳本命令參考

### 命令一覽

| 命令 | 說明 |
|------|------|
| `install` | 首次安裝並啟動 |
| `start` / `stop` / `restart` | 啟停控制 |
| `status` | 查看執行狀態 |
| `logs [模組]` | 查看日誌，如 `logs VIDEO` |
| `verify` | 健康檢查 |
| `check` | Docker 環境檢查 |
| `update` | 更新映像並重啟 |
| `pull` | 拉取預建構映像 |
| `build` | 本地重新建構映像 |
| `runtime` / `runtime-atomic` | **RUNTIME 原子模式**（只裝計算節點執行器，需 `VIDEO_BASE_URL`） |
| `profile` | 查看部署規格 |
| `analyze-logs` | 多模組日誌合併 |
| `analyze-disk` | 磁碟占用分析 |
| `diagnose` | 進入【分析】子選單 |
| `clean` | 清理容器與映像 ⚠️（含資料卷） |
| `help` | 顯示說明 |
| `menu` | 開啟互動引導 |

### 非互動日誌採集

```bash
cd .scripts/docker

./analyze_merge_logs.sh --non-interactive \
  --modules dev-iot-sink,dev-iot-message,biz-video --lines 500 --save

./analyze_merge_logs.sh --non-interactive --modules DEVICE --save
./analyze_disk_usage.sh --save --top 15
```

### 模式對照

| 操作 | 互動引導 | 指定命令 |
|------|----------|----------|
| 首次安裝 | 1 → 1 | `install` |
| 啟動服務 | 1 → 2 | `start` |
| 健康檢查 | 1 → 7 | `verify` |
| 日誌合併 | 2 → 1 | `analyze-logs` |
| 磁碟分析 | 2 → 2 | `analyze-disk` |

### 分模組部署

```bash
cd .scripts/docker && ./install_middleware_linux.sh install   # 僅中介軟體
cd .scripts/docker && ./install_business_linux.sh install     # 僅業務模組
cd AI && ./install_linux.sh install                           # 單模組
```

---

## RUNTIME 原子模式（計算節點）

適用於**邊緣算力盒 / 集羣計算節點**：本機**只安裝** C++ 執行器，不部署 VIDEO / WEB / DEVICE。告警與心跳匯聚到中心 VIDEO；正式 `realtime` 任務仍默認把帶框檢測流推到中心/集羣 SRS 的 `ai/` 應用。

> **原子 ≠ 永不推流**：原子只表示本機無業務面。詳細步驟見 [`RUNTIME/README.md`](../../RUNTIME/README.md)。

```bash
VIDEO_BASE_URL=http://<中心VIDEO>:6000 \
  bash .scripts/docker/install_linux.sh runtime

VIDEO_BASE_URL=http://192.168.1.10:6000 ./RUNTIME/install_linux.sh atomic
```

| 項 | 說明 |
|----|------|
| 必填 | `VIDEO_BASE_URL`（或參數傳入） |
| 安裝目錄 | 默認 `/opt/easyaiot/RUNTIME` |
| 產出 | `bin/RUNTIME`、`node.env`、`env.sh`、`config/atomic.example.ini` |
| 正式任務 | 中心 WEB 創建算法任務（`executor=cpp`），由 VIDEO + Agent 下發 |
| 手工冒煙 | `source /opt/easyaiot/RUNTIME/env.sh && $RUNTIME_BIN …/atomic.example.ini` |
| 批量分發 | WEB「業務運行時分發」→ RUNTIME(C++) |

中心機完整棧仍用 `install`；本機 VIDEO 安裝會自動編譯掛載 RUNTIME，與原子模式互不替代。

---

## 服務存取與連接埠

`verify` 通過後主要存取位址：

| 服務 | 位址 |
|------|------|
| WEB 管理平台 | https://\<伺服器IP\>:8888 |
| API Gateway | http://\<伺服器IP\>:48080 |
| Nacos | http://\<伺服器IP\>:8848/nacos |
| MinIO Console | http://\<伺服器IP\>:9001 |
| AI | http://\<伺服器IP\>:5000 |
| VIDEO | http://\<伺服器IP\>:6000 |
| APP H5（full） | http://\<伺服器IP\>:9010 |

| 連接埠 | 服務 |
|------|------|
| 8888 | WEB |
| 48080 | Gateway |
| 8848 | Nacos |
| 9000/9001 | MinIO |
| 5000 | AI |
| 6000 | VIDEO |
| 9010 | APP（full） |

完整連接埠列表見 [部署最佳實踐 - 連接埠要求](./部署最佳实践_zh_tw.md#環境要求與部署前檢查清單)。

---

## 常見問題

| 現象 | 處理 |
|------|------|
| Docker `permission denied` | `sudo usermod -aG docker $USER && newgrp docker` |
| Compose 版本過低 | `sudo apt install -y docker-compose-plugin` |
| 連接埠被占用 | `ss -tlnp \| grep <連接埠>` |
| 安裝失敗 | `tail .scripts/docker/logs/install_linux_*.log` |
| 服務正常但無法存取 | `verify` + 檢查防火牆 |
| 磁碟不足 | `df -h /`，建議預留 ≥ 300 GB |

**故障資訊採集：**

```bash
# 互動：2 分析 → 1 日誌 + 2 磁碟
# 命令列：
.scripts/docker/install_linux.sh check
.scripts/docker/install_linux.sh status
.scripts/docker/install_linux.sh verify
cd .scripts/docker && ./analyze_merge_logs.sh --non-interactive --modules all --save
./analyze_disk_usage.sh --save
```

更多排查見 [部署最佳實踐 - 故障排查](./部署最佳实践_zh_tw.md#故障排查)。

---

## 環境要求

| 項目 | 要求 |
|------|------|
| 作業系統 | Ubuntu 24.04+（建議 26.04）；亦支援 macOS、Windows、CentOS/RHEL、ARM、**麒麟(Kylin) / 歐拉(openEuler)** |
| CPU | 最低 4 核，建議 8 核+ |
| 記憶體 | 取決於部署規格（full ≥ 20 GB，建議 32 GB） |
| 磁碟 | 最低 300 GB 可用，建議 500 GB+ SSD |
| GPU | 可選；AI 訓練/推理建議 NVIDIA GPU（CUDA 12.8） |
| Docker Compose | v2.35.0+ |

```bash
# Docker 安裝（Ubuntu）
curl -fsSL https://get.docker.com | sudo sh
sudo apt install -y docker-compose-plugin
sudo usermod -aG docker $USER && newgrp docker
```

**注意事項：**

1. 首次安裝建議使用 `sudo`（設定映像加速與 RTP 連接埠預留）
2. 生產環境修改中介軟體預設密碼（見 [部署最佳實踐](./部署最佳实践_zh_tw.md#預設帳號密碼)）
3. `clean` 會刪除資料卷，執行前務必備份
4. 切換部署規格後需重建 WEB：`cd WEB && ./install_linux.sh build`

---

**文件版本**：3.2  
**最後更新**：2026-07-30  
**腳本入口**：Linux `install_linux.sh`；macOS `install_mac.sh`；Windows `install_windows.ps1` / `install_windows.sh`
