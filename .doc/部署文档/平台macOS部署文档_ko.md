# EasyAIoT 플랫폼 macOS 배포 문서

> 문서 버전: 1.1  
> 업데이트 날짜: 2026-08-01  
> 지원 시스템: macOS (Intel / Apple Silicon)  
> 배포 방식: **사전 빌드 이미지만** (로컬에서 비즈니스 코드 컴파일 안 함)

개요 및 명령 대조: [플랫폼 배포 문서](./平台部署文档_ko.md#macos--windows-이미지-전용-배포).  
PANEL 데스크톱 설치 패키지 빌드: [COMPILE/README.md](../../COMPILE/README.md).

---

## 목차

1. [개요](#1-개요)
2. [환경 준비](#2-환경-준비)
3. [원클릭 배포](#3-원클릭-배포)
4. [자주 사용하는 명령](#4-자주-사용하는-명령)
5. [주의사항 및 문제 해결](#5-주의사항-및-문제-해결)

---

## 1. 개요

macOS는 단일 진입점을 사용합니다:

```bash
.scripts/docker/install_mac.sh
```

Homebrew bash 4+ 사용을 권장합니다(시스템 `/bin/bash`는 3.2):

```bash
/opt/homebrew/bin/bash .scripts/docker/install_mac.sh <명령>
```

스크립트는 다음을 수행합니다:

1. **사전 환경 검사**(Docker Desktop / Compose / bash 4+ / curl): 부족한 항목을 안내한 뒤 **중단**
2. 필요 시 `open -a Docker`로 엔진 준비 대기
3. **필요에 따라** 국내 `registry-mirrors` 기록, 배포 형태에 맞춰 Docker 엔진 메모리 조정
4. 배포 사양(mini / standard / full)에 따라 사전 빌드 비즈니스 이미지 pull
5. `install_middleware_desktop.sh`로 미들웨어 pull·기동(**FUXA**는 전용 `pull_fuxa.sh`)
6. `EASYAIOT_SKIP_BUILD=1`로 각 모듈 `install_linux.sh`를 호출해 컨테이너만 기동

**미지원:** `build`, `build-runtime`, `clean-build-runtime`. 이미지는 Linux CI/서버에서 빌드해 레지스트리에 푸시해야 합니다(`runtime_registry.conf` 참고).

---

## 2. 환경 준비

### 2.1 하드웨어 및 Docker 엔진 메모리

| 사양 | 호스트 권장 | Docker 엔진 목표 메모리 | 설명 |
|------|-------------|------------------------|------|
| mini | ≥ 8 GB | **8 GB** | 엣지 / PoC |
| standard | ≥ 24 GB | **16 GB** | 일상 개발·데모 |
| full | ≥ 32 GB (48 GB+ 권장) | **24 GB** | 전체 기능 |

디스크: **≥ 100 GB** 여유 공간 권장(이미지·데이터 볼륨).

> Desktop은 엔진에 기본 ~8 GB만 할당하는 경우가 많습니다. `resources` / `bootstrap` / `install`은 부족 시 자동 상향(Docker Desktop `settings-store.json` 기록 후 엔진 재시작). 환경 변수로 덮어쓰기: `EASYAIOT_DOCKER_MEMORY_GB` / `EASYAIOT_DOCKER_CPUS` / `EASYAIOT_DOCKER_DISK_GB`; `EASYAIOT_DOCKER_SKIP_RESOURCES=1`로 건너뛰기.

### 2.2 소프트웨어 의존성

| 의존성 | 설명 |
|--------|------|
| Homebrew | [brew.sh](https://brew.sh) |
| Docker 엔진 | Docker Desktop(권장) 또는 Colima(`brew install docker colima`); `docker info` 사용 가능하면 됨 |
| Homebrew bash 4+ | `brew install bash`(시스템 `/bin/bash` 3.2는 이미지 pull 로직 실행 불가) |
| Git | 저장소 clone |
| curl | 헬스 체크(보통 시스템 기본) |
| python3 | `mirrors` / `resources` 설정 재작성 시 사용(macOS / Homebrew에 보통 포함) |

### 2.3 원클릭 사전 의존성 설치(권장)

최초 배포 전 의존성 설치 및 자가 점검(체크리스트 출력, 부족 항목 안내):

```bash
bash .scripts/docker/install_mac.sh bootstrap   # Homebrew bash + Docker Desktop(실패 시 Colima) + 미러/리소스
bash .scripts/docker/install_mac.sh check       # 사전 환경 자가 점검
bash .scripts/docker/install_mac.sh mirrors     # 국내 registry-mirrors(Linux와 동일)
bash .scripts/docker/install_mac.sh resources   # 형태별 엔진 메모리: mini 8G / standard 16G / full 24G
```

`install` / `pull` / `update` / `start`는 실제 배포 전 **자동으로 사전 검사**하며, 미충족 시 설치 안내 후 중단합니다.

검증:

```bash
docker --version
docker compose version
docker info | grep -A5 'Registry Mirrors'
docker info | grep -E 'CPUs|Total Memory'
bash --version   # ≥ 4 권장; Homebrew 경로는 보통 /opt/homebrew/bin/bash
```

### 2.4 국내 이미지 가속(Linux와 동일)

데스크톱과 Linux는 `DOCKER_MIRROR` / `DOCKER_MIRROR_FALLBACKS`를 공유합니다:

| 용도 | 동작 |
|------|------|
| Docker Hub / 미들웨어 | `~/.docker/daemon.json`의 `registry-mirrors` 기록: 기본 DaoCloud → 1ms → 1panel |
| **FUXA** | **예외:** `pull_fuxa.sh`는 **docker.1ms.run 우선**(DaoCloud는 `frangoteam/fuxa`에 자주 403); compose 고정명 `docker.1panel.live/frangoteam/fuxa:…` |
| 비즈니스 사전 빌드 이미지 | `runtime_registry.conf`에서 옴(예: `docker.cnb.cool/...`), `registry-mirrors` **영향 없음** |

```bash
# 자동 기록 및 Docker Desktop 재시작(bootstrap / install에서도 트리거 가능)
bash .scripts/docker/install_mac.sh mirrors

# 자동 mirrors 쓰기 건너뛰기
EASYAIOT_DOCKER_SKIP_MIRROR=1 bash .scripts/docker/install_mac.sh install
```

수동 동등 설정(보통 GUI 추가 변경 불필요):

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1ms.run",
    "https://docker.1panel.live"
  ]
}
```

### 2.5 Apple Silicon 설명

스크립트는 `uname -m`에 따라 런타임 이미지와 Nacos를 `linux/arm64`로 pull합니다. 원격 레지스트리에 해당 아키텍처 매니페스트가 있는지 확인하세요. amd64만 있다면 레지스트리 측에서 arm64를 추가하거나 Intel Mac / 원격 Linux를 사용하세요. Nacos에 amd64를 강제하지 마세요(QEMU가 매우 느림).

### 2.6 PANEL 데스크톱 설치 패키지(선택)

더블클릭 운영 패널이 필요하면 로컬에서 macOS 패키지를 빌드합니다(원형 흰 배경 아이콘, Linux와 동일):

```bash
bash COMPILE/build.sh macos --dmg
# 산출물: COMPILE/dist/macos/easyaiot-panel-<버전>.dmg
```

자세한 내용: [COMPILE/README.md](../../COMPILE/README.md#macos-打包dmg).

---

## 3. 원클릭 배포

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# 최초: 사전 의존성 → 자가 점검 → 배포
bash .scripts/docker/install_mac.sh bootstrap
bash .scripts/docker/install_mac.sh check
EASYAIOT_DEPLOY_PROFILE=full bash .scripts/docker/install_mac.sh install

# 또는 대화형 가이드
bash .scripts/docker/install_mac.sh

# 검증
bash .scripts/docker/install_mac.sh verify
```

비대화형 형태 지정:

```bash
export EASYAIOT_DEPLOY_PROFILE=mini   # 또는 standard / full
bash .scripts/docker/install_mac.sh install
```

설치 후 접속:

| 서비스 | 주소 |
|--------|------|
| WEB | https://localhost:8888 |
| Gateway | http://localhost:48080 |
| Nacos | http://localhost:8848/nacos |
| MinIO | http://localhost:9001 |
| FUXA (full) | http://localhost:1881 |
| PANEL (활성화 시) | http://localhost:9200 |

---

## 4. 자주 사용하는 명령

| 명령 | 설명 |
|------|------|
| `bootstrap` | 사전 의존성 설치(bash4 + Docker); mirrors / resources 시도 |
| `check` | 사전 자가 점검(목록 출력; 부족 항목 안내) |
| `mirrors` | 국내 `registry-mirrors` 구성(Linux와 동일) |
| `resources` | 형태별 Docker CPU/메모리/디스크 조정(`resources force`로 강제 재작성) |
| `install` | 이미지 pull 후 설치·기동 |
| `pull` / `update` | pull만 / 최신 pull 후 재시작 |
| `start` / `stop` / `restart` | 기동·중지 |
| `status` / `logs` / `verify` | 상태, 로그, 헬스 체크 |
| `profile` / `menu` / `help` | 사양, 대화형 메뉴, 도움말 |

```bash
bash .scripts/docker/install_mac.sh start
bash .scripts/docker/install_mac.sh stop
bash .scripts/docker/install_mac.sh logs VIDEO
bash .scripts/docker/install_mac.sh update
```

로그 디렉터리: `.scripts/docker/logs/install_mac_*.log`

---

## 5. 주의사항 및 문제 해결

| 문제 | 처리 |
|------|------|
| bash 4+ 필요 | `brew install bash` 후 `/opt/homebrew/bin/bash`로 실행; 또는 먼저 `bootstrap` |
| Docker daemon 미준비 | Docker Desktop 실행 후 고래 아이콘이 안정될 때까지 대기 |
| 엔진 메모리 부족 / OOM | `EASYAIOT_DEPLOY_PROFILE=full bash .scripts/docker/install_mac.sh resources`; 또는 Desktop → Settings → Resources ≥24GB |
| 미들웨어 pull 실패 | `bash .scripts/docker/install_mac.sh mirrors` 후 `docker info`로 Registry Mirrors 확인; FUXA는 `pull_fuxa.sh` 로그 |
| 비즈니스 이미지(cnb) pull 실패 | `registry-mirrors`는 `docker.cnb.cool`에 적용되지 않음; 네트워크 / 프록시 / `runtime_registry.conf` 확인 |
| Nacos 장시간 unhealthy | `NACOS_PLATFORM=linux/arm64` 확인; 콜드 스타트는 수 분 소요 가능; `docker logs nacos-server` |
| iot-tdengine Restarting | `tdengine-server` healthy 확인 후 `start` |
| 미디어 주소 / GB28181 이상 | `export HOST_IP=<로컬 LAN IP>` 후 `start` / `install` 재실행 |
| 실수로 `build` | 데스크톱은 거부함; `pull` + `install` 사용 |
| SRS 등 데이터 디렉터리 | 미디어 루트 `EASYAIOT_MEDIA_ROOT` (기본 `/mnt/easyaiot-media`; 데스크톱 fallback `$HOME/easyaiot/media`) |
| Colima와 Desktop 혼용 | `docker context use desktop-linux`(또는 `colima`); 배포 전 엔진 하나만 유지 |

프로덕션 및 전체 로컬 빌드는 Linux 사용: `.scripts/docker/install_linux.sh`.
