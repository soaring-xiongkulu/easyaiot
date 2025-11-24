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

# 获取占用端口的进程PID
get_port_pids() {
    local port=$1
    local pids=()
    
    if command -v lsof &> /dev/null; then
        # 使用lsof获取PID，排除标题行，提取唯一的PID
        while IFS= read -r line; do
            pid=$(echo "$line" | awk '{print $2}')
            # 跳过非数字的PID（如标题行）
            if [[ "$pid" =~ ^[0-9]+$ ]]; then
                pids+=("$pid")
            fi
        done < <(lsof -i :"$port" 2>/dev/null | tail -n +2)
    elif command -v fuser &> /dev/null; then
        # 使用fuser获取PID
        pids=($(fuser "$port/tcp" 2>/dev/null | tr -d ' '))
    fi
    
    # 去重
    if [ ${#pids[@]} -gt 0 ]; then
        printf '%s\n' "${pids[@]}" | sort -u
    fi
}

# 处理端口占用
handle_port_conflict() {
    local port=$1
    local pids=()
    
    print_warning "端口 $port 已被占用"
    print_info "占用端口的进程信息:"
    
    # 显示进程信息并收集PID
    if command -v lsof &> /dev/null; then
        lsof -i :"$port" | head -10
        while IFS= read -r pid; do
            if [[ "$pid" =~ ^[0-9]+$ ]]; then
                pids+=("$pid")
            fi
        done < <(lsof -i :"$port" 2>/dev/null | tail -n +2 | awk '{print $2}' | sort -u)
    elif command -v netstat &> /dev/null; then
        netstat -tulnp 2>/dev/null | grep ":$port " | head -5
        # netstat需要root权限才能显示PID，尝试提取
        while IFS= read -r line; do
            pid=$(echo "$line" | awk '{print $7}' | cut -d'/' -f1)
            if [[ "$pid" =~ ^[0-9]+$ ]]; then
                pids+=("$pid")
            fi
        done < <(netstat -tulnp 2>/dev/null | grep ":$port ")
    elif command -v ss &> /dev/null; then
        ss -tulnp 2>/dev/null | grep ":$port " | head -5
        # ss需要root权限才能显示PID
        while IFS= read -r line; do
            pid=$(echo "$line" | grep -oP 'pid=\K[0-9]+' || echo "")
            if [[ "$pid" =~ ^[0-9]+$ ]]; then
                pids+=("$pid")
            fi
        done < <(ss -tulnp 2>/dev/null | grep ":$port ")
    fi
    
    # 去重PID数组
    if [ ${#pids[@]} -gt 0 ]; then
        local unique_pids=($(printf '%s\n' "${pids[@]}" | sort -u))
        pids=("${unique_pids[@]}")
    fi
    
    # 如果没有获取到PID，提示用户手动处理
    if [ ${#pids[@]} -eq 0 ]; then
        print_warning "无法自动获取占用端口的进程PID（可能需要root权限）"
        print_info "请手动停止占用端口的进程，或修改 .env 文件中的 WEB_PORT 配置"
        return 1
    fi
    
    echo ""
    print_info "检测到以下进程占用端口: ${pids[*]}"
    echo ""
    print_info "请选择处理方式:"
    echo "  1) 自动 - 自动kill占用端口的进程"
    echo "  2) 手动 - 手动处理（脚本退出）"
    echo "  3) 停止 - 停止脚本执行"
    echo ""
    print_info "请输入选项 (1/2/3，默认: 2): "
    read -r choice
    
    case "${choice:-2}" in
        1)
            print_info "正在kill占用端口的进程..."
            local killed_count=0
            local failed_count=0
            
            for pid in "${pids[@]}"; do
                # 检查进程是否存在
                if kill -0 "$pid" 2>/dev/null; then
                    # 先尝试优雅终止
                    if kill "$pid" 2>/dev/null; then
                        print_info "已发送终止信号到进程 $pid"
                        killed_count=$((killed_count + 1))
                        # 等待2秒
                        sleep 2
                        # 如果进程还在，强制kill
                        if kill -0 "$pid" 2>/dev/null; then
                            print_warning "进程 $pid 未响应，强制kill..."
                            if kill -9 "$pid" 2>/dev/null; then
                                print_success "已强制kill进程 $pid"
                            else
                                print_error "无法kill进程 $pid（可能需要root权限）"
                                failed_count=$((failed_count + 1))
                            fi
                        else
                            print_success "进程 $pid 已终止"
                        fi
                    else
                        print_error "无法kill进程 $pid（可能需要root权限）"
                        failed_count=$((failed_count + 1))
                    fi
                else
                    print_info "进程 $pid 已不存在"
                fi
            done
            
            # 等待一下，让端口释放
            sleep 1
            
            # 再次检查端口是否释放
            if command -v lsof &> /dev/null; then
                if ! lsof -i :"$port" &> /dev/null; then
                    print_success "端口 $port 已释放"
                    return 0
                fi
            elif command -v netstat &> /dev/null; then
                if ! netstat -tuln 2>/dev/null | grep -q ":$port "; then
                    print_success "端口 $port 已释放"
                    return 0
                fi
            elif command -v ss &> /dev/null; then
                if ! ss -tuln 2>/dev/null | grep -q ":$port "; then
                    print_success "端口 $port 已释放"
                    return 0
                fi
            fi
            
            if [ $failed_count -gt 0 ]; then
                print_error "部分进程kill失败，端口可能仍被占用"
                print_info "请手动处理或修改 .env 文件中的 WEB_PORT 配置"
                return 1
            else
                print_warning "端口可能仍被占用，请稍后重试或手动检查"
                return 1
            fi
            ;;
        2)
            print_info "请手动停止占用端口的进程，或修改 .env 文件中的 WEB_PORT 配置"
            print_info "占用端口的进程PID: ${pids[*]}"
            print_info "可以使用以下命令kill进程: kill -9 ${pids[*]}"
            return 1
            ;;
        3)
            print_info "已取消操作"
            exit 0
            ;;
        *)
            print_error "无效选项，已取消操作"
            return 1
            ;;
    esac
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if [ -z "$port" ]; then
        # 从.env文件读取端口，如果没有则使用默认值8888
        if [ -f .env ]; then
            port=$(grep "^WEB_PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d ' ' | tr -d '"' | tr -d "'")
        fi
        port=${port:-8888}
    fi
    
    # 检查端口是否被占用
    local port_in_use=false
    
    if command -v lsof &> /dev/null; then
        if lsof -i :"$port" &> /dev/null; then
            port_in_use=true
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            port_in_use=true
        fi
    elif command -v ss &> /dev/null; then
        if ss -tuln 2>/dev/null | grep -q ":$port "; then
            port_in_use=true
        fi
    fi
    
    if [ "$port_in_use" = true ]; then
        handle_port_conflict "$port"
        return $?
    fi
    
    return 0
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

# 检查前端构建产物（已废弃，构建现在在容器内完成）
check_dist() {
    # 构建现在在Docker容器内完成，不再需要检查宿主机的dist目录
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

# 检查并切换 npm 源为国内源
check_and_switch_npm_registry() {
    if ! check_command npm; then
        return 0  # npm 不存在，跳过检查
    fi
    
    # 获取当前 npm 源
    CURRENT_REGISTRY=$(npm config get registry 2>/dev/null || echo "")
    
    # 国内源列表（支持新旧地址）
    DOMESTIC_REGISTRIES=(
        "https://registry.npmmirror.com"
        "https://registry.npm.taobao.org"
    )
    
    # 检查是否为国内源
    IS_DOMESTIC=false
    for registry in "${DOMESTIC_REGISTRIES[@]}"; do
        if [ "$CURRENT_REGISTRY" = "$registry" ] || [ "$CURRENT_REGISTRY" = "$registry/" ]; then
            IS_DOMESTIC=true
            break
        fi
    done
    
    # 如果不是国内源，切换为国内源
    if [ "$IS_DOMESTIC" = false ]; then
        print_warning "当前 npm 源: $CURRENT_REGISTRY"
        print_info "检测到非国内源，是否切换为国内源（淘宝镜像）？(Y/n)"
        read -r response
        if [[ ! "$response" =~ ^([nN][oO]|[nN])$ ]]; then
            print_info "正在切换 npm 源为国内源..."
            if npm config set registry https://registry.npmmirror.com; then
                print_success "npm 源已切换为: https://registry.npmmirror.com"
            else
                print_error "npm 源切换失败"
                return 1
            fi
        else
            print_info "保持当前 npm 源: $CURRENT_REGISTRY"
        fi
    else
        print_info "当前 npm 源已是国内源: $CURRENT_REGISTRY"
    fi
    
    return 0
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

# 构建前端项目（在宿主机上，可选，主要用于测试）
build_frontend() {
    print_warning "注意：前端构建现在在Docker容器内自动完成"
    print_info "此命令仅用于在宿主机上测试构建，不影响Docker部署"
    print_info "开始构建前端项目..."
    
    # 检查 Node.js
    if ! check_command node; then
        print_error "Node.js 未安装，请先安装 Node.js"
        echo "安装指南: https://nodejs.org/"
        exit 1
    fi
    
    # 检查并切换 npm 源为国内源
    check_and_switch_npm_registry
    
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
    
    print_success "前端项目构建完成（此构建仅用于测试，Docker部署时会重新构建）"
}

# 安装服务
install_service() {
    print_info "开始安装 WEB 服务..."
    
    check_docker
    check_docker_compose
    create_directories
    create_env_file
    
    # 检查端口占用
    if ! check_port; then
        print_error "端口检查失败，请解决端口占用问题后重试"
        exit 1
    fi
    
    # 注意：前端构建现在在Docker容器内完成，不再需要在宿主机上构建
    print_info "前端构建将在Docker容器内自动完成"
    
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
    if [ -f .env ]; then
        WEB_PORT=$(grep "^WEB_PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d ' ' | tr -d '"' | tr -d "'")
    fi
    WEB_PORT=${WEB_PORT:-8888}
    print_info "服务访问地址: http://localhost:${WEB_PORT}"
    print_info "健康检查地址: http://localhost:${WEB_PORT}/health"
    print_info "查看日志: ./install_linux.sh logs"
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
    
    # 检查端口占用
    if ! check_port; then
        print_error "端口检查失败，请解决端口占用问题后重试"
        exit 1
    fi
    
    # 注意：前端构建现在在Docker容器内完成，不再需要检查宿主机的dist目录
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
    
    # 注意：前端构建现在在Docker容器内完成，构建镜像时会自动完成
    print_info "前端构建将在Docker容器内自动完成"
    
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
    
    # 注意：前端构建现在在Docker容器内完成，重新构建镜像时会自动完成
    print_info "重新构建镜像（前端构建将在容器内自动完成）..."
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
    echo "  ./install_linux.sh [命令]"
    echo ""
    echo "可用命令:"
    echo "  install         - 安装并启动服务（首次运行）"
    echo "  start           - 启动服务"
    echo "  stop            - 停止服务"
    echo "  restart         - 重启服务"
    echo "  status          - 查看服务状态"
    echo "  logs            - 查看服务日志"
    echo "  logs -f         - 实时查看服务日志"
    echo "  build           - 重新构建镜像（前端构建在容器内自动完成）"
    echo "  build-frontend  - 在宿主机上构建前端项目（可选，用于测试）"
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

