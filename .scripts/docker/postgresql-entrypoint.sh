#!/bin/bash
# PostgreSQL 容器启动脚本
# 在启动 PostgreSQL 前自动修复数据目录权限问题
# 解决 "could not open file global/pg_filenode.map: Permission denied" 错误

set -e

# 数据目录路径
DATA_DIR="/var/lib/postgresql/data"
LOG_DIR="/var/log/postgresql"

# PostgreSQL 容器使用的 UID/GID
PG_UID=999
PG_GID=999

# 修复权限函数
fix_permissions() {
    # 只有 root 用户才能修复权限
    if [ "$EUID" -ne 0 ]; then
        # 如果不是 root，检查权限是否正确
        if [ -d "$DATA_DIR" ]; then
            CURRENT_UID=$(stat -c "%u" "$DATA_DIR" 2>/dev/null || echo "")
            if [ "$CURRENT_UID" != "$PG_UID" ]; then
                echo "⚠️  警告: 数据目录权限不正确 (UID: $CURRENT_UID, 应该是: $PG_UID)"
                echo "⚠️  容器需要以 root 启动才能自动修复权限"
                echo "⚠️  或者手动修复: sudo chown -R 999:999 $DATA_DIR $LOG_DIR"
            fi
        fi
        return 0
    fi
    
    echo "[PostgreSQL Entrypoint] 检查并修复数据目录权限..."
    
    # 创建目录（如果不存在）
    mkdir -p "$DATA_DIR" "$LOG_DIR"
    
    # 检查并修复权限
    if [ -d "$DATA_DIR" ]; then
        CURRENT_UID=$(stat -c "%u" "$DATA_DIR" 2>/dev/null || echo "")
        if [ "$CURRENT_UID" != "$PG_UID" ]; then
            echo "[PostgreSQL Entrypoint] 检测到权限问题：数据目录所有者是 UID $CURRENT_UID，应该是 $PG_UID"
            echo "[PostgreSQL Entrypoint] 正在修复权限..."
            
            chown -R ${PG_UID}:${PG_GID} "$DATA_DIR" "$LOG_DIR" 2>/dev/null || {
                echo "⚠️  警告: 无法修复权限，可能影响 PostgreSQL 启动"
                return 1
            }
            chmod -R 700 "$DATA_DIR" 2>/dev/null || true
            chmod -R 755 "$LOG_DIR" 2>/dev/null || true
            echo "[PostgreSQL Entrypoint] ✓ 权限已修复"
        else
            echo "[PostgreSQL Entrypoint] ✓ 数据目录权限正确 (UID: $CURRENT_UID)"
        fi
    fi
    
    # 如果使用 PGDATA 子目录，也检查其父目录权限
    if [ -n "$PGDATA" ] && [ "$PGDATA" != "$DATA_DIR" ]; then
        PGDATA_PARENT=$(dirname "$PGDATA")
        if [ -d "$PGDATA_PARENT" ]; then
            CURRENT_UID=$(stat -c "%u" "$PGDATA_PARENT" 2>/dev/null || echo "")
            if [ "$CURRENT_UID" != "$PG_UID" ]; then
                echo "[PostgreSQL Entrypoint] 修复 PGDATA 父目录权限..."
                chown -R ${PG_UID}:${PG_GID} "$PGDATA_PARENT" 2>/dev/null || true
                chmod -R 700 "$PGDATA_PARENT" 2>/dev/null || true
            fi
        fi
    fi
    
    return 0
}

# 执行权限修复（仅在 root 用户下执行）
fix_permissions

# 调用 PostgreSQL 官方镜像的原始 entrypoint
# PostgreSQL 的原始 entrypoint 会自动处理用户切换
# 使用 exec 确保信号正确传递
if [ "$EUID" -eq 0 ]; then
    # 如果是 root，使用 gosu 切换到 postgres 用户执行原始 entrypoint
    # 原始 entrypoint 会处理后续的用户切换和 PostgreSQL 启动
    if command -v gosu > /dev/null 2>&1; then
        exec gosu postgres /usr/local/bin/docker-entrypoint.sh "$@"
    else
        # 如果没有 gosu，尝试使用 su（但 PostgreSQL 镜像应该有 gosu）
        echo "⚠️  警告: gosu 未找到，尝试使用 su"
        exec su -s /bin/bash postgres -c "/usr/local/bin/docker-entrypoint.sh $*"
    fi
else
    # 如果已经是 postgres 用户，直接执行
    exec /usr/local/bin/docker-entrypoint.sh "$@"
fi

