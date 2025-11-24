#!/bin/bash

# ============================================
# EasyAIoT 统一安装脚本
# ============================================
# 使用方法：
#   ./install_linux.sh [命令]
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
#   check      - 检查 Docker 和 Docker Compose 安装状态
# ============================================

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
LOG_FILE="${LOG_DIR}/install_linux_$(date +%Y%m%d_%H%M%S).log"

# 初始化日志文件
echo "=========================================" >> "$LOG_FILE"
echo "EasyAIoT 统一安装脚本日志" >> "$LOG_FILE"
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
MODULE_PORTS["WEB"]="8888"

# 模块健康检查端点
declare -A MODULE_HEALTH_ENDPOINTS
MODULE_HEALTH_ENDPOINTS[".scripts/docker"]="/nacos/actuator/health"
MODULE_HEALTH_ENDPOINTS["DEVICE"]="/actuator/health"  # Gateway健康检查
MODULE_HEALTH_ENDPOINTS["AI"]="/actuator/health"
MODULE_HEALTH_ENDPOINTS["VIDEO"]="/actuator/health"
MODULE_HEALTH_ENDPOINTS["WEB"]="/health"

# 日志输出函数（去掉颜色代码后写入日志文件）
log_to_file() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    # 去掉 ANSI 颜色代码
    local clean_message=$(echo "$message" | sed -r "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[mGK]//g")
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

# 检查 Docker 权限
check_docker_permission() {
    # 首先检查 Docker daemon 是否运行
    if ! docker info &> /dev/null; then
        # 检查是否是权限问题还是 daemon 未运行
        local error_msg=$(docker info 2>&1)
        
        if echo "$error_msg" | grep -qi "permission denied\|cannot connect"; then
            print_error "没有权限访问 Docker daemon"
            echo ""
            echo "解决方案："
            echo "  1. 将当前用户添加到 docker 组："
            echo "     sudo usermod -aG docker $USER"
            echo "     然后重新登录或运行: newgrp docker"
            echo ""
            echo "  2. 或者使用 sudo 运行此脚本："
            echo "     sudo ./install_linux.sh $*"
            echo ""
        elif echo "$error_msg" | grep -qi "Is the docker daemon running"; then
            print_error "Docker daemon 未运行"
            echo ""
            
            # 检查是否是 systemd 超时问题
            if systemctl is-active docker.service &> /dev/null; then
                print_info "Docker 服务状态: $(systemctl is-active docker.service)"
            elif systemctl is-failed docker.service &> /dev/null && systemctl is-failed docker.service | grep -qi "failed\|timeout"; then
                print_warning "检测到 Docker 服务启动失败或超时"
                echo ""
                echo "这可能是 systemd 超时问题，请运行诊断脚本："
                echo "  sudo .scripts/docker/diagnose_docker_systemd.sh diagnose"
                echo ""
                echo "然后尝试修复："
                echo "  sudo .scripts/docker/diagnose_docker_systemd.sh fix-all"
                echo ""
            fi
            
            echo "解决方案："
            echo "  1. 启动 Docker 服务："
            echo "     sudo systemctl start docker"
            echo ""
            echo "  2. 如果启动失败，运行诊断脚本："
            echo "     sudo .scripts/docker/diagnose_docker_systemd.sh diagnose"
            echo ""
            echo "  3. 尝试修复 systemd 超时问题："
            echo "     sudo .scripts/docker/diagnose_docker_systemd.sh fix-all"
            echo ""
            echo "  4. 设置 Docker 服务开机自启："
            echo "     sudo systemctl enable docker"
            echo ""
        else
            print_error "无法连接到 Docker daemon"
            echo ""
            echo "错误信息: $error_msg"
            echo ""
            echo "请检查："
            echo "  1. Docker 服务是否运行: sudo systemctl status docker"
            echo "  2. 如果服务启动失败，运行诊断脚本："
            echo "     sudo .scripts/docker/diagnose_docker_systemd.sh diagnose"
            echo "  3. 当前用户是否有权限访问 Docker"
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
    print_info "检查 Docker 安装状态..."
    
    # 检查命令是否存在
    if ! check_command docker; then
        print_error "Docker 未安装"
        echo ""
        echo "安装方法："
        echo "  Ubuntu/Debian:"
        echo "    curl -fsSL https://get.docker.com -o get-docker.sh"
        echo "    sudo sh get-docker.sh"
        echo ""
        echo "  CentOS/RHEL:"
        echo "    sudo yum install -y docker"
        echo "    sudo systemctl start docker"
        echo "    sudo systemctl enable docker"
        echo ""
        echo "  更多安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # 获取 Docker 版本信息
    local docker_version=$(docker --version 2>/dev/null || echo "未知版本")
    print_success "Docker 已安装: $docker_version"
    
    # 检查 Docker 服务状态
    if systemctl is-active --quiet docker.service 2>/dev/null; then
        print_info "Docker 服务状态: 运行中"
    elif systemctl is-enabled --quiet docker.service 2>/dev/null; then
        print_warning "Docker 服务已启用但未运行"
    else
        print_warning "Docker 服务未启用"
    fi
    
    # 检查权限和 daemon 状态
    check_docker_permission "$@"
}

# 检查 Docker Compose 是否安装
check_docker_compose() {
    print_info "检查 Docker Compose 安装状态..."
    
    local version_output=""
    local compose_found=false
    
    # 检查 docker-compose (v1)
    if check_command docker-compose; then
        COMPOSE_CMD="docker-compose"
        version_output=$(docker-compose --version 2>/dev/null || echo "")
        if [ -n "$version_output" ]; then
            print_success "Docker Compose v1 已安装: $version_output"
            compose_found=true
        fi
    fi
    
    # 检查 docker compose (v2)
    if docker compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
        # 尝试多种方式获取版本信息
        # 方法1: 直接使用 version 命令（v2 的标准输出）
        version_output=$(docker compose version --short 2>/dev/null || echo "")
        
        # 方法2: 如果 --short 不可用，尝试解析完整输出
        if [ -z "$version_output" ]; then
            version_output=$(docker compose version 2>&1 | grep -E "version|Docker Compose" | head -1 | sed 's/^[[:space:]]*//' || echo "")
        fi
        
        # 方法3: 如果还是无法获取，检查是否是帮助信息
        if [ -z "$version_output" ] || echo "$version_output" | grep -qiE "usage|command|options"; then
            # 尝试使用 docker compose 的其他方式获取版本
            version_output=$(docker compose --version 2>/dev/null || docker compose version 2>&1 | head -1 || echo "")
            if echo "$version_output" | grep -qiE "usage|command|options"; then
                # 如果仍然是帮助信息，只显示命令可用
                print_success "Docker Compose v2 已安装 (docker compose 命令可用)"
            else
                print_success "Docker Compose v2 已安装: $version_output"
            fi
        else
            print_success "Docker Compose v2 已安装: $version_output"
        fi
        compose_found=true
    fi
    
    # 如果都不存在，报错
    if [ "$compose_found" = false ]; then
        print_error "Docker Compose 未安装"
        echo ""
        echo "安装方法："
        echo "  Docker Compose v2 (推荐，随 Docker Desktop 自动安装):"
        echo "    如果使用 Docker Desktop，Compose v2 已包含在内"
        echo ""
        echo "  Docker Compose v1 (独立安装):"
        echo "    sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose"
        echo "    sudo chmod +x /usr/local/bin/docker-compose"
        echo ""
        echo "  更多安装指南: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # 显示使用的命令
    print_info "使用命令: $COMPOSE_CMD"
}

# 创建统一网络
create_network() {
    print_info "创建统一网络 easyaiot-network..."
    
    # 检查网络是否已存在
    if docker network ls | grep -q easyaiot-network; then
        print_info "网络 easyaiot-network 已存在"
        
        # 检测网络是否可用（尝试创建一个临时容器测试）
        if ! docker run --rm --network easyaiot-network alpine:latest ping -c 1 8.8.8.8 > /dev/null 2>&1; then
            print_warning "检测到网络 easyaiot-network 可能存在问题（可能是IP变化导致）"
            print_info "正在尝试重新创建网络..."
            
            # 获取连接到该网络的所有容器
            local containers=$(docker network inspect easyaiot-network --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null || echo "")
            
            if [ -n "$containers" ]; then
                print_warning "以下容器正在使用该网络，需要先停止："
                echo "$containers" | tr ' ' '\n' | grep -v '^$' | while read -r container; do
                    echo "  - $container"
                done
                print_info "正在尝试断开这些容器与网络的连接..."
                
                # 尝试断开所有容器的网络连接
                echo "$containers" | tr ' ' '\n' | grep -v '^$' | while read -r container; do
                    if [ -n "$container" ]; then
                        print_info "断开容器 $container 与网络的连接..."
                        docker network disconnect -f easyaiot-network "$container" 2>/dev/null || true
                    fi
                done
                sleep 2
            fi
            
            # 删除旧网络
            print_info "删除旧网络..."
            if docker network rm easyaiot-network 2>&1; then
                print_success "旧网络已删除"
                sleep 1
            else
                local error_msg=$(docker network rm easyaiot-network 2>&1)
                print_warning "删除旧网络时出现问题: $error_msg"
                print_info "尝试强制删除..."
                # 如果普通删除失败，尝试查找并手动断开所有连接
                local network_id=$(docker network inspect easyaiot-network --format '{{.Id}}' 2>/dev/null || echo "")
                if [ -n "$network_id" ]; then
                    # 获取所有连接到该网络的容器ID
                    local container_ids=$(docker network inspect easyaiot-network --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null || echo "")
                    if [ -n "$container_ids" ]; then
                        echo "$container_ids" | tr ' ' '\n' | grep -v '^$' | while read -r container; do
                            docker network disconnect -f easyaiot-network "$container" 2>/dev/null || true
                        done
                        sleep 2
                        docker network rm easyaiot-network 2>/dev/null || true
                    fi
                fi
            fi
        else
            print_info "网络 easyaiot-network 运行正常"
            return 0
        fi
    fi
    
    # 创建网络（如果不存在或已删除）
    print_info "正在创建网络 easyaiot-network..."
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
            return 1
        elif echo "$create_output" | grep -qi "network with name.*already exists"; then
            print_warning "网络名称冲突，尝试使用不同的方法..."
            # 再次检查网络是否存在
            if docker network ls | grep -q easyaiot-network; then
                print_info "网络已存在，继续使用现有网络"
                return 0
            else
                print_error "无法创建网络: $create_output"
                return 1
            fi
        else
            print_error "无法创建网络 easyaiot-network"
            print_error "错误信息: $create_output"
            print_info "诊断建议："
            print_info "  1. 检查 Docker 服务是否正常运行: sudo systemctl status docker"
            print_info "  2. 检查当前用户是否有权限: docker network ls"
            print_info "  3. 查看 Docker 日志: sudo journalctl -u docker.service"
            return 1
        fi
    fi
}

# 修复脚本文件的换行符（Windows CRLF -> Unix LF）
fix_line_endings() {
    local script_file="$1"
    if [ ! -f "$script_file" ]; then
        return 1
    fi
    
    # 检查文件是否包含 \r 字符（更可靠的方法）
    if grep -q $'\r' "$script_file" 2>/dev/null; then
        print_info "修复 $script_file 的换行符（CRLF -> LF）..."
        # 使用 sed 去除 \r 字符
        if sed -i 's/\r$//' "$script_file" 2>/dev/null; then
            # sed -i 成功
            :
        else
            # 如果 sed -i 失败（某些系统不支持），使用临时文件
            local temp_file=$(mktemp)
            if sed 's/\r$//' "$script_file" > "$temp_file" 2>/dev/null; then
                mv "$temp_file" "$script_file"
            else
                rm -f "$temp_file"
                # 如果 sed 也失败，尝试使用 tr
                tr -d '\r' < "$script_file" > "$temp_file" 2>/dev/null && mv "$temp_file" "$script_file" || rm -f "$temp_file"
            fi
        fi
        # 确保文件有执行权限（只给所有者添加，避免需要 root 权限）
        chmod u+x "$script_file" 2>/dev/null || true
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
    
    # 特殊处理.scripts/docker模块（使用install_middleware_linux.sh脚本）
    if [ "$module" = ".scripts/docker" ]; then
        # 检查install_middleware_linux.sh文件
        local install_file="install_middleware_linux.sh"
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
        # 其他模块使用install_linux.sh脚本
        if [ ! -f "install_linux.sh" ]; then
            print_warning "模块 $module 没有 install_linux.sh 脚本，跳过"
            return 1
        fi
        
        # 修复换行符
        fix_line_endings "install_linux.sh"
        
        print_info "执行 $module_name: $command"
        
        if bash install_linux.sh "$command" 2>&1 | tee -a "$LOG_FILE"; then
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
install_linux() {
    print_section "开始安装所有服务"
    
    check_docker "$@"
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
    
    check_docker "$@"
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
        check_docker "$@"
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
    
    check_docker "$@"
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
    else
        print_info "已取消清理操作"
    fi
}

# 更新所有服务
update_all() {
    print_section "更新所有服务"
    
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
    
    check_docker "$@"
    
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
        print_info "查看日志: ./install_linux.sh logs"
        return 1
    fi
}

# 检查 Docker 和 Docker Compose 安装状态
check_environment() {
    print_section "检查运行环境"
    
    echo ""
    print_info "=== 检查 Docker ==="
    if check_command docker; then
        local docker_version=$(docker --version 2>/dev/null || echo "未知版本")
        print_success "Docker 已安装: $docker_version"
        
        # 检查 Docker 服务状态
        if systemctl is-active --quiet docker.service 2>/dev/null; then
            print_info "Docker 服务状态: 运行中"
        elif systemctl is-enabled --quiet docker.service 2>/dev/null; then
            print_warning "Docker 服务已启用但未运行"
        else
            print_warning "Docker 服务未启用"
        fi
        
        # 检查 Docker daemon 是否可访问
        if docker info &> /dev/null; then
            print_success "Docker daemon 可访问"
            
            # 显示 Docker 信息
            local docker_root=$(docker info 2>/dev/null | grep "Docker Root Dir" | awk '{print $4}' || echo "未知")
            print_info "Docker 根目录: $docker_root"
        else
            local error_msg=$(docker info 2>&1)
            if echo "$error_msg" | grep -qi "permission denied"; then
                print_error "Docker daemon 权限不足"
            elif echo "$error_msg" | grep -qi "Is the docker daemon running"; then
                print_error "Docker daemon 未运行"
            else
                print_error "无法连接到 Docker daemon"
            fi
        fi
    else
        print_error "Docker 未安装"
    fi
    
    echo ""
    print_info "=== 检查 Docker Compose ==="
    local compose_found=false
    
    # 检查 docker-compose (v1)
    if check_command docker-compose; then
        local version_output=$(docker-compose --version 2>/dev/null || echo "")
        if [ -n "$version_output" ]; then
            print_success "Docker Compose v1 已安装: $version_output"
            compose_found=true
        fi
    fi
    
    # 检查 docker compose (v2)
    if docker compose version &> /dev/null 2>&1; then
        local version_output=$(docker compose version --short 2>/dev/null || echo "")
        if [ -z "$version_output" ]; then
            version_output=$(docker compose version 2>&1 | grep -E "version|Docker Compose" | head -1 | sed 's/^[[:space:]]*//' || echo "可用")
        fi
        print_success "Docker Compose v2 已安装: $version_output"
        compose_found=true
    fi
    
    if [ "$compose_found" = false ]; then
        print_error "Docker Compose 未安装"
    fi
    
    echo ""
    print_info "=== 系统信息 ==="
    print_info "操作系统: $(uname -s) $(uname -r)"
    print_info "架构: $(uname -m)"
    print_info "用户: $(whoami)"
    
    echo ""
    print_section "检查完成"
}

# 显示帮助信息
show_help() {
    echo "EasyAIoT 统一安装脚本"
    echo ""
    echo "使用方法:"
    echo "  ./install_linux.sh [命令] [模块]"
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
    echo "  check           - 检查 Docker 和 Docker Compose 安装状态"
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
            install_linux
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
        check)
            check_environment
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

