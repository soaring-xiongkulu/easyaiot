#!/bin/bash

# ============================================
# PostgreSQL 权限修复脚本（快速修复）
# ============================================
# 此脚本用于快速修复 PostgreSQL 数据目录权限问题
# 解决 "could not open file global/pg_filenode.map: Permission denied" 错误
# 使用方法：
#   ./fix_postgresql_permissions.sh
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

# 检查 Docker 是否运行
check_docker() {
    if ! docker info &> /dev/null; then
        print_error "Docker daemon 未运行或无法访问"
        exit 1
    fi
}

# 停止 PostgreSQL 容器
stop_postgresql() {
    print_info "停止 PostgreSQL 容器..."
    if docker ps --filter "name=postgres-server" --format "{{.Names}}" | grep -q "postgres-server"; then
        docker stop postgres-server 2>/dev/null || true
        print_success "PostgreSQL 容器已停止"
        sleep 2
    else
        print_info "PostgreSQL 容器未运行"
    fi
}

# 修复数据目录权限
fix_permissions() {
    print_section "修复数据目录权限"
    
    local data_dir="${SCRIPT_DIR}/db_data/data"
    local log_dir="${SCRIPT_DIR}/db_data/log"
    
    print_info "数据目录: $data_dir"
    print_info "日志目录: $log_dir"
    
    # 创建目录（如果不存在）
    mkdir -p "$data_dir" "$log_dir"
    
    # 检查当前权限
    if [ -d "$data_dir" ]; then
        local owner=$(stat -c "%U:%G (%u:%g)" "$data_dir" 2>/dev/null || stat -f "%Su:%Sg" "$data_dir" 2>/dev/null || echo "未知")
        local perms=$(stat -c "%a" "$data_dir" 2>/dev/null || stat -f "%OLp" "$data_dir" 2>/dev/null || echo "未知")
        print_info "当前数据目录权限: $owner, 权限: $perms"
    fi
    
    # 设置权限（PostgreSQL 容器使用 UID 999）
    print_info "设置数据目录权限为 999:999..."
    
    if [ "$EUID" -eq 0 ]; then
        # 以 root 运行
        chown -R 999:999 "$data_dir" "$log_dir" 2>/dev/null || true
        chmod -R 700 "$data_dir" 2>/dev/null || true
        chmod -R 755 "$log_dir" 2>/dev/null || true
        print_success "权限已设置 (UID 999:999)"
    else
        # 需要 sudo
        if command -v sudo &> /dev/null; then
            print_info "使用 sudo 设置权限..."
            sudo chown -R 999:999 "$data_dir" "$log_dir" 2>/dev/null && \
            sudo chmod -R 700 "$data_dir" 2>/dev/null && \
            sudo chmod -R 755 "$log_dir" 2>/dev/null && \
            print_success "权限已设置 (UID 999:999)" || {
                print_error "无法设置权限"
                print_warning "请手动执行: sudo chown -R 999:999 $data_dir $log_dir"
                print_warning "然后执行: sudo chmod -R 700 $data_dir && sudo chmod -R 755 $log_dir"
                exit 1
            }
        else
            print_error "需要 root 权限或 sudo 来设置权限"
            print_warning "请手动执行: sudo chown -R 999:999 $data_dir $log_dir"
            print_warning "然后执行: sudo chmod -R 700 $data_dir && sudo chmod -R 755 $log_dir"
            exit 1
        fi
    fi
    
    # 验证权限
    if [ -d "$data_dir" ]; then
        local new_owner=$(stat -c "%U:%G (%u:%g)" "$data_dir" 2>/dev/null || stat -f "%Su:%Sg" "$data_dir" 2>/dev/null || echo "未知")
        local new_perms=$(stat -c "%a" "$data_dir" 2>/dev/null || stat -f "%OLp" "$data_dir" 2>/dev/null || echo "未知")
        print_info "修复后数据目录权限: $new_owner, 权限: $new_perms"
        
        # 检查是否是 999:999
        local uid=$(stat -c "%u" "$data_dir" 2>/dev/null || stat -f "%u" "$data_dir" 2>/dev/null || echo "")
        if [ "$uid" = "999" ]; then
            print_success "权限修复成功！"
        else
            print_warning "权限可能未正确设置，UID 应该是 999，当前是: $uid"
        fi
    fi
}

# 启动 PostgreSQL 容器
start_postgresql() {
    print_section "启动 PostgreSQL 容器"
    
    # 确定 docker compose 命令
    local compose_cmd
    if command -v docker-compose &> /dev/null; then
        compose_cmd="docker-compose"
    else
        compose_cmd="docker compose"
    fi
    
    print_info "使用命令: $compose_cmd"
    print_info "启动 PostgreSQL 容器..."
    
    if $compose_cmd up -d PostgresSQL 2>&1; then
        print_success "PostgreSQL 容器启动命令已执行"
        
        # 等待容器就绪
        print_info "等待 PostgreSQL 容器就绪（最多等待 60 秒）..."
        local max_attempts=30
        local attempt=0
        while [ $attempt -lt $max_attempts ]; do
            if docker exec postgres-server pg_isready -U postgres > /dev/null 2>&1; then
                print_success "PostgreSQL 容器已就绪"
                return 0
            fi
            attempt=$((attempt + 1))
            echo -n "."
            sleep 2
        done
        echo ""
        print_warning "PostgreSQL 容器未在预期时间内就绪"
        print_info "请检查日志: docker logs postgres-server"
        return 1
    else
        print_error "启动 PostgreSQL 容器失败"
        return 1
    fi
}

# 测试连接
test_connection() {
    print_section "测试数据库连接"
    
    print_info "测试数据库连接..."
    
    if docker exec postgres-server psql -U postgres -d postgres -c "SELECT version();" > /dev/null 2>&1; then
        print_success "数据库连接成功！"
        return 0
    else
        print_error "数据库连接失败"
        print_warning "请检查容器日志: docker logs postgres-server"
        return 1
    fi
}

# 主函数
main() {
    print_section "PostgreSQL 权限修复脚本"
    
    print_info "此脚本将修复 PostgreSQL 数据目录权限问题"
    print_info "解决 'could not open file global/pg_filenode.map: Permission denied' 错误"
    echo ""
    print_info "将执行以下操作："
    print_info "  1. 停止 PostgreSQL 容器"
    print_info "  2. 修复数据目录权限（设置为 999:999）"
    print_info "  3. 重新启动 PostgreSQL 容器"
    print_info "  4. 测试数据库连接"
    echo ""
    
    read -p "是否继续？(y/N): " -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_info "已取消操作"
        exit 0
    fi
    
    check_docker
    stop_postgresql
    fix_permissions
    start_postgresql
    test_connection
    
    print_section "修复完成"
    print_success "PostgreSQL 权限修复完成！"
    echo ""
    print_info "如果仍有问题，请检查："
    print_info "  1. 容器日志: docker logs postgres-server"
    print_info "  2. 数据目录权限: ls -la $SCRIPT_DIR/db_data/data"
    print_info "  3. 确保数据目录所有者是 999:999"
}

# 运行主函数
main "$@"

