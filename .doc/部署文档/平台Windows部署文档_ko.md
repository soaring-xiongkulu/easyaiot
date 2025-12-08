# EasyAIoT 플랫폼 Windows 로컬 배포 가이드

> 문서 버전: 1.0
> 업데이트 날짜: 2025년 12월 6일
> 지원 시스템: Windows 10/11


## 목차

1. [시스템 개요](#1-시스템-개요)
2. [환경 준비](#2-환경-준비)
3. [미들웨어 배포](#3-미들웨어-배포)
4. [서비스 시작](#4-서비스-시작)
5. [비디오 스트리밍 구성](#5-비디오-스트리밍-구성)
6. [문제 기록 및 해결 방법](#6-문제-기록-및-해결-방법)
7. [자주 사용하는 명령어 요약](#7-자주-사용하는-명령어-요약)
8. [부록](#8-부록)


## 1. 시스템 개요

### 1.1 프로젝트 소개

EasyAIoT는 IoT + AI 비디오 분석 플랫폼으로, 카메라 연결, 비디오 스트림 전송, AI 알고리즘 분석 등의 기능을 지원합니다.

### 1.2 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         WEB 前端 (Vue3)                          │
│                         端口: 3100                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DEVICE 网关 (Spring Cloud)                    │
│                         端口: 48080                              │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  VIDEO 服务   │       │   AI 服务     │       │ DEVICE 微服务 │
│  端口: 6000   │       │  端口: 8100   │       │  多个微服务   │
│  (Python)     │       │  (Python)     │       │  (Java)       │
└───────────────┘       └───────────────┘       └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          中间件层                                │
│  PostgreSQL | Redis | Nacos | MinIO | Kafka | TDengine | SRS   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 서비스 구성 요소 설명

| 서비스 | 기술 스택 | 포트 | 설명 |
|--------|----------|------|------|
| WEB | Vue3 + Vite | 3100 | 프론트엔드 인터페이스 |
| Gateway | Spring Cloud | 48080 | API 게이트웨이 |
| VIDEO | Python Flask | 6000 | 비디오 서비스 |
| AI | Python FastAPI | 8100 | AI 추론 서비스 |
| DEVICE | Spring Boot | 여러 개 | 디바이스 관리 마이크로서비스 |


## 2. 환경 준비

### 2.1 하드웨어 요구사항

- CPU: 4코어 이상
- 메모리: 16GB 이상 (권장 32GB)
- 하드 디스크: 100GB 이상의 사용 가능한 공간
- 네트워크: 카메라에 액세스할 수 있는 로컬 네트워크

### 2.2 소프트웨어 종속성

#### 2.2.1 JDK 21

다운로드 주소: https://adoptium.net/

설치 후 환경 변수 구성:
```
JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.x
Path 添加: %JAVA_HOME%\bin
```

설치 확인:
```powershell
java -version
```

#### 2.2.2 Node.js 18+

다운로드 주소: https://nodejs.org/

설치 확인:
```powershell
node -v
npm -v
```

#### 2.2.3 Python 3.10+ (Anaconda)

다운로드 주소: https://www.anaconda.com/

가상 환경 생성:
```powershell
conda create -n easyaiot python=3.10
conda activate easyaiot
```

#### 2.2.4 FFmpeg

다운로드 주소: https://www.gyan.dev/ffmpeg/builds/

`ffmpeg-release-essentials.zip`을 다운로드하고 지정된 디렉토리에 압축 해제, 예:
```
G:\ffmpeg-7.0.2-essentials_build\
```

설치 확인:
```powershell
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" -version
```

#### 2.2.5 Docker Desktop

다운로드 주소: https://www.docker.com/products/docker-desktop/

SRS 스트리밍 서버 실행에 사용됩니다. Docker는 SRS 스트리밍 서버 실행에만 사용되며, 다른 모든 서비스는 Docker를 사용하지 않고 로컬에 배포됩니다.

### 2.3 프로젝트 경로 계획

이 문서는 프로젝트 경로를 다음과 같이 가정합니다:
```
F:\EASYLOT\easyaiot-V4.0.0\
```

미들웨어 설치 경로:
```
F:\EASYLOT\PostgreSQL16\
F:\EASYLOT\Redis\
F:\EASYLOT\nacos\     ####要开启鉴权   自行百度
F:\EASYLOT\minio\  #####项目里边有数据库或者说minio的密码  所有密码都要和项目的配套一至  如minion  账号：minionminion 密码iot******
F:\EASYLOT\kafka\   ###自行下载
F:\EASYLOT\TDengine\  ####自行下载
```


## 3. 미들웨어 배포

### 3.1 PostgreSQL

#### 설치 정보
- 버전: 16.x
- 포트: 5432
- 사용자 이름: postgres
- 비밀번호: `iot45722414822`

#### 시작 명령
```powershell
# PostgreSQL 서비스 시작
pg_ctl -D "F:\EASYLOT\PostgreSQL16\data" start

# 또는 Windows 서비스 사용
net start postgresql-x64-16
```

#### 데이터베이스 생성
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "CREATE DATABASE \"iot-system\";"
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "CREATE DATABASE \"iot-video20\";"
```

#### 연결 확인
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"
```


### 3.2 Redis

#### 설치 정보
- 버전: 7.x
- 포트: 6379
- 비밀번호: `basiclab@iot975248395`

#### 시작 명령
```powershell
cd F:\EASYLOT\Redis
.\redis-server.exe redis.windows.conf
```

#### 연결 확인
```powershell
cd F:\EASYLOT\Redis
.\redis-cli.exe -a "basiclab@iot975248395" ping
# PONG을 반환해야 합니다
```


### 3.3 Nacos

#### 설치 정보
- 버전: 2.x
- 포트: 8848
- 사용자 이름: nacos
- 비밀번호: `basiclab@iot78475418754`
- 네임스페이스: local

#### 시작 명령
```powershell
cd F:\EASYLOT\nacos\bin
.\startup.cmd -m standalone
```

#### 액세스 주소
```
http://localhost:8848/nacos
```

#### 네임스페이스 구성
1. Nacos 콘솔에 로그인
2. "네임스페이스"로 이동
3. 네임스페이스를 생성하고 ID를 `local`로 설정


### 3.4 MinIO

#### 설치 정보
- 버전: 최신 버전
- API 포트: 9000
- 콘솔 포트: 9001
- 사용자 이름: minioadmin
- 비밀번호: `basiclab@iot975248395`

#### 시작 명령
```powershell
cd F:\EASYLOT\minio
.\minio.exe server data --console-address ":9001"
```

#### 액세스 주소
```
콘솔: http://localhost:9001
API: http://localhost:9000
```


### 3.5 Kafka

#### 설치 정보
- 버전: 3.x
- 포트: 9092
- Zookeeper 포트: 2181

#### 시작 명령 (먼저 Zookeeper를 시작해야 함)
```powershell
# 터미널 1: Zookeeper 시작
cd F:\EASYLOT\kafka
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties

# 터미널 2: Kafka 시작
cd F:\EASYLOT\kafka
.\bin\windows\kafka-server-start.bat .\config\server.properties
```


### 3.6 TDengine

#### 설치 정보
- 버전: 3.x
- 포트: 6030 (네이티브 연결), 6041 (REST API)
- 사용자 이름: root
- 비밀번호: taosdata

#### 시작 명령
```powershell
# TDengine 서비스 시작
net start taosd

# 또는 수동 시작
cd F:\EASYLOT\TDengine
.\taosd.exe
```

#### 연결 확인
```powershell
cd F:\EASYLOT\TDengine
.\taos.exe -u root -p taosdata
```


### 3.7 SRS 스트리밍 서버 (Docker)

#### 설치 정보
- 버전: ossrs/srs:5
- RTMP 포트: 1935
- HTTP-FLV 포트: 8080
- HTTP API 포트: 1985
- WebRTC 포트: 8000/udp

#### 구성 파일 생성

프로젝트 디렉토리에 구성 파일 `.scripts/srs/conf/simple.conf` 생성:
```conf
# SRS 간소화 구성
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

#### 시작 명령
```powershell
docker run -d --name srs-server `
  -p 1935:1935 `
  -p 8080:8080 `
  -p 1985:1985 `
  -p 8000:8000/udp `
  -v "F:\EASYLOT\easyaiot-V4.0.0\.scripts\srs\conf\simple.conf:/usr/local/srs/conf/docker.conf" `
  ossrs/srs:5 ./objs/srs -c conf/docker.conf
```

#### SRS 실행 상태 확인
```powershell
# 컨테이너 상태 확인
docker ps | findstr srs

# SRS API 확인
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/versions"
```

#### 자주 사용하는 Docker 명령
```powershell
# SRS 중지
docker stop srs-server

# SRS 시작
docker start srs-server

# 로그 보기
docker logs srs-server

# 컨테이너 삭제 (다시 생성해야 할 때)
docker rm srs-server
```


## 4. 서비스 시작

### 4.1 시작 순서

**다음 순서로 시작해야 합니다:**

1. 미들웨어 (PostgreSQL → Redis → Nacos → MinIO → Kafka → TDengine → SRS)
2. DEVICE 마이크로서비스 (Java)
3. VIDEO 서비스 (Python)
4. AI 서비스 (Python)
5. WEB 프론트엔드 (Vue)


### 4.2 DEVICE 마이크로서비스 시작

DEVICE 디렉토리에는 여러 Spring Boot 마이크로서비스가 있으며 각각 시작해야 합니다.

#### 4.2.1 게이트웨이 서비스 시작
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-gateway
mvn spring-boot:run
# 또는 IDE를 사용하여 시작
```

#### 4.2.2 시스템 서비스 시작
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-system\iot-system-biz
mvn spring-boot:run
```

#### 4.2.3 인프라 서비스 시작
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\DEVICE\iot-infra\iot-infra-biz
mvn spring-boot:run
```

#### 구성 파일 위치
- 게이트웨이: `DEVICE/iot-gateway/src/main/resources/bootstrap-dev.yaml`
- 시스템: `DEVICE/iot-system/iot-system-biz/src/main/resources/bootstrap-dev.yaml`
- 인프라: `DEVICE/iot-infra/iot-infra-biz/src/main/resources/bootstrap-dev.yaml`


### 4.3 VIDEO 서비스 시작

#### 4.3.1 종속성 설치
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
pip install -r requirements.txt
```

#### 4.3.2 환경 변수 구성

`VIDEO/.env` 파일을 편집하고 다음 구성이 올바른지 확인:
```properties
# 데이터베이스
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

# FFmpeg 경로 (Windows는 전체 경로를 구성해야 함)
FFMPEG_PATH=G:/ffmpeg-7.0.2-essentials_build/bin/ffmpeg.exe

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

#### 4.3.3 서비스 시작
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
python run.py
```

서비스 시작 후 포트 수신: 6000


### 4.4 AI 서비스 시작

#### 4.4.1 종속성 설치
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
pip install -r requirements.txt
```

#### 4.4.2 서비스 시작
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
python run.py
```

서비스 시작 후 포트 수신: 8100


### 4.5 WEB 프론트엔드 시작

#### 4.5.1 종속성 설치
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm install
# 또는 pnpm 사용
pnpm install
```

#### 4.5.2 개발 서버 시작
```powershell
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm run dev
```

서비스 시작 후 액세스 주소: http://localhost:3100

#### 4.5.3 로그인 정보
- 사용자 이름: admin
- 비밀번호: admin123


## 5. 비디오 스트리밍 구성

### 5.1 비디오 재생 프로세스

```
카메라(RTSP) → FFmpeg → SRS(RTMP) → HTTP-FLV → 프론트엔드 플레이어(flv.js)
```

### 5.2 카메라 추가

1. 프론트엔드 시스템에 로그인
2. "스트리밍" → "디바이스 목록"으로 이동
3. "새 비디오 소스 디바이스" 클릭
4. 카메라 유형 선택 (Hikvision/Dahua/Uniview/사용자 정의)
5. 카메라 정보 입력:
   - IP 주소
   - 포트 (기본값 554)
   - 사용자 이름
   - 비밀번호
6. 확인을 클릭하면 시스템이 자동으로 RTSP 주소를 생성합니다

### 5.3 스트리밍 시작

1. 디바이스 목록에서 추가한 카메라 찾기
2. "RTSP 전송 활성화" 버튼 클릭
3. 시스템이 자동으로 FFmpeg 스트리밍을 SRS로 시작합니다
4. "재생" 버튼을 클릭하여 비디오 보기

### 5.4 수동 스트리밍 테스트

자동 스트리밍이 실패하면 수동으로 테스트할 수 있습니다:

```powershell
# 스트리밍 테스트 명령
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/camera1"
```

### 5.5 재생 테스트

스트리밍이 성공한 후 다음 방법으로 재생을 테스트할 수 있습니다:

1. **SRS 내장 플레이어**
   ```
   http://127.0.0.1:8080/players/srs_player.html?autostart=true&stream=live/camera1.flv
   ```

2. **HTTP-FLV 주소**
   ```
   http://127.0.0.1:8080/live/camera1.flv
   ```

3. **VLC 플레이어**
   - VLC 열기
   - 미디어 → 네트워크 스트림 열기
   - 입력: `rtmp://127.0.0.1:1935/live/camera1`


## 6. 문제 기록 및 해결 방법

### 6.1 SRS 스트림 이름 길이 제한

#### 문제 설명
디바이스 ID(예: `1765004744998329500`)를 스트림 이름으로 사용하면 FFmpeg 스트리밍에서 오류가 발생합니다:
```
Error opening output rtmp://127.0.0.1:1935/live/1765004744998329500: I/O error
```

하지만 짧은 이름(예: `camera1`)을 사용하면 정상적으로 스트리밍됩니다.

#### 해결 방법
스트림 이름 생성 로직을 수정하여 `cam_` + 디바이스 ID의 처음 8자 사용:
```python
# VIDEO/app/services/camera_service.py
short_stream_name = f"cam_{device_id[:8]}"
rtmp_stream = f"rtmp://127.0.0.1:1935/live/{short_stream_name}"
http_stream = f"http://127.0.0.1:8080/live/{short_stream_name}.flv"
```

#### 기존 데이터 수동 수정
```powershell
$env:PGPASSWORD='iot45722414822'
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "UPDATE device SET rtmp_stream = 'rtmp://127.0.0.1:1935/live/cam_' || SUBSTRING(id, 1, 8), http_stream = 'http://127.0.0.1:8080/live/cam_' || SUBSTRING(id, 1, 8) || '.flv';"
```


### 6.2 FFmpeg 경로 문제 (Windows)

#### 문제 설명
VIDEO 서비스가 스트리밍을 시작할 때 오류가 발생하고 `ffmpeg` 명령을 찾을 수 없습니다.

#### 원인 분석
Windows 시스템에서 FFmpeg가 시스템 PATH에 추가되지 않은 경우 전체 경로를 사용해야 합니다.

#### 해결 방법
1. `VIDEO/.env`에서 FFmpeg 전체 경로 구성:
   ```properties
   FFMPEG_PATH=G:/ffmpeg-7.0.2-essentials_build/bin/ffmpeg.exe
   ```

2. `VIDEO/app/blueprints/camera.py`의 FFmpegDaemon 클래스 수정:
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


### 6.3 SRS Docker 구성 daemon 문제

#### 문제 설명
SRS Docker 컨테이너가 시작된 후 즉시 종료됩니다.

#### 원인 분석
SRS 구성 파일의 `daemon on;`은 SRS를 백그라운드로 실행하게 하지만 Docker 컨테이너는 포그라운드 프로세스가 필요합니다.

#### 해결 방법
SRS 구성 파일에서 설정:
```conf
daemon off;
```


### 6.4 포트 8080이 사용 중

#### 문제 설명
SRS의 HTTP-FLV 포트 8080이 다른 서비스와 충돌합니다.

#### 해결 방법
1. 포트를 사용하는 프로세스 확인:
   ```powershell
   netstat -ano | findstr :8080
   ```

2. 다른 서비스가 포트를 사용하는 경우 SRS 구성을 수정하여 다른 포트를 사용하거나 사용 중인 서비스를 중지할 수 있습니다.

3. Java 게이트웨이가 48080 포트를 사용하는지 확인하고 8080이 아닌지 확인합니다.


### 6.5 flv.js 플레이어 오디오 문제

#### 문제 설명
프론트엔드에서 비디오를 재생할 때 오류가 발생하거나 비디오를 재생할 수 없습니다.

#### 원인 분석
카메라에 오디오 스트림이 없을 수 있지만 FFmpeg가 오디오를 인코딩하려고 시도하여 오류가 발생합니다.

#### 해결 방법
1. FFmpeg 스트리밍 시 오디오 비활성화:
   ```
   -an
   ```

2. flv.js 구성에서 오디오 비활성화:
   ```javascript
   flvPlayer = flvjs.createPlayer({
       type: 'flv',
       url: url,
       isLive: true,
       hasAudio: false,  // 오디오 비활성화
       hasVideo: true,
   });
   ```


### 6.6 데이터베이스 연결 실패

#### 문제 설명
VIDEO 서비스 시작 시 데이터베이스 연결 오류가 발생합니다.

#### 진단 단계
1. PostgreSQL 서비스가 시작되었는지 확인:
   ```powershell
   $env:PGPASSWORD='iot45722414822'
   & "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"
   ```

2. 데이터베이스 `iot-video20`이 존재하는지 확인

3. `VIDEO/.env`의 DATABASE_URL 구성 확인


### 6.7 Nacos 등록 실패

#### 문제 설명
서비스 시작 시 Nacos에 등록할 수 없습니다.

#### 진단 단계
1. Nacos 서비스가 시작되었는지 확인:
   ```
   http://localhost:8848/nacos
   ```

2. 네임스페이스 `local`이 생성되었는지 확인

3. 구성 파일의 Nacos 주소 및 비밀번호 확인


### 6.8 프론트엔드 인증 코드가 표시되지 않음

#### 문제 설명
프론트엔드 로그인 페이지의 인증 코드 이미지를 로드할 수 없습니다.

#### 원인 분석
일반적으로 게이트웨이 서비스가 시작되지 않았거나 포트 구성이 잘못되었기 때문입니다.

#### 해결 방법
1. DEVICE 게이트웨이 서비스가 시작되었는지 확인 (포트 48080)
2. 프론트엔드 구성의 API 주소가 올바른지 확인
3. 브라우저 콘솔의 네트워크 요청 오류 확인


## 7. 자주 사용하는 명령어 요약

### 7.1 데이터베이스 작업

```powershell
# 비밀번호 환경 변수 설정
$env:PGPASSWORD='iot45722414822'

# 데이터베이스 연결
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20"

# 모든 데이터베이스 보기
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -c "\l"

# 디바이스 테이블 보기
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "SELECT id, name, source, rtmp_stream, http_stream FROM device;"

# 디바이스 스트림 주소 업데이트
& "F:\EASYLOT\PostgreSQL16\bin\psql.exe" -h localhost -U postgres -d "iot-video20" -c "UPDATE device SET http_stream = 'http://127.0.0.1:8080/live/cam_12345678.flv' WHERE id = '1234567890';"
```

### 7.2 SRS 작업

```powershell
# SRS 컨테이너 상태 확인
docker ps | findstr srs

# SRS 로그 보기
docker logs srs-server

# SRS 재시작
docker restart srs-server

# 현재 스트림 목록 보기
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/streams/" | ConvertTo-Json

# SRS 버전 확인
Invoke-RestMethod -Uri "http://127.0.0.1:1985/api/v1/versions"
```

### 7.3 FFmpeg 스트리밍 테스트

```powershell
# Hikvision 카메라 스트리밍 테스트
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/test"

# Dahua 카메라 스트리밍 테스트
& "G:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe" `
  -re `
  -rtsp_transport tcp `
  -i "rtsp://admin:password@192.168.1.64:554/cam/realmonitor?channel=1&subtype=0" `
  -c:v copy `
  -an `
  -f flv `
  "rtmp://127.0.0.1:1935/live/test"
```

### 7.4 서비스 시작 및 중지

```powershell
# VIDEO 서비스
cd F:\EASYLOT\easyaiot-V4.0.0\VIDEO
conda activate easyaiot
python run.py

# AI 서비스
cd F:\EASYLOT\easyaiot-V4.0.0\AI
conda activate easyaiot
python run.py

# WEB 프론트엔드
cd F:\EASYLOT\easyaiot-V4.0.0\WEB
npm run dev
```


## 8. 부록

### 8.1 포트 요약 테이블

| 서비스 | 포트 | 프로토콜 | 설명 |
|--------|------|----------|------|
| PostgreSQL | 5432 | TCP | 데이터베이스 |
| Redis | 6379 | TCP | 캐시 |
| Nacos | 8848 | HTTP | 서비스 등록 센터 |
| MinIO API | 9000 | HTTP | 객체 스토리지 API |
| MinIO Console | 9001 | HTTP | 객체 스토리지 콘솔 |
| Kafka | 9092 | TCP | 메시지 큐 |
| Zookeeper | 2181 | TCP | Kafka 종속성 |
| TDengine | 6030 | TCP | 시계열 데이터베이스 네이티브 연결 |
| TDengine REST | 6041 | HTTP | 시계열 데이터베이스 REST API |
| SRS RTMP | 1935 | TCP | RTMP 스트리밍 (푸시/풀) |
| SRS HTTP-FLV | 8080 | HTTP | HTTP-FLV 재생 |
| SRS API | 1985 | HTTP | SRS 관리 API |
| SRS WebRTC | 8000 | UDP | WebRTC |
| DEVICE Gateway | 48080 | HTTP | Java 게이트웨이 |
| VIDEO | 6000 | HTTP | 비디오 서비스 |
| AI | 8100 | HTTP | AI 서비스 |
| WEB | 3100 | HTTP | 프론트엔드 개발 서버 |

### 8.2 비밀번호 요약 테이블

| 서비스 | 사용자 이름 | 비밀번호 |
|--------|------------|----------|
| PostgreSQL | postgres | iot45722414822 |
| Redis | - | basiclab@iot975248395 |
| Nacos | nacos | basiclab@iot78475418754 |
| MinIO | minioadmin | basiclab@iot975248395 |
| TDengine | root | taosdata |
| WEB 프론트엔드 | admin | admin123 |
| 테스트 카메라 | admin | sr336699 |

### 8.3 카메라 RTSP 주소 형식

#### Hikvision
```
rtsp://用户名:密码@IP:554/Streaming/Channels/101  # 主码流
rtsp://用户名:密码@IP:554/Streaming/Channels/102  # 子码流
```

#### Dahua
```
rtsp://用户名:密码@IP:554/cam/realmonitor?channel=1&subtype=0  # 主码流
rtsp://用户名:密码@IP:554/cam/realmonitor?channel=1&subtype=1  # 子码流
```

#### Uniview
```
rtsp://用户名:密码@IP:554/unicast/c1/s0/live  # 主码流
rtsp://用户名:密码@IP:554/unicast/c1/s1/live  # 子码流
```

### 8.4 자주 묻는 질문 FAQ

**Q: 프론트엔드 페이지가 열리지 않나요?**
A: WEB 서비스가 시작되었는지 확인하고 포트 3100이 사용 중인지 확인하세요.

**Q: 로그인 시 네트워크 오류가 표시되나요?**
A: DEVICE 게이트웨이 서비스가 시작되었는지 확인하고 포트 48080이 정상인지 확인하세요.

**Q: 비디오가 검은 화면으로 재생되나요?**
A: 
1. SRS가 실행 중인지 확인: `docker ps | findstr srs`
2. 스트림이 있는지 확인: `http://127.0.0.1:1985/api/v1/streams/` 액세스
3. 수동 스트리밍 테스트 명령이 정상인지 확인

**Q: 스트리밍이 실패하나요?**
A: 
1. FFmpeg 경로가 올바른지 확인
2. 카메라 RTSP 주소에 액세스할 수 있는지 확인
3. SRS가 실행 중인지 확인
4. 스트림 이름이 너무 긴지 확인

**Q: 서비스가 Nacos에 등록되지 않나요?**
A: 
1. Nacos가 시작되었는지 확인
2. 네임스페이스 `local`이 존재하는지 확인
3. 비밀번호가 올바른지 확인


> 문서 끝
> 문제가 있으면 AI에 문의하세요

