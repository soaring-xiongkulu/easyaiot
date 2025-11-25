#!/bin/bash

# ============================================
# PostgreSQL 密码重置脚本
# ============================================
# 此脚本用于重置 PostgreSQL 密码
# 使用方法：
#   ./reset_postgresql_password.sh
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

# 目标密码（从docker-compose.yml中读取）
TARGET_PASSWORD="iot45722414822"

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

# 检查 Docker 是否运行
check_docker() {
    if ! docker info &> /dev/null; then
        print_error "Docker daemon 未运行或无法访问"
        exit 1
    fi
}

# 检查容器是否运行
check_container() {
    if ! docker ps --filter "name=postgres-server" --format "{{.Names}}" | grep -q "postgres-server"; then
        print_error "PostgreSQL 容器未运行，请先启动容器"
        exit 1
    fi
}

# 等待PostgreSQL就绪
wait_for_postgresql() {
    print_info "等待 PostgreSQL 就绪..."
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker exec postgres-server pg_isready -U postgres > /dev/null 2>&1; then
            print_success "PostgreSQL 已就绪"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    print_error "PostgreSQL 未在预期时间内就绪"
    return 1
}

# 重置密码
reset_password() {
    print_section "重置 PostgreSQL 密码"
    
    print_info "正在重置 postgres 用户密码为: $TARGET_PASSWORD"
    
    # 尝试通过容器内部重置密码（不需要密码）
    if docker exec postgres-server psql -U postgres -d postgres -c "ALTER USER postgres WITH PASSWORD '$TARGET_PASSWORD';" > /dev/null 2>&1; then
        print_success "密码重置成功（通过容器内部）"
        return 0
    fi
    
    # 如果失败，尝试通过trust模式连接
    print_warning "通过容器内部重置失败，尝试其他方法..."
    
    # 检查pg_hba.conf配置
    local pg_hba_content=$(docker exec postgres-server cat /var/lib/postgresql/data/pg_hba.conf 2>/dev/null || echo "")
    
    if echo "$pg_hba_content" | grep -q "127.0.0.1/32.*trust"; then
        print_info "检测到 trust 模式配置，尝试通过本地连接重置..."
        # 这里可能需要修改pg_hba.conf或使用其他方法
    fi
    
    print_error "无法重置密码，请检查容器日志: docker logs postgres-server"
    return 1
}

# 验证密码
verify_password() {
    print_section "验证密码"
    
    print_info "测试使用新密码连接数据库..."
    
    # 通过容器内部测试（不需要密码）
    if docker exec postgres-server psql -U postgres -d postgres -c "SELECT version();" > /dev/null 2>&1; then
        print_success "容器内部连接成功"
    else
        print_warning "容器内部连接失败"
    fi
    
    # 测试外部连接
    if command -v psql &> /dev/null; then
        export PGPASSWORD="$TARGET_PASSWORD"
        if psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
            print_success "外部连接成功！密码验证通过"
            unset PGPASSWORD
            return 0
        else
            print_warning "外部连接失败，但容器内部连接正常"
            print_info "这可能是 pg_hba.conf 配置问题"
            unset PGPASSWORD
        fi
    else
        print_warning "未安装 psql 客户端，跳过外部连接测试"
    fi
    
    return 0
}

# 重新加载配置
reload_config() {
    print_info "重新加载 PostgreSQL 配置..."
    if docker exec postgres-server psql -U postgres -d postgres -c "SELECT pg_reload_conf();" > /dev/null 2>&1; then
        print_success "配置已重新加载"
        return 0
    else
        print_warning "无法重新加载配置"
        return 1
    fi
}

# 主函数
main() {
    print_section "PostgreSQL 密码重置脚本"
    
    print_info "目标密码: $TARGET_PASSWORD"
    echo ""
    
    check_docker
    check_container
    wait_for_postgresql
    reset_password
    reload_config
    sleep 2
    verify_password
    
    print_section "完成"
    print_success "密码重置脚本执行完成"
    echo ""
    print_info "如果外部连接仍然失败，可能需要："
    print_info "  1. 检查 pg_hba.conf 配置"
    print_info "  2. 重启 PostgreSQL 容器: docker-compose restart PostgresSQL"
    print_info "  3. 查看容器日志: docker logs postgres-server"
}

# 运行主函数
main "$@"

