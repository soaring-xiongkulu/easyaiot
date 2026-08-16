#!/usr/bin/env bash
# EasyAIoT RTC 模块安装脚本
#
# 用法:
#   bash RTC/install_linux.sh install   # 安装并启动（统一部署入口）
#   bash RTC/install_linux.sh start|stop|restart|status|logs|update|clean
#   bash RTC/install_linux.sh build     # 构建 Docker 镜像
#   bash RTC/install_linux.sh vendor    # 拉取/更新 go2rtc 源码
#   bash RTC/install_linux.sh rebuild   # 重建镜像并启动
#   bash RTC/install_linux.sh dev       # 本地开发模式（不依赖 Docker）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
EASYAIOT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# shellcheck source=../.scripts/docker/deploy_profile.sh
source "${EASYAIOT_ROOT}/.scripts/docker/deploy_profile.sh"
# shellcheck source=../.scripts/docker/gpu_compose_helpers.sh
source "${EASYAIOT_ROOT}/.scripts/docker/gpu_compose_helpers.sh"
# shellcheck source=../.scripts/docker/module_update_helpers.sh
source "${EASYAIOT_ROOT}/.scripts/docker/module_update_helpers.sh"

RTC_IMAGE="${RTC_IMAGE:-rtc-service:latest}"
RTC_NAME="${RTC_NAME:-rtc-service}"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yaml"
GO2RTC_REPO="${GO2RTC_REPO:-https://github.com/AlexxIT/go2rtc.git}"
VENDOR_DIR="${SCRIPT_DIR}/vendor/go2rtc"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

need_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    print_error "需要 Docker"
    exit 1
  fi
}

detect_compose() {
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
  else
    print_error "需要 docker compose"
    exit 1
  fi
}

rtc_compose() {
  # 显式 -f 时会忽略 COMPOSE_FILE，需手动拼上桌面端 / source-free override
  local -a files=(-f "$COMPOSE_FILE")
  if [ -f docker-compose.desktop.yaml ] && { [ -n "${EASYAIOT_DESKTOP_OS:-}" ] || [ "${EASYAIOT_COMPOSE_DESKTOP:-0}" = "1" ]; }; then
    files+=(-f docker-compose.desktop.yaml)
  fi
  append_source_free_compose_file files
  $COMPOSE_CMD "${files[@]}" "$@"
}

ensure_env() {
  if [ ! -f "${SCRIPT_DIR}/.env.docker" ]; then
    cp "${SCRIPT_DIR}/env.example" "${SCRIPT_DIR}/.env.docker"
    print_info "已生成 .env.docker"
  fi
  if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    cp "${SCRIPT_DIR}/env.example" "${SCRIPT_DIR}/.env"
    print_info "已生成 .env"
  fi
  mkdir -p "${SCRIPT_DIR}/data/config"
  ensure_deploy_profile 2>/dev/null || true
}

pull_vendor() {
  print_info "拉取 go2rtc 源码 → ${VENDOR_DIR}"
  if ! easyaiot_have_git; then
    if [ -f "${VENDOR_DIR}/go.mod" ]; then
      print_warning "未安装 git，使用已有 vendor/go2rtc"
      return 0
    fi
    print_error "未安装 git，且缺少 ${VENDOR_DIR}；请安装 git 或一键 update 选「拉取预构建镜像」"
    return 1
  fi
  if [ -d "${VENDOR_DIR}/.git" ]; then
    git -C "${VENDOR_DIR}" pull --ff-only || {
      print_warning "git pull 失败，尝试重新 clone ..."
      rm -rf "${VENDOR_DIR}"
      git clone --depth 1 "${GO2RTC_REPO}" "${VENDOR_DIR}"
    }
  else
    mkdir -p "${SCRIPT_DIR}/vendor"
    git clone --depth 1 "${GO2RTC_REPO}" "${VENDOR_DIR}"
  fi
  print_success "go2rtc 版本: $(git -C "${VENDOR_DIR}" describe --tags --always 2>/dev/null || echo unknown)"
}

cleanup_renamed_containers() {
  local names
  names=$(docker ps -a --format '{{.Names}}' 2>/dev/null | grep -E '^[0-9a-f]{12}_rtc-service$' || true)
  [ -z "$names" ] && return 0
  print_warning "清理上次中断遗留的改名孤儿容器: $(echo "$names" | tr '\n' ' ')"
  echo "$names" | xargs -r docker rm -f >/dev/null 2>&1 || true
}

do_build() {
  need_docker
  if [ ! -f "${VENDOR_DIR}/go.mod" ]; then
    pull_vendor
  fi
  local platform_opts=""
  if [ -n "${DOCKER_PLATFORM:-}" ]; then
    platform_opts="--platform ${DOCKER_PLATFORM}"
    print_info "构建目标平台: ${DOCKER_PLATFORM}"
  fi
  print_info "构建镜像 ${RTC_IMAGE} ..."
  # shellcheck disable=SC2086
  docker build ${platform_opts} -t "${RTC_IMAGE}" -f "${SCRIPT_DIR}/Dockerfile" "${SCRIPT_DIR}"
  print_success "镜像构建完成: ${RTC_IMAGE}"
}

do_install() {
  need_docker
  detect_compose
  ensure_env

  if [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ] && docker image inspect "${RTC_IMAGE}" >/dev/null 2>&1; then
    print_success "镜像已从远程拉取 (${RTC_IMAGE})，跳过 Docker 构建"
  else
    do_build
  fi

  cleanup_renamed_containers
  rtc_compose up -d --remove-orphans
  print_success "RTC 服务安装完成"
  print_info "管理服务: http://localhost:6100"
  print_info "go2rtc UI: http://localhost:1984"
  print_info "健康检查: http://localhost:6100/actuator/health"
}

do_start() {
  need_docker
  detect_compose
  ensure_env
  if ! docker image inspect "${RTC_IMAGE}" >/dev/null 2>&1; then
    if [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ]; then
      print_error "镜像 ${RTC_IMAGE} 不存在，且已设置跳过构建"
      exit 1
    fi
    do_build
  fi
  cleanup_renamed_containers
  rtc_compose up -d --force-recreate --remove-orphans
  print_success "RTC 服务已启动"
  rtc_compose ps
}

do_stop() {
  need_docker
  detect_compose
  rtc_compose down
  print_success "RTC 服务已停止"
}

do_restart() {
  need_docker
  detect_compose
  ensure_env
  cleanup_renamed_containers
  rtc_compose up -d --force-recreate --remove-orphans
  print_success "RTC 服务已重启"
  rtc_compose ps
}

do_status() {
  need_docker
  detect_compose
  rtc_compose ps
  if docker ps --filter "name=${RTC_NAME}" --format '{{.Names}}' | grep -q "${RTC_NAME}"; then
    local health
    health=$(docker inspect --format='{{.State.Health.Status}}' "${RTC_NAME}" 2>/dev/null || echo "N/A")
    echo "健康状态: ${health}"
  else
    print_warning "服务未运行"
  fi
}

do_logs() {
  need_docker
  detect_compose
  rtc_compose logs -f --tail=100
}

do_update() {
  need_docker
  detect_compose
  ensure_env
  if easyaiot_update_should_recreate_only "${RTC_IMAGE}"; then
    :
  elif [ "${EASYAIOT_SKIP_BUILD:-0}" != "1" ]; then
    do_build
  elif ! docker image inspect "${RTC_IMAGE}" >/dev/null 2>&1; then
    print_error "镜像 ${RTC_IMAGE} 不存在，且已设置跳过构建"
    exit 1
  fi
  cleanup_renamed_containers
  rtc_compose up -d --force-recreate --remove-orphans
  print_success "RTC 服务已更新"
  rtc_compose ps
}

do_clean() {
  need_docker
  detect_compose
  rtc_compose down --rmi local 2>/dev/null || rtc_compose down || true
  docker rmi "${RTC_IMAGE}" 2>/dev/null || true
  print_success "RTC 容器与本地镜像已清理"
}

do_dev() {
  ensure_env
  pull_vendor
  if ! command -v go2rtc >/dev/null 2>&1; then
    print_warning "本地开发需先安装 go2rtc 二进制，或运行: bash install_linux.sh build && docker run ..."
    print_info "也可仅启动 Python 层（需外部 go2rtc 实例）"
  fi
  if [ ! -d "${SCRIPT_DIR}/.venv" ]; then
    python3 -m venv "${SCRIPT_DIR}/.venv"
  fi
  # shellcheck disable=SC1091
  source "${SCRIPT_DIR}/.venv/bin/activate"
  pip install -q -r "${SCRIPT_DIR}/requirements.txt"
  print_info "开发模式启动 Python 管理服务 ..."
  python "${SCRIPT_DIR}/run.py"
}

cmd="${1:-start}"
case "$cmd" in
  vendor|update-vendor) pull_vendor ;;
  build) do_build ;;
  install) do_install ;;
  start|up) do_start ;;
  stop|down) do_stop ;;
  restart) do_restart ;;
  status|ps) do_status ;;
  logs) do_logs ;;
  update) do_update ;;
  clean) do_clean ;;
  rebuild) do_build; detect_compose; ensure_env; rtc_compose up -d --force-recreate ;;
  dev) do_dev ;;
  help|--help|-h)
    echo "用法: $0 {install|start|stop|restart|status|logs|build|update|clean|vendor|rebuild|dev}"
    ;;
  *)
    echo "用法: $0 {install|start|stop|restart|status|logs|build|update|clean|vendor|rebuild|dev}"
    exit 1
    ;;
esac
