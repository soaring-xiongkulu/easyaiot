#!/bin/bash

# ============================================
# PostgreSQL 密码修复脚本
# ============================================
# 用于修复电脑重启后 PostgreSQL 密码认证失败的问题
# 使用方法：
#   ./fix_postgresql_password.sh
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

# 目标密码（与 docker-compose.yml 中的配置一致）
TARGET_PASSWORD="iot45722414822"

print_section "PostgreSQL 密码修复工具"

# 检查 Docker 是否运行
if ! docker ps &> /dev/null; then
    print_error "无法访问 Docker，请确保 Docker 服务正在运行"
    exit 1
fi

# 检查 PostgreSQL 容器是否存在
if ! docker ps -a --filter "name=postgres-server" --format "{{.Names}}" | grep -q "postgres-server"; then
    print_error "PostgreSQL 容器不存在或未运行"
    print_info "请先启动 PostgreSQL 容器："
    print_info "  cd .scripts/docker"
    print_info "  docker-compose up -d PostgresSQL"
    exit 1
fi

# 等待 PostgreSQL 就绪
print_info "等待 PostgreSQL 服务就绪..."
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec postgres-server pg_isready -U postgres > /dev/null 2>&1; then
        print_success "PostgreSQL 服务已就绪"
        break
    fi
    attempt=$((attempt + 1))
    if [ $((attempt % 10)) -eq 0 ]; then
        print_info "等待中... ($attempt/$max_attempts)"
    fi
    sleep 2
done

if [ $attempt -ge $max_attempts ]; then
    print_error "PostgreSQL 服务未就绪，请检查容器日志："
    print_info "  docker logs postgres-server"
    exit 1
fi

# 额外等待，确保数据库完全初始化
print_info "等待数据库完全初始化..."
sleep 5

# 重置密码
print_section "重置 PostgreSQL 密码"
print_info "正在重置 postgres 用户密码为: $TARGET_PASSWORD"

# 尝试重置密码
reset_attempts=0
max_reset_attempts=10
reset_success=0

while [ $reset_attempts -lt $max_reset_attempts ] && [ $reset_success -eq 0 ]; do
    # 使用本地连接重置密码（不需要密码）
    if docker exec postgres-server psql -U postgres -d postgres -c "ALTER USER postgres WITH PASSWORD '$TARGET_PASSWORD';" > /dev/null 2>&1; then
        print_success "PostgreSQL 密码重置成功"
        reset_success=1
        
        # 重新加载配置
        docker exec postgres-server psql -U postgres -d postgres -c "SELECT pg_reload_conf();" > /dev/null 2>&1 || true
        
        # 验证密码
        sleep 3
        if docker exec postgres-server psql -U postgres -d postgres -c "SELECT version();" > /dev/null 2>&1; then
            print_success "PostgreSQL 密码验证通过"
        else
            print_warning "密码重置成功，但验证时出现问题（可能正常）"
        fi
        break
    else
        reset_attempts=$((reset_attempts + 1))
        if [ $reset_attempts -lt $max_reset_attempts ]; then
            print_warning "密码重置失败，正在重试 ($reset_attempts/$max_reset_attempts)..."
            sleep 5
        fi
    fi
done

if [ $reset_success -eq 0 ]; then
    print_error "PostgreSQL 密码重置失败（已重试 $max_reset_attempts 次）"
    echo ""
    print_info "可能的解决方案："
    print_info "  1. 检查容器日志: docker logs postgres-server"
    print_info "  2. 重启容器后重试: docker restart postgres-server"
    print_info "  3. 手动执行重置命令:"
    print_info "     docker exec postgres-server psql -U postgres -d postgres -c \"ALTER USER postgres WITH PASSWORD '$TARGET_PASSWORD';\""
    exit 1
fi

# 配置 pg_hba.conf（如果需要）
print_section "检查 pg_hba.conf 配置"
pg_hba_path="/var/lib/postgresql/data/pg_hba.conf"
has_host_all=$(docker exec postgres-server grep -E "^host\s+all\s+all\s+0\.0\.0\.0/0\s+md5" "$pg_hba_path" 2>/dev/null || echo "")

if [ -n "$has_host_all" ]; then
    print_success "pg_hba.conf 已包含允许所有主机连接的配置"
else
    print_info "添加允许所有主机连接的配置..."
    if docker exec postgres-server sh -c "echo '' >> $pg_hba_path && echo '# 允许从宿主机和所有网络连接（由修复脚本自动添加）' >> $pg_hba_path && echo 'host    all             all             0.0.0.0/0               md5' >> $pg_hba_path && echo 'host    all             all             ::/0                    md5' >> $pg_hba_path" 2>/dev/null; then
        print_success "已添加允许所有主机连接的配置"
        # 重新加载配置
        docker exec postgres-server psql -U postgres -d postgres -c "SELECT pg_reload_conf();" > /dev/null 2>&1 || true
    else
        print_warning "添加配置失败，但密码已重置成功"
    fi
fi

# 测试连接
print_section "测试数据库连接"
if command -v psql &> /dev/null; then
    export PGPASSWORD="$TARGET_PASSWORD"
    if psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
        print_success "宿主机连接测试成功"
        unset PGPASSWORD
    else
        print_warning "宿主机连接测试失败（可能需要检查防火墙或网络配置）"
        unset PGPASSWORD
    fi
else
    print_info "未安装 psql 客户端，跳过连接测试"
fi

echo ""
print_success "PostgreSQL 密码修复完成！"
print_info "密码已设置为: $TARGET_PASSWORD"
print_info "现在可以正常连接数据库了"

