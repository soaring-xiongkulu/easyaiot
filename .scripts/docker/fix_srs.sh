#!/bin/bash

# ============================================
# SRS 容器重启脚本
# ============================================
# 重启 docker-compose 中的 SRS 服务（容器名：srs-server），用于配置变更或异常恢复后快速拉起。
# 与 compose 约定一致：宿主机 NFS 媒体根挂载为容器内 /data（录像与 srs.log）。
# 使用方法（在 .scripts/docker 目录下）：
#   ./fix_srs.sh
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONTAINER_NAME="${SRS_CONTAINER_NAME:-srs-server}"
COMPOSE_SERVICE="${SRS_COMPOSE_SERVICE:-SRS}"
HOST_DATA_DIR="${EASYAIOT_MEDIA_ROOT:-/mnt/easyaiot-media}"

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_docker() {
    if ! docker info &>/dev/null; then
        print_error "Docker daemon 未运行或无法访问"
        exit 1
    fi
}

get_compose_cmd() {
    if command -v docker-compose &>/dev/null; then
        echo "docker-compose"
    else
        echo "docker compose"
    fi
}

# 与 compose 约定一致：NFS 媒体根挂载为容器 /data（录像 srs.log 与 playbacks）
ensure_srs_host_data_dir() {
    local mount_root="${EASYAIOT_MEDIA_ROOT:-/mnt/easyaiot-media}"
    local nfs_script="${SCRIPT_DIR}/../media-cluster/nfs/ensure_nfs_media_stack.sh"
    if [ -f "$nfs_script" ]; then
        if [ "$EUID" -eq 0 ]; then
            env EASYAIOT_MEDIA_ROOT="$mount_root" NFS_SERVER="${NFS_SERVER:-}" bash "$nfs_script"
        elif command -v sudo &>/dev/null; then
            sudo env EASYAIOT_MEDIA_ROOT="$mount_root" NFS_SERVER="${NFS_SERVER:-}" bash "$nfs_script"
        else
            env EASYAIOT_MEDIA_ROOT="$mount_root" NFS_SERVER="${NFS_SERVER:-}" bash "$nfs_script"
        fi
    else
        mkdir -p "${mount_root}/playbacks" 2>/dev/null || true
    fi
}

restart_srs() {
    check_docker
    ensure_srs_host_data_dir

    if docker inspect "$CONTAINER_NAME" &>/dev/null; then
        print_info "重启容器 ${CONTAINER_NAME} ..."
        docker restart "$CONTAINER_NAME"
        print_success "已执行 docker restart ${CONTAINER_NAME}"
    else
        print_warning "未找到容器 ${CONTAINER_NAME}，尝试通过 compose 启动服务 ${COMPOSE_SERVICE} ..."
        local compose_cmd
        compose_cmd="$(get_compose_cmd)"
        if [ ! -f "${SCRIPT_DIR}/docker-compose.yml" ]; then
            print_error "未找到 ${SCRIPT_DIR}/docker-compose.yml，无法创建 SRS 容器"
            exit 1
        fi
        (cd "$SCRIPT_DIR" && $compose_cmd -f docker-compose.yml up -d "$COMPOSE_SERVICE")
        print_success "已执行 compose up -d ${COMPOSE_SERVICE}"
    fi
}

verify_srs() {
    print_info "等待 SRS 就绪（最多约 15 秒）..."
    local i
    for i in $(seq 1 15); do
        if curl -sf --connect-timeout 2 "http://127.0.0.1:1985/api/v1/versions" >/dev/null 2>&1; then
            print_success "SRS HTTP API 已响应: http://127.0.0.1:1985/api/v1/versions"
            return 0
        fi
        sleep 1
    done
    print_warning "未能通过 HTTP 探测 SRS（请检查容器日志: docker logs ${CONTAINER_NAME}）"
}

main() {
    restart_srs
    verify_srs
}

main "$@"
