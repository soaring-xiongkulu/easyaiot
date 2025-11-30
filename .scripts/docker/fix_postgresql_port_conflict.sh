#!/bin/bash

# ============================================
# PostgreSQL 端口冲突修复脚本
# ============================================
# 用于修复宿主机 PostgreSQL 服务占用 5432 端口导致 Docker 容器无法启动的问题
# 使用方法：
#   ./fix_postgresql_port_conflict.sh
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

DB_PORT="5432"

print_section "PostgreSQL 端口冲突检测和修复工具"

# 检查端口是否被占用
print_info "检查端口 $DB_PORT 是否被占用..."
port_in_use=0
port_process=""

if command -v ss &> /dev/null; then
    port_info=$(ss -tlnp 2>/dev/null | grep -E ":$DB_PORT[[:space:]]|:$DB_PORT$" | head -1 || echo "")
    if [ -n "$port_info" ]; then
        port_in_use=1
        if echo "$port_info" | grep -q "docker"; then
            print_info "端口 $DB_PORT 被 Docker 容器占用（正常）"
            port_in_use=0
        else
            print_warning "端口 $DB_PORT 被非 Docker 进程占用"
            # 尝试获取进程信息
            if pgrep -f "postgres.*$DB_PORT" > /dev/null 2>&1; then
                port_process=$(pgrep -f "postgres.*$DB_PORT" | head -1)
                print_info "检测到 PostgreSQL 进程: PID $port_process"
            elif pgrep -f "/usr/lib/postgresql" > /dev/null 2>&1; then
                port_process=$(pgrep -f "/usr/lib/postgresql" | head -1)
                print_info "检测到 PostgreSQL 进程: PID $port_process"
            fi
        fi
    else
        print_success "端口 $DB_PORT 未被占用"
    fi
elif command -v netstat &> /dev/null; then
    port_info=$(netstat -tlnp 2>/dev/null | grep -E ":$DB_PORT[[:space:]]|:$DB_PORT$" | head -1 || echo "")
    if [ -n "$port_info" ]; then
        port_in_use=1
        if echo "$port_info" | grep -q "docker"; then
            print_info "端口 $DB_PORT 被 Docker 容器占用（正常）"
            port_in_use=0
        else
            print_warning "端口 $DB_PORT 被非 Docker 进程占用"
        fi
    else
        print_success "端口 $DB_PORT 未被占用"
    fi
else
    print_warning "无法检查端口状态（ss 或 netstat 命令不可用）"
fi

# 检查 Docker 容器端口映射
print_info "检查 Docker 容器端口映射..."
container_ports=$(docker inspect postgres-server --format '{{json .HostConfig.PortBindings}}' 2>/dev/null || echo "{}")
if [ "$container_ports" = "{}" ] || [ -z "$container_ports" ]; then
    print_error "Docker 容器端口映射未配置"
    if [ $port_in_use -eq 1 ]; then
        print_warning "这很可能是由于端口 $DB_PORT 被宿主机 PostgreSQL 服务占用导致的"
    fi
else
    print_success "Docker 容器端口映射配置正常"
fi

# 如果检测到端口冲突，提供解决方案
if [ $port_in_use -eq 1 ] && [ -n "$port_process" ]; then
    print_section "检测到端口冲突"
    
    print_error "宿主机 PostgreSQL 服务正在运行并占用端口 $DB_PORT"
    print_info "这导致 Docker 容器无法绑定该端口"
    echo ""
    print_info "解决方案（选择其一）："
    echo ""
    print_info "方案 1：停止宿主机 PostgreSQL 服务（推荐）"
    print_info "  执行命令："
    print_info "    sudo systemctl stop postgresql"
    print_info "    sudo systemctl disable postgresql  # 可选：禁止开机自启"
    echo ""
    print_info "方案 2：修改 Docker 容器端口映射"
    print_info "  编辑 docker-compose.yml，将端口映射改为："
    print_info "    ports:"
    print_info "      - \"5433:5432\"  # 使用 5433 作为宿主机端口"
    print_info "  然后更新连接配置中的端口号"
    echo ""
    print_info "方案 3：修改宿主机 PostgreSQL 端口"
    print_info "  编辑 /etc/postgresql/*/main/postgresql.conf，修改 port = 5433"
    print_info "  然后重启宿主机 PostgreSQL 服务"
    echo ""
    
    # 询问是否自动停止宿主机服务
    read -p "是否要尝试停止宿主机 PostgreSQL 服务？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "尝试停止宿主机 PostgreSQL 服务..."
        if systemctl is-active --quiet postgresql 2>/dev/null; then
            if sudo systemctl stop postgresql 2>/dev/null; then
                print_success "宿主机 PostgreSQL 服务已停止"
                sleep 2
                
                # 重新启动 Docker 容器
                print_info "重新启动 Docker 容器..."
                if docker-compose stop PostgresSQL 2>/dev/null; then
                    docker-compose up -d PostgresSQL
                    print_success "Docker 容器已重新启动"
                    print_info "等待容器就绪..."
                    sleep 5
                    
                    # 测试连接
                    if docker exec postgres-server pg_isready -U postgres > /dev/null 2>&1; then
                        print_success "PostgreSQL 容器已就绪"
                        print_info "现在可以运行 ./test_postgresql_connection.sh 测试连接"
                    else
                        print_warning "容器启动中，请稍后运行 ./test_postgresql_connection.sh 测试连接"
                    fi
                else
                    print_warning "无法通过 docker-compose 重启容器，请手动执行："
                    print_info "  docker-compose up -d PostgresSQL"
                fi
            else
                print_error "无法停止宿主机 PostgreSQL 服务（需要 sudo 权限）"
                print_info "请手动执行: sudo systemctl stop postgresql"
            fi
        else
            print_info "宿主机 PostgreSQL 服务未运行（可能已被停止）"
        fi
    else
        print_info "未自动停止服务，请手动选择上述方案之一解决端口冲突"
    fi
else
    print_success "未检测到端口冲突"
    print_info "如果 Docker 容器仍无法启动，请检查容器日志："
    print_info "  docker logs postgres-server"
fi

echo ""
print_success "端口冲突检测完成！"

