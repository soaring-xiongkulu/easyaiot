#!/bin/bash

# ============================================
# PostgreSQL 容器重启脚本
# ============================================
# 用于杀死占用 5432 端口的进程并重启 PostgreSQL Docker 容器
# 使用方法：
#   sudo ./restart_postgresql.sh
# 或
#   ./restart_postgresql.sh  (需要管理员权限)
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

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "此脚本需要管理员权限（root 或 sudo）"
        print_info "请使用以下命令运行："
        echo "  sudo $0"
        exit 1
    fi
}

# 检查端口占用
check_port() {
    local port=$1
    print_info "检查端口 $port 是否被占用..."
    
    # 使用 lsof 或 ss 命令查找占用端口的进程
    local pid=""
    
    if command -v lsof >/dev/null 2>&1; then
        pid=$(lsof -ti:$port 2>/dev/null || echo "")
    elif command -v ss >/dev/null 2>&1; then
        pid=$(ss -lptn "sport = :$port" | grep -oP 'pid=\K[0-9]+' | head -1 || echo "")
    elif command -v netstat >/dev/null 2>&1; then
        pid=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | head -1 || echo "")
    else
        print_error "未找到 lsof、ss 或 netstat 命令，无法检查端口占用"
        return 1
    fi
    
    if [ -n "$pid" ]; then
        print_warning "端口 $port 被进程 PID $pid 占用"
        # 获取进程信息
        if ps -p "$pid" >/dev/null 2>&1; then
            local process_info=$(ps -p "$pid" -o comm=,args= 2>/dev/null || echo "未知进程")
            print_info "进程信息: $process_info"
        fi
        echo "$pid"
        return 0
    else
        print_success "端口 $port 未被占用"
        return 1
    fi
}

# 杀死占用端口的进程
kill_port_process() {
    local port=$1
    print_section "处理端口 $port 占用"
    
    local pid=$(check_port "$port")
    
    if [ -n "$pid" ]; then
        print_warning "准备杀死进程 PID: $pid"
        
        # 先尝试优雅终止
        print_info "尝试优雅终止进程..."
        if kill -TERM "$pid" 2>/dev/null; then
            sleep 2
            # 检查进程是否还在运行
            if ps -p "$pid" >/dev/null 2>&1; then
                print_warning "进程仍在运行，使用强制终止..."
                kill -KILL "$pid" 2>/dev/null || true
                sleep 1
            else
                print_success "进程已优雅终止"
                return 0
            fi
        else
            print_warning "无法发送 TERM 信号，尝试强制终止..."
            kill -KILL "$pid" 2>/dev/null || true
            sleep 1
        fi
        
        # 再次检查
        if ps -p "$pid" >/dev/null 2>&1; then
            print_error "无法终止进程 PID: $pid"
            return 1
        else
            print_success "进程 PID $pid 已成功终止"
            return 0
        fi
    else
        print_info "端口 $port 未被占用，无需终止进程"
        return 0
    fi
}

# 重启 PostgreSQL 容器
restart_postgresql_container() {
    print_section "重启 PostgreSQL 容器"
    
    local compose_file="docker-compose.yml"
    local service_name="PostgresSQL"
    local container_name="postgres-server"
    
    # 检查 docker-compose.yml 是否存在
    if [ ! -f "$compose_file" ]; then
        print_error "未找到 $compose_file 文件"
        return 1
    fi
    
    # 检查 Docker 是否运行
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker 未运行，请先启动 Docker"
        return 1
    fi
    
    # 停止容器
    print_info "停止 PostgreSQL 容器..."
    if docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
        docker stop "$container_name" >/dev/null 2>&1 || true
        print_success "容器已停止"
    else
        print_warning "容器 $container_name 不存在"
    fi
    
    # 等待一下确保端口释放
    sleep 2
    
    # 启动容器
    print_info "启动 PostgreSQL 容器..."
    if docker-compose -f "$compose_file" up -d "$service_name" 2>&1; then
        print_success "PostgreSQL 容器启动成功"
        
        # 等待容器就绪
        print_info "等待容器就绪..."
        local max_wait=30
        local wait_count=0
        while [ $wait_count -lt $max_wait ]; do
            if docker exec "$container_name" pg_isready -U postgres >/dev/null 2>&1; then
                print_success "PostgreSQL 容器已就绪"
                return 0
            fi
            sleep 1
            wait_count=$((wait_count + 1))
        done
        
        print_warning "容器已启动，但健康检查超时（可能仍在初始化中）"
        return 0
    else
        print_error "PostgreSQL 容器启动失败"
        return 1
    fi
}

# 主函数
main() {
    print_section "PostgreSQL 容器重启脚本"
    
    # 检查 root 权限
    check_root
    
    local port=5432
    
    # 杀死占用端口的进程
    kill_port_process "$port"
    
    # 重启容器
    restart_postgresql_container
    
    print_section "操作完成"
    print_success "PostgreSQL 容器重启流程已完成"
    print_info "可以使用以下命令查看容器状态："
    echo "  docker ps | grep postgres-server"
    echo "  docker logs postgres-server"
}

# 执行主函数
main "$@"

