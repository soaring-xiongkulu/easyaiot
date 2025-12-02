#!/bin/bash

# DEVICE模块 Docker Compose 管理脚本
# 用于管理DEVICE目录下的所有Docker服务

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

# 检查并修复文件权限
fix_file_permissions() {
    local file_path="$1"
    local min_perms="$2"
    
    if [ ! -e "$file_path" ]; then
        return 1
    fi
    
    # 获取当前权限
    local current_perms=$(stat -c "%a" "$file_path" 2>/dev/null || echo "000")
    
    # 检查权限是否足够
    if [ "$current_perms" -lt "$min_perms" ] 2>/dev/null; then
        print_info "修复文件权限: $file_path (当前: $current_perms, 需要: $min_perms)"
        if [ "$EUID" -eq 0 ]; then
            chmod "$min_perms" "$file_path" 2>/dev/null || return 1
        elif command -v sudo &> /dev/null; then
            sudo chmod "$min_perms" "$file_path" 2>/dev/null || return 1
        else
            print_warning "无法修复权限，请手动执行: chmod $min_perms $file_path"
            return 1
        fi
    fi
    
    return 0
}

# 检查并修复目录权限
fix_directory_permissions() {
    local dir_path="$1"
    local min_perms="$2"
    
    if [ ! -d "$dir_path" ]; then
        return 1
    fi
    
    # 获取当前权限
    local current_perms=$(stat -c "%a" "$dir_path" 2>/dev/null || echo "000")
    
    # 检查权限是否足够
    if [ "$current_perms" -lt "$min_perms" ] 2>/dev/null; then
        print_info "修复目录权限: $dir_path (当前: $current_perms, 需要: $min_perms)"
        if [ "$EUID" -eq 0 ]; then
            chmod "$min_perms" "$dir_path" 2>/dev/null || return 1
        elif command -v sudo &> /dev/null; then
            sudo chmod "$min_perms" "$dir_path" 2>/dev/null || return 1
        else
            print_warning "无法修复权限，请手动执行: chmod $min_perms $dir_path"
            return 1
        fi
    fi
    
    return 0
}

# 检查docker-compose.yml是否存在并修复权限
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yml文件不存在: $COMPOSE_FILE"
        exit 1
    fi
    
    # 检查并修复文件权限（至少需要 644，Docker 需要读取）
    if ! fix_file_permissions "$COMPOSE_FILE" "644"; then
        print_warning "无法自动修复 docker-compose.yml 权限，尝试手动修复..."
        # 尝试使用更宽松的权限
        if [ "$EUID" -eq 0 ]; then
            chmod 644 "$COMPOSE_FILE" 2>/dev/null || chmod 755 "$COMPOSE_FILE" 2>/dev/null || true
        elif command -v sudo &> /dev/null; then
            sudo chmod 644 "$COMPOSE_FILE" 2>/dev/null || sudo chmod 755 "$COMPOSE_FILE" 2>/dev/null || true
        fi
    fi
    
    # 检查并修复脚本目录权限（至少需要 755）
    if ! fix_directory_permissions "$SCRIPT_DIR" "755"; then
        print_warning "无法自动修复脚本目录权限，尝试手动修复..."
        if [ "$EUID" -eq 0 ]; then
            chmod 755 "$SCRIPT_DIR" 2>/dev/null || true
        elif command -v sudo &> /dev/null; then
            sudo chmod 755 "$SCRIPT_DIR" 2>/dev/null || true
        fi
    fi
    
    # 验证文件是否可读
    if [ ! -r "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yml 文件不可读: $COMPOSE_FILE"
        print_error "当前权限: $(stat -c "%a %U:%G" "$COMPOSE_FILE" 2>/dev/null || echo "未知")"
        print_error "请手动修复权限: chmod 644 $COMPOSE_FILE"
        exit 1
    fi
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# WEB目录路径
WEB_DIR="${SCRIPT_DIR}/../WEB"

# 创建WEB必要的目录
create_web_directories() {
    print_info "创建WEB必要的目录..."
    mkdir -p "${WEB_DIR}/conf"
    mkdir -p "${WEB_DIR}/logs"
    mkdir -p "${WEB_DIR}/conf/ssl"
    mkdir -p "${WEB_DIR}/dist"
    print_success "WEB目录创建完成"
}

# 检查前端构建产物
check_web_dist() {
    if [ ! -d "${WEB_DIR}/dist" ] || [ -z "$(ls -A ${WEB_DIR}/dist 2>/dev/null)" ]; then
        print_warning "WEB/dist 目录不存在或为空，需要先构建前端项目"
        print_info "运行: $0 build-frontend"
        return 1
    fi
    return 0
}

# 构建前端项目
build_frontend() {
    print_info "开始构建前端项目..."
    
    if [ ! -d "$WEB_DIR" ]; then
        print_error "WEB目录不存在: $WEB_DIR"
        exit 1
    fi
    
    cd "$WEB_DIR"
    
    # 检查 Node.js 和 pnpm
    if ! check_command node; then
        print_error "Node.js 未安装，请先安装 Node.js"
        echo "安装指南: https://nodejs.org/"
        exit 1
    fi
    
    if ! check_command pnpm; then
        print_warning "pnpm 未安装，尝试使用 npm..."
        if ! check_command npm; then
            print_error "npm 未安装，请先安装 Node.js"
            exit 1
        fi
        PACKAGE_MANAGER="npm"
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
    cd "$SCRIPT_DIR"
}

# 检查并构建Jar包（已废弃，现在在Docker容器中编译）
check_and_build_jars() {
    print_info "跳过宿主机Jar包检查（编译将在Docker容器中完成）..."
    # 不再需要在宿主机上编译，所有编译都在Docker容器中完成
}

# 构建所有镜像
build_images() {
    print_info "开始构建所有Docker镜像（在容器中编译，显示完整日志）..."
    
    # 确保权限正确
    check_compose_file
    
    cd "$SCRIPT_DIR"
    # 使用 --progress=plain 显示完整输出
    # 注意：编译将在Docker容器中完成，不需要宿主机Maven环境
    
    # 直接执行命令并实时输出
    local exit_code
    
    # 执行构建命令（不使用 --progress，兼容所有版本）
    $DOCKER_COMPOSE build
    exit_code=$?
    
    # 检查命令是否成功
    if [ $exit_code -ne 0 ]; then
        print_error "镜像构建失败（退出码: $exit_code）"
        exit 1
    fi
    
    print_success "镜像构建完成（所有编译在容器中完成）"
}

# 构建并启动所有服务
build_and_start() {
    print_info "开始构建并启动所有服务（在容器中编译，显示完整日志）..."
    
    # 确保权限正确
    check_compose_file
    
    cd "$SCRIPT_DIR"
    
    # 验证 Docker 可以访问 docker-compose.yml
    if ! $DOCKER_COMPOSE config > /dev/null 2>&1; then
        print_error "Docker Compose 无法读取配置文件"
        print_error "文件路径: $COMPOSE_FILE"
        print_error "文件权限: $(stat -c "%a %U:%G" "$COMPOSE_FILE" 2>/dev/null || echo "未知")"
        print_error "目录权限: $(stat -c "%a %U:%G" "$SCRIPT_DIR" 2>/dev/null || echo "未知")"
        print_info "尝试修复权限..."
        
        # 尝试修复权限
        if [ "$EUID" -eq 0 ]; then
            chmod 644 "$COMPOSE_FILE" 2>/dev/null || true
            chmod 755 "$SCRIPT_DIR" 2>/dev/null || true
        elif command -v sudo &> /dev/null; then
            sudo chmod 644 "$COMPOSE_FILE" 2>/dev/null || true
            sudo chmod 755 "$SCRIPT_DIR" 2>/dev/null || true
        fi
        
        # 再次验证
        if ! $DOCKER_COMPOSE config > /dev/null 2>&1; then
            print_error "权限修复后仍无法读取配置文件"
            print_error "请手动检查并修复权限:"
            print_error "  chmod 644 $COMPOSE_FILE"
            print_error "  chmod 755 $SCRIPT_DIR"
            exit 1
        else
            print_success "权限已修复，可以继续"
        fi
    fi
    
    # 使用 --progress=plain 显示完整输出
    # 注意：编译将在Docker容器中完成，不需要宿主机Maven环境
    
    # 直接执行命令并实时输出
    local exit_code
    
    # 执行构建和启动命令（不使用 --progress，兼容所有版本）
    $DOCKER_COMPOSE up -d --build
    exit_code=$?
    
    # 检查命令是否成功
    if [ $exit_code -ne 0 ]; then
        print_error "服务构建或启动失败（退出码: $exit_code）"
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
    
    print_success "服务构建并启动完成（所有编译在容器中完成，共 $container_count 个容器）"
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
    print_info "更新所有服务（在容器中重新构建并重启，显示完整日志）..."
    
    # 确保权限正确
    check_compose_file
    
    cd "$SCRIPT_DIR"
    # 使用 --progress=plain 显示完整输出
    # 注意：编译将在Docker容器中完成，不需要宿主机Maven环境
    
    # 直接执行命令并实时输出
    local exit_code
    
    # 执行更新命令（不使用 --progress，兼容所有版本）
    $DOCKER_COMPOSE up -d --build --force-recreate
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
    
    print_success "服务更新完成（所有编译在容器中完成，共 $container_count 个容器）"
}

# 显示帮助信息
show_help() {
    cat << EOF
DEVICE模块 Docker Compose 管理脚本

用法: $0 [命令] [选项]

命令:
    build               构建所有Docker镜像（在容器中编译，无需宿主机Maven）
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
    update              更新服务（在容器中重新构建并重启）
    install             安装（构建并启动所有服务，在容器中编译）
    help                显示此帮助信息

示例:
    $0 install                    # 构建并启动所有服务
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
        echo "2) 启动所有服务"
        echo "3) 停止所有服务"
        echo "4) 重启所有服务"
        echo "5) 查看服务状态"
        echo "6) 查看日志（所有服务）"
        echo "7) 查看日志（指定服务）"
        echo "8) 重启指定服务"
        echo "9) 停止指定服务"
        echo "10) 启动指定服务"
        echo "11) 更新服务（重新构建并重启）"
        echo "12) 清理（删除容器，保留镜像）"
        echo "13) 完全清理（删除容器和镜像）"
        echo "0) 退出"
        echo
        read -p "请选择操作 [0-13]: " choice
        
        case $choice in
            1)
                build_and_start
                ;;
            2)
                start_services
                ;;
            3)
                stop_services
                ;;
            4)
                restart_services
                ;;
            5)
                show_status
                ;;
            6)
                show_logs
                ;;
            7)
                echo "可用服务:"
                cd "$SCRIPT_DIR"
                $DOCKER_COMPOSE config --services
                read -p "请输入服务名称: " service_name
                show_logs "$service_name"
                ;;
            8)
                echo "可用服务:"
                cd "$SCRIPT_DIR"
                $DOCKER_COMPOSE config --services
                read -p "请输入服务名称: " service_name
                restart_service "$service_name"
                ;;
            9)
                echo "可用服务:"
                cd "$SCRIPT_DIR"
                $DOCKER_COMPOSE config --services
                read -p "请输入服务名称: " service_name
                stop_service "$service_name"
                ;;
            10)
                echo "可用服务:"
                cd "$SCRIPT_DIR"
                $DOCKER_COMPOSE config --services
                read -p "请输入服务名称: " service_name
                start_service "$service_name"
                ;;
            11)
                update_services
                ;;
            12)
                clean
                ;;
            13)
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

