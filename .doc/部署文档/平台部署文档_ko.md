# EasyAIoT 플랫폼 배포 문서

## 📋 목차

- [개요](#개요)
- [환경 요구사항](#환경-요구사항)
- [빠른 시작](#빠른-시작)
- [스크립트 사용 설명](#스크립트-사용-설명)
- [모듈 설명](#모듈-설명)
- [서비스 포트](#서비스-포트)
- [자주 묻는 질문](#자주-묻는-질문)
- [로그 관리](#로그-관리)

## 개요

EasyAIoT는 클라우드-엣지 통합 지능형 알고리즘 애플리케이션 플랫폼으로, 통합 설치 스크립트를 사용하여 원클릭 배포를 지원합니다. 이 플랫폼은 Docker 컨테이너화 배포를 지원하며, 모든 서비스 모듈을 빠르게 설치하고 시작할 수 있습니다.

### 플랫폼 아키텍처

EasyAIoT 플랫폼은 다음 핵심 모듈로 구성됩니다:

- **기본 서비스** (`.scripts/docker`): Nacos, PostgreSQL, Redis, TDEngine, Kafka, MinIO 등 미들웨어 포함
- **DEVICE 서비스**: 디바이스 관리 및 게이트웨이 서비스 (Java 기반)
- **AI 서비스**: 인공지능 처리 서비스 (Python 기반)
- **VIDEO 서비스**: 비디오 처리 서비스 (Python 기반)
- **WEB 서비스**: Web 프론트엔드 서비스 (Vue 기반)

## 환경 요구사항

### 시스템 요구사항

- **운영체제**:
    - Linux (Ubuntu 20.04+ 또는 CentOS 7+ 권장)
    - macOS (macOS 10.15+ 권장)
    - Windows (Windows 10/11 권장, PowerShell 5.1+ 필요)
- **메모리**: 8GB 이상 권장
- **디스크**: 50GB 이상의 여유 공간 권장
- **CPU**: 4코어 이상 권장

### 소프트웨어 의존성

배포 스크립트를 실행하기 전에 다음 소프트웨어가 설치되어 있는지 확인해야 합니다:

1. **Docker** (필수 버전 v29.0.0+)
    - 설치 가이드: https://docs.docker.com/get-docker/
    - 설치 확인: `docker --version`
    - **참고**: Docker 버전은 v29.0.0 이상이어야 하며, 이보다 낮은 버전은 정상적으로 실행되지 않습니다.

2. **Docker Compose** (필수 버전 v2.35.0+)
    - 설치 가이드: https://docs.docker.com/compose/install/
    - 설치 확인: `docker compose version`
    - **참고**: Docker Compose 버전은 v2.35.0 이상이어야 하며, 이보다 낮은 버전은 정상적으로 실행되지 않습니다.

3. **기타 의존성**:
    - **Linux/macOS**: `curl` (건강 상태 확인에 사용, 일반적으로 시스템에 기본 탑재)
    - **Windows**: PowerShell 5.1+ (일반적으로 시스템에 기본 탑재)

### Docker 권한 설정

#### Linux

현재 사용자가 Docker 데몬에 접근할 권한이 있는지 확인하세요:

```bash
# 방법1: 사용자를 docker 그룹에 추가 (권장)
sudo usermod -aG docker $USER
# 그런 다음 다시 로그인하거나 다음 실행
newgrp docker

# 방법2: sudo를 사용하여 스크립트 실행 (비권장)
sudo ./install_linux.sh [명령]
```

Docker 권한 확인:

```bash
docker ps
```

#### macOS

macOS는 일반적으로 특별한 권한 설정이 필요하지 않으며, Docker Desktop이 자동으로 권한을 처리합니다.

#### Windows

Windows에서 Docker Desktop은 권한을 자동으로 처리합니다. 필요한 경우 관리자 권한으로 PowerShell을 실행하세요.

## 빠른 시작

### Linux 배포

#### 1. 프로젝트 코드 가져오기

```bash
# 프로젝트 클론 (아직 없는 경우)
git clone <repository-url>
cd easyaiot
```

#### 2. 스크립트 디렉토리로 이동

```bash
cd .scripts/docker
```

#### 3. 스크립트 실행 권한 부여

```bash
chmod +x install_linux.sh
```

#### 4. 모든 서비스 일괄 설치

```bash
./install_linux.sh install
```

이 명령은 다음을 수행합니다:
- Docker 및 Docker Compose 환경 확인
- 통합 네트워크 `easyaiot-network` 생성
- 의존성 순서에 따라 모든 모듈 설치
- 모든 서비스 컨테이너 시작

#### 5. 서비스 상태 확인

```bash
./install_linux.sh verify
```

모든 서비스가 정상적으로 실행 중이면 서비스 접근 주소가 표시됩니다.

### macOS 배포

#### 1. 프로젝트 코드 가져오기

```bash
# 프로젝트 클론 (아직 없는 경우)
git clone <repository-url>
cd easyaiot
```

#### 2. 스크립트 디렉토리로 이동

```bash
cd .scripts/docker
```

#### 3. 스크립트 실행 권한 부여

```bash
chmod +x install_mac.sh
```

#### 4. 모든 서비스 일괄 설치

```bash
./install_mac.sh install
```

이 명령은 다음을 수행합니다:
- Docker 및 Docker Compose 환경 확인
- 통합 네트워크 `easyaiot-network` 생성
- 의존성 순서에 따라 모든 모듈 설치
- 모든 서비스 컨테이너 시작

#### 5. 서비스 상태 확인

```bash
./install_mac.sh verify
```

모든 서비스가 정상적으로 실행 중이면 서비스 접근 주소가 표시됩니다.

### Windows 배포

#### 1. 프로젝트 코드 가져오기

```powershell
# 프로젝트 클론 (아직 없는 경우)
git clone <repository-url>
cd easyaiot
```

#### 2. 스크립트 디렉토리로 이동

```powershell
cd .scripts\docker
```

#### 3. 실행 정책 설정 (필요한 경우)

PowerShell 스크립트를 처음 실행하는 경우 실행 정책을 설정해야 할 수 있습니다:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 4. 모든 서비스 일괄 설치

```powershell
.\install_win.ps1 install
```

이 명령은 다음을 수행합니다:
- Docker 및 Docker Compose 환경 확인
- 통합 네트워크 `easyaiot-network` 생성
- 의존성 순서에 따라 모든 모듈 설치
- 모든 서비스 컨테이너 시작

#### 5. 서비스 상태 확인

```powershell
.\install_win.ps1 verify
```

모든 서비스가 정상적으로 실행 중이면 서비스 접근 주소가 표시됩니다.

## 스크립트 사용 설명

### 스크립트 위치

통합 설치 스크립트는 프로젝트 루트 디렉토리의 `.scripts/docker/` 디렉토리에 위치합니다:

- **Linux**: `install_linux.sh`
- **macOS**: `install_mac.sh`
- **Windows**: `install_win.ps1`

### 사용 가능한 명령

모든 운영체제에서 동일한 명령을 지원하지만, 스크립트 이름이 다릅니다:

| 명령 | 설명 | Linux 예제 | macOS 예제 | Windows 예제 |
|------|------|-----------|-----------|-------------|
| `install` | 모든 서비스 설치 및 시작 (첫 실행) | `./install_linux.sh install` | `./install_mac.sh install` | `.\install_win.ps1 install` |
| `start` | 모든 서비스 시작 | `./install_linux.sh start` | `./install_mac.sh start` | `.\install_win.ps1 start` |
| `stop` | 모든 서비스 중지 | `./install_linux.sh stop` | `./install_mac.sh stop` | `.\install_win.ps1 stop` |
| `restart` | 모든 서비스 재시작 | `./install_linux.sh restart` | `./install_mac.sh restart` | `.\install_win.ps1 restart` |
| `status` | 모든 서비스 상태 확인 | `./install_linux.sh status` | `./install_mac.sh status` | `.\install_win.ps1 status` |
| `logs` | 모든 서비스 로그 확인 | `./install_linux.sh logs` | `./install_mac.sh logs` | `.\install_win.ps1 logs` |
| `build` | 모든 이미지 재빌드 | `./install_linux.sh build` | `./install_mac.sh build` | `.\install_win.ps1 build` |
| `clean` | 모든 컨테이너 및 이미지 정리 (위험한 작업) | `./install_linux.sh clean` | `./install_mac.sh clean` | `.\install_win.ps1 clean` |
| `update` | 모든 서비스 업데이트 및 재시작 | `./install_linux.sh update` | `./install_mac.sh update` | `.\install_win.ps1 update` |
| `verify` | 모든 서비스가 성공적으로 시작되었는지 확인 | `./install_linux.sh verify` | `./install_mac.sh verify` | `.\install_win.ps1 verify` |

### 명령 상세 설명

#### install - 서비스 설치

처음 배포 시 사용하며, 모든 서비스 모듈을 설치하고 시작합니다:

**Linux/macOS**:
```bash
./install_linux.sh install    # Linux
./install_mac.sh install       # macOS
```

**Windows**:
```powershell
.\install_win.ps1 install
```

**실행 절차**:
1. Docker 및 Docker Compose 환경 확인
2. Docker 네트워크 `easyaiot-network` 생성
3. 의존성 순서에 따라 각 모듈 설치:
    - 기본 서비스 (Nacos, PostgreSQL, Redis 등)
    - DEVICE 서비스
    - AI 서비스
    - VIDEO 서비스
    - WEB 서비스
4. 설치 결과 통계 표시

#### start - 서비스 시작

설치된 모든 서비스를 시작합니다:

**Linux/macOS**:
```bash
./install_linux.sh start    # Linux
./install_mac.sh start      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 start
```

#### stop - 서비스 중지

실행 중인 모든 서비스를 중지합니다 (역순으로 중지):

**Linux/macOS**:
```bash
./install_linux.sh stop    # Linux
./install_mac.sh stop      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 stop
```

#### restart - 서비스 재시작

모든 서비스를 재시작합니다:

**Linux/macOS**:
```bash
./install_linux.sh restart    # Linux
./install_mac.sh restart      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 restart
```

#### status - 상태 확인

모든 서비스의 실행 상태를 확인합니다:

**Linux/macOS**:
```bash
./install_linux.sh status    # Linux
./install_mac.sh status      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 status
```

#### logs - 로그 확인

모든 서비스의 로그를 확인합니다 (최근 100줄):

**Linux/macOS**:
```bash
./install_linux.sh logs    # Linux
./install_mac.sh logs      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 logs
```

#### build - 이미지 빌드

모든 서비스의 Docker 이미지를 재빌드합니다 (`--no-cache` 옵션 사용):

**Linux/macOS**:
```bash
./install_linux.sh build    # Linux
./install_mac.sh build      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 build
```

**참고**: 빌드 과정은 시간이 오래 걸릴 수 있으니 인내심을 가지고 기다려 주세요.

#### clean - 서비스 정리

**⚠️ 위험한 작업**: 모든 컨테이너, 이미지 및 데이터 볼륨 삭제

**Linux/macOS**:
```bash
./install_linux.sh clean    # Linux
./install_mac.sh clean      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 clean
```

실행 전 확인을 요청하며, `y` 또는 `Y`를 입력하면 계속 진행하고, 다른 입력은 작업을 취소합니다.

**정리 내용**:
- 모든 서비스 컨테이너
- 모든 서비스 이미지
- 모든 데이터 볼륨
- Docker 네트워크 `easyaiot-network`

#### update - 서비스 업데이트

최신 이미지를 가져와 모든 서비스를 재시작합니다:

**Linux/macOS**:
```bash
./install_linux.sh update    # Linux
./install_mac.sh update      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 update
```

**실행 절차**:
1. 각 모듈의 최신 이미지 가져오기
2. 새로운 이미지를 사용하도록 모든 서비스 재시작

#### verify - 서비스 확인

모든 서비스가 정상적으로 시작되어 접근 가능한지 확인합니다:

**Linux/macOS**:
```bash
./install_linux.sh verify    # Linux
./install_mac.sh verify      # macOS
```

**Windows**:
```powershell
.\install_win.ps1 verify
```

**확인 내용**:
- 서비스 포트 접근 가능 여부 확인
- 건강 상태 확인 엔드포인트 정상 응답 여부 확인
- 서비스 접근 주소 표시

**성공 출력 예제**:
```
[SUCCESS] 모든 서비스가 정상적으로 실행 중입니다!

서비스 접근 주소:
  기본 서비스 (Nacos):     http://localhost:8848/nacos
  기본 서비스 (MinIO):     http://localhost:9000 (API), http://localhost:9001 (Console)
  Device 서비스 (Gateway):  http://localhost:48080
  AI 서비스:                http://localhost:5000
  Video 서비스:             http://localhost:6000
  Web 프론트엔드:               http://localhost:8888
```

## 모듈 설명

### 기본 서비스 (`.scripts/docker`)

**설명**: 플랫폼 실행에 필요한 모든 미들웨어 서비스 포함

**포함 서비스**:
- **Nacos**: 서비스 등록 및 설정 센터
- **PostgreSQL**: 관계형 데이터베이스
- **Redis**: 캐시 데이터베이스
- **TDEngine**: 시계열 데이터베이스
- **Kafka**: 메시지 큐
- **MinIO**: 객체 저장 서비스

**배포 방식**:
- **Linux**: `install_middleware_linux.sh` 스크립트 사용
- **macOS**: `install_middleware_mac.sh` 스크립트 사용
- **Windows**: `install_middleware_win.ps1` 스크립트 사용

### DEVICE 서비스

**설명**: 디바이스 관리 및 게이트웨이 서비스로, 디바이스 접속, 제품 관리, 데이터 레이블링, 규칙 엔진 등의 기능 제공

**기술 스택**: Java (Spring Cloud)

**배포 방식**:
- **Linux**: `install_linux.sh` 스크립트 사용
- **macOS**: `install_mac.sh` 스크립트 사용
- **Windows**: `install_win.ps1` 스크립트 사용

**주요 기능**:
- 디바이스 관리
- 제품 관리
- 데이터 레이블링
- 규칙 엔진
- 알고리즘 스토어
- 시스템 관리

### AI 서비스

**설명**: 인공지능 처리 서비스로, 비디오 분석 및 AI 알고리즘 실행 담당

**기술 스택**: Python

**배포 방식**:
- **Linux**: `install_linux.sh` 스크립트 사용
- **macOS**: `install_mac.sh` 스크립트 사용
- **Windows**: `install_win.ps1` 스크립트 사용

**주요 기능**:
- 비디오 분석
- AI 알고리즘 실행
- 모델 추론

### VIDEO 서비스

**설명**: 비디오 처리 서비스로, 비디오 스트림 처리 및 전송 담당

**기술 스택**: Python

**배포 방식**:
- **Linux**: `install_linux.sh` 스크립트 사용
- **macOS**: `install_mac.sh` 스크립트 사용
- **Windows**: `install_win.ps1` 스크립트 사용

**주요 기능**:
- 비디오 스트림 처리
- 비디오 전송
- 스트리밍 서비스

### WEB 서비스

**설명**: Web 프론트엔드 서비스로, 사용자 인터페이스 제공

**기술 스택**: Vue.js

**배포 방식**:
- **Linux**: `install_linux.sh` 스크립트 사용
- **macOS**: `install_mac.sh` 스크립트 사용
- **Windows**: `install_win.ps1` 스크립트 사용

**주요 기능**:
- 사용자 인터페이스
- 데이터 시각화
- 시스템 관리 인터페이스

## 서비스 포트

| 서비스 모듈 | 포트 | 설명 | 접근 주소 |
|---------|------|------|----------|
| Nacos | 8848 | 서비스 등록 및 설정 센터 | http://localhost:8848/nacos |
| MinIO API | 9000 | 객체 저장 API | http://localhost:9000 |
| MinIO Console | 9001 | 객체 저장 콘솔 | http://localhost:9001 |
| DEVICE Gateway | 48080 | 디바이스 서비스 게이트웨이 | http://localhost:48080 |
| AI 서비스 | 5000 | AI 처리 서비스 | http://localhost:5000 |
| VIDEO 서비스 | 6000 | 비디오 처리 서비스 | http://localhost:6000 |
| WEB 프론트엔드 | 8888 | Web 프론트엔드 인터페이스 | http://localhost:8888 |

### 건강 상태 확인 엔드포인트

각 서비스의 건강 상태 확인 엔드포인트:

| 서비스 모듈 | 건강 상태 확인 엔드포인트 |
|---------|-------------|
| 기본 서비스 (Nacos) | `/nacos/actuator/health` |
| DEVICE 서비스 | `/actuator/health` |
| AI 서비스 | `/actuator/health` |
| VIDEO 서비스 | `/actuator/health` |
| WEB 서비스 | `/health` |

## 자주 묻는 질문

### 1. Docker 권한 문제

**문제**: 스크립트 실행 시 "Docker 데몬에 접근 권한이 없습니다"라는 메시지 표시

**해결 방법**:

**Linux**:
```bash
# 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 다시 로그인하거나 실행
newgrp docker

# 권한 확인
docker ps
```

**macOS**:
macOS는 일반적으로 특별한 설정이 필요하지 않으며, Docker Desktop이 실행 중인지 확인하세요.

**Windows**:
Windows에서 Docker Desktop은 권한을 자동으로 처리합니다. Docker Desktop이 실행 중인지 확인하세요.

### 2. 포트 점유

**문제**: 서비스 시작 시 포트가 이미 사용 중이라고 표시

**해결 방법**:

**Linux**:
```bash
# 포트 점유 상황 확인
sudo netstat -tulpn | grep <포트 번호>
# 또는
sudo lsof -i :<포트 번호>

# 포트를 점유하는 프로세스를 중지하거나 서비스 설정에서 포트 수정
```

**macOS**:
```bash
# 포트 점유 상황 확인
lsof -i :<포트 번호>

# 포트를 점유하는 프로세스를 중지하거나 서비스 설정에서 포트 수정
```

**Windows**:
```powershell
# 포트 점유 상황 확인
netstat -ano | findstr :<포트 번호>

# 포트를 점유하는 프로세스를 중지하거나 서비스 설정에서 포트 수정
```

### 3. 서비스 시작 실패

**문제**: 특정 서비스 모듈 시작 실패

**해결 방법**:

**Linux/macOS**:
```bash
# 1. 서비스 로그 확인
./install_linux.sh logs    # Linux
./install_mac.sh logs      # macOS

# 2. 특정 모듈의 상세 로그 확인
cd <모듈 디렉토리>
docker-compose logs

# 3. Docker 리소스 확인
docker ps -a
docker images

# 4. 네트워크 확인
docker network ls
docker network inspect easyaiot-network
```

**Windows**:
```powershell
# 1. 서비스 로그 확인
.\install_win.ps1 logs

# 2. 특정 모듈의 상세 로그 확인
cd <모듈 디렉토리>
docker-compose logs

# 3. Docker 리소스 확인
docker ps -a
docker images

# 4. 네트워크 확인
docker network ls
docker network inspect easyaiot-network
```

### 4. 이미지 빌드 실패

**문제**: 이미지 빌드 시 실패

**해결 방법**:

**Linux/macOS**:
```bash
# 1. Docker 디스크 공간 확인
docker system df

# 2. 사용하지 않는 리소스 정리
docker system prune -a

# 3. 네트워크 연결 확인 (기본 이미지 가져오기 필요 시)
ping registry-1.docker.io

# 4. 실패 모듈의 이미지 개별 빌드
cd <모듈 디렉토리>
docker-compose build --no-cache
```

**Windows**:
```powershell
# 1. Docker 디스크 공간 확인
docker system df

# 2. 사용하지 않는 리소스 정리
docker system prune -a

# 3. 네트워크 연결 확인 (기본 이미지 가져오기 필요 시)
Test-NetConnection registry-1.docker.io -Port 443

# 4. 실패 모듈의 이미지 개별 빌드
cd <모듈 디렉토리>
docker-compose build --no-cache
```

### 5. 서비스 접근 불가

**문제**: 서비스가 시작되었지만 브라우저를 통해 접근할 수 없음

**해결 방법**:

**Linux**:
```bash
# 1. 서비스가 정상적으로 실행 중인지 확인
./install_linux.sh verify

# 2. 방화벽 설정 확인
sudo ufw status
# 포트를 열어야 하는 경우
sudo ufw allow <포트 번호>

# 3. 서비스 로그 확인
./install_linux.sh logs

# 4. 컨테이너 상태 확인
docker ps
```

**macOS**:
```bash
# 1. 서비스가 정상적으로 실행 중인지 확인
./install_mac.sh verify

# 2. 방화벽 설정 확인 (시스템 환경설정 > 보안 및 개인정보 보호 > 방화벽)

# 3. 서비스 로그 확인
./install_mac.sh logs

# 4. 컨테이너 상태 확인
docker ps
```

**Windows**:
```powershell
# 1. 서비스가 정상적으로 실행 중인지 확인
.\install_win.ps1 verify

# 2. 방화벽 설정 확인 (Windows 방화벽 설정)

# 3. 서비스 로그 확인
.\install_win.ps1 logs

# 4. 컨테이너 상태 확인
docker ps
```

### 6. 데이터 손실 문제

**문제**: 서비스 정리 후 데이터 손실

**설명**: `clean` 명령은 모든 데이터 볼륨을 삭제하여 데이터 손실을 초래합니다. 이는 예상된 동작입니다.

**예방 조치**:
- `clean` 실행 전 중요 데이터 백업
- 프로덕션 환경에서 `clean` 명령 사용 주의
- 데이터 볼륨 백업 도구 사용 권장

## 로그 관리

### 로그 파일 위치

스크립트 실행 로그는 `.scripts/docker/logs/` 디렉토리에 저장됩니다:

- **Linux**: `install_linux_YYYYMMDD_HHMMSS.log`
- **macOS**: `install_mac_YYYYMMDD_HHMMSS.log`
- **Windows**: `install_win_YYYYMMDD_HHMMSS.log`

로그 파일 이름에는 타임스탬프가 포함되어 있어 다른 실행 기록을 쉽게 구분할 수 있습니다.

### 로그 확인

#### 스크립트 실행 로그 확인

**Linux/macOS**:
```bash
# 최신 로그 파일 확인
ls -lt .scripts/docker/logs/ | head -5

# 특정 로그 파일 확인
tail -f .scripts/docker/logs/install_linux_20240101_120000.log    # Linux
tail -f .scripts/docker/logs/install_mac_20240101_120000.log      # macOS
```

**Windows**:
```powershell
# 최신 로그 파일 확인
Get-ChildItem .scripts\docker\logs\ | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# 특정 로그 파일 확인
Get-Content .scripts\docker\logs\install_win_20240101_120000.log -Wait
```

#### 서비스 컨테이너 로그 확인

**Linux/macOS**:
```bash
# 모든 서비스 로그 확인
./install_linux.sh logs    # Linux
./install_mac.sh logs      # macOS

# 특정 서비스의 로그 확인 (해당 모듈 디렉토리로 이동 필요)
cd DEVICE
docker-compose logs -f
```

**Windows**:
```powershell
# 모든 서비스 로그 확인
.\install_win.ps1 logs

# 특정 서비스의 로그 확인 (해당 모듈 디렉토리로 이동 필요)
cd DEVICE
docker-compose logs -f
```

### 로그 내용

스크립트 로그에는 다음이 포함됩니다:
- 실행 타임스탬프
- 실행된 명령
- 각 모듈의 실행 결과
- 오류 메시지 및 경고
- 서비스 상태 정보

## 배포 절차 권장사항

### 처음 배포

#### Linux

1. **환경 준비**
   ```bash
   # 시스템 요구사항 확인
   uname -a
   free -h
   df -h
   
   # Docker 및 Docker Compose 설치
   # 참고: https://docs.docker.com/get-docker/
   ```

2. **코드 가져오기**
   ```bash
   git clone <repository-url>
   cd easyaiot
   ```

3. **설치 실행**
   ```bash
   cd .scripts/docker
   chmod +x install_linux.sh
   ./install_linux.sh install
   ```

4. **배포 확인**
   ```bash
   ./install_linux.sh verify
   ```

5. **서비스 접근**
    - 브라우저에서 각 서비스 주소 접근
    - 서비스가 정상적으로 실행 중인지 확인

#### macOS

1. **환경 준비**
   ```bash
   # 시스템 요구사항 확인
   uname -a
   system_profiler SPHardwareDataType | grep Memory
   df -h
   
   # Docker Desktop for Mac 설치
   # 참고: https://docs.docker.com/desktop/install/mac-install/
   ```

2. **코드 가져오기**
   ```bash
   git clone <repository-url>
   cd easyaiot
   ```

3. **설치 실행**
   ```bash
   cd .scripts/docker
   chmod +x install_mac.sh
   ./install_mac.sh install
   ```

4. **배포 확인**
   ```bash
   ./install_mac.sh verify
   ```

5. **서비스 접근**
    - 브라우저에서 각 서비스 주소 접근
    - 서비스가 정상적으로 실행 중인지 확인

#### Windows

1. **환경 준비**
   ```powershell
   # 시스템 요구사항 확인
   systeminfo | findstr /C:"OS Name" /C:"Total Physical Memory"
   
   # Docker Desktop for Windows 설치
   # 참고: https://docs.docker.com/desktop/install/windows-install/
   ```

2. **코드 가져오기**
   ```powershell
   git clone <repository-url>
   cd easyaiot
   ```

3. **설치 실행**
   ```powershell
   cd .scripts\docker
   .\install_win.ps1 install
   ```

4. **배포 확인**
   ```powershell
   .\install_win.ps1 verify
   ```

5. **서비스 접근**
    - 브라우저에서 각 서비스 주소 접근
    - 서비스가 정상적으로 실행 중인지 확인

### 일상적인 운영 관리

#### Linux/macOS

1. **서비스 시작**
   ```bash
   ./install_linux.sh start    # Linux
   ./install_mac.sh start      # macOS
   ```

2. **서비스 중지**
   ```bash
   ./install_linux.sh stop    # Linux
   ./install_mac.sh stop      # macOS
   ```

3. **서비스 재시작**
   ```bash
   ./install_linux.sh restart    # Linux
   ./install_mac.sh restart      # macOS
   ```

4. **상태 확인**
   ```bash
   ./install_linux.sh status    # Linux
   ./install_mac.sh status      # macOS
   ```

5. **로그 확인**
   ```bash
   ./install_linux.sh logs    # Linux
   ./install_mac.sh logs      # macOS
   ```

#### Windows

1. **서비스 시작**
   ```powershell
   .\install_win.ps1 start
   ```

2. **서비스 중지**
   ```powershell
   .\install_win.ps1 stop
   ```

3. **서비스 재시작**
   ```powershell
   .\install_win.ps1 restart
   ```

4. **상태 확인**
   ```powershell
   .\install_win.ps1 status
   ```

5. **로그 확인**
   ```powershell
   .\install_win.ps1 logs
   ```

### 업데이트 배포

#### Linux/macOS

1. **최신 코드 가져오기**
   ```bash
   git pull
   ```

2. **서비스 업데이트**
   ```bash
   cd .scripts/docker
   ./install_linux.sh update    # Linux
   ./install_mac.sh update      # macOS
   ```

3. **업데이트 확인**
   ```bash
   ./install_linux.sh verify    # Linux
   ./install_mac.sh verify      # macOS
   ```

#### Windows

1. **최신 코드 가져오기**
   ```powershell
   git pull
   ```

2. **서비스 업데이트**
   ```powershell
   cd .scripts\docker
   .\install_win.ps1 update
   ```

3. **업데이트 확인**
   ```powershell
   .\install_win.ps1 verify
   ```

## 주의사항

1. **버전 요구사항**: **반드시** Docker v29.0.0+ 및 Docker Compose v2.35.0+를 설치해야 하며, 이보다 낮은 버전은 정상적으로 실행되지 않습니다.
2. **네트워크 요구사항**: 서버가 Docker Hub 또는 구성된 이미지 저장소에 접근할 수 있는지 확인하세요.
3. **리소스 요구사항**: 서버에 충분한 CPU, 메모리 및 디스크 공간이 있는지 확인하세요.
4. **포트 충돌**: 필요한 포트가 다른 서비스에 의해 점유되지 않았는지 확인하세요.
5. **데이터 백업**: 프로덕션 환경 배포 전 중요 데이터를 백업하세요.
6. **보안 설정**: 프로덕션 환경에서는 방화벽 및 보안 그룹 규칙을 구성하세요.
7. **로그 관리**: 정기적으로 오래된 로그 파일을 정리하여 디스크 공간 부족을 방지하세요.

## 기술 지원

문제가 발생하면 다음을 확인하세요:

1. 본 문서의 [자주 묻는 질문](#자주-묻는-질문) 부분 확인
2. 서비스 로그 확인: `./install_all.sh logs`
3. Docker 상태 확인: `docker ps -a`
4. 프로젝트 저장소에 Issue 제출

---

**문서 버전**: 1.0  
**마지막 업데이트**: 2024-01-01  
**스크립트 위치**: `.scripts/docker/install_all.sh`