#!/bin/bash

# ============================================
# Docker Compose 服务启动脚本
# ============================================
# 用于启动 docker-compose.yml 中定义的所有服务
# 使用方法：
#   ./start_services.sh [选项]
#
# 选项：
#   -w, --wait      启动后等待所有服务就绪（默认启用）
#   -v, --verify    启动后验证所有服务状态（默认启用）
#   -q, --quiet     静默模式，减少输出
#   -h, --help      显示帮助信息
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 默认选项
WAIT_FOR_SERVICES=true
VERIFY_SERVICES=true
QUIET_MODE=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--wait)
            WAIT_FOR_SERVICES=true
            shift
            ;;
        --no-wait)
            WAIT_FOR_SERVICES=false
            shift
            ;;
        -v|--verify)
            VERIFY_SERVICES=true
            shift
            ;;
        --no-verify)
            VERIFY_SERVICES=false
            shift
            ;;
        -q|--quiet)
            QUIET_MODE=true
            shift
            ;;
        -h|--help)
            echo "Docker Compose 服务启动脚本"
            echo ""
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -w, --wait        启动后等待所有服务就绪（默认启用）"
            echo "  --no-wait         不等待服务就绪"
            echo "  -v, --verify      启动后验证所有服务状态（默认启用）"
            echo "  --no-verify       不验证服务状态"
            echo "  -q, --quiet       静默模式，减少输出"
            echo "  -h, --help        显示此帮助信息"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 -h 或 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 打印带颜色的消息
print_info() {
    if [ "$QUIET_MODE" = false ]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

print_success() {
    if [ "$QUIET_MODE" = false ]; then
        echo -e "${GREEN}[SUCCESS]${NC} $1"
    fi
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    if [ "$QUIET_MODE" = false ]; then
        echo ""
        echo -e "${CYAN}========================================${NC}"
        echo -e "${CYAN}  $1${NC}"
        echo -e "${CYAN}========================================${NC}"
        echo ""
    fi
}

# 检查 Docker 是否运行
check_docker() {
    print_info "检查 Docker 服务状态..."
    if ! docker ps &> /dev/null; then
        print_error "无法访问 Docker，请确保 Docker 服务正在运行"
        echo ""
        echo "解决方案："
        echo "  1. 启动 Docker 服务: sudo systemctl start docker"
        echo "  2. 检查 Docker 状态: sudo systemctl status docker"
        echo "  3. 如果当前用户没有权限，请添加到 docker 组："
        echo "     sudo usermod -aG docker \$USER"
        echo "     然后重新登录或运行: newgrp docker"
        exit 1
    fi
    print_success "Docker 服务正在运行"
}

# 检查 Docker Compose
check_docker_compose() {
    print_info "检查 Docker Compose..."
    
    # 检查 docker compose (v2)
    if docker compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
        print_success "Docker Compose v2 可用"
        return 0
    fi
    
    # 检查 docker-compose (v1)
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        print_success "Docker Compose v1 可用"
        return 0
    fi
    
    print_error "Docker Compose 未安装或不可用"
    echo ""
    echo "安装方法："
    echo "  Docker Compose v2 (推荐):"
    echo "    通常随 Docker Desktop 或 Docker Engine 一起安装"
    echo ""
    echo "  Docker Compose v1:"
    echo "    sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
    echo "    sudo chmod +x /usr/local/bin/docker-compose"
    exit 1
}

# 检查 docker-compose.yml 文件
check_compose_file() {
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml 文件不存在"
        exit 1
    fi
    print_success "找到 docker-compose.yml 文件"
}

# 检查并创建 Docker 网络
check_network() {
    print_info "检查 Docker 网络..."
    if docker network ls --format "{{.Name}}" | grep -q "^easyaiot-network$"; then
        print_success "网络 easyaiot-network 已存在"
    else
        print_warning "网络 easyaiot-network 不存在，正在创建..."
        if docker network create easyaiot-network &> /dev/null; then
            print_success "网络 easyaiot-network 创建成功"
        else
            print_error "网络创建失败"
            exit 1
        fi
    fi
}

# 启动服务
start_services() {
    print_section "启动所有服务"
    
    print_info "使用命令: $COMPOSE_CMD up -d"
    
    if $COMPOSE_CMD up -d; then
        print_success "所有服务启动命令已执行"
    else
        print_error "服务启动失败"
        echo ""
        echo "请检查："
        echo "  1. docker-compose.yml 文件是否正确"
        echo "  2. 端口是否被占用"
        echo "  3. 查看详细错误: $COMPOSE_CMD up -d"
        exit 1
    fi
}

# 等待服务就绪
wait_for_services() {
    if [ "$WAIT_FOR_SERVICES" = false ]; then
        return 0
    fi
    
    print_section "等待服务就绪"
    
    local max_wait=300  # 最大等待时间（秒）
    local elapsed=0
    local interval=5    # 检查间隔（秒）
    
    print_info "等待服务启动（最多 ${max_wait} 秒）..."
    
    while [ $elapsed -lt $max_wait ]; do
        local all_healthy=true
        local running_count=0
        local total_count=0
        
        # 检查主要服务容器
        local services=(
            "nacos-server"
            "postgres-server"
            "tdengine-server"
            "redis-server"
            "kafka-server"
            "minio-server"
            "srs-server"
            "nodered-server"
            "emqx-server"
        )
        
        for container in "${services[@]}"; do
            total_count=$((total_count + 1))
            if docker ps --filter "name=${container}" --format "{{.Names}}" | grep -q "^${container}$"; then
                running_count=$((running_count + 1))
                # 检查健康状态（如果配置了健康检查）
                local health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none")
                if [ "$health" = "unhealthy" ]; then
                    all_healthy=false
                elif [ "$health" = "starting" ]; then
                    all_healthy=false
                fi
            else
                all_healthy=false
            fi
        done
        
        if [ "$QUIET_MODE" = false ]; then
            echo -ne "\r${BLUE}[INFO]${NC} 运行中: ${running_count}/${total_count}   "
        fi
        
        if [ $running_count -eq $total_count ] && [ "$all_healthy" = true ]; then
            if [ "$QUIET_MODE" = false ]; then
                echo ""
            fi
            print_success "所有服务已启动并运行"
            return 0
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    if [ "$QUIET_MODE" = false ]; then
        echo ""
    fi
    print_warning "等待超时，部分服务可能仍在启动中"
    print_info "运行中的服务: ${running_count}/${total_count}"
}

# 显示服务状态
show_status() {
    print_section "服务状态"
    
    echo -e "${CYAN}容器状态:${NC}"
    $COMPOSE_CMD ps
    
    echo ""
    echo -e "${CYAN}快速命令:${NC}"
    echo "  查看所有容器: docker ps"
    echo "  查看服务日志: $COMPOSE_CMD logs [服务名]"
    echo "  查看所有日志: $COMPOSE_CMD logs"
    echo "  停止所有服务: $COMPOSE_CMD down"
    echo "  重启服务: $COMPOSE_CMD restart [服务名]"
    echo "  验证服务: ./verify_services.sh"
}

# 验证服务
verify_services() {
    if [ "$VERIFY_SERVICES" = false ]; then
        return 0
    fi
    
    if [ -f "./verify_services.sh" ]; then
        print_section "验证服务状态"
        if [ "$QUIET_MODE" = true ]; then
            ./verify_services.sh 2>&1 | grep -E "\[(SUCCESS|ERROR|WARNING|INFO)\]" || true
        else
            ./verify_services.sh
        fi
    else
        print_warning "验证脚本 verify_services.sh 不存在，跳过验证"
    fi
}

# 主函数
main() {
    print_section "Docker Compose 服务启动工具"
    
    # 检查前置条件
    check_docker
    check_docker_compose
    check_compose_file
    check_network
    
    # 启动服务
    start_services
    
    # 等待服务就绪
    wait_for_services
    
    # 显示状态
    show_status
    
    # 验证服务
    verify_services
    
    echo ""
    print_success "服务启动完成！"
    echo ""
    print_info "访问地址："
    echo "  Nacos:     http://localhost:8848/nacos (用户名/密码: nacos/nacos)"
    echo "  MinIO:     http://localhost:9001 (用户名/密码: minioadmin/basiclab@iot975248395)"
    echo "  NodeRED:   http://localhost:1880"
    echo "  EMQX:      http://localhost:18083 (用户名/密码: admin/basiclab@iot6874125784)"
    echo "  SRS:       http://localhost:1985/api/v1/versions"
    echo ""
}

# 执行主函数
main "$@"

