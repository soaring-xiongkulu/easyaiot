#!/bin/bash

# ============================================
# PostgreSQL 最大连接数配置生效脚本
# ============================================
# 此脚本用于重启 PostgreSQL 容器以使 max_connections=10240 配置生效
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_info "开始应用 PostgreSQL 最大连接数配置..."

# 检查容器是否存在
if ! docker ps -a --filter "name=postgres-server" --format "{{.Names}}" | grep -q "postgres-server"; then
    print_error "PostgreSQL 容器 postgres-server 不存在"
    print_info "请先启动 PostgreSQL 容器"
    exit 1
fi

# 检查容器是否在运行
if ! docker ps --filter "name=postgres-server" --format "{{.Names}}" | grep -q "postgres-server"; then
    print_warning "PostgreSQL 容器未运行，正在启动..."
    docker start postgres-server
    sleep 5
fi

# 显示当前配置
print_info "检查当前 max_connections 配置..."
current_max_conn=$(docker exec postgres-server psql -U postgres -d postgres -t -c "SHOW max_connections;" 2>/dev/null | tr -d ' ' || echo "")

if [ -n "$current_max_conn" ]; then
    print_info "当前 max_connections: $current_max_conn"
else
    print_warning "无法获取当前 max_connections 配置"
fi

# 重启容器
print_info "正在重启 PostgreSQL 容器以使配置生效..."
if docker restart postgres-server; then
    print_success "PostgreSQL 容器已重启"
else
    print_error "重启 PostgreSQL 容器失败"
    exit 1
fi

# 等待容器启动
print_info "等待 PostgreSQL 服务就绪..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec postgres-server pg_isready -U postgres > /dev/null 2>&1; then
        print_success "PostgreSQL 服务已就绪"
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
done

if [ $attempt -ge $max_attempts ]; then
    print_error "PostgreSQL 服务启动超时"
    exit 1
fi

# 验证配置
print_info "验证 max_connections 配置..."
sleep 3
new_max_conn=$(docker exec postgres-server psql -U postgres -d postgres -t -c "SHOW max_connections;" 2>/dev/null | tr -d ' ' || echo "")

if [ -n "$new_max_conn" ]; then
    if [ "$new_max_conn" = "10240" ]; then
        print_success "max_connections 配置已生效: $new_max_conn"
    else
        print_warning "max_connections 配置为: $new_max_conn（期望值: 10240）"
        print_info "如果配置未生效，请检查 docker-compose.yml 中的 command 参数"
    fi
else
    print_warning "无法验证 max_connections 配置"
fi

# 显示连接统计信息
print_info "当前数据库连接统计:"
docker exec postgres-server psql -U postgres -d postgres -c "SELECT count(*) as current_connections, max_conn as max_connections, max_conn - count(*) as available_connections FROM pg_stat_activity, (SELECT setting::int as max_conn FROM pg_settings WHERE name = 'max_connections') as max_conn_settings GROUP BY max_conn;" 2>/dev/null || print_warning "无法获取连接统计信息"

print_success "配置应用完成！"

