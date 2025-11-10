#!/bin/bash

# ============================================
# EasyAIoT 统一安装脚本
# ============================================
# 使用方法：
#   ./install.sh [命令]
#
# 可用命令：
#   install    - 安装并启动所有服务（首次运行）
#   start      - 启动所有服务
#   stop       - 停止所有服务
#   restart    - 重启所有服务
#   status     - 查看所有服务状态
#   logs       - 查看服务日志
#   build      - 重新构建所有镜像
#   clean      - 清理所有容器和镜像
#   update     - 更新并重启所有服务
#   verify     - 验证所有服务是否启动成功
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# 模块列表（按依赖顺序）
MODULES=(
    ".scripts/docker"  # 基础服务（Nacos、PostgreSQL、Redis等）
    "DEVICE"           # Device服务（网关和微服务）
    "AI"               # AI服务
    "VIDEO"            # Video服务
    "WEB"              # Web前端服务
)

# 模块名称映射
declare -A MODULE_NAMES
MODULE_NAMES[".scripts/docker"]="基础服务"
MODULE_NAMES["DEVICE"]="Device服务"
MODULE_NAMES["AI"]="AI服务"
MODULE_NAMES["VIDEO"]="Video服务"
MODULE_NAMES["WEB"]="Web前端服务"

# 模块端口映射
declare -A MODULE_PORTS
MODULE_PORTS[".scripts/docker"]="8848"  # Nacos端口
MODULE_PORTS["DEVICE"]="48080"           # Gateway端口
MODULE_PORTS["AI"]="5000"
MODULE_PORTS["VIDEO"]="6000"
MODULE_PORTS["WEB"]="80"

# 模块健康检查端点
declare -A MODULE_HEALTH_ENDPOINTS
MODULE_HEALTH_ENDPOINTS[".scripts/docker"]="/nacos/actuator/health"
MODULE_HEALTH_ENDPOINTS["DEVICE"]="/actuator/health"  # Gateway健康检查
MODULE_HEALTH_ENDPOINTS["AI"]="/actuator/health"
MODULE_HEALTH_ENDPOINTS["VIDEO"]="/actuator/health"
MODULE_HEALTH_ENDPOINTS["WEB"]="/health"

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

print_section() {
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
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

# 创建统一网络
create_network() {
    print_info "创建统一网络 easyaiot-network..."
    if ! docker network ls | grep -q easyaiot-network; then
        docker network create easyaiot-network 2>/dev/null || true
        print_success "网络 easyaiot-network 已创建"
    else
        print_info "网络 easyaiot-network 已存在"
    fi
}

# 执行模块命令
execute_module_command() {
    local module=$1
    local command=$2
    local module_name=${MODULE_NAMES[$module]}
    
    if [ ! -d "$PROJECT_ROOT/$module" ]; then
        print_warning "模块 $module 不存在，跳过"
        return 1
    fi
    
    cd "$PROJECT_ROOT/$module"
    
    # 特殊处理.scripts/docker和DEVICE模块（使用docker-compose.yml）
    if [ "$module" = ".scripts/docker" ] || [ "$module" = "DEVICE" ]; then
        # 检查docker-compose文件
        local compose_file="docker-compose.yml"
        if [ ! -f "$compose_file" ]; then
            print_warning "模块 $module 没有 $compose_file 文件，跳过"
            return 1
        fi
        
        # 确定docker compose命令
        local compose_cmd
        if check_command docker-compose; then
            compose_cmd="docker-compose"
        else
            compose_cmd="docker compose"
        fi
        
        print_info "执行 $module_name: $command"
        
        case "$command" in
            install|start)
                $compose_cmd -f "$compose_file" up -d
                ;;
            stop)
                $compose_cmd -f "$compose_file" down
                ;;
            restart)
                $compose_cmd -f "$compose_file" restart
                ;;
            status)
                $compose_cmd -f "$compose_file" ps
                ;;
            logs)
                $compose_cmd -f "$compose_file" logs --tail=100
                ;;
            build)
                $compose_cmd -f "$compose_file" build --no-cache
                ;;
            clean)
                $compose_cmd -f "$compose_file" down -v
                ;;
            update)
                $compose_cmd -f "$compose_file" pull
                $compose_cmd -f "$compose_file" up -d
                ;;
            *)
                print_warning "未知命令: $command"
                return 1
                ;;
        esac
        
        if [ $? -eq 0 ]; then
            print_success "$module_name: $command 执行成功"
            return 0
        else
            print_error "$module_name: $command 执行失败"
            return 1
        fi
    else
        # 其他模块使用install.sh脚本
        if [ ! -f "install.sh" ]; then
            print_warning "模块 $module 没有 install.sh 脚本，跳过"
            return 1
        fi
        
        print_info "执行 $module_name: $command"
        
        if bash install.sh "$command" 2>&1; then
            print_success "$module_name: $command 执行成功"
            return 0
        else
            print_error "$module_name: $command 执行失败"
            return 1
        fi
    fi
}

# 等待服务就绪
wait_for_service() {
    local service_name=$1
    local port=$2
    local health_endpoint=$3
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        # 尝试多种方式检测服务
        if [ -n "$health_endpoint" ]; then
            # 使用健康检查端点
            if curl -s --connect-timeout 2 "http://localhost:$port$health_endpoint" > /dev/null 2>&1; then
                return 0
            fi
        else
            # 使用端口检测
            if command -v nc &> /dev/null && nc -z localhost $port 2>/dev/null; then
                return 0
            elif command -v timeout &> /dev/null && timeout 1 bash -c "cat < /dev/null > /dev/tcp/localhost/$port" 2>/dev/null; then
                return 0
            elif curl -s --connect-timeout 1 "http://localhost:$port" > /dev/null 2>&1; then
                return 0
            fi
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    return 1
}

# 验证服务健康状态
verify_service_health() {
    local module=$1
    local module_name=${MODULE_NAMES[$module]}
    local port=${MODULE_PORTS[$module]}
    local health_endpoint=${MODULE_HEALTH_ENDPOINTS[$module]}
    
    print_info "验证 $module_name (端口: $port)..."
    
    if wait_for_service "$module_name" "$port" "$health_endpoint"; then
        # 检查HTTP响应
        if [ -n "$health_endpoint" ]; then
            response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port$health_endpoint" 2>/dev/null || echo "000")
            if [ "$response" = "200" ] || [ "$response" = "000" ]; then
                print_success "$module_name 运行正常"
                return 0
            else
                print_warning "$module_name 响应异常 (HTTP $response)"
                return 1
            fi
        else
            print_success "$module_name 运行正常"
            return 0
        fi
    else
        print_error "$module_name 未就绪"
        return 1
    fi
}

# 安装所有服务
install_all() {
    print_section "开始安装所有服务"
    
    check_docker
    check_docker_compose
    create_network
    
    local success_count=0
    local total_count=${#MODULES[@]}
    
    for module in "${MODULES[@]}"; do
        print_section "安装 ${MODULE_NAMES[$module]}"
        if execute_module_command "$module" "install"; then
            success_count=$((success_count + 1))
        else
            print_error "${MODULE_NAMES[$module]} 安装失败"
        fi
        echo ""
    done
    
    print_section "安装完成"
    echo "成功安装: $success_count / $total_count 个模块"
    
    if [ $success_count -eq $total_count ]; then
        print_success "所有模块安装成功！"
        echo ""
        print_info "等待服务启动..."
        sleep 10
        verify_all
    else
        print_warning "部分模块安装失败，请检查日志"
        exit 1
    fi
}

# 启动所有服务
start_all() {
    print_section "启动所有服务"
    
    check_docker
    check_docker_compose
    create_network
    
    for module in "${MODULES[@]}"; do
        execute_module_command "$module" "start"
        echo ""
    done
    
    print_success "所有服务启动完成"
    echo ""
    print_info "等待服务就绪..."
    sleep 10
    verify_all
}

# 停止所有服务
stop_all() {
    print_section "停止所有服务"
    
    check_docker
    check_docker_compose
    
    # 逆序停止
    for ((idx=${#MODULES[@]}-1 ; idx>=0 ; idx--)); do
        execute_module_command "${MODULES[idx]}" "stop"
        echo ""
    done
    
    print_success "所有服务已停止"
}

# 重启所有服务
restart_all() {
    print_section "重启所有服务"
    
    check_docker
    check_docker_compose
    create_network
    
    for module in "${MODULES[@]}"; do
        execute_module_command "$module" "restart"
        echo ""
    done
    
    print_success "所有服务重启完成"
    echo ""
    print_info "等待服务就绪..."
    sleep 10
    verify_all
}

# 查看所有服务状态
status_all() {
    print_section "所有服务状态"
    
    check_docker
    check_docker_compose
    
    for module in "${MODULES[@]}"; do
        print_section "${MODULE_NAMES[$module]} 状态"
        execute_module_command "$module" "status"
        echo ""
    done
}

# 查看日志
view_logs() {
    local module=${1:-""}
    
    if [ -z "$module" ]; then
        print_info "查看所有服务日志..."
        check_docker
        check_docker_compose
        
        for module in "${MODULES[@]}"; do
            print_section "${MODULE_NAMES[$module]} 日志"
            execute_module_command "$module" "logs"
            echo ""
        done
    else
        print_info "查看 $module 服务日志..."
        execute_module_command "$module" "logs"
    fi
}

# 构建所有镜像
build_all() {
    print_section "构建所有镜像"
    
    check_docker
    check_docker_compose
    
    for module in "${MODULES[@]}"; do
        execute_module_command "$module" "build"
        echo ""
    done
    
    print_success "所有镜像构建完成"
}

# 清理所有服务
clean_all() {
    print_warning "这将删除所有容器、镜像和数据卷，确定要继续吗？(y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_section "清理所有服务"
        
        check_docker
        check_docker_compose
        
        # 逆序清理
        for ((idx=${#MODULES[@]}-1 ; idx>=0 ; idx--)); do
            execute_module_command "${MODULES[idx]}" "clean"
            echo ""
        done
        
        # 清理网络
        print_info "清理网络..."
        docker network rm easyaiot-network 2>/dev/null || true
        
        print_success "清理完成"
    else
        print_info "已取消清理操作"
    fi
}

# 更新所有服务
update_all() {
    print_section "更新所有服务"
    
    check_docker
    check_docker_compose
    create_network
    
    for module in "${MODULES[@]}"; do
        execute_module_command "$module" "update"
        echo ""
    done
    
    print_success "所有服务更新完成"
    echo ""
    print_info "等待服务就绪..."
    sleep 10
    verify_all
}

# 验证所有服务
verify_all() {
    print_section "验证所有服务"
    
    check_docker
    
    local success_count=0
    local total_count=${#MODULES[@]}
    local failed_modules=()
    
    for module in "${MODULES[@]}"; do
        if verify_service_health "$module"; then
            success_count=$((success_count + 1))
        else
            failed_modules+=("${MODULE_NAMES[$module]}")
        fi
        echo ""
    done
    
    print_section "验证结果"
    echo "成功: ${GREEN}$success_count${NC} / $total_count"
    
    if [ $success_count -eq $total_count ]; then
        print_success "所有服务运行正常！"
        echo ""
        echo -e "${GREEN}服务访问地址:${NC}"
        echo -e "  基础服务 (Nacos):     http://localhost:8848/nacos"
        echo -e "  Device服务 (Gateway):  http://localhost:48080"
        echo -e "  AI服务:                http://localhost:5000"
        echo -e "  Video服务:             http://localhost:6000"
        echo -e "  Web前端:               http://localhost:80"
        echo ""
        return 0
    else
        print_warning "部分服务未就绪:"
        for failed in "${failed_modules[@]}"; do
            echo -e "  ${RED}✗ $failed${NC}"
        done
        echo ""
        print_info "查看日志: ./install.sh logs"
        return 1
    fi
}

# 显示帮助信息
show_help() {
    echo "EasyAIoT 统一安装脚本"
    echo ""
    echo "使用方法:"
    echo "  ./install.sh [命令] [模块]"
    echo ""
    echo "可用命令:"
    echo "  install         - 安装并启动所有服务（首次运行）"
    echo "  start           - 启动所有服务"
    echo "  stop            - 停止所有服务"
    echo "  restart         - 重启所有服务"
    echo "  status          - 查看所有服务状态"
    echo "  logs            - 查看所有服务日志"
    echo "  logs [模块]     - 查看指定模块日志"
    echo "  build           - 重新构建所有镜像"
    echo "  clean           - 清理所有容器和镜像"
    echo "  update          - 更新并重启所有服务"
    echo "  verify          - 验证所有服务是否启动成功"
    echo "  help            - 显示此帮助信息"
    echo ""
    echo "模块列表:"
    for module in "${MODULES[@]}"; do
        echo "  - ${MODULE_NAMES[$module]} ($module)"
    done
    echo ""
}

# 主函数
main() {
    case "${1:-help}" in
        install)
            install_all
            ;;
        start)
            start_all
            ;;
        stop)
            stop_all
            ;;
        restart)
            restart_all
            ;;
        status)
            status_all
            ;;
        logs)
            view_logs "$2"
            ;;
        build)
            build_all
            ;;
        clean)
            clean_all
            ;;
        update)
            update_all
            ;;
        verify)
            verify_all
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
