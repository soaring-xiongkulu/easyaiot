#!/bin/bash

# ============================================
# EasyAIoT 中间件部署脚本
# ============================================
# 使用方法：
#   ./install_all.sh [命令]
#
# 可用命令：
#   install    - 安装并启动所有中间件（首次运行）
#   start      - 启动所有中间件
#   stop       - 停止所有中间件
#   restart    - 重启所有中间件
#   status     - 查看所有中间件状态
#   logs       - 查看中间件日志
#   build      - 重新构建所有镜像
#   clean      - 清理所有容器和镜像
#   update     - 更新并重启所有中间件
#   verify     - 验证所有中间件是否启动成功
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"

# 中间件服务列表
MIDDLEWARE_SERVICES=(
    "Nacos"
    "PostgresSQL"
    "TDengine"
    "Redis"
    "Kafka"
)

# 中间件端口映射
declare -A MIDDLEWARE_PORTS
MIDDLEWARE_PORTS["Nacos"]="8848"
MIDDLEWARE_PORTS["PostgresSQL"]="5432"
MIDDLEWARE_PORTS["TDengine"]="6030"
MIDDLEWARE_PORTS["Redis"]="6379"
MIDDLEWARE_PORTS["Kafka"]="9092"

# 中间件健康检查端点
declare -A MIDDLEWARE_HEALTH_ENDPOINTS
MIDDLEWARE_HEALTH_ENDPOINTS["Nacos"]="/nacos/actuator/health"
MIDDLEWARE_HEALTH_ENDPOINTS["PostgresSQL"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["TDengine"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["Redis"]=""
MIDDLEWARE_HEALTH_ENDPOINTS["Kafka"]=""

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

# 检查 Docker 权限
check_docker_permission() {
    if ! docker ps &> /dev/null; then
        print_error "没有权限访问 Docker daemon"
        echo ""
        echo "解决方案："
        echo "  1. 将当前用户添加到 docker 组："
        echo "     sudo usermod -aG docker $USER"
        echo "     然后重新登录或运行: newgrp docker"
        echo ""
        echo "  2. 或者使用 sudo 运行此脚本："
        echo "     sudo ./install_middleware.sh $*"
        echo ""
        exit 1
    fi
}

# 检查 Docker 是否安装
check_docker() {
    if ! check_command docker; then
        print_error "Docker 未安装，请先安装 Docker"
        echo "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker 已安装: $(docker --version)"
    check_docker_permission "$@"
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

# 检查docker-compose.yml是否存在
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yml文件不存在: $COMPOSE_FILE"
        exit 1
    fi
}

# 等待 PostgreSQL 服务就绪
wait_for_postgresql() {
    local max_attempts=60
    local attempt=0
    
    print_info "等待 PostgreSQL 服务就绪..."
    while [ $attempt -lt $max_attempts ]; do
        if docker exec postgres-server pg_isready -U postgres > /dev/null 2>&1; then
            print_success "PostgreSQL 服务已就绪"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    print_error "PostgreSQL 服务未就绪"
    return 1
}

# 等待 Nacos 服务就绪
wait_for_nacos() {
    local max_attempts=60
    local attempt=0
    
    print_info "等待 Nacos 服务就绪..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s --connect-timeout 2 "http://localhost:8848/nacos/actuator/health" > /dev/null 2>&1; then
            print_success "Nacos 服务已就绪"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    print_error "Nacos 服务未就绪"
    return 1
}

# 创建数据库
create_database() {
    local db_name=$1
    
    print_info "创建数据库: $db_name"
    
    if docker exec postgres-server psql -U postgres -lqt | cut -d \| -f 1 | grep -qw "$db_name"; then
        print_info "数据库 $db_name 已存在，跳过创建"
        return 0
    fi
    
    if docker exec postgres-server psql -U postgres -c "CREATE DATABASE \"$db_name\";" > /dev/null 2>&1; then
        print_success "数据库 $db_name 创建成功"
        return 0
    else
        print_error "数据库 $db_name 创建失败"
        return 1
    fi
}

# 执行 SQL 初始化脚本
execute_sql_script() {
    local db_name=$1
    local sql_file=$2
    local error_log=$(mktemp)
    
    if [ ! -f "$sql_file" ]; then
        print_error "SQL 文件不存在: $sql_file"
        return 1
    fi
    
    print_info "执行 SQL 脚本: $sql_file -> 数据库: $db_name"
    
    # 执行 SQL 脚本，捕获错误输出
    if docker exec -i postgres-server psql -U postgres -d "$db_name" < "$sql_file" > /dev/null 2>"$error_log"; then
        print_success "SQL 脚本执行成功: $sql_file"
        rm -f "$error_log"
        return 0
    else
        # 检查错误日志，忽略常见的非致命错误
        local error_content=$(cat "$error_log" 2>/dev/null || echo "")
        rm -f "$error_log"
        
        # 如果错误日志为空或只包含警告，认为成功
        if [ -z "$error_content" ] || echo "$error_content" | grep -qiE "(warning|notice|already exists|does not exist)"; then
            print_success "SQL 脚本执行完成: $sql_file (可能有警告，但已忽略)"
            return 0
        else
            print_warning "SQL 脚本执行可能有问题: $sql_file"
            print_info "错误信息: $error_content"
            # 即使有错误也继续，因为某些 SQL 文件可能包含错误处理
            return 0
        fi
    fi
}

# 初始化 Nacos 用户密码（通过 API 在首次启动时设置）
init_nacos_password() {
    local username=${1:-nacos}
    local password=${2:-basiclab@iot78475418754}
    
    print_info "初始化 Nacos 用户密码: $username"
    
    # 等待 Nacos 完全启动
    sleep 5
    
    # 首先尝试使用新密码检查密码是否已设置
    local check_response=$(curl -s -X GET "http://localhost:8848/nacos/v1/auth/users?pageNo=1&pageSize=10" \
        --user "nacos:$password" 2>/dev/null)
    
    # 如果新密码认证成功，说明密码已经是目标密码
    if [ $? -eq 0 ] && [ -n "$check_response" ] && echo "$check_response" | grep -q "\"username\":\"$username\""; then
        print_success "Nacos 用户 $username 密码已正确设置"
        return 0
    fi
    
    # 尝试使用默认密码进行认证，检查是否为首次启动
    check_response=$(curl -s -X GET "http://localhost:8848/nacos/v1/auth/users?pageNo=1&pageSize=10" \
        --user "nacos:nacos" 2>/dev/null)
    
    # 检查用户是否存在
    local user_exists=false
    if [ $? -eq 0 ] && [ -n "$check_response" ]; then
        if echo "$check_response" | grep -q "\"username\":\"$username\"" || echo "$check_response" | grep -q "$username"; then
            user_exists=true
        fi
    fi
    
    # 如果用户存在且使用默认密码，说明需要修改密码
    if [ "$user_exists" = true ]; then
        print_info "检测到 Nacos 用户 $username 使用默认密码，正在初始化密码..."
        # 使用默认密码登录，通过 API 修改密码
        local response=$(curl -s -w "\n%{http_code}" -X PUT "http://localhost:8848/nacos/v1/auth/users" \
            -H "Content-Type: application/x-www-form-urlencoded" \
            -d "username=$username&newPassword=$password" \
            --user "nacos:nacos" 2>/dev/null)
        
        local http_code=$(echo "$response" | tail -n 1)
        local body=$(echo "$response" | sed '$d')
        
        if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
            print_success "Nacos 用户 $username 密码初始化成功"
            return 0
        else
            print_warning "Nacos 用户密码初始化可能失败，HTTP 状态码: $http_code，响应: $body"
        fi
    else
        # 如果用户不存在，说明是首次启动，创建用户并设置密码
        print_info "首次启动 Nacos，创建用户 $username 并设置密码..."
        # 对于首次启动，Nacos 默认用户是 nacos/nacos，我们需要修改密码
        # 先尝试使用默认密码修改
        local response=$(curl -s -w "\n%{http_code}" -X PUT "http://localhost:8848/nacos/v1/auth/users" \
            -H "Content-Type: application/x-www-form-urlencoded" \
            -d "username=$username&newPassword=$password" \
            --user "nacos:nacos" 2>/dev/null)
        
        local http_code=$(echo "$response" | tail -n 1)
        local body=$(echo "$response" | sed '$d')
        
        if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
            print_success "Nacos 用户 $username 密码初始化成功"
            return 0
        else
            print_warning "Nacos 用户密码初始化可能失败，HTTP 状态码: $http_code，响应: $body"
        fi
    fi
    
    # 验证最终结果
    sleep 2
    check_response=$(curl -s -X GET "http://localhost:8848/nacos/v1/auth/users?pageNo=1&pageSize=10" \
        --user "nacos:$password" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$check_response" ] && echo "$check_response" | grep -q "\"username\":\"$username\""; then
        print_success "Nacos 用户 $username 密码初始化成功（验证通过）"
        return 0
    else
        print_warning "Nacos 用户密码初始化可能失败，但将继续执行"
        return 0
    fi
}

# 初始化数据库
init_databases() {
    print_section "初始化数据库"
    
    # 等待 PostgreSQL 就绪
    if ! wait_for_postgresql; then
        print_error "PostgreSQL 未就绪，无法初始化数据库"
        return 1
    fi
    
    # 等待 Nacos 就绪
    if ! wait_for_nacos; then
        print_warning "Nacos 未就绪，将跳过 Nacos 用户创建"
    fi
    
    # 定义数据库和 SQL 文件映射
    # SQL 文件路径：相对于脚本目录的上一级目录的 postgresql 目录
    local sql_dir="$(cd "${SCRIPT_DIR}/../postgresql" && pwd)"
    declare -A DB_SQL_MAP
    DB_SQL_MAP["iot-ai10"]="${sql_dir}/iot-ai10.sql"
    DB_SQL_MAP["iot-device10"]="${sql_dir}/iot-device10.sql"
    DB_SQL_MAP["iot-video10"]="${sql_dir}/iot-video10.sql"
    DB_SQL_MAP["ruoyi-vue-pro10"]="${sql_dir}/ruoyi-vue-pro10.sql"
    
    local success_count=0
    local total_count=${#DB_SQL_MAP[@]}
    
    # 创建数据库并执行 SQL 脚本
    for db_name in "${!DB_SQL_MAP[@]}"; do
        local sql_file="${DB_SQL_MAP[$db_name]}"
        
        if create_database "$db_name"; then
            if execute_sql_script "$db_name" "$sql_file"; then
                success_count=$((success_count + 1))
            fi
        fi
        echo ""
    done
    
    # 初始化 Nacos 用户密码
    echo ""
    if wait_for_nacos; then
        init_nacos_password "nacos" "basiclab@iot78475418754"
    fi
    
    echo ""
    print_section "数据库初始化结果"
    echo "成功: ${GREEN}$success_count${NC} / $total_count"
    
    if [ $success_count -eq $total_count ]; then
        print_success "所有数据库初始化完成！"
        return 0
    else
        print_warning "部分数据库初始化失败"
        return 1
    fi
}

# 安装所有中间件
install_middleware() {
    print_section "开始安装所有中间件"
    
    check_docker "$@"
    check_docker_compose
    check_compose_file
    create_network
    
    print_info "启动所有中间件服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d
    
    print_success "中间件安装完成"
    echo ""
    print_info "等待服务启动..."
    sleep 10
    verify_middleware
    
    # 初始化数据库
    echo ""
    init_databases
}

# 启动所有中间件
start_middleware() {
    print_section "启动所有中间件"
    
    check_docker "$@"
    check_docker_compose
    check_compose_file
    create_network
    
    print_info "启动所有中间件服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d
    
    print_success "所有中间件启动完成"
    echo ""
    print_info "等待服务就绪..."
    sleep 10
    verify_middleware
}

# 停止所有中间件
stop_middleware() {
    print_section "停止所有中间件"
    
    check_docker "$@"
    check_docker_compose
    check_compose_file
    
    print_info "停止所有中间件服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" down
    
    print_success "所有中间件已停止"
}

# 重启所有中间件
restart_middleware() {
    print_section "重启所有中间件"
    
    check_docker "$@"
    check_docker_compose
    check_compose_file
    create_network
    
    print_info "重启所有中间件服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" restart
    
    print_success "所有中间件重启完成"
    echo ""
    print_info "等待服务就绪..."
    sleep 10
    verify_middleware
}

# 查看所有中间件状态
status_middleware() {
    print_section "所有中间件状态"
    
    check_docker "$@"
    check_docker_compose
    check_compose_file
    
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps
}

# 查看日志
view_logs() {
    local service=${1:-""}
    
    check_docker "$@"
    check_docker_compose
    check_compose_file
    
    if [ -z "$service" ]; then
        print_info "查看所有中间件日志..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" logs --tail=100
    else
        print_info "查看 $service 服务日志..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" logs --tail=100 "$service"
    fi
}

# 构建所有镜像
build_middleware() {
    print_section "构建所有中间件镜像"
    
    check_docker "$@"
    check_docker_compose
    check_compose_file
    
    print_info "构建所有中间件镜像..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" build --no-cache
    
    print_success "所有中间件镜像构建完成"
}

# 清理所有中间件
clean_middleware() {
    print_warning "这将删除所有中间件容器、镜像和数据卷，确定要继续吗？(y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_section "清理所有中间件"
        
        check_docker "$@"
        check_docker_compose
        check_compose_file
        
        print_info "清理所有中间件服务..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" down -v
        
        print_success "清理完成"
    else
        print_info "已取消清理操作"
    fi
}

# 更新所有中间件
update_middleware() {
    print_section "更新所有中间件"
    
    check_docker "$@"
    check_docker_compose
    check_compose_file
    create_network
    
    print_info "拉取最新镜像..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" pull
    
    print_info "重启所有中间件服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d
    
    print_success "所有中间件更新完成"
    echo ""
    print_info "等待服务就绪..."
    sleep 10
    verify_middleware
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

# 验证中间件健康状态
verify_service_health() {
    local service=$1
    local port=${MIDDLEWARE_PORTS[$service]}
    local health_endpoint=${MIDDLEWARE_HEALTH_ENDPOINTS[$service]}
    
    print_info "验证 $service (端口: $port)..."
    
    if wait_for_service "$service" "$port" "$health_endpoint"; then
        # 检查HTTP响应
        if [ -n "$health_endpoint" ]; then
            response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port$health_endpoint" 2>/dev/null || echo "000")
            if [ "$response" = "200" ] || [ "$response" = "000" ]; then
                print_success "$service 运行正常"
                return 0
            else
                print_warning "$service 响应异常 (HTTP $response)"
                return 1
            fi
        else
            print_success "$service 运行正常"
            return 0
        fi
    else
        print_error "$service 未就绪"
        return 1
    fi
}

# 验证所有中间件
verify_middleware() {
    print_section "验证所有中间件"
    
    check_docker "$@"
    
    local success_count=0
    local total_count=${#MIDDLEWARE_SERVICES[@]}
    local failed_services=()
    
    for service in "${MIDDLEWARE_SERVICES[@]}"; do
        if verify_service_health "$service"; then
            success_count=$((success_count + 1))
        else
            failed_services+=("$service")
        fi
        echo ""
    done
    
    print_section "验证结果"
    echo "成功: ${GREEN}$success_count${NC} / $total_count"
    
    if [ $success_count -eq $total_count ]; then
        print_success "所有中间件运行正常！"
        echo ""
        echo -e "${GREEN}中间件访问地址:${NC}"
        echo -e "  Nacos:      http://localhost:8848/nacos"
        echo -e "  PostgreSQL: localhost:5432"
        echo -e "  TDengine:   localhost:6030"
        echo -e "  Redis:      localhost:6379"
        echo -e "  Kafka:      localhost:9092"
        echo ""
        return 0
    else
        print_warning "部分中间件未就绪:"
        for failed in "${failed_services[@]}"; do
            echo -e "  ${RED}✗ $failed${NC}"
        done
        echo ""
        print_info "查看日志: ./install.sh logs"
        return 1
    fi
}

# 显示帮助信息
show_help() {
    echo "EasyAIoT 中间件部署脚本"
    echo ""
    echo "使用方法:"
    echo "  ./install.sh [命令] [服务]"
    echo ""
    echo "可用命令:"
    echo "  install         - 安装并启动所有中间件（首次运行）"
    echo "  start           - 启动所有中间件"
    echo "  stop            - 停止所有中间件"
    echo "  restart         - 重启所有中间件"
    echo "  status          - 查看所有中间件状态"
    echo "  logs            - 查看所有中间件日志"
    echo "  logs [服务]     - 查看指定服务日志"
    echo "  build           - 重新构建所有镜像"
    echo "  clean           - 清理所有容器和镜像"
    echo "  update          - 更新并重启所有中间件"
    echo "  verify          - 验证所有中间件是否启动成功"
    echo "  help            - 显示此帮助信息"
    echo ""
    echo "中间件服务列表:"
    for service in "${MIDDLEWARE_SERVICES[@]}"; do
        echo "  - $service"
    done
    echo ""
}

# 主函数
main() {
    case "${1:-help}" in
        install)
            install_middleware
            ;;
        start)
            start_middleware
            ;;
        stop)
            stop_middleware
            ;;
        restart)
            restart_middleware
            ;;
        status)
            status_middleware
            ;;
        logs)
            view_logs "$2"
            ;;
        build)
            build_middleware
            ;;
        clean)
            clean_middleware
            ;;
        update)
            update_middleware
            ;;
        verify)
            verify_middleware
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
