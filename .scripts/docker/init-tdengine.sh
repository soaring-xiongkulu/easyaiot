#!/bin/bash
# TDengine 数据库初始化脚本
# 执行 SQL 文件初始化数据库和超级表

set -e

TDENGINE_HOST="${TDENGINE_HOST:-tdengine-server}"
TDENGINE_PORT="${TDENGINE_PORT:-6030}"
SQL_FILE="${SQL_FILE:-/init-sql/tdengine_super_tables.sql}"

# 超时设置（秒）
MAX_WAIT=180
TIMEOUT=300

echo "等待 TDengine 服务就绪..."
WAIT_COUNT=0
READY=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    # 检查连接
    result=$(timeout 5 taos -h "$TDENGINE_HOST" -P "$TDENGINE_PORT" -s "select 1;" 2>&1 || echo "TIMEOUT")
    
    if echo "$result" | grep -qE "Query OK|1 row|rows in set"; then
        # 再次确认连接成功，并检查集群状态
        cluster_check=$(timeout 5 taos -h "$TDENGINE_HOST" -P "$TDENGINE_PORT" -s "show dnodes;" 2>&1 | grep -c "localhost\|online" || echo "0")
        if [ "$cluster_check" -gt 0 ]; then
            echo "✓ TDengine 已就绪（连接测试通过，集群状态正常）"
            READY=1
            break
        fi
    fi
    
    WAIT_COUNT=$((WAIT_COUNT + 1))
    if [ $((WAIT_COUNT % 10)) -eq 0 ]; then
        echo "  尝试 $WAIT_COUNT/$MAX_WAIT..."
        if [ -n "$result" ] && [ "$result" != "TIMEOUT" ]; then
            echo "  当前状态: ${result:0:100}"
        fi
    fi
    sleep 2
done

# 最终检查
if [ $READY -eq 0 ]; then
    echo "✗ TDengine 未就绪，超时退出（等待了 $MAX_WAIT 秒）"
    echo "最后一次连接尝试结果:"
    timeout 5 taos -h "$TDENGINE_HOST" -P "$TDENGINE_PORT" -s "select 1;" 2>&1 || echo "连接超时或失败"
    exit 1
fi

echo ""
echo "执行 SQL 文件: ${SQL_FILE}"
if [ ! -f "$SQL_FILE" ]; then
    echo "✗ SQL 文件不存在: ${SQL_FILE}"
    exit 1
fi

# 执行 SQL 文件（使用 -s 参数执行整个文件内容，避免交互式问题）
# 添加超时机制，避免卡住
echo "导入 SQL 文件（超时时间: ${TIMEOUT}秒）..."
SQL_CONTENT=$(cat "$SQL_FILE")

# 使用timeout命令执行SQL，避免无限等待
SQL_OUTPUT=$(timeout $TIMEOUT taos -h "$TDENGINE_HOST" -P "$TDENGINE_PORT" -s "$SQL_CONTENT" 2>&1)
SQL_EXIT_CODE=$?

if [ $SQL_EXIT_CODE -eq 0 ]; then
    echo "✓ SQL 文件执行成功"
elif [ $SQL_EXIT_CODE -eq 124 ]; then
    echo "✗ SQL 文件执行超时（超过 ${TIMEOUT} 秒）"
    echo "这通常表示 TDengine 服务未正常启动或响应缓慢"
    echo "请检查 TDengine 服务状态和日志"
    exit 1
else
    # 检查是否是已知的非致命错误
    if echo "$SQL_OUTPUT" | grep -qiE "(already exists|exist|warning|notice)"; then
        echo "⚠️  SQL 文件执行有警告，但继续检查..."
    else
        echo "⚠️  SQL 文件执行可能有错误:"
        echo "$SQL_OUTPUT" | head -n 20
    fi
    
    # 即使有错误也继续，检查数据库和超级表是否已创建
    echo "验证数据库和超级表是否已创建..."
    DB_CHECK=$(timeout 10 taos -h "$TDENGINE_HOST" -P "$TDENGINE_PORT" -s "use iot_device; show stables;" 2>&1)
    if echo "$DB_CHECK" | grep -q "st_"; then
        echo "✓ 数据库和超级表已创建（可能有警告，但已忽略）"
    else
        echo "✗ SQL 文件执行失败，数据库或超级表未正确创建"
        echo "数据库检查结果:"
        echo "$DB_CHECK" | head -n 10
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

