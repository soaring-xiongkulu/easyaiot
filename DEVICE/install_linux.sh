#!/bin/bash

# DEVICE模块 Docker Compose 管理脚本
# 用于管理DEVICE目录下的所有Docker服务
# 使用统一的多阶段构建 Dockerfile

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"

# 检查docker-compose是否存在
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: 未找到docker或docker-compose命令${NC}"
    exit 1
fi

# 使用docker compose（新版本）或docker-compose（旧版本）
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif docker-compose version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo -e "${RED}错误: 未找到docker compose或docker-compose命令${NC}"
    exit 1
fi

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

# 检查docker-compose.yml是否存在
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yml文件不存在: $COMPOSE_FILE"
        exit 1
    fi
    
    # 验证文件是否可读
    if [ ! -r "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yml 文件不可读: $COMPOSE_FILE"
        exit 1
    fi
}

# 检查 Docker daemon 是否运行
check_docker_daemon() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon 未运行，请先启动 Docker 服务"
        print_info "尝试启动: sudo systemctl start docker"
        exit 1
    fi
}

# 检查所有运行时镜像是否已存在
check_images_exist() {
    local images=(
        "iot-gateway:latest"
        "iot-module-system-biz:latest"
        "iot-module-infra-biz:latest"
        "iot-module-device-biz:latest"
        "iot-module-dataset-biz:latest"
        "iot-module-tdengine-biz:latest"
        "iot-module-file-biz:latest"
        "iot-module-message-biz:latest"
        "iot-sink-biz:latest"
    )
    
    local missing_count=0
    
    for image in "${images[@]}"; do
        if ! docker image inspect "$image" > /dev/null 2>&1; then
            missing_count=$((missing_count + 1))
        fi
    done
    
    if [ "$missing_count" -eq 0 ]; then
        return 0  # 所有镜像都存在
    else
        return 1  # 有镜像缺失
    fi
}

# 构建所有镜像
build_images() {
    print_info "========== 构建所有运行时镜像 =========="
    
    # 检查镜像是否已存在
    if check_images_exist; then
        print_success "所有运行时镜像已存在，跳过构建阶段"
        print_success "========== 构建完成（跳过）=========="
        echo
        return 0
    fi
    
    # 确保权限正确
    check_compose_file
    check_docker_daemon
    
    cd "$SCRIPT_DIR"
    
    # 构建所有运行时镜像
    print_info "构建所有运行时镜像..."
    local exit_code
    
    # 构建所有服务镜像
    $DOCKER_COMPOSE build --parallel
    exit_code=$?
    
    # 检查命令是否成功
    if [ $exit_code -ne 0 ]; then
        print_error "运行时镜像构建失败（退出码: $exit_code）"
        exit 1
    fi
    
    print_success "========== 所有运行时镜像构建完成 =========="
    echo
}

# 构建并启动所有服务
build_and_start() {
    print_info "========== 开始构建并启动所有服务 =========="
    echo
    
    # 确保权限正确
    print_info "检查 Docker Compose 配置文件..."
    check_compose_file
    check_docker_daemon
    print_success "配置文件检查完成"
    
    print_info "切换到脚本目录: $SCRIPT_DIR"
    if ! cd "$SCRIPT_DIR"; then
        print_error "无法切换到目录: $SCRIPT_DIR"
        exit 1
    fi
    print_success "当前工作目录: $(pwd)"
    
    # 验证 Docker Compose 可以读取配置文件
    print_info "验证 Docker Compose 可以读取配置文件..."
    local compose_test_output
    set +e  # 暂时关闭错误退出，以便捕获退出码
    compose_test_output=$($DOCKER_COMPOSE -f "$COMPOSE_FILE" config 2>&1)
    local compose_test_exit=$?
    set -e  # 重新开启错误退出
    
    if [ $compose_test_exit -ne 0 ]; then
        print_error "Docker Compose 无法读取配置文件"
        echo "$compose_test_output" | sed 's/^/  /'
        exit 1
    else
        print_success "Docker Compose 配置文件验证通过"
    fi
    
    echo
    
    # 构建所有镜像
    build_images
    
    # 启动所有服务
    print_info "========== 启动所有服务 =========="
    
    print_info "准备启动所有服务..."
    echo
    
    # 启动所有服务
    print_info "启动所有服务..."
    set +e  # 暂时关闭错误退出，以便捕获退出码
    $DOCKER_COMPOSE up -d
    exit_code=$?
    set -e  # 重新开启错误退出
    
    echo  # 添加空行分隔
    
    # 检查命令是否成功
    if [ $exit_code -ne 0 ]; then
        print_error "服务启动失败（退出码: $exit_code）"
        exit 1
    fi
    
    # 验证容器是否真的创建了
    local container_count
    container_count=$($DOCKER_COMPOSE ps -q 2>/dev/null | wc -l)
    if [ "$container_count" -eq 0 ]; then
        print_error "警告：没有检测到运行的容器"
        print_info "请检查 docker-compose.yml 配置和依赖服务（如 Nacos、PostgreSQL、Redis 等）"
        print_info "尝试查看服务状态："
        $DOCKER_COMPOSE ps
        exit 1
    fi
    
    print_success "========== 服务构建并启动完成 =========="
    print_success "服务构建并启动完成（共 $container_count 个容器）"
    echo
    print_info "可以使用以下命令查看服务状态:"
    print_info "  $0 status"
    print_info "  $0 logs [服务名]"
}

# 启动所有服务
start_services() {
    print_info "启动所有服务..."
    cd "$SCRIPT_DIR"
    # 使用 --quiet-pull 减少拉取镜像时的输出
    if echo "$DOCKER_COMPOSE" | grep -q "docker compose"; then
        $DOCKER_COMPOSE up -d --quiet-pull 2>&1 | grep -E "(Creating|Starting|Started|ERROR|WARNING)" || true
    else
        $DOCKER_COMPOSE up -d 2>&1 | grep -E "(Creating|Starting|Started|ERROR|WARNING)" || true
    fi
    print_success "服务启动完成"
}

# 停止所有服务
stop_services() {
    print_info "停止所有服务..."
    cd "$SCRIPT_DIR"
    $DOCKER_COMPOSE down
    print_success "服务已停止"
}

# 重启所有服务
restart_services() {
    print_info "重启所有服务..."
    cd "$SCRIPT_DIR"
    $DOCKER_COMPOSE restart
    print_success "服务重启完成"
}

# 查看服务状态
show_status() {
    print_info "服务状态:"
    cd "$SCRIPT_DIR"
    $DOCKER_COMPOSE ps
}

# 查看日志
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        print_info "查看所有服务日志（最近50行，按Ctrl+C退出）..."
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE logs -f --tail=50
    else
        print_info "查看服务 $service 的日志（最近50行，按Ctrl+C退出）..."
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE logs -f --tail=50 "$service"
    fi
}

# 查看特定服务的日志（最近50行）
show_logs_tail() {
    local service=$1
    if [ -z "$service" ]; then
        print_info "查看所有服务最近50行日志..."
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE logs --tail=50
    else
        print_info "查看服务 $service 最近50行日志..."
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE logs --tail=50 "$service"
    fi
}

# 重启特定服务
restart_service() {
    local service=$1
    if [ -z "$service" ]; then
        print_error "请指定要重启的服务名称"
        echo "可用服务:"
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE config --services
        exit 1
    fi
    print_info "重启服务: $service"
    cd "$SCRIPT_DIR"
    $DOCKER_COMPOSE restart "$service"
    print_success "服务 $service 重启完成"
}

# 停止特定服务
stop_service() {
    local service=$1
    if [ -z "$service" ]; then
        print_error "请指定要停止的服务名称"
        echo "可用服务:"
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE config --services
        exit 1
    fi
    print_info "停止服务: $service"
    cd "$SCRIPT_DIR"
    $DOCKER_COMPOSE stop "$service"
    print_success "服务 $service 已停止"
}

# 启动特定服务
start_service() {
    local service=$1
    if [ -z "$service" ]; then
        print_error "请指定要启动的服务名称"
        echo "可用服务:"
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE config --services
        exit 1
    fi
    print_info "启动服务: $service"
    cd "$SCRIPT_DIR"
    $DOCKER_COMPOSE up -d "$service"
    print_success "服务 $service 启动完成"
}

# 清理（停止并删除容器）
clean() {
    print_warning "这将停止并删除所有容器，但保留镜像"
    read -p "确认继续? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE down
        print_success "清理完成"
    else
        print_info "操作已取消"
    fi
}

# 完全清理（包括镜像）
clean_all() {
    print_warning "这将停止并删除所有容器和镜像"
    read -p "确认继续? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE down --rmi all
        print_success "完全清理完成"
    else
        print_info "操作已取消"
    fi
}

# 更新服务（重新构建并重启）
update_services() {
    print_info "========== 更新所有服务 =========="
    
    # 确保权限正确
    check_compose_file
    check_docker_daemon
    
    cd "$SCRIPT_DIR"
    
    # 重新构建运行时镜像
    print_info "重新构建运行时镜像..."
    build_images
    
    # 重启所有服务
    print_info "重启所有服务..."
    local exit_code
    
    # 强制重新创建并启动所有服务
    $DOCKER_COMPOSE up -d --force-recreate
    exit_code=$?
    
    # 检查命令是否成功
    if [ $exit_code -ne 0 ]; then
        print_error "服务更新失败（退出码: $exit_code）"
        exit 1
    fi
    
    # 验证容器是否真的创建了
    local container_count
    container_count=$($DOCKER_COMPOSE ps -q 2>/dev/null | wc -l)
    if [ "$container_count" -eq 0 ]; then
        print_error "警告：没有检测到运行的容器"
        print_info "请检查 docker-compose.yml 配置和依赖服务（如 Nacos、PostgreSQL、Redis 等）"
        print_info "尝试查看服务状态："
        $DOCKER_COMPOSE ps
        exit 1
    fi
    
    print_success "========== 服务更新完成（共 $container_count 个容器）=========="
}

# 显示帮助信息
show_help() {
    cat << EOF
DEVICE模块 Docker Compose 管理脚本

用法: $0 [命令] [选项]

构建流程:
    使用统一的多阶段构建 Dockerfile，在一个构建过程中完成所有服务的编译和镜像构建
    所有服务共享同一个构建阶段，提高构建效率

命令:
    build               构建所有运行时镜像
    start               启动所有服务
    stop                停止所有服务
    restart             重启所有服务
    status              查看服务状态
    logs [服务名]       查看日志（所有服务或指定服务，最近50行）
    logs-tail [服务名]  查看最近50行日志
    restart-service     重启指定服务
    stop-service        停止指定服务
    start-service       启动指定服务
    clean               清理（停止并删除容器，保留镜像）
    clean-all           完全清理（停止并删除容器和镜像）
    update              更新服务（重新构建并重启）
    install             安装（构建并启动所有服务）
    help                显示此帮助信息

示例:
    $0 install                    # 构建并启动所有服务
    $0 build                      # 仅构建运行时镜像
    $0 start                      # 启动所有服务
    $0 logs iot-gateway           # 查看iot-gateway的日志
    $0 restart-service iot-system # 重启iot-system服务
    $0 status                     # 查看所有服务状态

可用服务:
    - iot-gateway
    - iot-system
    - iot-infra
    - iot-device
    - iot-dataset
    - iot-tdengine
    - iot-file
    - iot-message
    - iot-sink

EOF
}

# 主函数
main() {
    check_compose_file
    
    case "${1:-}" in
        build)
            build_images
            ;;
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
            show_logs "$2"
            ;;
        logs-tail)
            show_logs_tail "$2"
            ;;
        restart-service)
            restart_service "$2"
            ;;
        stop-service)
            stop_service "$2"
            ;;
        start-service)
            start_service "$2"
            ;;
        clean)
            clean
            ;;
        clean-all)
            clean_all
            ;;
        update)
            update_services
            ;;
        install|build-and-start)
            build_and_start
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            # 如果没有参数，显示交互式菜单
            show_interactive_menu
            ;;
        *)
            print_error "未知命令: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# 交互式菜单
show_interactive_menu() {
    while true; do
        echo
        echo -e "${BLUE}========================================${NC}"
        echo -e "${BLUE}  DEVICE模块 Docker Compose 管理${NC}"
        echo -e "${BLUE}========================================${NC}"
        echo "1) 安装/构建并启动所有服务"
        echo "2) 构建所有运行时镜像"
        echo "3) 启动所有服务"
        echo "4) 停止所有服务"
        echo "5) 重启所有服务"
        echo "6) 查看服务状态"
        echo "7) 查看日志（所有服务）"
        echo "8) 查看日志（指定服务）"
        echo "9) 重启指定服务"
        echo "10) 停止指定服务"
        echo "11) 启动指定服务"
        echo "12) 更新服务（重新构建并重启）"
        echo "13) 清理（删除容器，保留镜像）"
        echo "14) 完全清理（删除容器和镜像）"
        echo "0) 退出"
        echo
        read -p "请选择操作 [0-14]: " choice
        
        case $choice in
            1)
                build_and_start
                ;;
            2)
                build_images
                ;;
            3)
                start_services
                ;;
            4)
                stop_services
                ;;
            5)
                restart_services
                ;;
            6)
                show_status
                ;;
            7)
                show_logs
                ;;
            8)
                echo "可用服务:"
                cd "$SCRIPT_DIR"
                $DOCKER_COMPOSE config --services
                read -p "请输入服务名称: " service_name
                show_logs "$service_name"
                ;;
            9)
                echo "可用服务:"
                cd "$SCRIPT_DIR"
                $DOCKER_COMPOSE config --services
                read -p "请输入服务名称: " service_name
                restart_service "$service_name"
                ;;
            10)
                echo "可用服务:"
                cd "$SCRIPT_DIR"
                $DOCKER_COMPOSE config --services
                read -p "请输入服务名称: " service_name
                stop_service "$service_name"
                ;;
            11)
                echo "可用服务:"
                cd "$SCRIPT_DIR"
                $DOCKER_COMPOSE config --services
                read -p "请输入服务名称: " service_name
                start_service "$service_name"
                ;;
            12)
                update_services
                ;;
            13)
                clean
                ;;
            14)
                clean_all
                ;;
            0)
                print_info "退出"
                exit 0
                ;;
            *)
                print_error "无效选择，请重新输入"
                ;;
        esac
    done
}

# 执行主函数
main "$@"
