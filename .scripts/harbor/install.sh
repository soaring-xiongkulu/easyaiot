#!/bin/bash

# Harbor 服务管理脚本
# 用法: ./manage.sh [start|stop|restart|status|logs|ps|down|up]

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 显示使用说明
show_usage() {
    echo "Harbor 服务管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "可用命令:"
    echo "  start      - 启动 Harbor 服务"
    echo "  stop       - 停止 Harbor 服务"
    echo "  restart    - 重启 Harbor 服务"
    echo "  status     - 查看服务状态"
    echo "  logs       - 查看服务日志 (支持 -f 参数实时跟踪)"
    echo "  ps         - 查看运行中的容器"
    echo "  up         - 创建并启动服务 (等同于 start)"
    echo "  down       - 停止并删除容器"
    echo "  clean      - 清理停止的容器和未使用的资源"
    echo "  help       - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start              # 启动服务"
    echo "  $0 logs -f            # 实时查看日志"
    echo "  $0 logs core          # 查看 core 服务日志"
    echo "  $0 logs -f proxy      # 实时查看 proxy 服务日志"
}

# 检查 docker-compose 是否可用
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "未找到 docker-compose 或 docker compose 命令"
        exit 1
    fi
}

# 获取 docker-compose 命令
get_docker_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        echo "docker compose"
    fi
}

# 启动服务
start_services() {
    print_info "正在启动 Harbor 服务..."
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    $DOCKER_COMPOSE up -d
    if [ $? -eq 0 ]; then
        print_success "Harbor 服务启动成功"
        echo ""
        print_info "等待服务就绪..."
        sleep 3
        show_status
    else
        print_error "Harbor 服务启动失败"
        exit 1
    fi
}

# 停止服务
stop_services() {
    print_info "正在停止 Harbor 服务..."
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    $DOCKER_COMPOSE stop
    if [ $? -eq 0 ]; then
        print_success "Harbor 服务已停止"
    else
        print_error "停止 Harbor 服务失败"
        exit 1
    fi
}

# 重启服务
restart_services() {
    print_info "正在重启 Harbor 服务..."
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    $DOCKER_COMPOSE restart
    if [ $? -eq 0 ]; then
        print_success "Harbor 服务重启成功"
        echo ""
        sleep 2
        show_status
    else
        print_error "重启 Harbor 服务失败"
        exit 1
    fi
}

# 查看服务状态
show_status() {
    print_info "Harbor 服务状态:"
    echo ""
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    $DOCKER_COMPOSE ps
    echo ""
    print_info "服务健康检查:"
    $DOCKER_COMPOSE ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

# 查看日志
show_logs() {
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    if [ -z "$1" ]; then
        print_info "查看所有 Harbor 服务日志..."
        $DOCKER_COMPOSE logs "$@"
    else
        print_info "查看 Harbor 服务日志: $*"
        $DOCKER_COMPOSE logs "$@"
    fi
}

# 查看容器列表
show_containers() {
    print_info "Harbor 运行中的容器:"
    echo ""
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    $DOCKER_COMPOSE ps
}

# 停止并删除容器
down_services() {
    print_warning "此操作将停止并删除所有 Harbor 容器"
    read -p "确定要继续吗? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "正在停止并删除 Harbor 容器..."
        DOCKER_COMPOSE=$(get_docker_compose_cmd)
        $DOCKER_COMPOSE down
        if [ $? -eq 0 ]; then
            print_success "Harbor 容器已停止并删除"
        else
            print_error "操作失败"
            exit 1
        fi
    else
        print_info "操作已取消"
    fi
}

# 清理资源
clean_resources() {
    print_info "正在清理 Harbor 相关资源..."
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    $DOCKER_COMPOSE down --remove-orphans
    docker system prune -f --volumes --filter "label=com.docker.compose.project=harbor" 2>/dev/null || true
    print_success "清理完成"
}

# 主函数
main() {
    check_docker_compose

    case "${1:-help}" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            shift
            show_logs "$@"
            ;;
        ps)
            show_containers
            ;;
        up)
            start_services
            ;;
        down)
            down_services
            ;;
        clean)
            clean_resources
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "未知命令: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

main "$@"

