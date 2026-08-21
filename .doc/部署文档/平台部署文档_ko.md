# EasyAIoT 플랫폼 배포 가이드

> 첫 배포는 [빠른 시작](#빠른-시작)을 참조하세요. 고급 운영, GPU, 데이터베이스 및 문제 해결은 [배포 모범 사례](./部署最佳实践_ko.md)를 참조하세요.

---

## 목차

- [개요](#개요)
- [두 가지 사용 모드](#두-가지-사용-모드)
- [빠른 시작](#빠른-시작)
- [배포 프로필](#배포-프로필)
- [스크립트 명령 참조](#스크립트-명령-참조)
- [서비스 접속 및 포트](#서비스-접속-및-포트)
- [FAQ](#faq)
- [환경 요구사항](#환경-요구사항)

---

## 개요

EasyAIoT는 **Docker 컨테이너와 통합 설치 스크립트**를 통해 배포됩니다. 플랫폼은 기본 미들웨어와 DEVICE, AI, VIDEO, WEB, APP 비즈니스 모듈로 구성됩니다.

| 모듈 | 디렉터리 | 설명 |
|------|------|------|
| 기본 서비스 | `.scripts/docker` | Nacos, PostgreSQL, Redis, Kafka, MinIO 등 |
| DEVICE | `DEVICE/` | 장치 관리 및 API 게이트웨이 (Java / Spring Cloud) |
| AI | `AI/` | 모델 학습 및 추론 (Python) |
| VIDEO | `VIDEO/` | 비디오 스트리밍, 알림, 녹화 (Python) |
| WEB | `WEB/` | 관리 콘솔 (Vue 3) |
| APP | `APP/` | 모바일 H5 (**full** 프로필만) |

**통합 진입 스크립트** (아래 Linux x86 예시):

| OS | 스크립트 |
|----|--------|
| Linux x86 | `.scripts/docker/install_linux.sh` |
| CentOS / RHEL (x86) | `.scripts/docker/install_linux_centos.sh` |
| **CentOS / RHEL · ARM** | `.scripts/docker/install_linux_centos_arm.sh` |
| **Kylin (麒麟)** | `.scripts/docker/install_linux_kylin.sh` |
| **openEuler (欧拉)** | `.scripts/docker/install_linux_openeuler.sh` |
| Linux ARM (일반) | `.scripts/docker/install_linux_arm.sh` |
| macOS | `.scripts/docker/install_mac.sh` |
| Windows | `.scripts/docker/install_windows.ps1` / `install_windows.sh` |

---

## 두 가지 사용 모드

통합 진입 스크립트는 **대화형 안내**와 **직접 명령** 모드를 지원하며, 기본 기능은 동일합니다:

| | 대화형 | 직접 명령 |
|---|---|---|
| **진입** | 인수 없음 / `menu` / `interactive` | `<명령> [인수]` |
| **사용 사례** | 첫 배포, 현장 운영, 문제 해결 | 개발, 스크립트 운영, CI/CD |
| **조작** | 메뉴 기반, 숫자 선택 | 하위 명령 직접 실행 |
| **실행 후** | 현재 메뉴 수준으로 복귀 | 완료 시 종료 |

```bash
# 대화형
sudo .scripts/docker/install_linux.sh

# 직접 명령
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh status
```

**선택 가이드:**

- 일상적인 수동 운영, 명령 인수에 익숙하지 않음 → 대화형
- 작업을 알고 있으며 스크립트 또는 cron 작업에 사용 → 직접 명령 (Cron/CI에서 **인수 없이** 호출하지 마세요 — 입력 대기로 블로킹됩니다)

### 대화형: 메뉴 구조

**루트 메뉴**

```
  1) Deploy — install, start/stop, update, status, logs
  2) Analyze — log merge, disk usage, health checks
  0) Exit
```

**[Deploy] 하위 메뉴**

| # | 작업 | 동등 명령 |
|:-:|------|----------|
| 1 | 첫 설치 및 시작 | `install` |
| 2 | 모든 서비스 시작 | `start` |
| 3 | 모든 서비스 중지 | `stop` |
| 4 | 모든 서비스 재시작 | `restart` |
| 5 | 실행 상태 보기 | `status` |
| 6 | 로그 보기 | `logs` |
| 7 | 상태 검증 | `verify` |
| 8 | 이미지 업데이트 및 재시작 | `update` |
| 9 | Docker 환경 확인 | `check` |
| 10 | 배포 프로필 보기 | `profile` |
| 11 | 전체 CLI 도움말 | `help` |

**[Analyze] 하위 메뉴**

| # | 작업 | 동등 명령 |
|:-:|------|----------|
| 1 | 다중 모듈 로그 병합(소스당 ~500줄) | `analyze-logs` |
| 2 | 디스크 사용량 분석 | `analyze-disk` |
| 3 | 상태 + 상태 검증 | `status` + `verify` |
| 4 | Docker 환경 확인 | `check` |

**일반적인 경로:**

| 시나리오 | 대화형 경로 |
|----------|-------------|
| 첫 배포 | 1 → 1 → 7 |
| 재부팅 후 시작 | 1 → 2 → 7 |
| 진단 정보 수집 | 2 → 3 → 1 → 2 |

---

## 빠른 시작

README를 열자마자 속으로: 「이거… 내 허접한 기계에서 돌아갈까?」 — **됩니다. 겁먹지 마세요.**

가장 가벼운 등급 **edge**, 컨테이너 총 사용 약 **1 GB**. 카메라 접속·실시간 분석·스마트 경보, 작은 기계로도 폐루프. 낡은 노트북부터 돌려 보세요 — 맛 들리면 그때 올려타도 됩니다.

### 세 단계로 탑승 (권장 경량 등급)

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# 방식 A (권장)
EASYAIOT_DEPLOY_PROFILE=edge sudo bash .scripts/docker/install_linux.sh install

# 방식 B
# sudo bash .scripts/docker/install_linux.sh edge install
```

설치 후 브라우저에서 `https://<서버IP>:8888` — 기본 계정 `admin` / `admin123`. 검증:

```bash
.scripts/docker/install_linux.sh verify
# 선택: 메모리가 등급 한도 안인지 한 번 더 확인
.scripts/docker/install_linux.sh resources
```

초록불이 떴다면 퇴근입니다 — 생각보다 쉽죠. 오늘 커피는 일찍 마셔도 됩니다.

> 전체 프로필·대화형 메뉴·CentOS / ARM / openEuler 진입이 필요하면 아래 사전 요건과 두 가지 설치 방식을 이어 보세요.

### 사전 요건

- OS: **Ubuntu 24.04+** (26.04 권장); **CentOS/RHEL**, ARM, **Kylin (麒麟) / openEuler (欧拉)**도 지원
- Docker + Docker Compose **v2.35+** (CentOS / **openEuler (欧拉)**에서는 OS 전용 진입 스크립트로 Docker CE 설치/업그레이드 가능)
- **≥ 300 GB** 여유 디스크 공간 (경량 **edge**는 훨씬 여유; 풀 등급은 이 정도 권장)

```bash
docker --version && docker compose version && docker ps
```

### 옵션 1: 대화형

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

sudo .scripts/docker/install_linux.sh
# CentOS / RHEL x86: sudo .scripts/docker/install_linux_centos.sh
# CentOS / RHEL ARM: sudo .scripts/docker/install_linux_centos_arm.sh
# openEuler: sudo .scripts/docker/install_linux_openeuler.sh
# 1 Deploy → 1 First install → 7 Health verify
```

첫 설치 시 프로필(**edge** 포함)을 대화형으로 선택합니다. 완료 후 `https://<server-ip>:8888`을 엽니다 (기본 `admin` / `admin123`).

### 옵션 2: 직접 명령

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# 선택: 사전 빌드 이미지를 가져와 설치 시간 단축
sudo .scripts/docker/install_linux.sh pull
# CentOS x86: sudo .scripts/docker/install_linux_centos.sh pull
# CentOS ARM: sudo .scripts/docker/install_linux_centos_arm.sh pull
# openEuler: sudo .scripts/docker/install_linux_openeuler.sh pull

sudo .scripts/docker/install_linux.sh install
# CentOS x86: sudo .scripts/docker/install_linux_centos.sh install
# CentOS ARM: sudo .scripts/docker/install_linux_centos_arm.sh install
# openEuler: sudo .scripts/docker/install_linux_openeuler.sh install

.scripts/docker/install_linux.sh verify
# 선택: 메모리가 등급 한도 안인지 한 번 더 확인
.scripts/docker/install_linux.sh resources
```

설치 후 `https://<server-ip>:8888`을 엽니다. 초록불이 떴다면 퇴근입니다 — 생각보다 쉽죠.

### CentOS / RHEL 참고

`.scripts/docker/install_linux_centos.sh` 사용 (CentOS 7/8/Stream, Rocky, Alma, RHEL · x86). 상세(ZH): [平台部署文档_zh.md](./平台部署文档_zh.md#centos--rhel-系说明).

### CentOS / RHEL · ARM 참고

`.scripts/docker/install_linux_centos_arm.sh` 사용 (aarch64/arm64 CentOS/RHEL). Docker CE / 미러 / firewalld 준비 후 `install_linux_arm.sh`에 위임. 상세(ZH): [平台部署文档_zh.md](./平台部署文档_zh.md#centos--rhel-系--arm-说明).

### **openEuler (欧拉)** 참고

`.scripts/docker/install_linux_openeuler.sh` 사용 (openEuler 24.03 LTS / 24.x). 시스템 `docker-engine` 제거, Docker CE 저장소 `$releasever` 수정, 미러/firewalld 구성 후 `install_linux.sh`에 위임. 상세(ZH): [平台部署文档_zh.md](./平台部署文档_zh.md#openeuler-24x-说明).

### 설치 소요 시간

| 시나리오 | 예상 시간 |
|----------|----------|
| 사전 빌드 이미지 가져옴 | 10–30분 |
| 로컬 전체 빌드 | 30분~수시간 |

`install` 흐름: 프로필 선택 → 환경 확인 → 네트워크 생성 → 미들웨어 및 모듈 배포 → 상태 대기. [원클릭 및 단계별 배포](./部署最佳实践_ko.md#원클릭-배포) 참조.

---

## macOS / Windows 이미지 전용 배포

데스크톱은 **사전 빌드 이미지**만 지원합니다 (`install_mac.sh` / `install_windows.ps1` / `install_windows.sh`). 로컬 `build` / `build-runtime` 불가. 상세: [macOS](./平台macOS部署文档_ko.md), [Windows](./平台Windows部署文档_ko.md). 개요(ZH): [平台部署文档_zh.md](./平台部署文档_zh.md#macos--windows-镜像部署).

```bash
bash .scripts/docker/install_mac.sh install
bash .scripts/docker/install_windows.sh install
```

---

## 배포 프로필

첫 `install` 시 대화형으로 선택되며 `.scripts/docker/.deploy_profile`에 저장됩니다. 이후 `start` / `stop` / `update`에서 재사용됩니다.

| 옵션 | 이름 | 권장 RAM | 사용 사례 |
|:------:|------|-----------------|----------|
| 0 | **edge** | ≥ 2 GB | 최경량 엣지 ( [빠른 시작](#빠른-시작) 참고) |
| 1 | **mini** | ≥ 8 GB | 엣지 노드, PoC |
| 2 | **standard** | ≥ 16 GB | 일반 프로덕션 |
| 3 | **full** (기본값) | ≥ 20 GB | 전체 기능 + APP H5 |

```bash
.scripts/docker/install_linux.sh profile                              # 현재 프로필 보기
export EASYAIOT_DEPLOY_PROFILE=full && sudo .../install_linux.sh install  # 비대화형
```

프로필별 서비스 차이: [배포 프로필 선택](./部署最佳实践_ko.md#배포-프로필-선택).

---

## 스크립트 명령 참조

### 명령

| 명령 | 설명 |
|------|------|
| `install` | 첫 설치 및 시작 |
| `start` / `stop` / `restart` | 수명 주기 제어 |
| `status` | 실행 상태 보기 |
| `logs [모듈]` | 로그 보기, 예: `logs VIDEO` |
| `verify` | 상태 점검 |
| `check` | Docker 환경 확인 |
| `update` | 이미지 업데이트 및 재시작 |
| `pull` | 사전 빌드 이미지 가져오기 |
| `build` |
| `runtime` / `runtime-atomic` | **RUNTIME 원자 모드**(실행기만 설치, `VIDEO_BASE_URL` 필요) |
| `build` | 로컬에서 이미지 재빌드 |
| `profile` | 배포 프로필 보기 |
| `analyze-logs` | 다중 모듈 로그 병합 |
| `analyze-disk` | 디스크 사용량 분석 |
| `diagnose` | [Analyze] 하위 메뉴 진입 |
| `clean` | 컨테이너 및 이미지 제거 ⚠️ (볼륨 포함) |
| `help` | 도움말 표시 |
| `menu` | 대화형 안내 열기 |

### 비대화형 로그 수집

```bash
cd .scripts/docker

./analyze_merge_logs.sh --non-interactive \
  --modules dev-iot-sink,dev-iot-message,biz-video --lines 500 --save

./analyze_merge_logs.sh --non-interactive --modules DEVICE --save
./analyze_disk_usage.sh --save --top 15
```

### 모드 대조

| 작업 | 대화형 | 직접 명령 |
|------|--------|----------|
| 첫 설치 | 1 → 1 | `install` |
| 서비스 시작 | 1 → 2 | `start` |
| 상태 점검 | 1 → 7 | `verify` |
| 로그 병합 | 2 → 1 | `analyze-logs` |
| 디스크 분석 | 2 → 2 | `analyze-disk` |

### 모듈별 배포

```bash
cd .scripts/docker && ./install_middleware_linux.sh install   # 미들웨어만
cd .scripts/docker && ./install_business_linux.sh install     # 비즈니스 모듈만
cd AI && ./install_linux.sh install                           # 단일 모듈
```

---

---

## RUNTIME 원자 모드(연산 노드)

**엣지 박스 / 클러스터 워커**용: 로컬에 VIDEO / WEB / DEVICE 없이 **C++ 실행기만** 설치. 경보·하트비트는 센터 VIDEO로 집약; 정식 `realtime` 작업은 기본으로 센터/클러스터 SRS `ai/`에 박스 검출 스트림을 푸시.

> **원자 ≠ 영상 미푸시.** 원자는 로컬 비즈니스 스택이 없다는 뜻. 상세: [`RUNTIME/README.md`](../../RUNTIME/README.md).

```bash
VIDEO_BASE_URL=http://<센터VIDEO>:6000 \
  bash .scripts/docker/install_linux.sh runtime

VIDEO_BASE_URL=http://192.168.1.10:6000 ./RUNTIME/install_linux.sh atomic
```

| 항목 | 설명 |
|------|------|
| 필수 | `VIDEO_BASE_URL` |
| 설치 경로 | 기본 `/opt/easyaiot/RUNTIME` |
| 산출물 | `bin/RUNTIME`, `node.env`, `env.sh`, `config/atomic.example.ini` |
| 정식 작업 | 센터 WEB에서 `executor=cpp` 알고리즘 작업 생성 |
| 스모크 | `source /opt/easyaiot/RUNTIME/env.sh && $RUNTIME_BIN …/atomic.example.ini` |

전체 스택은 계속 `install`; 로컬 VIDEO 설치의 RUNTIME 마운트와 원자 모드는 별개입니다.

---

## 서비스 접속 및 포트

`verify` 통과 후:

| 서비스 | URL |
|------|-----|
| WEB 콘솔 | https://\<server-ip\>:8888 |
| API Gateway | http://\<server-ip\>:48080 |
| Nacos | http://\<server-ip\>:8848/nacos |
| MinIO Console | http://\<server-ip\>:9001 |
| AI | http://\<server-ip\>:5000 |
| VIDEO | http://\<server-ip\>:6000 |
| APP H5 (full) | http://\<server-ip\>:9010 |

| 포트 | 서비스 |
|------|------|
| 8888 | WEB |
| 48080 | Gateway |
| 8848 | Nacos |
| 9000/9001 | MinIO |
| 5000 | AI |
| 6000 | VIDEO |
| 9010 | APP (full) |

전체 포트 목록: [환경 요구사항 및 배포 전 점검](./部署最佳实践_ko.md#환경-요구사항).

---

## FAQ

| 증상 | 해결 방법 |
|------|----------|
| Docker `permission denied` | `sudo usermod -aG docker $USER && newgrp docker` |
| Compose 버전이 너무 낮음 | `sudo apt install -y docker-compose-plugin` |
| 포트 사용 중 | `ss -tlnp \| grep <port>` |
| 설치 실패 | `tail .scripts/docker/logs/install_linux_*.log` |
| 서비스는 실행 중이나 접속 불가 | `verify` + 방화벽 확인 |
| 디스크 공간 부족 | `df -h /`, ≥ 300 GB 확보 |

**진단 정보 수집:**

```bash
# 대화형: 2 Analyze → 1 Logs + 2 Disk
# 직접 명령:
.scripts/docker/install_linux.sh check
.scripts/docker/install_linux.sh status
.scripts/docker/install_linux.sh verify
cd .scripts/docker && ./analyze_merge_logs.sh --non-interactive --modules all --save
./analyze_disk_usage.sh --save
```

자세한 내용: [문제 해결](./部署最佳实践_ko.md#문제-해결).

---

## 환경 요구사항

| 항목 | 요구사항 |
|------|----------|
| OS | Ubuntu 24.04+ (26.04 권장); macOS, Windows, CentOS/RHEL, ARM, **Kylin (麒麟) / openEuler (欧拉)**도 지원 |
| CPU | 최소 4코어, 8코어 이상 권장 |
| RAM | 프로필에 따라 다름 (full ≥ 20 GB, 32 GB 권장) |
| 디스크 | 최소 300 GB 여유, 500 GB+ SSD 권장 |
| GPU | 선택 사항; AI 학습/추론용 NVIDIA GPU (CUDA 12.8) |
| Docker Compose | v2.35.0+ |

```bash
# Docker 설치 (Ubuntu)
curl -fsSL https://get.docker.com | sudo sh
sudo apt install -y docker-compose-plugin
sudo usermod -aG docker $USER && newgrp docker
```

**참고 사항:**

1. 첫 설치 시 `sudo` 사용 (미러 가속 및 RTP 포트 예약)
2. 프로덕션에서 기본 미들웨어 비밀번호 변경 ([자격 증명](./部署最佳实践_ko.md#기본-자격-증명))
3. `clean`은 볼륨을 삭제합니다 — 먼저 백업하세요
4. 프로필 변경 후 WEB 재빌드: `cd WEB && ./install_linux.sh build`

---

**문서 버전**: 3.1  
**최종 업데이트**: 2026-07-08  
**스크립트 진입점**: `.scripts/docker/install_linux.sh` (인수 없음 = 대화형; `<명령>` = 직접 실행)
