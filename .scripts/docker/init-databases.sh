#!/bin/bash
# PostgreSQL 数据库初始化脚本
# 此脚本会创建所需的数据库并导入对应的 SQL 文件
# 注意：此脚本仅在 PostgreSQL 首次启动时执行（数据目录为空时）

set -e

SQL_DIR="/docker-entrypoint-initdb.d"
POSTGRES_USER="${POSTGRES_USER:-postgres}"

# 数据库和 SQL 文件映射（使用函数模拟关联数组，兼容 bash 3.2）
get_sql_file() {
    case "$1" in
        "ruoyi-vue-pro20") echo "ruoyi-vue-pro10.sql" ;;
        "iot-device20") echo "iot-device10.sql" ;;
        "iot-message20") echo "iot-message10.sql" ;;
        "iot-video20") echo "iot-video10.sql" ;;
        "iot-ai20") echo "iot-ai10.sql" ;;
        *) echo "" ;;
    esac
}

# 数据库列表
DATABASES=("ruoyi-vue-pro20" "iot-device20" "iot-message20" "iot-video20" "iot-ai20")

echo "=========================================="
echo "开始初始化 PostgreSQL 数据库"
echo "=========================================="

# 等待 PostgreSQL 就绪
echo "等待 PostgreSQL 就绪..."
until psql -U "$POSTGRES_USER" -d postgres -c '\q' 2>/dev/null; do
    sleep 1
done

echo "PostgreSQL 已就绪，开始创建数据库..."
echo ""

# 创建数据库并导入 SQL
success_count=0
total_count=${#DATABASES[@]}

for db_name in "${DATABASES[@]}"; do
    sql_file=$(get_sql_file "$db_name")
    
    if [ -z "$sql_file" ]; then
        echo "⚠️  警告: 数据库 $db_name 没有对应的 SQL 文件映射，跳过"
        continue
    fi
    
    echo "处理数据库: $db_name"
    echo "  SQL 文件: $sql_file"
    
    # 检查数据库是否已存在
    if psql -U "$POSTGRES_USER" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$db_name'" | grep -q 1; then
        echo "  ✓ 数据库 $db_name 已存在"
    else
        echo "  → 创建数据库: $db_name"
        if psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE \"$db_name\";" 2>/dev/null; then
            echo "  ✓ 数据库创建成功"
        else
            echo "  ✗ 数据库创建失败"
            continue
        fi
    fi
    
    # 检查表是否已存在（判断是否已初始化）
    table_count=$(psql -U "$POSTGRES_USER" -d "$db_name" -tc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "0")
    
    if [ "$table_count" -gt 0 ]; then
        echo "  ✓ 数据库已包含 $table_count 个表，跳过 SQL 导入"
        success_count=$((success_count + 1))
    else
        if [ -f "$SQL_DIR/$sql_file" ]; then
            echo "  → 导入 SQL 文件: $sql_file"
            if psql -U "$POSTGRES_USER" -d "$db_name" -f "$SQL_DIR/$sql_file" > /dev/null 2>&1; then
                echo "  ✓ SQL 文件导入成功"
                success_count=$((success_count + 1))
            else
                echo "  ✗ SQL 文件导入失败，请检查文件内容"
            fi
        else
            echo "  ✗ SQL 文件不存在: $SQL_DIR/$sql_file"
        fi
    fi
    echo ""
done

echo "=========================================="
if [ $success_count -eq $total_count ]; then
    echo "✓ 数据库初始化完成！($success_count/$total_count)"
else
    echo "⚠️  数据库初始化部分完成 ($success_count/$total_count)"
fi
echo "=========================================="

