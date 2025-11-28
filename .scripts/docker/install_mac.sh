#!/bin/bash

# ============================================
# EasyAIoT 统一安装脚本 (macOS 版本)
# ============================================
# 使用方法：
#   ./install_mac.sh [命令]
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

# 确保使用 bash 执行此脚本
if [ -z "$BASH_VERSION" ]; then
    # 如果当前 shell 不是 bash，使用 bash 重新执行
    if command -v bash &> /dev/null; then
        exec bash "$0" "$@"
    else
        echo "错误: 需要 bash 环境，但未找到 bash 命令" >&2
        exit 1
    fi
fi

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录（从.scripts/docker回到项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 日志文件配置
LOG_DIR="${SCRIPT_DIR}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/install_mac_$(date +%Y%m%d_%H%M%S).log"

# 初始化日志文件
echo "=========================================" >> "$LOG_FILE"
echo "EasyAIoT 统一安装脚本日志 (macOS)" >> "$LOG_FILE"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "命令: $*" >> "$LOG_FILE"
echo "=========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 模块列表（按依赖顺序）
MODULES=(
    ".scripts/docker"  # 基础服务（Nacos、PostgreSQL、Redis等）
    "DEVICE"           # Device服务（网关和微服务）
     "AI"               # AI服务
     "VIDEO"            # Video服务
    "WEB"              # Web前端服务
)

# 模块信息（使用函数兼容 bash 3.2）
get_module_name() {
    case "$1" in
        ".scripts/docker") echo "基础服务" ;;
        "DEVICE") echo "Device服务" ;;
         "AI") echo "AI服务" ;;
         "VIDEO") echo "Video服务" ;;
        "WEB") echo "Web前端服务" ;;
        *) echo "$1" ;;
    esac
}

get_module_port() {
    case "$1" in
        ".scripts/docker") echo "8848" ;;
        "DEVICE") echo "48080" ;;
        "AI") echo "5000" ;;
        "VIDEO") echo "6000" ;;
        "WEB") echo "8888" ;;
        *) echo "" ;;
    esac
}

get_module_health() {
    case "$1" in
        ".scripts/docker") echo "/nacos/actuator/health" ;;
        "DEVICE") echo "/actuator/health" ;;
        "AI") echo "/actuator/health" ;;
        "VIDEO") echo "/actuator/health" ;;
        "WEB") echo "/health" ;;
        *) echo "" ;;
    esac
}

# 日志输出函数（去掉颜色代码后写入日志文件）
log_to_file() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    # 去掉 ANSI 颜色代码（macOS 使用 BSD sed，需要不同的语法）
    local clean_message=$(echo "$message" | sed -E "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[mGK]//g")
    echo "[$timestamp] $clean_message" >> "$LOG_FILE"
}

# 打印带颜色的消息（同时输出到日志文件）
print_info() {
    local message="${BLUE}[INFO]${NC} $1"
    echo -e "$message"
    log_to_file "[INFO] $1"
}

print_success() {
    local message="${GREEN}[SUCCESS]${NC} $1"
    echo -e "$message"
    log_to_file "[SUCCESS] $1"
}

print_warning() {
    local message="${YELLOW}[WARNING]${NC} $1"
    echo -e "$message"
    log_to_file "[WARNING] $1"
}

print_error() {
    local message="${RED}[ERROR]${NC} $1"
    echo -e "$message"
    log_to_file "[ERROR] $1"
}

print_section() {
    local section="$1"
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  $section${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    log_to_file ""
    log_to_file "========================================="
    log_to_file "  $section"
    log_to_file "========================================="
    log_to_file ""
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

# 检查 Docker 权限（macOS 版本）
check_docker_permission() {
    # 首先检查 Docker daemon 是否运行
    if ! docker info &> /dev/null; then
        # 检查是否是权限问题还是 daemon 未运行
        local error_msg=$(docker info 2>&1)
        
        if echo "$error_msg" | grep -qi "permission denied\|cannot connect"; then
            print_error "没有权限访问 Docker daemon"
            echo ""
            echo "解决方案："
            echo "  1. 确保 Docker Desktop 正在运行"
            echo "  2. 打开 Docker Desktop 应用程序"
            echo "  3. 等待 Docker Desktop 完全启动后再运行此脚本"
            echo ""
        elif echo "$error_msg" | grep -qi "Is the docker daemon running"; then
            print_error "Docker daemon 未运行"
            echo ""
            echo "解决方案："
            echo "  1. 打开 Docker Desktop 应用程序"
            echo "  2. 等待 Docker Desktop 完全启动（状态栏图标显示为运行中）"
            echo "  3. 如果 Docker Desktop 未安装，请访问: https://www.docker.com/products/docker-desktop"
            echo ""
        else
            print_error "无法连接到 Docker daemon"
            echo ""
            echo "错误信息: $error_msg"
            echo ""
            echo "请检查："
            echo "  1. Docker Desktop 是否已安装并正在运行"
            echo "  2. 尝试重启 Docker Desktop"
            echo "  3. 如果问题持续，请重新安装 Docker Desktop"
            echo ""
        fi
        exit 1
    fi
    
    # 验证 docker ps 命令是否可用
    if ! docker ps &> /dev/null; then
        print_error "Docker 命令执行失败"
        exit 1
    fi
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
    print_success "Docker 已安装: $(docker --version)"
    check_docker_permission "$@"
}

# 检查 Docker Compose 是否安装
check_docker_compose() {
    local version_output=""
    
    # 检查 docker-compose (v1)
    if check_command docker-compose; then
        COMPOSE_CMD="docker-compose"
        version_output=$(docker-compose --version 2>/dev/null || echo "")
        if [ -n "$version_output" ]; then
            print_success "Docker Compose 已安装: $version_output"
            return 0
        fi
    fi
    
    # 检查 docker compose (v2)
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        # 尝试多种方式获取版本信息
        version_output=$(docker compose version --short 2>/dev/null || echo "")
        
        if [ -z "$version_output" ]; then
            version_output=$(docker compose version 2>&1 | grep -E "version|Docker Compose" | head -1 | sed 's/^[[:space:]]*//' || echo "")
        fi
        
        if [ -z "$version_output" ] || echo "$version_output" | grep -qiE "usage|command|options"; then
            version_output=$(docker compose --version 2>/dev/null || docker compose version 2>&1 | head -1 || echo "")
            if echo "$version_output" | grep -qiE "usage|command|options"; then
                print_success "Docker Compose 已安装 (docker compose 命令可用)"
            else
                print_success "Docker Compose 已安装: $version_output"
            fi
        else
            print_success "Docker Compose 已安装: $version_output"
        fi
        return 0
    fi
    
    # 如果都不存在，报错
    print_error "Docker Compose 未安装，请先安装 Docker Compose"
    echo "Docker Desktop for Mac 已包含 Docker Compose，请确保 Docker Desktop 已正确安装"
    echo "安装指南: https://docs.docker.com/compose/install/"
    exit 1
}

# 创建统一网络
create_network() {
    print_info "创建统一网络 easyaiot-network..."
    if docker network inspect easyaiot-network >/dev/null 2>&1; then
        print_info "网络 easyaiot-network 已存在"
        return
    fi

    if docker network create easyaiot-network >/dev/null 2>&1; then
        print_success "网络 easyaiot-network 已创建"
    else
        print_error "无法创建网络 easyaiot-network"
        exit 1
    fi
}

# 修复脚本文件的换行符（Windows CRLF -> Unix LF）
fix_line_endings() {
    local script_file="$1"
    if [ ! -f "$script_file" ]; then
        return 1
    fi
    
    # 检查文件是否包含 \r 字符（macOS 使用 BSD sed）
    if grep -q $'\r' "$script_file" 2>/dev/null; then
        print_info "修复 $script_file 的换行符（CRLF -> LF）..."
        # macOS 使用 BSD sed，需要指定备份扩展名或使用空字符串
        if sed -i '' 's/\r$//' "$script_file" 2>/dev/null; then
            :
        else
            # 如果 sed -i 失败，使用临时文件
            local temp_file=$(mktemp)
            if sed 's/\r$//' "$script_file" > "$temp_file" 2>/dev/null; then
                mv "$temp_file" "$script_file"
            else
                rm -f "$temp_file"
                # 如果 sed 也失败，尝试使用 tr
                tr -d '\r' < "$script_file" > "$temp_file" 2>/dev/null && mv "$temp_file" "$script_file" || rm -f "$temp_file"
            fi
        fi
        # 确保文件有执行权限
        chmod +x "$script_file" 2>/dev/null || true
    fi
}

# 执行模块命令
execute_module_command() {
    local module=$1
    local command=$2
    local module_name=$(get_module_name "$module")
    
    if [ ! -d "$PROJECT_ROOT/$module" ]; then
        print_warning "模块 $module 不存在，跳过"
        return 1
    fi
    
    cd "$PROJECT_ROOT/$module"
    
    # 特殊处理.scripts/docker模块（使用install_middleware_mac.sh脚本）
    if [ "$module" = ".scripts/docker" ]; then
        # 检查install_middleware_mac.sh文件
        local install_file="install_middleware_mac.sh"
        if [ ! -f "$install_file" ]; then
            print_warning "模块 $module 没有 $install_file 文件，跳过"
            return 1
        fi
        
        # 修复换行符
        fix_line_endings "$install_file"
        
        print_info "执行 $module_name: $command"
        
        if bash "$install_file" "$command" 2>&1 | tee -a "$LOG_FILE"; then
            print_success "$module_name: $command 执行成功"
            return 0
        else
            print_error "$module_name: $command 执行失败"
            return 1
        fi
    # 特殊处理DEVICE模块（使用docker-compose.yml）
    elif [ "$module" = "DEVICE" ]; then
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
                if $compose_cmd -f "$compose_file" up -d 2>&1 | tee -a "$LOG_FILE"; then
                    print_success "$module_name: $command 执行成功"
                    return 0
                else
                    print_error "$module_name: $command 执行失败"
                    return 1
                fi
                ;;
            stop)
                if $compose_cmd -f "$compose_file" down 2>&1 | tee -a "$LOG_FILE"; then
                    print_success "$module_name: $command 执行成功"
                    return 0
                else
                    print_error "$module_name: $command 执行失败"
                    return 1
                fi
                ;;
            restart)
                if $compose_cmd -f "$compose_file" restart 2>&1 | tee -a "$LOG_FILE"; then
                    print_success "$module_name: $command 执行成功"
                    return 0
                else
                    print_error "$module_name: $command 执行失败"
                    return 1
                fi
                ;;
            status)
                $compose_cmd -f "$compose_file" ps 2>&1 | tee -a "$LOG_FILE"
                return $?
                ;;
            logs)
                $compose_cmd -f "$compose_file" logs --tail=100 2>&1 | tee -a "$LOG_FILE"
                return $?
                ;;
            build)
                if $compose_cmd -f "$compose_file" build --no-cache 2>&1 | tee -a "$LOG_FILE"; then
                    print_success "$module_name: $command 执行成功"
                    return 0
                else
                    print_error "$module_name: $command 执行失败"
                    return 1
                fi
                ;;
            clean)
                if $compose_cmd -f "$compose_file" down -v 2>&1 | tee -a "$LOG_FILE"; then
                    print_success "$module_name: $command 执行成功"
                    return 0
                else
                    print_error "$module_name: $command 执行失败"
                    return 1
                fi
                ;;
            update)
                if ($compose_cmd -f "$compose_file" pull && $compose_cmd -f "$compose_file" up -d) 2>&1 | tee -a "$LOG_FILE"; then
                    print_success "$module_name: $command 执行成功"
                    return 0
                else
                    print_error "$module_name: $command 执行失败"
                    return 1
                fi
                ;;
            *)
                print_warning "未知命令: $command"
                return 1
                ;;
        esac
    else
        # 其他模块使用install_mac.sh脚本
        if [ ! -f "install_mac.sh" ]; then
            # 如果 install_mac.sh 不存在，尝试使用 install_linux.sh（向后兼容）
            if [ -f "install_linux.sh" ]; then
                print_info "未找到 install_mac.sh，使用 install_linux.sh（向后兼容）"
                fix_line_endings "install_linux.sh"
                print_info "执行 $module_name: $command"
                if bash install_linux.sh "$command" 2>&1 | tee -a "$LOG_FILE"; then
                    print_success "$module_name: $command 执行成功"
                    return 0
                else
                    print_error "$module_name: $command 执行失败"
                    return 1
                fi
            else
                print_warning "模块 $module 没有 install_mac.sh 或 install_linux.sh 脚本，跳过"
                return 1
            fi
        fi
        
        # 修复换行符
        fix_line_endings "install_mac.sh"
        
        print_info "执行 $module_name: $command"
        
        if bash install_mac.sh "$command" 2>&1 | tee -a "$LOG_FILE"; then
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
    local module_name=$(get_module_name "$module")
    local port=$(get_module_port "$module")
    local health_endpoint=$(get_module_health "$module")
    
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
install_mac() {
    print_section "开始安装所有服务"
    
    check_macos
    check_docker "$@"
    check_docker_compose
    create_network
    
    local success_count=0
    local total_count=${#MODULES[@]}
    
    for module in "${MODULES[@]}"; do
        print_section "安装 $(get_module_name "$module")"
        if execute_module_command "$module" "install"; then
            success_count=$((success_count + 1))
        else
            print_error "$(get_module_name "$module") 安装失败"
        fi
        echo ""
    done
    
    print_section "安装完成"
    echo "成功安装: $success_count / $total_count 个模块"
    
    if [ $success_count -eq $total_count ]; then
        print_success "所有模块安装成功！"
    else
        print_warning "部分模块安装失败，请检查日志"
        exit 1
    fi
}

# 等待基础服务就绪
wait_for_base_services() {
    print_info "等待基础服务就绪..."
    
    # 等待 PostgreSQL
    if docker ps --filter "name=postgres-server" --format "{{.Names}}" | grep -q "postgres-server"; then
        print_info "等待 PostgreSQL 服务就绪..."
        local max_attempts=60
        local attempt=0
        while [ $attempt -lt $max_attempts ]; do
            if docker exec postgres-server pg_isready -U postgres > /dev/null 2>&1; then
                print_success "PostgreSQL 服务已就绪"
                break
            fi
            attempt=$((attempt + 1))
            sleep 2
        done
        if [ $attempt -ge $max_attempts ]; then
            print_warning "PostgreSQL 服务未在预期时间内就绪，继续执行..."
        fi
    fi
    
    # 等待 Nacos
    if docker ps --filter "name=nacos-server" --format "{{.Names}}" | grep -q "nacos-server"; then
        print_info "等待 Nacos 服务就绪..."
        local max_attempts=60
        local attempt=0
        while [ $attempt -lt $max_attempts ]; do
            if curl -s --connect-timeout 2 "http://localhost:8848/nacos/actuator/health" > /dev/null 2>&1; then
                print_success "Nacos 服务已就绪"
                break
            fi
            attempt=$((attempt + 1))
            sleep 2
        done
        if [ $attempt -ge $max_attempts ]; then
            print_warning "Nacos 服务未在预期时间内就绪，继续执行..."
        fi
    fi
    
    # 等待 Redis
    if docker ps --filter "name=redis-server" --format "{{.Names}}" | grep -q "redis-server"; then
        print_info "等待 Redis 服务就绪..."
        local max_attempts=30
        local attempt=0
        while [ $attempt -lt $max_attempts ]; do
            if docker exec redis-server redis-cli ping > /dev/null 2>&1; then
                print_success "Redis 服务已就绪"
                break
            fi
            attempt=$((attempt + 1))
            sleep 1
        done
        if [ $attempt -ge $max_attempts ]; then
            print_warning "Redis 服务未在预期时间内就绪，继续执行..."
        fi
    fi
}

# 启动所有服务
start_all() {
    print_section "启动所有服务"
    
    check_macos
    check_docker "$@"
    check_docker_compose
    create_network
    
    # 先启动基础服务（.scripts/docker）
    print_section "启动基础服务"
    execute_module_command ".scripts/docker" "start"
    echo ""
    
    # 等待基础服务就绪
    wait_for_base_services
    echo ""
    
    # 再启动其他服务
    for module in "${MODULES[@]}"; do
        # 跳过基础服务（已经启动）
        if [ "$module" = ".scripts/docker" ]; then
            continue
        fi
        execute_module_command "$module" "start"
        echo ""
    done
    
    print_success "所有服务启动完成"
}

# 停止所有服务
stop_all() {
    print_section "停止所有服务"
    
    check_macos
    check_docker "$@"
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
    
    check_macos
    check_docker "$@"
    check_docker_compose
    create_network
    
    for module in "${MODULES[@]}"; do
        execute_module_command "$module" "restart"
        echo ""
    done
    
    print_success "所有服务重启完成"
}

# 查看所有服务状态
status_all() {
    print_section "所有服务状态"
    
    check_macos
    check_docker "$@"
    check_docker_compose
    
    for module in "${MODULES[@]}"; do
        print_section "$(get_module_name "$module") 状态"
        execute_module_command "$module" "status"
        echo ""
    done
}

# 查看日志
view_logs() {
    local module=${1:-""}
    
    if [ -z "$module" ]; then
        print_info "查看所有服务日志..."
        check_macos
        check_docker "$@"
        check_docker_compose
        
        for module in "${MODULES[@]}"; do
            print_section "$(get_module_name "$module") 日志"
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
    
    check_macos
    check_docker "$@"
    check_docker_compose
    
    for module in "${MODULES[@]}"; do
        execute_module_command "$module" "build"
        echo ""
    done
    
    print_success "所有镜像构建完成"
}

# 检查并重新加载环境变量（macOS 版本）
reload_environment() {
    # macOS 使用 ~/.zshrc 或 ~/.bash_profile
    local profile_files=("$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.bashrc")
    local profile_file=""
    
    # 查找存在的配置文件
    for file in "${profile_files[@]}"; do
        if [ -f "$file" ]; then
            profile_file="$file"
            break
        fi
    done
    
    # 如果都不存在，检查是否有 JAVA_HOME 环境变量
    if [ -z "$profile_file" ]; then
        if [ -n "$JAVA_HOME" ]; then
            print_info "检测到 JAVA_HOME 环境变量: $JAVA_HOME"
            return 0
        fi
        print_info "未找到环境变量配置文件，跳过环境变量加载"
        return 0
    fi
    
    if ! grep -q "JAVA_HOME\|JRE_HOME" "$profile_file" 2>/dev/null; then
        print_info "$profile_file 中未找到 JAVA_HOME 或 JRE_HOME 配置"
        return 0
    fi
    
    print_info "检测到 $profile_file 中有环境变量配置，正在重新加载..."
    
    # 直接 source 配置文件
    local error_file=$(mktemp)
    if source "$profile_file" > "$error_file" 2>&1; then
        rm -f "$error_file"
        print_success "环境变量已重新加载"
        
        # 验证 JAVA_HOME 是否已设置
        if [ -n "$JAVA_HOME" ]; then
            print_info "JAVA_HOME: $JAVA_HOME"
            # 验证 java 命令是否可用
            if command -v java &> /dev/null; then
                local java_version=$(java -version 2>&1 | head -n 1)
                print_info "Java 版本: $java_version"
            fi
            return 0
        else
            print_warning "JAVA_HOME 未设置，可能环境变量配置有问题"
            print_info "请检查 $profile_file 中的 JAVA_HOME 配置"
            return 1
        fi
    else
        local source_error=$(cat "$error_file" 2>/dev/null || echo "")
        rm -f "$error_file"
        print_warning "source $profile_file 执行失败"
        if [ -n "$source_error" ]; then
            print_info "错误信息: $source_error"
        fi
        print_info "请手动执行: source $profile_file"
        return 1
    fi
}

# 清理所有服务
clean_all() {
    print_warning "这将删除所有容器、镜像和数据卷，确定要继续吗？(y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_section "清理所有服务"
        
        check_macos
        check_docker "$@"
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
        
        # 清理完成后，自动检查并重新加载环境变量
        echo ""
        reload_environment
    else
        print_info "已取消清理操作"
    fi
}

# 更新所有服务
update_all() {
    print_section "更新所有服务"
    
    check_macos
    check_docker "$@"
    check_docker_compose
    create_network
    
    for module in "${MODULES[@]}"; do
        execute_module_command "$module" "update"
        echo ""
    done
    
    print_success "所有服务更新完成"
}

# 验证所有服务
verify_all() {
    print_section "验证所有服务"
    
    check_macos
    check_docker "$@"
    
    local success_count=0
    local total_count=${#MODULES[@]}
    local failed_modules=()
    
    for module in "${MODULES[@]}"; do
        if verify_service_health "$module"; then
            success_count=$((success_count + 1))
        else
            failed_modules+=("$(get_module_name "$module")")
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
        echo -e "  基础服务 (MinIO):     http://localhost:9000 (API), http://localhost:9001 (Console)"
        echo -e "  Device服务 (Gateway):  http://localhost:48080"
        echo -e "  AI服务:                http://localhost:5000"
        echo -e "  Video服务:             http://localhost:6000"
        echo -e "  Web前端:               http://localhost:8888"
        echo ""
        return 0
    else
        print_warning "部分服务未就绪:"
        for failed in "${failed_modules[@]}"; do
            echo -e "  ${RED}✗ $failed${NC}"
        done
        echo ""
        print_info "查看日志: ./install_mac.sh logs"
        return 1
    fi
}

# 显示帮助信息
show_help() {
    echo "EasyAIoT 统一安装脚本 (macOS 版本)"
    echo ""
    echo "使用方法:"
    echo "  ./install_mac.sh [命令] [模块]"
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
        echo "  - $(get_module_name "$module") ($module)"
    done
    echo ""
    echo "注意："
    echo "  - 此脚本需要 Docker Desktop for Mac"
    echo "  - 请确保 Docker Desktop 已安装并正在运行"
    echo ""
}

# 主函数
main() {
    # 在执行任何命令之前（除了 help），先检查系统并尝试加载环境变量
    if [ "${1:-help}" != "help" ] && [ "${1:-help}" != "--help" ] && [ "${1:-help}" != "-h" ]; then
        check_macos
        reload_environment
    fi
    
    case "${1:-help}" in
        install)
            install_mac
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

# 脚本结束时记录日志文件路径
if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
    echo "" >> "$LOG_FILE"
    echo "=========================================" >> "$LOG_FILE"
    echo "脚本结束时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
    echo "=========================================" >> "$LOG_FILE"
    echo ""
    print_info "日志文件已保存到: $LOG_FILE"
fi

