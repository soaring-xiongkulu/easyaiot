#!/bin/bash

# ============================================
# Nexus3 部署脚本
# ============================================
# 使用方法：
#   ./install.sh [命令]
#
# 可用命令：
#   install    - 安装并启动 Nexus3（首次运行）
#   start      - 启动 Nexus3
#   stop       - 停止 Nexus3
#   restart    - 重启 Nexus3
#   reinstall  - 重新安装 Nexus3（可选择是否保留数据）
#   status     - 查看 Nexus3 状态
#   logs       - 查看 Nexus3 日志
#   fix        - 修复数据目录权限
#   clean      - 清理容器和数据（危险操作）
#   check      - 检查 Docker 和 Docker Compose 安装状态
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
NETWORK_NAME="easyaiot-network"
CONTAINER_NAME="nexus-server"
NEXUS_PORT="18081"

# 日志函数
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
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    print_success "Docker 已安装: $(docker --version)"
}

# 检查 Docker Compose 是否安装
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检测使用 docker-compose 还是 docker compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        print_success "Docker Compose 已安装: $(docker-compose --version)"
    else
        COMPOSE_CMD="docker compose"
        print_success "Docker Compose 已安装: $(docker compose version)"
    fi
}

# 检查 docker-compose.yml 文件是否存在
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yml 文件不存在: $COMPOSE_FILE"
        exit 1
    fi
    print_success "docker-compose.yml 文件存在"
}

# 创建 Docker 网络
create_network() {
    if ! docker network inspect "$NETWORK_NAME" &> /dev/null; then
        print_info "创建 Docker 网络: $NETWORK_NAME"
        docker network create "$NETWORK_NAME" || {
            print_error "创建网络失败"
            exit 1
        }
        print_success "网络创建成功"
    else
        print_info "网络已存在: $NETWORK_NAME"
    fi
}

# 创建数据目录
create_data_directories() {
    print_info "创建数据目录..."
    mkdir -p "${SCRIPT_DIR}/nexus_data"
    
    # Nexus3 容器内运行的用户是 UID 200，需要设置正确的权限
    print_info "设置数据目录权限（Nexus3 容器使用 UID 200）..."
    
    if [ "$EUID" -eq 0 ]; then
        # 以 root 运行
        chown -R 200:200 "${SCRIPT_DIR}/nexus_data" 2>/dev/null || true
        chmod -R 755 "${SCRIPT_DIR}/nexus_data" 2>/dev/null || true
        print_success "权限已设置 (UID 200:200)"
    else
        # 需要 sudo
        if command -v sudo &> /dev/null; then
            sudo chown -R 200:200 "${SCRIPT_DIR}/nexus_data" 2>/dev/null && \
            sudo chmod -R 755 "${SCRIPT_DIR}/nexus_data" 2>/dev/null && \
            print_success "权限已设置 (UID 200:200)" || {
                print_warning "无法设置权限，请手动执行: sudo chown -R 200:200 ${SCRIPT_DIR}/nexus_data"
                print_warning "然后执行: sudo chmod -R 755 ${SCRIPT_DIR}/nexus_data"
            }
        else
            print_warning "需要 root 权限或 sudo 来设置权限"
            print_warning "请手动执行: sudo chown -R 200:200 ${SCRIPT_DIR}/nexus_data"
            print_warning "然后执行: sudo chmod -R 755 ${SCRIPT_DIR}/nexus_data"
        fi
    fi
    
    print_success "数据目录创建完成"
}

# 检查端口占用
check_port() {
    if lsof -Pi :$NEXUS_PORT -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$NEXUS_PORT "; then
        print_warning "端口 $NEXUS_PORT 已被占用"
        return 1
    fi
    return 0
}

# 安装 Nexus3
install_nexus() {
    print_section "开始安装 Nexus3"
    
    check_docker
    check_docker_compose
    check_compose_file
    create_network
    create_data_directories
    
    if ! check_port; then
        print_error "端口 $NEXUS_PORT 被占用，请先释放端口或修改配置"
        exit 1
    fi
    
    print_info "拉取 Nexus3 镜像..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" pull || {
        print_warning "镜像拉取失败，将使用本地镜像"
    }
    
    print_info "启动 Nexus3 容器..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d
    
    print_success "Nexus3 安装完成"
    print_info "等待 Nexus3 启动（这可能需要几分钟）..."
    
    # 等待服务启动
    local max_attempts=60
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker exec "$CONTAINER_NAME" wget --quiet --tries=1 --spider http://localhost:8081/ 2>/dev/null; then
            print_success "Nexus3 已启动"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -ge $max_attempts ]; then
        echo ""
        print_warning "Nexus3 启动超时，请检查日志: ./install.sh logs"
        echo ""
        print_info "访问地址: ${GREEN}http://localhost:$NEXUS_PORT${NC}"
        print_info "（服务可能仍在启动中，请稍后访问）"
        return 1
    fi
    
    echo ""
    # 等待密码文件生成（Nexus3 启动后需要一些时间生成密码文件）
    print_info "等待密码文件生成..."
    local password_file="${SCRIPT_DIR}/nexus_data/admin.password"
    local password_attempts=30
    local password_attempt=0
    while [ $password_attempt -lt $password_attempts ]; do
        if [ -f "$password_file" ]; then
            break
        fi
        password_attempt=$((password_attempt + 1))
        sleep 2
    done
    
    # 读取并显示登录信息
    echo ""
    print_section "Nexus3 安装成功"
    echo ""
    print_success "访问地址: ${GREEN}http://localhost:$NEXUS_PORT${NC}"
    echo ""
    print_success "默认管理员账号: ${GREEN}admin${NC}"
    
    if [ -f "$password_file" ]; then
        local admin_password=$(cat "$password_file" | tr -d '\n\r ')
        if [ -n "$admin_password" ]; then
            print_success "默认管理员密码: ${GREEN}$admin_password${NC}"
            echo ""
            print_warning "重要提示：首次登录后请立即修改默认密码！"
        else
            print_warning "密码文件存在但为空，请稍后手动获取密码："
            echo "  docker exec $CONTAINER_NAME cat /nexus-data/admin.password"
        fi
    else
        print_warning "密码文件尚未生成，请稍后执行以下命令获取密码："
        echo "  docker exec $CONTAINER_NAME cat /nexus-data/admin.password"
        echo ""
        print_info "或者稍后运行: ./install.sh status 查看登录信息"
    fi
    
    echo ""
    print_info "提示：首次登录后系统会要求修改默认密码"
    echo ""
    return 0
}

# 启动 Nexus3
start_nexus() {
    print_section "启动 Nexus3"
    check_docker_compose
    check_compose_file
    
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d
    print_success "Nexus3 启动命令已执行"
    
    sleep 3
    show_status
}

# 停止 Nexus3
stop_nexus() {
    print_section "停止 Nexus3"
    check_docker_compose
    check_compose_file
    
    $COMPOSE_CMD -f "$COMPOSE_FILE" down
    print_success "Nexus3 已停止"
}

# 重新安装 Nexus3
reinstall_nexus() {
    print_section "重新安装 Nexus3"
    print_warning "此操作将停止并删除容器，然后重新安装"
    read -p "是否保留数据目录？(输入 'yes' 保留数据，其他任意键删除数据): " keep_data
    
    check_docker_compose
    check_compose_file
    
    # 停止并删除容器
    print_info "停止并删除容器..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" down -v
    
    # 根据用户选择处理数据目录
    if [ "$keep_data" != "yes" ]; then
        if [ -d "${SCRIPT_DIR}/nexus_data" ]; then
            print_warning "删除数据目录..."
            rm -rf "${SCRIPT_DIR}/nexus_data"
            print_success "数据目录已删除"
        fi
    else
        print_info "保留数据目录: ${SCRIPT_DIR}/nexus_data"
    fi
    
    # 重新安装
    print_info "开始重新安装..."
    install_nexus
}

# 重启 Nexus3
restart_nexus() {
    print_section "重启 Nexus3"
    check_docker_compose
    check_compose_file
    
    $COMPOSE_CMD -f "$COMPOSE_FILE" restart
    print_success "Nexus3 已重启"
    
    sleep 3
    show_status
}

# 查看状态
show_status() {
    print_section "Nexus3 状态"
    check_docker_compose
    check_compose_file
    
    echo ""
    print_info "容器状态:"
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps
    
    echo ""
    if docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" | grep -q "$CONTAINER_NAME"; then
        print_info "健康检查:"
        if docker exec "$CONTAINER_NAME" wget --quiet --tries=1 --spider http://localhost:8081/ 2>/dev/null; then
            print_success "Nexus3 运行正常"
            echo ""
            print_section "登录信息"
            print_success "访问地址: ${GREEN}http://localhost:$NEXUS_PORT${NC}"
            print_success "默认管理员账号: ${GREEN}admin${NC}"
            
            # 尝试读取密码文件
            local password_file="${SCRIPT_DIR}/nexus_data/admin.password"
            if [ -f "$password_file" ]; then
                local admin_password=$(cat "$password_file" | tr -d '\n\r ' 2>/dev/null)
                if [ -n "$admin_password" ]; then
                    print_success "默认管理员密码: ${GREEN}$admin_password${NC}"
                else
                    print_warning "密码文件存在但为空，请执行以下命令获取："
                    echo "  docker exec $CONTAINER_NAME cat /nexus-data/admin.password"
                fi
            else
                print_warning "密码文件不存在，请执行以下命令获取："
                echo "  docker exec $CONTAINER_NAME cat /nexus-data/admin.password"
            fi
        else
            print_warning "Nexus3 容器运行中，但服务可能尚未完全启动"
            echo ""
            print_info "访问地址: ${GREEN}http://localhost:$NEXUS_PORT${NC}"
            print_info "（服务可能仍在启动中，请稍后访问）"
        fi
    else
        print_warning "Nexus3 容器未运行"
        echo ""
        print_info "访问地址: ${GREEN}http://localhost:$NEXUS_PORT${NC}"
        print_info "（请先启动服务: ./install.sh start）"
    fi
}

# 查看日志
show_logs() {
    print_section "Nexus3 日志"
    check_docker_compose
    check_compose_file
    
    $COMPOSE_CMD -f "$COMPOSE_FILE" logs -f --tail=100
}

# 修复权限
fix_permissions() {
    print_section "修复 Nexus3 数据目录权限"
    
    local data_dir="${SCRIPT_DIR}/nexus_data"
    
    print_info "数据目录: $data_dir"
    
    # 创建目录（如果不存在）
    mkdir -p "$data_dir"
    
    # 检查当前权限
    if [ -d "$data_dir" ]; then
        local owner=$(stat -c "%U:%G (%u:%g)" "$data_dir" 2>/dev/null || stat -f "%Su:%Sg" "$data_dir" 2>/dev/null || echo "未知")
        local perms=$(stat -c "%a" "$data_dir" 2>/dev/null || stat -f "%OLp" "$data_dir" 2>/dev/null || echo "未知")
        print_info "当前数据目录权限: $owner, 权限: $perms"
    fi
    
    # 设置权限（Nexus3 容器使用 UID 200）
    print_info "设置数据目录权限为 200:200..."
    
    if [ "$EUID" -eq 0 ]; then
        # 以 root 运行
        chown -R 200:200 "$data_dir" 2>/dev/null || true
        chmod -R 755 "$data_dir" 2>/dev/null || true
        print_success "权限已设置 (UID 200:200)"
    else
        # 需要 sudo
        if command -v sudo &> /dev/null; then
            sudo chown -R 200:200 "$data_dir" 2>/dev/null && \
            sudo chmod -R 755 "$data_dir" 2>/dev/null && \
            print_success "权限已设置 (UID 200:200)" || {
                print_error "无法设置权限"
                print_warning "请手动执行: sudo chown -R 200:200 $data_dir"
                print_warning "然后执行: sudo chmod -R 755 $data_dir"
                exit 1
            }
        else
            print_error "需要 root 权限或 sudo 来设置权限"
            print_warning "请手动执行: sudo chown -R 200:200 $data_dir"
            print_warning "然后执行: sudo chmod -R 755 $data_dir"
            exit 1
        fi
    fi
    
    # 验证权限
    if [ -d "$data_dir" ]; then
        local new_owner=$(stat -c "%U:%G (%u:%g)" "$data_dir" 2>/dev/null || stat -f "%Su:%Sg" "$data_dir" 2>/dev/null || echo "未知")
        local new_perms=$(stat -c "%a" "$data_dir" 2>/dev/null || stat -f "%OLp" "$data_dir" 2>/dev/null || echo "未知")
        print_info "修复后数据目录权限: $new_owner, 权限: $new_perms"
        
        # 检查是否是 200:200
        local uid=$(stat -c "%u" "$data_dir" 2>/dev/null || stat -f "%u" "$data_dir" 2>/dev/null || echo "")
        if [ "$uid" = "200" ]; then
            print_success "权限修复成功！"
        else
            print_warning "权限可能未正确设置，UID 应该是 200，当前是: $uid"
        fi
    fi
}

# 清理（危险操作）
clean_nexus() {
    print_section "清理 Nexus3"
    print_warning "此操作将删除容器和数据，请确认！"
    read -p "输入 'yes' 确认删除: " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_info "操作已取消"
        return
    fi
    
    check_docker_compose
    check_compose_file
    
    print_info "停止并删除容器..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" down -v
    
    print_warning "是否删除数据目录？(这将删除所有 Nexus3 数据)"
    read -p "输入 'yes' 确认删除数据: " confirm_data
    
    if [ "$confirm_data" = "yes" ]; then
        if [ -d "${SCRIPT_DIR}/nexus_data" ]; then
            rm -rf "${SCRIPT_DIR}/nexus_data"
            print_success "数据目录已删除"
        fi
    else
        print_info "保留数据目录: ${SCRIPT_DIR}/nexus_data"
    fi
    
    print_success "清理完成"
}

# 检查环境
check_environment() {
    print_section "环境检查"
    check_docker
    check_docker_compose
    check_compose_file
    create_network
    
    echo ""
    print_info "端口检查:"
    if check_port; then
        print_success "端口 $NEXUS_PORT 可用"
    else
        print_warning "端口 $NEXUS_PORT 已被占用"
    fi
    
    echo ""
    print_info "数据目录:"
    if [ -d "${SCRIPT_DIR}/nexus_data" ]; then
        print_success "数据目录存在: ${SCRIPT_DIR}/nexus_data"
        du -sh "${SCRIPT_DIR}/nexus_data" 2>/dev/null || true
    else
        print_info "数据目录不存在（将在安装时创建）"
    fi
}

# 主函数
main() {
    case "${1:-}" in
        install)
            install_nexus
            ;;
        start)
            start_nexus
            ;;
        stop)
            stop_nexus
            ;;
        reinstall)
            reinstall_nexus
            ;;
        restart)
            restart_nexus
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        fix)
            fix_permissions
            ;;
        clean)
            clean_nexus
            ;;
        check)
            check_environment
            ;;
        *)
            echo "用法: $0 {install|start|stop|restart|reinstall|status|logs|fix|clean|check}"
            echo ""
            echo "命令说明:"
            echo "  install   - 安装并启动 Nexus3（首次运行）"
            echo "  start     - 启动 Nexus3"
            echo "  stop      - 停止 Nexus3"
            echo "  restart   - 重启 Nexus3"
            echo "  reinstall - 重新安装 Nexus3（可选择是否保留数据）"
            echo "  status    - 查看 Nexus3 状态"
            echo "  logs      - 查看 Nexus3 日志"
            echo "  fix       - 修复数据目录权限"
            echo "  clean     - 清理容器和数据（危险操作）"
            echo "  check     - 检查 Docker 和 Docker Compose 安装状态"
            exit 1
            ;;
    esac
}

main "$@"
