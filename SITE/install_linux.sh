#!/bin/bash
# ============================================
# SITE 官方网站 Docker Compose 管理脚本
# ============================================
# 用法: ./install_linux.sh [install|start|stop|restart|status|logs|build|clean|update]
# 统一入口：
#   ./.scripts/docker/install_linux.sh site [子命令]
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
EASYAIOT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${EASYAIOT_ROOT}/.scripts/docker/init-build-cache-dirs.sh" ]; then
    # shellcheck source=../.scripts/docker/init-build-cache-dirs.sh
    source "${EASYAIOT_ROOT}/.scripts/docker/init-build-cache-dirs.sh"
fi
if [ -f "${EASYAIOT_ROOT}/.scripts/docker/deploy_profile.sh" ]; then
    # shellcheck source=../.scripts/docker/deploy_profile.sh
    source "${EASYAIOT_ROOT}/.scripts/docker/deploy_profile.sh"
fi
if [ -z "${RUNTIME_IMAGE_COMMON_LOADED:-}" ] && [ -f "${EASYAIOT_ROOT}/.scripts/docker/runtime_image_common.sh" ]; then
    _site_saved_script_dir="$SCRIPT_DIR"
    SCRIPT_DIR="${EASYAIOT_ROOT}/.scripts/docker"
    # shellcheck source=../.scripts/docker/runtime_image_common.sh
    source "${SCRIPT_DIR}/runtime_image_common.sh"
    SCRIPT_DIR="$_site_saved_script_dir"
fi

COMPOSE_CMD=""
SITE_PORT="${SITE_PORT:-8090}"

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_command() {
    command -v "$1" &>/dev/null
}

ensure_docker() {
    if ! check_command docker; then
        print_error "Docker 未安装"
        exit 1
    fi
    if check_command docker-compose; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &>/dev/null; then
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose 未安装"
        exit 1
    fi
}

ensure_network() {
    if ! docker network inspect easyaiot-network &>/dev/null; then
        print_info "创建 docker 网络 easyaiot-network"
        docker network create easyaiot-network >/dev/null
    fi
}

cleanup_renamed_containers() {
    local names
    names=$(docker ps -a --format '{{.Names}}' 2>/dev/null | grep -E '^[0-9a-f]{12}_site-service$' || true)
    [ -z "$names" ] && return 0
    print_warning "清理改名孤儿容器: $(echo "$names" | tr '\n' ' ')"
    echo "$names" | xargs -r docker rm -f >/dev/null 2>&1 || true
}

site_pull_prebuilt_image() {
    type runtime_load_registry >/dev/null 2>&1 || return 1
    type runtime_remote_ref >/dev/null 2>&1 || return 1
    runtime_load_registry
    export REGISTRY="${REGISTRY:-$RUNTIME_IMAGE_REGISTRY}"
    local arch rref lref
    arch=$(runtime_detect_arch)
    rref=$(runtime_remote_ref "aiot-site" "" "$arch")
    lref=$(runtime_local_ref "site-service")
    print_info "尝试拉取远程镜像: ${rref}"
    if docker pull "$rref" 2>/dev/null; then
        docker tag "$rref" "$lref" 2>/dev/null || true
        print_success "预构建镜像拉取成功: ${lref}"
        return 0
    fi
    return 1
}

build_image() {
    ensure_docker
    if [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ] && docker image inspect site-service:latest >/dev/null 2>&1; then
        print_success "镜像已存在且 EASYAIOT_SKIP_BUILD=1，跳过构建"
        return 0
    fi
    if [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ] && site_pull_prebuilt_image; then
        return 0
    fi

    print_info "构建 site-service 镜像..."
    mkdir -p "${SCRIPT_DIR}/logs" "${SCRIPT_DIR}/docker-build-logs"
    local ts cache_bust
    ts=$(date +%Y%m%d-%H%M%S)
    cache_bust=$(git -C "$SCRIPT_DIR" rev-parse HEAD 2>/dev/null || echo "nogit")

    local platform_opts=()
    if [ -n "${DOCKER_PLATFORM:-}" ]; then
        platform_opts+=(--platform "$DOCKER_PLATFORM")
    fi

    DOCKER_BUILDKIT=1 docker build \
        --build-context "webconf=${EASYAIOT_ROOT}/WEB/conf" \
        --build-arg "CACHE_BUST=${cache_bust}" \
        --build-arg "SKIP_VITE_BUILD=${SKIP_VITE_BUILD:-0}" \
        --build-arg "NPM_REGISTRY=${NPM_REGISTRY:-https://registry.npmmirror.com/}" \
        --build-arg "APK_MIRROR=${APK_MIRROR:-mirrors.tuna.tsinghua.edu.cn}" \
        "${platform_opts[@]}" \
        -t site-service:latest \
        -f Dockerfile \
        . 2>&1 | tee "${SCRIPT_DIR}/docker-build-logs/docker-build-${ts}.log"

    print_success "镜像构建完成: site-service:latest"
}

compose_up() {
    ensure_docker
    ensure_network
    cleanup_renamed_containers
    mkdir -p "${SCRIPT_DIR}/logs"
    export SITE_PORT
    $COMPOSE_CMD -f docker-compose.yaml up -d --remove-orphans
    print_success "SITE 已启动 → http://localhost:${SITE_PORT}"
}

compose_down() {
    ensure_docker
    $COMPOSE_CMD -f docker-compose.yaml down --remove-orphans || true
    cleanup_renamed_containers
    print_success "SITE 已停止"
}

start_service() {
    if ! docker image inspect site-service:latest >/dev/null 2>&1; then
        if ! site_pull_prebuilt_image; then
            build_image
        fi
    fi
    compose_up
}

install_service() {
    print_info "安装 SITE 官方网站模块"
    if [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ] && site_pull_prebuilt_image; then
        compose_up
        return 0
    fi
    build_image
    compose_up
}

show_status() {
    ensure_docker
    $COMPOSE_CMD -f docker-compose.yaml ps
    if docker ps --format '{{.Names}}' | grep -qx 'site-service'; then
        print_info "健康检查: $(curl -fsS "http://127.0.0.1:${SITE_PORT}/health" 2>/dev/null || echo unavailable)"
    fi
}

show_logs() {
    ensure_docker
    $COMPOSE_CMD -f docker-compose.yaml logs -f --tail=200
}

clean_service() {
    compose_down
    docker rmi site-service:latest >/dev/null 2>&1 || true
    print_success "SITE 容器与本地镜像已清理"
}

update_service() {
    build_image
    compose_up
}

usage() {
    cat <<EOF
SITE 官方网站管理脚本

用法: $0 [命令]

命令:
  install   构建并启动
  start     启动（缺镜像则构建/拉取）
  stop      停止
  restart   重启
  status    状态
  logs      日志
  build     仅构建镜像
  clean     停止并删除镜像
  update    重新构建并启动
EOF
}

main() {
    local cmd="${1:-install}"
    case "$cmd" in
        install)  install_service ;;
        start)    start_service ;;
        stop)     compose_down ;;
        restart)  compose_down; start_service ;;
        status)   show_status ;;
        logs)     show_logs ;;
        build)    build_image ;;
        clean)    clean_service ;;
        update)   update_service ;;
        -h|--help|help) usage ;;
        *)
            print_error "未知命令: $cmd"
            usage
            exit 1
            ;;
    esac
}

main "$@"
