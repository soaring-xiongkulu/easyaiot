#!/bin/bash
#
# PostgreSQL pg_hba.conf 修复脚本
# 用于修复 "no pg_hba.conf entry for host" 连接错误
#
# 使用方法：
#     bash fix_postgresql_pg_hba.sh [--check-only] [--force]
#
# 选项：
#     --check-only    仅检查配置，不进行修改
#     --force         强制重新添加配置（即使已存在）
#
# @author 翱翔的雄库鲁
# @email andywebjava@163.com
# @wechat EasyAIoT2025

# 不使用 set -e，以便更好地处理错误
set -o pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
POSTGRES_CONTAINER="postgres-server"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="iot45722414822"
POSTGRES_DB="iot-video20"

# 从环境变量或.env文件获取配置
if [ -f .env ]; then
    # 提取 DATABASE_URL 中的配置
    DATABASE_URL=$(grep -E '^DATABASE_URL=' .env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
    if [ -n "$DATABASE_URL" ]; then
        # 解析 postgresql://user:password@host:port/database
        if echo "$DATABASE_URL" | grep -q "postgresql://"; then
            DB_PART=$(echo "$DATABASE_URL" | sed 's|postgresql://||')
            if echo "$DB_PART" | grep -q "@"; then
                USER_PASS=$(echo "$DB_PART" | cut -d'@' -f1)
                POSTGRES_USER=$(echo "$USER_PASS" | cut -d':' -f1)
                POSTGRES_PASSWORD=$(echo "$USER_PASS" | cut -d':' -f2)
            fi
            HOST_DB=$(echo "$DB_PART" | cut -d'@' -f2-)
            if echo "$HOST_DB" | grep -q "/"; then
                POSTGRES_DB=$(echo "$HOST_DB" | cut -d'/' -f2 | cut -d'?' -f1)
            fi
        fi
    fi
fi

# 解析命令行参数
CHECK_ONLY=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            echo -e "${YELLOW}未知参数: $1${NC}"
            shift
            ;;
    esac
done

# 打印函数
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
    print_info "检查 Docker 服务状态..."
    if ! docker ps &> /dev/null; then
        print_error "无法访问 Docker，请确保 Docker 服务正在运行"
        return 1
    fi
    print_success "Docker 服务正在运行"
    return 0
}

# 检查 PostgreSQL 容器
check_postgres_container() {
    print_info "检查 PostgreSQL 容器状态..."
    
    # 检查容器是否存在
    if ! docker ps -a --filter "name=$POSTGRES_CONTAINER" --format "{{.Names}}" | grep -q "$POSTGRES_CONTAINER"; then
        print_error "PostgreSQL 容器 '$POSTGRES_CONTAINER' 不存在"
        print_info "请先启动 PostgreSQL 容器"
        return 1
    fi
    
    # 检查容器是否在运行
    container_status=$(docker ps --filter "name=$POSTGRES_CONTAINER" --format "{{.Status}}" 2>/dev/null | head -1 || echo "")
    if [ -z "$container_status" ]; then
        print_warning "PostgreSQL 容器存在但未运行"
        if [ "$CHECK_ONLY" = false ]; then
            print_info "正在启动容器..."
            if docker start "$POSTGRES_CONTAINER" > /dev/null 2>&1; then
                print_info "等待容器启动..."
                sleep 5
                container_status=$(docker ps --filter "name=$POSTGRES_CONTAINER" --format "{{.Status}}" 2>/dev/null | head -1 || echo "")
            else
                print_error "无法启动容器"
                return 1
            fi
        else
            return 1
        fi
    fi
    
    if [ -n "$container_status" ]; then
        print_success "PostgreSQL 容器正在运行"
        print_info "容器状态: $container_status"
        return 0
    else
        print_error "PostgreSQL 容器无法启动"
        return 1
    fi
}

# 等待 PostgreSQL 服务就绪
wait_for_postgresql() {
    print_info "等待 PostgreSQL 服务就绪..."
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker exec "$POSTGRES_CONTAINER" pg_isready -U "$POSTGRES_USER" > /dev/null 2>&1; then
            print_success "PostgreSQL 服务已就绪"
            return 0
        fi
        attempt=$((attempt + 1))
        if [ $((attempt % 5)) -eq 0 ]; then
            print_info "等待中... ($attempt/$max_attempts)"
        fi
        sleep 2
    done
    
    print_error "PostgreSQL 服务未就绪"
    return 1
}

# 获取 PostgreSQL 实际使用的 pg_hba.conf 路径
get_pg_hba_path() {
    print_info "查找 PostgreSQL pg_hba.conf 文件路径..."
    
    # 方法1: 通过 PostgreSQL 查询
    hba_file=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -t -A -c "SHOW hba_file;" 2>/dev/null | head -1 | tr -d ' ' || echo "")
    
    if [ -n "$hba_file" ] && [ "$hba_file" != "" ]; then
        print_success "找到 pg_hba.conf 文件: $hba_file"
        echo "$hba_file"
        return 0
    fi
    
    # 方法2: 尝试常见路径
    common_paths=(
        "/var/lib/postgresql/data/pgdata/pg_hba.conf"
        "/var/lib/postgresql/data/pg_hba.conf"
        "/var/lib/postgresql/pg_hba.conf"
    )
    
    for path in "${common_paths[@]}"; do
        if docker exec "$POSTGRES_CONTAINER" test -f "$path" 2>/dev/null; then
            print_success "找到 pg_hba.conf 文件: $path"
            echo "$path"
            return 0
        fi
    done
    
    print_error "无法找到 pg_hba.conf 文件"
    return 1
}

# 检查是否已配置允许所有主机连接
check_pg_hba_config() {
    local pg_hba_path="$1"
    
    print_info "检查 pg_hba.conf 配置..."
    
    # 检查是否已有允许所有主机连接的配置
    has_host_all=$(docker exec "$POSTGRES_CONTAINER" grep -E "^host\s+all\s+all\s+0\.0\.0\.0/0\s+md5" "$pg_hba_path" 2>/dev/null || echo "")
    has_host_ipv6=$(docker exec "$POSTGRES_CONTAINER" grep -E "^host\s+all\s+all\s+::/0\s+md5" "$pg_hba_path" 2>/dev/null || echo "")
    
    if [ -n "$has_host_all" ] && [ -n "$has_host_ipv6" ]; then
        print_success "pg_hba.conf 已包含允许所有主机连接的配置"
        return 0
    else
        print_warning "pg_hba.conf 缺少允许所有主机连接的配置"
        if [ -z "$has_host_all" ]; then
            print_info "缺少 IPv4 配置 (0.0.0.0/0)"
        fi
        if [ -z "$has_host_ipv6" ]; then
            print_info "缺少 IPv6 配置 (::/0)"
        fi
        return 1
    fi
}

# 添加 pg_hba.conf 配置
add_pg_hba_config() {
    local pg_hba_path="$1"
    
    print_info "添加允许所有主机连接的配置到 pg_hba.conf..."
    
    # 备份原文件
    local backup_path="${pg_hba_path}.backup.$(date +%Y%m%d_%H%M%S)"
    if docker exec "$POSTGRES_CONTAINER" cp "$pg_hba_path" "$backup_path" 2>/dev/null; then
        print_success "已备份 pg_hba.conf 到: $backup_path"
    else
        print_warning "无法备份 pg_hba.conf，继续执行..."
    fi
    
    # 检查是否已存在配置（避免重复添加）
    if [ "$FORCE" = false ]; then
        if check_pg_hba_config "$pg_hba_path"; then
            print_info "配置已存在，跳过添加"
            return 0
        fi
    fi
    
    # 添加配置
    # 方法1: 使用 echo 命令追加（以 postgres 用户执行）
    if docker exec -u postgres "$POSTGRES_CONTAINER" sh -c "
        echo '' >> '$pg_hba_path' && \
        echo '# 允许从宿主机和所有网络连接（由修复脚本自动添加）' >> '$pg_hba_path' && \
        echo 'host    all             all             0.0.0.0/0               md5' >> '$pg_hba_path' && \
        echo 'host    all             all             ::/0                    md5' >> '$pg_hba_path'
    " 2>/dev/null; then
        print_success "已添加配置到 pg_hba.conf"
        return 0
    fi
    
    # 方法2: 使用临时文件（备用方法）
    print_warning "方法1失败，尝试使用临时文件方法..."
    local temp_file=$(mktemp)
    cat > "$temp_file" << 'EOF'

# 允许从宿主机和所有网络连接（由修复脚本自动添加）
host    all             all             0.0.0.0/0               md5
host    all             all             ::/0                    md5
EOF
    
    if docker cp "$temp_file" "$POSTGRES_CONTAINER:/tmp/pg_hba_append.conf" 2>/dev/null && \
       docker exec -u postgres "$POSTGRES_CONTAINER" sh -c "cat /tmp/pg_hba_append.conf >> '$pg_hba_path' && rm /tmp/pg_hba_append.conf" 2>/dev/null; then
        print_success "已通过临时文件添加配置"
        rm -f "$temp_file"
        return 0
    else
        print_error "无法添加配置到 pg_hba.conf"
        rm -f "$temp_file"
        return 1
    fi
}

# 重新加载 PostgreSQL 配置
reload_postgresql_config() {
    print_info "重新加载 PostgreSQL 配置..."
    
    if docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -c "SELECT pg_reload_conf();" > /dev/null 2>&1; then
        print_success "PostgreSQL 配置已重新加载"
        return 0
    else
        print_error "无法重新加载 PostgreSQL 配置"
        print_warning "您可能需要重启 PostgreSQL 容器才能使配置生效"
        return 1
    fi
}

# 验证连接
test_connection() {
    print_info "测试数据库连接..."
    
    # 检查 psql 是否可用
    if ! command -v psql &> /dev/null; then
        print_warning "psql 命令不可用，跳过连接测试"
        return 0
    fi
    
    # 测试连接
    export PGPASSWORD="$POSTGRES_PASSWORD"
    if psql -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" > /dev/null 2>&1; then
        print_success "数据库连接测试成功"
        unset PGPASSWORD
        return 0
    else
        print_warning "数据库连接测试失败（这可能是因为其他原因）"
        unset PGPASSWORD
        return 1
    fi
}

# 显示配置信息
show_config_info() {
    local pg_hba_path="$1"
    
    print_section "当前 pg_hba.conf 配置（最后10行）"
    if docker exec "$POSTGRES_CONTAINER" test -f "$pg_hba_path" 2>/dev/null; then
        docker exec "$POSTGRES_CONTAINER" sh -c "tail -10 '$pg_hba_path'" 2>/dev/null || print_warning "无法读取配置（可能权限问题）"
    else
        print_error "配置文件不存在: $pg_hba_path"
    fi
    echo ""
}

# 主函数
main() {
    print_section "PostgreSQL pg_hba.conf 修复工具"
    
    print_info "PostgreSQL 容器: $POSTGRES_CONTAINER"
    print_info "PostgreSQL 用户: $POSTGRES_USER"
    print_info "PostgreSQL 数据库: $POSTGRES_DB"
    echo ""
    
    # 检查 Docker
    if ! check_docker; then
        exit 1
    fi
    
    # 检查 PostgreSQL 容器
    if ! check_postgres_container; then
        exit 1
    fi
    
    # 等待 PostgreSQL 就绪
    if ! wait_for_postgresql; then
        exit 1
    fi
    
    # 获取 pg_hba.conf 路径
    pg_hba_path=$(get_pg_hba_path 2>&1 | tail -1)  # 只取最后一行（路径）
    if [ -z "$pg_hba_path" ] || [ ! -z "$(echo "$pg_hba_path" | grep -E '\[INFO\]|\[SUCCESS\]|\[ERROR\]')" ]; then
        # 如果返回值包含日志信息，重新获取
        pg_hba_path=$(docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -t -A -c "SHOW hba_file;" 2>/dev/null | head -1 | tr -d ' ' || echo "")
        if [ -z "$pg_hba_path" ]; then
            pg_hba_path="/var/lib/postgresql/data/pgdata/pg_hba.conf"
        fi
    fi
    
    if [ -z "$pg_hba_path" ]; then
        print_error "无法确定 pg_hba.conf 文件路径"
        exit 1
    fi
    
    echo ""  # 空行分隔
    
    # 显示当前配置
    show_config_info "$pg_hba_path"
    
    # 检查配置
    if check_pg_hba_config "$pg_hba_path"; then
        print_success "配置检查通过，无需修复"
        if [ "$CHECK_ONLY" = false ]; then
            test_connection
        fi
        exit 0
    fi
    
    # 如果只是检查，退出
    if [ "$CHECK_ONLY" = true ]; then
        print_warning "配置检查未通过，但 --check-only 模式，不进行修复"
        exit 1
    fi
    
    # 添加配置
    if ! add_pg_hba_config "$pg_hba_path"; then
        exit 1
    fi
    
    # 显示更新后的配置
    echo ""
    show_config_info "$pg_hba_path"
    
    # 重新加载配置
    if ! reload_postgresql_config; then
        print_warning "配置已添加，但重新加载失败"
        print_info "建议重启 PostgreSQL 容器: docker restart $POSTGRES_CONTAINER"
    fi
    
    # 验证连接
    echo ""
    test_connection
    
    print_section "修复完成"
    print_success "PostgreSQL pg_hba.conf 配置已修复"
    print_info "如果仍有连接问题，请检查："
    print_info "  1. PostgreSQL 容器是否正常运行"
    print_info "  2. 端口 5432 是否已映射到宿主机"
    print_info "  3. 防火墙设置是否允许连接"
    echo ""
}

# 运行主函数
main "$@"

