#!/bin/bash

# ============================================
# WEB服务 Docker Compose 管理脚本
# ============================================
# 使用方法：
#   ./install_all.sh [命令]
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
#   build-frontend - 构建前端项目
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
    if ! check_command docker-compose && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        echo "安装指南: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # 检查是 docker-compose 还是 docker compose
    if check_command docker-compose; then
        COMPOSE_CMD="docker-compose"
        print_success "Docker Compose 已安装: $(docker-compose --version)"
    else
        COMPOSE_CMD="docker compose"
        print_success "Docker Compose 已安装: $(docker compose version)"
    fi
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    mkdir -p conf
    mkdir -p logs
    mkdir -p conf/ssl
    mkdir -p dist
    print_success "目录创建完成"
}

# 检查前端构建产物
check_dist() {
    if [ ! -d "dist" ] || [ -z "$(ls -A dist 2>/dev/null)" ]; then
        print_warning "dist 目录不存在或为空，需要先构建前端项目"
        print_info "运行: ./install.sh build-frontend"
        return 1
    fi
    return 0
}

# 创建 .env 文件
create_env_file() {
    if [ ! -f .env ]; then
        print_info ".env 文件不存在，正在创建..."
        if [ -f env.example ]; then
            cp env.example .env
            print_success ".env 文件已从 env.example 创建"
            print_warning "请编辑 .env 文件，配置端口等参数"
        else
            print_error "env.example 文件不存在，无法创建 .env 文件"
            exit 1
        fi
    else
        print_info ".env 文件已存在"
    fi
}

# 安装 pnpm
install_pnpm() {
    print_info "正在安装 pnpm..."
    
    # 检查是否有 npm
    if ! check_command npm; then
        print_error "npm 未安装，无法安装 pnpm，请先安装 Node.js"
        exit 1
    fi
    
    # 使用 npm 全局安装 pnpm
    if npm install -g pnpm; then
        print_success "pnpm 安装成功: $(pnpm --version)"
        return 0
    else
        print_error "pnpm 安装失败"
        return 1
    fi
}

# 构建前端项目
build_frontend() {
    print_info "开始构建前端项目..."
    
    # 检查 Node.js
    if ! check_command node; then
        print_error "Node.js 未安装，请先安装 Node.js"
        echo "安装指南: https://nodejs.org/"
        exit 1
    fi
    
    # 检查 pnpm
    if ! check_command pnpm; then
        print_warning "pnpm 未安装"
        print_info "是否自动安装 pnpm？(y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            if install_pnpm; then
                PACKAGE_MANAGER="pnpm"
            else
                print_warning "pnpm 安装失败，尝试使用 npm..."
                if ! check_command npm; then
                    print_error "npm 未安装，请先安装 Node.js"
                    exit 1
                fi
                PACKAGE_MANAGER="npm"
            fi
        else
            print_info "跳过 pnpm 安装，尝试使用 npm..."
            if ! check_command npm; then
                print_error "npm 未安装，请先安装 Node.js"
                exit 1
            fi
            PACKAGE_MANAGER="npm"
        fi
    else
        PACKAGE_MANAGER="pnpm"
    fi
    
    print_info "使用包管理器: $PACKAGE_MANAGER"
    
    # 安装依赖
    if [ ! -d "node_modules" ]; then
        print_info "安装依赖..."
        $PACKAGE_MANAGER install
    fi
    
    # 构建项目
    print_info "构建前端项目..."
    if [ "$PACKAGE_MANAGER" = "pnpm" ]; then
        pnpm build
    else
        npm run build
    fi
    
    print_success "前端项目构建完成"
}

# 安装服务
install_service() {
    print_info "开始安装 WEB 服务..."
    
    check_docker
    check_docker_compose
    create_directories
    create_env_file
    
    # 检查前端构建产物
    if ! check_dist; then
        print_warning "是否现在构建前端项目？(y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            build_frontend
        else
            print_error "请先构建前端项目: ./install.sh build-frontend"
            exit 1
        fi
    fi
    
    # 确保先清理可能存在的残留容器
    print_info "检查并清理残留容器..."
    docker rm -f web-service 2>/dev/null || true
    $COMPOSE_CMD down --remove-orphans 2>/dev/null || true
    
    print_info "构建 Docker 镜像..."
    $COMPOSE_CMD build
    
    print_info "启动服务..."
    $COMPOSE_CMD up -d
    
    print_success "服务安装完成！"
    print_info "等待服务启动..."
    sleep 3
    
    # 检查服务状态
    check_status
    
    # 读取端口配置
    WEB_PORT=$(grep VITE_PORT .env 2>/dev/null | cut -d '=' -f2 | tr -d ' ' || echo "80")
    print_info "服务访问地址: http://localhost:${WEB_PORT}"
    print_info "健康检查地址: http://localhost:${WEB_PORT}/health"
    print_info "查看日志: ./install.sh logs"
}

# 启动服务
start_service() {
    print_info "启动服务..."
    check_docker
    check_docker_compose
    
    if [ ! -f .env ]; then
        print_warning ".env 文件不存在，正在创建..."
        create_env_file
    fi
    
    if ! check_dist; then
        print_error "dist 目录不存在或为空，请先构建前端项目: ./install.sh build-frontend"
        exit 1
    fi
    
    $COMPOSE_CMD up -d
    print_success "服务已启动"
    check_status
}

# 停止服务
stop_service() {
    print_info "停止服务..."
    check_docker
    check_docker_compose
    
    $COMPOSE_CMD down
    print_success "服务已停止"
}

# 重启服务
restart_service() {
    print_info "重启服务..."
    check_docker
    check_docker_compose
    
    $COMPOSE_CMD restart
    print_success "服务已重启"
    check_status
}

# 查看服务状态
check_status() {
    print_info "服务状态:"
    check_docker
    check_docker_compose
    
    $COMPOSE_CMD ps
    
    echo ""
    print_info "容器健康状态:"
    if docker ps --filter "name=web-service" --format "table {{.Names}}\t{{.Status}}" | grep -q web-service; then
        docker ps --filter "name=web-service" --format "table {{.Names}}\t{{.Status}}"
        
        # 检查健康检查
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' web-service 2>/dev/null || echo "N/A")
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
    check_docker
    check_docker_compose
    
    if ! check_dist; then
        print_warning "dist 目录不存在或为空，是否先构建前端项目？(y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            build_frontend
        fi
    fi
    
    $COMPOSE_CMD build --no-cache
    print_success "镜像构建完成"
}

# 清理服务
clean_service() {
    check_docker
    check_docker_compose
    
    print_warning "这将删除容器、镜像和数据卷，确定要继续吗？(y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_info "停止并删除容器..."
        $COMPOSE_CMD down -v --remove-orphans
        
        # 强制删除容器（即使已停止）
        print_info "强制删除残留容器..."
        docker rm -f web-service 2>/dev/null || true
        
        print_info "删除镜像..."
        docker rmi web-service:latest 2>/dev/null || true
        
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
    
    print_info "拉取最新代码..."
    git pull || print_warning "Git pull 失败，继续使用当前代码"
    
    # 重新构建前端
    print_warning "是否重新构建前端项目？(y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        build_frontend
    fi
    
    print_info "重新构建镜像..."
    $COMPOSE_CMD build
    
    print_info "重启服务..."
    $COMPOSE_CMD up -d
    
    print_success "服务更新完成"
    check_status
}

# 显示帮助信息
show_help() {
    echo "WEB服务 Docker Compose 管理脚本"
    echo ""
    echo "使用方法:"
    echo "  ./install.sh [命令]"
    echo ""
    echo "可用命令:"
    echo "  install         - 安装并启动服务（首次运行）"
    echo "  start           - 启动服务"
    echo "  stop            - 停止服务"
    echo "  restart         - 重启服务"
    echo "  status          - 查看服务状态"
    echo "  logs            - 查看服务日志"
    echo "  logs -f         - 实时查看服务日志"
    echo "  build           - 重新构建镜像"
    echo "  build-frontend  - 构建前端项目"
    echo "  clean           - 清理容器和镜像"
    echo "  update          - 更新并重启服务"
    echo "  help            - 显示此帮助信息"
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
        build-frontend)
            build_frontend
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

