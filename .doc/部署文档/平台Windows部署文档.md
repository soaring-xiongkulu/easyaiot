# EasyAIoT Platform Windows Local Deployment Guide

> Document Version: 1.0
> Update Date: December 6, 2025
> Compatible Systems: Windows 10/11


## Table of Contents

1. [System Overview](#1-system-overview)
2. [Environment Preparation](#2-environment-preparation)
3. [Middleware Deployment](#3-middleware-deployment)
4. [Service Startup](#4-service-startup)
5. [Video Streaming Configuration](#5-video-streaming-configuration)
6. [Troubleshooting Records & Solutions](#6-troubleshooting-records--solutions)
7. [Common Commands Summary](#7-common-commands-summary)
8. [Appendix](#8-appendix)


## 1. System Overview

### 1.1 Project Introduction

EasyAIoT is an Internet of Things + AI video analytics platform, supporting features such as camera integration, video stream forwarding, and AI algorithm analysis.

### 1.2 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         WEB Frontend (Vue3)                      │
│                         Port: 3100                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DEVICE Gateway (Spring Cloud)                 │
│                         Port: 48080                              │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  VIDEO Service│       │   AI Service  │       │ DEVICE Micro- │
│  Port: 6000   │       │  Port: 8100   │       │    services   │
│  (Python)     │       │  (Python)     │       │    (Java)     │
└───────────────┘       └───────────────┘       └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Middleware Layer                         │
│  PostgreSQL | Redis | Nacos | MinIO | Kafka | TDengine | SRS   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Service Component Description

| Service | Tech Stack | Port | Description |
|------|--------|------|------|
| WEB | Vue3 + Vite | 3100 | Frontend Interface |
| Gateway | Spring Cloud | 48080 | API Gateway |
| VIDEO | Python Flask | 6000 | Video Service |
| AI | Python FastAPI | 8100 | AI Inference Service |
| DEVICE | Spring Boot | Multiple | Device Management Microservices |


## 2. Environment Preparation

### 2.1 Hardware Requirements

- CPU: 4 cores or more
- RAM: 16GB or more (32GB recommended)
- Storage: 100GB or more available space
- Network: LAN accessible to cameras

### 2.2 Software Dependencies

#### 2.2.1 JDK 21

Download URL: https://adoptium.net/

Configure environment variables after installation:
```
JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.x
Add to Path: %JAVA_HOME%\bin
```

Verify installation:
```powershell
java -version
```

#### 2.2.2 Node.js 18+

Download URL: https://nodejs.org/

Verify installation:
```powershell
node -v
npm -v
```

#### 2.2.3 Python 3.10+ (Anaconda)

Download URL: https://www.anaconda.com/

Create a virtual environment:
```powershell
conda create -n easyaiot python=3.10
conda activate easyaiot
```

#### 2.2.4 FFmpeg

Download URL: https://www.gyan.dev/ffmpeg/builds/

Download `ffmpeg-release-essentials.zip`, extract to a specified directory, for example:
```
G:\ffmpeg-7.0.2-essentials_build\
```

Verify installation:
```powershell
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" -version
```

#### 2.2.5 Docker Desktop

Download URL: https://www.docker.com/products/docker-desktop/

Used for running the SRS streaming media server. Docker is only used for running the SRS streaming media server. All other services are deployed locally without Docker.

### 2.3 Project Path Planning

This document assumes the project path is:
```
F:\EASYLOT\easyaiot-V4.0.0\
```

Middleware installation paths:
```
F:\EASYLOT\PostgreSQL16\
F:\EASYLOT\Redis\
F:\EASYLOT\nacos\     #### Enable authentication    Search online for instructions
F:\EASYLOT\minio\  ##### The project has database or MinIO passwords. All passwords must match those in the project configuration. E.g., MinIO username: minioadmin, password: iot******
F:\EASYLOT\kafka\   ### Download yourself
F:\EASYLOT\TDengine\  #### Download yourself
```


## 3. Middleware Deployment

### 3.1 PostgreSQL

#### Installation Info
- Version: 16.x
- Port: 5432
- Username: postgres
- Password: `iot45722414822`

#### Startup Commands
```powershell
# Start PostgreSQL service
pg_ctl -D "F:\EASYLOT\PostgreSQL16\data" start

# Or use Windows service
net start postgresql-x64-16
```

#### Create Databases
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "CREATE DATABASE \"iot-system\";"
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "CREATE DATABASE \"iot-video20\";"
```

#### Verify Connection
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"
```


### 3.2 Redis

#### Installation Info
- Version: 7.x
- Port: 6379
- Password: `basiclab@iot975248395`

#### Startup Commands
```powershell
cd F:\EASYLOT\Redis
.\redis-server.exe redis.windows.conf
```

#### Verify Connection
```powershell
cd F:\EASYLOT\Redis
.\redis-cli.exe -a "basiclab@iot975248395" ping
# Should return PONG
```


### 3.3 Nacos

#### Installation Info
- Version: 2.x
- Port: 8848
- Username: nacos
- Password: `basiclab@iot78475418754`
- Namespace: local

#### Startup Commands
```powershell
cd F:\EASYLOT\nacos\bin
.\startup.cmd -m standalone
```

#### Access Address
```
http://localhost:8848/nacos
```

#### Configure Namespace
1. Log in to the Nacos console
2. Go to "Namespace Management"
3. Create a namespace, set ID to `local`


### 3.4 MinIO

#### Installation Info
- Version: Latest
- API Port: 9000
- Console Port: 9001
- Username: minioadmin
- Password: `basiclab@iot975248395`

#### Startup Commands
```powershell
cd F:\EASYLOT\minio
.\minio.exe server data --console-address ":9001"
```

#### Access Address
```
Console: http://localhost:9001
API: http://localhost:9000
```


### 3.5 Kafka

#### Installation Info
- Version: 3.x
- Port: 9092
- Zookeeper Port: 2181

#### Startup Commands (Start Zookeeper first)
```powershell
# Terminal 1: Start Zookeeper
cd F:\EASYLOT\kafka
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties

# Terminal 2: Start Kafka
cd F:\EASYLOT\kafka
.\bin\windows\kafka-server-start.bat .\config\server.properties
```


### 3.6 TDengine

#### Installation Info
- Version: 3.x
- Port: 6030 (Native connection), 6041 (REST API)
- Username: root
- Password: taosdata

#### Startup Commands
```powershell
# Start TDengine service
net start taosd

# Or start manually
cd F:\EASYLOT\TDengine
.\taosd.exe
```

#### Verify Connection
```powershell
cd F:\EASYLOT\TDengine
.\taos.exe -u root -p taosdata
```


### 3.7 SRS Streaming Media Server (Docker)

#### Installation Info
- Version: ossrs/srs:5
- RTMP Port: 1935
- HTTP-FLV Port: 8080
- HTTP API Port: 1985
- WebRTC Port: 8000/udp

#### Create Configuration File

Create configuration file `.scripts/srs/conf/simple.conf` in the project directory:
```conf
# SRS simplified configuration
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

#### Startup Commands
```powershell
docker run -d --name srs-server `
  -p 1935:1935 `
  -p 8080:8080 `
  -p 1985:1985 `
  -p 8000:8000/udp `
  -v "F:\EASYLOT\easyaiot-V4.0.0\.scripts\srs\conf\simple.conf:/usr/local/srs/conf/docker.conf" `
  ossrs/srs:5 ./objs/srs -c conf/docker.conf
```

#### Verify SRS Running Status
```powershell
# Check container status
docker ps | findstr srs

# Check SRS API
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/versions"
```

#### Common Docker Commands
```powershell
# Stop SRS
docker stop srs-server

# Start SRS
docker start srs-server

# View logs
docker logs srs-server

# Delete container (when recreation is needed)
docker rm srs-server
```


## 4. Service Startup

### 4.1 Startup Sequence

**Must start in the following order:**

1. Middleware (PostgreSQL → Redis → Nacos → MinIO → Kafka → TDengine → SRS)
2. DEVICE Microservices (Java)
3. VIDEO Service (Python)
4. AI Service (Python)
5. WEB Frontend (Vue)


### 4.2 DEVICE Microservices Startup

The DEVICE directory contains multiple Spring Boot microservices, which need to be started separately.

#### 4.2.1 Start Gateway Service
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-gateway
mvn spring-boot:run
# Or start with an IDE
```

#### 4.2.2 Start System Service
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-system\iot-system-biz
mvn spring-boot:run
```

#### 4.2.3 Start Infrastructure Service
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-infra\iot-infra-biz
mvn spring-boot:run
```

#### Configuration File Locations
- Gateway: `DEVICE/iot-gateway/src/main/resources/bootstrap-dev.yaml`
- System: `DEVICE/iot-system/iot-system-biz/src/main/resources/bootstrap-dev.yaml`
- Infrastructure: `DEVICE/iot-infra/iot-infra-biz/src/main/resources/bootstrap-dev.yaml`


### 4.3 VIDEO Service Startup

#### 4.3.1 Install Dependencies
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
pip install -r requirements.txt
```

#### 4.3.2 Configure Environment Variables

Edit the `VIDEO/.env` file, ensure the following configurations are correct:
```properties
# Database
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

# FFmpeg Path (Must be full path on Windows)
FFMPEG_PATH=G:/ffmpeg-7.0.2-essentials_build/bin/ffmpeg.exe

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

#### 4.3.3 Start Service
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
python run.py
```

Service starts listening on port: 6000


### 4.4 AI Service Startup

#### 4.4.1 Install Dependencies
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
pip install -r requirements.txt
```

#### 4.4.2 Start Service
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
python run.py
```

Service starts listening on port: 8100


### 4.5 WEB Frontend Startup

#### 4.5.1 Install Dependencies
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm install
# Or use pnpm
pnpm install
```

#### 4.5.2 Start Development Server
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm run dev
```

Access address after service starts: http://localhost:3100

#### 4.5.3 Login Information
- Username: admin
- Password: admin123



## 5. Video Streaming Configuration

### 5.1 Video Playback Flow

```
Camera(RTSP) → FFmpeg → SRS(RTMP) → HTTP-FLV → Frontend Player(flv.js)
```

### 5.2 Add Camera

1. Log in to the frontend system
2. Go to "Streaming Media" → "Device List"
3. Click "Add Video Source Device"
4. Select camera type (Hikvision/Dahua/Uniview/Custom)
5. Fill in camera information:
    - IP Address
    - Port (default 554)
    - Username
    - Password
6. Click OK, the system will automatically generate the RTSP address

### 5.3 Start Streaming

1. Find the added camera in the device list
2. Click the "Enable RTSP Forwarding" button
3. The system will automatically start FFmpeg to push the stream to SRS
4. Click the "Play" button to view the video

### 5.4 Manual Streaming Test

If automatic streaming fails, you can test manually:

```powershell
# Test streaming command
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/camera1"
```

### 5.5 Test Playback

After successful streaming, test playback in the following ways:

1. **SRS Built-in Player**
   ```
   http://127.0.0.1:8080/players/srs_player.html?autostart=true&stream=live/camera1.flv
   ```

2. **HTTP-FLV Address**
   ```
   http://127.0.0.1:8080/live/camera1.flv
   ```

3. **VLC Player**
    - Open VLC
    - Media → Open Network Stream
    - Input: `rtmp://127.0.0.1:1935/live/camera1`


## 6. Troubleshooting Records & Solutions

### 6.1 SRS Stream Name Length Limit

#### Problem Description
When using device ID (e.g., `1765004744998329500`) as stream name, FFmpeg reports an error during streaming:
```
Error opening output rtmp://127.0.0.1:1935/live/1765004744998329500: I/O error
```

But using a short name (e.g., `camera1`) works fine.

#### Solution
Modify the stream name generation logic to use `cam_` + first 8 characters of the device ID:
```python
# VIDEO/app/services/camera_service.py
short_stream_name = f"cam_{device_id[:8]}"
rtmp_stream = f"rtmp://127.0.0.1:1935/live/{short_stream_name}"
http_stream = f"http://127.0.0.1:8080/live/{short_stream_name}.flv"
```

#### Manual Fix for Existing Data
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "UPDATE device SET rtmp_stream = 'rtmp://127.0.0.1:1935/live/cam_' || SUBSTRING(id, 1, 8), http_stream = 'http://127.0.0.1:8080/live/cam_' || SUBSTRING(id, 1, 8) || '.flv';"
```


### 6.2 FFmpeg Path Issue (Windows)

#### Problem Description
VIDEO service reports an error during startup/streaming, cannot find `ffmpeg` command.

#### Root Cause Analysis
On Windows systems, if FFmpeg is not added to the system PATH, the full path must be used.

#### Solution
1. Configure the full FFmpeg path in `VIDEO/.env`:
   ```properties
   FFMPEG_PATH=G:/ffmpeg-7.0.2-essentials_build/bin/ffmpeg.exe
   ```

2. Modify the FFmpegDaemon class in `VIDEO/app/blueprints/camera.py`:
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


### 6.3 SRS Docker Configuration Daemon Issue

#### Problem Description
SRS Docker container exits immediately after startup.

#### Root Cause Analysis
`daemon on;` in the SRS configuration file causes SRS to run in the background, but Docker containers require a foreground process.

#### Solution
Set in the SRS configuration file:
```conf
daemon off;
```


### 6.4 Port 8080 Occupied

#### Problem Description
SRS's HTTP-FLV port 8080 conflicts with other services.

#### Solution
1. Check which process is occupying the port:
   ```powershell
   netstat -ano | findstr :8080
   ```

2. If another service is using it, modify the SRS configuration to use a different port, or stop the occupying service.

3. Ensure the Java gateway is using port 48080, not 8080.


### 6.5 flv.js Player Audio Issue

#### Problem Description
Frontend reports an error during video playback, or video cannot play.

#### Root Cause Analysis
The camera might not have an audio stream, but FFmpeg tries to encode audio causing an error.

#### Solution
1. Disable audio when FFmpeg streams:
   ```
   -an
   ```

2. Configure flv.js to disable audio:
   ```javascript
   flvPlayer = flvjs.createPlayer({
       type: 'flv',
       url: url,
       isLive: true,
       hasAudio: false,  // Disable audio
       hasVideo: true,
   });
   ```


### 6.6 Database Connection Failure

#### Problem Description
VIDEO service reports a database connection error on startup.

#### Troubleshooting Steps
1. Confirm PostgreSQL service is running:
   ```powershell
   $env:PGPASSWORD='iot45722414822'
   & "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"
   ```

2. Confirm the database `iot-video20` exists

3. Check the DATABASE_URL configuration in `VIDEO/.env`


### 6.7 Nacos Registration Failure

#### Problem Description
Services cannot register to Nacos on startup.

#### Troubleshooting Steps
1. Confirm Nacos service is running:
   ```
   http://localhost:8848/nacos
   ```

2. Confirm the namespace `local` has been created

3. Check the Nacos address and password in the configuration files


### 6.8 Frontend CAPTCHA Not Displaying

#### Problem Description
The CAPTCHA image on the frontend login page fails to load.

#### Root Cause Analysis
Usually caused by the DEVICE gateway service not starting, or incorrect port configuration.

#### Solution
1. Confirm the DEVICE gateway service is running (port 48080)
2. Confirm the API address configured in the frontend is correct
3. Check network request errors in the browser console


## 7. Common Commands Summary

### 7.1 Database Operations

```powershell
# Set password environment variable
$env:PGPASSWORD='iot45722414822'

# Connect to database
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20"

# View all databases
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"

# View device table
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "SELECT id, name, source, rtmp_stream, http_stream FROM device;"

# Update device stream address
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "UPDATE device SET http_stream = 'http://127.0.0.1:8080/live/cam_12345678.flv' WHERE id = '1234567890';"
```

### 7.2 SRS Operations

```powershell
# Check SRS container status
docker ps | findstr srs

# View SRS logs
docker logs srs-server

# Restart SRS
docker restart srs-server

# View current stream list
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/streams/" | ConvertTo-Json

# Check SRS version
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/versions"
```

### 7.3 FFmpeg Streaming Test

```powershell
# Hikvision camera streaming test
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/test"

# Dahua camera streaming test
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/cam/realmonitor?channel=1&subtype=0" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/test"
```

### 7.4 Service Start/Stop

```powershell
# VIDEO service
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
python run.py

# AI service
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
python run.py

# WEB frontend
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm run dev
```


## 8. Appendix

### 8.1 Port Summary Table

| Service | Port | Protocol | Description |
|------|------|------|------|
| PostgreSQL | 5432 | TCP | Database |
| Redis | 6379 | TCP | Cache |
| Nacos | 8848 | HTTP | Service Registry |
| MinIO API | 9000 | HTTP | Object Storage API |
| MinIO Console | 9001 | HTTP | Object Storage Console |
| Kafka | 9092 | TCP | Message Queue |
| Zookeeper | 2181 | TCP | Kafka Dependency |
| TDengine | 6030 | TCP | Time-series DB Native Connection |
| TDengine REST | 6041 | HTTP | Time-series DB REST API |
| SRS RTMP | 1935 | TCP | RTMP Push/Pull |
| SRS HTTP-FLV | 8080 | HTTP | HTTP-FLV Playback |
| SRS API | 1985 | HTTP | SRS Management API |
| SRS WebRTC | 8000 | UDP | WebRTC |
| DEVICE Gateway | 48080 | HTTP | Java Gateway |
| VIDEO | 6000 | HTTP | Video Service |
| AI | 8100 | HTTP | AI Service |
| WEB | 3100 | HTTP | Frontend Dev Server |

### 8.2 Password Summary Table

| Service | Username | Password |
|------|--------|------|
| PostgreSQL | postgres | iot45722414822 |
| Redis | - | basiclab@iot975248395 |
| Nacos | nacos | basiclab@iot78475418754 |
| MinIO | minioadmin | basiclab@iot975248395 |
| TDengine | root | taosdata |
| WEB Frontend | admin | admin123 |
| Test Camera | admin | sr336699 |

### 8.3 Camera RTSP Address Formats

#### Hikvision
```
rtsp://username:password@IP:554/Streaming/Channels/101  # Main stream
rtsp://username:password@IP:554/Streaming/Channels/102  # Sub stream
```

#### Dahua
```
rtsp://username:password@IP:554/cam/realmonitor?channel=1&subtype=0  # Main stream
rtsp://username:password@IP:554/cam/realmonitor?channel=1&subtype=1  # Sub stream
```

#### Uniview
```
rtsp://username:password@IP:554/unicast/c1/s0/live  # Main stream
rtsp://username:password@IP:554/unicast/c1/s1/live  # Sub stream
```

### 8.4 Frequently Asked Questions (FAQ)

**Q: Frontend page won't open?**
A: Check if the WEB service is started, if port 3100 is occupied.

**Q: Network error when logging in?**
A: Check if the DEVICE gateway service is started, if port 48080 is working.

**Q: Video playback shows black screen?**
A:
1. Check if SRS is running: `docker ps | findstr srs`
2. Check if there is any stream: Visit `http://127.0.0.1:1985/api/v1/streams/`
3. Test the manual streaming command to see if it works

**Q: Streaming fails?**
A:
1. Check if the FFmpeg path is correct
2. Check if the camera RTSP address is accessible
3. Check if SRS is running
4. Check if the stream name is too long

**Q: Service fails to register with Nacos?**
A:
1. Check if Nacos is running
2. Check if the namespace `local` exists
3. Check if the password is correct


> End of Document
> If you have any questions, please contact AI