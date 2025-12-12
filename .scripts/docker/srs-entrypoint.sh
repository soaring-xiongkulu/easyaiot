#!/bin/bash
# SRS 容器启动脚本
# 在启动 SRS 前自动设置 /data 目录权限，确保创建的录像文件可以被普通用户删除

set -e

# 数据目录路径
DATA_DIR="/data"
PLAYBACKS_DIR="/data/playbacks"

echo "[SRS Entrypoint] 检查并设置数据目录权限..."

# 创建目录（如果不存在）
mkdir -p "$DATA_DIR" "$PLAYBACKS_DIR"

# 设置目录权限为 777，确保所有用户都可以读写
# 这样即使 SRS 以 root 运行，创建的文件也可以被普通用户删除
chmod -R 777 "$DATA_DIR" 2>/dev/null || {
    echo "⚠️  警告: 无法设置目录权限，可能影响文件访问"
}

# 设置 umask，让新创建的文件权限更宽松（666 = rw-rw-rw-）
# 这样即使以 root 运行，创建的文件也可以被普通用户读写
umask 0000

echo "[SRS Entrypoint] ✓ 数据目录权限已设置"
echo "[SRS Entrypoint] ✓ umask 已设置为 0000（新文件权限: 666）"

# 调用 SRS 原始命令
# 使用 exec 确保信号正确传递
exec "$@"











