#!/bin/bash

# ============================================
# 删除所有表并重新导入SQL文件的脚本
# 适用于 PostgreSQL 数据库
# 警告：此脚本将删除数据库中的所有表并重新导入，请谨慎使用！
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 默认配置（可以从环境变量或参数覆盖）
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-iot45722414822}"

# SQL文件路径（相对于项目根目录）
SQL_DIR="${SQL_DIR:-$PROJECT_ROOT/.scripts/postgresql}"

# 数据库和SQL文件映射
declare -A DB_SQL_MAP=(
    ["ruoyi-vue-pro20"]="ruoyi-vue-pro10.sql"
    ["iot-device20"]="iot-device10.sql"
    ["iot-message20"]="iot-message10.sql"
)

# 显示使用说明
show_usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --host HOST         数据库主机 (默认: localhost)"
    echo "  -p, --port PORT         数据库端口 (默认: 5432)"
    echo "  -U, --user USER         数据库用户 (默认: postgres)"
    echo "  -W, --password PASS     数据库密码 (默认: 从环境变量或配置读取)"
    echo "  -s, --sql-dir DIR       SQL文件目录 (默认: ./.scripts/postgresql)"
    echo "  --skip-drop             跳过删除表步骤，直接导入"
    echo "  --skip-import           只删除表，不导入"
    echo "  --help                  显示此帮助信息"
    echo ""
    echo "环境变量:"
    echo "  DB_HOST                 数据库主机"
    echo "  DB_PORT                 数据库端口"
    echo "  DB_USER                 数据库用户"
    echo "  DB_PASSWORD             数据库密码"
    echo "  SQL_DIR                 SQL文件目录"
    echo ""
    echo "示例:"
    echo "  $0 -h localhost -p 5432 -U postgres"
    echo "  DB_PASSWORD=mypass $0"
}

# 解析命令行参数
SKIP_DROP=false
SKIP_IMPORT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            DB_HOST="$2"
            shift 2
            ;;
        -p|--port)
            DB_PORT="$2"
            shift 2
            ;;
        -U|--user)
            DB_USER="$2"
            shift 2
            ;;
        -W|--password)
            DB_PASSWORD="$2"
            shift 2
            ;;
        -s|--sql-dir)
            SQL_DIR="$2"
            shift 2
            ;;
        --skip-drop)
            SKIP_DROP=true
            shift
            ;;
        --skip-import)
            SKIP_IMPORT=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}错误: 未知参数 $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# 检查 psql 命令是否可用
if ! command -v psql &> /dev/null; then
    echo -e "${RED}错误: 未找到 psql 命令，请先安装 PostgreSQL 客户端${NC}"
    exit 1
fi

# 检查 SQL 文件目录是否存在
if [ ! -d "$SQL_DIR" ]; then
    echo -e "${RED}错误: SQL 文件目录不存在: $SQL_DIR${NC}"
    exit 1
fi

# 确认操作
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}删除表并重新导入SQL文件脚本${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo -e "${YELLOW}数据库连接信息:${NC}"
echo "  主机: $DB_HOST"
echo "  端口: $DB_PORT"
echo "  用户: $DB_USER"
echo ""
echo -e "${YELLOW}将处理的数据库:${NC}"
for db_name in "${!DB_SQL_MAP[@]}"; do
    sql_file="${DB_SQL_MAP[$db_name]}"
    echo "  - $db_name -> $sql_file"
done
echo ""
if [ "$SKIP_DROP" = true ]; then
    echo -e "${BLUE}注意: 将跳过删除表步骤${NC}"
fi
if [ "$SKIP_IMPORT" = true ]; then
    echo -e "${BLUE}注意: 将跳过导入步骤${NC}"
fi
echo ""
read -p "确认要继续吗？(输入 'YES' 继续): " confirm

if [ "$confirm" != "YES" ]; then
    echo -e "${YELLOW}操作已取消${NC}"
    exit 0
fi

# 设置密码
export PGPASSWORD="$DB_PASSWORD"

# 处理每个数据库
success_count=0
total_count=${#DB_SQL_MAP[@]}

for db_name in "${!DB_SQL_MAP[@]}"; do
    sql_file="${DB_SQL_MAP[$db_name]}"
    sql_path="$SQL_DIR/$sql_file"
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}处理数据库: $db_name${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # 检查SQL文件是否存在
    if [ ! -f "$sql_path" ]; then
        echo -e "${RED}✗ SQL 文件不存在: $sql_path${NC}"
        continue
    fi
    
    # 检查数据库是否存在
    if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$db_name'" | grep -q 1; then
        echo -e "${YELLOW}⚠ 数据库 '$db_name' 不存在，跳过${NC}"
        continue
    fi
    
    # 步骤1: 删除所有表
    if [ "$SKIP_DROP" = false ]; then
        echo -e "${GREEN}步骤1: 删除数据库 '$db_name' 中的所有表...${NC}"
        
        # 动态生成删除所有表的SQL
        # 查询所有表名（排除系统表），使用CASCADE确保删除依赖关系
        # 参考 AI/drop_import_tables.py 和 VIDEO/drop_import_tables.py 的实现方式
        drop_sql=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" -t -A -c "
            SELECT 'DROP TABLE IF EXISTS \"' || schemaname || '\".\"' || tablename || '\" CASCADE;'
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        " 2>/dev/null)
        
        if [ -n "$drop_sql" ]; then
            # 创建临时SQL文件
            temp_drop_sql=$(mktemp)
            
            # 先禁用外键约束检查（PostgreSQL使用session_replication_role）
            echo "SET session_replication_role = 'replica';" > "$temp_drop_sql"
            echo "$drop_sql" >> "$temp_drop_sql"
            echo "SET session_replication_role = 'origin';" >> "$temp_drop_sql"
            
            # 执行删除
            if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" -f "$temp_drop_sql" > /dev/null 2>&1; then
                echo -e "${GREEN}  ✓ 所有表已删除${NC}"
            else
                echo -e "${YELLOW}  ⚠ 删除表时出现警告（可能数据库为空或已删除）${NC}"
            fi
            
            # 清理临时文件
            rm -f "$temp_drop_sql"
        else
            echo -e "${BLUE}  ℹ 数据库中没有表需要删除${NC}"
        fi
    fi
    
    # 步骤2: 导入SQL文件
    if [ "$SKIP_IMPORT" = false ]; then
        echo -e "${GREEN}步骤2: 导入SQL文件 '$sql_file'...${NC}"
        
        # 创建临时文件，过滤掉DROP DATABASE和CREATE DATABASE语句
        temp_sql=$(mktemp)
        
        # 过滤SQL文件：移除DROP DATABASE、CREATE DATABASE语句，以及psql元命令
        # 参考 init-databases.sh 的导入方式，直接使用psql -f导入
        sed -E '/^DROP DATABASE/d; /^CREATE DATABASE/d; /^\\connect/d; /^\\unrestrict/d; /^\\restrict/d; /^\\encoding/d' "$sql_path" > "$temp_sql"
        
        # 导入过滤后的SQL文件
        # 参考 init-databases.sh: psql -U "$POSTGRES_USER" -d "$db_name" -f "$SQL_DIR/$sql_file" > /dev/null 2>&1
        if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" -f "$temp_sql" > /dev/null 2>&1; then
            echo -e "${GREEN}  ✓ SQL文件导入成功${NC}"
            ((success_count++))
        else
            # 如果导入失败，显示错误信息
            echo -e "${RED}  ✗ SQL文件导入失败，显示错误信息:${NC}"
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" -f "$temp_sql" 2>&1 | grep -i "error\|fatal" | head -20
        fi
        
        # 清理临时文件
        rm -f "$temp_sql"
    else
        ((success_count++))
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
if [ $success_count -eq $total_count ]; then
    echo -e "${GREEN}✓ 所有操作完成！成功处理 $success_count/$total_count 个数据库${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ 部分操作完成：成功 $success_count/$total_count 个数据库${NC}"
    exit 1
fi
