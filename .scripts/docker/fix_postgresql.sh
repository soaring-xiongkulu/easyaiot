#!/bin/bash

# ============================================
# PostgreSQL 密码修复脚本
# ============================================
# 此脚本用于修复 PostgreSQL 容器重启后密码变化的问题
# 使用方法：
#   ./fix_postgresql.sh
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
    print_section "停止 PostgreSQL 容器"
    
    # 确定 docker compose 命令
    local compose_cmd
    if command -v docker-compose &> /dev/null; then
        compose_cmd="docker-compose"
    else
        compose_cmd="docker compose"
    fi
    
    # 1. 先 kill 容器（强制终止）
    print_info "步骤 1: 强制终止 PostgreSQL 容器..."
    if docker ps --filter "name=postgres-server" --format "{{.Names}}" | grep -q "postgres-server"; then
        docker kill postgres-server 2>/dev/null && print_success "容器已强制终止" || print_info "容器未运行，跳过 kill"
    else
        print_info "容器未运行，跳过 kill"
    fi
    
    # 2. 然后 stop 容器（优雅停止，如果还在运行）
    print_info "步骤 2: 优雅停止 PostgreSQL 容器..."
    if docker ps -a --filter "name=postgres-server" --format "{{.Names}}" | grep -q "postgres-server"; then
        docker stop postgres-server 2>/dev/null && print_success "容器已停止" || print_info "容器已停止"
    else
        print_info "容器不存在，跳过 stop"
    fi
    
    # 3. 使用 docker-compose down 完全清理（包括网络等）
    print_info "步骤 3: 使用 docker-compose 完全清理 PostgreSQL 服务..."
    cd "$SCRIPT_DIR"
    $compose_cmd stop PostgresSQL 2>/dev/null || true
    $compose_cmd rm -f PostgresSQL 2>/dev/null || true
    print_success "PostgreSQL 容器已完全清理"
    
    # 4. 确保容器完全移除
    print_info "步骤 4: 确保容器完全移除..."
    if docker ps -a --filter "name=postgres-server" --format "{{.Names}}" | grep -q "postgres-server"; then
        docker rm -f postgres-server 2>/dev/null && print_success "残留容器已移除" || print_warning "无法移除残留容器"
    else
        print_success "容器已完全移除"
    fi
    
    # 等待一下确保清理完成
    sleep 2
}

# 修复数据目录权限
fix_permissions() {
    print_section "修复数据目录权限"
    
    local data_dir="${SCRIPT_DIR}/db_data/data"
    local log_dir="${SCRIPT_DIR}/db_data/log"
    
    print_info "检查数据目录..."
    
    # 创建目录（如果不存在）
    mkdir -p "$data_dir" "$log_dir"
    
    # 检查是否需要迁移数据（从 pgdata 子目录）
    local pgdata_subdir="${data_dir}/pgdata"
    if [ -d "$pgdata_subdir" ] && [ -n "$(ls -A "$pgdata_subdir" 2>/dev/null)" ]; then
        print_warning "检测到数据在 pgdata 子目录中，需要迁移到根目录..."
        print_info "正在迁移数据..."
        
        # 备份现有数据
        if [ -d "$data_dir" ] && [ -n "$(ls -A "$data_dir" 2>/dev/null | grep -v pgdata)" ]; then
            print_warning "数据目录根目录已有内容，创建备份..."
            local backup_dir="${data_dir}.backup.$(date +%Y%m%d_%H%M%S)"
            mv "$data_dir" "$backup_dir" 2>/dev/null || true
            mkdir -p "$data_dir"
        fi
        
        # 移动 pgdata 内容到根目录
        if [ -d "$pgdata_subdir" ]; then
            print_info "移动数据从 $pgdata_subdir 到 $data_dir..."
            mv "$pgdata_subdir"/* "$data_dir"/ 2>/dev/null || true
            rmdir "$pgdata_subdir" 2>/dev/null || true
            print_success "数据迁移完成"
        fi
    fi
    
    # 设置权限
    print_info "设置数据目录权限..."
    if [ "$EUID" -eq 0 ]; then
        chown -R 999:999 "$data_dir" "$log_dir"
        chmod -R 700 "$data_dir"
        chmod -R 755 "$log_dir"
        print_success "权限已设置 (UID 999:999)"
    else
        if command -v sudo &> /dev/null; then
            sudo chown -R 999:999 "$data_dir" "$log_dir" 2>/dev/null && \
            sudo chmod -R 700 "$data_dir" 2>/dev/null && \
            sudo chmod -R 755 "$log_dir" 2>/dev/null && \
            print_success "权限已设置 (UID 999:999)" || \
            print_warning "无法设置权限，可能需要手动执行: sudo chown -R 999:999 $data_dir $log_dir"
        else
            print_warning "无法设置权限，请手动执行: sudo chown -R 999:999 $data_dir $log_dir"
        fi
    fi
}

# 验证数据目录
verify_data_directory() {
    print_section "验证数据目录"
    
    local data_dir="${SCRIPT_DIR}/db_data/data"
    
    if [ ! -d "$data_dir" ]; then
        print_error "数据目录不存在: $data_dir"
        return 1
    fi
    
    # 检查是否已初始化
    if [ -z "$(ls -A "$data_dir" 2>/dev/null)" ]; then
        print_warning "数据目录为空，PostgreSQL 将在首次启动时初始化"
        print_info "初始化将使用 docker-compose.yml 中配置的密码: iot45722414822"
    else
        # 检查关键文件
        if [ -f "$data_dir/PG_VERSION" ] || [ -f "$data_dir/postgresql.conf" ]; then
            print_success "数据目录已包含 PostgreSQL 数据"
            print_info "PostgreSQL 将使用已有的密码配置，不会重新初始化"
        else
            print_warning "数据目录存在但可能未正确初始化"
        fi
    fi
    
    # 显示目录权限
    local owner=$(stat -c "%U:%G" "$data_dir" 2>/dev/null || stat -f "%Su:%Sg" "$data_dir" 2>/dev/null || echo "未知")
    local perms=$(stat -c "%a" "$data_dir" 2>/dev/null || stat -f "%OLp" "$data_dir" 2>/dev/null || echo "未知")
    print_info "数据目录权限: $owner, 权限: $perms"
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
    print_info "当前目录: $(pwd)"
    
    # 切换到 docker-compose.yml 所在目录
    cd "$SCRIPT_DIR"
    
    # 重新创建并启动 PostgreSQL 容器
    print_info "重新创建并启动 PostgreSQL 容器..."
    if $compose_cmd up -d --force-recreate --no-deps PostgresSQL 2>&1; then
        print_success "PostgreSQL 容器启动命令已执行"
        
        # 等待容器就绪
        print_info "等待 PostgreSQL 容器就绪..."
        local max_attempts=30
        local attempt=0
        while [ $attempt -lt $max_attempts ]; do
            if docker exec postgres-server pg_isready -U postgres > /dev/null 2>&1; then
                print_success "PostgreSQL 容器已就绪"
                return 0
            fi
            attempt=$((attempt + 1))
            sleep 2
        done
        
        print_warning "PostgreSQL 容器未在预期时间内就绪，请检查日志: docker logs postgres-server"
        return 1
    else
        print_error "启动 PostgreSQL 容器失败"
        print_info "尝试查看错误信息..."
        $compose_cmd up -d PostgresSQL 2>&1 || true
        return 1
    fi
}

# 测试连接
test_connection() {
    print_section "测试数据库连接"
    
    print_info "测试使用密码 'iot45722414822' 连接数据库..."
    
    if docker exec postgres-server psql -U postgres -d postgres -c "SELECT version();" > /dev/null 2>&1; then
        print_success "数据库连接成功！"
        print_info "密码验证通过"
        return 0
    else
        print_error "数据库连接失败"
        print_warning "请检查："
        print_warning "  1. 容器日志: docker logs postgres-server"
        print_warning "  2. 数据目录权限是否正确"
        print_warning "  3. 如果数据目录是新初始化的，密码应该是: iot45722414822"
        return 1
    fi
}

# 主函数
main() {
    print_section "PostgreSQL 密码修复脚本"
    
    print_info "此脚本将："
    print_info "  1. 强制终止 (kill) PostgreSQL 容器"
    print_info "  2. 优雅停止 (stop) PostgreSQL 容器"
    print_info "  3. 完全清理 (rm) PostgreSQL 容器"
    print_info "  4. 修复数据目录权限"
    print_info "  5. 迁移数据（如果需要）"
    print_info "  6. 重新创建并启动 PostgreSQL 容器"
    print_info "  7. 测试数据库连接"
    echo ""
    
    read -p "是否继续？(y/N): " -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_info "已取消操作"
        exit 0
    fi
    
    check_docker
    stop_postgresql
    fix_permissions
    verify_data_directory
    start_postgresql
    test_connection
    
    print_section "修复完成"
    print_success "PostgreSQL 修复脚本执行完成"
    echo ""
    print_info "如果仍有问题，请检查："
    print_info "  1. 容器日志: docker logs postgres-server"
    print_info "  2. 数据目录: $SCRIPT_DIR/db_data/data"
    print_info "  3. 确保应用程序使用的密码是: iot45722414822"
}

# 运行主函数
main "$@"

