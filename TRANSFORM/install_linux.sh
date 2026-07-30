#!/bin/bash
# ============================================
# TRANSFORM 系统对接 Docker Compose 管理脚本
# 仅 full 全量部署形态启用
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

# shellcheck source=../.scripts/docker/deploy_profile.sh
source "${EASYAIOT_ROOT}/.scripts/docker/deploy_profile.sh"
if [ -z "${RUNTIME_IMAGE_COMMON_LOADED:-}" ]; then
    _tf_saved_script_dir="$SCRIPT_DIR"
    SCRIPT_DIR="${EASYAIOT_ROOT}/.scripts/docker"
    # shellcheck source=../.scripts/docker/runtime_image_common.sh
    source "${SCRIPT_DIR}/runtime_image_common.sh"
    SCRIPT_DIR="$_tf_saved_script_dir"
fi

COMPOSE_CMD=""
DOCKER_CHECKED=0
LOCAL_IMAGE="transform-service:latest"
REMOTE_NAME="aiot-transform"

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_command() { command -v "$1" &>/dev/null; }

check_docker() {
    [ "$DOCKER_CHECKED" = "1" ] && return 0
    if ! check_command docker; then
        print_error "Docker 未安装"
        exit 1
    fi
    DOCKER_CHECKED=1
}

check_docker_compose() {
    [ -n "$COMPOSE_CMD" ] && return 0
    if check_command docker-compose; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &>/dev/null; then
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose 未安装"
        exit 1
    fi
}

require_full_profile() {
    ensure_deploy_profile
    apply_transform_deploy_env "$EASYAIOT_ROOT"
    if [ "${EASYAIOT_DEPLOY_PROFILE:-full}" != "full" ]; then
        print_warning "TRANSFORM 仅在 full 全量部署形态下启用，当前: ${EASYAIOT_DEPLOY_PROFILE}"
        exit 1
    fi
}

transform_pull_prebuilt_image() {
    runtime_load_registry
    export REGISTRY="${REGISTRY:-$RUNTIME_IMAGE_REGISTRY}"
    local arch; arch=$(runtime_detect_arch)
    local rref; rref=$(runtime_remote_ref "$REMOTE_NAME" "" "$arch")
    local lref; lref=$(runtime_local_ref "transform-service")
    print_info "尝试拉取远程镜像: ${rref}"
    if docker pull "$rref" 2>/dev/null; then
        docker tag "$rref" "$lref" 2>/dev/null || true
        print_success "预构建镜像拉取成功: ${lref}"
        return 0
    fi
    return 1
}

transform_skip_build_from_pull() {
    [ "${EASYAIOT_SKIP_BUILD:-0}" != "1" ] && return 1
    docker image inspect "$LOCAL_IMAGE" >/dev/null 2>&1 || return 1
    print_success "镜像已从远程拉取 ($LOCAL_IMAGE)，跳过本地构建"
    return 0
}

ensure_jar() {
    local jar="transform-runtime/target/transform-runtime-1.0.0.jar"
    if [ -f "$jar" ]; then
        return 0
    fi
    print_info "未找到 $jar，执行 Maven 打包..."
    if ! check_command mvn; then
        print_error "需要 Maven 以本地构建 TRANSFORM（或先拉取预构建镜像）"
        return 1
    fi
    mvn -pl transform-runtime -am package -DskipTests -q
}

docker_build_image() {
    ensure_jar || return 1
    local platform_opts=""
    if [ -n "${DOCKER_PLATFORM:-}" ]; then
        platform_opts="--platform $DOCKER_PLATFORM"
        print_info "构建目标平台: ${DOCKER_PLATFORM}"
    fi
    # shellcheck disable=SC2086
    docker build $platform_opts -t "$LOCAL_IMAGE" -f Dockerfile .
}

cleanup_renamed_containers() {
    local names
    names=$(docker ps -a --format '{{.Names}}' 2>/dev/null | grep -E '^[0-9a-f]{12}_transform-service$' || true)
    [ -z "$names" ] && return 0
    print_warning "清理改名孤儿容器: $(echo "$names" | tr '\n' ' ')"
    echo "$names" | xargs -r docker rm -f >/dev/null 2>&1 || true
}

ensure_env_file() {
    if [ ! -f .env.docker ]; then
        print_info "生成 .env.docker ..."
        apply_transform_deploy_env "$EASYAIOT_ROOT"
    fi
    mkdir -p data/transform-backup
}

acquire_image() {
    if [ "${EASYAIOT_SKIP_IMAGE_PROMPT:-0}" = "1" ]; then
        if ! docker image inspect "$LOCAL_IMAGE" >/dev/null 2>&1; then
            print_info "本地无 transform-service 镜像，尝试拉取 aiot-transform..."
            transform_pull_prebuilt_image && export EASYAIOT_SKIP_BUILD=1 \
                || print_warning "TRANSFORM 预构建镜像拉取失败，将尝试本地构建"
        fi
        return 0
    fi

    local do_local=0
    if [ -t 0 ]; then
        print_info "镜像获取方式: 1) 拉取预构建（默认） 2) 本地构建"
        read -r -p "是否从远程仓库下载预构建镜像？(Y/n) " resp
        case "${resp:-Y}" in n|N|no|NO) do_local=1 ;; esac
    else
        print_info "非交互模式，默认拉取预构建镜像"
    fi

    if [ "$do_local" -eq 0 ]; then
        if transform_pull_prebuilt_image; then
            export EASYAIOT_SKIP_BUILD=1
        else
            print_warning "预构建镜像拉取失败，将尝试本地构建"
            do_local=1
        fi
    fi
}

install_service() {
    print_info "开始安装 TRANSFORM 服务..."
    require_full_profile
    acquire_image
    check_docker
    check_docker_compose
    ensure_env_file

    docker rm -f transform-service 2>/dev/null || true
    $COMPOSE_CMD down --remove-orphans 2>/dev/null || true
    cleanup_renamed_containers

    if transform_skip_build_from_pull; then
        :
    elif [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ] && docker image inspect "$LOCAL_IMAGE" >/dev/null 2>&1; then
        print_success "镜像已就绪 ($LOCAL_IMAGE)，跳过构建"
    else
        print_info "构建 Docker 镜像..."
        docker_build_image
    fi

    print_info "启动服务..."
    $COMPOSE_CMD up -d --remove-orphans
    sleep 3
    check_status
    print_success "TRANSFORM 安装完成 → http://localhost:48096/actuator/health"
}

start_service() {
    require_full_profile
    check_docker
    check_docker_compose
    ensure_env_file
    cleanup_renamed_containers
    if ! docker image inspect "$LOCAL_IMAGE" >/dev/null 2>&1; then
        print_warning "本地无镜像，尝试拉取或构建..."
        acquire_image
        if ! docker image inspect "$LOCAL_IMAGE" >/dev/null 2>&1; then
            docker_build_image || exit 1
        fi
    fi
    $COMPOSE_CMD up -d --remove-orphans
    print_success "服务已启动"
    check_status
}

stop_service() {
    check_docker
    check_docker_compose
    $COMPOSE_CMD down --remove-orphans 2>/dev/null || docker rm -f transform-service 2>/dev/null || true
    print_success "服务已停止"
}

restart_service() {
    require_full_profile
    check_docker
    check_docker_compose
    ensure_env_file
    $COMPOSE_CMD restart
    print_success "服务已重启"
    check_status
}

check_status() {
    check_docker
    check_docker_compose
    $COMPOSE_CMD ps 2>/dev/null || true
    if docker ps --filter "name=^/transform-service$" --format '{{.Names}}' | grep -qx transform-service; then
        docker ps --filter "name=transform-service" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
    else
        print_warning "服务未运行"
    fi
}

view_logs() {
    check_docker
    check_docker_compose
    if [ "$1" = "-f" ] || [ "$1" = "--follow" ]; then
        $COMPOSE_CMD logs -f
    else
        $COMPOSE_CMD logs --tail=100
    fi
}

build_image() {
    require_full_profile
    check_docker
    docker_build_image
    print_success "镜像构建完成: $LOCAL_IMAGE"
}

clean_service() {
    check_docker
    check_docker_compose
    if [ "${EASYAIOT_AUTO_YES:-}" != "1" ]; then
        print_warning "将删除 TRANSFORM 容器与镜像，确定继续？"
        read -r -p "确认继续? [y/n] " response
        case "$(echo "$response" | tr '[:upper:]' '[:lower:]')" in
            y|yes) ;;
            *) print_info "已取消"; return 0 ;;
        esac
    fi
    $COMPOSE_CMD down -v --remove-orphans 2>/dev/null || true
    docker rm -f transform-service 2>/dev/null || true
    docker rmi "$LOCAL_IMAGE" 2>/dev/null || true
    print_success "清理完成"
}

update_service() {
    require_full_profile
    check_docker
    check_docker_compose
    ensure_env_file
    if [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ]; then
        transform_pull_prebuilt_image || print_warning "拉取失败，尝试本地重建"
    fi
    if ! transform_skip_build_from_pull; then
        docker_build_image || return 1
    fi
    cleanup_renamed_containers
    $COMPOSE_CMD up -d --remove-orphans
    print_success "服务更新完成"
    check_status
}

show_help() {
    echo "TRANSFORM 系统对接管理脚本（仅 full 形态）"
    echo "用法: ./install_linux.sh [install|start|stop|restart|status|logs|build|clean|update]"
}

main() {
    case "${1:-help}" in
        install) install_service ;;
        start) start_service ;;
        stop) stop_service ;;
        restart) restart_service ;;
        status) check_status ;;
        logs) view_logs "$2" ;;
        build) build_image ;;
        clean) clean_service ;;
        update) update_service ;;
        help|--help|-h) show_help ;;
        *) print_error "未知命令: $1"; show_help; exit 1 ;;
    esac
}

main "$@"
