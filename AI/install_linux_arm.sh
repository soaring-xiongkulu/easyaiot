#!/bin/bash

# ============================================
# AI服务 Docker Compose 管理脚本 (ARM架构版本)
# ============================================
# 管理服务：ai-service (5000)，数据集标注已合并至 WEB + /model/dataset API
# 使用方法：
#   ./install_linux_arm.sh [命令]
#
# 可用命令：
#   install    - 安装并启动服务（首次运行）
#   start      - 启动服务
#   stop       - 停止服务
#   restart    - 重启服务
#   status     - 查看服务状态
#   logs       - 查看服务日志
#   build      - 重新构建镜像
#   clean      - 清理容器和镜像
#   update     - 更新并重启服务
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ARM架构基础镜像
ARM_BASE_IMAGE="pytorch/manylinuxaarch64-builder:cuda12.9"
DOCKER_PLATFORM="linux/arm64"
EASYAIOT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=../.scripts/docker/init-build-cache-dirs.sh
source "${EASYAIOT_ROOT}/.scripts/docker/init-build-cache-dirs.sh"
# shellcheck source=../.scripts/docker/deploy_profile.sh
source "${EASYAIOT_ROOT}/.scripts/docker/deploy_profile.sh"
# shellcheck source=../.scripts/docker/module_update_helpers.sh
source "${EASYAIOT_ROOT}/.scripts/docker/module_update_helpers.sh"
BUILD_CACHE_DIR="$(easyaiot_build_cache_base "$EASYAIOT_ROOT")"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 清理 compose recreate 被中断后遗留的「改名孤儿容器」（形如 <12位hex>_ai-service）。
# recreate 时 compose 先把旧容器改名让出 container_name，中途被打断旧容器就残留；
# 它若仍在运行会占住宿主机端口，新容器起不来。--remove-orphans 清不掉它
# （只清「服务已从 compose 文件移除」的孤儿），须在 up 前按名主动删除。
cleanup_renamed_containers() {
    local names
    names=$(docker ps -a --format '{{.Names}}' 2>/dev/null | grep -E '^[0-9a-f]{12}_ai-service$' || true)
    [ -z "$names" ] && return 0
    print_warning "清理上次中断遗留的改名孤儿容器: $(echo "$names" | tr '\n' ' ')"
    echo "$names" | xargs -r docker rm -f >/dev/null 2>&1 || true
}

init_build_cache_dirs() {
    init_easyaiot_build_cache_dirs "$EASYAIOT_ROOT"
}

prepare_cached_resources() {
    init_easyaiot_build_cache_dirs "$EASYAIOT_ROOT"
    local cache_script="${SCRIPT_DIR}/cache_resources_arm.sh"
    local wheels
    wheels="$(arm_pip_wheels_build_context_dir_for "$EASYAIOT_ROOT" ai)"

    if arm_pip_wheels_ready_for "$EASYAIOT_ROOT" ai; then
        print_success "检测到完整 pip-wheels: $wheels"
        return 0
    fi
    if [ "${AUTO_CACHE_PIP:-1}" = "1" ] && [ -f "$cache_script" ]; then
        print_warning "ARM pip-wheels 缺失或不完整，自动执行 cache_resources_arm.sh..."
        if [ -x "$cache_script" ]; then
            if "$cache_script"; then
                print_success "预缓存完成，继续安装流程"
            else
                print_warning "预缓存脚本执行失败，继续按现有本地资源/网络环境执行"
            fi
        else
            if /bin/bash "$cache_script"; then
                print_success "预缓存完成，继续安装流程"
            else
                print_warning "预缓存脚本执行失败，继续按现有本地资源/网络环境执行"
            fi
        fi
    else
        print_info "未检测到 pip-wheels，构建时将使用 pip-cache 在线安装"
        print_info "可手动执行: ./cache_resources_arm.sh"
    fi
}

optimize_dockerfile_pip_cache() {
    local dockerfile_path="$1"
    if [ ! -f "$dockerfile_path" ]; then
        return 0
    fi

    if grep -q -- "--no-cache-dir" "$dockerfile_path"; then
        print_info "优化 ${dockerfile_path} 的 pip 缓存配置（移除 --no-cache-dir）..."
        sed -i 's/ --no-cache-dir//g' "$dockerfile_path"
        print_success "${dockerfile_path} 已启用 pip 缓存复用"
    fi
}

build_with_cache() {
    local no_cache_flag="$1"
    local build_log="/tmp/docker_build_$$.log"
    local build_status=0
    local cache_opts=""
    local max_retries=3
    local attempt=1

    init_build_cache_dirs
    enable_docker_buildkit
    optimize_dockerfile_pip_cache Dockerfile.arm
    prepare_cached_resources

    cache_opts="--build-arg BASE_IMAGE=${ARM_BASE_IMAGE} --build-arg OFFLINE_MODE=${OFFLINE_MODE:-0}"
    # AlmaLinux 8 aarch64：清华源已 404，默认华为云（Dockerfile 内仍会探测并回退）
    cache_opts="$cache_opts --build-arg YUM_MIRROR_URL=${YUM_MIRROR_URL:-https://mirrors.huaweicloud.com}"
    cache_opts="$cache_opts --build-arg PIP_INDEX_URL=${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
    print_info "docker build（ARM，Dockerfile.arm，.build-cache bind mount）..."
    while [ $attempt -le $max_retries ]; do
        print_info "执行构建（第 ${attempt}/${max_retries} 次）..."
        set +e
        docker build \
            -f Dockerfile.arm \
            --build-context "pip-cache=$(pip_cache_build_context_dir_for "$EASYAIOT_ROOT" ai)" \
            --build-context "pip-wheels=$(arm_pip_wheels_build_context_dir_for "$EASYAIOT_ROOT" ai)" \
            --target runtime \
            --platform "$DOCKER_PLATFORM" \
            -t ai-service:latest \
            --pull=false \
            $cache_opts \
            $no_cache_flag \
            . 2>&1 | tee "$build_log"
        build_status=${PIPESTATUS[0]}
        set -e

        if [ $build_status -eq 0 ]; then
            break
        fi

        if grep -qiE "(failed to fetch anonymous token|dial tcp .*:443: i/o timeout|DeadlineExceeded|failed to resolve source metadata)" "$build_log" && [ $attempt -lt $max_retries ]; then
            print_warning "检测到访问 Docker Hub 超时，10 秒后自动重试..."
            sleep 10
            attempt=$((attempt + 1))
            continue
        fi

        break
    done

    if [ $build_status -ne 0 ]; then
        print_error "镜像构建失败"
        grep -iE "(error|warning|failed|失败|警告)" "$build_log" | tail -20 || true
        rm -f "$build_log"
        return 1
    fi

    rm -f "$build_log"
    return 0
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# 检查 Docker 是否安装
check_docker() {
    if ! check_command docker; then
        print_error "Docker 未安装，请先安装 Docker"
        echo "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker 已安装: $(docker --version)"
}

# 检查 Docker Compose 是否安装
check_docker_compose() {
    # 已检测过（COMPOSE_CMD 已确定）则直接复用，避免重复执行 docker compose version
    if [ -n "$COMPOSE_CMD" ]; then
        return 0
    fi
    # 先检查 docker-compose 命令
    if check_command docker-compose; then
        COMPOSE_CMD="docker-compose"
        print_success "Docker Compose 已安装: $(docker-compose --version)"
        return 0
    fi
    
    # 再检查 docker compose 插件
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        print_success "Docker Compose 已安装: $(docker compose version)"
        return 0
    fi
    
    # 如果都不存在，报错
    print_error "Docker Compose 未安装，请先安装 Docker Compose"
    echo "安装指南: https://docs.docker.com/compose/install/"
    exit 1
}

# 检测服务器架构并验证是否为ARM
detect_architecture() {
    print_info "检测服务器架构..."
    ARCH=$(uname -m)
    
    case "$ARCH" in
        aarch64|arm64)
            ARCH="aarch64"
            DOCKER_PLATFORM="linux/arm64"
            print_success "检测到 ARM 架构: $ARCH (aarch64/arm64)"
            print_info "使用 ARM 基础镜像: $ARM_BASE_IMAGE"
            ;;
        armv7l|armv6l)
            ARCH="armv7l"
            DOCKER_PLATFORM="linux/arm/v7"
            print_warning "检测到 ARM 架构: $ARCH (armv7l/armv6l)"
            print_warning "注意：armv7l/armv6l 架构可能不完全支持，建议使用 aarch64/arm64"
            print_info "使用 ARM 基础镜像: $ARM_BASE_IMAGE"
            ;;
        x86_64|amd64)
            if [ "${EASYAIOT_CROSS_BUILD:-0}" = "1" ]; then
                ARCH="aarch64"
                DOCKER_PLATFORM="linux/arm64"
                print_info "跨架构构建模式: 在 x86_64 上构建 ARM64 镜像"
                print_info "基础镜像: $ARM_BASE_IMAGE"
            else
                print_error "检测到 x86_64 架构"
                print_error "本脚本专用于 ARM 架构部署"
                print_info "如需在 x86_64 架构上部署，请使用 install_linux.sh"
                exit 1
            fi
            ;;
        *)
            print_error "未识别的架构: $ARCH"
            print_error "本脚本仅支持 ARM 架构（aarch64/arm64/armv7l/armv6l）"
            exit 1
            ;;
    esac
    
    # 导出环境变量供docker-compose使用
    export DOCKER_PLATFORM
    export ARM_BASE_IMAGE
    export BASE_IMAGE="$ARM_BASE_IMAGE"
}

# 确保 ARM 架构 Dockerfile（Dockerfile.arm）存在，不覆写 x86 Dockerfile
configure_arm_dockerfile() {
    print_info "配置 ARM 架构 Dockerfile（Dockerfile.arm）..."
    
    if [ -f Dockerfile.arm ]; then
        print_info "使用现有的 Dockerfile.arm"
    else
        print_info "创建 ARM 版本的 Dockerfile.arm..."
        # 替换第一行的 FROM 语句
        sed "1s|^FROM.*|FROM ${ARM_BASE_IMAGE} AS base|" Dockerfile > Dockerfile.arm.tmp
        
        # 检查 manylinuxaarch64-builder 镜像是否需要特殊处理
        if echo "$ARM_BASE_IMAGE" | grep -q "manylinuxaarch64-builder"; then
            print_warning "检测到构建器镜像，可能需要额外的运行时配置"
            print_info "如果构建失败，请考虑使用运行时镜像，如：pytorch/pytorch:2.9.0-cuda12.8-cudnn9-runtime"
        fi
        
        mv Dockerfile.arm.tmp Dockerfile.arm
        print_success "已创建 ARM 版本的 Dockerfile.arm"
    fi

    optimize_dockerfile_pip_cache Dockerfile.arm
}

# 配置架构相关的docker-compose设置
configure_architecture() {
    print_info "配置 Docker Compose 架构设置..."
    
    # 创建或更新 .env.arch 文件来存储架构配置
    if [ ! -f .env.arch ] || ! grep -q "DOCKER_PLATFORM=" .env.arch 2>/dev/null; then
        echo "# 架构配置（由install_linux_arm.sh自动生成）" > .env.arch
        echo "DOCKER_PLATFORM=$DOCKER_PLATFORM" >> .env.arch
        echo "BASE_IMAGE=$ARM_BASE_IMAGE" >> .env.arch
        print_success "已创建架构配置文件 .env.arch"
    else
        # 更新现有配置
        sed -i "s|^DOCKER_PLATFORM=.*|DOCKER_PLATFORM=$DOCKER_PLATFORM|" .env.arch
        sed -i "s|^BASE_IMAGE=.*|BASE_IMAGE=$ARM_BASE_IMAGE|" .env.arch
        print_info "已更新架构配置文件 .env.arch"
    fi
    
    print_success "架构配置完成: $ARCH -> $DOCKER_PLATFORM"
}

# 检查并创建 Docker 网络
check_network() {
    print_info "检查 Docker 网络 easyaiot-network..."
    
    # 检查网络是否已存在（使用网络名称而不是ID）
    if docker network ls --format "{{.Name}}" 2>/dev/null | grep -q "^easyaiot-network$"; then
        print_info "网络 easyaiot-network 已存在"
        return 0
    fi
    
    # 网络不存在，尝试创建
    print_info "网络 easyaiot-network 不存在，正在创建..."
    local create_output=$(docker network create easyaiot-network 2>&1)
    local create_exit_code=$?
    
    if [ $create_exit_code -eq 0 ]; then
        print_success "网络 easyaiot-network 已创建"
        return 0
    else
        # 检查错误原因
        if echo "$create_output" | grep -qi "already exists"; then
            print_info "网络 easyaiot-network 已存在（可能在检查后创建）"
            return 0
        elif echo "$create_output" | grep -qi "permission denied"; then
            print_error "没有权限创建 Docker 网络"
            print_info "请确保当前用户在 docker 组中，或使用 sudo 运行脚本"
            print_info "解决方案："
            echo "  1. 将当前用户添加到 docker 组："
            echo "     sudo usermod -aG docker $USER"
            echo "     然后重新登录或运行: newgrp docker"
            echo ""
            echo "  2. 或者使用 sudo 运行此脚本："
            echo "     sudo ./install_linux_arm.sh $*"
            exit 1
        elif echo "$create_output" | grep -qi "network with name.*already exists"; then
            print_warning "网络名称冲突，但网络已存在，继续使用现有网络"
            return 0
        else
            print_error "无法创建网络 easyaiot-network"
            print_error "错误信息: $create_output"
            print_info "诊断建议："
            print_info "  1. 检查 Docker 服务是否正常运行: sudo systemctl status docker"
            print_info "  2. 检查当前用户是否有权限: docker network ls"
            print_info "  3. 查看 Docker 日志: sudo journalctl -u docker.service"
            exit 1
        fi
    fi
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    mkdir -p data/uploads
    mkdir -p data/datasets
    mkdir -p data/models
    mkdir -p data/inference_results
    mkdir -p static/models
    mkdir -p temp_uploads
    mkdir -p model
    print_success "目录创建完成"
}

# 创建 .env.docker 文件（用于Docker部署）
create_env_file() {
    if [ ! -f .env.docker ]; then
        print_info ".env.docker 文件不存在，正在创建..."
        if [ -f env.example ]; then
            cp env.example .env.docker
            print_success ".env.docker 文件已从 env.example 创建"
            
            # 自动配置中间件连接信息（使用localhost，因为docker-compose.yaml使用host网络模式）
            print_info "自动配置中间件连接信息..."
            
            # 更新数据库连接
            sed -i 's|^DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:iot45722414822@localhost:5432/iot-ai20|' .env.docker
            
            # 更新Nacos配置
            sed -i 's|^NACOS_SERVER=.*|NACOS_SERVER=localhost:8848|' .env.docker
            
            # 更新MinIO配置
            sed -i 's|^MINIO_ENDPOINT=.*|MINIO_ENDPOINT=localhost:9000|' .env.docker
            sed -i 's|^MINIO_SECRET_KEY=.*|MINIO_SECRET_KEY=basiclab@iot975248395|' .env.docker
            
            # 更新Nacos密码
            sed -i 's|^NACOS_PASSWORD=.*|NACOS_PASSWORD=basiclab@iot78475418754|' .env.docker
            
            # 确保Nacos命名空间为空（使用默认命名空间）
            sed -i 's|^NACOS_NAMESPACE=.*|NACOS_NAMESPACE=|' .env.docker
            
            print_success "中间件连接信息已自动配置"
            print_info "如需修改其他配置，请编辑 .env.docker 文件"
        else
            print_error "env.example 文件不存在，无法创建 .env.docker 文件"
            exit 1
        fi
    else
        print_info ".env.docker 文件已存在"
        print_info "检查并更新中间件连接信息..."
        
        if grep -q "DATABASE_URL=.*PostgresSQL" .env.docker || grep -q "DATABASE_URL=.*postgres-server" .env.docker; then
            sed -i 's|^DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:iot45722414822@localhost:5432/iot-ai20|' .env.docker
            print_info "已更新数据库连接为 localhost:5432（host网络模式）"
        fi
        
        if grep -q "NACOS_SERVER=.*Nacos" .env.docker || grep -q "NACOS_SERVER=.*14\.18\.122\.2" .env.docker || grep -q "NACOS_SERVER=.*nacos-server" .env.docker; then
            sed -i 's|^NACOS_SERVER=.*|NACOS_SERVER=localhost:8848|' .env.docker
            print_info "已更新Nacos连接为 localhost:8848（host网络模式）"
        fi
        
        if grep -q "MINIO_ENDPOINT=.*MinIO" .env.docker || grep -q "MINIO_ENDPOINT=.*minio-server" .env.docker; then
            sed -i 's|^MINIO_ENDPOINT=.*|MINIO_ENDPOINT=localhost:9000|' .env.docker
            print_info "已更新MinIO连接为 localhost:9000（host网络模式）"
        fi
        
        if grep -q "^NACOS_NAMESPACE=.*" .env.docker && ! grep -q "^NACOS_NAMESPACE=$" .env.docker; then
            sed -i 's|^NACOS_NAMESPACE=.*|NACOS_NAMESPACE=|' .env.docker
            print_info "已更新Nacos命名空间为空（使用默认命名空间）"
        fi
    fi

    # 部署形态集成：与 x86 install_linux.sh 保持一致，确保同形态部署相同服务
    ensure_deploy_profile
    apply_python_service_deploy_env "${EASYAIOT_ROOT}"
    if is_mini_deploy_profile; then
        print_info "mini 形态：已配置本机部署（JAVA_BACKEND_URL=48099, NODE_REMOTE_DEPLOY=false）"
        migrate_mini_minio_data_to_local_storage "${EASYAIOT_ROOT}"
    else
        print_info "${EASYAIOT_DEPLOY_PROFILE:-full} 形态：已配置网关部署（JAVA_BACKEND_URL=48080, MinIO 启用）"
    fi
}

# 安装服务
install_service() {
    print_info "开始安装 AI 服务（ARM架构）..."
    
    check_docker
    check_docker_compose
    detect_architecture
    configure_architecture
    configure_arm_dockerfile
    check_network
    create_directories
    create_env_file
    prepare_cached_resources
    
    if [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ] && docker image inspect ai-service:latest >/dev/null 2>&1; then
        print_success "镜像已从远程拉取 (ai-service:latest)，跳过构建"
    else
        print_info "构建 Docker 镜像（ARM架构，优先复用离线 pip 缓存）..."
        print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $ARM_BASE_IMAGE"
        print_warning "首次构建可能需要较长时间（20-40分钟），请耐心等待..."
        echo ""
        
        if ! build_with_cache ""; then
            exit 1
        fi
        echo ""
        print_success "镜像构建完成！"
    fi
    
    print_info "启动服务..."
    cleanup_renamed_containers
    $COMPOSE_CMD up -d --remove-orphans --quiet-pull 2>&1 | grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" || true
    
    print_success "服务安装完成！"
    print_info "等待服务启动..."
    sleep 5
    
    # 检查服务状态
    check_status
    
    print_info "AI 服务访问地址: http://localhost:5000"
    print_info "AI 健康检查: http://localhost:5000/actuator/health"
    print_info "数据集标注: WEB 数据集详情 → 图像数据集标注"
    print_info "查看日志: ./install_linux_arm.sh logs"
}

# 启动服务（同步部署形态 env 后 force-recreate，使 compose env_file 注入生效）
start_service() {
    print_info "启动服务..."
    check_docker
    check_docker_compose
    detect_architecture
    configure_arm_dockerfile
    check_network
    
    if [ ! -f .env.docker ]; then
        print_warning ".env.docker 文件不存在，正在创建..."
        create_env_file
    else
        ensure_deploy_profile
    fi
    
    cleanup_renamed_containers
    $COMPOSE_CMD up -d --force-recreate --remove-orphans --quiet-pull 2>&1 | grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" || true
    print_success "服务已启动"
    check_status
}

# 停止服务
stop_service() {
    print_info "停止服务..."
    check_docker
    check_docker_compose
    
    $COMPOSE_CMD down --remove-orphans 2>&1 | grep -v "^Stopping\|^Removing\|^Network" || true
    print_success "服务已停止"
}

# 重启服务（同步部署形态 env 后 force-recreate）
restart_service() {
    print_info "重启服务..."
    check_docker
    check_docker_compose
    detect_architecture
    configure_arm_dockerfile

    ensure_deploy_profile
    cleanup_renamed_containers
    $COMPOSE_CMD up -d --force-recreate --remove-orphans --quiet-pull 2>&1 | grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" || true
    print_success "服务已重启"
    check_status
}

# 查看服务状态
check_status() {
    print_info "服务状态:"
    check_docker
    check_docker_compose
    
    $COMPOSE_CMD ps 2>/dev/null | head -20
    
    echo ""
    print_info "容器健康状态:"
    local any_running=false
    for svc in ai-service; do
        if docker ps --filter "name=^${svc}$" --format "{{.Names}}" 2>/dev/null | grep -q "^${svc}$"; then
            any_running=true
            docker ps --filter "name=^${svc}$" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null
            HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null || echo "N/A")
            if [ "$HEALTH" != "N/A" ]; then
                echo "${svc} 健康状态: $HEALTH"
            fi
        else
            print_warning "${svc} 未运行"
        fi
    done
    if [ "$any_running" = true ]; then
        print_info "AI 服务: http://localhost:5000"
    fi
}

# 查看日志
view_logs() {
    check_docker
    check_docker_compose
    
    if [ "$1" == "-f" ] || [ "$1" == "--follow" ]; then
        print_info "实时查看日志（按 Ctrl+C 退出）..."
        $COMPOSE_CMD logs -f
    else
        print_info "查看最近日志..."
        $COMPOSE_CMD logs --tail=100
    fi
}

# 构建镜像
build_image() {
    print_info "重新构建 Docker 镜像（ARM架构）..."
    check_docker
    check_docker_compose
    detect_architecture
    configure_architecture
    configure_arm_dockerfile

    if [ "${FORCE_REBUILD:-0}" != "1" ] && docker image inspect ai-service:latest >/dev/null 2>&1; then
        print_success "ai-service:latest 已存在，跳过 Docker 构建（强制重建请设置 FORCE_REBUILD=1）"
        return 0
    fi
    
    print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $ARM_BASE_IMAGE"
    print_warning "重新构建可能需要较长时间（20-40分钟），请耐心等待..."
    echo ""

    local cache_flag=""
    [ "${FORCE_REBUILD:-0}" = "1" ] && cache_flag="--no-cache"
    if ! build_with_cache "$cache_flag"; then
        exit 1
    fi
    echo ""
    print_success "镜像构建完成"
}

# 清理服务
clean_service() {
    if [ "${EASYAIOT_AUTO_YES:-}" != "1" ]; then
        print_warning "这将删除容器、镜像和数据卷，确定要继续吗？"
        local response
        while true; do
            read -r -p "确认继续? [y/n] " response
            case "$(echo "$response" | tr '[:upper:]' '[:lower:]')" in
                y|yes) break ;;
                n|no|'')
                    print_info "已取消清理操作"
                    return
                    ;;
                *) echo "请输入 y/yes 或 n/no" ;;
            esac
        done
    fi

    check_docker
    check_docker_compose
    print_info "停止并删除容器..."
    $COMPOSE_CMD down -v --remove-orphans 2>&1 | grep -v "^Stopping\|^Removing\|^Network" || true
    
    print_info "删除镜像..."
    docker rmi ai-service:latest >/dev/null 2>&1 || true
    
    print_success "清理完成"
}

# 更新服务
# 性能优化（与 x86 install_linux.sh 保持一致）：
#   1. 业务源码经 docker-compose 卷挂载（./:/app）进容器。「仅改业务代码、依赖不变」时，
#      update 完全跳过 docker build：git pull 后只重启容器进程即可加载新代码（秒级）。
#   2. 仅当以下任一成立时才重建镜像：镜像不存在 / FORCE_REBUILD=1 /
#      本次 git pull 改动了依赖或构建输入（requirements*.txt、Dockerfile、docker-entrypoint.sh）。
#   3. 需要构建时复用 BuildKit 层缓存 + 离线 pip 缓存（build_with_cache 已内置 prepare）。
update_service() {
    print_info "更新服务..."
    check_docker
    check_docker_compose
    detect_architecture
    configure_architecture
    configure_arm_dockerfile
    check_network

    # 拉取预构建 / 无 git：禁止 git pull，仅 recreate
    if easyaiot_update_should_recreate_only ai-service:latest; then
        cleanup_renamed_containers
        $COMPOSE_CMD up -d --remove-orphans --no-deps --quiet-pull ai-service 2>&1 | grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" || true
        print_success "服务更新完成"
        check_status
        return 0
    fi

    # 记录更新前代码版本，用于判断依赖/构建文件是否变化
    local rev_before=""
    rev_before="$(easyaiot_git_rev_parse_head)"

    print_info "拉取最新代码..."
    # --ff-only：快进失败立即返回；无 git 时跳过 pull，基于当前目录构建
    easyaiot_git_pull_ff_only

    local rev_after=""
    rev_after="$(easyaiot_git_rev_parse_head)"

    # ---- 判断是否需要重建镜像 ----
    local needs_build=0
    if ! docker image inspect ai-service:latest >/dev/null 2>&1; then
        needs_build=1
        print_info "镜像不存在，需要构建"
    elif [ "${FORCE_REBUILD:-0}" = "1" ]; then
        needs_build=1
        print_info "FORCE_REBUILD=1，强制重建镜像"
    elif [ -z "$rev_before" ]; then
        needs_build=1
        print_warning "无法获取 git 版本信息，保守起见重建镜像"
    elif [ "$rev_before" != "$rev_after" ]; then
        local dep_changes dep_diff_rc=0
        dep_changes="$(git diff --name-only "$rev_before" "$rev_after" -- \
            requirements.txt requirements-base.txt requirements-docker.txt \
            Dockerfile Dockerfile.arm docker-entrypoint.sh 2>/dev/null)" || dep_diff_rc=$?
        if [ "$dep_diff_rc" -ne 0 ]; then
            needs_build=1
            print_warning "无法比较依赖变化（git diff 失败），保守起见重建镜像"
        elif [ -n "$dep_changes" ]; then
            needs_build=1
            print_info "检测到依赖/构建文件变化，需要重建镜像："
            echo "$dep_changes" | sed 's/^/    /'
        fi
    fi

    if [ "$needs_build" = "1" ]; then
        prepare_cached_resources
        print_info "重新构建镜像（复用 BuildKit 层缓存 + 离线 pip 缓存）..."
        print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $ARM_BASE_IMAGE"
        print_warning "构建可能需要较长时间（20-40分钟），请耐心等待..."
        echo ""
        if ! build_with_cache ""; then
            exit 1
        fi
        echo ""
        print_success "镜像构建完成！"
        print_info "应用新镜像（仅重建变更服务，最小化停机）..."
        cleanup_renamed_containers
        $COMPOSE_CMD up -d --remove-orphans --no-deps --quiet-pull ai-service 2>&1 | grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" || true
    else
        print_success "依赖未变，跳过镜像构建（业务代码经卷挂载，重启进程即可生效）"
        cleanup_renamed_containers
        $COMPOSE_CMD up -d --remove-orphans --no-deps --quiet-pull ai-service 2>&1 | grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" || true

        local code_changed=0
        if [ -n "$rev_before" ] && [ "$rev_before" != "$rev_after" ]; then
            code_changed=1
        elif ! easyaiot_git_worktree_clean; then
            code_changed=1
        fi

        if [ "$code_changed" = "1" ]; then
            print_info "重启容器进程以加载最新源码（秒级）..."
            $COMPOSE_CMD restart ai-service 2>&1 | grep -v "^Restarting" || true
        else
            print_info "代码无变更，无需重启"
        fi
    fi

    print_success "服务更新完成"
    check_status
}

# 显示帮助信息
show_help() {
    echo "AI服务 Docker Compose 管理脚本 (ARM架构版本)"
    echo ""
    echo "管理服务:"
    echo "  - ai-service (端口 5000，含 /model/dataset 自动标注 API)"
    echo ""
    echo "使用方法:"
    echo "  ./install_linux_arm.sh [命令]"
    echo ""
    echo "可用命令:"
    echo "  install    - 安装并启动服务（首次运行）"
    echo "  start      - 启动服务"
    echo "  stop       - 停止服务"
    echo "  restart    - 重启服务"
    echo "  status     - 查看服务状态"
    echo "  logs       - 查看服务日志"
    echo "  logs -f    - 实时查看服务日志"
    echo "  build      - 重新构建镜像"
    echo "  clean      - 清理容器和镜像"
    echo "  update     - 更新并重启服务"
    echo "  help       - 显示此帮助信息"
    echo ""
    echo "注意："
    echo "  - 本脚本专用于 ARM 架构（aarch64/arm64）"
    echo "  - 使用基础镜像: $ARM_BASE_IMAGE"
    echo "  - 支持与 x86 版本相同的部署形态: mini(1) / standard(2) / full(3)"
    echo "    通过环境变量 EASYAIOT_DEPLOY_PROFILE 控制"
    echo "  - 如需在 x86_64 架构上部署，请使用 install_linux.sh"
    echo ""
}

# 主函数
main() {
    case "${1:-help}" in
        install)
            install_service
            ;;
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            check_status
            ;;
        logs)
            view_logs "$2"
            ;;
        build)
            build_image
            ;;
        clean)
            clean_service
            ;;
        update)
            update_service
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
