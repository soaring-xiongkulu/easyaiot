# EasyAIoT 배포 모범 사례

> 이 문서는 프로젝트 스크립트와 동기화되며, 프로덕션 배포 및 운영을 다룹니다.  
> 빠른 시작은 [플랫폼 배포 가이드](./平台部署文档_ko.md)를 참조하세요.

---

## 목차

- [두 가지 사용 모드 (상세)](#두-가지-사용-모드-상세)
- [5분 배포 흐름](#5분-배포-흐름)
- [배포 프로필 선택](#배포-프로필-선택)
- [환경 요구 사항 및 배포 전 점검](#환경-요구-사항-및-배포-전-점검)
- [원클릭 및 단계별 배포](#원클릭-및-단계별-배포)
- [RUNTIME 원자 모드(경량 연산 노드)](#runtime-원자-모드경량-연산-노드)
- [일반 운영](#일반-운영)
- [사전 빌드 이미지](#사전-빌드-이미지)
- [GPU 구성](#gpu-구성)
- [특수 환경](#특수-환경)
- [데이터베이스 참고 사항](#데이터베이스-참고-사항)
- [기본 자격 증명](#기본-자격-증명)
- [문제 해결](#문제-해결)
- [로그 위치](#로그-위치)
- [업데이트 및 제거](#업데이트-및-제거)
- [아키텍처 참조](#아키텍처-참조)

---

## 두 가지 사용 모드 (상세)

통합 진입 스크립트(`install_linux.sh` / `install_linux_centos.sh` / `install_linux_centos_arm.sh` / `install_linux_openeuler.sh` / `install_linux_arm.sh` / `install_linux_kylin.sh`)는 **두 가지 동등한 사용 패턴**을 지원합니다:

| 모드 | 진입 | 대상 | 특징 |
|------|------|------|------|
| **대화형** | 인수 없음 / `menu` / `interactive` | 현장 운영, 수동 작업 | 메뉴 기반, 단계별, 실행 후 현재 메뉴로 복귀 |
| **직접 명령** | `<command> [args]` | 개발, SRE, CI/CD | 스크립트화 가능, 반복 실행, 완료 시 종료 |

```bash
# 대화형
sudo .scripts/docker/install_linux.sh

# 직접 명령
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh status
```

**선택 가이드:** 수동 운영에는 대화형을, 스크립트 시나리오(Cron / Ansible / CI)에는 직접 명령을 사용하세요. 자동화에서 인수 없이 호출하지 **마세요**.

### 대화형: 메뉴 구조

**루트 메뉴**

```
  1) Deploy — install, start/stop, update, status, logs
  2) Analyze — logs, disk, status diagnostics
  0) Exit
```

**[Deploy] 하위 메뉴**

| # | 작업 | 동등 명령 |
|:-:|------|----------|
| 1 | 최초 설치 및 시작 | `install` |
| 2 | 모든 서비스 시작 | `start` |
| 3 | 모든 서비스 중지 | `stop` |
| 4 | 모든 서비스 재시작 | `restart` |
| 5 | 상태 보기 | `status` |
| 6 | 로그 보기 | `logs` |
| 7 | 상태 검증 | `verify` |
| 8 | 이미지 업데이트 및 재시작 | `update` |
| 9 | Docker 환경 점검 | `check` |
| 10 | 배포 프로필 보기 | `profile` |
| 11 | 전체 CLI 도움말 | `help` |

**[Analyze] 하위 메뉴** — 지원팀에 적합한 출력

| # | 작업 | 동등 명령 |
|:-:|------|----------|
| 1 | 다중 모듈 로그 병합 | `analyze-logs` |
| 2 | 디스크 사용량 분석 | `analyze-disk` |
| 3 | 상태 + 상태 검증 | `status` + `verify` |
| 4 | Docker 환경 점검 | `check` |

**로그 병합 내부 메뉴** (Analyze → 1에서): 번호로 소스 선택(예: `24,23,27`), `0` = 현재 프로필 전체, `b` = [Analyze]로 돌아가기.

### 직접 명령: 전체 참조

```bash
cd .scripts/docker   # 또는 프로젝트 루트에서 .scripts/docker/install_linux.sh 사용

# 라이프사이클
./install_linux.sh install | start | stop | restart | update | clean

# 관측
./install_linux.sh status | logs | logs WEB | verify | check | profile

# 빌드 및 이미지
./install_linux.sh build | pull | build-runtime [module]

# 진단
./install_linux.sh diagnose          # [Analyze] 하위 메뉴 진입 (여전히 대화형)
./install_linux.sh analyze-logs      # 로그 병합
./install_linux.sh analyze-disk      # 디스크 보고서

# 도움말
./install_linux.sh help | menu
```

### 분석 도구: 고급 사용법

`.scripts/docker/`의 분석 스크립트는 독립 실행 가능합니다:

**다중 모듈 로그 병합 `analyze_merge_logs.sh`**

```bash
cd .scripts/docker

# 비대화형 (런북에 권장)
./analyze_merge_logs.sh --non-interactive \
  --modules dev-iot-sink,dev-iot-message,biz-video --lines 500 --save

# 모듈 별칭
./analyze_merge_logs.sh --non-interactive --modules DEVICE
./analyze_merge_logs.sh --non-interactive --modules .scripts/docker
./analyze_merge_logs.sh --non-interactive --modules all --save

# 일반 단위 ID: mw-nacos / mw-postgres / dev-iot-gateway / dev-iot-sink / biz-ai / biz-video / biz-web
./analyze_merge_logs.sh --help
```

수집 전략: `docker logs`(마지막 N줄) → 컨테이너 불가 시 호스트 로그 파일 → 최신 로테이션 파일 tail.

**디스크 사용량 `analyze_disk_usage.sh`**

```bash
./analyze_disk_usage.sh                  # 터미널 보고서
./analyze_disk_usage.sh --save           # logs/disk_usage_*.log에 저장
./analyze_disk_usage.sh --top 20
```

주요 디렉터리: MinIO `record-space` / `alert-images`, 로컬 `playbacks`, 알림 이미지 스테이징.

### 자동화 참고 사항

- Cron / Ansible / CI는 인수 없이 호출하면 **안 됩니다** (메뉴에서 대기)
- 메뉴 트리거 작업은 `EASYAIOT_FROM_MENU=1`을 설정하여 설치 후 루트 메뉴로 돌아가지 않음
- 비대화형 프로필: `export EASYAIOT_DEPLOY_PROFILE=full`

### 모듈별 스크립트와의 관계

모듈 디렉터리(`DEVICE/`, `AI/`, `VIDEO/` …)에는 해당 모듈 전용 독립 `install_linux.sh`가 있으며, 통합 [Analyze] 메뉴는 **없습니다**.  
전체 플랫폼 오케스트레이션 + 대화형 가이드 + 모듈 간 로그/디스크 분석 → `.scripts/docker/install_linux.sh`만 사용하세요.

---

## 5분 배포 흐름

```bash
git clone https://gitee.com/volara/easyaiot.git && cd easyaiot

docker --version && docker compose version

# 옵션 A: 직접 명령
sudo .scripts/docker/install_linux.sh pull    # 선택: 사전 빌드 이미지
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh verify

# 옵션 B: 대화형
sudo .scripts/docker/install_linux.sh         # 1 Deploy → 1 Install → 7 Verify

# 접속: http://<server-ip>:8888
```

### 설치 소요 시간

| 시나리오 | 시간 |
|----------|------|
| 사전 빌드 이미지 pull 완료 | 10–30분 |
| 전체 로컬 빌드 | 30분 ~ 수 시간 |

---

## 배포 프로필 선택

첫 `install` 시 대화형으로 선택하거나 `export EASYAIOT_DEPLOY_PROFILE=mini|standard|full`로 지정합니다.  
`.scripts/docker/.deploy_profile`에 저장되며 `start` / `stop` / `update`에서 재사용됩니다.

| 프로필 | 별칭 | 권장 RAM | 사용 사례 |
|--------|------|----------|-----------|
| **mini** | `1` / `4g` | ≥ 8 GB | 엣지 노드, PoC |
| **standard** | `2` / `16g` | ≥ 16 GB | 일반 프로덕션 |
| **full** | `3` (기본값) | ≥ 20 GB | 전체 기능 + APP H5 |

```bash
.scripts/docker/install_linux.sh profile
```

### 프로필별 서비스

**mini**

- 비즈니스: `iot-system`, `iot-gateway`, `iot-sink`, `iot-infra`, VIDEO, AI, WEB
- 미들웨어: Nacos, PostgreSQL, Redis, Kafka, MinIO, SRS, EMQX
- 미시작: `iot-device`, `iot-dataset`, `iot-node`, `iot-visualize`, `iot-file`, `iot-message`, `iot-gb28181`, `iot-tdengine`, Milvus, ZLMediaKit, Node-RED, FUXA, TDengine, APP / VISUALIZE / TRANSFORM 등
- 이벤트 평면: standard/full과 동일 — MQTT → Gateway → iot-sink
- 미디어: 설치 시 NFS 미디어 스택 자동 준비 (`EASYAIOT_MEDIA_ROOT`)
- API 라우팅: Gateway(48080) 통합 진입

**standard**

- 미시작: TDengine, Node-RED, `iot-device`, `iot-tdengine`
- 나머지 모두 시작

**full**

- **APP 모바일 H5**(9010)를 포함한 모든 비즈니스 모듈 및 미들웨어

메모리 분석:

```bash
.scripts/docker/analyze_deploy_memory.sh
.scripts/docker/analyze_deploy_memory.sh --all-profiles
```

---

## 환경 요구 사항 및 배포 전 점검

### 하드웨어

| 리소스 | 최소 | 권장 |
|--------|------|------|
| CPU | 4코어 | 8코어 이상 |
| RAM | 프로필 참조 (full ≥ 20 GB) | 32 GB 이상 |
| 디스크 | **300 GB** 여유 | 500 GB 이상 SSD |
| GPU | 없음 (CPU 가능) | NVIDIA GPU (CUDA 12.8) |

### 소프트웨어

| 소프트웨어 | 요구 사항 |
|------------|-----------|
| OS | Ubuntu 24.04+ (26.04 권장); CentOS/RHEL, **Kylin (麒麟) / openEuler (欧拉)**, ARM64도 지원 |
| Docker | 설치 및 데몬 접근 가능 |
| Docker Compose | **v2.35.0+** (`docker compose` 플러그인) |
| NVIDIA Driver / Container Toolkit | GPU 시나리오만 |

### Docker 권한

```bash
sudo usermod -aG docker $USER && newgrp docker
docker ps   # permission denied 없이 성공해야 함
```

미러 및 RTP 포트 설정을 위해 최초 설치 시 `sudo`를 사용하세요.

### 배포 전 점검

```bash
.scripts/docker/detect_system_info.sh
.scripts/docker/install_linux.sh check
df -h / && docker system df
```

### 포트 요구 사항

| 포트 | 서비스 | 비고 |
|------|--------|------|
| 1880 | Node-RED | full/standard |
| 1883 | EMQX | full/standard |
| 1935 | SRS | RTMP |
| 5432 | PostgreSQL | 기본 데이터베이스 |
| 6000 | VIDEO | 비디오 처리 |
| 6030 | TDengine | full |
| 6080 | ZLMediaKit | 미디어 서버 |
| 6379 | Redis | 캐시 |
| 8848 | Nacos | 레지스트리/설정 |
| 8888 | WEB | 관리 UI |
| 9000/9001 | MinIO | 객체 스토리지 |
| 9010 | APP | full만 |
| 9092 | Kafka | 메시지 큐 |
| 19530 | Milvus | 벡터 DB |
| 48080 | Gateway | API 게이트웨이 |
| 5000 | AI | AI 서비스 |
| 30000-30500 | ZLM RTP | 스크립트가 예약 시도 |

```bash
ss -tlnp | grep -E '8848|5432|6379|9092|5000|6000|8888|48080'
```

---

## 원클릭 및 단계별 배포

### 원클릭

```bash
sudo .scripts/docker/install_linux.sh install
.scripts/docker/install_linux.sh verify
```

**자동 `install` 흐름:**

1. 프로필 선택 → `.deploy_profile`에 저장
2. 사전 빌드 이미지 감지 (pull 완료 시 로컬 빌드 건너뜀)
3. Docker / Compose / 컨테이너 생성 점검
4. 호스트 IP 감지 (`HOST_IP=<ip>`로 재정의 가능)
5. RTP 포트 30000-30500 예약 (root 필요)
6. Docker 미러 구성 (root 필요)
7. `easyaiot-network` 생성
8. 순서대로 배포: middleware → DEVICE → AI → VIDEO → WEB → APP (full)
9. PostgreSQL / Nacos / Redis 대기
10. 필요 시 edge Agent 확보

### 단계별

먼저 프로필 설정:

```bash
export EASYAIOT_DEPLOY_PROFILE=full
```

**1단계: 미들웨어**

```bash
cd .scripts/docker && ./install_middleware_linux.sh install
```

| 미들웨어 | 포트 | 용도 |
|----------|------|------|
| Nacos | 8848 | 레지스트리/설정 |
| PostgreSQL | 5432 | 기본 DB (6개 데이터베이스) |
| Redis | 6379 | 캐시 |
| Kafka | 9092 | 메시지 큐 |
| MinIO | 9000/9001 | 객체 스토리지 |
| Milvus | 19530/9091 | 벡터 DB |
| SRS | 1935 | 스트리밍 |
| EMQX | 1883 | MQTT (full/standard) |
| ZLMediaKit | 6080 | 미디어 서버 |
| TDengine | 6030 | 시계열 DB (full) |
| Node-RED | 1880 | 규칙 엔진 |

**2단계 이상: 비즈니스 모듈**

```bash
cd DEVICE && ./install_linux.sh install
cd AI    && ./install_linux.sh install
cd VIDEO && ./install_linux.sh install
cd WEB   && ./install_linux.sh install
cd APP   && ./install_linux.sh install   # full만
```

**비즈니스 모듈만**

```bash
cd .scripts/docker
./install_business_linux.sh install
./install_business_linux.sh update DEVICE WEB
./install_business_linux.sh verify
```

---

## RUNTIME 원자 모드(경량 연산 노드)

센터 풀스택과 경량 연산 노드를 분리 계획하세요:

| 역할 | 배포 내용 | 진입점 |
|------|-----------|--------|
| **센터 / 일체형** | 미들웨어 + DEVICE/AI/VIDEO/WEB…; VIDEO가 RUNTIME 자동 마운트 | `install_linux.sh install` |
| **연산 노드** | **RUNTIME만** | `VIDEO_BASE_URL=… install_linux.sh runtime` |
| **다중 노드** | SSH 일괄 배포 | WEB 「업무 런타임 배포」→ RUNTIME(C++) |

```bash
VIDEO_BASE_URL=http://<센터VIDEO>:6000 \
  sudo -E bash .scripts/docker/install_linux.sh runtime

./RUNTIME/install_linux.sh status
source /opt/easyaiot/RUNTIME/env.sh
```

필수 `VIDEO_BASE_URL`. 원자 ≠ 미푸시. mini/standard/full과 무관 — 연산 박스에서 전체 `install`을 다시 실행하지 마세요. 상세: [`RUNTIME/README.md`](../../RUNTIME/README.md).

---

## 일반 운영

### 통합 스크립트

```bash
./install_linux.sh install | start | stop | restart | status
./install_linux.sh logs | logs WEB | verify | check | profile
./install_linux.sh build | pull | update | clean
./install_linux.sh diagnose | analyze-logs | analyze-disk | help
```

### 모듈별 스크립트

각 모듈(`DEVICE` / `AI` / `VIDEO` / `WEB` / `APP`):

```bash
./install_linux.sh install | start | stop | restart | status | logs | build | clean | update
```

미들웨어:

```bash
cd .scripts/docker
./install_middleware_linux.sh install | start | stop | restart | status | logs | build | clean | update
```

### 환경 변수

| 변수 | 설명 |
|------|------|
| `EASYAIOT_DEPLOY_PROFILE` | `mini` / `standard` / `full` |
| `HOST_IP` | 호스트 IP 강제 지정 |
| `PARALLEL_MODULES=true` | 비즈니스 모듈 병렬 시작/업데이트 |
| `PARALLEL_BUILD=true` | 병렬 빌드 (OOM 방지를 위해 기본값은 순차) |
| `FORCE_NETWORK_RECREATE=true` | IP 변경 후 네트워크 재생성 |
| `EASYAIOT_RUNTIME_REGISTRY` | 사전 빌드 이미지 레지스트리 |

---

## 사전 빌드 이미지

설정: `.scripts/docker/runtime_registry.conf`

```bash
.scripts/docker/install_linux.sh pull                    # 대화형 pull
.scripts/docker/install_linux.sh build-runtime           # 빌드 및 push (CI/release)
.scripts/docker/install_linux.sh build-runtime DEVICE    # 단일 모듈
```

pull 후 `install` / `update`가 `.runtime_images_pulled`를 감지하고 컨테이너를 직접 시작합니다.

---

## GPU 구성

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi
```

자동 감지: GPU 있음 → `runtime: nvidia`; GPU 없음 → CPU 모드.

다중 GPU: `export CUDA_VISIBLE_DEVICES=0,1`

---

## 특수 환경

```bash
# CentOS / RHEL / Rocky / Alma x86 (Docker CE 자동 업그레이드, firewalld 포트 개방)
sudo .scripts/docker/install_linux_centos.sh install
# Docker만 준비: sudo .scripts/docker/install_linux_centos.sh --upgrade-docker-only

# CentOS / RHEL ARM (환경 준비 후 install_linux_arm.sh 위임)
sudo .scripts/docker/install_linux_centos_arm.sh install
# Docker만 준비: sudo .scripts/docker/install_linux_centos_arm.sh --upgrade-docker-only

# openEuler
sudo .scripts/docker/install_linux_openeuler.sh install
# Docker만 준비: sudo .scripts/docker/install_linux_openeuler.sh --upgrade-docker-only

# Kylin OS
sudo .scripts/docker/install_linux_kylin.sh install

# ARM64 (일반)
sudo .scripts/docker/install_linux_arm.sh install

# macOS / Windows
bash .scripts/docker/install_mac.sh install
bash .scripts/docker/install_windows.sh install
```

---

## 데이터베이스 참고 사항

### PostgreSQL (6개 데이터베이스, 스크립트는 `.scripts/postgresql/`)

| 데이터베이스 | 용도 |
|--------------|------|
| ruoyi-vue-pro20 | 시스템 관리 |
| iot-ai20 | AI 서비스 |
| iot-device10 | 디바이스 관리 |
| iot-gb2818110 | 영상 감시 |
| iot-message10 | 메시징 |
| iot-video10 | 비디오 처리 |

### TDengine

SQL은 `.scripts/tdengine/tdengine_super_tables.sql`에 있으며, full 프로필에서 자동 초기화됩니다.

### 백업

```bash
.scripts/postgresql/backup_databases.sh
```

---

## 기본 자격 증명

| 미들웨어 | 사용자명 | 비밀번호 | 콘솔 |
|----------|----------|----------|------|
| Nacos | nacos | nacos | :8848/nacos |
| PostgreSQL | postgres | iot45722414822 | — |
| Redis | — | basiclab@iot975248395 | — |
| MinIO | minioadmin | basiclab@iot975248395 | :9001 |
| EMQX | admin | basiclab@iot6874125784 | :18083 |
| Milvus | — | — | :9091 |

> **프로덕션에서는 모든 기본 비밀번호를 변경하세요.**

---

## 문제 해결

### 권장 흐름

**대화형:**

```
No args → 2 Analyze → 4 Docker check → 3 Status+health → 1 Logs → 2 Disk
```

**직접 명령:**

```bash
.scripts/docker/install_linux.sh check
.scripts/docker/install_linux.sh status
.scripts/docker/install_linux.sh verify

cd .scripts/docker
./analyze_disk_usage.sh --save
./analyze_merge_logs.sh --non-interactive --modules dev-iot-sink,biz-video,mw-nacos --lines 500 --save
```

### 일반적인 문제

**서비스 시작 실패**

```bash
docker ps -a
docker logs -f postgres-server
.scripts/docker/install_linux.sh logs
```

**네트워크 (호스트 IP 변경)**

```bash
export FORCE_NETWORK_RECREATE=true
.scripts/docker/install_linux.sh restart
```

**PostgreSQL / Redis**

```bash
.scripts/docker/fix_postgresql.sh
.scripts/docker/fix_redis.sh
```

**Docker 시스템**

```bash
sudo .scripts/docker/diagnose_docker_systemd.sh diagnose
.scripts/docker/cleanup_docker_space.sh
```

**Kafka 컨슈머 그룹**

```bash
cd VIDEO && ./fix_kafka_consumer_group.sh
```

**프로필 변경 후 WEB**

```bash
cd WEB && ./install_linux.sh build
```

---

## 로그 위치

| 위치 | 설명 |
|------|------|
| `.scripts/docker/logs/` | 설치 스크립트 로그; `merged_logs_*`, `disk_usage_*` 보고서 |
| `.scripts/docker/standalone-logs/` | Nacos 및 기타 미들웨어 디스크 로그 |
| `.build-cache/device/logs/` | DEVICE 마이크로서비스 Spring 로그 |
| `${EASYAIOT_MEDIA_ROOT:-/mnt/easyaiot-media}/srs.log` | SRS 스트리밍 (`deploy_profile`이 미디어 루트 해석) |
| `WEB/logs/runtime.log` | WEB 런타임 로그 |
| `docker logs <container>` | 컨테이너 stdout (AI/VIDEO에서 일반적) |

| 필요 | 대화형 | 직접 명령 |
|------|--------|----------|
| 마지막 500줄, 다중 서비스 | Analyze → 1 | `analyze-logs` 또는 `analyze_merge_logs.sh --modules ...` |
| 단일 모듈, 실시간 tail | Deploy → 6 | `logs VIDEO` 또는 `docker compose logs -f` |
| 설치 실패 | — | `tail .scripts/docker/logs/install_linux_*.log` |

---

## 업데이트 및 제거

```bash
git pull origin main
sudo .scripts/docker/install_linux.sh update
.scripts/docker/install_linux.sh verify
```

단일 모듈: `cd AI && ./install_linux.sh update`

제거:

```bash
sudo .scripts/docker/install_linux.sh clean   # ⚠️ 컨테이너, 이미지, 볼륨 삭제
```

---

## 아키텍처 참조

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEB Frontend (:8888)                          │
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

*문서 버전: 3.1 | 2026-07-08 | 스크립트 진입점: `.scripts/docker/install_linux.sh` (인수 없음=대화형; `<command>`=직접)*
