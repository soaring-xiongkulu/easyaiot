#!/bin/bash

# ============================================
# AI服务 Docker Compose 管理脚本 (ARM架构版本)
# ============================================
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
            print_error "检测到 x86_64 架构"
            print_error "本脚本专用于 ARM 架构部署"
            print_info "如需在 x86_64 架构上部署，请使用 install_linux.sh"
            exit 1
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

# 配置ARM架构的Dockerfile
configure_arm_dockerfile() {
    print_info "配置 ARM 架构 Dockerfile..."
    
    # 备份原始 Dockerfile
    if [ ! -f Dockerfile.orig ]; then
        cp Dockerfile Dockerfile.orig
        print_info "已备份原始 Dockerfile 为 Dockerfile.orig"
    fi
    
    # 创建 ARM 版本的 Dockerfile
    if [ -f Dockerfile.arm ]; then
        print_info "使用现有的 Dockerfile.arm"
        cp Dockerfile.arm Dockerfile
    else
        print_info "创建 ARM 版本的 Dockerfile..."
        # 替换第一行的 FROM 语句
        sed "1s|^FROM.*|FROM ${ARM_BASE_IMAGE} AS base|" Dockerfile.orig > Dockerfile.arm.tmp
        
        # 检查 manylinuxaarch64-builder 镜像是否需要特殊处理
        # 如果是构建器镜像，可能需要额外的运行时镜像
        if echo "$ARM_BASE_IMAGE" | grep -q "manylinuxaarch64-builder"; then
            print_warning "检测到构建器镜像，可能需要额外的运行时配置"
            print_info "如果构建失败，请考虑使用运行时镜像，如：pytorch/pytorch:2.9.0-cuda12.8-cudnn9-runtime"
        fi
        
        mv Dockerfile.arm.tmp Dockerfile.arm
        cp Dockerfile.arm Dockerfile
        print_success "已创建 ARM 版本的 Dockerfile"
    fi
}

# 恢复原始 Dockerfile（可选）
restore_dockerfile() {
    if [ -f Dockerfile.orig ]; then
        print_info "恢复原始 Dockerfile..."
        cp Dockerfile.orig Dockerfile
        print_success "已恢复原始 Dockerfile"
    fi
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
            
            # 更新数据库连接（使用localhost，因为使用host网络模式，中间件端口已映射到宿主机）
            sed -i 's|^DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:iot45722414822@localhost:5432/iot-ai20|' .env.docker
            
            # 更新Nacos配置（使用localhost，因为使用host网络模式）
            sed -i 's|^NACOS_SERVER=.*|NACOS_SERVER=localhost:8848|' .env.docker
            
            # 更新MinIO配置（使用localhost，因为使用host网络模式）
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
        
        # 检查并更新数据库连接（如果使用Docker服务名，改为localhost，因为使用host网络模式）
        if grep -q "DATABASE_URL=.*PostgresSQL" .env.docker || grep -q "DATABASE_URL=.*postgres-server" .env.docker; then
            sed -i 's|^DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:iot45722414822@localhost:5432/iot-ai20|' .env.docker
            print_info "已更新数据库连接为 localhost:5432（host网络模式）"
        fi
        
        # 检查并更新Nacos配置（如果使用Docker服务名或IP地址，改为localhost，因为使用host网络模式）
        if grep -q "NACOS_SERVER=.*Nacos" .env.docker || grep -q "NACOS_SERVER=.*14\.18\.122\.2" .env.docker || grep -q "NACOS_SERVER=.*nacos-server" .env.docker; then
            sed -i 's|^NACOS_SERVER=.*|NACOS_SERVER=localhost:8848|' .env.docker
            print_info "已更新Nacos连接为 localhost:8848（host网络模式）"
        fi
        
        # 检查并更新MinIO配置（如果使用Docker服务名，改为localhost，因为使用host网络模式）
        if grep -q "MINIO_ENDPOINT=.*MinIO" .env.docker || grep -q "MINIO_ENDPOINT=.*minio-server" .env.docker; then
            sed -i 's|^MINIO_ENDPOINT=.*|MINIO_ENDPOINT=localhost:9000|' .env.docker
            print_info "已更新MinIO连接为 localhost:9000（host网络模式）"
        fi
        
        # 检查并更新Nacos命名空间（如果设置为local或其他非空值，则重置为空，使用默认命名空间）
        if grep -q "^NACOS_NAMESPACE=.*" .env.docker && ! grep -q "^NACOS_NAMESPACE=$" .env.docker; then
            sed -i 's|^NACOS_NAMESPACE=.*|NACOS_NAMESPACE=|' .env.docker
            print_info "已更新Nacos命名空间为空（使用默认命名空间）"
        fi
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
    
    print_info "构建 Docker 镜像（ARM架构）..."
    print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $ARM_BASE_IMAGE"
    print_warning "首次构建可能需要较长时间（20-40分钟），请耐心等待..."
    print_info "正在下载基础镜像和安装依赖..."
    print_info "构建进度将实时显示，请勿中断..."
    echo ""
    
    # 使用环境变量传递架构配置给docker-compose
    # 使用 --platform 参数指定 ARM 平台
    BUILD_LOG="/tmp/docker_build_$$.log"
    set +e  # 暂时关闭错误退出，以便捕获构建状态
    BASE_IMAGE=$ARM_BASE_IMAGE DOCKER_BUILDKIT=1 $COMPOSE_CMD build --platform "$DOCKER_PLATFORM" 2>&1 | tee "$BUILD_LOG"
    BUILD_STATUS=${PIPESTATUS[0]}
    set -e  # 重新开启错误退出
    
    if [ $BUILD_STATUS -ne 0 ]; then
        print_error "镜像构建失败"
        print_info "查看详细错误信息:"
        grep -iE "(error|warning|failed|失败|警告)" "$BUILD_LOG" | tail -20 || true
        rm -f "$BUILD_LOG"
        exit 1
    fi
    
    rm -f "$BUILD_LOG"
    echo ""
    print_success "镜像构建完成！"
    
    print_info "启动服务..."
    $COMPOSE_CMD up -d --quiet-pull 2>&1 | grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" || true
    
    print_success "服务安装完成！"
    print_info "等待服务启动..."
    sleep 5
    
    # 检查服务状态
    check_status
    
    print_info "服务访问地址: http://localhost:5000"
    print_info "健康检查地址: http://localhost:5000/actuator/health"
    print_info "查看日志: ./install_linux_arm.sh logs"
}

# 启动服务
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
    fi
    
    $COMPOSE_CMD up -d --quiet-pull 2>&1 | grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" || true
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

# 重启服务
restart_service() {
    print_info "重启服务..."
    check_docker
    check_docker_compose
    detect_architecture
    configure_arm_dockerfile
    
    $COMPOSE_CMD restart 2>&1 | grep -v "^Restarting" || true
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
    if docker ps --filter "name=ai-service" --format "{{.Names}}" 2>/dev/null | grep -q ai-service; then
        docker ps --filter "name=ai-service" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null
        
        # 检查健康检查
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' ai-service 2>/dev/null || echo "N/A")
        if [ "$HEALTH" != "N/A" ]; then
            echo "健康状态: $HEALTH"
        fi
    else
        print_warning "服务未运行"
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
    
    print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $ARM_BASE_IMAGE"
    print_warning "重新构建可能需要较长时间（20-40分钟），请耐心等待..."
    print_info "正在重新下载基础镜像和安装依赖..."
    print_info "构建进度将实时显示，请勿中断..."
    echo ""
    
    # 使用环境变量传递架构配置给docker-compose
    BUILD_LOG="/tmp/docker_build_$$.log"
    set +e  # 暂时关闭错误退出，以便捕获构建状态
    BASE_IMAGE=$ARM_BASE_IMAGE DOCKER_BUILDKIT=1 $COMPOSE_CMD build --no-cache --platform "$DOCKER_PLATFORM" 2>&1 | tee "$BUILD_LOG"
    BUILD_STATUS=${PIPESTATUS[0]}
    set -e  # 重新开启错误退出
    
    if [ $BUILD_STATUS -ne 0 ]; then
        print_error "镜像构建失败"
        print_info "查看详细错误信息:"
        grep -iE "(error|warning|failed|失败|警告)" "$BUILD_LOG" | tail -20 || true
        rm -f "$BUILD_LOG"
        exit 1
    fi
    
    rm -f "$BUILD_LOG"
    echo ""
    print_success "镜像构建完成"
}

# 清理服务
clean_service() {
    print_warning "这将删除容器、镜像和数据卷，确定要继续吗？(y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        check_docker
        check_docker_compose
        print_info "停止并删除容器..."
        $COMPOSE_CMD down -v --remove-orphans 2>&1 | grep -v "^Stopping\|^Removing\|^Network" || true
        
        print_info "删除镜像..."
        docker rmi ai-service:latest >/dev/null 2>&1 || true
        
        # 可选：恢复原始 Dockerfile
        # restore_dockerfile
        
        print_success "清理完成"
    else
        print_info "已取消清理操作"
    fi
}

# 更新服务
update_service() {
    print_info "更新服务..."
    check_docker
    check_docker_compose
    detect_architecture
    configure_architecture
    configure_arm_dockerfile
    check_network
    
    print_info "拉取最新代码..."
    git pull || print_warning "Git pull 失败，继续使用当前代码"
    
    print_info "重新构建镜像..."
    print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $ARM_BASE_IMAGE"
    print_warning "构建可能需要较长时间（20-40分钟），请耐心等待..."
    print_info "正在构建镜像..."
    print_info "构建进度将实时显示，请勿中断..."
    echo ""
    
    # 使用环境变量传递架构配置给docker-compose
    BUILD_LOG="/tmp/docker_build_$$.log"
    set +e  # 暂时关闭错误退出，以便捕获构建状态
    BASE_IMAGE=$ARM_BASE_IMAGE DOCKER_BUILDKIT=1 $COMPOSE_CMD build --platform "$DOCKER_PLATFORM" 2>&1 | tee "$BUILD_LOG"
    BUILD_STATUS=${PIPESTATUS[0]}
    set -e  # 重新开启错误退出
    
    if [ $BUILD_STATUS -ne 0 ]; then
        print_error "镜像构建失败"
        print_info "查看详细错误信息:"
        grep -iE "(error|warning|failed|失败|警告)" "$BUILD_LOG" | tail -20 || true
        rm -f "$BUILD_LOG"
        exit 1
    fi
    
    rm -f "$BUILD_LOG"
    echo ""
    print_success "镜像构建完成！"
    
    print_info "重启服务..."
    $COMPOSE_CMD up -d --quiet-pull 2>&1 | grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" || true
    
    print_success "服务更新完成"
    check_status
}

# 显示帮助信息
show_help() {
    echo "AI服务 Docker Compose 管理脚本 (ARM架构版本)"
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

