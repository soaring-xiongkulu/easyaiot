#!/bin/bash
# TDengine 数据库初始化脚本
# 执行 SQL 文件初始化数据库和超级表

set -e

TDENGINE_HOST="${TDENGINE_HOST:-tdengine-server}"
TDENGINE_PORT="${TDENGINE_PORT:-6030}"
SQL_FILE="${SQL_FILE:-/init-sql/tdengine_super_tables.sql}"

echo "等待 TDengine 服务就绪..."
for i in $(seq 1 60); do
    # 检查连接，忽略 "unavailable" 输出，只检查退出码
    if taos -h "$TDENGINE_HOST" -P "$TDENGINE_PORT" -s "select 1;" 2>&1 | grep -q "Query OK" || [ $? -eq 0 ]; then
        # 再次确认连接成功
        result=$(taos -h "$TDENGINE_HOST" -P "$TDENGINE_PORT" -s "select 1;" 2>&1)
        if echo "$result" | grep -q "Query OK\|1 row"; then
            echo "✓ TDengine 已就绪"
            break
        fi
    fi
    if [ $i -lt 60 ]; then
        echo "  尝试 $i/60..."
        sleep 2
    fi
done

# 最终检查
if ! taos -h "$TDENGINE_HOST" -P "$TDENGINE_PORT" -s "select 1;" 2>&1 | grep -q "Query OK\|1 row"; then
    echo "✗ TDengine 未就绪，超时退出"
    exit 1
fi

echo ""
echo "执行 SQL 文件: ${SQL_FILE}"
if [ ! -f "$SQL_FILE" ]; then
    echo "✗ SQL 文件不存在: ${SQL_FILE}"
    exit 1
fi

# 执行 SQL 文件（使用 -s 参数执行整个文件内容，避免交互式问题）
echo "导入 SQL 文件..."
SQL_CONTENT=$(cat "$SQL_FILE")
if taos -h "$TDENGINE_HOST" -P "$TDENGINE_PORT" -s "$SQL_CONTENT" 2>&1; then
    echo "✓ SQL 文件执行成功"
else
    # 即使有错误也继续，检查数据库和超级表是否已创建
    if taos -h "$TDENGINE_HOST" -P "$TDENGINE_PORT" -s "use iot_device; show stables;" 2>&1 | grep -q "st_"; then
        echo "✓ 数据库和超级表已创建（可能有警告，但已忽略）"
    else
        echo "✗ SQL 文件执行失败"
        exit 1
    fi
fi

echo ""
echo "验证数据库创建..."
if taos -h "$TDENGINE_HOST" -P "$TDENGINE_PORT" -s "use iot_device; show stables;" 2>&1 | grep -q "st_"; then
    stable_count=$(taos -h "$TDENGINE_HOST" -P "$TDENGINE_PORT" -s "use iot_device; show stables;" 2>&1 | grep -c "st_" || echo "0")
    echo "✓ TDengine 数据库初始化完成，已创建 $stable_count 个超级表"
else
    echo "⚠️  警告: 数据库已创建，但未检测到超级表"
fi

