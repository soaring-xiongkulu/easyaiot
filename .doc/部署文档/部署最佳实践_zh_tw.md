# EasyAIoT 部署最佳實踐

> 本文件與專案腳本即時對齊，涵蓋生產環境部署與運維細節。  
> 快速上手請參閱 [平台部署文件_zh_tw.md](./平台部署文档_zh_tw.md)。

---

## 目錄

- [兩種使用模式（詳細）](#兩種使用模式詳細)
- [快速開始](#快速開始)
- [5 分鐘完整檔備忘](#5-分鐘完整檔備忘)
- [部署規格選型](#部署規格選型)
- [環境要求與部署前檢查](#環境要求與部署前檢查清單)
- [一鍵部署與分步部署](#一鍵部署與分步部署)
- [RUNTIME 原子模式（計算節點輕裝）](#runtime-原子模式計算節點輕裝)
- [常用運維命令](#常用運維命令)
- [預建構映像](#預建構映像)
- [GPU 配置](#gpu-配置)
- [特殊環境](#特殊環境)
- [資料庫說明](#資料庫說明)
- [預設帳號密碼](#預設帳號密碼)
- [故障排查](#故障排查)
- [日誌位置](#日誌位置)
- [更新與卸載](#更新與卸載)
- [架構參考](#架構參考)

---

## 兩種使用模式（詳細）

統一入口腳本（`install_linux.sh` / `install_linux_centos.sh` / `install_linux_centos_arm.sh` / `install_linux_openeuler.sh` / `install_linux_arm.sh` / `install_linux_kylin.sh`）支援 **兩種等價用法**：

| 模式 | 入口 | 受眾 | 特點 |
|------|------|------|------|
| **互動引導** | 無參數 / `menu` / `interactive` | 現場運維、手動操作 | 中文選單、分步引導、執行後自動回到當前選單 |
| **指定命令** | `<命令> [參數]` | 開發、SRE、CI/CD | 可腳本化、可重複、執行完即退出 |

```bash
# 互動引導
sudo .scripts/docker/install_linux.sh

# 指定命令
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh status
```

**選型建議：** 手動運維優先互動引導；腳本化場景（Cron / Ansible / CI）必須使用指定命令，禁止無參數呼叫。

### 互動引導：選單結構

**根選單**

```
  1) 部署 — 安裝、啟停、更新、狀態、日誌
  2) 分析 — 日誌、磁碟、狀態等問題定位
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

**【分析】子選單** — 輸出建議直接發給技術支援

| # | 操作 | 等價命令 |
|:-:|------|----------|
| 1 | 多模組日誌合併 | `analyze-logs` |
| 2 | 磁碟占用分析 | `analyze-disk` |
| 3 | 狀態 + 健康驗證 | `status` + `verify` |
| 4 | Docker 環境檢查 | `check` |

**日誌合併內層**（從分析 → 1 進入）：按序號多選日誌源（如 `24,23,27`），`0` = 當前規格下全部，`b` = 返回【分析】。

### 指定命令：完整參考

```bash
cd .scripts/docker   # 以下均可用 .scripts/docker/install_linux.sh 從專案根執行

# 生命週期
./install_linux.sh install | start | stop | restart | update | clean

# 可觀測性
./install_linux.sh status | logs | logs WEB | verify | check | profile

# 建構與映像
./install_linux.sh build | pull | build-runtime [模組]

# 問題分析
./install_linux.sh diagnose          # 進入【分析】子選單（仍互動）
./install_linux.sh analyze-logs      # 日誌合併
./install_linux.sh analyze-disk      # 磁碟報告

# 說明
./install_linux.sh help | menu
```

### 分析工具：進階用法

分析腳本位於 `.scripts/docker/`，可獨立執行：

**多模組日誌合併 `analyze_merge_logs.sh`**

```bash
cd .scripts/docker

./analyze_merge_logs.sh --non-interactive \
  --modules dev-iot-sink,dev-iot-message,biz-video --lines 500 --save

./analyze_merge_logs.sh --non-interactive --modules DEVICE
./analyze_merge_logs.sh --non-interactive --modules .scripts/docker
./analyze_merge_logs.sh --non-interactive --modules all --save

# 常用單元 ID：mw-nacos / mw-postgres / dev-iot-gateway / dev-iot-sink / biz-ai / biz-video / biz-web
./analyze_merge_logs.sh --help
```

採集策略：優先 `docker logs`（最近 N 行）→ 容器不可用時讀宿主機日誌 → 滾動日誌取最新檔案尾部。

**磁碟占用 `analyze_disk_usage.sh`**

```bash
./analyze_disk_usage.sh                  # 終端報告
./analyze_disk_usage.sh --save           # 落盤到 logs/disk_usage_*.log
./analyze_disk_usage.sh --top 20
```

重點目錄：MinIO `record-space` / `alert-images`、本地 `playbacks`、告警圖中轉目錄。

### 自動化注意事項

- Cron / Ansible / CI **禁止**無參數呼叫（會阻塞在選單）
- 從選單內部觸發的操作設 `EASYAIOT_FROM_MENU=1`，避免 install 後彈回根選單；命令列模式無此行為
- 非互動指定規格：`export EASYAIOT_DEPLOY_PROFILE=full`

### 與單模組腳本的關係

各模組目錄（`DEVICE/`、`AI/`、`VIDEO/` …）有獨立 `install_linux.sh`，僅管理該模組，**不含**統一【分析】選單。  
全平台編排 + 互動引導 + 跨模組日誌/磁碟分析 → 只用 `.scripts/docker/install_linux.sh`。

---

## 快速開始

打開文件心裏嘀咕：「我這破機器……裝得動嗎？」——**能。先別慫。**

最輕一檔 **edge**，容器總佔用大約就 **1 GB**。舊筆記本先爽一把，上癮了再升檔也不遲。

```bash
git clone https://gitee.com/volara/easyaiot.git && cd easyaiot

# 推薦：最輕量檔
EASYAIOT_DEPLOY_PROFILE=edge sudo bash .scripts/docker/install_linux.sh install

# 或互動引導（選單裡也可選 edge / mini / standard / full）
# sudo .scripts/docker/install_linux.sh

.scripts/docker/install_linux.sh verify
# 可選：再瞄一眼記憶體是否還在規格內
.scripts/docker/install_linux.sh resources
```

裝完瀏覽器打開 `https://<伺服器IP>:8888`，預設 `admin` / `admin123`。  
綠燈齊了就收工——比你想的輕鬆，今天可以提前喝杯咖啡了。

### 5 分鐘完整檔備忘

```bash
# 方式 A：指定命令（完整檔示例）
sudo .scripts/docker/install_linux.sh pull    # 可選，拉預建構映像
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh verify

# 方式 B：互動引導
sudo .scripts/docker/install_linux.sh         # 1 部署 → 1 安裝 → 7 驗證

# 存取：https://<伺服器IP>:8888
```

### 安裝耗時

| 情況 | 耗時 |
|------|------|
| 已拉預建構映像 | 10～30 分鐘 |
| 本地完整建構 | 30 分鐘～數小時 |

---

## 部署規格選型

首次 `install` 互動選擇，或 `export EASYAIOT_DEPLOY_PROFILE=edge|mini|standard|full`。  
結果保存在 `.scripts/docker/.deploy_profile`，後續 `start` / `stop` / `update` 自動沿用。

| 規格 | 別名 | 建議記憶體 | 適用場景 |
|------|------|----------|----------|
| **edge** | `0` | ≥ 2 GB | 最輕量邊緣 / 舊機器嘗鮮 |
| **mini** | `1` / `4g` | ≥ 8 GB | 邊緣節點、PoC |
| **standard** | `2` / `16g` | ≥ 16 GB | 常規生產 |
| **full** | `3`（預設） | ≥ 20 GB | 完整功能 + APP H5 |

```bash
.scripts/docker/install_linux.sh profile
```

### 各規格包含的服務

**mini**

- 業務：`iot-system`、`iot-gateway`、`iot-sink`、`iot-infra`、VIDEO、AI、WEB
- 中介軟體：Nacos、PostgreSQL、Redis、Kafka、MinIO、SRS、EMQX
- 不啟動：`iot-device`、`iot-dataset`、`iot-node`、`iot-visualize`、`iot-file`、`iot-message`、`iot-gb28181`、`iot-tdengine`、Milvus、ZLMediaKit、Node-RED、FUXA、TDengine、APP / VISUALIZE / TRANSFORM 等全量模組
- 事件面：與 standard/full 一致 — MQTT → Gateway → iot-sink 落庫與歸檔
- 媒體：安裝時自動準備 NFS 媒體棧（`EASYAIOT_MEDIA_ROOT`）
- API 路由：經 Gateway（48080）統一入口

**standard**

- 不啟動：TDengine、Node-RED、`iot-device`、`iot-tdengine`
- 其餘全部啟動

**full**

- 全部業務模組與中介軟體，含 **APP 行動端 H5**（9010）

記憶體分析：

```bash
.scripts/docker/analyze_deploy_memory.sh
.scripts/docker/analyze_deploy_memory.sh --all-profiles
```

### NFS 共享媒體儲存

告警截圖、SRS 錄影等**統一寫入 NFS 媒體根**（環境變數 `EASYAIOT_MEDIA_ROOT`）。單機部署由本機 export；叢集由 iot-node 分配 NFS 掛載；桌面端以本地目錄 bind。

| 項 | 說明 |
|----|------|
| 標準路徑 | `/mnt/easyaiot-media`（`alert_images/`、`playbacks/` 等） |
| 無 sudo | 自動 fallback 至 `$HOME/easyaiot/media` |
| 容器內 | 固定掛載 `/mnt/easyaiot-media` |
| 錄影歸檔 | SRS `on_dvr` → iot-sink → MinIO → playback URL |
| 告警 | RUNTIME/VIDEO → MQTT → iot-sink 讀 NFS 同路徑 → MinIO → DB |

一鍵安裝會呼叫 `.scripts/media-cluster/nfs/ensure_nfs_media_stack.sh`；鏈路驗收：

```bash
.scripts/docker/verify_dvr_nfs_chain.sh
.scripts/docker/verify_alert_mqtt_chain.sh
```

---

## 環境要求與部署前檢查清單

### 硬體

| 資源 | 最低 | 建議 |
|------|------|------|
| CPU | 4 核 | 8 核+ |
| 記憶體 | 見部署規格（full ≥ 20 GB） | 32 GB+ |
| 磁碟 | **300 GB** 可用 | 500 GB+ SSD |
| GPU | 無（CPU 可執行） | NVIDIA GPU（CUDA 12.8） |

### 軟體

| 軟體 | 要求 |
|------|------|
| 作業系統 | Ubuntu 24.04+（建議 26.04）；亦支援 CentOS/RHEL、**麒麟(Kylin) / 歐拉(openEuler)**、ARM64 |
| Docker | 已安裝且 daemon 可存取 |
| Docker Compose | **v2.35.0+**（`docker compose` 插件） |
| NVIDIA Driver / Container Toolkit | 僅 GPU 場景 |

### Docker 權限

```bash
sudo usermod -aG docker $USER && newgrp docker
docker ps   # 應無 permission denied
```

首次安裝建議 `sudo`，以設定映像源與 RTP 連接埠預留。

### 部署前檢查

```bash
.scripts/docker/detect_system_info.sh
.scripts/docker/install_linux.sh check
df -h / && docker system df
```

### 連接埠要求

| 連接埠 | 服務 | 說明 |
|------|------|------|
| 1880 | Node-RED | full/standard |
| 1883 | EMQX | full/standard |
| 1935 | SRS | RTMP |
| 5432 | PostgreSQL | 主資料庫 |
| 6000 | VIDEO | 視訊處理 |
| 6030 | TDengine | full |
| 6080 | ZLMediaKit | 媒體伺服器 |
| 6379 | Redis | 快取 |
| 8848 | Nacos | 註冊/配置 |
| 8888 | WEB | 管理介面 |
| 9000/9001 | MinIO | 物件儲存 |
| 9010 | APP | 僅 full |
| 9092 | Kafka | 訊息佇列 |
| 19530 | Milvus | 向量庫 |
| 48080 | Gateway | API 閘道 |
| 5000 | AI | AI 服務 |
| 30000-30500 | ZLM RTP | 腳本會嘗試預留 |

```bash
ss -tlnp | grep -E '8848|5432|6379|9092|5000|6000|8888|48080'
```

---

## 一鍵部署與分步部署

### 一鍵部署

```bash
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh verify
```

**install 自動流程：**

1. 選擇部署規格 → 寫入 `.deploy_profile`
2. 預建構映像檢測（若已 pull 則跳過本地 build）
3. Docker / Compose / 容器建立能力檢查
4. 宿主機 IP 檢測（可設 `HOST_IP=<ip>`）
5. RTP 連接埠 30000-30500 預留（需 root）
6. Docker 映像加速設定（需 root）
7. 建立 `easyaiot-network`
8. 按序部署：中介軟體 → DEVICE → AI → VIDEO → WEB → APP（full）
9. 等待 PostgreSQL / Nacos / Redis 就緒
10. 按需確保邊緣 Agent

### 分步部署

先確定規格：

```bash
export EASYAIOT_DEPLOY_PROFILE=full
```

**第一步：中介軟體**

```bash
cd .scripts/docker && ./install_middleware_linux.sh install
```

| 中介軟體 | 連接埠 | 用途 |
|--------|------|------|
| Nacos | 8848 | 註冊/配置 |
| PostgreSQL | 5432 | 主資料庫（6 庫） |
| Redis | 6379 | 快取 |
| Kafka | 9092 | 訊息佇列 |
| MinIO | 9000/9001 | 物件儲存 |
| Milvus | 19530/9091 | 向量庫 |
| SRS | 1935 | 串流媒體 |
| EMQX | 1883 | MQTT（full/standard） |
| ZLMediaKit | 6080 | 媒體伺服器 |
| TDengine | 6030 | 時序庫（full） |
| Node-RED | 1880 | 規則引擎 |

**第二步～：業務模組**

```bash
cd DEVICE && ./install_linux.sh install
cd AI    && ./install_linux.sh install
cd VIDEO && ./install_linux.sh install
cd WEB   && ./install_linux.sh install
cd APP   && ./install_linux.sh install   # 僅 full
```

**僅業務模組（不含中介軟體）**

```bash
cd .scripts/docker
./install_business_linux.sh install
./install_business_linux.sh update DEVICE WEB
./install_business_linux.sh verify
```

---

## RUNTIME 原子模式（計算節點輕裝）

完整棧（中心）與輕裝算力節點應分開規劃：

| 角色 | 部署內容 | 入口 |
|------|----------|------|
| **中心 / 一體機** | 中介軟體 + DEVICE/AI/VIDEO/WEB…；VIDEO 自動掛載 RUNTIME | `install_linux.sh install` |
| **計算節點** | **只裝 RUNTIME** | `VIDEO_BASE_URL=… install_linux.sh runtime` |
| **多節點批量** | 同上，經 SSH 分發 | WEB「業務運行時分發」→ RUNTIME(C++) |

```bash
VIDEO_BASE_URL=http://<中心VIDEO>:6000 \
  sudo -E bash .scripts/docker/install_linux.sh runtime

./RUNTIME/install_linux.sh status
source /opt/easyaiot/RUNTIME/env.sh
```

要點：必填 `VIDEO_BASE_URL`；原子 ≠ 永不推流；與 mini/standard/full 無關——不要在算力盒上再跑完整 `install`。細則見 [`RUNTIME/README.md`](../../RUNTIME/README.md)。

---

## 常用運維命令

### 統一腳本

```bash
./install_linux.sh install | start | stop | restart | status
./install_linux.sh logs | logs WEB | verify | check | profile
./install_linux.sh build | pull | update | clean
./install_linux.sh runtime          # 原子模式（需 VIDEO_BASE_URL）
./install_linux.sh diagnose | analyze-logs | analyze-disk | help
```

### 單模組腳本

每個模組（`DEVICE` / `AI` / `VIDEO` / `WEB` / `APP`）：

```bash
./install_linux.sh install | start | stop | restart | status | logs | build | clean | update
```

中介軟體：

```bash
cd .scripts/docker
./install_middleware_linux.sh install | start | stop | restart | status | logs | build | clean | update
```

### 常用環境變數

| 變數 | 說明 |
|------|------|
| `EASYAIOT_DEPLOY_PROFILE` | `mini` / `standard` / `full` |
| `HOST_IP` | 強制宿主機 IP |
| `PARALLEL_MODULES=true` | 業務模組並行啟動/更新 |
| `PARALLEL_BUILD=true` | 並行建構（預設串行防 OOM） |
| `FORCE_NETWORK_RECREATE=true` | IP 變更後重建網路 |
| `EASYAIOT_RUNTIME_REGISTRY` | 預建構映像倉庫 |

---

## 預建構映像

設定檔：`.scripts/docker/runtime_registry.conf`

```bash
.scripts/docker/install_linux.sh pull                    # 互動拉取
.scripts/docker/install_linux.sh build-runtime           # 建構並推送（CI/發布）
.scripts/docker/install_linux.sh build-runtime DEVICE    # 單模組
```

拉取成功後，`install` / `update` 偵測到 `.runtime_images_pulled` 標記，直接啟動容器。

---

## GPU 配置

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi
```

腳本自動偵測 GPU：有 → `runtime: nvidia`；無 → CPU 模式。

多 GPU：`export CUDA_VISIBLE_DEVICES=0,1`

---

## 特殊環境

```bash
# CentOS / RHEL / Rocky / Alma x86（自動升級 Docker CE、放行 firewalld）
sudo .scripts/docker/install_linux_centos.sh install
# 僅準備 Docker：sudo .scripts/docker/install_linux_centos.sh --upgrade-docker-only

# CentOS / RHEL 系 ARM（環境準備後轉交 install_linux_arm.sh）
sudo .scripts/docker/install_linux_centos_arm.sh install
# 僅準備 Docker：sudo .scripts/docker/install_linux_centos_arm.sh --upgrade-docker-only

# openEuler（卸載自帶 docker-engine、修復倉庫 releasever、裝 Docker CE）
sudo .scripts/docker/install_linux_openeuler.sh install
# 僅準備 Docker：sudo .scripts/docker/install_linux_openeuler.sh --upgrade-docker-only

# 銀河麒麟
sudo .scripts/docker/install_linux_kylin.sh install

# ARM64（通用，非 EL 系）
sudo .scripts/docker/install_linux_arm.sh install

# macOS
bash .scripts/docker/install_mac.sh install

# Windows
bash .scripts/docker/install_windows.sh install
```

CentOS 說明：x86 入口 `install_linux_centos.sh` 會先準備 Docker CE（替換 CentOS 7 自帶 docker 1.13）、鏡像源與 firewalld，再轉交 `install_linux.sh`；ARM 入口 `install_linux_centos_arm.sh` 同樣準備環境後轉交 `install_linux_arm.sh`。詳見 [平台部署文档_zh.md](./平台部署文档_zh.md#centos--rhel-系--arm-说明)。

**歐拉(openEuler)** 說明：入口 `install_linux_openeuler.sh` 會卸載自帶 docker-engine、修復 `$releasever`、配置鏡像源/DNS 與 firewalld，再轉交 `install_linux.sh`。詳見 [平台部署文档_zh.md](./平台部署文档_zh.md#openeuler-24x-说明)。

詳見 [平台部署文档_zh.md](./平台部署文档_zh.md#macos--windows-镜像部署)、[平台macOS部署文档_zh.md](./平台macOS部署文档_zh.md)、[平台Windows部署文档_zh.md](./平台Windows部署文档_zh.md)。

---

## 資料庫說明

### PostgreSQL（6 庫，腳本位於 `.scripts/postgresql/`）

| 庫名 | 用途 |
|------|------|
| ruoyi-vue-pro20 | 系統管理 |
| iot-ai20 | AI 服務 |
| iot-device10 | 裝置管理 |
| iot-gb2818110 | 視訊監控 |
| iot-message10 | 訊息推送 |
| iot-video10 | 視訊處理 |

### TDengine

SQL 位於 `.scripts/tdengine/tdengine_super_tables.sql`，full 規格自動初始化。

### 備份

```bash
.scripts/postgresql/backup_databases.sh
```

---

## 預設帳號密碼

| 中介軟體 | 使用者名稱 | 密碼 | 主控台 |
|--------|--------|------|--------|
| Nacos | nacos | nacos | :8848/nacos |
| PostgreSQL | postgres | iot45722414822 | — |
| Redis | — | basiclab@iot975248395 | — |
| MinIO | minioadmin | basiclab@iot975248395 | :9001 |
| EMQX | admin | basiclab@iot6874125784 | :18083 |
| Milvus | — | — | :9091 |

> **生產環境務必修改所有預設密碼。**

---

## 故障排查

### 推薦流程

**互動引導：**

```
無參數 → 2 分析 → 4 Docker 檢查 → 3 狀態+健康 → 1 日誌 → 2 磁碟
```

**指定命令：**

```bash
.scripts/docker/install_linux.sh check
.scripts/docker/install_linux.sh status
.scripts/docker/install_linux.sh verify

cd .scripts/docker
./analyze_disk_usage.sh --save
./analyze_merge_logs.sh --non-interactive --modules dev-iot-sink,biz-video,mw-nacos --lines 500 --save
```

### 常見問題

**服務啟動失敗**

```bash
docker ps -a
docker logs -f postgres-server
.scripts/docker/install_linux.sh logs
```

**網路問題（宿主機 IP 變更）**

```bash
export FORCE_NETWORK_RECREATE=true
.scripts/docker/install_linux.sh restart
```

**PostgreSQL / Redis**

```bash
.scripts/docker/fix_postgresql.sh
.scripts/docker/fix_redis.sh
```

**Docker 系統問題**

```bash
sudo .scripts/docker/diagnose_docker_systemd.sh diagnose
.scripts/docker/cleanup_docker_space.sh
```

**Kafka 消費組**

```bash
cd VIDEO && ./fix_kafka_consumer_group.sh
```

**切換規格後 WEB 異常**

```bash
cd WEB && ./install_linux.sh build
```

---

## 日誌位置

| 位置 | 說明 |
|------|------|
| `.scripts/docker/logs/` | 安裝腳本日誌；`merged_logs_*`、`disk_usage_*` 分析報告 |
| `.scripts/docker/standalone-logs/` | Nacos 等中介軟體落盤 |
| `.build-cache/device/logs/` | DEVICE 微服務 Spring 日誌 |
| `${EASYAIOT_MEDIA_ROOT:-/mnt/easyaiot-media}/srs.log` | SRS 串流媒體（媒體根由 `deploy_profile` 解析） |
| `WEB/logs/runtime.log` | WEB 執行日誌 |
| `docker logs <容器名>` | 容器 stdout（AI/VIDEO 常用） |

| 需求 | 互動 | 命令列 |
|------|------|--------|
| 多服務最近 500 行 | 分析 → 1 | `analyze-logs` 或 `analyze_merge_logs.sh --modules ...` |
| 單模組即時追蹤 | 部署 → 6 | `logs VIDEO` 或 `docker compose logs -f` |
| 安裝失敗 | — | `tail .scripts/docker/logs/install_linux_*.log` |

---

## 更新與卸載

```bash
git pull origin main
sudo .scripts/docker/install_linux.sh update
.scripts/docker/install_linux.sh verify
```

單模組：`cd AI && ./install_linux.sh update`

卸載：

```bash
sudo .scripts/docker/install_linux.sh clean   # ⚠️ 刪容器、映像、資料卷
```

---

## 架構參考

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEB 前端 (:8888)                              │
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

*文件版本：3.1 | 2026-07-08 | 腳本入口：`.scripts/docker/install_linux.sh`（無參數=互動；`<命令>`=直執）*
