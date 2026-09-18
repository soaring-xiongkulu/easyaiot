#!/bin/bash

# ============================================
# CentOS 7.9 单独部署 RustFS 容器脚本
# ============================================
# 仅启动 docker-compose.yml 中的 RustFS 服务（不启动其他中间件）
#
# 使用方法：
#   cd .scripts/docker
#   chmod +x start_rustfs_centos7.sh
#   sudo ./start_rustfs_centos7.sh
#
# 选项：
#   -h, --help          显示帮助
#   -f, --force         跳过 CentOS 7 系统检查
#   --stop              停止 RustFS 容器
#   --restart           重启 RustFS 容器
#   --status            查看容器与健康状态
#   --no-wait           启动后不等待健康检查
#   --skip-mirror       跳过配置 Docker 国内镜像源
#   --skip-pull         跳过拉取镜像
#   --no-upgrade-docker 检测到过旧 Docker 时不自动升级
#   --upgrade-docker    强制升级 Docker CE（需 root）
#   --skip-upload       跳过自动上传 RustFS 数据
#
# 默认连接信息（与 docker-compose.yml 一致）：
#   API:     http://127.0.0.1:9000
#   控制台:  http://127.0.0.1:9001
#   用户:    minioadmin
#   密码:    basiclab@iot975248395
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="docker-compose.yml"
SERVICE_MINIO="RustFS"
CONTAINER_NAME="rustfs-server"
NETWORK_NAME="easyaiot-network"
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001
MINIO_ROOT_USER="minioadmin"
MINIO_ROOT_PASSWORD="basiclab@iot975248395"
DOCKER_MIRROR="https://docker.m.daocloud.io/"

# 与 docker-compose.yml 保持一致，启动时从 compose 解析
MINIO_IMAGE="rustfs/rustfs:1.0.0"

FORCE_OS_CHECK=false
WAIT_READY=true
SKIP_MIRROR=false
SKIP_PULL=false
SKIP_DOCKER_UPGRADE=false
FORCE_DOCKER_UPGRADE=false
SKIP_UPLOAD=false
MIN_DOCKER_MAJOR=20
ACTION="start"

print_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

print_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

show_help() {
    cat <<'EOF'
CentOS 7.9 单独部署 RustFS 容器

用法:
  ./start_rustfs_centos7.sh [选项]

选项:
  -h, --help          显示此帮助
  -f, --force         跳过 CentOS 7 系统检查
  --stop              停止 RustFS 容器
  --restart           重启 RustFS 容器
  --status            查看容器状态
  --no-wait           启动后不等待健康检查
  --skip-mirror       跳过配置 Docker 国内镜像源
  --skip-pull         跳过拉取镜像
  --no-upgrade-docker 不自动升级过旧 Docker
  --upgrade-docker    强制升级 Docker CE（需 root）
  --skip-upload       跳过自动上传 RustFS 数据

示例:
  sudo ./start_rustfs_centos7.sh        # 启动后自动上传 ../minio 数据（CentOS7 用 mc）
  ./start_rustfs_centos7.sh --status
  ./upload_rustfs_data.sh --prefer-mc --non-interactive
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help) show_help; exit 0 ;;
            -f|--force) FORCE_OS_CHECK=true; shift ;;
            --stop) ACTION="stop"; shift ;;
            --restart) ACTION="restart"; shift ;;
            --status) ACTION="status"; shift ;;
            --no-wait) WAIT_READY=false; shift ;;
            --skip-mirror) SKIP_MIRROR=true; shift ;;
            --skip-pull) SKIP_PULL=true; shift ;;
            --no-upgrade-docker) SKIP_DOCKER_UPGRADE=true; shift ;;
            --upgrade-docker) FORCE_DOCKER_UPGRADE=true; shift ;;
            --skip-upload) SKIP_UPLOAD=true; shift ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

check_centos7() {
    if [ "$FORCE_OS_CHECK" = true ]; then
        print_warning "已跳过 CentOS 7 系统检查 (--force)"
        return 0
    fi

    print_section "系统环境检查"

    local os_id="" os_version=""
    if [ -f /etc/os-release ]; then
        # shellcheck source=/dev/null
        source /etc/os-release
        os_id="${ID:-}"
        os_version="${VERSION_ID:-}"
    elif [ -f /etc/redhat-release ]; then
        grep -qi "centos" /etc/redhat-release 2>/dev/null && os_id="centos"
        os_version=$(grep -oE '[0-9]+\.[0-9]+' /etc/redhat-release | head -1)
    fi

    if [ "$os_id" = "centos" ]; then
        print_success "CentOS 7.x (${os_version:-7})"
    else
        print_warning "当前系统 ID=${os_id:-未知}，脚本针对 CentOS 7 优化"
    fi

    if command -v getenforce >/dev/null 2>&1; then
        print_info "SELinux 状态: $(getenforce 2>/dev/null || echo 未知)"
    fi

    if systemctl is-active firewalld >/dev/null 2>&1; then
        print_info "firewalld 运行中，若无法访问请放行:"
        print_info "  sudo firewall-cmd --permanent --add-port=9000/tcp --add-port=9001/tcp && sudo firewall-cmd --reload"
    fi
}

resolve_compose_cmd() {
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
    else
        print_error "未找到 docker compose / docker-compose"
        print_info "CentOS 7: sudo yum install -y docker-ce docker-ce-cli containerd.io"
        exit 1
    fi
    print_info "使用 Compose 命令: $COMPOSE_CMD"
}

check_docker() {
    print_info "检查 Docker 服务..."
    if docker info >/dev/null 2>&1; then
        print_success "Docker 可用"
        return 0
    fi

    if command -v systemctl >/dev/null 2>&1; then
        if [ "$EUID" -eq 0 ]; then
            systemctl start docker || true
        elif command -v sudo >/dev/null 2>&1; then
            sudo systemctl start docker || true
        fi
    fi

    if ! docker info >/dev/null 2>&1; then
        print_error "无法连接 Docker，请执行: sudo systemctl start docker"
        exit 1
    fi
    print_success "Docker 已启动"
}

get_docker_server_version() {
    local ver
    ver=$(docker version 2>/dev/null | awk '
        /^Server:/ { in_server=1; next }
        in_server && /^Version:/ { print $2; exit }
        in_server && /^[A-Z]/ && $1 !~ /^Version:/ { in_server=0 }
    ')
    if [ -n "$ver" ]; then
        echo "$ver"
        return 0
    fi
    docker -v 2>/dev/null | sed -n 's/.*[Vv]ersion \([^, ]*\).*/\1/p' | head -1
}

is_docker_too_old() {
    local ver="${1:-$(get_docker_server_version)}"
    [ -z "$ver" ] && return 0
    local major minor
    major=$(echo "$ver" | cut -d. -f1)
    minor=$(echo "$ver" | cut -d. -f2)
    major=${major:-0}
    minor=${minor:-0}
    if [ "$major" -le 1 ] 2>/dev/null && [ "$minor" -lt 20 ] 2>/dev/null; then
        return 0
    fi
    [ "$major" -lt "$MIN_DOCKER_MAJOR" ] 2>/dev/null
}

upgrade_docker_ce_centos7() {
    print_section "升级 Docker CE（CentOS 7）"

    if [ "$EUID" -ne 0 ]; then
        print_error "升级 Docker 需要 root"
        return 1
    fi

    yum remove -y docker docker-client docker-client-latest docker-common \
        docker-latest docker-latest-logrotate docker-logrotate \
        docker-selinux docker-engine-selinux docker-engine 2>/dev/null || true

    yum install -y yum-utils device-mapper-persistent-data lvm2

    if ! yum-config-manager --add-repo https://mirrors.huaweicloud.com/docker-ce/linux/centos/docker-ce.repo 2>/dev/null; then
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    fi

    set +e
    yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    local yum_rc=$?
    set -e
    if [ "$yum_rc" -ne 0 ]; then
        yum install -y docker-ce docker-ce-cli containerd.io || return 1
    fi

    systemctl daemon-reload
    systemctl enable docker
    systemctl start docker
    sleep 2

    docker info >/dev/null 2>&1 || return 1
    print_success "Docker 已升级: $(get_docker_server_version)"
    return 0
}

ensure_modern_docker() {
    local ver
    ver=$(get_docker_server_version)
    print_info "Docker 版本: ${ver:-未知}"

    if [ "$FORCE_DOCKER_UPGRADE" = true ]; then
        [ "$EUID" -eq 0 ] || { print_error "--upgrade-docker 需要 root"; exit 1; }
        upgrade_docker_ce_centos7 || exit 1
        return 0
    fi

    if ! is_docker_too_old "$ver"; then
        print_success "Docker 版本可拉取 ${MINIO_IMAGE}"
        return 0
    fi

    print_warning "Docker ${ver} 过旧，拉取 RustFS 镜像会报 missing signature key"
    print_info "需升级到 docker-ce ${MIN_DOCKER_MAJOR}+（与 start_postgresql_centos7.sh 相同）"

    if [ "$SKIP_DOCKER_UPGRADE" = true ]; then
        print_error "已指定 --no-upgrade-docker，请执行: sudo $0 --upgrade-docker"
        exit 1
    fi

    if [ "$EUID" -ne 0 ]; then
        print_error "自动升级需要 root，请执行: sudo $0"
        exit 1
    fi

    print_info "将以 root 自动升级 Docker CE（取消请用 --no-upgrade-docker）..."
    upgrade_docker_ce_centos7 || exit 1
}

configure_docker_mirror() {
    if [ "$SKIP_MIRROR" = true ]; then
        print_info "已跳过 Docker 镜像源配置 (--skip-mirror)"
        return 0
    fi

    print_section "配置 Docker 国内镜像源"

    local docker_config_file="/etc/docker/daemon.json"
    [ "$EUID" -eq 0 ] || {
        print_warning "非 root，跳过 daemon.json 配置，将尝试国内镜像站直连拉取"
        return 0
    }

    mkdir -p /etc/docker

    if [ -f "$docker_config_file" ] && grep -q 'docker\.m\.daocloud\.io' "$docker_config_file" 2>/dev/null; then
        print_success "Docker 镜像源已配置（${DOCKER_MIRROR}）"
        return 0
    fi

    local config_updated=false
    if [ ! -f "$docker_config_file" ]; then
        cat > "$docker_config_file" <<EOF
{
  "registry-mirrors": ["${DOCKER_MIRROR}"]
}
EOF
        config_updated=true
    elif command -v python3 >/dev/null 2>&1; then
        set +e
        python3 - "$docker_config_file" "$DOCKER_MIRROR" <<'PYEOF'
import json, sys
config_file, mirror = sys.argv[1], sys.argv[2].rstrip("/") + "/"
with open(config_file, "r") as f:
    config = json.load(f)
mirrors = config.get("registry-mirrors", [])
if not isinstance(mirrors, list):
    mirrors = []
if not any(m.rstrip("/") == mirror.rstrip("/") for m in mirrors):
    mirrors.append(mirror)
    config["registry-mirrors"] = mirrors
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
PYEOF
        [ $? -eq 0 ] && config_updated=true
        set -e
    else
        print_warning "请手动在 ${docker_config_file} 添加: ${DOCKER_MIRROR}"
        return 0
    fi

    if [ "$config_updated" = true ]; then
        print_success "Docker 镜像源已更新为 ${DOCKER_MIRROR}"
        set +e
        systemctl daemon-reload
        systemctl restart docker
        set -e
        sleep 2
        docker info >/dev/null 2>&1 && print_success "Docker 服务已重启" || \
            print_warning "Docker 重启后异常，将继续尝试直连拉取"
    fi
}

resolve_minio_image_from_compose() {
    local img
    img=$($COMPOSE_CMD -f "$COMPOSE_FILE" config 2>/dev/null | awk '
        $1 == "RustFS:" { svc=1; next }
        svc && $1 == "image:" { print $2; exit }
        svc && $1 ~ /^[A-Za-z]/ && $1 != "image:" { svc=0 }
    ')
    if [ -z "$img" ]; then
        img=$(awk '
            /^  RustFS:/ { p=1; next }
            p && /image:/ { gsub(/.*image:[[:space:]]*/, ""); gsub(/["'\'']/, ""); print; exit }
        ' "$COMPOSE_FILE" 2>/dev/null)
    fi
    if [ -n "$img" ]; then
        MINIO_IMAGE="$img"
        print_info "RustFS 镜像: ${MINIO_IMAGE}"
    else
        print_warning "未能从 compose 解析镜像，使用默认: ${MINIO_IMAGE}"
    fi
}

_pull_from_registry() {
    local source_image="$1"
    print_info "从国内镜像站直连拉取: ${source_image}"
    set +e
    DOCKER_CONTENT_TRUST=0 docker pull "$source_image"
    local pull_rc=$?
    set -e
    if [ "$pull_rc" -eq 0 ]; then
        docker tag "$source_image" "$MINIO_IMAGE" 2>/dev/null || true
        print_success "已拉取并标记为 ${MINIO_IMAGE}"
        return 0
    fi
    return 1
}

ensure_minio_image() {
    if [ "$SKIP_PULL" = true ]; then
        docker image inspect "$MINIO_IMAGE" >/dev/null 2>&1 || {
            print_error "本地不存在镜像 ${MINIO_IMAGE}"
            exit 1
        }
        return 0
    fi

    print_section "拉取 RustFS 镜像 (${MINIO_IMAGE})"

    if docker image inspect "$MINIO_IMAGE" >/dev/null 2>&1; then
        print_success "镜像已存在: ${MINIO_IMAGE}"
        return 0
    fi

    if is_docker_too_old "$(get_docker_server_version)"; then
        print_error "Docker 版本过旧，请先升级: sudo $0 --upgrade-docker"
        exit 1
    fi

    export DOCKER_CONTENT_TRUST=0
    local mirrors=(
        "docker.m.daocloud.io/${MINIO_IMAGE}"
    )

    local pulled=false img
    for img in "${mirrors[@]}"; do
        if _pull_from_registry "$img"; then
            pulled=true
            break
        fi
    done

    if [ "$pulled" != true ]; then
        print_warning "国内镜像站直连失败，尝试 docker pull ${MINIO_IMAGE} ..."
        set +e
        DOCKER_CONTENT_TRUST=0 docker pull "$MINIO_IMAGE" && pulled=true
        set -e
    fi

    if [ "$pulled" = true ] && docker image inspect "$MINIO_IMAGE" >/dev/null 2>&1; then
        print_success "RustFS 镜像就绪: ${MINIO_IMAGE}"
        return 0
    fi

    print_error "无法拉取 RustFS 镜像"
    print_info "可尝试: docker pull ${MINIO_IMAGE}"
    exit 1
}

check_compose_file() {
    [ -f "$COMPOSE_FILE" ] || { print_error "未找到 ${COMPOSE_FILE}"; exit 1; }
}

ensure_network() {
    if docker network ls --format '{{.Name}}' | grep -q "^${NETWORK_NAME}$"; then
        print_success "Docker 网络 ${NETWORK_NAME} 已存在"
    else
        docker network create "$NETWORK_NAME" >/dev/null
        print_success "已创建网络 ${NETWORK_NAME}"
    fi
}

create_data_dirs() {
    local data_dir="${SCRIPT_DIR}/rustfs_data/data"
    local logs_dir="${SCRIPT_DIR}/rustfs_data/logs"

    print_info "准备数据目录 rustfs_data/{data,logs}..."
    mkdir -p "$data_dir" "$logs_dir"
    chown -R 10001:10001 "$data_dir" "$logs_dir" 2>/dev/null || \
        sudo chown -R 10001:10001 "$data_dir" "$logs_dir" 2>/dev/null || true
    print_success "RustFS 数据目录已就绪"
}

check_port_available() {
    local port="$1"
    local pid=""
    if command -v ss >/dev/null 2>&1; then
        pid=$(ss -lptn "sport = :${port}" 2>/dev/null | grep -oP 'pid=\K[0-9]+' | head -1 || true)
    elif command -v netstat >/dev/null 2>&1; then
        pid=$(netstat -tlnp 2>/dev/null | grep ":${port} " | awk '{print $7}' | cut -d'/' -f1 | head -1 || true)
    fi

    if [ -n "$pid" ] && [ "$pid" != "-" ]; then
        if docker ps --filter "name=${CONTAINER_NAME}" --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
            print_info "端口 ${port} 已由 ${CONTAINER_NAME} 使用"
            return 0
        fi
        print_warning "端口 ${port} 被进程 PID=${pid} 占用"
        return 1
    fi
    print_success "端口 ${port} 可用"
}

check_ports() {
    print_info "检查端口 ${MINIO_API_PORT} / ${MINIO_CONSOLE_PORT}..."
    check_port_available "$MINIO_API_PORT" || return 1
    check_port_available "$MINIO_CONSOLE_PORT" || return 1
}

start_minio() {
    print_section "启动 RustFS (${SERVICE_MINIO})"
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d "$SERVICE_MINIO"
    print_success "已执行: $COMPOSE_CMD up -d ${SERVICE_MINIO}"
}

wait_for_minio() {
    if [ "$WAIT_READY" = false ]; then
        return 0
    fi

    print_info "等待 RustFS 就绪（最多 90 秒）..."
    local attempt=0
    while [ "$attempt" -lt 30 ]; do
        if curl -sf "http://127.0.0.1:${MINIO_API_PORT}/health/ready" >/dev/null 2>&1; then
            print_success "RustFS 健康检查通过"
            return 0
        fi
        if docker exec "$CONTAINER_NAME" curl -sf "http://localhost:9000/health/ready" >/dev/null 2>&1; then
            print_success "RustFS 容器内健康检查通过"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 3
    done

    print_warning "健康检查超时，容器可能仍在启动"
    print_info "查看日志: docker logs ${CONTAINER_NAME}"
    return 1
}

show_connection_info() {
    print_section "RustFS 连接信息"
    echo "  容器名:   ${CONTAINER_NAME}"
    echo "  API:      http://127.0.0.1:${MINIO_API_PORT}"
    echo "  控制台:   http://127.0.0.1:${MINIO_CONSOLE_PORT}"
    echo "  用户名:   ${MINIO_ROOT_USER}"
    echo "  密码:     ${MINIO_ROOT_PASSWORD}"
    echo ""
    print_info "常用命令:"
    echo "  docker ps | grep ${CONTAINER_NAME}"
    echo "  docker logs -f ${CONTAINER_NAME}"
    echo "  curl http://127.0.0.1:${MINIO_API_PORT}/health/ready"
    echo "  ./upload_rustfs_data.sh --prefer-mc --non-interactive"
}

upload_rustfs_data_auto() {
    if [ "$SKIP_UPLOAD" = true ]; then
        print_info "已跳过 RustFS 数据上传 (--skip-upload)"
        return 0
    fi

    local upload_script="${SCRIPT_DIR}/upload_rustfs_data.sh"
    if [ ! -f "$upload_script" ]; then
        print_warning "未找到 upload_rustfs_data.sh，跳过数据上传"
        return 0
    fi

    print_section "自动上传 RustFS 数据"
    chmod +x "$upload_script" 2>/dev/null || true
    set +e
    "$upload_script" --prefer-mc --non-interactive
    local rc=$?
    set -e
    if [ "$rc" -eq 0 ]; then
        print_success "RustFS 数据上传完成"
        return 0
    fi
    print_warning "RustFS 数据上传未完全成功 (exit ${rc})，可手动: ./upload_rustfs_data.sh --prefer-mc"
    return 0
}

stop_minio() {
    print_section "停止 RustFS"
    if docker ps --filter "name=${CONTAINER_NAME}" --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        docker stop "$CONTAINER_NAME"
        print_success "容器已停止"
    else
        $COMPOSE_CMD -f "$COMPOSE_FILE" stop "$SERVICE_MINIO" 2>/dev/null || true
        print_info "容器未在运行"
    fi
}

show_status() {
    print_section "RustFS 状态"
    docker ps -a --filter "name=${CONTAINER_NAME}" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' || true
    echo ""
    if curl -sf "http://127.0.0.1:${MINIO_API_PORT}/health/ready" >/dev/null 2>&1; then
        print_success "健康检查: 正常"
    else
        print_warning "健康检查: 未就绪"
    fi
}

main() {
    parse_args "$@"

    case "$ACTION" in
        stop)
            check_docker
            resolve_compose_cmd
            stop_minio
            exit 0
            ;;
        status)
            check_docker
            show_status
            exit 0
            ;;
        restart)
            check_docker
            resolve_compose_cmd
            check_compose_file
            stop_minio
            sleep 2
            ACTION="start"
            ;;
    esac

    print_section "CentOS 7.9 RustFS 独立部署"
    check_centos7
    check_docker
    ensure_modern_docker
    configure_docker_mirror || print_warning "镜像源配置未完成，将尝试直连拉取"
    resolve_compose_cmd
    check_compose_file
    resolve_minio_image_from_compose
    ensure_minio_image
    ensure_network
    create_data_dirs
    check_ports || print_warning "端口冲突可能导致启动失败，继续尝试..."

    start_minio
    wait_for_minio || true
    upload_rustfs_data_auto
    show_connection_info
    print_success "RustFS 独立部署流程完成"
}

main "$@"
