# EasyAIoT 平台 Windows 本地部署指南

> 文檔版本：1.0
> 更新日期：2025年12月6日
> 適用系統：Windows 10/11


## 目錄

1. [系統概述](#1-系統概述)
2. [環境準備](#2-環境準備)
3. [中間件部署](#3-中間件部署)
4. [服務啟動](#4-服務啟動)
5. [視頻流媒體配置](#5-視頻流媒體配置)
6. [踩坑記錄與解決方案](#6-踩坑記錄與解決方案)
7. [常用命令匯總](#7-常用命令匯總)
8. [附錄](#8-附錄)


## 1. 系統概述

### 1.1 項目簡介

EasyAIoT 是一個物聯網+AI視頻分析平台，支持攝像頭接入、視頻流轉發、AI算法分析等功能。

### 1.2 系統架構

```
┌─────────────────────────────────────────────────────────────────┐
│                         WEB 前端 (Vue3)                          │
│                         端口: 3100                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DEVICE 網關 (Spring Cloud)                    │
│                         端口: 48080                              │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  VIDEO 服務   │       │   AI 服務     │       │ DEVICE 微服務 │
│  端口: 6000   │       │  端口: 8100   │       │  多個微服務   │
│  (Python)     │       │  (Python)     │       │  (Java)       │
└───────────────┘       └───────────────┘       └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          中間件層                                │
│  PostgreSQL | Redis | Nacos | MinIO | Kafka | TDengine | SRS   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 服務組件說明

| 服務 | 技術棧 | 端口 | 說明 |
|------|--------|------|------|
| WEB | Vue3 + Vite | 3100 | 前端界面 |
| Gateway | Spring Cloud | 48080 | API網關 |
| VIDEO | Python Flask | 6000 | 視頻服務 |
| AI | Python FastAPI | 8100 | AI推理服務 |
| DEVICE | Spring Boot | 多個 | 設備管理微服務 |


## 2. 環境準備

### 2.1 硬件要求

- CPU: 4核以上
- 內存: 16GB以上（推薦32GB）
- 硬盤: 100GB以上可用空間
- 網絡: 能訪問攝像頭的局域網

### 2.2 軟件依賴

#### 2.2.1 JDK 21

下載地址：https://adoptium.net/

安裝後配置環境變量：
```
JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.x
Path 添加: %JAVA_HOME%\bin
```

驗證安裝：
```powershell
java -version
```

#### 2.2.2 Node.js 18+

下載地址：https://nodejs.org/

驗證安裝：
```powershell
node -v
npm -v
```

#### 2.2.3 Python 3.10+ (Anaconda)

下載地址：https://www.anaconda.com/

創建虛擬環境：
```powershell
conda create -n easyaiot python=3.10
conda activate easyaiot
```

#### 2.2.4 FFmpeg

下載地址：https://www.gyan.dev/ffmpeg/builds/

下載 `ffmpeg-release-essentials.zip`，解壓到指定目錄，例如：
```
G:\ffmpeg-7.0.2-essentials_build\
```

驗證安裝：
```powershell
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" -version
```

#### 2.2.5 Docker Desktop

下載地址：https://www.docker.com/products/docker-desktop/

用於運行 SRS 流媒體服務器。   docker僅用於運行SRS流媒體服務器  其他服務全部本地部署不適用docker

### 2.3 項目路徑規劃

本文檔假設項目路徑為：
```
F:\EASYLOT\easyaiot-V4.0.0\
```

中間件安裝路徑：
```
F:\EASYLOT\PostgreSQL16\
F:\EASYLOT\Redis\
F:\EASYLOT\nacos\     ####要開啟鑒權   自行百度
F:\EASYLOT\minio\  #####項目裡邊有數據庫或者說minio的密碼  所有密碼都要和項目的配套一至  如minion  賬號：minionminion 密碼iot******
F:\EASYLOT\kafka\   ###自行下載
F:\EASYLOT\TDengine\  ####自行下載
```


## 3. 中間件部署

### 3.1 PostgreSQL

#### 安裝信息
- 版本：16.x
- 端口：5432
- 用戶名：postgres
- 密碼：`iot45722414822`

#### 啟動命令
```powershell
# 啟動 PostgreSQL 服務
pg_ctl -D "F:\EASYLOT\PostgreSQL16\data" start

# 或者使用 Windows 服務
net start postgresql-x64-16
```

#### 創建數據庫
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "CREATE DATABASE \"iot-system\";"
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "CREATE DATABASE \"iot-video20\";"
```

#### 驗證連接
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"
```


### 3.2 Redis

#### 安裝信息
- 版本：7.x
- 端口：6379
- 密碼：`basiclab@iot975248395`

#### 啟動命令
```powershell
cd F:\EASYLOT\Redis
.\redis-server.exe redis.windows.conf
```

#### 驗證連接
```powershell
cd F:\EASYLOT\Redis
.\redis-cli.exe -a "basiclab@iot975248395" ping
# 應返回 PONG
```


### 3.3 Nacos

#### 安裝信息
- 版本：2.x
- 端口：8848
- 用戶名：nacos
- 密碼：`basiclab@iot78475418754`
- 命名空間：local

#### 啟動命令
```powershell
cd F:\EASYLOT\nacos\bin
.\startup.cmd -m standalone
```

#### 訪問地址
```
http://localhost:8848/nacos
```

#### 配置命名空間
1. 登錄 Nacos 控制台
2. 進入「命名空間」
3. 創建命名空間，ID 設置為 `local`


### 3.4 MinIO

#### 安裝信息
- 版本：最新版
- API端口：9000
- 控制台端口：9001
- 用戶名：minioadmin
- 密碼：`basiclab@iot975248395`

#### 啟動命令
```powershell
cd F:\EASYLOT\minio
.\minio.exe server data --console-address ":9001"
```

#### 訪問地址
```
控制台：http://localhost:9001
API：http://localhost:9000
```


### 3.5 Kafka

#### 安裝信息
- 版本：3.x
- 端口：9092
- Zookeeper端口：2181

#### 啟動命令（需要先啟動 Zookeeper）
```powershell
# 終端1：啟動 Zookeeper
cd F:\EASYLOT\kafka
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties

# 終端2：啟動 Kafka
cd F:\EASYLOT\kafka
.\bin\windows\kafka-server-start.bat .\config\server.properties
```


### 3.6 TDengine

#### 安裝信息
- 版本：3.x
- 端口：6030（原生連接）、6041（REST API）
- 用戶名：root
- 密碼：taosdata

#### 啟動命令
```powershell
# 啟動 TDengine 服務
net start taosd

# 或者手動啟動
cd F:\EASYLOT\TDengine
.\taosd.exe
```

#### 驗證連接
```powershell
cd F:\EASYLOT\TDengine
.\taos.exe -u root -p taosdata
```


### 3.7 SRS 流媒體服務器（Docker）

#### 安裝信息
- 版本：ossrs/srs:5
- RTMP端口：1935
- HTTP-FLV端口：8080
- HTTP API端口：1985
- WebRTC端口：8000/udp

#### 創建配置文件

在項目目錄創建配置文件 `.scripts/srs/conf/simple.conf`：
```conf
# SRS 簡化配置
listen              1935;
max_connections     1000;
daemon              off;

http_server {
    enabled         on;
    listen          8080;
    dir             ./objs/nginx/html;
}

http_api {
    enabled         on;
    listen          1985;
}

vhost __defaultVhost__ {
    http_remux {
        enabled     on;
        mount       [vhost]/[app]/[stream].flv;
    }
}
```

#### 啟動命令
```powershell
docker run -d --name srs-server `
  -p 1935:1935 `
  -p 8080:8080 `
  -p 1985:1985 `
  -p 8000:8000/udp `
  -v "F:\EASYLOT\easyaiot-V4.0.0\.scripts\srs\conf\simple.conf:/usr/local/srs/conf/docker.conf" `
  ossrs/srs:5 ./objs/srs -c conf/docker.conf
```

#### 驗證 SRS 運行狀態
```powershell
# 查看容器狀態
docker ps | findstr srs

# 查看 SRS API
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/versions"
```

#### 常用 Docker 命令
```powershell
# 停止 SRS
docker stop srs-server

# 啟動 SRS
docker start srs-server

# 查看日誌
docker logs srs-server

# 刪除容器（需要重新創建時）
docker rm srs-server
```


## 4. 服務啟動

### 4.1 啟動順序

**必須按以下順序啟動：**

1. 中間件（PostgreSQL → Redis → Nacos → MinIO → Kafka → TDengine → SRS）
2. DEVICE 微服務（Java）
3. VIDEO 服務（Python）
4. AI 服務（Python）
5. WEB 前端（Vue）


### 4.2 DEVICE 微服務啟動

DEVICE 目錄下有多個 Spring Boot 微服務，需要分別啟動。

#### 4.2.1 啟動網關服務
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-gateway
mvn spring-boot:run
# 或者使用 IDE 啟動
```

#### 4.2.2 啟動系統服務
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-system\iot-system-biz
mvn spring-boot:run
```

#### 4.2.3 啟動基礎設施服務
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-infra\iot-infra-biz
mvn spring-boot:run
```

#### 配置文件位置
- 網關：`DEVICE/iot-gateway/src/main/resources/bootstrap-dev.yaml`
- 系統：`DEVICE/iot-system/iot-system-biz/src/main/resources/bootstrap-dev.yaml`
- 基礎設施：`DEVICE/iot-infra/iot-infra-biz/src/main/resources/bootstrap-dev.yaml`


### 4.3 VIDEO 服務啟動

#### 4.3.1 安裝依賴
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
pip install -r requirements.txt
```

#### 4.3.2 配置環境變量

編輯 `VIDEO/.env` 文件，確保以下配置正確：
```properties
# 數據庫
DATABASE_URL=postgresql://postgres:iot45722414822@localhost:5432/iot-video20

# Nacos
NACOS_SERVER=localhost:8848
NACOS_NAMESPACE=local
NACOS_USERNAME=nacos
NACOS_PASSWORD=basiclab@iot78475418754

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=basiclab@iot975248395

# FFmpeg 路徑（Windows 必須配置完整路徑）
FFMPEG_PATH=G:/ffmpeg-7.0.2-essentials_build/bin/ffmpeg.exe

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

#### 4.3.3 啟動服務
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
python run.py
```

服務啟動後監聽端口：6000


### 4.4 AI 服務啟動

#### 4.4.1 安裝依賴
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
pip install -r requirements.txt
```

#### 4.4.2 啟動服務
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
python run.py
```

服務啟動後監聽端口：8100


### 4.5 WEB 前端啟動

#### 4.5.1 安裝依賴
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm install
# 或者使用 pnpm
pnpm install
```

#### 4.5.2 啟動開發服務器
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm run dev
```

服務啟動後訪問地址：http://localhost:3100

#### 4.5.3 登錄信息
- 用戶名：admin
- 密碼：admin123


## 5. 視頻流媒體配置

### 5.1 視頻播放流程

```
攝像頭(RTSP) → FFmpeg → SRS(RTMP) → HTTP-FLV → 前端播放器(flv.js)
```

### 5.2 添加攝像頭

1. 登錄前端系統
2. 進入「流媒體」→「設備列表」
3. 點擊「新增視頻源設備」
4. 選擇攝像頭類型（海康/大華/宇視/自定義）
5. 填寫攝像頭信息：
   - IP地址
   - 端口（默認554）
   - 用戶名
   - 密碼
6. 點擊確定，系統會自動生成 RTSP 地址

### 5.3 啟動推流

1. 在設備列表中找到已添加的攝像頭
2. 點擊「啟用RTSP轉發」按鈕
3. 系統會自動啟動 FFmpeg 推流到 SRS
4. 點擊「播放」按鈕查看視頻

### 5.4 手動測試推流

如果自動推流失敗，可以手動測試：

```powershell
# 測試推流命令
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/camera1"
```

### 5.5 測試播放

推流成功後，可以通過以下方式測試播放：

1. **SRS 自帶播放器**
   ```
   http://127.0.0.1:8080/players/srs_player.html?autostart=true&stream=live/camera1.flv
   ```

2. **HTTP-FLV 地址**
   ```
   http://127.0.0.1:8080/live/camera1.flv
   ```

3. **VLC 播放器**
   - 打開 VLC
   - 媒體 → 打開網絡串流
   - 輸入：`rtmp://127.0.0.1:1935/live/camera1`


## 6. 踩坑記錄與解決方案

### 6.1 SRS 流名稱長度限制

#### 問題描述
使用設備ID（如 `1765004744998329500`）作為流名稱時，FFmpeg 推流報錯：
```
Error opening output rtmp://127.0.0.1:1935/live/1765004744998329500: I/O error
```

但使用短名稱（如 `camera1`）可以正常推流。

#### 解決方案
修改流名稱生成邏輯，使用 `cam_` + 設備ID前8位：
```python
# VIDEO/app/services/camera_service.py
short_stream_name = f"cam_{device_id[:8]}"
rtmp_stream = f"rtmp://127.0.0.1:1935/live/{short_stream_name}"
http_stream = f"http://127.0.0.1:8080/live/{short_stream_name}.flv"
```

#### 手動修復已有數據
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "UPDATE device SET rtmp_stream = 'rtmp://127.0.0.1:1935/live/cam_' || SUBSTRING(id, 1, 8), http_stream = 'http://127.0.0.1:8080/live/cam_' || SUBSTRING(id, 1, 8) || '.flv';"
```


### 6.2 FFmpeg 路徑問題（Windows）

#### 問題描述
VIDEO 服務啟動推流時報錯，找不到 `ffmpeg` 命令。

#### 原因分析
Windows 系統中，如果 FFmpeg 沒有添加到系統 PATH，需要使用完整路徑。

#### 解決方案
1. 在 `VIDEO/.env` 中配置 FFmpeg 完整路徑：
   ```properties
   FFMPEG_PATH=G:/ffmpeg-7.0.2-essentials_build/bin/ffmpeg.exe
   ```

2. 修改 `VIDEO/app/blueprints/camera.py` 中的 FFmpegDaemon 類：
   ```python
   ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')
   ffmpeg_cmd = [
       ffmpeg_path,
       '-re',
       '-rtsp_transport', 'tcp',
       '-i', self.source,
       '-c:v', 'copy',
       '-an',
       '-f', 'flv',
       self.rtmp_stream
   ]
   ```


### 6.3 SRS Docker 配置 daemon 問題

#### 問題描述
SRS Docker 容器啟動後立即退出。

#### 原因分析
SRS 配置文件中 `daemon on;` 會導致 SRS 進入後台運行，但 Docker 容器需要前台進程。

#### 解決方案
在 SRS 配置文件中設置：
```conf
daemon off;
```


### 6.4 端口 8080 被佔用

#### 問題描述
SRS 的 HTTP-FLV 端口 8080 與其他服務衝突。

#### 解決方案
1. 檢查佔用端口的進程：
   ```powershell
   netstat -ano | findstr :8080
   ```

2. 如果是其他服務佔用，可以修改 SRS 配置使用其他端口，或者停止佔用的服務。

3. 確保 Java 網關使用的是 48080 端口，不是 8080。


### 6.5 flv.js 播放器音頻問題

#### 問題描述
前端播放視頻時報錯，或者視頻無法播放。

#### 原因分析
攝像頭可能沒有音頻流，但 FFmpeg 嘗試編碼音頻導致錯誤。

#### 解決方案
1. FFmpeg 推流時禁用音頻：
   ```
   -an
   ```

2. flv.js 配置禁用音頻：
   ```javascript
   flvPlayer = flvjs.createPlayer({
       type: 'flv',
       url: url,
       isLive: true,
       hasAudio: false,  // 禁用音頻
       hasVideo: true,
   });
   ```


### 6.6 數據庫連接失敗

#### 問題描述
VIDEO 服務啟動時報數據庫連接錯誤。

#### 排查步驟
1. 確認 PostgreSQL 服務已啟動：
   ```powershell
   $env:PGPASSWORD='iot45722414822'
   & "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"
   ```

2. 確認數據庫 `iot-video20` 存在

3. 檢查 `VIDEO/.env` 中的 DATABASE_URL 配置


### 6.7 Nacos 註冊失敗

#### 問題描述
服務啟動時無法註冊到 Nacos。

#### 排查步驟
1. 確認 Nacos 服務已啟動：
   ```
   http://localhost:8848/nacos
   ```

2. 確認命名空間 `local` 已創建

3. 檢查配置文件中的 Nacos 地址和密碼


### 6.8 前端驗證碼不顯示

#### 問題描述
前端登錄頁面驗證碼圖片無法加載。

#### 原因分析
通常是網關服務未啟動，或者端口配置錯誤。

#### 解決方案
1. 確認 DEVICE 網關服務已啟動（端口 48080）
2. 確認前端配置的 API 地址正確
3. 檢查瀏覽器控制台的網絡請求錯誤


## 7. 常用命令匯總

### 7.1 數據庫操作

```powershell
# 設置密碼環境變量
$env:PGPASSWORD='iot45722414822'

# 連接數據庫
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20"

# 查看所有數據庫
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"

# 查看設備表
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "SELECT id, name, source, rtmp_stream, http_stream FROM device;"

# 更新設備流地址
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "UPDATE device SET http_stream = 'http://127.0.0.1:8080/live/cam_12345678.flv' WHERE id = '1234567890';"
```

### 7.2 SRS 操作

```powershell
# 查看 SRS 容器狀態
docker ps | findstr srs

# 查看 SRS 日誌
docker logs srs-server

# 重啟 SRS
docker restart srs-server

# 查看當前推流列表
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/streams/" | ConvertTo-Json

# 查看 SRS 版本
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/versions"
```

### 7.3 FFmpeg 推流測試

```powershell
# 海康攝像頭推流測試
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/test"

# 大華攝像頭推流測試
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/cam/realmonitor?channel=1&subtype=0" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/test"
```

### 7.4 服務啟停

```powershell
# VIDEO 服務
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
python run.py

# AI 服務
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
python run.py

# WEB 前端
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm run dev
```


## 8. 附錄

### 8.1 端口匯總表

| 服務 | 端口 | 協議 | 說明 |
|------|------|------|------|
| PostgreSQL | 5432 | TCP | 數據庫 |
| Redis | 6379 | TCP | 緩存 |
| Nacos | 8848 | HTTP | 服務註冊中心 |
| MinIO API | 9000 | HTTP | 對象存儲 API |
| MinIO Console | 9001 | HTTP | 對象存儲控制台 |
| Kafka | 9092 | TCP | 消息隊列 |
| Zookeeper | 2181 | TCP | Kafka 依賴 |
| TDengine | 6030 | TCP | 時序數據庫原生連接 |
| TDengine REST | 6041 | HTTP | 時序數據庫 REST API |
| SRS RTMP | 1935 | TCP | RTMP 推流/拉流 |
| SRS HTTP-FLV | 8080 | HTTP | HTTP-FLV 播放 |
| SRS API | 1985 | HTTP | SRS 管理 API |
| SRS WebRTC | 8000 | UDP | WebRTC |
| DEVICE Gateway | 48080 | HTTP | Java 網關 |
| VIDEO | 6000 | HTTP | 視頻服務 |
| AI | 8100 | HTTP | AI 服務 |
| WEB | 3100 | HTTP | 前端開發服務器 |

### 8.2 密碼匯總表

| 服務 | 用戶名 | 密碼 |
|------|--------|------|
| PostgreSQL | postgres | iot45722414822 |
| Redis | - | basiclab@iot975248395 |
| Nacos | nacos | basiclab@iot78475418754 |
| MinIO | minioadmin | basiclab@iot975248395 |
| TDengine | root | taosdata |
| WEB 前端 | admin | admin123 |
| 測試攝像頭 | admin | sr336699 |

### 8.3 攝像頭 RTSP 地址格式

#### 海康威視
```
rtsp://用戶名:密碼@IP:554/Streaming/Channels/101  # 主碼流
rtsp://用戶名:密碼@IP:554/Streaming/Channels/102  # 子碼流
```

#### 大華
```
rtsp://用戶名:密碼@IP:554/cam/realmonitor?channel=1&subtype=0  # 主碼流
rtsp://用戶名:密碼@IP:554/cam/realmonitor?channel=1&subtype=1  # 子碼流
```

#### 宇視
```
rtsp://用戶名:密碼@IP:554/unicast/c1/s0/live  # 主碼流
rtsp://用戶名:密碼@IP:554/unicast/c1/s1/live  # 子碼流
```

### 8.4 常見問題 FAQ

**Q: 前端頁面打不開？**
A: 檢查 WEB 服務是否啟動，端口 3100 是否被佔用。

**Q: 登錄時提示網絡錯誤？**
A: 檢查 DEVICE 網關服務是否啟動，端口 48080 是否正常。

**Q: 視頻播放黑屏？**
A: 
1. 檢查 SRS 是否運行：`docker ps | findstr srs`
2. 檢查是否有推流：訪問 `http://127.0.0.1:1985/api/v1/streams/`
3. 手動測試推流命令是否正常

**Q: 推流失敗？**
A: 
1. 檢查 FFmpeg 路徑是否正確
2. 檢查攝像頭 RTSP 地址是否可訪問
3. 檢查 SRS 是否運行
4. 檢查流名稱是否過長

**Q: 服務註冊到 Nacos 失敗？**
A: 
1. 檢查 Nacos 是否啟動
2. 檢查命名空間 `local` 是否存在
3. 檢查密碼是否正確


> 文檔結束
> 如有問題，請聯繫AI

