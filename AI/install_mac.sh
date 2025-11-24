#!/bin/bash

# ============================================
# AI服务 Docker Compose 管理脚本 (macOS 版本)
# ============================================
# 使用方法：
#   ./install_mac.sh [命令]
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

# 检查是否为 macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "此脚本仅支持 macOS 系统"
        exit 1
    fi
    print_success "检测到 macOS 系统: $(sw_vers -productVersion)"
}

# 检查 Docker 是否安装
check_docker() {
    if ! check_command docker; then
        print_error "Docker 未安装，请先安装 Docker Desktop"
        echo "安装指南: https://www.docker.com/products/docker-desktop"
        echo ""
        echo "安装步骤："
        echo "  1. 访问 https://www.docker.com/products/docker-desktop"
        echo "  2. 下载并安装 Docker Desktop for Mac"
        echo "  3. 启动 Docker Desktop 应用程序"
        echo "  4. 等待 Docker Desktop 完全启动后再运行此脚本"
        exit 1
    fi
    
    # 检查 Docker daemon 是否运行
    if ! docker info &> /dev/null; then
        print_error "Docker daemon 未运行"
        echo ""
        echo "解决方案："
        echo "  1. 打开 Docker Desktop 应用程序"
        echo "  2. 等待 Docker Desktop 完全启动（状态栏图标显示为运行中）"
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
    echo "Docker Desktop for Mac 已包含 Docker Compose，请确保 Docker Desktop 已正确安装"
    echo "安装指南: https://docs.docker.com/compose/install/"
    exit 1
}

# 架构检测（macOS 版本，支持 Apple Silicon）
ARCH=""
DOCKER_PLATFORM=""
BASE_IMAGE=""

# 检测服务器架构并验证是否支持
detect_architecture() {
    print_info "检测服务器架构..."
    ARCH=$(uname -m)
    
    case "$ARCH" in
        x86_64|amd64)
            ARCH="x86_64"
            DOCKER_PLATFORM="linux/amd64"
            # macOS 不支持 NVIDIA GPU，使用 CPU 版本的 PyTorch
            BASE_IMAGE="pytorch/pytorch:2.1.0-cpu"
            print_success "检测到架构: $ARCH (x86_64)"
            print_info "使用 PyTorch CPU 镜像: $BASE_IMAGE"
            print_warning "注意：macOS 不支持 NVIDIA GPU，将使用 CPU 模式运行"
            ;;
        arm64|aarch64)
            ARCH="arm64"
            DOCKER_PLATFORM="linux/arm64"
            # Apple Silicon 使用 ARM64 版本的 PyTorch
            BASE_IMAGE="pytorch/pytorch:2.1.0-cpu"
            print_success "检测到架构: $ARCH (Apple Silicon)"
            print_info "使用 PyTorch CPU 镜像: $BASE_IMAGE"
            print_warning "注意：macOS 不支持 NVIDIA GPU，将使用 CPU 模式运行"
            ;;
        *)
            print_error "未识别的架构: $ARCH"
            print_error "本服务仅支持 x86_64 和 arm64 架构"
            exit 1
            ;;
    esac
    
    # 导出环境变量供docker-compose使用
    export DOCKER_PLATFORM
    export BASE_IMAGE
}

# 配置架构相关的docker-compose设置
configure_architecture() {
    print_info "配置 Docker Compose 架构设置..."
    
    # 创建或更新 .env.arch 文件来存储架构配置
    if [ ! -f .env.arch ] || ! grep -q "DOCKER_PLATFORM=" .env.arch 2>/dev/null; then
        echo "# 架构配置（由install_mac.sh自动生成）" > .env.arch
        echo "DOCKER_PLATFORM=$DOCKER_PLATFORM" >> .env.arch
        echo "BASE_IMAGE=$BASE_IMAGE" >> .env.arch
        print_success "已创建架构配置文件 .env.arch"
    else
        # 更新现有配置（macOS 使用 BSD sed，需要 -i ''）
        sed -i '' "s|^DOCKER_PLATFORM=.*|DOCKER_PLATFORM=$DOCKER_PLATFORM|" .env.arch
        sed -i '' "s|^BASE_IMAGE=.*|BASE_IMAGE=$BASE_IMAGE|" .env.arch
        print_info "已更新架构配置文件 .env.arch"
    fi
    
    print_success "架构配置完成: $ARCH -> $DOCKER_PLATFORM"
}

# 检查并创建 Docker 网络
check_network() {
    print_info "检查 Docker 网络 easyaiot-network..."
    if ! docker network ls --quiet 2>/dev/null | grep -q "^easyaiot-network$"; then
        print_info "网络 easyaiot-network 不存在，正在创建..."
        if docker network create easyaiot-network >/dev/null 2>&1; then
            print_success "网络 easyaiot-network 已创建"
        else
            print_error "无法创建网络 easyaiot-network"
            exit 1
        fi
    else
        print_info "网络 easyaiot-network 已存在"
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
            
            # 自动配置中间件连接信息（使用Docker服务名称）
            print_info "自动配置中间件连接信息..."
            
            # 更新数据库连接（使用中间件服务名称，注意：服务名是PostgresSQL）
            sed -i '' 's|^DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:iot45722414822@PostgresSQL:5432/iot-ai20|' .env.docker
            
            # 更新Nacos配置（使用中间件服务名称，注意：服务名是Nacos）
            sed -i '' 's|^NACOS_SERVER=.*|NACOS_SERVER=Nacos:8848|' .env.docker
            
            # 更新MinIO配置（使用中间件服务名称，注意：服务名是MinIO）
            sed -i '' 's|^MINIO_ENDPOINT=.*|MINIO_ENDPOINT=MinIO:9000|' .env.docker
            sed -i '' 's|^MINIO_SECRET_KEY=.*|MINIO_SECRET_KEY=basiclab@iot975248395|' .env.docker
            
            # 更新Nacos密码
            sed -i '' 's|^NACOS_PASSWORD=.*|NACOS_PASSWORD=basiclab@iot78475418754|' .env.docker
            
            # 确保Nacos命名空间为空（使用默认命名空间）
            sed -i '' 's|^NACOS_NAMESPACE=.*|NACOS_NAMESPACE=|' .env.docker
            
            print_success "中间件连接信息已自动配置"
            print_info "如需修改其他配置，请编辑 .env.docker 文件"
        else
            print_error "env.example 文件不存在，无法创建 .env.docker 文件"
            exit 1
        fi
    else
        print_info ".env.docker 文件已存在"
        print_info "检查并更新中间件连接信息..."
        
        # 检查并更新数据库连接（如果还是localhost或旧的服务名）
        if grep -q "DATABASE_URL=.*localhost" .env.docker || grep -q "DATABASE_URL=.*postgres-server" .env.docker; then
            sed -i '' 's|^DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:iot45722414822@PostgresSQL:5432/iot-ai20|' .env.docker
            print_info "已更新数据库连接为 PostgresSQL:5432"
        fi
        
        # 检查并更新Nacos配置（如果还是IP地址或旧的服务名）
        if grep -q "NACOS_SERVER=.*14\.18\.122\.2" .env.docker || grep -q "NACOS_SERVER=.*localhost" .env.docker || grep -q "NACOS_SERVER=.*nacos-server" .env.docker; then
            sed -i '' 's|^NACOS_SERVER=.*|NACOS_SERVER=Nacos:8848|' .env.docker
            print_info "已更新Nacos连接为 Nacos:8848"
        fi
        
        # 检查并更新MinIO配置（如果还是localhost或旧的服务名）
        if grep -q "MINIO_ENDPOINT=.*localhost" .env.docker || grep -q "MINIO_ENDPOINT=.*minio-server" .env.docker; then
            sed -i '' 's|^MINIO_ENDPOINT=.*|MINIO_ENDPOINT=MinIO:9000|' .env.docker
            print_info "已更新MinIO连接为 MinIO:9000"
        fi
        
        # 检查并更新Nacos命名空间（如果设置为local或其他非空值，则重置为空，使用默认命名空间）
        if grep -q "^NACOS_NAMESPACE=.*" .env.docker && ! grep -q "^NACOS_NAMESPACE=$" .env.docker; then
            sed -i '' 's|^NACOS_NAMESPACE=.*|NACOS_NAMESPACE=|' .env.docker
            print_info "已更新Nacos命名空间为空（使用默认命名空间）"
        fi
    fi
}

# 安装服务
install_service() {
    print_info "开始安装 AI 服务..."
    
    check_macos
    check_docker
    check_docker_compose
    detect_architecture
    configure_architecture
    check_network
    create_directories
    create_env_file
    
    print_info "构建 Docker 镜像..."
    print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $BASE_IMAGE"
    # 使用环境变量传递架构配置给docker-compose
    BUILD_OUTPUT=$(BASE_IMAGE=$BASE_IMAGE $COMPOSE_CMD build 2>&1)
    BUILD_STATUS=$?
    # 只显示错误和警告信息
    echo "$BUILD_OUTPUT" | grep -iE "(error|warning|failed|失败|警告)" || true
    if [ $BUILD_STATUS -ne 0 ]; then
        print_error "镜像构建失败"
        exit 1
    fi
    
    print_info "启动服务..."
    $COMPOSE_CMD up -d --quiet-pull 2>&1 | grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" || true
    
    print_success "服务安装完成！"
    print_info "等待服务启动..."
    sleep 5
    
    # 检查服务状态
    check_status
    
    print_info "服务访问地址: http://localhost:5000"
    print_info "健康检查地址: http://localhost:5000/actuator/health"
    print_info "查看日志: ./install_mac.sh logs"
}

# 启动服务
start_service() {
    print_info "启动服务..."
    check_macos
    check_docker
    check_docker_compose
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
    print_info "重新构建 Docker 镜像..."
    check_macos
    check_docker
    check_docker_compose
    detect_architecture
    configure_architecture
    
    print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $BASE_IMAGE"
    # 使用环境变量传递架构配置给docker-compose
    BUILD_OUTPUT=$(BASE_IMAGE=$BASE_IMAGE $COMPOSE_CMD build --no-cache 2>&1)
    BUILD_STATUS=$?
    # 只显示错误和警告信息
    echo "$BUILD_OUTPUT" | grep -iE "(error|warning|failed|失败|警告)" || true
    if [ $BUILD_STATUS -ne 0 ]; then
        print_error "镜像构建失败"
        exit 1
    fi
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
        
        print_success "清理完成"
    else
        print_info "已取消清理操作"
    fi
}

# 更新服务
update_service() {
    print_info "更新服务..."
    check_macos
    check_docker
    check_docker_compose
    detect_architecture
    configure_architecture
    check_network
    
    print_info "拉取最新代码..."
    git pull || print_warning "Git pull 失败，继续使用当前代码"
    
    print_info "重新构建镜像..."
    print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $BASE_IMAGE"
    # 使用环境变量传递架构配置给docker-compose
    BUILD_OUTPUT=$(BASE_IMAGE=$BASE_IMAGE $COMPOSE_CMD build 2>&1)
    BUILD_STATUS=$?
    # 只显示错误和警告信息
    echo "$BUILD_OUTPUT" | grep -iE "(error|warning|failed|失败|警告)" || true
    if [ $BUILD_STATUS -ne 0 ]; then
        print_error "镜像构建失败"
        exit 1
    fi
    
    print_info "重启服务..."
    $COMPOSE_CMD up -d --quiet-pull 2>&1 | grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" || true
    
    print_success "服务更新完成"
    check_status
}

# 显示帮助信息
show_help() {
    echo "AI服务 Docker Compose 管理脚本 (macOS 版本)"
    echo ""
    echo "使用方法:"
    echo "  ./install_mac.sh [命令]"
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
    echo "  - 此脚本需要 Docker Desktop for Mac"
    echo "  - macOS 不支持 NVIDIA GPU，将使用 CPU 模式运行"
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

