#!/bin/bash

# ============================================
# PostgreSQL 连接测试脚本（Linux）
# ============================================
# 用于测试从宿主机连接 PostgreSQL 数据库
# 使用方法：
#   ./test_postgresql_connection.sh
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

# PostgreSQL 连接配置
DB_HOST="127.0.0.1"
DB_PORT="5432"
DB_USER="postgres"
DB_PASSWORD="iot45722414822"
DB_NAME="postgres"

print_section "PostgreSQL 连接测试工具"

# 检查 Docker 是否运行
print_info "检查 Docker 服务状态..."
if ! docker ps &> /dev/null; then
    print_error "无法访问 Docker，请确保 Docker 服务正在运行"
    exit 1
fi
print_success "Docker 服务正在运行"

# 检查 PostgreSQL 容器是否存在
print_info "检查 PostgreSQL 容器状态..."
if ! docker ps -a --filter "name=postgres-server" --format "{{.Names}}" | grep -q "postgres-server"; then
    print_error "PostgreSQL 容器不存在"
    print_info "请先启动 PostgreSQL 容器："
    print_info "  cd .scripts/docker"
    print_info "  docker-compose up -d PostgresSQL"
    exit 1
fi

# 检查容器是否在运行
container_status=$(docker ps --filter "name=postgres-server" --format "{{.Status}}" 2>/dev/null | head -1 || echo "")
if [ -z "$container_status" ]; then
    print_warning "PostgreSQL 容器存在但未运行"
    print_info "正在启动容器..."
    docker start postgres-server > /dev/null 2>&1 || {
        print_error "无法启动容器"
        exit 1
    }
    print_info "等待容器启动..."
    sleep 5
    container_status=$(docker ps --filter "name=postgres-server" --format "{{.Status}}" 2>/dev/null | head -1 || echo "")
fi

if [ -n "$container_status" ]; then
    print_success "PostgreSQL 容器正在运行"
    print_info "容器状态: $container_status"
else
    print_error "PostgreSQL 容器无法启动"
    exit 1
fi

# 等待 PostgreSQL 服务就绪（容器内）
print_info "等待 PostgreSQL 服务就绪（容器内）..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec postgres-server pg_isready -U postgres > /dev/null 2>&1; then
        print_success "PostgreSQL 服务已就绪（容器内）"
        break
    fi
    attempt=$((attempt + 1))
    if [ $((attempt % 5)) -eq 0 ]; then
        print_info "等待中... ($attempt/$max_attempts)"
    fi
    sleep 2
done

if [ $attempt -ge $max_attempts ]; then
    print_error "PostgreSQL 服务未就绪（容器内）"
    print_info "查看容器日志: docker logs postgres-server"
    exit 1
fi

# 检查端口是否监听
print_info "检查端口 $DB_PORT 是否监听..."
port_check_failed=0
if command -v ss &> /dev/null; then
    if ss -tlnp 2>/dev/null | grep -qE ":$DB_PORT[[:space:]]|:$DB_PORT$"; then
        port_info=$(ss -tlnp 2>/dev/null | grep -E ":$DB_PORT[[:space:]]|:$DB_PORT$" | head -1)
        print_success "端口 $DB_PORT 正在监听"
        print_info "端口信息: $port_info"
        
        # 检查是否是Docker容器监听的端口
        if echo "$port_info" | grep -q "docker"; then
            print_info "检测到 Docker 容器正在监听端口 $DB_PORT"
        else
            print_warning "端口 $DB_PORT 被非 Docker 进程占用"
            print_info "这可能导致 Docker 容器无法绑定该端口"
            print_info "检查是否有宿主机 PostgreSQL 服务正在运行..."
            if pgrep -f "postgres.*$DB_PORT" > /dev/null 2>&1 || pgrep -f "/usr/lib/postgresql" > /dev/null 2>&1; then
                print_error "检测到宿主机 PostgreSQL 服务正在运行并占用端口 $DB_PORT"
                print_info "解决方案："
                print_info "  1. 停止宿主机 PostgreSQL 服务: sudo systemctl stop postgresql"
                print_info "  2. 或者修改 docker-compose.yml 中的端口映射（如 5433:5432）"
                port_check_failed=1
            fi
        fi
    else
        print_warning "端口 $DB_PORT 未监听（可能无法从宿主机连接）"
    fi
elif command -v netstat &> /dev/null; then
    if netstat -tlnp 2>/dev/null | grep -qE ":$DB_PORT[[:space:]]|:$DB_PORT$"; then
        port_info=$(netstat -tlnp 2>/dev/null | grep -E ":$DB_PORT[[:space:]]|:$DB_PORT$" | head -1)
        print_success "端口 $DB_PORT 正在监听"
        print_info "端口信息: $port_info"
        
        # 检查是否是Docker容器监听的端口
        if echo "$port_info" | grep -q "docker"; then
            print_info "检测到 Docker 容器正在监听端口 $DB_PORT"
        else
            print_warning "端口 $DB_PORT 被非 Docker 进程占用"
            print_info "这可能导致 Docker 容器无法绑定该端口"
            print_info "检查是否有宿主机 PostgreSQL 服务正在运行..."
            if pgrep -f "postgres.*$DB_PORT" > /dev/null 2>&1 || pgrep -f "/usr/lib/postgresql" > /dev/null 2>&1; then
                print_error "检测到宿主机 PostgreSQL 服务正在运行并占用端口 $DB_PORT"
                print_info "解决方案："
                print_info "  1. 停止宿主机 PostgreSQL 服务: sudo systemctl stop postgresql"
                print_info "  2. 或者修改 docker-compose.yml 中的端口映射（如 5433:5432）"
                port_check_failed=1
            fi
        fi
    else
        print_warning "端口 $DB_PORT 未监听（可能无法从宿主机连接）"
    fi
else
    print_warning "无法检查端口状态（ss 或 netstat 命令不可用）"
fi

# 检查Docker容器的端口映射
print_info "检查 Docker 容器端口映射..."
container_ports=$(docker inspect postgres-server --format '{{json .HostConfig.PortBindings}}' 2>/dev/null || echo "{}")
if [ "$container_ports" != "{}" ] && [ -n "$container_ports" ]; then
    print_success "Docker 容器端口映射配置正常"
    echo "$container_ports" | python3 -m json.tool 2>/dev/null || echo "$container_ports"
else
    print_error "Docker 容器端口映射未配置或配置失败"
    print_info "可能的原因：端口 $DB_PORT 已被其他进程占用"
    if [ $port_check_failed -eq 0 ]; then
        print_info "建议检查："
        print_info "  1. 是否有其他 PostgreSQL 实例正在运行"
        print_info "  2. 运行: docker logs postgres-server 查看容器启动日志"
    fi
fi

# 测试连接（方法1: 使用 psql 客户端）
print_section "测试数据库连接"

if command -v psql &> /dev/null; then
    print_info "使用 psql 客户端测试连接..."
    export PGPASSWORD="$DB_PASSWORD"
    
    # 测试基本连接
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
        print_success "psql 连接测试成功"
        
        # 获取 PostgreSQL 版本信息
        version_info=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT version();" 2>/dev/null | head -1 | xargs)
        print_info "PostgreSQL 版本: $version_info"
        
        # 测试查询
        print_info "执行测试查询..."
        result=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT 1 as test_value, current_database() as database, current_user as user;" 2>/dev/null | head -1 | xargs)
        if [ -n "$result" ]; then
            print_success "查询测试成功"
            print_info "查询结果: $result"
        fi
        
        # 列出所有数据库
        print_info "列出所有数据库..."
        databases=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;" 2>/dev/null | xargs)
        if [ -n "$databases" ]; then
            print_success "数据库列表:"
            echo "$databases" | tr ' ' '\n' | while read -r db; do
                if [ -n "$db" ]; then
                    echo "  - $db"
                fi
            done
        fi
        
        unset PGPASSWORD
    else
        print_error "psql 连接测试失败"
        unset PGPASSWORD
        
        # 尝试诊断问题
        print_info "诊断连接问题..."
        
        # 检查密码是否正确
        print_info "测试密码是否正确（通过容器内连接）..."
        if docker exec postgres-server psql -U postgres -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
            print_success "容器内连接正常"
            
            # 检查端口映射
            container_ports=$(docker inspect postgres-server --format '{{json .HostConfig.PortBindings}}' 2>/dev/null || echo "{}")
            if [ "$container_ports" = "{}" ] || [ -z "$container_ports" ]; then
                print_error "Docker 容器端口映射未配置"
                print_warning "这通常是由于端口 $DB_PORT 被宿主机 PostgreSQL 服务占用导致的"
                print_info ""
                print_info "建议运行端口冲突修复脚本："
                print_info "  ./fix_postgresql_port_conflict.sh"
                print_info ""
                print_info "或者运行密码修复脚本（如果端口映射正常）："
                print_info "  ./fix_postgresql_password.sh"
            else
                print_warning "可能的问题："
                print_info "  1. 密码不正确（宿主机连接需要密码认证）"
                print_info "  2. pg_hba.conf 配置不允许从宿主机连接"
                print_info "  3. 防火墙或网络配置问题"
                print_info ""
                print_info "建议运行修复脚本："
                print_info "  ./fix_postgresql_password.sh"
            fi
        else
            print_error "容器内连接也失败，请检查容器状态"
        fi
        exit 1
    fi
else
    print_warning "未安装 psql 客户端，跳过 psql 测试"
    print_info "安装 psql 客户端："
    print_info "  Ubuntu/Debian: sudo apt-get install postgresql-client"
    print_info "  CentOS/RHEL: sudo yum install postgresql"
    print_info "  macOS: brew install postgresql"
fi

# 测试连接（方法2: 使用 telnet 或 nc）
print_info "测试端口连通性..."
if command -v nc &> /dev/null; then
    if nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
        print_success "端口 $DB_PORT 可达（使用 nc）"
    else
        print_warning "端口 $DB_PORT 不可达（使用 nc）"
    fi
elif command -v telnet &> /dev/null; then
    if timeout 2 bash -c "echo > /dev/tcp/$DB_HOST/$DB_PORT" 2>/dev/null; then
        print_success "端口 $DB_PORT 可达（使用 bash）"
    else
        print_warning "端口 $DB_PORT 不可达（使用 bash）"
    fi
else
    print_warning "无法测试端口连通性（nc 或 telnet 命令不可用）"
fi

# 测试连接（方法3: 使用 Python）
if command -v python3 &> /dev/null; then
    print_info "使用 Python 测试连接..."
    python3 << EOF
import sys
try:
    import psycopg2
    try:
        conn = psycopg2.connect(
            host="$DB_HOST",
            port=$DB_PORT,
            user="$DB_USER",
            password="$DB_PASSWORD",
            database="$DB_NAME",
            connect_timeout=5
        )
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"[SUCCESS] Python 连接测试成功")
        print(f"[INFO] PostgreSQL 版本: {version}")
        cur.close()
        conn.close()
        sys.exit(0)
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Python 连接测试失败: {e}")
        sys.exit(1)
except ImportError:
    print("[WARNING] psycopg2 未安装，跳过 Python 测试")
    print("[INFO] 安装命令: pip3 install psycopg2-binary")
    sys.exit(0)
EOF
    python_exit_code=$?
    if [ $python_exit_code -eq 0 ]; then
        print_success "Python 连接测试成功"
    elif [ $python_exit_code -eq 1 ]; then
        print_error "Python 连接测试失败"
    fi
fi

# 总结
print_section "测试总结"
print_success "PostgreSQL 连接测试完成！"
print_info "连接信息："
print_info "  主机: $DB_HOST"
print_info "  端口: $DB_PORT"
print_info "  用户: $DB_USER"
print_info "  数据库: $DB_NAME"
echo ""
print_info "如果连接失败，请检查："
print_info "  1. 容器是否正常运行: docker ps | grep postgres"
print_info "  2. 端口是否正确映射: docker port postgres-server"
print_info "  3. 密码是否正确: 运行 ./fix_postgresql_password.sh"
print_info "  4. pg_hba.conf 配置: docker exec postgres-server cat /var/lib/postgresql/data/pg_hba.conf"

